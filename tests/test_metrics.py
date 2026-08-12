"""P5.1 acceptance — golden-file test: hand-computed metrics on a scripted
run must match exactly, plus integration sanity on a real world."""

import pytest

from tatkal_sim.measure.metrics import compute
from tatkal_sim.model.server import ServerConfig
from tatkal_sim.model.workload import Intent
from tests.helpers_server import server_world

T0 = 30.0
POOL = (1, "AC", "D0")

# Four users, every mechanism exercised once:
#   u0 t0_human   books cleanly (winner, ttda 0.1)
#   u1 t0_human   sold out (rejected, ttda 0.2)
#   u2 bot        times out twice, abandons — but the server sells it a
#                 seat anyway at 33.0 (ghost sale) and serves a second
#                 stale answer at 35.0
#   u3 pre_fire   polls pre-T0 ("not open"), rejected at 30.3 (ttda 5.3)
INTENTS = [
    Intent(0, POOL, "t0_humans", 30.0),
    Intent(1, POOL, "t0_humans", 30.0),
    Intent(2, POOL, "bots", 30.0),
    Intent(3, POOL, "pre_fire", 25.0),
]

LOG = [
    ("request", 25.0, 3, 1),
    ("served", 25.01, 3, repr(0.005), "not_open"),
    ("response", 25.01, 3, "not_open"),
    ("request", 30.0, 0, 1),
    ("request", 30.0, 1, 1),
    ("request", 30.0, 2, 1),
    ("request", 30.0, 3, 2),
    ("sold", 30.1, 0, POOL),
    ("served", 30.1, 0, repr(0.05), "booked"),
    ("response", 30.1, 0, "booked"),
    ("definitive", 30.1, 0, "booked", repr(0.1)),
    ("served", 30.2, 1, repr(0.05), "sold_out"),
    ("response", 30.2, 1, "sold_out"),
    ("definitive", 30.2, 1, "sold_out", repr(0.2)),
    ("served", 30.3, 3, repr(0.06), "sold_out"),
    ("response", 30.3, 3, "sold_out"),
    ("definitive", 30.3, 3, "sold_out", repr(5.3)),
    ("timeout", 32.0, 2, 1),
    ("request", 32.5, 2, 2),
    ("sold", 33.0, 2, POOL),  # ghost: client timed out at 32.0
    ("served", 33.0, 2, repr(0.4), "booked"),
    ("stale_response", 33.0, 2),
    ("timeout", 34.5, 2, 2),
    ("abandon", 34.5, 2),
    ("served", 35.0, 2, repr(0.3), "sold_out"),
    ("stale_response", 35.0, 2),
]


def golden():
    return compute(
        LOG,
        INTENTS,
        t0=T0,
        inventory_totals={"initial": 2, "remaining": 0, "sold": 2},
        inventory_violations=[],
        identity_on=True,
        run_end=35.0,
    )


def test_ttda_split_never_averaged():
    m = golden()
    assert m["ttda"]["winners"] == {"p50": 0.1, "p95": 0.1, "p99": 0.1, "n": 1}
    assert m["ttda"]["rejected"]["n"] == 2
    assert m["ttda"]["rejected"]["p99"] == 5.3


def test_goodput_over_sellout_window():
    g = golden()["goodput"]
    assert g["sellout_reached"] is True
    assert g["window_s"] == pytest.approx(3.0)  # T0=30 -> second seat sold at 33
    assert g["sold_per_s"] == pytest.approx(2 / 3.0)
    assert g["seats_sold"] == 2
    assert g["definitive_booked_users"] == 1
    assert g["ghost_sales"] == 1  # the seat sold to the departed bot


def test_rates_never_summed():
    m = golden()
    # clean: sold_out(u1), not_open(u3), sold_out(u3) over 6 requests
    assert m["clean_rejection_rate"] == pytest.approx(3 / 6)
    # hard: 2 timeouts, 0 hard-error responses
    assert m["hard_error_rate"] == pytest.approx(2 / 6)


def test_retry_amplification():
    assert golden()["retry_amplification"] == pytest.approx(6 / 4)


def test_wasted_work_ratio_pairs_served_with_stale():
    total = 0.005 + 0.05 + 0.05 + 0.06 + 0.4 + 0.3
    wasted = 0.4 + 0.3
    assert golden()["wasted_work_ratio"] == pytest.approx(wasted / total)


def test_fairness_by_first_arrival_cohort():
    f = golden()["fairness"]
    assert f["seats_by_cohort"] == {"bots": 1, "t0_humans": 1}
    assert f["population_by_cohort"] == {"bots": 1, "pre_fire": 1, "t0_humans": 2}
    assert f["bots_win_share"] == pytest.approx(0.5)
    assert f["bots_population_share"] == pytest.approx(0.25)


def test_settling_none_without_baseline_traffic():
    # only one pre-T0 sample at 25.01 — the baseline window [19, 20] is
    # empty, so settling is reported as None, never fabricated
    assert golden()["settling_time_s"] is None
    assert golden()["abandon_count"] == 1


def test_integration_on_a_real_world_run():
    intents, engine, srv = server_world(scfg=ServerConfig(workers=8, seats_per_pool=10))
    m = compute(
        engine.log,
        intents,
        t0=30.0,
        inventory_totals=srv.inventory.totals(),
        inventory_violations=srv.inventory.violations(),
        run_end=engine.clock.now(),
    )
    assert 0.0 <= m["clean_rejection_rate"] <= 1.0
    assert 0.0 <= m["hard_error_rate"] <= 1.0
    assert m["retry_amplification"] >= 1.0
    assert m["ttda"]["winners"]["n"] + m["ttda"]["rejected"]["n"] + m["abandon_count"] == len(
        intents
    )
    assert m["goodput"]["seats_sold"] >= m["goodput"]["definitive_booked_users"]
    assert m["settling_time_s"] is None or m["settling_time_s"] >= 0.0
