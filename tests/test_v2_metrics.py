"""V4 acceptance (tatkal-v2 tasks.md V4.1/V4.2)."""

import pytest

from tatkal_sim.measure.metrics_v2 import (
    draw_share_advantage,
    error_taxonomy,
    per_tranche_fairness,
    three_variant_table,
    two_clock,
)
from tatkal_sim.model.workload_v2 import OPERATING_WORKLOAD_V2, with_abuse
from tatkal_sim.runner_v2 import V2Arm, run_arm_v2_once


# ---------------------------------------------------------------- V4.1
def test_two_clock_synthetic_hand_check():
    from tatkal_sim.model.workload_v2 import V2Intent

    intents = [V2Intent(1, (1, "AC", "D0"), "t0_humans", 10.0, identity_id=1, controller_id=1)]
    log = [
        ("request", 10.0, 1, 1),
        ("alloc_lose", 15.0, 1),
        ("definitive", 15.5, 1, "sold_out", "5.5"),
    ]
    tc = two_clock(log, intents)
    assert tc["absolute_ttda"]["p50"] == 5.5  # 15.5 - 10.0
    assert tc["post_event_resolution"]["p50"] == 0.5  # 15.5 - 15.0
    assert tc["n_members"] == 1


def test_two_clock_on_m2_run():
    r = run_arm_v2_once(V2Arm("m2", "m2"), 0)
    tc = two_clock(r["log"], r["intents"])
    # the absolute clock contains the deliberate wait (~Q); post-event
    # resolution does not (D14.5)
    assert tc["absolute_ttda"]["p50"] > 3.0
    assert tc["post_event_resolution"]["p50"] < 2.0
    assert tc["n_members"] > 2000


def test_draw_share_advantage_controller_rollup():
    r = run_arm_v2_once(V2Arm("m2-p04", "m2", wcfg=with_abuse(OPERATING_WORKLOAD_V2, 0.4)), 0)
    adv = draw_share_advantage(r["log"], r["intents"])
    assert "identity_split" in adv and "human" in adv
    assert adv["identity_split"]["controllers"] == 60
    # m identities per controller: abuse advantage must exceed honest ~1
    assert adv["identity_split"]["advantage"] > adv["human"]["advantage"]
    assert adv["identity_split"]["advantage"] > 1.5


def test_per_tranche_fairness_on_m3():
    r = run_arm_v2_once(V2Arm("m3", "m3"), 0)
    rows = per_tranche_fairness(r["log"], r["intents"], r["intents"])
    assert len(rows) == 4
    assert [row["tranche"] for row in rows] == [0, 1, 2, 3]
    assert sum(row["seats_sold"] for row in rows) == r["metrics"]["goodput"]["seats_sold"]


def test_error_taxonomy_streams():
    r = run_arm_v2_once(V2Arm("m2", "m2"), 0)
    tax = error_taxonomy(r["log"])
    assert tax["lottery_loss"] > 2000
    assert tax["booked"] > 150
    # never summed: keys stay distinct and individually addressable
    assert set(tax) == {
        "booked",
        "clean_reject",
        "lottery_loss",
        "timeouts",
        "hard_errors",
        "abandons",
    }


# ---------------------------------------------------------------- V4.2
def test_three_variant_table_gate():
    ok = three_variant_table({"fitted": {"v": 1}, "plateau": {"v": 2}, "cliff": {"v": 3}}, "p99")
    assert ok["metric"] == "p99"
    with pytest.raises(ValueError, match="missing variants.*cliff"):
        three_variant_table({"fitted": {}, "plateau": {}}, "p99")
