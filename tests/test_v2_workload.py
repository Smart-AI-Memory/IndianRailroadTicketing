"""V1 acceptance (tatkal-v2 tasks.md V1.1-V1.4)."""

import hashlib
from collections import Counter

from tatkal_sim.config import FidelityConfig
from tatkal_sim.core.rng import RngStreams
from tatkal_sim.model.workload_v2 import (
    BASE_MIX,
    OPERATING_WORKLOAD_V2,
    V2WorkloadConfig,
    generate_intents_v2,
    with_abuse,
    with_uptake,
)

FID = FidelityConfig()


def gen(arm_kind, cfg=OPERATING_WORKLOAD_V2, seed=0):
    return generate_intents_v2(cfg, FID, RngStreams(seed), arm_kind)


def digest(intents):
    return hashlib.sha256(
        repr(
            [
                (
                    i.user_id,
                    i.identity_id,
                    i.controller_id,
                    i.pool,
                    i.cohort,
                    i.strategy,
                    repr(i.t_arrival),
                    repr(i.t_register),
                )
                for i in intents
            ]
        ).encode()
    ).hexdigest()


# ---------------------------------------------------------------- V1.1
def test_identity_structure_controller_rollup():
    intents = gen("m2", with_abuse(OPERATING_WORKLOAD_V2, 0.2))
    split = [i for i in intents if i.strategy == "identity_split"]
    controllers = {i.controller_id for i in split}
    assert len(controllers) == 30  # 30 abusers
    assert len(split) == 150  # 5 identities each
    for c in controllers:
        assert sum(1 for i in split if i.controller_id == c) == 5
    # humans: identity 1:1, controller == self
    humans = [i for i in intents if i.cohort != "bots"]
    assert all(i.controller_id == i.user_id for i in humans)
    assert len({i.identity_id for i in intents}) == len(intents)  # identities unique


# ---------------------------------------------------------------- V1.2
def test_m1_registration_counts_exact():
    for r in (0.5, 0.8, 0.95):
        intents = gen("m1", with_uptake(OPERATING_WORKLOAD_V2, r))
        eligible = [i for i in intents if i.cohort in ("pre_fire", "t0_humans")]
        registered = [i for i in eligible if i.t_register is not None]
        assert len(registered) == round(r * len(eligible))
        cfg = OPERATING_WORKLOAD_V2
        for i in registered:
            assert cfg.t0 - cfg.reg_window <= i.t_register < cfg.t0
    # background and walk-ups never register
    bg = [i for i in gen("m1") if i.cohort == "background"]
    assert all(i.t_register is None for i in bg)


def test_camp_bots_register_front_of_window_in_m1():
    cfg = OPERATING_WORKLOAD_V2
    camp = [i for i in gen("m1") if i.strategy == "camp"]
    assert len(camp) == BASE_MIX["camp"]
    start = cfg.t0 - cfg.reg_window
    for i in camp:
        assert i.t_register is not None
        assert start <= i.t_register <= start + 0.05 * cfg.reg_window


# ---------------------------------------------------------------- V1.3
def test_composition_and_degenerate_forms():
    # eng: camp->race, identity_split->mimic
    c = Counter(i.strategy for i in gen("eng") if i.cohort == "bots")
    assert c == {"race": 90, "mimic": 60}
    # m1: camp real, identity_split->mimic
    c = Counter(i.strategy for i in gen("m1") if i.cohort == "bots")
    assert c == {"race": 60, "mimic": 60, "camp": 30}
    # m3: camp real, identity_split->mimic
    c = Counter(i.strategy for i in gen("m3") if i.cohort == "bots")
    assert c == {"race": 60, "mimic": 60, "camp": 30}
    # m2 at center: full base mix, split entries = 30 controllers x 5
    intents = gen("m2", with_abuse(OPERATING_WORKLOAD_V2, 0.2))
    bots = [i for i in intents if i.cohort == "bots"]
    controllers = Counter()
    for i in bots:
        if i.strategy == "identity_split":
            controllers[i.controller_id] = 1
    c = Counter(i.strategy for i in bots)
    # camp -> race in m2 (no window to camp): race = 60 + 30
    assert c["race"] == 90 and c["mimic"] == 30 and c["camp"] == 0
    assert sum(controllers.values()) == 30


def test_bot_cohort_off_replacement_carries():
    fid = FidelityConfig(bot_cohort=False)
    intents = generate_intents_v2(OPERATING_WORKLOAD_V2, fid, RngStreams(0), "eng")
    assert not [i for i in intents if i.cohort == "bots"]
    humans = [i for i in intents if i.cohort == "t0_humans"]
    assert len(humans) == OPERATING_WORKLOAD_V2.n_t0_humans + OPERATING_WORKLOAD_V2.n_bots


# ---------------------------------------------------------------- V1.4
def test_abuse_center_cell_is_base_mix():
    a = gen("m2", with_abuse(OPERATING_WORKLOAD_V2, 0.2))
    b = gen("m2", OPERATING_WORKLOAD_V2)  # default abuse_p = 0.2
    assert digest(a) == digest(b)


def test_abuse_sweep_counts():
    for p, n_split_controllers, n_mimic in (
        (0.0, 0, 60),
        (0.1, 15, 45),
        (0.2, 30, 30),
        (0.4, 60, 0),
    ):
        intents = gen("m2", with_abuse(OPERATING_WORKLOAD_V2, p))
        bots = [i for i in intents if i.cohort == "bots"]
        c = Counter(i.strategy for i in bots)
        assert len({i.controller_id for i in bots if i.strategy == "identity_split"}) == (
            n_split_controllers
        )
        assert c["mimic"] == n_mimic
        assert c["race"] == 90  # race (incl. degenerate camp) never varies with p


# ------------------------------------------------- open-loop determinism
def test_open_loop_determinism():
    for kind in ("eng", "m1", "m2", "m3"):
        assert digest(gen(kind, seed=7)) == digest(gen(kind, seed=7))
        assert digest(gen(kind, seed=7)) != digest(gen(kind, seed=8))


def test_v1_generator_untouched_by_v2_import():
    """The registration stream is v2-only; v1 draws stay anchored."""
    from tatkal_sim.model.workload import OPERATING_WORKLOAD, generate_intents, trace_digest

    d = trace_digest(generate_intents(OPERATING_WORKLOAD, FID, RngStreams(0)))
    gen("m1")  # exercise v2 generation
    assert trace_digest(generate_intents(OPERATING_WORKLOAD, FID, RngStreams(0))) == d


def test_small_config_scales():
    small = V2WorkloadConfig()  # 215 humans, 15 bots — mix must scale? No:
    # BASE_MIX is absolute (150); small configs must override n_bots via mix.
    # Guard: mismatched n_bots fails loudly rather than silently mis-mixing.
    import pytest

    with pytest.raises(AssertionError):
        generate_intents_v2(small, FID, RngStreams(0), "eng")
