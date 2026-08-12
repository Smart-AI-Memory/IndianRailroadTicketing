"""P2.3 acceptance — direction-of-effect for the six workload-side toggles.

Each test asserts the design table's documented direction as a measurable
delta at fixed seeds (D10/C4) — never an impossibility claim. Server-side
toggles (3.3, 3.4, 3.6, 3.7) are P3.5's job.
"""

from tatkal_sim.config import FidelityConfig
from tatkal_sim.model.users import (
    peak_in_flight,
    peak_rate,
    retry_amplification,
    total_requests,
    winners_by_cohort,
)
from tatkal_sim.model.workload import OPERATING_WORKLOAD, WorkloadConfig
from tests.conftest import StubService, run_world

SEED = 20260811
SMALL = WorkloadConfig(n_pre_fire=10, n_t0_humans=60, n_bots=6)


def slow_service(c, q, wc):
    return StubService(c, q, wc.t0, delay=1.5)


def silent_service(c, q, wc):
    return StubService(c, q, wc.t0, silent=True)


def world(fid, factory=slow_service, wcfg=OPERATING_WORKLOAD):
    return run_world(seed=SEED, fidelity=fid, wcfg=wcfg, service_factory=factory)


# R3.1 — open-loop arrivals
def test_closed_loop_self_throttles_offered_load():
    on = world(FidelityConfig())
    off = world(FidelityConfig(open_loop_arrivals=False))
    assert peak_in_flight(off.engine.log) <= 40  # gated at K=32 (+ poll noise)
    assert peak_in_flight(on.engine.log) >= 5 * peak_in_flight(off.engine.log)
    assert peak_rate(off.engine.log) < peak_rate(on.engine.log)


# R3.2 — retry amplification
def test_retries_raise_offered_load_under_failure():
    on = world(FidelityConfig(), factory=silent_service, wcfg=SMALL)
    off = world(FidelityConfig(retries_enabled=False), factory=silent_service, wcfg=SMALL)
    assert total_requests(on.engine.log) > 2 * total_requests(off.engine.log)


# R3.5 — T0 concentration
def test_spreading_arrivals_kills_the_spike():
    on = world(FidelityConfig())
    off = world(FidelityConfig(t0_concentration=False))
    assert peak_in_flight(off.engine.log) < 0.3 * peak_in_flight(on.engine.log)


# R3.8 — Zipf demand
def test_uniform_demand_deletes_the_hot_key():
    def hot_share(w):
        pools = [i.pool[0] for i in w.intents]
        return pools.count(1) / len(pools)

    on = world(FidelityConfig())
    off = world(FidelityConfig(zipf_demand=False))
    assert hot_share(on) > hot_share(off) + 0.10


# R3.9 — bot cohort
def test_bots_win_disproportionately_under_scarcity():
    # capacity 100: the pre-fire cohort's T0 re-fires legitimately take the
    # first ~30 seats (pre-firing converts to seats); with 40 the contest
    # would be over before the bot window's tighter timing can show at all.
    # Pinned to the original 260-user shape: the direction claim is
    # scale-independent, and the D14 supercritical OPERATING would need
    # retuned capacity for no extra signal.
    w = world(
        FidelityConfig(),
        factory=lambda c, q, wc: StubService(c, q, wc.t0, delay=0.05, capacity=100),
        wcfg=WorkloadConfig(n_pre_fire=30, n_t0_humans=215, n_bots=15, n_background=0),
    )
    wins = winners_by_cohort(w.engine.log, w.intents)
    n = len(w.intents)
    bots_n = sum(1 for i in w.intents if i.cohort == "bots")
    total_wins = sum(wins.values())
    win_share = wins.get("bots", 0) / total_wins
    pop_share = bots_n / n
    assert win_share > 2 * pop_share  # tighter timing converts to seats


# R3.10 — user identity
def test_identity_off_hides_retry_amplification():
    w = world(FidelityConfig(), factory=silent_service, wcfg=SMALL)
    n_users = len(w.intents)
    amp_on = retry_amplification(w.engine.log, n_users, identity_on=True)
    amp_off = retry_amplification(w.engine.log, n_users, identity_on=False)
    assert amp_on > 2.0  # the storm is real...
    assert amp_off == 1.0  # ...and identity-off cannot see it
