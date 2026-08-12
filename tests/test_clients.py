"""P2.2 acceptance — every outcome class's client behaviour per the matrix."""

from tatkal_sim.config import FidelityConfig
from tatkal_sim.core import Clock, EventQueue, RngStreams
from tatkal_sim.model.users import ClientConfig, ClientEngine, Outcome, total_requests
from tatkal_sim.model.workload import Intent, WorkloadConfig
from tests.conftest import ScriptService, StubService

WCFG = WorkloadConfig(t0=30.0)


def run_single(
    script=None,
    *,
    cohort="t0_humans",
    t_arrival=30.0,
    ccfg=None,
    fidelity=None,
    service=None,
    seed=1,
):
    """One intent against a scripted/stub service; returns (engine, service)."""
    clock = Clock()
    queue = EventQueue(clock)
    streams = RngStreams(seed)
    ccfg = ccfg or ClientConfig()
    fidelity = fidelity or FidelityConfig()
    svc = service(clock, queue) if service else ScriptService(clock, queue, script)
    eng = ClientEngine(clock, queue, streams, fidelity, ccfg, WCFG, svc)
    eng.start([Intent(0, (1, "AC", "D0"), cohort, t_arrival)])
    queue.run(max_events=10_000)
    return eng, svc


def kinds(eng):
    return [e[0] for e in eng.log]


def definitive(eng):
    return [e for e in eng.log if e[0] == "definitive"]


def test_booked_is_definitive_one_request():
    eng, _ = run_single([Outcome.BOOKED])
    assert total_requests(eng.log) == 1
    assert definitive(eng)[0][3] == "booked"


def test_sold_out_is_definitive_no_retry_by_default():
    eng, _ = run_single([Outcome.SOLD_OUT])
    assert total_requests(eng.log) == 1
    assert definitive(eng)[0][3] == "sold_out"


def test_p_retry_after_reject_drives_retries():
    ccfg = ClientConfig(p_retry_after_reject=1.0, max_attempts=3)
    eng, _ = run_single([Outcome.SOLD_OUT], ccfg=ccfg)
    assert total_requests(eng.log) == 3  # re-tries until attempts exhausted
    assert kinds(eng)[-1] == "abandon"


def test_mech_reject_definitive_like_sold_out():
    eng, _ = run_single([Outcome.MECH_REJECT])
    assert total_requests(eng.log) == 1
    assert definitive(eng)[0][3] == "mech_reject"


def test_not_open_polls_then_fires_at_t0():
    eng, _ = run_single(
        service=lambda c, q: StubService(c, q, WCFG.t0, delay=0.01),
        t_arrival=WCFG.t0 - 3.0,
        cohort="pre_fire",
    )
    reqs = [e for e in eng.log if e[0] == "request"]
    pre = [e for e in reqs if e[1] < WCFG.t0]
    assert len(pre) >= 3  # polls every 0.75 s across 3 s
    assert any(e[1] == WCFG.t0 for e in reqs)  # the real attempt fires AT T0
    assert definitive(eng)[0][3] == "booked"
    # TTDA clock starts at the FIRST pre-T0 poll: pre-firing is not free
    assert float(definitive(eng)[0][4]) >= 3.0


def test_queue_position_polls_at_interval_without_burning_attempts():
    ccfg = ClientConfig(poll_interval=1.0, max_attempts=2)
    eng, _ = run_single([Outcome.QUEUE_POSITION] * 4 + [Outcome.BOOKED], ccfg=ccfg)
    reqs = [e[1] for e in eng.log if e[0] == "request"]
    assert len(reqs) == 5  # 4 polls + resolution — attempts never exhausted
    gaps = [round(b - a, 3) for a, b in zip(reqs, reqs[1:])]
    assert all(abs(g - 1.01) < 0.02 for g in gaps)  # interval + service delay
    assert definitive(eng)[0][3] == "booked"


def test_hard_error_retries_with_backoff_then_succeeds():
    eng, _ = run_single([Outcome.HARD_ERROR, Outcome.BOOKED])
    reqs = [e[1] for e in eng.log if e[0] == "request"]
    assert len(reqs) == 2
    assert abs((reqs[1] - reqs[0]) - (0.01 + 0.5)) < 1e-6  # delay + backoff_base
    assert definitive(eng)[0][3] == "booked"


def test_timeout_retries_until_exhausted_then_abandons():
    # patience_mean high so attempt exhaustion (not patience) ends the intent
    ccfg = ClientConfig(patience_mean=100.0)
    eng, _ = run_single(service=lambda c, q: StubService(c, q, WCFG.t0, silent=True), ccfg=ccfg)
    assert total_requests(eng.log) == ccfg.max_attempts
    assert kinds(eng).count("timeout") == ccfg.max_attempts
    assert kinds(eng)[-1] == "abandon"


def test_retries_off_means_one_attempt_then_abandon():
    eng, _ = run_single(
        service=lambda c, q: StubService(c, q, WCFG.t0, silent=True),
        fidelity=FidelityConfig(retries_enabled=False),
    )
    assert total_requests(eng.log) == 1
    assert kinds(eng)[-1] == "abandon"


def test_patience_exhaustion_abandons_early():
    ccfg = ClientConfig(patience_mean=0.1, max_attempts=10)
    eng, _ = run_single(service=lambda c, q: StubService(c, q, WCFG.t0, silent=True), ccfg=ccfg)
    assert total_requests(eng.log) == 1  # first timeout already exceeds patience
    assert kinds(eng)[-1] == "abandon"


def test_bot_speedup_halves_timeout_and_backoff():
    human, _ = run_single(service=lambda c, q: StubService(c, q, WCFG.t0, silent=True))
    bot, _ = run_single(service=lambda c, q: StubService(c, q, WCFG.t0, silent=True), cohort="bots")
    t2_human = [e[1] for e in human.log if e[0] == "request"][1]
    t2_bot = [e[1] for e in bot.log if e[0] == "request"][1]
    assert t2_bot - WCFG.t0 == 0.5 * (t2_human - WCFG.t0)  # (timeout+backoff) scaled


def test_stale_response_after_timeout_is_dropped():
    # service answers at 3.0 s; client times out at 2.0 s and retries —
    # the late response must not resurrect the closed attempt
    eng, _ = run_single(service=lambda c, q: StubService(c, q, WCFG.t0, delay=3.0))
    resp_before_second_timeout = [e for e in eng.log if e[0] == "response" and e[1] < WCFG.t0 + 2.0]
    assert not resp_before_second_timeout
    assert kinds(eng).count("timeout") >= 1
