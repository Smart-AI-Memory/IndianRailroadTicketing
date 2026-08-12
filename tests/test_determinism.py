"""P1.3 acceptance — identical seeds, byte-identical results (R1)."""

import json

from tatkal_sim.runner import result_digest, run_trivial


def test_same_seed_byte_identical():
    r1 = run_trivial(20260811)
    r2 = run_trivial(20260811)
    assert json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)
    assert result_digest(r1) == result_digest(r2)


def test_different_seeds_differ():
    assert result_digest(run_trivial(1)) != result_digest(run_trivial(2))


def test_trivial_workload_actually_ran():
    r = run_trivial(20260811, n_arrivals=100)
    # 100 arrival triggers + 100 arrive events... arrive is scheduled per
    # trigger and each arrival schedules one completion: 200 events total
    assert r["completions"] == 100
    assert r["events_processed"] == 200
    assert float(r["final_time"]) > 0.0


def test_digest_stability_against_key_order():
    r = run_trivial(3)
    shuffled = dict(reversed(list(r.items())))
    assert result_digest(shuffled) == result_digest(r)
