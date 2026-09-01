# tatkal-v3 — requirements

**Status:** RATIFIED (2026-09-01, D12) — authored under the opened
D6 gate (synthesis PR #10 merged). Every numeric constant is carried
with its source named, **registered at the design gate** (D13), or
marked **UNSET** (fixed by decision entry before any run that
depends on it — D1 pre-registration discipline; bars and guards land
at Gate B).

**Purpose:** determine which currency of identity-pricing reclaims
the lottery's fairness under abuse and at what cost to honest users;
close v2's costed-burst coverage gap for the allocation arms; and
give v2's M3 negative its retry-sensitivity analysis.

**Source:** v3 decisions ledger D1–D11 (`decisions.md`), seeded by
the ratified v3 starter (`../tatkal-v2/v3-starter.md`); factual
baseline is the v2 graded record (`../tatkal-v2/RESULTS.md`, sealed
D19) as synthesized with transfer limits in
`../../v1-v2-synthesis.md`.

---

## Problem

v2 established that allocation mechanisms — not engineering — produce
bot/human fairness, and quantified the attack that remains:

- **Unmitigated lotteries pay identity abusers ≈ m** (the identities
  they hold) at low prevalence; abuse self-dilutes at scale but
  honest-user fairness degrades monotonically with prevalence.
  Mitigation, not prevalence, is the open lever (v2 §2).
- **The costing lesson generalizes:** v1's waiting room survived
  until its own notification channel was costed, then died (v2 §3).
  v2's M1/M2 cells ran at `c_push = 0` only — the allocation arms'
  own burst channel is uncosted, exactly the class of gap that killed
  the waiting-room claim. Synthesis C3: *a mechanism whose benefit
  case leaves its own infrastructure uncosted is unevaluated.*
- **M3's double negative is contingent:** fairness breach and
  inventory starvation were measured at `p_retry = 0`, where rejected
  demand leaves forever. The negative's sensitivity to the retry
  model is unmeasured (v2 §4).

v3 therefore has three jobs, fixed by D2:

1. price identities inside M2 three different ways and find which
   reclaims parity under abuse (D5 arms, D9 modelling);
2. run M1/M2 across the registered `c_push` grid (D14.2 carry),
   under the amended floor rule (D1/D18.2);
3. sweep `p_retry_after_reject` for M3.

## Experimental framing

> Which identity-pricing currency — work, money, or enrollment —
> reclaims lottery parity under multi-identity abuse, at what cost to
> honest users, and without merely moving the contention bottleneck
> to its own pricing infrastructure? Do the allocation arms' fairness
> results survive costed notification bursts? Does rejected-demand
> re-entry rescue paced drain?

Framing conventions carry from v1/v2 (D1): no mechanism is assumed to
work before measurement; a correctly measured negative is a
successful outcome; simulated mechanisms carry no policy authority.

---

# Requirements

## R1 — extend the v2 simulator; v1 and v2 physics preserved

v3 extends `src/tatkal_sim` in place. v1 and v2 arms MUST remain
runnable unchanged; they are v3's baselines and its regression check.

### Acceptance

- The full v1+v2 test suite passes unmodified on the v3 tree.
- A designated v2 arm re-run under the v3 tree reproduces its v2
  metrics within the registered tolerance (**carry**: the V0.2
  tolerance entry; if v3 needs its own value it is **UNSET** until a
  decision entry).

## R2 — identity-mitigation arms (D2.1, D5, D9)

Three arms, each pricing an identity in a different currency. The
**cross-arm comparison is the finding** (D5). Each arm MUST state,
before running, its **abuse-pricing statement** — the v3 analogue of
v2's F5 statement: *how does this arm make an abuser's marginal
identity cost more than an honest user's single identity?* No
statement, no run.

Modelling discipline for all three (D9): swept, capacity-bounded
costs — **never invented latency distributions**. Infrastructure an
arm depends on is either an explicit bounded resource with a swept
parameter, or explicitly declared free with the declaration carried
into the results as a limitation.

### R2.1 — verification-cost arm (work-priced)

Each identity entering the draw costs a verification work item
executed on the **shared worker pool** (D5). Per D9 the pool is the
existing bounded-queue machinery; the knob is per-verification
service cost `c_verify`, a **swept parameter** (grid **PROPOSED** at
design). Verification work lands when the identity enters the pool —
inside the qualification window for M2-shaped entry — so heavy
verification directly loads the spike surface. **The arm is
explicitly evaluated for bottleneck-moving:** verification-pool wait
is reported as its own stream with its own floor (D4 rule 2).

### R2.2 — deposit arm (money-priced)

Entry stakes a deposit `d`, refunded to losers (D5); an abuser's
extra winning identities forfeit their deposits when not redeemed
(one controller redeems at most one seat). `d` is a **utility
parameter, not a payment flow** (D5 — payment processing stays
deferred). The abuser's entry decision is a registered deterministic
rule over `d` and expected win value (model **PROPOSED** at design;
no learning, D3 bot-repertoire freeze). Honest users are
deposit-insensitive by default (**PROPOSED**; any price-sensitivity
model for honest users is a population change requiring a decision
entry under D3).

### R2.3 — registration-bound arm (enrollment-priced)

Only identities registered in a pre-window may enter the draw — the
M1×M2 hybrid (D5). The registration surface is NOT idealized:
arrivals follow a **deadline-spike profile** (D9; profile constants
**PROPOSED** at design) because v2's uniform-registration triviality
finding (v2 §6) is scale- and shape-dependent, and deadline
concentration is the realistic adversarial shape. R2.1's
verification-cost composition with this arm is a labelled variant,
not a fourth arm.

### Acceptance (all of R2)

- Each arm's parameters, entry/decision rules, and abuse-pricing
  statement are fixed by decision entry before its first evaluated
  run.
- Each arm reports: controller-level draw-share advantage (the D5/v2
  fairness metric, carried), honest-user cost (both clocks, and any
  arm-specific price paid), and — for R2.1/R2.3 — the pricing
  infrastructure's own load stream and floor.
- The unmitigated-M2 comparison (R6) exists for every abuse
  prevalence cell the arm runs at.

## R3 — costed M1/M2 notification bursts (D2.2)

Run M1 and M2 across the registered shared `c_push` grid
(**carry:** {0, ¼, ½, 1, 2} × status service time, v2 D14.2; the
zero cells are the v2 record, reused per the center-cell rule).

- The amended floor rule is binding (D1): post-event floors are
  **max(burst drain, winner-redemption drain)**, with every drain
  component enumerated (D4 rule 2).
- Per D4 rule 1, every per-grid-point bar registered here MUST map to
  a planned cell in tasks.md **before** gate approval — this
  requirement exists because v2 registered bars for cells it never
  ran.

### Acceptance

- Every registered (arm × c_push) bar has a planned cell; the
  coverage check is part of the tasks-gate checklist.
- Loser-clock and combined post-event p99 graded per grid point
  against floors stated per grid point (or bound at the registered
  worst case, stated at registration).

## R4 — M3 retry-model sensitivity (D2.3)

Sweep `p_retry_after_reject` (grid **PROPOSED** at design; MUST
include 0 — the v2 record cell, reused) for the M3 paced-drain arm.

- Question registered in advance: does re-entering rejected demand
  recover **inventory** (v2: 125/200 starved) and **fairness** (v2:
  guard breached, camp bots feast per-tranche)?
- v1's horizon-censoring lesson is binding here (v2 R4.2 carry): any
  metric running to a definitive across the retry chain MUST be
  checked for censoring before registration, with a censoring-robust
  companion registered alongside — the per-tranche post-event clock
  is the default candidate.

### Acceptance

- Per-tranche and whole-run inventory, fairness, and retry
  amplification reported at every grid point; the v2 cell reproduces
  within the R1 tolerance.

## R5 — fidelity: carry everything, plus the deadline surface

v1 R3.1–R3.10 and v2's additions (error taxonomy R4.1,
censoring-robust metrics R4.2, three-variant bracketing R4.3) carry
unchanged. One addition:

### R5.1 — deadline-spike registration arrivals (D9)

The registration surface for R2.3 (and R2.1 where composed) is
modelled with the same arrival machinery as the T0 spike, aimed at
the window close. Uniform registration (the v2 M1 model) remains
available as a labelled variant so the deadline effect is itself
measurable — the delta between the two profiles is a reported
result, not an assumption.

## R6 — baselines (fixed before any evaluated run)

- **Mitigation baseline:** v2's unmitigated M2 at each abuse
  prevalence cell (the v2 record where the population is unchanged —
  D3 carries it verbatim, so v2 archived cells are legitimate
  comparators; any re-run replaces them only via decision entry).
- **Engineering comparator:** v2's rung 2 under the v2 population
  (archived).
- **Parity anchor:** v2's M2 at p = 0.
- **For R3:** the v2 `c_push = 0` M1/M2 cells anchor the sweep.
- **For R4:** the v2 M3 cell (p_retry = 0) anchors the sweep.

Cross-version comparability is the payoff of D3; it holds only while
the population is untouched, which is why population additions
require decision entries.

## R7 — population and seeds (D3)

The v2 registered population (D13) carries **verbatim**: cohorts,
operating scale, σ_T0, the 60/30/30/30 strategy mix with the
degenerate-form rule, m = 5, abuse prevalence grid
p ∈ {0, 0.1, 0.2, 0.4}, the 20-seed universal floor, and the
center-cell rule. The bot repertoire stays fixed; co-evolution stays
deferred.

New v3 axes (mitigation-strength grids: `c_verify`, `d`,
`p_retry_after_reject`; deadline-profile constants) are **mechanism
parameters, not population changes** — they are registered at the
design gate. Anything that changes who arrives, when, or with what
strategy is a population change and requires its own decision entry.

## R8 — pre-registered evaluation criteria

All v2 R7 machinery carries: floor-aware bars (derive floor → state
distance → register by entry; no floor statement, no bar), the D5
no-metric-no-guard-no-run rule, paired per-seed deltas with 95% CIs,
no CI-overlap API, "did not help" = CI includes zero, and a
multiplicity policy registered before any evaluated run (v2
precedent: Holm within family over the inventoried comparisons).

v3-specific bindings (D4):

1. **Bar-cell coverage:** the tasks gate does not pass while any
   registered bar lacks a planned cell.
2. **Floor completeness:** every floor derivation enumerates its
   drain components — for v3 that includes the verification-pool
   drain (R2.1), burst drain and winner-redemption drain (R3), and
   per-tranche drains (R4) — and states why omitted components are
   irrelevant.

All bar values, guard values, effect-size and regression bounds:
**UNSET** by design until the Gate-B entry, per D3-carry procedure.

## R9 — second calibration anchor (D8, D10, D11)

A MariaDB/MySQL run behind the existing R2 harness
(`tools/r2_server.py`, `tools/calibrate_r2.py`): same endpoint
semantics, same concurrency ladder, ≥ 3 reps, same machine.

**Shape criteria, registered before the run** (constants **PROPOSED**
at design; fixed by entry before execution): the Postgres-anchor
shape is *confirmed* if the MariaDB curve shows (a) an identifiable
knee, (b) p50 flat within a registered factor across the ladder, and
(c) p99 degradation past the knee exceeding a registered multiple
while p50 stays flat. Any other outcome is a *falsification of
engine-independence* and is reported as such.

### Acceptance

- Raw CSV committed under `calibration/`; criteria graded in a short
  report; an addendum to `docs/v1-v2-synthesis.md` updates
  threat-to-validity #1 **whichever way the result goes** (D8).
- The MariaDB install is recorded in the README when it happens
  (D11).

## R10 — ML scope

No new ML work in v3 (carry of v2 R8; D2 keeps co-evolution
deferred). The bot repertoire is a fixed probe. The v1 classifier is
not run inside mitigation arms.

---

# Explicitly deferred from v3 (D2)

Deferred, not rejected: two-phase inventory / seat-hold (would fix
M2's ghost race and enable real redemption windows — the deposit
arm's forfeiture rule is the utility-level stand-in); adversarial bot
co-evolution; distributed load; autoscaling; payment processing;
multi-region; production auth / CAPTCHA; production traffic replay;
anything that contacts IRCTC.

---

# Safety and experimental boundary

Carried verbatim from v1 (D1):

This prototype MUST remain a simulation/calibration experiment.

It MUST NOT send load or automated booking requests to IRCTC.

The v3 experiment MUST use synthetic workloads and a locally
controlled calibration service/database.

No claim should be made that the prototype has solved the production
IRCTC system unless independently supported by evidence.

---

# Honest framing

Identity-pricing mechanisms are **regressive by construction** unless
proven otherwise: a deposit prices out the poor, verification prices
out the poorly-connected, enrollment prices out the late-informed.
v3 results MUST therefore be reported in terms of *who each
mitigation disadvantages* — the honest-user cost readout is
first-class, not a guard footnote. A mitigation that reclaims parity
by pricing out honest cohorts along with abusers has not produced
fairness; it has relocated unfairness somewhere the fairness metric
does not look. Simulated results carry no authority over real-system
policy (D1, verbatim).

---

# Expected result

Pre-stated so that finding it is not mistaken for disappointment:

> All three arms reclaim most of the parity lost to abuse, in
> different corners: registration-bound cheapest for honest users but
> weakest against patient abusers; deposit strongest against abuse
> economics but carrying the worst regressive profile; verification-
> cost effective only until `c_verify` moves the bottleneck to its
> own pool — with the deadline-spike profile, not the mitigation,
> deciding whether the registration surface survives. Costed bursts
> degrade loser clocks without touching allocation fairness. M3
> recovers inventory partially under re-entry while its fairness
> breach persists.

A negative on any clause — including "no arm reclaims parity without
unacceptable honest-user cost" — is a valid outcome if correctly
measured. Per D1's honest framing, that outcome would itself be the
finding.

---

# Definition of done for the requirements phase

- R1–R10 reviewed and ratified by decision entry.
- Every arm has a measurable acceptance condition and owes an
  abuse-pricing statement before running.
- Every PROPOSED constant is fixed at the design gate; every UNSET
  constant is traceable to the entry that must fix it.
- Baselines (R6) fixed before any evaluated run; v2-record reuse
  cells identified explicitly.
- The bar-cell coverage check and floor completeness rule are wired
  into the tasks gate checklist.
- Multiplicity policy registered before evaluation.
- v3/v4 boundaries explicit (deferred list above).
- No experiment requires contacting IRCTC.
