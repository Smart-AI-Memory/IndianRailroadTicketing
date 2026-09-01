"""tatkal-v3 W3.1 acceptance: honest-cost readout on a synthetic log,
every number hand-computed (tasks.md W3.1)."""

from __future__ import annotations

from tatkal_sim.measure.metrics_v3 import honest_cost
from tatkal_sim.model.workload_v2 import V2Intent

T0 = 100.0
POOL = (1, "AC", "d")


def _intent(uid, cohort, strategy="", t_register=None):
    return V2Intent(
        uid,
        POOL,
        cohort,
        T0,
        identity_id=uid,
        controller_id=uid,
        strategy=strategy,
        t_register=t_register,
    )


def test_honest_cost_hand_computed():
    intents = [
        _intent(1, "t0_humans", t_register=T0 - 40.0),  # registered human
        _intent(2, "t0_humans"),  # unregistered human, priced out
        _intent(3, "bots", strategy="race"),  # bot, verify-missed
        _intent(4, "background"),
    ]
    log = [
        # human 1: requests at 100, verified in 2s, wins at 106, definitive 107
        ("request", 100.0, 1),
        ("verify_start", 100.0, 1),
        ("verify_done", 102.0, 1),
        ("stake_in", 100.0, 1, 0.5),
        ("alloc_win", 106.0, 1),
        ("stake_return", 106.0, 1, 0.5),
        ("definitive", 107.0, 1, "booked"),
        # human 2: ineligible at 100.5, definitive 108
        ("request", 100.5, 2),
        ("ineligible", 100.5, 2),
        ("definitive", 108.5, 2, "sold_out"),
        # bot 3: verify-missed at the draw, loses
        ("request", 100.2, 3),
        ("verify_start", 100.2, 3),
        ("verify_missed", 106.0, 3),
        ("alloc_lose", 106.0, 3),
        ("definitive", 106.5, 3, "sold_out"),
        # background 4: plain request, definitive
        ("request", 103.0, 4),
        ("definitive", 103.4, 4, "sold_out"),
    ]
    hc = honest_cost(log, intents, t0=T0)

    h = hc["t0_humans"]
    assert h["n"] == 2
    # absolute TTDA: human1 107-100=7, human2 108.5-100.5=8 -> p50 of [7, 8]
    assert h["absolute_ttda"]["n"] == 2
    assert h["absolute_ttda"]["p50"] in (7.0, 8.0)  # percentile convention
    # post-event: only human1 is a draw member: 107-106=1
    assert h["post_event_resolution"] == {"p50": 1.0, "p95": 1.0, "p99": 1.0, "n": 1}
    # verify wait: human1 only, 102-100=2
    assert h["verify_wait"]["p50"] == 2.0 and h["verify_wait"]["n"] == 1
    # stake exposure: human1, 106-100=6
    assert h["stake_exposure"]["p50"] == 6.0
    # registration burden: human1, 100-60=40
    assert h["reg_burden"]["p50"] == 40.0 and h["reg_burden"]["n"] == 1
    assert h["ineligible"] == 1  # human2
    assert h["verify_missed"] == 0

    b = hc["bots"]
    assert b["verify_missed"] == 1
    assert b["post_event_resolution"]["p50"] == 0.5  # 106.5-106
    assert b["ineligible"] == 0

    bg = hc["background"]
    assert bg["absolute_ttda"]["p50"] == 103.4 - 103.0
    assert bg["reg_burden"]["n"] == 0
