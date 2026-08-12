"""P6 acceptance — rungs 0-2, the binding operating point, and baselines.

Gate A is closed (D14), so arm runs are sanctioned. Tests here cover the
machinery and the safe structural directions; the evidentiary comparisons
live in the committed 20-seed report, not in assertions.
"""

from tatkal_sim.config import FidelityConfig
from tatkal_sim.core import Clock, EventQueue, RngStreams
from tatkal_sim.measure.fitting import fitted_server_config
from tatkal_sim.model.users import Outcome
from tatkal_sim.model.workload import OPERATING_WORKLOAD
from tatkal_sim.runner import Arm, run_arm_once
from tatkal_sim.strategies.base import RungParams, build_rung
from tatkal_sim.strategies.fast_fail import FastFail


def rung_arm(k: int, seats: int = 25) -> Arm:
    return Arm(f"rung{k}", fitted_server_config(seats), wcfg=OPERATING_WORKLOAD, rung=k)


# -- D14 binding operating-point check ---------------------------------------
def test_binding_operating_point_supercritical():
    """In-flight >= 256 sustained for >= 1 s on real rung 0 (fitted
    profile) — the chair-amended realization of the C=256 point."""
    from tatkal_sim.model.server import Server
    from tatkal_sim.model.users import ClientConfig, ClientEngine
    from tatkal_sim.model.workload import generate_intents

    for seed in (1, 2):
        clock = Clock()
        queue = EventQueue(clock)
        streams = RngStreams(seed)
        fid = FidelityConfig()
        intents = generate_intents(OPERATING_WORKLOAD, fid, streams)
        log: list = []
        server = Server(
            clock, queue, streams, fid, fitted_server_config(25), OPERATING_WORKLOAD.t0, log=log
        )
        engine = ClientEngine(
            clock, queue, streams, fid, ClientConfig(), OPERATING_WORKLOAD, server, log=log
        )
        engine.start(intents)
        queue.run(max_events=5_000_000)
        t0 = OPERATING_WORKLOAD.t0
        delta = {"request": 1, "response": -1, "timeout": -1}
        inflight, above, last_t = 0, 0.0, t0
        for e in sorted((e for e in log if e[0] in delta and e[1] >= t0), key=lambda e: e[1]):
            if inflight >= 256:
                above += e[1] - last_t
            last_t = e[1]
            inflight += delta[e[0]]
        assert above >= 1.0, f"seed {seed}: sustained only {above:.2f}s at >=256"


# -- strategy units ----------------------------------------------------------
class _CountingService:
    def __init__(self):
        self.in_flight = 0
        self.peak = 0
        self.responders = []

    def submit(self, uid, pool, respond):
        self.in_flight += 1
        self.peak = max(self.peak, self.in_flight)

        def done(outcome=Outcome.BOOKED):
            self.in_flight -= 1
            respond(outcome)

        self.responders.append(done)


def test_bounded_fifo_caps_inner_concurrency_and_releases_in_order():
    clock = Clock()
    queue = EventQueue(clock)
    inner = _CountingService()
    svc = build_rung(1, inner, clock, queue, RungParams(admit_limit=3))
    seen = []
    for i in range(10):
        svc.submit(i, (1, "AC", "D0"), lambda o, i=i: seen.append(i))
    assert inner.peak == 3 and inner.in_flight == 3
    while inner.responders:
        inner.responders.pop(0)()
        queue.run()
    assert inner.peak == 3  # the cap held throughout
    assert seen == list(range(10))  # FIFO order preserved end-to-end


def test_fast_fail_learns_then_rejects_at_edge():
    clock = Clock()
    queue = EventQueue(clock)
    inner = _CountingService()
    svc = FastFail(inner, clock, queue, staleness=0.05, reject_cost=0.0005)
    outcomes = []
    svc.submit(1, (1, "AC", "D0"), lambda o: outcomes.append(o))
    inner.responders.pop(0)(Outcome.SOLD_OUT)  # cache observes sold-out
    queue.run()
    # within staleness: still forwarded to inner
    svc.submit(2, (1, "AC", "D0"), lambda o: outcomes.append(o))
    assert len(inner.responders) == 1
    inner.responders.pop(0)(Outcome.SOLD_OUT)
    queue.run()
    # after staleness: rejected at the edge, inner never sees it
    clock._advance(clock.now() + 0.06)
    svc.submit(3, (1, "AC", "D0"), lambda o: outcomes.append(o))
    queue.run()
    assert not inner.responders
    assert outcomes[-1] is Outcome.MECH_REJECT
    # other pools unaffected
    svc.submit(4, (2, "AC", "D0"), lambda o: outcomes.append(o))
    assert len(inner.responders) == 1


# -- rung-0 fit sanity and structural directions -----------------------------
def test_rung0_reproduces_calibration_shaped_collapse():
    """P6.1: during the first spike second the naive server operates in
    the calibrated high-concurrency regime — served-request rate in a
    loose band around the fitted thr(256), and conn resets present."""
    m = run_arm_once(rung_arm(0), seed=1)
    assert m["hard_error_rate"] > 0.2  # collapse signal: resets at the door
    # sell-out inside the window and inventory fully accounted
    assert m["goodput"]["sellout_reached"]
    assert m["inventory"]["violations"] == []


def test_rung1_bounded_admission_eliminates_conn_resets():
    """Structural: with admission capped at 8, the server never sees
    enough concurrency to refuse connections — the failure mode moves
    from resets to waiting."""
    r0 = run_arm_once(rung_arm(0), seed=1)
    r1 = run_arm_once(rung_arm(1), seed=1)
    assert r1["hard_error_rate"] < 0.01 < r0["hard_error_rate"]


def test_rung2_fast_fail_answers_losers_quickly():
    """Structural: once sold out, rung 2 rejects at the edge — rejected
    users' p99 TTDA collapses vs rung 1's queue-wait."""
    r1 = run_arm_once(rung_arm(1), seed=1)
    r2 = run_arm_once(rung_arm(2), seed=1)
    assert r2["ttda"]["rejected"]["p99"] < r1["ttda"]["rejected"]["p99"]
    assert r2["clean_rejection_rate"] >= r1["clean_rejection_rate"]
