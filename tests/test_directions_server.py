"""P3.5 acceptance — direction-of-effect for the four server-side toggles.

Measurable directional deltas at fixed seeds (D10/C4), per the design
table: 3.3 bounded capacity, 3.4 atomic inventory, 3.6 wasted work,
3.7 heavy-tailed service.
"""

from tatkal_sim.config import FidelityConfig
from tatkal_sim.model.server import ServerConfig
from tatkal_sim.model.users import ClientConfig
from tatkal_sim.model.workload import WorkloadConfig
from tests.helpers_server import manual_batch, pct, server_world

NO_TAIL = FidelityConfig(heavy_tail_service=False)
OVERLOAD = ServerConfig(workers=4, accept_queue=16, conn_limit=64)


# R3.3 — bounded capacity (ablation-only when off)
def test_unbounded_backend_erases_overload_signals():
    # unique pools + sharded: no lock contention, so the comparison isolates
    # WORKER queueing — the thing this toggle ablates (the lock is R3.4's)
    scfg = ServerConfig(
        workers=4,
        accept_queue=16,
        conn_limit=64,
        app_mu=-3.0,  # ~50 ms service so worker queueing is visible
        app_sigma=0.1,
        sharded=True,
        seats_per_pool=1000,
    )
    pool_of = lambda i: (i, "AC", "D0")  # noqa: E731

    def booked_lat(lat, out):
        return [t for t, o in zip(lat, out) if o == "booked"]

    on_lat, on_out, on_srv = manual_batch(200, scfg=scfg, fidelity=NO_TAIL, pool_of=pool_of)
    off_lat, off_out, off_srv = manual_batch(
        200,
        scfg=scfg,
        fidelity=FidelityConfig(bounded_capacity=False, heavy_tail_service=False),
        pool_of=pool_of,
    )
    assert on_srv.hard_errors_conn + on_srv.hard_errors_queue > 0
    assert off_srv.hard_errors_conn + off_srv.hard_errors_queue == 0
    assert "hard_error" not in off_out
    # served-request latency: worker queue delay vanishes when capacity is infinite
    assert pct(booked_lat(off_lat, off_out), 0.95) < 0.5 * pct(booked_lat(on_lat, on_out), 0.95)


# R3.4 — atomic inventory
def test_atomicity_off_produces_double_sells():
    fid = FidelityConfig(atomic_inventory=False, heavy_tail_service=False)
    scfg = ServerConfig(
        workers=64,
        accept_queue=1000,
        conn_limit=1000,
        app_mu=-11.5,
        app_sigma=0.0,
        lock_hold=0.01,
        seats_per_pool=5,
    )
    _, outcomes, srv = manual_batch(40, scfg=scfg, fidelity=fid)
    assert outcomes.count("booked") > 5  # more bookings than seats existed
    assert any("double-sell" in v or "!=" in v for v in srv.inventory.violations())
    # control: atomic path with identical load stays clean
    _, outcomes_on, srv_on = manual_batch(40, scfg=scfg, fidelity=NO_TAIL)
    assert outcomes_on.count("booked") == 5
    assert srv_on.inventory.violations() == []


# R3.6 — wasted work
def test_wasted_work_starves_goodput_under_overload():
    """Overloaded server, impatient clients: with wasted work ON the queue
    is full of requests whose clients already left, and the server burns
    capacity answering ghosts; OFF (the flattering lie) sheds them and
    goodput recovers. Direction: booked-definitives fall when ON."""
    wcfg = WorkloadConfig(n_pre_fire=0, n_t0_humans=80, n_bots=0)
    ccfg = ClientConfig(timeout_s=1.0, max_attempts=3, patience_mean=6.0)
    scfg = ServerConfig(
        workers=2,
        accept_queue=200,
        conn_limit=500,
        app_mu=-1.6,  # ~0.2 s service: capacity 10/s vs an 80-user burst
        app_sigma=0.1,
        seats_per_pool=1000,
        assumed_client_timeout=1.0,
    )

    def run(fid):
        _, engine, srv = server_world(seed=5, fidelity=fid, wcfg=wcfg, ccfg=ccfg, scfg=scfg)
        booked = sum(1 for e in engine.log if e[0] == "definitive" and e[3] == "booked")
        return booked, srv.busy_seconds

    on_booked, on_busy = run(FidelityConfig(heavy_tail_service=False))
    off_booked, off_busy = run(FidelityConfig(wasted_work=False, heavy_tail_service=False))
    assert off_booked > on_booked  # ghosts starve live users of goodput
    assert on_busy > 3.0 * off_busy  # ...while burning multiples of capacity


# R3.7 — heavy-tailed service
def test_heavy_tail_raises_p99_over_p50():
    # unique pools + sharded + ample workers: zero contention, so latency
    # IS app_time and the mixture component is what p99/p50 sees
    scfg = ServerConfig(
        workers=300,
        accept_queue=1000,
        conn_limit=1000,
        seats_per_pool=1000,
        sharded=True,
        tail_p=0.05,
    )

    def ratio(fid, seed=3):
        lat, _, _ = manual_batch(
            200, scfg=scfg, fidelity=fid, seed=seed, pool_of=lambda i: (i, "AC", "D0")
        )
        return pct(lat, 0.99) / pct(lat, 0.50)

    assert ratio(FidelityConfig()) > 3.0 * ratio(NO_TAIL)
