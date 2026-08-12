# tatkal-v3 — requirements

**Status:** draft (2026-08-12) — awaiting chair ratification. Every
numeric constant is carried with its source named or explicitly marked
**UNSET** (fixed by decision entry before any dependent run, per D1).

**Purpose:** determine which way of pricing identities reclaims
lottery parity under abuse and at what cost to honest users; complete
the costing story for the allocation arms; and measure whether v2's
M3 negative survives realistic retry behaviour.

**Source:** v3 ledger D1–D5; factual baseline is the v2 graded record
(RESULTS.md, chair-approved, sealed D19).

---

## Problem

v2 settled the headline: allocation mechanisms deliver bot parity
where engineering delivers only an orderly latency contest. Three
edges remain open, and they are v3's scope (D2):

1. **The lottery's parity is unguarded against identity abuse.** An
   unmitigated M2 pays an abuser ≈ m at low prevalence; honest-user
   fairness degrades monotonically with prevalence. Mitigation — not
   prevalence self-dilution — is the open lever.
2. **The allocation arms' notification bursts were costed only at
   zero.** v2 proved the waiting room dies at ¼ of a status check per
   push; whether M1/M2's fairness wins carry a similar latency price
   is unmeasured (the un-run D14.2 grid).
3. **M3's double negative was measured at p_retry = 0** — the corner
   where rejected demand vanishes. Its sensitivity to the retry model
   is unknown.

## Experimental framing

The experiment is designed to answer:

> Which identity-pricing mechanism — work (verification), money
> (deposit), or enrollment (registration binding) — reclaims M2's
> parity under abuse, and what does each cost honest users? Do M1/M2
> survive realistically costed notification? Does paced drain recover
> when rejected users re-enter?

Conventions carried (D1): no mechanism assumed to work before
measurement; negatives are valid outcomes; simulated mechanisms carry
no policy authority.

---

# Requirements

## R1 — simulator reuse; two continuity anchors

v3 extends the v2 tree; v1 and v2 arms MUST remain runnable unchanged.

- The v1 physics anchor (v2 tests) stays in CI untouched.
- **NEW v2-continuity anchor:** an M2 arm with mitigation disabled at
  c_push = 0 MUST reproduce the corresponding v2 cell bit-identically
  (the D3 population carry makes this exact reproduction possible;
  tolerance: exact, carrying v2's D16 convention — re-registered for
  v3 by decision entry at V0).

## R2 — identity-mitigation arms (D5)

All three arms mitigate the SAME base mechanism (v2's M2 at Q = 5 s)
and are evaluated against the same abuse grid (D3: p ∈ {0, 0.1, 0.2,
0.4}, m = 5). Per-arm fairness metric: controller-level draw-share
advantage (carried); each arm additionally defines its honest-user
cost metric below — registered before guards per the carried D5
discipline.

### R2.1 — verification-cost arm (work-priced)

Every identity entering the pool triggers a verification work item on
the **shared worker pool** (the D14.2 costing pattern): cost factor
`c_verify` × status check, `c_verify` **UNSET** (grid registered
before runs; the verification stampede is itself a spike surface and
MUST be measured as its own load stream).

- Only identities whose verification completes by the draw enter it;
  later verifications fall through to post-draw fast-fail. The
  timing rule (verify-by-draw) is part of the arm's registration.
- Honest-user cost metric: added latency and the entry-exclusion rate
  for honest users whose verification misses the draw.
- Hypothesis mechanics: abusers pay m verifications per draw; the
  shared pool makes everyone pay for the abusers' verifications.

### R2.2 — deposit arm (money-priced; accounting model)

Entry stakes a deposit `d` per identity (abstract utility units —
explicitly NOT payment processing, which stays deferred; D5). Losers
are refunded; the deposit prices the *risk-free multiplication* of
entries.

- **Fixed-repertoire consequence (stated honestly):** under D3 the bot
  repertoire does not adapt, so a deposit deters no simulated
  behaviour. The arm is therefore an **accounting arm**: it reports
  the abuse-economics statement — at deposit d and prevalence p, an
  abuser's expected net utility per draw — and the threshold d* where
  abuse becomes net-negative.
- **Optional behavioural variant (needs a chair entry per D3):** a
  static, pre-registered abuse budget B per abuser, entries =
  min(m, floor(B/d)). Not adaptation — a fixed budget constraint —
  but it adds a population parameter and therefore requires a D3
  amendment entry before it may run. Flagged as an open decision.
- Honest-user cost metric: deposit friction is reported qualitatively
  (a real deposit excludes the unbanked; the simulation cannot price
  this and MUST NOT pretend to — honest-framing item).

### R2.3 — registration-bound arm (enrollment-priced; M1×M2 hybrid)

Only identities registered during a pre-window [T0 − W_b, T0) may
enter the draw (M1's registration machinery over M2's pool); W_b
**UNSET** (candidate: carry W = 300 s).

- Registration one-shots are costed as in M1 (v2 R2.1 carry);
  abusers must pre-register all m identities.
- **The cost is borne by honest walk-ups:** unregistered honest users
  are excluded from the draw. Honest-user cost metric: the walk-up
  exclusion rate at the carried r_reg grid {0.5, 0.8, 0.95} — the
  fairness-vs-inclusion trade-off IS this arm's finding.

## R3 — costed M1/M2 notification bursts (D2.2)

M1 (center uptake) and M2 (center abuse) re-run across the full
D14.2 c_push grid {0, ¼, ½, 1, 2} × status check.

- Floors per the amended rule (D18.2, binding via D1): post-event
  floor = max(burst drain, winner-redemption drain), with the D4.2
  completeness enumeration.
- Bars per grid point; **every bar maps to a planned cell (D4.1)** —
  the tasks.md cell list is checked against the bar list at gate
  approval.
- Fairness guards re-evaluated at each grid point (costing must not
  silently change who wins; expected: fairness is costing-independent
  — a stated prediction, cheap to check).

## R4 — M3 retry-model sensitivity (D2.3)

M3 re-run over a `p_retry_after_reject` grid, **UNSET** (candidate:
{0, 0.3, 0.7, 1.0}; the 0 cell MUST be the v2 cell, reproduced
bit-identically as a third anchor).

- Measured per cell: seats sold (inventory recovery), whole-run and
  per-tranche F-ratio, retry amplification per tranche, and the
  v2-carried latency clocks.
- The open question stated as a two-sided hypothesis: retry may
  recover inventory while leaving fairness camped (campers also
  benefit from re-entry), or recover both, or amplify into the
  congestion regime (R3.2's spiral) — no direction is assumed.

## R5 — baselines and comparisons

- **Mitigation arms (R2)** are compared against **v2's unmitigated M2
  cells** on paired seeds (the D3 carry makes v2's archived cells
  directly reusable — same population, same seeds; the v2-continuity
  anchor in R1 proves it). Rung 2/rung 4 context columns carry from
  the v2 archives.
- **R3 cells** compare against their own zero-cost anchors.
- **R4 cells** compare against the v2 M3 cell (p_retry = 0).
- v1 absolute numbers remain non-citable (v2 D12 carries).

## R6 — population (D3)

Carried verbatim from v2's D13 — cohorts, scale, σ_T0, mix,
degenerate-form rule, m = 5, abuse grid, 20-seed universal floor,
center-cell rule. The only candidate addition is R2.2's abuse budget
B, which requires its own entry before any run uses it.

## R7 — pre-registered evaluation criteria

All carried: floors before bars (amended floor rule + D4.2
completeness), per-mechanism fairness metrics before guards, paired
per-seed bootstrap CIs (B = 10,000, seeded), no CI-overlap API,
three-variant bracketing, two-clock reporting, misses reported never
adjusted. Registered before any evaluated run:

- the comparison inventory and **multiplicity policy** (v2 precedent:
  Holm within family — carried as the default candidate, confirmed or
  amended at the gate);
- every bar with floor distance AND its evaluating cell (D4.1);
- guard values per arm (candidates: the carried 1.05 zero-abuse guard;
  the ≤ m guard for unmitigated comparisons; mitigation arms
  additionally guard honest-user cost — values UNSET).

## R8 — ML scope

None. The repertoire stays fixed (D3); co-evolution stays deferred.
The deposit arm's economics are computed, not learned.

---

# Explicitly deferred from v3 (D2)

Two-phase inventory / seat-hold; adversarial co-evolution; real
distributed load / autoscaling; payment processing (the deposit is an
abstraction, not a payment flow); multi-region; production auth;
CAPTCHA; traffic replay; anything contacting IRCTC.

---

# Safety and experimental boundary

Carried verbatim (D1): simulation/calibration only; MUST NOT send
load or automated booking requests to IRCTC; synthetic workloads and
locally controlled services only; no claim of having solved production
IRCTC without independent evidence.

---

# Honest framing

- Mitigation results are evidence for study, not policy
  recommendations. Each pricing mechanism excludes someone: work
  pricing excludes the slow-of-device, money pricing excludes the
  unbanked, enrollment pricing excludes the unaware. The simulation
  measures the in-model costs and MUST name the out-of-model ones it
  cannot measure.
- The deposit arm is an accounting model over fixed behaviour; its d*
  threshold is an economic statement about the modelled utilities,
  nothing more.

---

# Expected result

The experiment is designed so that the following outcome is
acceptable:

> Registration binding reclaims parity fully but prices out walk-up
> honest users in proportion to (1 − r_reg); verification pricing
> reduces abuse advantage roughly in proportion to its cost while
> taxing every honest user's latency through the shared pool; the
> deposit analysis identifies a finite d* at every prevalence;
> costed bursts move M1/M2's latency bars but not their fairness;
> and M3 recovers inventory with retry while fairness stays camped.

This is a hypothesis, not a guaranteed result; a negative on any
clause — including "no mitigation reclaims parity without an
unacceptable honest-user cost" — is a valid outcome if correctly
measured.

---

# Definition of done for the requirements phase

- R1–R8 reviewed and ratified by decision entry.
- Every UNSET constant listed and traceable to its future entry
  (c_verify grid, d grid, W_b, p_retry grid, guard values, budget B
  if admitted).
- The R2.2 behavioural-variant question (abuse budget) is ruled
  before design.
- Every arm has a fairness metric AND an honest-user cost metric.
- Bar-cell coverage (D4.1) and floor completeness (D4.2) are wired
  into the gate checklist.
- The three anchors are named: v1 physics, v2 continuity
  (mitigation-off M2), v2 M3 cell (p_retry = 0).
- v3/v4 boundaries explicit (deferred list above).
- No experiment requires contacting IRCTC.
