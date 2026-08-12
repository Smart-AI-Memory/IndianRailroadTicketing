"""Open-loop intent generation (R3.1, R3.5, R3.8, R3.9, R3.10; task P2.1).

Intents are generated BEFORE the run from (config, fidelity, rng) only —
the function signature is the open-loop guarantee: no server state exists
to leak in. Users are classified by first arrival into exactly one cohort
(D10/C3): `pre_fire`, `t0_humans`, or `bots`. The retry-driven second wave
is a request-level phenomenon and never appears here.

Pre-fire semantics (P2.1 acceptance, elaborating the design matrix): a
pre-fire user POLLS before T0 — each poll is a real request answered
"not open" — and fires the real attempt at T0. The polling supplies the
pre-T0 request density the settling-time baseline window needs.

Toggles consulted: `t0_concentration` (off spreads T0 arrivals over a
wide window — the stampede becomes an ordinary load test), `zipf_demand`
(off = uniform across trains), `bot_cohort` (off = bots replaced by
t0-humans so total population is held constant across the comparison).
"""

from __future__ import annotations

from dataclasses import dataclass

from tatkal_sim.config import FidelityConfig
from tatkal_sim.core.rng import RngStreams

Pool = tuple[int, str, str]  # (train, class, date)


@dataclass(frozen=True)
class Intent:
    user_id: int
    pool: Pool
    cohort: str  # first-arrival cohort: pre_fire | t0_humans | bots
    t_arrival: float  # first request time (pre-fire: first pre-T0 poll)


@dataclass(frozen=True)
class WorkloadConfig:
    t0: float = 30.0  # opening instant; room before it for the baseline
    n_pre_fire: int = 30
    n_t0_humans: int = 215
    n_bots: int = 15
    sigma_t0: float = 0.35  # |N(0, sigma)| jitter after T0 (sub-second mass)
    bot_window: float = 0.05  # bots: uniform [T0, T0 + bot_window]
    pre_fire_window: float = 20.0  # pre-fire arrivals: uniform [T0 - w, T0)
    pre_fire_poll: float = 0.75  # pre-T0 poll interval (density source)
    spread_window: float = 60.0  # t0_concentration OFF: uniform over this
    # background cohort (D14): post-spike trickle so settling time is
    # measurable at all — without it the run ends with the spike and no
    # quiet interval can exist
    n_background: int = 60
    background_start: float = 2.0  # offsets after T0
    background_end: float = 32.0
    n_trains: int = 8
    zipf_s: float = 1.1
    classes: tuple[str, ...] = ("AC",)
    date: str = "D0"
    # bot behaviour family (P8, R7.1 circularity guard): the classifier is
    # TRAINED on one family and EVALUATED against the others, which it has
    # never seen. Arrival pattern per family; cadence via ClientConfig.
    #   sniper — uniform in the bot window right at T0 (the default)
    #   burst  — a tight volley a few ms after T0
    #   mimic  — human-shaped arrival jitter; only cadence differs
    bot_family: str = "sniper"


#: Operating workload — the SUPERCRITICAL realization of the ratified
#: C=256 operating point (chair amendment, decisions.md D14): the
#: "peak in-flight = 256 +/- 5%" target proved bistable-unsatisfiable, so
#: the binding check is in-flight >= 256 SUSTAINED >= 1 s at the
#: calibration-analogue conn ceiling (450). Verified on the real rung-0
#: fitted profile in tests/test_rungs.py.
OPERATING_WORKLOAD = WorkloadConfig(n_t0_humans=2500, n_bots=150)


def _zipf_weights(n: int, s: float) -> list[float]:
    return [1.0 / (rank**s) for rank in range(1, n + 1)]


def generate_intents(
    cfg: WorkloadConfig, fidelity: FidelityConfig, streams: RngStreams
) -> list[Intent]:
    """Deterministic intent schedule from (config, fidelity, seed) only."""
    arrivals = streams.get("arrivals")
    demand = streams.get("demand")

    n_bots = cfg.n_bots if fidelity.bot_cohort else 0
    n_humans = cfg.n_t0_humans + (0 if fidelity.bot_cohort else cfg.n_bots)

    weights = (
        _zipf_weights(cfg.n_trains, cfg.zipf_s) if fidelity.zipf_demand else [1.0] * cfg.n_trains
    )
    trains = list(range(1, cfg.n_trains + 1))

    def draw_pool() -> Pool:
        train = demand.choices(trains, weights=weights)[0]
        klass = demand.choice(cfg.classes)
        return (train, klass, cfg.date)

    intents: list[Intent] = []
    uid = 0

    # cohort generation order is fixed; per-user draw order is fixed —
    # both load-bearing for byte-identical traces (R1).
    for _ in range(cfg.n_pre_fire):
        t = cfg.t0 - arrivals.uniform(0.0, cfg.pre_fire_window)
        intents.append(Intent(uid, draw_pool(), "pre_fire", t))
        uid += 1

    for _ in range(n_humans):
        if fidelity.t0_concentration:
            t = cfg.t0 + abs(arrivals.gauss(0.0, cfg.sigma_t0))
        else:
            t = cfg.t0 + arrivals.uniform(0.0, cfg.spread_window)
        intents.append(Intent(uid, draw_pool(), "t0_humans", t))
        uid += 1

    for _ in range(n_bots):
        if cfg.bot_family == "sniper":
            t = cfg.t0 + arrivals.uniform(0.0, cfg.bot_window)
        elif cfg.bot_family == "burst":
            t = cfg.t0 + arrivals.uniform(0.005, 0.015)
        elif cfg.bot_family == "mimic":
            t = cfg.t0 + abs(arrivals.gauss(0.0, 0.2))  # human-shaped arrival
        else:
            raise ValueError(f"unknown bot_family: {cfg.bot_family}")
        intents.append(Intent(uid, draw_pool(), "bots", t))
        uid += 1

    for _ in range(cfg.n_background):
        t = cfg.t0 + arrivals.uniform(cfg.background_start, cfg.background_end)
        intents.append(Intent(uid, draw_pool(), "background", t))
        uid += 1

    intents.sort(key=lambda i: (i.t_arrival, i.user_id))
    return intents


def trace_digest(intents: list[Intent]) -> str:
    """Digest of the schedule — equality across arms proves trace reuse."""
    import hashlib

    return hashlib.sha256(
        repr([(i.user_id, i.pool, i.cohort, repr(i.t_arrival)) for i in intents]).encode()
    ).hexdigest()
