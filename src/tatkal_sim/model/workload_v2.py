"""v2 workload: identity structure and bot strategies (tatkal-v2 V1).

Extends the v1 open-loop guarantee unchanged: intents are generated
BEFORE the run from (config, fidelity, rng) only. v1's
`generate_intents` is untouched (the V0.2 anchor pins it); v2 arms use
`generate_intents_v2`.

Registered constants live in `V2WorkloadConfig` defaults and are
decision-entry-bound (decisions.md D13/D14): do not change them outside
a new entry.

Cohorts and strategies (D13.3):
- humans (pre_fire / t0_humans / background): one identity each,
  strategy "".
- bots: 150 split race/mimic/camp/identity-split = 60/30/30/30, with
  the degenerate-form rule applied per arm kind:
    camp           -> race outside M1/M3 (no window/tranche to camp)
    identity-split -> mimic outside M2   (no draw to multiply into)
- M2 abuse sweep (D13.4): n_split = round(p * n_bots) bots run
  identity-split; the conversion is mimic <-> identity-split ONLY
  (identity-split's degenerate form is mimic, so the two are the same
  bot under different arms). p = 0.2 therefore reproduces the base mix
  exactly (V1.4 acceptance); race and camp counts never vary with p.
- identity-split controllers hold m = 5 identities; each identity is a
  separate intent (mimic-shaped arrival) sharing the controller id.

M1 registration (D13.2/D13.6, D14.1): exactly round(r_reg * n) of the
(pre_fire + t0_humans) humans register, one-shot, uniform over
[T0 - W, T0); camp bots register in the first 5% of W. Walk-ups and
background never register.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from tatkal_sim.config import FidelityConfig
from tatkal_sim.core.rng import RngStreams
from tatkal_sim.model.workload import Intent, WorkloadConfig, _zipf_weights

ARM_KINDS = ("eng", "m1", "m2", "m3")

#: D13.3 base mix — never varies except mimic<->identity-split under p.
BASE_MIX = {"race": 60, "mimic": 30, "camp": 30, "identity_split": 30}


@dataclass(frozen=True)
class V2Intent(Intent):
    identity_id: int = -1
    controller_id: int = -1  # == user_id except for identity-split entries
    strategy: str = ""  # "" for humans; effective (post-degenerate) for bots
    t_register: float | None = None  # M1 registration instant, else None


@dataclass(frozen=True)
class V2WorkloadConfig(WorkloadConfig):
    # D14.1 windows
    reg_window: float = 300.0  # W (M1)
    qual_window: float = 5.0  # Q (M2)
    pace_tranches: int = 4  # k (M3)
    pace_horizon: float = 8.0  # H (M3)
    # D13.2 / D13.4
    r_reg: float = 0.8  # swept {0.5, 0.8, 0.95}
    abuse_p: float = 0.2  # swept {0, 0.1, 0.2, 0.4} in M2 cells
    m_identities: int = 5  # fixed (D13.4)


def _effective_strategy(base: str, arm_kind: str) -> str:
    """D13.3 degenerate-form rule."""
    if base == "camp" and arm_kind not in ("m1", "m3"):
        return "race"
    if base == "identity_split" and arm_kind != "m2":
        return "mimic"
    return base


def _strategy_counts(cfg: V2WorkloadConfig, arm_kind: str) -> dict[str, int]:
    """Base mix, with the M2 abuse sweep's mimic<->identity-split shift."""
    counts = dict(BASE_MIX)
    if arm_kind == "m2":
        n_split = round(cfg.abuse_p * cfg.n_bots)
        if n_split > BASE_MIX["identity_split"] + BASE_MIX["mimic"]:
            raise ValueError(f"abuse_p={cfg.abuse_p} exceeds mimic pool")
        counts["identity_split"] = n_split
        counts["mimic"] = BASE_MIX["mimic"] + (BASE_MIX["identity_split"] - n_split)
    return counts


def generate_intents_v2(
    cfg: V2WorkloadConfig,
    fidelity: FidelityConfig,
    streams: RngStreams,
    arm_kind: str,
) -> list[V2Intent]:
    """Deterministic v2 schedule from (config, fidelity, seed, arm_kind)."""
    if arm_kind not in ARM_KINDS:
        raise ValueError(f"unknown arm_kind: {arm_kind}")
    arrivals = streams.get("arrivals")
    demand = streams.get("demand")
    registration = streams.get("registration")  # own stream: v1 draws safe

    weights = (
        _zipf_weights(cfg.n_trains, cfg.zipf_s) if fidelity.zipf_demand else [1.0] * cfg.n_trains
    )
    trains = list(range(1, cfg.n_trains + 1))

    def draw_pool():
        train = demand.choices(trains, weights=weights)[0]
        klass = demand.choice(cfg.classes)
        return (train, klass, cfg.date)

    intents: list[V2Intent] = []
    uid = 0
    identity = 0

    def add(pool, cohort, t, *, strategy="", controller=None, t_register=None):
        nonlocal uid, identity
        intents.append(
            V2Intent(
                uid,
                pool,
                cohort,
                t,
                identity_id=identity,
                controller_id=controller if controller is not None else uid,
                strategy=strategy,
                t_register=t_register,
            )
        )
        uid += 1
        identity += 1

    # ---- humans: generation order fixed (R1), v1 cohort semantics ----
    human_slots: list[tuple[str, float]] = []
    for _ in range(cfg.n_pre_fire):
        human_slots.append(("pre_fire", cfg.t0 - arrivals.uniform(0.0, cfg.pre_fire_window)))
    n_bots = cfg.n_bots if fidelity.bot_cohort else 0
    n_humans = cfg.n_t0_humans + (0 if fidelity.bot_cohort else cfg.n_bots)
    for _ in range(n_humans):
        if fidelity.t0_concentration:
            t = cfg.t0 + abs(arrivals.gauss(0.0, cfg.sigma_t0))
        else:
            t = cfg.t0 + arrivals.uniform(0.0, cfg.spread_window)
        human_slots.append(("t0_humans", t))

    # M1: exactly round(r_reg * n) registrants among pre_fire + t0_humans
    reg_flags = [False] * len(human_slots)
    if arm_kind == "m1":
        n_reg = round(cfg.r_reg * len(human_slots))
        for idx in registration.sample(range(len(human_slots)), n_reg):
            reg_flags[idx] = True

    for (cohort, t), registered in zip(human_slots, reg_flags):
        t_reg = None
        if registered:
            t_reg = cfg.t0 - registration.uniform(0.0, cfg.reg_window)
        add(draw_pool(), cohort, t, t_register=t_reg)

    # ---- bots: D13.3 mix, strategy generation order fixed ----
    if n_bots:
        counts = _strategy_counts(cfg, arm_kind)
        assert sum(counts.values()) == cfg.n_bots
        for base in ("race", "mimic", "camp", "identity_split"):
            eff = _effective_strategy(base, arm_kind)
            for _ in range(counts[base]):
                if eff == "race":
                    t = cfg.t0 + arrivals.uniform(0.0, cfg.bot_window)
                    add(draw_pool(), "bots", t, strategy="race")
                elif eff == "mimic":
                    t = cfg.t0 + abs(arrivals.gauss(0.0, 0.2))
                    add(draw_pool(), "bots", t, strategy="mimic")
                elif eff == "camp":
                    # M1: registers in the first 5% of W (D13.3); fires at T0.
                    # M3: first arrival races tranche 1; per-tranche
                    # re-arrival is client behaviour (V3.3).
                    t = cfg.t0 + arrivals.uniform(0.0, cfg.bot_window)
                    t_reg = None
                    if arm_kind == "m1":
                        t_reg = (
                            cfg.t0
                            - cfg.reg_window
                            + registration.uniform(0.0, 0.05 * cfg.reg_window)
                        )
                    add(draw_pool(), "bots", t, strategy="camp", t_register=t_reg)
                else:  # identity_split (M2 only): m entries, one controller
                    controller = uid
                    pool = draw_pool()
                    for _ in range(cfg.m_identities):
                        t = cfg.t0 + abs(arrivals.gauss(0.0, 0.2))
                        add(pool, "bots", t, strategy="identity_split", controller=controller)

    # ---- background: v1 semantics, never registers ----
    for _ in range(cfg.n_background):
        t = cfg.t0 + arrivals.uniform(cfg.background_start, cfg.background_end)
        add(draw_pool(), "background", t)

    intents.sort(key=lambda i: (i.t_arrival, i.user_id))
    return intents


#: Operating v2 workload — D13 population over the v1 D14 operating scale.
OPERATING_WORKLOAD_V2 = V2WorkloadConfig(n_t0_humans=2500, n_bots=150)


def with_uptake(cfg: V2WorkloadConfig, r_reg: float) -> V2WorkloadConfig:
    return replace(cfg, r_reg=r_reg)


def with_abuse(cfg: V2WorkloadConfig, p: float) -> V2WorkloadConfig:
    return replace(cfg, abuse_p=p)
