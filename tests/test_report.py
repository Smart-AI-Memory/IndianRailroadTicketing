"""P5.3 acceptance — report renders from a 2-arm smoke run with every
required section: SMOKE banner, variant + toggles, both comparison
families, out-of-order labelling, and the Gate A profile."""

from tatkal_sim.model.server import ServerConfig
from tatkal_sim.runner import Arm, render_report, run_arm_once, sweep

SEEDS = [1, 2, 3, 4, 5]

RUNG0 = Arm("rung0-naive", ServerConfig(workers=8, seats_per_pool=10))
OTHER = Arm(
    "smoke-bounded", ServerConfig(workers=8, accept_queue=16, conn_limit=64, seats_per_pool=10)
)
OOO = Arm(
    "pure-queueing-experiment",
    ServerConfig(workers=8, seats_per_pool=10),
    out_of_order=True,
)


def rendered(arms=None):
    arms = arms or [RUNG0, OTHER]
    results = sweep(arms, SEEDS)
    return render_report(
        arms,
        results,
        ladder_pairs=[(arms[1].name, arms[0].name)],
        baseline_pairs=[(arms[1].name, arms[0].name)],
    )


def test_report_renders_with_all_required_sections():
    text = rendered()
    assert "SMOKE RUN" in text  # 5 seeds < 20: no claim may be made
    assert "knee variant: `fitted`" in text
    assert "enabled toggles:" in text and "atomic_inventory" in text
    assert "Ladder family" in text and "Baseline family" in text
    assert "Gate A profile" in text
    assert "wasted_work_ratio" in text and "fairness.bots_win_share" in text
    assert "Sensitivity" in text


def test_report_is_deterministic():
    assert rendered() == rendered()


def test_out_of_order_arm_is_labelled_never_a_rung():
    text = rendered(arms=[RUNG0, OOO])
    assert "[OUT-OF-ORDER — not a rung]" in text


def test_sweep_reuses_identical_traces_per_seed():
    """Same seed -> same workload trace across arms: the paired design's
    precondition (D6). Metrics that depend only on the workload agree."""
    a = run_arm_once(RUNG0, seed=9)
    b = run_arm_once(OTHER, seed=9)
    assert a["fairness"]["population_by_cohort"] == b["fairness"]["population_by_cohort"]


def test_every_run_enforces_inventory_invariants():
    # run_arm_once calls assert_ok() unconditionally — a run with violations
    # cannot produce metrics at all
    m = run_arm_once(RUNG0, seed=1)
    assert m["inventory"]["violations"] == []
