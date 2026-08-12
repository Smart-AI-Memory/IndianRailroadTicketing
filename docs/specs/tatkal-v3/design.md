# tatkal-v3 — design

**Status:** draft (2026-08-12) — awaiting chair review. Constants
marked **PROPOSED** require registration by decision entry; D6-
registered constants are cited, not re-opened.

**Inputs:** requirements.md (ratified, D7); v3 ledger D1–D6; the v2
simulator and archives (population D3-carried, so v2's archived cells
are directly reusable as baselines and anchors).

---

## Shape of the extension

The structural fact of v3: **three of five scope items need no new
simulator code.**

- **Deposit arm** — a pure analysis module over per-controller win
  distributions (deterministic re-derivation from existing cells, the
  V7 pattern). No mechanism code.
- **Costed M1/M2 bursts** — a cell list. `CostedPush` is already
  parameterized; the c_push grid simply gets run for the allocation
  arms.
- **M3 retry sweep** — a `ClientConfig` knob (`p_retry_after_reject`)
  that has existed since v1.

New mechanism code is confined to the two identity-pricing arms, both
small extensions of `LotteryPool`:

- **M2v** (`VerifyingLotteryPool`): a verification work item per
  entering identity; the draw runs over verified ∩ active.
- **M2r** (`RegistrationBoundLotteryPool`): M1's registration workload
  over M2's pool; unregistered entries are rejected at the edge.

## Arm M2v — verification-cost

- On an identity's FIRST pool entry, one verification work item is
  submitted to the **shared worker pool** at
  `c_verify × status_cost_factor` (D6.4 grid {0, ½, 1, 2}; the zero
  cell is the unmitigated continuity anchor and reuses the v2
  archive). One item per identity, not per poll — **PROPOSED** (the
  alternative, re-verification per poll, models a stateless verifier
  and multiplies load; not what real verification does).
- **Verify-by-draw (D6.3):** the draw at T0+Q runs over identities
  whose verification completed by the draw instant ∩ still active.
  Later completions fall to the post-draw fast-fail path.
- Log stream: `("verify_start"/"verify_done", t, identity)` — the
  verification load stream is reported separately (its saturation is
  the arm's failure mode: a verification stampede that starves
  bookings).
- Honest-user cost metrics (D6.2): added entry latency; draw-miss
  exclusion rate among honest identities (verification pending at
  draw).
- Mechanics of the hypothesis: abusers submit m verifications each —
  at c_verify = 2 and p = 0.4 that is 300 extra heavy status-class
  work items in the entry seconds, paid by every user of the shared
  pool.

## Arm M2r — registration-bound

- Registration workload: M1's machinery over W_b = 300 s (D6.4);
  honest registrants per the carried r_reg grid {0.5, 0.8, 0.95};
  camp bots front-load (carried D13.3 behaviour); **identity-split
  abusers must pre-register all m identities** (registration
  one-shots × m, costed).
- **Entry semantics — PROPOSED: reject-at-entry.** An unregistered
  identity's pool entry gets an edge MECH_REJECT (fast definitive,
  v1 reject semantics) rather than silent exclusion at the draw.
  Rationale: walk-ups learn their fate in milliseconds instead of
  waiting Q for a draw they were never in; the alternative
  (exclude-at-draw) manufactures deliberate wait for users the
  mechanism has already decided against.
- Honest-user cost metric (D6.2): walk-up rejection count/rate per
  r_reg cell — the fairness-vs-inclusion trade-off is this arm's
  finding, reported as a function of uptake.
- Workload note: registration flags for M2r identities are arm-side
  behaviour of existing cohorts (exactly as M1's were) — no D3
  population change.

## Deposit arm — forfeiture accounting (analysis module)

D6.4 registers: seat value 1, **losers refunded**. The design
consequence — flagged for chair review because it interprets what the
deposit prices:

- With losers refunded, entry multiplication is capital-lockup only;
  the deposit's bite is on **multi-win forfeiture**: an abuser who
  wins k seats can redeem one; the other (k−1) deposits are forfeit
  (no resale in-model; two-phase inventory stays deferred).
- **d\*(p) = the deposit at which an abuser's expected net utility is
  zero:** E[net] = P(≥1 win)·(1 − price_effect) − E[max(0, K−1)]·d,
  computed from the **per-controller win distribution K** tallied by
  deterministic re-run of the fitted M2 cells (V7 pattern; the
  archives hold aggregates only).
- Output: d\* per prevalence cell, plus the honest-framing statement
  (out-of-model exclusions named, never quantified — D6.2).
- At m = 5 and per-identity win odds ~7%, multi-win is rare —
  **a large d\* is an acceptable and likely outcome** (the
  refund-losers design is weak against low-multiplicity abuse; that
  finding is the point, not a failure).

## R3 — costed-burst cells

- **Cell list — PROPOSED: center cells only.** M1 at r_reg = 0.8 and
  M2 at p = 0.2, each × c_push {¼, ½, 1, 2} × 3 variants × 20 seeds
  (zero cells already exist in the v2 archives). Full uptake/abuse ×
  c_push crosses would quadruple the family for a second-order
  interaction no hypothesis names.
- Floors per the amended rule with **D4.2 enumeration**: components
  included — notification-burst drain, winner-redemption drain;
  components omitted with cause — verification (absent from these
  arms), registration (pre-T0, outside the post-event window).
- Per D4.1, tasks.md carries a **bar × cell coverage table**; a bar
  without a cell fails gate approval mechanically.
- Fairness guards re-evaluated per grid point; prediction registered
  in requirements: fairness is costing-independent.

## M3 retry sweep

- Cells: p_retry {0.3, 0.7, 1.0} × 3 variants × 20 seeds; the 0 cell
  IS the v2 archive cell (third anchor, bit-identical).
- The knob applies population-wide through `ClientConfig` (bots retry
  at their cadence — carried v1 semantics); camp re-arrival behaviour
  is unchanged and now interacts with honest re-entry.
- Measured per cell: seats sold, whole-run + per-tranche F, retry
  amplification per tranche, congestion indicators (R3.2's spiral is
  a named possible outcome), both clocks.

## Anchors (R1)

1. v1 physics anchor — carried in CI unchanged.
2. **v2-continuity anchor:** M2v at c_verify = 0 reproduces the v2
   M2 cell bit-identically (tolerance: exact, re-registered at V0).
3. **M3 anchor:** the p_retry = 0 cell equals the v2 M3 archive
   bit-identically.

## Cell budget (evaluated runs)

| family | cells | runs |
|---|---|---|
| M2v (c_verify {½,1,2} × p {0,.1,.2,.4}) | 12 × 3 variants | 720 |
| M2r (r_reg {.5,.8,.95} × p {0,.2}) | 6 × 3 | 360 |
| costed bursts (2 arms × 4 c_push) | 8 × 3 | 480 |
| M3 retry (3 values) | 3 × 3 | 180 |
| **total** | **87 cells** | **1,740** |

M2v × abuse cross is required (mitigation's whole point is its abuse
response); M2r × abuse limited to {0, 0.2} — **PROPOSED** (the
registration wall's abuse response is structural — abusers either
pre-register m identities or lose them — so two prevalence points
bound it; the full grid adds cells without a hypothesis).

## Design choices open for chair review

1. **M2v verification: one work item per identity at first entry**
   (not per poll).
2. **M2r entry semantics: reject-at-entry** (fast edge answer for
   walk-ups).
3. **Deposit forfeiture accounting** — the deposit prices multi-win
   forfeiture given D6.4's losers-refunded model; d* computed from
   per-controller win distributions; a large d* is an acceptable
   finding.
4. **Costed-burst cell list: center cells only** (no uptake/abuse ×
   c_push cross).
5. **M2r abuse grid limited to {0, 0.2}** (structural response, two
   points bound it).

Each lands as a decision entry; tasks.md (with the D4.1 coverage
table) follows once these are ruled.
