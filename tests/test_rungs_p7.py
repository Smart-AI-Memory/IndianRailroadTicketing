"""P7 acceptance — rungs 3-5: sharding direction, waiting room + eviction,
status stream, adaptive limiter stability."""

from tatkal_sim.measure.metrics import r8_status_stream
from tatkal_sim.model.users import Outcome
from tatkal_sim.runner import ladder_arm, run_arm_once


def metrics_and_log(arm, seed=1):
    """run_arm_once returns metrics only; re-run capturing the log too."""
    from tatkal_sim.core import Clock, EventQueue, RngStreams
    from tatkal_sim.model.server import Server
    from tatkal_sim.model.users import ClientEngine
    from tatkal_sim.model.workload import generate_intents
    from tatkal_sim.strategies.base import build_rung

    clock = Clock()
    queue = EventQueue(clock)
    streams = RngStreams(seed)
    intents = generate_intents(arm.wcfg, arm.fidelity, streams)
    log: list = []
    server = Server(clock, queue, streams, arm.fidelity, arm.scfg, arm.wcfg.t0, log=log)
    service = build_rung(arm.rung, server, clock, queue, getattr(arm, 'rung_params', None))
    engine = ClientEngine(clock, queue, streams, arm.fidelity, arm.ccfg, arm.wcfg, service, log=log)
    layer = service
    while layer is not server:
        if hasattr(layer, "bind_push"):
            layer.bind_push(engine.push_definitive)
        layer = getattr(layer, "inner", server)
    engine.start(intents)
    queue.run(max_events=5_000_000)
    server.inventory.assert_ok()
    return engine, server, log, intents


# -- P7.1: sharding ----------------------------------------------------------
def test_rung3_sharding_not_worse_and_direction_consistent():
    """The calibration sharded8 control (p99 halves at equal throughput)
    fixes the direction; in the Zipf experiment the hot pool still
    dominates the tail, so the assertion is 'no material regression'."""
    r2 = run_arm_once(ladder_arm(2), seed=1)
    r3 = run_arm_once(ladder_arm(3), seed=1)
    assert r3["resolution"]["winners"]["p99"] <= r2["resolution"]["winners"]["p99"] * 1.3
    assert r3["goodput"]["sold_per_s"] >= r2["goodput"]["sold_per_s"] * 0.8


# -- P7.2: waiting room ------------------------------------------------------
def test_rung4_everyone_resolved_and_eviction_immediate():
    engine, server, log, intents = metrics_and_log(ladder_arm(4))
    definitive = {e[2] for e in log if e[0] == "definitive"}
    abandoned = {e[2] for e in log if e[0] == "abandon"}
    assert definitive | abandoned == {i.user_id for i in intents}
    assert not abandoned  # push delivery: nobody left to give up
    # eviction acceptance: every user who ARRIVED before sell-out resolves
    # within ~an edge answer of it (queued tokens are pushed sold-out at
    # eviction); later arrivals (background cohort) resolve on arrival
    sellout = max(e[1] for e in log if e[0] == "sold")
    first_req = {}
    for e in log:
        if e[0] == "request" and e[2] not in first_req:
            first_req[e[2]] = e[1]
    late = [
        e
        for e in log
        if e[0] == "definitive" and first_req[e[2]] <= sellout and e[1] > sellout + 0.5
    ]
    assert not late, f"{len(late)} pre-sellout users resolved late"


def test_rung4_status_stream_exists_and_is_evaluated():
    # scarcity config: eviction is near-instant, so status load is light —
    # the machinery must still measure and evaluate it
    _, _, log, _ = metrics_and_log(ladder_arm(4))
    r8 = r8_status_stream(log)
    assert r8["status_requests"] > 100
    assert 0.0 < r8["status_busy_share"] < 1.0
    assert r8["status_p99_wait_s"] is not None
    assert isinstance(r8["status_is_new_bottleneck"], bool)


def test_rung4_drain_heavy_config_produces_a_real_polling_storm():
    """R8's stressor: abundant inventory means the queue drains for real
    (~1.6 s), tokens wait, and fast polling becomes serious load."""
    from tatkal_sim.model.users import ClientConfig

    arm = ladder_arm(4, seats=400, ccfg=ClientConfig(poll_interval=0.25))
    _, _, log, _ = metrics_and_log(arm)
    r8 = r8_status_stream(log)
    assert r8["status_requests"] > 1000
    assert r8["status_busy_share"] > 0.05


def test_rung4_rejected_resolution_beats_polling_cadence():
    """Push eviction: rejected users learn their fate far faster than the
    1 s poll interval — the D10 requirement that made rung 4 viable."""
    m = run_arm_once(ladder_arm(4), seed=1)
    assert m["resolution"]["rejected"]["p99"] < 0.5


# -- P7.3: adaptive limiter --------------------------------------------------
def test_rung5_stable_across_knee_variants():
    for variant in ("fitted", "plateau", "cliff"):
        m = run_arm_once(ladder_arm(5, variant=variant), seed=1)
        assert m["inventory"]["violations"] == []
        assert m["goodput"]["sellout_reached"], variant
        assert m["ttda"]["winners"]["n"] > 0


def test_rung5_limiter_converges_to_a_sane_band():
    from tatkal_sim.core import Clock, EventQueue, RngStreams
    from tatkal_sim.model.server import Server
    from tatkal_sim.model.users import ClientEngine
    from tatkal_sim.model.workload import generate_intents
    from tatkal_sim.strategies.base import build_rung

    arm = ladder_arm(5)
    clock = Clock()
    queue = EventQueue(clock)
    streams = RngStreams(1)
    intents = generate_intents(arm.wcfg, arm.fidelity, streams)
    log: list = []
    server = Server(clock, queue, streams, arm.fidelity, arm.scfg, arm.wcfg.t0, log=log)
    service = build_rung(arm.rung, server, clock, queue, getattr(arm, 'rung_params', None))
    engine = ClientEngine(clock, queue, streams, arm.fidelity, arm.ccfg, arm.wcfg, service, log=log)
    layer = service
    limiter = None
    while layer is not server:
        if type(layer).__name__ == "AdaptiveLimit":
            limiter = layer
        if hasattr(layer, "bind_push"):
            layer.bind_push(engine.push_definitive)
        layer = getattr(layer, "inner", server)
    assert limiter is not None
    engine.start(intents)
    queue.run(max_events=5_000_000)
    assert 1.0 <= limiter.limit <= 64.0  # neither collapse nor runaway


# -- push delivery unit ------------------------------------------------------
def test_push_definitive_is_idempotent_and_stales_open_attempts():
    from tatkal_sim.config import FidelityConfig
    from tatkal_sim.core import Clock, EventQueue, RngStreams
    from tatkal_sim.model.users import ClientConfig, ClientEngine
    from tatkal_sim.model.workload import Intent, WorkloadConfig

    class Silent:
        def submit(self, uid, pool, respond):
            pass  # never answers

    wcfg = WorkloadConfig()
    clock = Clock()
    queue = EventQueue(clock)
    eng = ClientEngine(
        clock, queue, RngStreams(1), FidelityConfig(), ClientConfig(), wcfg, Silent()
    )
    eng.start([Intent(0, (1, "AC", "D0"), "t0_humans", wcfg.t0)])
    queue.run(until=wcfg.t0 + 0.5)  # request now open, unanswered
    eng.push_definitive(0, Outcome.BOOKED)
    eng.push_definitive(0, Outcome.SOLD_OUT)  # second push must be a no-op
    queue.run()
    definitive = [e for e in eng.log if e[0] == "definitive"]
    assert len(definitive) == 1 and definitive[0][3] == "booked"
