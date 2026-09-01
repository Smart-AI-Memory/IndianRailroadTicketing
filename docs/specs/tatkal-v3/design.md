# tatkal-v3 — design

**Status:** draft — proposed (2026-09-01); awaiting chair approval at
the design gate. Constants marked **PROPOSED** become **registered**
by the approving decision entry; DC1–DC6 are the choices the chair
rules on.

**Inputs:** requirements.md (draft), decisions.md D1–D11,
`../tatkal-v2/design.md` (the machinery being extended),
`../tatkal-v2/population-derivation.md` (D13, carried verbatim by
D3).

---

## Shape of the extension

v3 adds identity-pricing to the M2 draw path, a deadline-shaped
registration surface, and two sweeps over machinery that already
exists (bursts, retries). No new simulator concepts beyond one:
**priced entry** — an identity's admission to a draw pool can carry a
cost in work, stake, or eligibility.

- The v2 allocation-event machinery (V2.1), burst costing (V2.2),
  identity structure (V1.1), and two-clock metrics (V2.4) carry
  unchanged.
- v1 and v2 arms compile and run untouched (R1); mitigation is
  composed onto the M2 path as entry filters/costs, not as changes to
  the draw itself — the draw stays a uniform lottery over admitted
  unique identities, so every v3/v2 fairness delta is attributable to
  the pricing, not to a changed allocation rule.

## Arm A1 — verification-cost (R2.1)

Entry pipeline: an identity arriving in the qualification window
submits entry → a verification work item (service time `c_verify`)
is enqueued on the **shared worker pool** → the identity joins the
draw pool only when its verification completes **before the draw
instant**; unverified-by-draw identities are resolved as clean
rejections in the burst (their outcome stream is labelled
`verify-missed`, distinct from lottery-loss — R4.1 carry).

- **DC1 — `c_verify` grid PROPOSED:** {¼, 1, 4} × the booking app
  service time. ¼ = cheap check (cache hit against a pre-verified
  registry), 1 = as expensive as booking work itself, 4 = a real
  document-check-shaped cost. The grid deliberately brackets the
  bottleneck-moving threshold: at 4× with the full pool entering,
  verification demand exceeds the window's total service capacity by
  construction, so the mechanism MUST degrade — what matters is how
  (clean `verify-missed` rejections vs. contention collapse).
- Verification-pool wait is logged per identity; its floor is the
  work-conservation arithmetic (entries × c_verify ÷ pool capacity),
  enumerated per D4 rule 2.
- Abuse-pricing statement (owed per R2 before running, drafted here):
  *an abuser pays m verifications to gain m draw tickets; the
  currency is shared-pool work, so the abuser's price is also
  everyone's congestion — the arm's fairness gain and its
  self-inflicted load are the same number, measured twice.*

## Arm A2 — deposit (R2.2)

Entry stakes `d` (ticket value normalized to V = 1). Refunds: losers
refunded in full at the draw burst; **an unredeemed winning identity
forfeits its stake** (one controller redeems at most one seat;
auto-redeem carries from v2 M1 for the redeemed seat).

- **DC2 — abuser entry rule PROPOSED (deterministic, no learning):**
  a controller holding m identities enters k of them, where k
  maximizes `E[seats won | k] · V − E[extra wins | k] · d`, computed
  under the pool-size expectation the abuser would form from the
  registered population (all constants public inside the model; no
  private information). At d = 0 this degenerates to k = m — the v2
  unmitigated cell, which is the continuity check.
- **DC3 — `d` grid PROPOSED:** {0.1, 0.5, 2} × V. Below win-value,
  near it, and punitive.
- Honest users are deposit-insensitive (requirements R2.2 default):
  they enter their one identity at any d in the grid. The regressive-
  profile readout (Honest framing) is therefore *modelled* as zero in
  v3 and MUST be reported as an unmodelled harm axis, not as
  evidence of harmlessness.
- Abuse-pricing statement (draft): *the marginal identity's price is
  the expected forfeiture on its excess win; abuse becomes
  economically self-defeating exactly when d exceeds the marginal
  ticket's expected value — the grid brackets that point.*

## Arm A3 — registration-bound (R2.3)

Only identities registered in the pre-window [T0−W, T0) may enter
the draw; W = 300 s carries from v2 M1 (D14). Allocation stays the
qualification-window lottery (M2 semantics with an eligibility
filter), so A3 differs from v2's M1 in exactly one respect worth
isolating: entry happens at T0 under M2 rules, but eligibility was
priced earlier, in calendar time an abuser must have spent per
identity.

- **DC4 — deadline-spike registration profile PROPOSED (R5.1):**
  40% of registrants uniform over W; 60% concentrated in the final
  10% of W with the same σ-shaped concentration machinery as the T0
  spike (σ_reg = σ_T0, aimed at T0−ε). Camp bots register in the
  first 5% of W (D13.3 carry — camping the *open* is the bot shape;
  the deadline crowd is the human shape). The uniform profile (v2
  M1's model) runs as a labelled variant so the deadline delta is
  itself a result (R5.1 acceptance).
- Registration requests are costed server work (v2 M1 carry);
  under the deadline profile the registration surface is a genuine
  second spike — the v2 triviality finding (§6) gets its stress
  test here without a fourth arm.
- Abuse-pricing statement (draft): *the marginal identity's price is
  enrollment in advance — an abuser must have held and registered m
  identities before T0; the arm is strong against opportunistic
  abuse and weak against patient abuse, and the m = 5 registered
  abuser measures exactly the patient case.*

## R3 sweep — costed M1/M2 bursts

Machinery exists (V2.2); the cells were never run. Grid: c_push ∈
{¼, ½, 1, 2} × status service time (zero cells = v2 record, reused
per center-cell rule). Arms at their v2 center cells (M1 r_reg = 0.8;
M2 p = 0.1). Floors per grid point: **max(burst drain,
winner-redemption drain)** with both components enumerated (D1
amended rule; the D18.2 miss is the origin story).

## R4 sweep — M3 retry sensitivity

- **DC5 — `p_retry_after_reject` grid PROPOSED:** {0, 0.25, 0.5, 1.0}
  (0 = v2 record cell, reused). Retry timing per the v1 retry model
  unchanged; the knob is re-entry probability only (population
  otherwise untouched per D3).
- Censoring control (R4.2 carry): whole-run TTDA is censoring-prone
  across retry chains — the registered companion is the per-tranche
  post-event resolution clock; both reported.

## R9 — MariaDB anchor run

`tools/r2_server.py` gains an engine flag (Postgres default,
MariaDB via the same SQL surface — `SELECT … FOR UPDATE` decrement);
`tools/calibrate_r2.py` runs the identical ladder (concurrency
1…256, ≥ 3 reps).

- **DC6 — shape criteria PROPOSED** (R9; registered before the run):
  *confirmed* iff (a) an identifiable knee exists; (b) p50 at 8× knee
  concurrency ≤ 2× p50 at the knee; (c) p99 at 8× knee ≥ 10× p99 at
  the knee. Anything else falsifies engine-independence and is
  reported as such, with the synthesis addendum updating threat #1
  either way (D8/D11).

## Measurement

- Fairness: controller-level draw-share advantage, unchanged from v2
  (D5 metric carry) — the mitigation arms change *entry*, not the
  draw, so the metric transfers by construction.
- **Honest-cost readout (first-class per Honest framing):** per arm,
  honest users report both clocks, verification wait (A1), stake-at-
  risk exposure time (A2, report-only), and registration burden (A3:
  the deliberate pre-window action). Reported per cohort, not only
  in aggregate.
- New outcome streams: `verify-missed` (A1), `forfeit` (A2),
  `ineligible` (A3) — distinct in the taxonomy (R4.1); no report
  path sums them with errors or lottery-loss.
- Three-variant bracketing (R4.3) carries: every headline claim gets
  the plateau/fitted/cliff table; A1's verification load under the
  cliff variant is the expected dark corner (the v1 rung-4 lesson,
  new subsystem).
- Paired-seed harness, 20-seed floor, B = 10,000 bootstrap, Holm
  within family: all carry.

## Floors (owed at Gate B, derivations enumerated per D4 rule 2)

- A1: verification-pool drain floor (entries × c_verify ÷ capacity)
  per grid point, **plus** the booking-path floors it composes with.
- R3 cells: max(burst drain, winner-redemption drain) per c_push
  point.
- M3: per-tranche drain floors and whole-run H + last-drain floor
  (v2 carry), re-stated per p_retry point where re-entry adds drain.
- Every derivation lists included components and why the omitted are
  irrelevant.

## Cell budget (for the tasks ladder; final list is tasks.md + Gate B)

| family | cells | seeds | runs |
|---|---|---|---|
| A1: c_verify {¼,1,4} × p {0,.1,.2,.4}, fitted | 12 | 20 | 240 |
| A2: d {.1,.5,2} × p {0,.1,.2,.4}, fitted | 12 | 20 | 240 |
| A3: profile {deadline,uniform} × p {0,.1,.2,.4}, fitted | 8 | 20 | 160 |
| Arm-center 3-variant bracketing (3 arms × center cell × plateau/cliff) | 6 | 20 | 120 |
| R3 bursts: 2 arms × c_push {¼,½,1,2}, fitted | 8 | 20 | 160 |
| R3 bracketing at c_push = 1 (2 arms × 2 variants) | 4 | 20 | 80 |
| M3: p_retry {.25,.5,1} × 3 variants | 9 | 20 | 180 |
| **total new evaluated runs** | **59** | | **1180** |

v2 record cells (zero/center anchors) are reused, not re-run
(center-cell rule). ~1.5× the v2 sweep; laptop-scale per R1's DES
constraint.

## Out of scope

Two-phase inventory (A2's forfeiture rule is the utility-level
stand-in), honest-user price sensitivity (reported as an unmodelled
axis), adaptive bots, distributed load, new ML — all per D2/D3.

## Design choices for the chair (DC1–DC6)

| # | Choice | Proposed |
|---|---|---|
| DC1 | `c_verify` grid | {¼, 1, 4} × app service time |
| DC2 | Abuser deposit-entry rule | deterministic expected-value k*, no learning |
| DC3 | `d` grid | {0.1, 0.5, 2} × V |
| DC4 | Deadline registration profile | 40% uniform + 60% final-10% spike, σ_reg = σ_T0; uniform as labelled variant |
| DC5 | `p_retry` grid | {0, 0.25, 0.5, 1.0} |
| DC6 | Anchor shape criteria | knee exists; p50 ≤ 2×; p99 ≥ 10× at 8× knee |

Approval of this document registers DC1–DC6 as proposed unless
individually amended in the approving entry.
