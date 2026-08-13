# tatkal-v3 — design

**Status:** approved 2026-08-13 (D8). Every constant and semantic
below is registered by decision entry — nothing here is PROPOSED.
D6-registered constants are cited, not re-opened.

**Inputs:** requirements.md (ratified, D7); v3 ledger D1–D8; the v2
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
  archive). One item per identity, not per poll — **registered
  (D8.1)** (the alternative, re-verification per poll, models a
  stateless verifier and multiplies load; not what real verification
  does).
- **Verification is cached per identity, not per entry (D8.1 rider):**
  an identity that re-enters the pool under the R4 retry sweep does
  NOT re-verify. Stated because v3 sweeps `p_retry` and the
  interaction would otherwise be undefined.
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
- **Entry semantics — registered (D8.2): reject-at-entry.** An
  unregistered identity's pool entry gets an edge MECH_REJECT (fast
  definitive, v1 reject semantics) rather than silent exclusion at the
  draw. Rationale: walk-ups learn their fate in milliseconds instead
  of waiting Q for a draw they were never in; the alternative
  (exclude-at-draw) manufactures deliberate wait for users the
  mechanism has already decided against.
- **Out-of-model note (D8.2 rider):** reject-at-entry is also a fast
  oracle for registration state. Under the D3 fixed repertoire no
  simulated abuser exploits it, so there is no in-model effect — it is
  named in honest framing and never quantified.
- Honest-user cost metric (D6.2): walk-up rejection count/rate per
  r_reg cell — the fairness-vs-inclusion trade-off is this arm's
  finding, reported as a function of uptake.
- Workload note: registration flags for M2r identities are arm-side
  behaviour of existing cohorts (exactly as M1's were) — no D3
  population change.

## Deposit arm — forfeiture accounting (analysis module)

D6.4 registers: seat value 1, **losers refunded**. The design
consequence, **ruled at D8.3** — this is what the deposit prices:

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

- **Cell list — registered (D8.4): center cells only.** M1 at
  r_reg = 0.8 and M2 at p = 0.2, each × c_push {¼, ½, 1, 2} ×
  3 variants × 20 seeds (zero cells already exist in the v2 archives).
  Full uptake/abuse × c_push crosses would quadruple the family for a
  second-order interaction no hypothesis names. D8.4 notes this
  amends nothing: ratified R3 already reads "M1 (center uptake) and
  M2 (center abuse)".
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
| M2r (r_reg {.5,.8,.95} × p {0,.1,.2,.4}) | 12 × 3 | 720 |
| costed bursts (2 arms × 4 c_push) | 8 × 3 | 480 |
| M3 retry (3 values) | 3 × 3 | 180 |
| **total** | **105 cells** | **2,100** |

Both running mitigation arms carry the **full** D3 abuse grid
p ∈ {0, 0.1, 0.2, 0.4} — **registered (D8.5)**. The draft proposed
narrowing M2r to {0, 0.2} on the grounds that the registration wall's
abuse response is structural; the chair rejected it. Ratified R2 binds
all three arms to the same abuse grid, so narrowing one is a
requirements amendment rather than a design choice, and none is made.
Substantively: the deposit arm never runs, which makes M2v vs M2r the
live head-to-head, and D5 makes the comparison across arms the
finding — two common prevalence points is too thin a basis for it.
The ruling costs +6 parameter cells / +360 runs against the draft.

## Design choices — all ruled (D8)

The five choices this document put to the chair were ruled on
2026-08-13. Four approved (1 and 2 with riders now folded into the
arm sections above), one rejected:

| # | choice | ruling |
|---|---|---|
| 1 | M2v: one work item per identity at first entry | approved + rider: verification cached per identity, no re-verify under retry |
| 2 | M2r: reject-at-entry | approved + rider: registration oracle named as out-of-model |
| 3 | deposit prices multi-win forfeiture; large d\* acceptable | approved |
| 4 | costed bursts: center cells only | approved (confirmatory — matches ratified R3) |
| 5 | M2r abuse grid {0, 0.2} | **rejected** — full grid stands (D8.5) |

Next: tasks.md with the D4.1 bar × cell coverage table, checked
against the budget above.
