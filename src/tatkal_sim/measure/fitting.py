"""Calibration fit (R2 carried half; tasks P4.1-P4.3).

Fits the server model to `calibration/2026-08-11-postgres-http.csv` under
the design's predeclared protocol (D10/S8):

- objective: joint log-space RMSE over per-level MEDIANS of steady
  throughput and steady p99;
- target: every fitted median within +/-25% of measured;
- overfit guard: leave-one-level-out, held-out prediction within +/-40%;
- miss path: per-level residuals reported; the chair accepts a documented
  deviation or directs refinement — never a silent bad fit.

Replica: the R2 harness's shape re-created in-model — C closed-loop
clients, synchronized first request at T0 (the convoy), then back-to-back
requests for the measured duration (steady state excludes each client's
first request), hot key = one pool, `max_connections`/backlog analogues
from the real run.

Model extension flagged to the chair: `congestion_k` (ServerConfig) —
effective app_time scales with active connections. The measured system's
throughput DECLINES 4865 -> 1537 ops/s with concurrency; a fixed-service
FIFO model can only plateau. The sharded8 control (p99 halves at equal
throughput) identifies the app-tier component this term carries.
"""

from __future__ import annotations

import itertools
import json
import math
import statistics
import dataclasses
from dataclasses import dataclass
from pathlib import Path

from tatkal_sim.config import FidelityConfig
from tatkal_sim.core import Clock, EventQueue, RngStreams
from tatkal_sim.model.server import Server, ServerConfig
from tatkal_sim.model.users import Outcome

CSV = Path("docs/specs/tatkal-spike-prototype/calibration/2026-08-11-postgres-http.csv")
HOT_POOL = (1, "AC", "D0")


# ---------------------------------------------------------------- CSV loading
@dataclass(frozen=True)
class Level:
    concurrency: int
    thr: float  # median steady throughput, ops/s
    p50: float  # ms
    p95: float
    p99: float
    thr_range: tuple[float, float]
    p99_range: tuple[float, float]
    convoy_p99: float


def load_calibration(path: Path = CSV) -> tuple[list[Level], dict]:
    rows: list[dict] = []
    for line in path.read_text().splitlines():
        if line.startswith("#") or line.startswith("concurrency,"):
            continue
        c = line.split(",")
        rows.append(
            dict(
                c=int(c[0]),
                mode=c[2],
                thr=float(c[3]),
                p50=float(c[5]),
                p95=float(c[6]),
                p99=float(c[7]),
                cv99=float(c[10]),
            )
        )
    hot = [r for r in rows if r["mode"] == "hot"]
    levels = []
    for c in sorted({r["c"] for r in hot}):
        g = [r for r in hot if r["c"] == c]
        thr = [r["thr"] for r in g]
        p99 = [r["p99"] for r in g]
        levels.append(
            Level(
                c,
                statistics.median(thr),
                statistics.median(r["p50"] for r in g),
                statistics.median(r["p95"] for r in g),
                statistics.median(p99),
                (min(thr), max(thr)),
                (min(p99), max(p99)),
                statistics.median(r["cv99"] for r in g),
            )
        )
    sh = [r for r in rows if r["mode"] == "sharded8"]
    sharded64 = {
        "thr": statistics.median(r["thr"] for r in sh),
        "p99": statistics.median(r["p99"] for r in sh),
    }
    return levels, sharded64


# ------------------------------------------------------------------- replica
def replica_run(
    concurrency: int,
    scfg: ServerConfig,
    *,
    seed: int = 1,
    duration: float = 2.0,
    sharded_pools: int = 0,
    fidelity: FidelityConfig | None = None,
) -> dict:
    """Closed-loop calibration replica; returns steady + convoy stats."""
    fidelity = fidelity or FidelityConfig()
    clock = Clock()
    queue = EventQueue(clock)
    streams = RngStreams(seed)
    server = Server(clock, queue, streams, fidelity, scfg, t0=0.0)
    samples: list[tuple[float, bool]] = []  # (latency_s, is_first)
    errors = 0

    def client(i: int) -> None:
        pool = (1 + i % sharded_pools, "AC", "D0") if sharded_pools else HOT_POOL
        first = True

        def fire() -> None:
            t_start = clock.now()

            def respond(outcome: Outcome, _first=None) -> None:
                nonlocal first, errors
                if outcome is Outcome.HARD_ERROR:
                    errors += 1
                else:
                    samples.append((clock.now() - t_start, first))
                first = False
                if clock.now() < duration:
                    fire()

            server.submit(i, pool, respond)

        fire()

    for i in range(concurrency):
        queue.schedule_at(0.0, lambda i=i: client(i))
    queue.run(max_events=5_000_000)

    steady = sorted(s[0] for s in samples if not s[1])
    convoy = sorted(s[0] for s in samples if s[1])

    def pct(xs: list[float], p: float) -> float:
        return xs[min(len(xs) - 1, int(len(xs) * p))] * 1000.0 if xs else float("nan")

    return {
        "thr": len(steady) / duration,
        "p50": pct(steady, 0.50),
        "p95": pct(steady, 0.95),
        "p99": pct(steady, 0.99),
        "convoy_p99": pct(convoy, 0.99),
        "errors": errors,
    }


def replica_config(params: dict, **kw) -> ServerConfig:
    """Calibration-replica server config from a fit-parameter dict.

    Keys: workers, service_ms, congestion_k, gamma, hold_ms, and optionally
    sigma (app_sigma as a fit parameter), tail_mean_ms (app-phase rare
    extra), stall_mean_ms (hold-stall: rare long stall INSIDE the lock
    hold, blocking the queue behind it — the chair-directed refinement
    mechanism). Rare-event probabilities are fixed at 1%; the means are
    what the fit tunes.
    """
    return ServerConfig(
        workers=params["workers"],
        accept_queue=512,  # harness request_queue_size
        conn_limit=450,  # harness max_connections
        app_mu=math.log(params["service_ms"] / 1000.0),
        app_sigma=params.get("sigma", kw.pop("app_sigma", 0.6)),
        tail_p=kw.pop("tail_p", 0.01),
        tail_mean=params.get("tail_mean_ms", 0.0) / 1000.0,
        lock_hold=params["hold_ms"] / 1000.0,
        congestion_k=params["congestion_k"],
        congestion_gamma=params.get("gamma", 1.0),
        hold_stall_p=0.01,
        hold_stall_mean=params.get("stall_mean_ms", 0.0) / 1000.0,
        seats_per_pool=10_000_000,  # measures capacity, not the sell-out race
        **kw,
    )


# ----------------------------------------------------------------- objective
def model_curve(
    scfg: ServerConfig, levels: list[int], *, seeds=(1,), duration=2.0
) -> dict[int, dict]:
    out = {}
    for c in levels:
        runs = [replica_run(c, scfg, seed=s, duration=duration) for s in seeds]
        out[c] = {
            k: statistics.median(r[k] for r in runs)
            for k in ("thr", "p50", "p95", "p99", "convoy_p99")
        }
    return out


def residuals(curve: dict[int, dict], targets: list[Level]) -> dict[int, dict]:
    res = {}
    for lvl in targets:
        m = curve[lvl.concurrency]
        res[lvl.concurrency] = {
            "thr_ratio": m["thr"] / lvl.thr,
            "p99_ratio": m["p99"] / lvl.p99,
        }
    return res


def objective(curve: dict[int, dict], targets: list[Level]) -> float:
    total = 0.0
    for lvl in targets:
        m = curve[lvl.concurrency]
        total += math.log(m["thr"] / lvl.thr) ** 2 + math.log(m["p99"] / lvl.p99) ** 2
    return math.sqrt(total / (2 * len(targets)))


# --------------------------------------------------------------------- search
def fit(
    targets: list[Level],
    *,
    grid: dict | None = None,
    seeds=(1,),
    duration: float = 1.0,
    log=lambda s: None,
) -> tuple[dict, float]:
    """Deterministic grid search over the six fit parameters.

    Default grid is the analytic neighborhood derived from the measured
    curve: W~2-4 (GIL-limited true parallelism), gamma~0.45 (sublinear
    congestion growth fitted from the 8->64->256 decline ratios).
    """
    levels = [t.concurrency for t in targets]
    grid = grid or {
        "workers": [2, 3, 4],
        "service_ms": [0.12, 0.16, 0.20],
        "congestion_k": [0.3, 0.5, 0.8],
        "gamma": [0.35, 0.45, 0.55],
        "hold_ms": [0.05, 0.10, 0.20],
        "tail_mean_ms": [0.0, 2.0, 5.0],
    }
    best, best_loss = None, float("inf")
    keys = list(grid)
    for combo in itertools.product(*(grid[k] for k in keys)):
        p = dict(zip(keys, combo))
        loss = objective(
            model_curve(replica_config(p), levels, seeds=seeds, duration=duration),
            targets,
        )
        if loss < best_loss:
            best, best_loss = p, loss
            log(f"  new best {best} loss={loss:.4f}")
    return best, best_loss


def refine(
    params: dict, targets: list[Level], *, steps=2, seeds=(1,), duration=1.0, log=lambda s: None
) -> tuple[dict, float]:
    """Local coordinate refinement around a grid optimum."""
    factors = [0.8, 0.9, 1.0, 1.1, 1.25]
    best, best_loss = dict(params), float("inf")
    levels = [t.concurrency for t in targets]
    for _ in range(steps):
        for key in (
            "service_ms",
            "congestion_k",
            "gamma",
            "hold_ms",
            "sigma",
            "stall_mean_ms",
            "tail_mean_ms",
        ):
            if not best.get(key):
                continue  # multiplicative steps cannot move a zero
            trials = []
            for f in factors:
                p = dict(best)
                p[key] = best[key] * f
                loss = objective(
                    model_curve(replica_config(p), levels, seeds=seeds, duration=duration),
                    targets,
                )
                trials.append((loss, p))
            loss, p = min(trials, key=lambda t: t[0])
            if loss < best_loss:
                best, best_loss = p, loss
                log(f"  refine {key} -> {p[key]:.4g} loss={loss:.4f}")
    return best, best_loss


# ------------------------------------------------------- experiment profiles
FIT_JSON = CSV.parent / "fit-2026-08-11.json"


def fitted_server_config(seats_per_pool: int = 25, path: Path = FIT_JSON) -> ServerConfig:
    """The committed fitted profile, re-seated for experiment scarcity.

    Everything except inventory comes from the calibration fit; seats are
    the experiment's scarcity knob (default 25/pool: ~13x overall, ~40x
    hot-pool oversubscription at the operating workload).
    """
    return dataclasses.replace(
        replica_config(load_fit(path)["params"]), seats_per_pool=seats_per_pool
    )


# ------------------------------------------------------------- knee variants
def knee_variant(name: str, fitted: dict) -> ServerConfig:
    """Selectable server profiles (P4.3): fitted / plateau / cliff.

    Every report names the variant it ran under (R2 acceptance).
    """
    if name == "fitted":
        p = dict(fitted)
    elif name == "plateau":
        p = {**fitted, "congestion_k": 0.0}  # capacity flatlines, no decline
    elif name == "cliff":
        # sharp collapse: congestion grows superlinearly past the knee
        p = {**fitted, "congestion_k": fitted["congestion_k"] * 2.0, "gamma": 1.0}
    else:
        raise ValueError(f"unknown knee variant: {name}")
    return replica_config(p)


KNEE_VARIANTS = ("fitted", "plateau", "cliff")


# ------------------------------------------------------------------ SVG plot
def _panel(x0, series, measured, title, ylab, width=430, height=300):
    """One log-x/log-y panel as SVG fragments. series/measured: {c: value}."""
    cs = sorted(measured)
    xmin, xmax = math.log(min(cs)), math.log(max(cs))
    vals = [v for v in list(series.values()) + [m for m, *_ in measured.values()] if v > 0]
    ymin, ymax = math.log(min(vals)) - 0.2, math.log(max(vals)) + 0.2
    px = lambda c: x0 + 50 + (math.log(c) - xmin) / (xmax - xmin) * (width - 70)  # noqa: E731
    py = lambda v: 30 + (ymax - math.log(v)) / (ymax - ymin) * (height - 60)  # noqa: E731
    out = [f'<text x="{x0 + width / 2}" y="18" text-anchor="middle" class="t">{title}</text>']
    out.append(
        f'<text x="{x0 + 12}" y="{height / 2}" class="a" transform="rotate(-90 {x0 + 12} {height / 2})" text-anchor="middle">{ylab}</text>'
    )
    for c in cs:
        out.append(f'<text x="{px(c)}" y="{height - 12}" text-anchor="middle" class="a">{c}</text>')
    # measured: point + min-max whisker
    for c, (med, lo, hi) in measured.items():
        out.append(f'<line x1="{px(c)}" y1="{py(lo)}" x2="{px(c)}" y2="{py(hi)}" class="w"/>')
        out.append(f'<circle cx="{px(c)}" cy="{py(med)}" r="4" class="m"/>')
    # model line
    pts = " ".join(f"{px(c)},{py(series[c])}" for c in cs if series.get(c, 0) > 0)
    out.append(f'<polyline points="{pts}" class="f"/>')
    return out


def write_fit_svg(path: Path, targets: list[Level], curve: dict[int, dict]) -> None:
    thr_meas = {t.concurrency: (t.thr, *t.thr_range) for t in targets}
    p99_meas = {t.concurrency: (t.p99, *t.p99_range) for t in targets}
    body = _panel(
        0, {c: v["thr"] for c, v in curve.items()}, thr_meas, "steady throughput (ops/s)", "ops/s"
    )
    body += _panel(440, {c: v["p99"] for c, v in curve.items()}, p99_meas, "steady p99 (ms)", "ms")
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 880 320" '
        'font-family="system-ui,sans-serif">'
        "<style>.t{font-size:13px;font-weight:600}.a{font-size:10px;fill:#666}"
        ".m{fill:#1a6feb}.w{stroke:#1a6feb;stroke-width:1.5;opacity:.5}"
        ".f{fill:none;stroke:#d9480f;stroke-width:2}</style>"
        '<rect width="880" height="320" fill="white"/>'
        + "".join(body)
        + '<text x="440" y="315" text-anchor="middle" class="a">'
        "blue = measured (median, min-max) · orange = fitted model · log-log</text>"
        "</svg>"
    )
    path.write_text(svg)


# ---------------------------------------------------------------- artifacts
def save_fit(path: Path, params: dict, loss: float, res: dict, lolo: dict, meta: dict) -> None:
    path.write_text(
        json.dumps(
            {"params": params, "objective": loss, "residuals": res, "lolo": lolo, "meta": meta},
            indent=2,
            sort_keys=True,
        )
    )


def load_fit(path: Path) -> dict:
    return json.loads(path.read_text())
