"""V0.2 anchor (tatkal-v2 tasks.md; decisions.md D16).

Golden-snapshot reproduction check: rung 2, fitted variant, operating
workload, seed 0, captured 2026-08-12 while the v2 tree was
code-identical to the v1 close (main @ PR #5 merge). D16 registers the
tolerance as EXACT — the full-metrics digest must match bit-identically.
If this test fails, a v2 change altered v1 physics: that is a ladder
stop, not a snapshot refresh. The digest may only be re-captured under
a decision entry that explains the physics change.
"""

from tatkal_sim.runner import ladder_arm, result_digest, run_arm_once

# sha256 over the sorted-key JSON of the full R6 metrics dict (D16).
V1_ANCHOR_DIGEST = "8cf416627b2bac1a8f7b5ff559a09c485f36cb71be0f8350881f2f9edcf9b439"


def test_v1_physics_anchor_bit_identical():
    metrics = run_arm_once(ladder_arm(2), 0)
    assert result_digest(metrics) == V1_ANCHOR_DIGEST


def test_v1_anchor_headline_values():
    """Human-readable sentinels so a digest break points somewhere."""
    m = run_arm_once(ladder_arm(2), 0)
    g = m["goodput"]
    assert g["seats_sold"] == 200
    assert g["ghost_sales"] == 0
    assert g["sellout_reached"] is True
    assert g["sold_per_s"] == 1740.919908379298
