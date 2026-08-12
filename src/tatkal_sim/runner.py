"""Run orchestration: determinism harness (P1.3), arm sweeps and the
report generator (P5.2/P5.3).

An ARM is a named, fully-specified runnable configuration. At P5 that is
(fidelity, server config, client config, workload config, knee-variant
name); P6 adds the admission strategy. Arms are compared ONLY through the
paired harness (measure/stats.py) — both families (D10/S3):

- ladder family: rung k vs rung k-1 (marginal delta, R4);
- baseline family: adaptive/ML arm vs the strong baseline (R5).

Reports carry: the knee-variant name (R2 acceptance), the enabled
fidelity toggles (R3 acceptance), out-of-order arm labelling (R4/D5), a
SMOKE banner when below the pre-registered >= 20 replications, and the
rung-0 profile of the three unthresholded metrics that informs Gate A.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from tatkal_sim.config import FidelityConfig
from tatkal_sim.core import Clock, EventQueue, RngStreams
from tatkal_sim.measure import metrics as metrics_mod
from tatkal_sim.measure.stats import MIN_SEEDS, PairedResult, paired_compare
from tatkal_sim.model.server import Server, ServerConfig
from tatkal_sim.model.users import ClientConfig, ClientEngine
from tatkal_sim.model.workload import OPERATING_WORKLOAD, WorkloadConfig, generate_intents


# ------------------------------------------------------------ P1.3 harness
def result_digest(result: dict) -> str:
    """Canonical digest: sha256 of sorted-key JSON. Byte-level, on purpose."""
    return hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()


def run_trivial(master_seed: int, n_arrivals: int = 100) -> dict:
    """Trivial workload exercising clock + cascade + rng streams (P1.3)."""
    clock = Clock()
    queue = EventQueue(clock)
    streams = RngStreams(master_seed)
    arrivals = streams.get("arrivals")
    service = streams.get("service")
    completion_log: list[tuple[int, float]] = []

    def complete(i: int) -> None:
        completion_log.append((i, clock.now()))

    def arrive(i: int) -> None:
        queue.schedule_in(service.expovariate(1.0), lambda: complete(i))

    t = 0.0
    for i in range(n_arrivals):
        t += arrivals.expovariate(1.0)
        queue.schedule_at(t, lambda i=i: arrive(i))
    processed = queue.run()
    return {
        "master_seed": master_seed,
        "events_processed": processed,
        "completions": len(completion_log),
        "final_time": repr(clock.now()),
        "log_sha256": hashlib.sha256(repr(completion_log).encode()).hexdigest(),
    }


# ------------------------------------------------------------------- arms
@dataclass(frozen=True)
class Arm:
    name: str
    scfg: ServerConfig
    fidelity: FidelityConfig = field(default_factory=FidelityConfig)
    ccfg: ClientConfig = field(default_factory=ClientConfig)
    wcfg: WorkloadConfig = field(default_factory=lambda: OPERATING_WORKLOAD)
    variant: str = "fitted"  # knee-shape profile name (R2 acceptance)
    out_of_order: bool = False  # R4/D5: labelled, never reported as a rung


def run_arm_once(arm: Arm, seed: int) -> dict:
    """One seeded run of one arm -> full R6 metrics dict."""
    clock = Clock()
    queue = EventQueue(clock)
    streams = RngStreams(seed)
    intents = generate_intents(arm.wcfg, arm.fidelity, streams)
    log: list = []
    server = Server(clock, queue, streams, arm.fidelity, arm.scfg, arm.wcfg.t0, log=log)
    engine = ClientEngine(clock, queue, streams, arm.fidelity, arm.ccfg, arm.wcfg, server, log=log)
    engine.start(intents)
    queue.run(max_events=5_000_000)
    server.inventory.assert_ok()  # invariants run on EVERY run (R3.4)
    return metrics_mod.compute(
        log,
        intents,
        t0=arm.wcfg.t0,
        inventory_totals=server.inventory.totals(),
        inventory_violations=server.inventory.violations(),
        identity_on=arm.fidelity.user_identity,
        run_end=clock.now(),
    )


def sweep(arms: list[Arm], seeds: list[int]) -> dict[str, dict[int, dict]]:
    """All arms x all seeds. Same seed -> same workload trace across arms."""
    return {arm.name: {seed: run_arm_once(arm, seed) for seed in seeds} for arm in arms}


def metric_series(results: dict[int, dict], path: str) -> dict[int, float]:
    """Extract {seed: scalar} for a dotted metric path, e.g. 'ttda.winners.p99'."""
    out = {}
    for seed, m in results.items():
        v: object = m
        for part in path.split("."):
            v = v[part]  # type: ignore[index]
        out[seed] = float(v)  # type: ignore[arg-type]
    return out


# ------------------------------------------------------------------ report
HEADLINE_METRICS = ("ttda.winners.p99", "ttda.rejected.p99", "goodput.sold_per_s")
GATE_A_METRICS = ("wasted_work_ratio", "settling_time_s", "fairness.bots_win_share")


def _fmt(v: float | None) -> str:
    return "n/a" if v is None else (f"{v:.4g}")


def render_report(
    arms: list[Arm],
    results: dict[str, dict[int, dict]],
    *,
    ladder_pairs: list[tuple[str, str]],
    baseline_pairs: list[tuple[str, str]],
    stats_seed: int = 0,
) -> str:
    seeds = sorted(next(iter(results.values())).keys())
    smoke = len(seeds) < MIN_SEEDS
    lines = ["# tatkal-sim run report", ""]
    if smoke:
        lines += [
            f"> **SMOKE RUN** — {len(seeds)} seeds, below the pre-registered "
            f"minimum of {MIN_SEEDS} replications (R6). No claim may be made "
            "from this report.",
            "",
        ]
    lines += [f"Seeds: {seeds}", ""]

    lines += ["## Arms", ""]
    for arm in arms:
        toggles = ", ".join(arm.fidelity.enabled_toggles())
        badge = " **[OUT-OF-ORDER — not a rung]**" if arm.out_of_order else ""
        lines += [
            f"- **{arm.name}**{badge} — knee variant: `{arm.variant}`; "
            f"enabled toggles: {toggles}",
        ]
    lines += [""]

    lines += ["## Per-arm metrics (median across seeds)", ""]
    header = ["arm"] + [m for m in HEADLINE_METRICS] + list(GATE_A_METRICS)
    lines += ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    import statistics as st

    for arm in arms:
        row = [arm.name]
        for path in HEADLINE_METRICS + GATE_A_METRICS:
            try:
                vals = [v for v in metric_series(results[arm.name], path).values()]
                row.append(_fmt(st.median(vals)))
            except (KeyError, TypeError):
                row.append("n/a")
        lines += ["| " + " | ".join(row) + " |"]
    lines += [""]

    def family(title: str, pairs: list[tuple[str, str]]) -> None:
        # NB: append/extend only — `lines +=` would rebind and shadow the
        # closure variable (UnboundLocalError)
        lines.append(f"## {title}")
        lines.append("")
        if not pairs:
            lines.extend(["(none in this run)", ""])
            return
        lines.extend(
            [
                "| candidate | baseline | metric | median delta | 95% CI | verdict |",
                "|---|---|---|---|---|---|",
            ]
        )
        for cand, base in pairs:
            for path in HEADLINE_METRICS:
                try:
                    r: PairedResult = paired_compare(
                        path,
                        metric_series(results[cand], path),
                        metric_series(results[base], path),
                        stats_seed=stats_seed,
                    )
                except (KeyError, TypeError):
                    continue
                lines.append(
                    f"| {cand} | {base} | {path} | {_fmt(r.median_delta)} | "
                    f"[{_fmt(r.ci_lo)}, {_fmt(r.ci_hi)}] | {r.verdict()} |"
                )
        lines.append("")

    family("Ladder family — rung vs predecessor (R4 marginal deltas)", ladder_pairs)
    family("Baseline family — arm vs strong baseline (R5)", baseline_pairs)

    lines += [
        "## Gate A profile — unthresholded metrics on the naive arm",
        "",
        "The chair sets thresholds (or report-only status) for these before "
        "any R4 arm run; this profile is the informing input (D10).",
        "",
    ]
    rung0 = arms[0].name
    lines += ["| metric | median | min | max |", "|---|---|---|---|"]
    for path in GATE_A_METRICS:
        try:
            vals = sorted(v for v in metric_series(results[rung0], path).values())
            lines.append(
                f"| {path} | {_fmt(st.median(vals))} | {_fmt(vals[0])} | {_fmt(vals[-1])} |"
            )
        except (KeyError, TypeError):
            lines.append(f"| {path} | n/a | n/a | n/a |")
    lines += [
        "",
        "## Sensitivity",
        "",
        "(stub — populated by the P9 sweep: knee variants x Zipf s x retry "
        "policy x bot share. A win in one corner is not a win.)",
        "",
    ]
    return "\n".join(lines)
