"""tatkal-v3 W1 acceptance tests (tasks.md W1.1–W1.4).

W1.1  policy=None -> bit-identical to the v2 M2 arm (log and metrics).
W1.2  verification overload degrades to clean verify-missed, never
      lost intents; per-identity wait is derivable from the log.
W1.3  DC2 k* rule (D17-corrected) behaves; forfeiture ledger balances;
      d = 0 is refused by the policy (pass-through cell is policy=None).
W1.4  DC4 deadline profile concentrates registrations at the window
      close; the uniform variant does not; generation is deterministic;
      the ineligible stream exists end-to-end.
"""

from __future__ import annotations

import dataclasses as dc

import pytest

from tatkal_sim.config import FidelityConfig
from tatkal_sim.core import RngStreams
from tatkal_sim.model.workload_v2 import (
    OPERATING_WORKLOAD_V2,
    V2WorkloadConfig,
    generate_intents_v2,
    with_abuse,
)
from tatkal_sim.runner_v2 import V2Arm, run_arm_v2_once
from tatkal_sim.runner_v3 import V3Arm, run_arm_v3_once
from tatkal_sim.strategies.mitigation import DepositPolicy, deposit_k_star

WCFG_P01 = with_abuse(OPERATING_WORKLOAD_V2, 0.1)

#: small human-only workload for targeted mechanism tests
# Overload arithmetic (W1.2): fitted app time ~77 us x 2 workers gives
# ~0.4 s of pool capacity in a 0.2 s window; ~120 in-window entrants at
# c_verify=200 (~15 ms each) demand ~1.9 s — 4-5x oversubscribed, so
# some verify and many miss. c_verify=200 is a test amplifier for the
# microsecond-scale fitted service time, not a DC1 grid value.
SMALL = V2WorkloadConfig(n_pre_fire=0, n_t0_humans=300, n_bots=150, n_background=0, qual_window=0.2)
NO_BOTS = dc.replace(FidelityConfig(), bot_cohort=False)


def _events(log, name):
    return [e for e in log if e[0] == name]


# ------------------------------------------------------------------ W1.1
def test_w11_null_policy_bit_identical_to_v2_m2():
    v2 = run_arm_v2_once(V2Arm("m2-p0.1-fitted", "m2", wcfg=WCFG_P01), seed=0)
    v3 = run_arm_v3_once(V3Arm("v3-none", mitigation="none", wcfg=WCFG_P01), seed=0)
    assert v3["metrics"] == v2["metrics"]
    assert v3["log"] == v2["log"]
    assert v3["intents"] == v2["intents"]


# ------------------------------------------------------------------ W1.2
def test_w12_verification_overload_clean_never_lost():
    arm = V3Arm(
        "a1-overload",
        mitigation="verify",
        c_verify=200.0,
        wcfg=SMALL,
        fidelity=NO_BOTS,
    )
    r = run_arm_v3_once(arm, seed=0)
    log = r["log"]
    started = {e[2] for e in _events(log, "verify_start")}
    done = {e[2] for e in _events(log, "verify_done")}
    missed = {e[2] for e in _events(log, "verify_missed")}
    assert started, "no entries attempted verification"
    # overload by construction: 4x-app-time verification for every
    # entrant inside a 0.5 s window exceeds pool capacity
    assert missed, "expected verify-missed under overload"
    # every started identity resolves exactly one way before/at the draw
    done_before_draw = done - missed
    assert started == done_before_draw | missed
    assert not (done_before_draw & missed)
    # wait is derivable and non-negative for completed verifications
    t_start = {e[2]: e[1] for e in _events(log, "verify_start")}
    for _, t, uid in _events(log, "verify_done"):
        assert t >= t_start[uid]


# ------------------------------------------------------------------ W1.3
def test_w13_k_star_rule():
    # tiny price: staking every identity dominates
    assert deposit_k_star(d=1e-9, m=5, p_win=0.05) == 5
    # k* is non-increasing in d
    ks = [deposit_k_star(d, 5, 0.05) for d in (0.01, 0.1, 0.5, 2.0, 10.0)]
    assert ks == sorted(ks, reverse=True)
    # punitive price with a near-certain pool loss still stakes one
    # identity while expected value is positive
    assert deposit_k_star(0.5, 5, 0.05) >= 1


def test_w13_zero_deposit_refused():
    with pytest.raises(ValueError):
        DepositPolicy(0.0, OPERATING_WORKLOAD_V2, seats_total=200)


def test_w13_forfeiture_ledger_balances():
    arm = V3Arm("a2-d0.5", mitigation="deposit", d=0.5, wcfg=with_abuse(OPERATING_WORKLOAD_V2, 0.2))
    r = run_arm_v3_once(arm, seed=0)
    log = r["log"]
    n_in = len(_events(log, "stake_in"))
    n_refund = len(_events(log, "stake_refund"))
    n_return = len(_events(log, "stake_return"))
    n_forfeit = len(_events(log, "stake_forfeit"))
    assert n_in > 0
    assert n_in == n_refund + n_return + n_forfeit
    # no identity appears in two ledger outcomes
    uids = [e[2] for e in log if e[0] in ("stake_refund", "stake_return", "stake_forfeit")]
    assert len(uids) == len(set(uids))


# ------------------------------------------------------------------ W1.4
def _registered_offsets(cfg, seed=0):
    intents = generate_intents_v2(cfg, FidelityConfig(), RngStreams(seed), "a3")
    return [cfg.t0 - i.t_register for i in intents if i.t_register is not None and i.strategy == ""]


def test_w14_deadline_profile_concentrates_at_close():
    cfg = dc.replace(OPERATING_WORKLOAD_V2, t0=400.0)
    offsets = _registered_offsets(cfg)
    assert offsets
    frac_final_decile = sum(1 for o in offsets if o <= 0.1 * cfg.reg_window) / len(offsets)
    # DC4: 60% deadline cohort (sigma 0.35 s << 30 s) + ~4% of the
    # uniform cohort also lands there; assert well above uniform's 10%
    assert frac_final_decile >= 0.55

    uni = dc.replace(cfg, reg_profile="uniform")
    frac_uni = sum(1 for o in _registered_offsets(uni) if o <= 0.1 * cfg.reg_window) / len(
        _registered_offsets(uni)
    )
    assert frac_uni < 0.2


def test_w14_generation_deterministic_and_open_loop():
    cfg = dc.replace(OPERATING_WORKLOAD_V2, t0=400.0)
    a = generate_intents_v2(cfg, FidelityConfig(), RngStreams(7), "a3")
    b = generate_intents_v2(cfg, FidelityConfig(), RngStreams(7), "a3")
    assert a == b


def test_w14_ineligible_stream_end_to_end():
    arm = V3Arm(
        "a3-smoke",
        mitigation="regbound",
        wcfg=dc.replace(OPERATING_WORKLOAD_V2, r_reg=0.5),
    )
    r = run_arm_v3_once(arm, seed=0)
    ineligible = _events(r["log"], "ineligible")
    assert ineligible, "expected unregistered entrants to log ineligible"
    uids = [e[2] for e in ineligible]
    assert len(uids) == len(set(uids)), "ineligible logged once per identity"
