"""tatkal-v3 W2 acceptance tests (tasks.md W2.1–W2.3).

Smoke runs are labelled diagnostic and never cited as results
(standing rules). Statements are on record via D20; these tests pin
the mechanical acceptance:

W2.1  A1 runs per variant; verification streams present.
W2.2  A2 d-grid smoke monotonicity — higher d never raises k*, and
      the D20 bracket point collapses the abuser to one identity.
W2.3  A3 camping-buys-nothing leak diagnostic: under the timing-blind
      draw, camp bots' per-identity win rate matches the registered
      field's (the v2 M1 diagnostic, carried to a3 semantics).
"""

from __future__ import annotations

import dataclasses as dc

from tatkal_sim.model.workload_v2 import OPERATING_WORKLOAD_V2, with_abuse
from tatkal_sim.runner_v3 import V3Arm, run_arm_v3_once
from tatkal_sim.strategies.mitigation import (
    C_VERIFY_GRID,
    D_GRID,
    DepositPolicy,
    expected_pool_identities,
)

WCFG_P02 = with_abuse(OPERATING_WORKLOAD_V2, 0.2)
VARIANTS = ("fitted", "plateau", "cliff")


# ------------------------------------------------------------------ W2.1
def test_w21_a1_smoke_per_variant():
    for variant in VARIANTS:
        arm = V3Arm(
            f"a1-smoke-{variant}",
            mitigation="verify",
            c_verify=1.0,
            wcfg=WCFG_P02,
            variant=variant,
        )
        r = run_arm_v3_once(arm, seed=0)  # diagnostic, never a result
        log = r["log"]
        assert any(e[0] == "verify_start" for e in log)
        assert any(e[0] == "alloc_event" for e in log)
        # inventory invariant enforced inside the runner (assert_ok)


def test_w21_dc1_grid_is_registered():
    assert C_VERIFY_GRID == (0.25, 1.0, 4.0)


# ------------------------------------------------------------------ W2.2
def test_w22_d_grid_smoke_monotonicity():
    seats_total = 25 * WCFG_P02.n_trains * len(WCFG_P02.classes)
    ks = [DepositPolicy(d, WCFG_P02, seats_total).k_star for d in D_GRID]
    assert ks == sorted(ks, reverse=True), "higher d must never raise k*"
    # D20 pre-registration: no bite on the original grid, full
    # collapse at the bracket point
    assert ks[0] == WCFG_P02.m_identities  # d = 0.1
    assert ks[-1] == 1  # d = 15 deters every marginal identity


def test_w22_a2_smoke_stake_counts_follow_k_star():
    seats_total = 25 * WCFG_P02.n_trains * len(WCFG_P02.classes)
    n_split = round(WCFG_P02.abuse_p * WCFG_P02.n_bots)
    for d in (0.5, 15.0):
        arm = V3Arm(f"a2-smoke-d{d}", mitigation="deposit", d=d, wcfg=WCFG_P02)
        r = run_arm_v3_once(arm, seed=0)
        k = DepositPolicy(d, WCFG_P02, seats_total).k_star
        staked = {e[2] for e in r["log"] if e[0] == "stake_in"}
        split_staked = [
            i for i in r["intents"] if i.strategy == "identity_split" and i.user_id in staked
        ]
        per_controller: dict[int, int] = {}
        for i in split_staked:
            per_controller[i.controller_id] = per_controller.get(i.controller_id, 0) + 1
        assert len(per_controller) == n_split
        assert all(v == k for v in per_controller.values())


# ------------------------------------------------------------------ W2.3
def test_w23_a3_camping_buys_nothing():
    """Leak diagnostic: the draw is timing-blind, so camp bots
    (registered in the first 5% of W) must win at the same
    per-identity rate as everyone else registered. Aggregated over
    seeds for statistical room; a real ordering/timing leak would be
    dramatic, so the band is wide but meaningful."""
    camp_wins = camp_n = other_wins = other_n = 0
    for seed in range(12):
        arm = V3Arm("a3-diag", mitigation="regbound", wcfg=WCFG_P02)
        r = run_arm_v3_once(arm, seed=seed)
        winners = {e[2] for e in r["log"] if e[0] == "alloc_win"}
        for i in r["intents"]:
            if i.t_register is None:
                continue
            if i.strategy == "camp":
                camp_n += 1
                camp_wins += i.user_id in winners
            else:
                other_n += 1
                other_wins += i.user_id in winners
    assert camp_n and other_n
    camp_rate = camp_wins / camp_n
    other_rate = other_wins / other_n
    assert other_rate > 0
    ratio = camp_rate / other_rate
    assert 0.5 <= ratio <= 1.6, f"camping moved the odds: ratio={ratio:.2f}"


def test_w23_expected_pool_matches_generation():
    """The DC2 public-constants pool expectation matches the actual
    generated identity count for the M2-family workload (sanity for
    the k* odds; drift here would silently mis-price the abuser)."""
    from tatkal_sim.config import FidelityConfig
    from tatkal_sim.core import RngStreams
    from tatkal_sim.model.workload_v2 import generate_intents_v2

    intents = generate_intents_v2(WCFG_P02, FidelityConfig(), RngStreams(0), "m2")
    t0_family = [i for i in intents if i.cohort in ("t0_humans", "bots")]
    assert len(t0_family) == expected_pool_identities(WCFG_P02)
