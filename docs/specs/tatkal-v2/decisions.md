# tatkal v2 — decisions ledger

Append-only. Chair: Patrick. Nothing binds without an entry; reversals
get new entries. Numbering restarts at D1 per this ledger's D1 (the v1
ledger is sealed at D17 in `../tatkal-spike-prototype/decisions.md`).

## D1 — v2 opened; v1 conventions carried; starter ratified

**Date:** 2026-08-12 · **Decided by:** chair (ratification pass over
`../tatkal-spike-prototype/v2-starter.md` §5) · **Status:** final

v2 of the tatkal experiment is opened in this directory with its own
ledger, numbering restarted at D1. The following v1 conventions carry
forward unchanged:

- **Chair model:** Patrick rules; append-only decision entries; nothing
  binds without an entry; reversals get new entries.
- **Pre-registration discipline:** constants/thresholds fixed before
  runs; misses reported, never adjusted; paired per-seed stats only (no
  CI-overlap API, by design).
- **Safety boundary (verbatim):** simulation/calibration only; MUST NOT
  send load or automated booking requests to IRCTC; synthetic workloads
  and locally controlled calibration service/database only; no claim of
  having solved production IRCTC without independent evidence.
- **Honest framing:** scarcity-allocation problem, not only a throughput
  problem; simulated mechanisms carry no authority over real policy.

The v2 starter is ratified as the seed document, as amended by D2–D6.

**Binds:** this directory's spec documents; the starter's §1 carry-in
facts are the factual baseline for v2 requirements.

## D2 — v2 scope: mechanism-design simulations + costed push delivery

**Date:** 2026-08-12 · **Decided by:** chair (starter §5-Q1) ·
**Status:** final

In scope for v2:

1. **Mechanism-design simulations** — pre-registration windows, lottery
   over a qualification window, deliberately paced drains (RESULTS §9's
   "first v2 candidates"; each attacks F5 by making the contest outlast
   the arrival spread).
2. **Costed push delivery** — re-test of the rung-4 waiting room with
   push notification realistically costed (v1 modelled it cost-free
   while fully costing polling; Antigravity seat's open question).

Explicitly out of v2 scope (deferred, not rejected): two-phase
inventory / seat-hold expiry; adversarial bot co-evolution (bounded by
F5 — premature before a mechanism lengthens the contest); real
distributed load / autoscaling; and the standing v1 deferrals (payment,
multi-region, production auth, CAPTCHA, traffic replay, anything
contacting IRCTC).

**Binds:** v2 requirements scope section.

## D3 — floor-aware success-bar derivation is binding

**Date:** 2026-08-12 · **Decided by:** chair (starter §5-Q3) ·
**Status:** final

Floor derivation is a mandatory pre-registration step: every success bar
must state its distance from the relevant physics floor (inventory-drain
arithmetic, or the analogous floor for the metric) **before** the bar is
registered. A bar without a stated floor distance cannot be registered.

Origin: v1's winners bar sat ~4% above the inventory-drain floor by
accident (retro pushback item).

**Binds:** every pre-registered bar in v2.

## D4 — populations and seeds re-derived for v2

**Date:** 2026-08-12 · **Decided by:** chair (starter §5-Q4, against the
starter's draft recommendation to carry v1's) · **Status:** final

v2 populations and seed counts are **re-derived fresh** rather than
carried from v1's D11/20-seed protocol: mechanism-design arms (lotteries,
paced drains) may need different population structure. The derivation
must **document the break from v1** — where and why v2's populations
differ — so cross-version comparisons are made knowingly or not at all.

The center-cell rule stands regardless: sensitivity-sweep center cells
reuse main-sweep data; never re-run the center at lower seed count
(v1's 10-seed center contradicted its 20-seed main sweep in P9).

**Binds:** v2 population/seed derivation document; every sensitivity
sweep.

## D5 — fairness metric defined per mechanism, before guards

**Date:** 2026-08-12 · **Decided by:** chair (starter §5-Q5) ·
**Status:** final

v1's F-ratio measured bot advantage in a latency contest; a lottery or
paced drain changes what "advantage" means. Each mechanism arm must
therefore define its fairness metric — what bot advantage means under
that mechanism — **before** its guard value is registered. No metric,
no guard, no run.

**Binds:** every mechanism arm's fairness guard in v2.

## D6 — push costing: shared worker pool, swept per-push cost

**Date:** 2026-08-12 · **Decided by:** chair (starter §5-Q6) ·
**Status:** final

"Realistically costed" push delivery means: push work is costed on the
**same shared worker pool** that costed v1's status polling (symmetric
costing), with the per-push cost as a **swept parameter**. The sweep's
purpose is to locate the break-even — the push cost at which the waiting
room's advantage disappears — rather than to bet on a single cost value.
Sweep range and grid are pre-registered per D3 discipline before any
run.

**Binds:** the costed-push arm's design and its pre-registered sweep.

## D7 — mechanism arms baselined against rung 2 AND rung 4

**Date:** 2026-08-12 · **Decided by:** chair (requirements judgment-call
pass, JC1) · **Status:** final

The mechanism-design arms (M1–M3) are compared against both the
fast-fail baseline (v1 rung 2) and the engineering-best treatment (v1
rung 4, waiting room). v2's question is framed as: do allocation
mechanisms beat the best engineering-only treatment on fairness — not
merely the naive floor. The extra cells are accepted.

**Binds:** R5; every M-arm evaluation design.

## D8 — FRFS in M1 is disfavoured; using it requires justification

**Date:** 2026-08-12 · **Decided by:** chair (JC2) · **Status:** final

First-registered-first-served allocation within the pre-registration
window recreates the latency contest at window-open, defeating the
arm's F5 purpose. It is **disfavoured, not banned**: choosing it
requires a justifying decision entry. The default candidate remains a
timing-independent rule (lottery over registrants).

**Binds:** R2.1's allocation-rule decision.

## D9 — bot repertoire: fixed, re-derived in the population work

**Date:** 2026-08-12 · **Decided by:** chair (JC3) · **Status:** final

The bot cohort's v2 behaviour repertoire is **re-derived** as part of
the R6 population derivation (camping a window is a different strategy
than racing a drain), then **frozen** by pre-registration before runs.
Bots are a load and fairness probe, not a learning adversary —
adversarial co-evolution stays deferred per D2. Carrying v1's
drain-race repertoire unchanged was rejected as flattering the
mechanism arms.

**Binds:** R6 population document; R8.

## D10 — M2 identity abuse is a swept population parameter

**Date:** 2026-08-12 · **Decided by:** chair (JC4, going beyond the
draft's specify-before-metric proposal) · **Status:** final

Multi-identity prevalence is a **swept population parameter**, not a
fixed assumption: M2's fairness is reported **as a function of abuse
level**. The identity/duplicate-handling model must still be specified
before M2's fairness metric is registered (the metric is meaningless
without defining what an identity is), and the sweep grid is
pre-registered per D3 discipline. The zero-abuse cell anchors the sweep
(clean-identity idealization becomes a cell, not the model).

**Binds:** R2.2; R6 population derivation (abuse-prevalence axis); M2's
fairness metric registration.

## D11 — v2 requirements ratified in full

**Date:** 2026-08-12 · **Decided by:** chair · **Status:** final

requirements.md, as drafted from D1–D6 and amended by the D7–D10
judgment-call rulings, is **ratified in full**. R1–R8, the deferral
list, the safety boundary, honest framing, and the expected-result
hypothesis are binding. Every UNSET constant remains open by design and
must be fixed by decision entry before any run that depends on it, per
D1's pre-registration discipline.

The design phase opens. First artifact: the R6 population derivation
document (D4/D9/D10 all feed it; the mechanism arms cannot be detailed
until it exists).

**Binds:** requirements.md (status: ratified); the design phase's
sequencing.

## D12 — baselines run under the v2 population; v1 numbers not citable in comparisons

**Date:** 2026-08-12 · **Decided by:** chair (population-derivation §4)
· **Status:** final

The D7 engineering baselines (rung 2, rung 4) are **re-run under the v2
population** on the same paired seeds as the mechanism arms; all v2
comparisons use these re-runs. v1's absolute rung numbers are **not
citable in v2 comparisons** — the paired design does not cross
versions. The v1-population re-run survives only as R1's physics
regression check and is never compared against mechanism arms.

**Binds:** R5 baselines; population-derivation §4/§5; every D7
comparison's data provenance.

## D13 — population constants registered; bot repertoire frozen

**Date:** 2026-08-12 · **Decided by:** chair (registration pass over
population-derivation A1–A5) · **Status:** final

Registered per pre-registration discipline (D1); no value below may be
adjusted after runs — misses are reported:

1. **Carries:** operating scale 30 / 2500 / 150 / 60 (pre_fire /
   t0_humans / bots / background); σ_T0 = 0.35 s; background window
   T0+2 s → T0+32 s; **20 seeds** as the universal per-cell floor,
   centers reusing main-sweep data.
2. **M1 registration uptake is SWEPT** (chair ruling, against the
   fixed-value recommendation): `r_reg` ∈ {0.5, 0.8, 0.95}, center
   0.8 — M1's result is reported as a function of registration uptake.
   Grid taken from the ruled option's stated example; the chair may
   amend the grid by a further entry before M1 runs.
3. **Bot repertoire FROZEN (D9 executed):** four strategies as defined
   in population-derivation A3 — race and mimic carrying v1 values
   (race: uniform [T0, T0+50 ms], `bot_speedup` 0.5; mimic: |N(0,
   0.35 s)|, cadence 0.5), camp (first 5% of W / within 50 ms of
   tranche opens), identity-split (m identities, mimic timing) — with
   the degenerate-form rule (camp→race, identity-split→mimic where
   inapplicable) and mix **60 / 30 / 30 / 30**. No strategy adapts to
   observed outcomes.
4. **Identity-abuse model (D10 executed):** m = 5 fixed; prevalence
   swept p ∈ {0, 0.1, 0.2, 0.4} of the bot cohort in M2 cells
   (0/15/30/60 abusers), zero-abuse anchoring, p = 0.2 aligned with
   the A3 mix center.
5. **Prediction P1 registered:** at p = 0, per-strategy fairness for
   race and mimic under M2 ≈ 1; residual advantage at p = 0 is an
   implementation-leak diagnostic, not a finding.
6. **§7 resolutions adopted:** background cohort unchanged under M3
   (fidelity), settling window per-arm after the final allocation
   event; M1 registration is one-shot per registrant, uniform over W.

**Binds:** population-derivation.md (status: registered); every v2
evaluated run's workload; M1's cell structure (r_reg × its other
axes); M2's abuse sweep.

## D14 — design approved; window and costing constants registered

**Date:** 2026-08-12 · **Decided by:** chair (design-choice pass
DC1–DC5) · **Status:** final

design.md is **approved**; all five open design choices ruled as
proposed, and the following constants are registered (D1/D3 discipline
— misses reported, never adjusted):

1. **Windows (DC1):** W = 300 s (M1; W/σ_T0 ≈ 857); Q = 5 s (M2;
   Q/σ_T0 ≈ 14, Q/bot_window = 100; background overlap after T0+2 s
   accepted and reported); k = 4 equal 50-seat tranches over H = 8 s
   (M3; spacing ≈ 5.7×σ_T0, span ≈ 23×σ_T0).
2. **Push-cost grid (DC2):** c_push ∈ {0, ¼, ½, 1, 2} ×
   `status_service_time`, **shared** by the R3′ waiting-room re-run and
   the M1/M2 notification bursts — one costing model across v2; the
   zero cell is the v1-continuity anchor.
3. **M3 composition base (DC3):** rung-2 serving layer (fast-fail,
   sold-out cache reset at each tranche open). A rung-4-based variant
   is not part of the evaluated ladder.
4. **M1 redemption (DC4):** auto-redeem — winners' bookings
   auto-submit at T0 with standard human jitter; no redemption-window
   mechanic (two-phase inventory stays deferred per D2).
5. **Two-clock reporting (DC5):** allocation arms report absolute TTDA
   (from arrival, including the deliberate wait) AND post-event
   resolution latency (from the allocation event) as separate
   first-class metrics, with D3 floor statements per clock.

Still owed before runs (not opened by this entry): per-mechanism
fairness *guard values* (D5 — definitions proposed in design.md,
guards registered with bars), and every success bar with its floor
statement (D3).

**Binds:** design.md (status: approved); tasks.md structure; every
evaluated run's window/costing configuration.

## D15 — tasks.md approved; ladder active

**Date:** 2026-08-12 · **Decided by:** chair · **Status:** final

tasks.md (V0–V7 with Gate B) is **approved**; the ladder is active and
binding as gated. V0 begins immediately. Gate B remains the chair
decision standing between implementation (V0–V4) and every evaluated
run (V5–V6); the V0.2 reproduction tolerance is the one chair
registration inside the build phases.

**Binds:** tasks.md (status: approved, ladder active); build-phase
sequencing.

## Open questions (no decision yet)

*(new questions get logged here)*
