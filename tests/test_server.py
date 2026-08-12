"""P3.1-P3.3 acceptance — bounds, emergent lock queueing, inventory invariants."""

import pytest

from tatkal_sim.config import FidelityConfig
from tatkal_sim.model.server import ServerConfig
from tatkal_sim.model.users import Outcome
from tests.helpers_server import T0, manual_batch, pct, server_world

NO_TAIL = FidelityConfig(heavy_tail_service=False)


# -- P3.1: all three bounds, degradation, pre-T0 -----------------------------
def test_conn_limit_produces_hard_errors():
    _, outcomes, srv = manual_batch(
        30, scfg=ServerConfig(workers=2, accept_queue=100, conn_limit=10)
    )
    assert srv.hard_errors_conn == 20  # 10 admitted, 20 reset at the door
    assert outcomes.count("hard_error") == 20


def test_accept_queue_overflow_drops_newest_as_hard_error():
    _, outcomes, srv = manual_batch(
        30, scfg=ServerConfig(workers=2, accept_queue=8, conn_limit=1000)
    )
    assert srv.hard_errors_queue == 30 - 2 - 8
    assert outcomes.count("hard_error") == srv.hard_errors_queue


def test_no_infinite_elasticity_latency_grows_past_capacity():
    scfg = ServerConfig(workers=4, accept_queue=1000, conn_limit=1000)
    lat_small, _, _ = manual_batch(4, scfg=scfg, fidelity=NO_TAIL)
    lat_big, _, _ = manual_batch(64, scfg=scfg, fidelity=NO_TAIL)
    assert pct(lat_big, 0.95) > 4 * pct(lat_small, 0.95)  # queueing is real


def test_pre_t0_requests_get_not_open_and_no_inventory_moves():
    lat, outcomes, srv = manual_batch(10, at=T0 - 5.0)
    assert set(outcomes) == {Outcome.NOT_OPEN.value}
    assert srv.inventory.first_decrement_t is None
    assert srv.inventory.totals()["sold"] == 0


def test_pre_t0_decrement_raises_hard():
    _, _, srv = manual_batch(1)  # post-T0 world, then abuse the API directly
    with pytest.raises(RuntimeError, match="before T0"):
        srv.inventory.try_book((1, "AC", "D0"), T0 - 1.0)


def test_full_world_zero_decrements_before_t0():
    _, engine, srv = server_world(scfg=ServerConfig(seats_per_pool=1000))
    assert srv.inventory.first_decrement_t is not None
    assert srv.inventory.first_decrement_t >= T0


# -- P3.2: lock_wait emergent — p99 ~ queue-depth x hold ---------------------
def test_hot_key_tail_is_queue_depth_times_hold():
    """N contenders, workers ample, app_time negligible+deterministic,
    heavy tail pinned OFF (task acceptance): the i-th grant completes at
    ~i x lock_hold, so p99 ~ 0.99N x hold. Emergent, not drawn."""
    n, hold = 50, 0.01
    scfg = ServerConfig(
        workers=64,
        accept_queue=1000,
        conn_limit=1000,
        app_mu=-11.5,  # ~1e-5 s: negligible
        app_sigma=0.0,  # deterministic
        lock_hold=hold,
        seats_per_pool=1000,
    )
    lat, outcomes, _ = manual_batch(n, scfg=scfg, fidelity=NO_TAIL)
    assert outcomes.count("booked") == n
    expected = 0.99 * n * hold
    assert expected * 0.8 <= pct(lat, 0.99) <= expected * 1.2
    # and the median waits about half the queue: fair FIFO, not a lottery
    assert 0.3 * n * hold <= pct(lat, 0.50) <= 0.7 * n * hold


def test_sharded_locks_do_not_block_each_other():
    n, hold = 40, 0.01
    scfg = ServerConfig(
        workers=64,
        accept_queue=1000,
        conn_limit=1000,
        app_mu=-11.5,
        app_sigma=0.0,
        lock_hold=hold,
        seats_per_pool=1000,
    )
    # all on one pool vs spread over 8 pools (sharded=True)
    hot, _, _ = manual_batch(n, scfg=scfg, fidelity=NO_TAIL)
    spread, _, _ = manual_batch(
        n,
        scfg=ServerConfig(**{**scfg.__dict__, "sharded": True}),
        fidelity=NO_TAIL,
        pool_of=lambda i: (1 + i % 8, "AC", "D0"),
    )
    # 8 independent queues of depth n/8: tail shrinks ~8x (calibration
    # sharded8 control's direction)
    assert pct(spread, 0.99) < 0.3 * pct(hot, 0.99)


# -- P3.3: invariants --------------------------------------------------------
def test_invariants_hold_on_a_full_run():
    _, engine, srv = server_world(scfg=ServerConfig(seats_per_pool=20))
    assert srv.inventory.violations() == []
    srv.inventory.assert_ok()
    totals = srv.inventory.totals()
    assert totals["sold"] + totals["remaining"] == totals["initial"]
    assert totals["sold"] > 0  # scarcity actually bit: hot pool sold out


def test_nonatomic_toggle_breaks_invariants():
    fid = FidelityConfig(atomic_inventory=False, heavy_tail_service=False)
    scfg = ServerConfig(
        workers=64,
        accept_queue=1000,
        conn_limit=1000,
        app_mu=-11.5,
        app_sigma=0.0,
        lock_hold=0.01,
        seats_per_pool=10,
    )
    _, outcomes, srv = manual_batch(40, scfg=scfg, fidelity=fid)
    assert srv.inventory.violations()  # lost updates / oversell detected
    with pytest.raises(AssertionError):
        srv.inventory.assert_ok()


# -- P3 exit: unmitigated end-to-end at operating load -----------------------
def test_operating_load_end_to_end_rung0_shaped():
    """No admission layer = rung-0-shaped. Every user must end resolved
    (definitive or abandon), invariants must hold, and the run is
    laptop-trivial (the sweep-scale requirement follows)."""
    from tatkal_sim.model.workload import OPERATING_WORKLOAD

    intents, engine, srv = server_world(
        seed=1, wcfg=OPERATING_WORKLOAD, scfg=ServerConfig(workers=8, seats_per_pool=10)
    )
    srv.inventory.assert_ok()
    resolved = {e[2] for e in engine.log if e[0] in ("definitive", "abandon")}
    assert resolved == {i.user_id for i in intents}  # nobody left dangling
    booked = sum(1 for e in engine.log if e[0] == "definitive" and e[3] == "booked")
    assert 0 < booked <= srv.inventory.totals()["initial"]
