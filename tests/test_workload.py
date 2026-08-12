"""P2.1 acceptance — open-loop generator: purity, cohorts, Zipf, C=256, density."""

from tatkal_sim.config import FidelityConfig
from tatkal_sim.core import RngStreams
from tatkal_sim.model.users import requests_in_window
from tatkal_sim.model.workload import (
    OPERATING_WORKLOAD,
    generate_intents,
    trace_digest,
)
from tests.conftest import run_world

FID = FidelityConfig()


def gen(seed=1, fid=FID, cfg=OPERATING_WORKLOAD):
    return generate_intents(cfg, fid, RngStreams(seed))


def test_schedule_is_pure_and_byte_identical():
    """Same (config, fidelity, seed) -> identical trace. No server input
    exists in the signature — open-loop by construction (R3.1)."""
    assert trace_digest(gen(seed=7)) == trace_digest(gen(seed=7))
    assert trace_digest(gen(seed=7)) != trace_digest(gen(seed=8))


def test_cohort_timing_matches_config():
    cfg = OPERATING_WORKLOAD
    intents = gen()
    by = lambda c: [i for i in intents if i.cohort == c]  # noqa: E731
    assert all(cfg.t0 - cfg.pre_fire_window <= i.t_arrival < cfg.t0 for i in by("pre_fire"))
    assert all(cfg.t0 <= i.t_arrival <= cfg.t0 + cfg.bot_window for i in by("bots"))
    humans = by("t0_humans")
    assert all(i.t_arrival >= cfg.t0 for i in humans)
    within_1s = sum(1 for i in humans if i.t_arrival <= cfg.t0 + 1.0)
    assert within_1s / len(humans) > 0.95  # sub-second concentration (R3.5)


def test_bot_cohort_off_holds_population_constant():
    on, off = gen(fid=FID), gen(fid=FidelityConfig(bot_cohort=False))
    assert len(on) == len(off)
    assert not [i for i in off if i.cohort == "bots"]


def test_zipf_concentrates_demand_on_hot_train():
    intents = gen()
    hot = sum(1 for i in intents if i.pool[0] == 1) / len(intents)
    uni = gen(fid=FidelityConfig(zipf_demand=False))
    hot_uni = sum(1 for i in uni if i.pool[0] == 1) / len(uni)
    assert hot > hot_uni + 0.10  # R3.8 direction, asserted again in P2.3


def test_background_cohort_arrives_after_the_spike():
    """D14: the background trickle exists so settling time is measurable;
    it arrives strictly inside [T0+start, T0+end]."""
    cfg = OPERATING_WORKLOAD
    bg = [i for i in gen() if i.cohort == "background"]
    assert len(bg) == cfg.n_background
    assert all(
        cfg.t0 + cfg.background_start <= i.t_arrival <= cfg.t0 + cfg.background_end for i in bg
    )


# NOTE: the stub-based "peak in-flight = 256 +/- 5%" check that lived here
# was SUPERSEDED by chair amendment D14 (the target is bistable-
# unsatisfiable on the fitted profile). The binding operating-point check
# — in-flight >= 256 sustained >= 1 s on real rung 0 — is
# tests/test_rungs.py::test_binding_operating_point_supercritical.


def test_pre_t0_density_supports_settling_baseline():
    """The settling-time baseline window (ending 10 s before T0) needs
    enough requests for a windowed percentile — pre-fire polling supplies
    them (P2.1 acceptance)."""
    w = run_world(seed=1, wcfg=OPERATING_WORKLOAD)
    t0 = OPERATING_WORKLOAD.t0
    assert requests_in_window(w.engine.log, t0 - 11.0, t0 - 10.0) >= 10


def test_intents_sorted_and_ids_unique():
    intents = gen()
    times = [i.t_arrival for i in intents]
    assert times == sorted(times)
    assert len({i.user_id for i in intents}) == len(intents)
