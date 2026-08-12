# tatkal v2 — starter

**Status:** RATIFIED as amended (2026-08-12) — the §5 ratification pass
is complete; rulings are recorded as D1–D6 in
[`../tatkal-v2/decisions.md`](../tatkal-v2/decisions.md), which is now
the binding record. Where this file and the ledger differ, the ledger
wins. Notable amendment: §5-Q4 was ruled *against* the draft
recommendation — populations/seeds are re-derived for v2 (D4), not
carried from v1.

This file was drafted from the v1 record after the results-review
rulings (D17, RESULTS.md §§4–11, retro carry-forwards) and served as the
agenda for the ratification pass.

---

## 1. What v1 established (carry-in facts, final per D17)

- **No pre-registered bar claimably met** (post-review grading; the
  earlier rung-4 bar-met claim was downgraded to inconclusive).
- **Engineering alone converted a latency contest into an *orderly*
  latency contest — not into fair allocation** (RESULTS §9). This is the
  central fact v2 exists to act on.
- **Honest negatives stand (D2):** adaptive limiting regressed (F3); the
  timing classifier breaches the 5% fairness guard against the held-out
  mimic family (F4) — improvement claims are limited to non-mimicking
  automation.
- **F5 — drain-speed blindness:** at a ~100 ms sell-out, timing-only
  classification is structurally blind; *any* fairness intervention
  needs the contest to last longer than the population's arrival spread.
  Feature-independent — a stronger learner does not escape it.
- **F6 — failure modes are regime-dependent:** the fitted regime fails
  by connection resets, not timeouts; single-metric harnesses miss this.
- **Headline results are server-variant-dependent** (plateau clean,
  fitted inconclusive, cliff a catastrophic reversal — the waiting
  room's own status stream strangles the drain on a
  congestion-collapsing backend).
- **Absolute numbers are laptop-specific**; directions and orderings are
  the transferable claims.

## 2. Scope candidates (ranked; chair selects in §5-Q1)

1. **Mechanism-design simulations** — pre-registration windows, lottery
   over a qualification window, deliberately paced drains. RESULTS §9
   names these "the first v2 candidates": they are the only untested
   route to durable fairness, and each directly attacks F5 by making the
   contest outlast the arrival spread. Highest leverage; pure
   simulation, no new infra.
2. **Costed push delivery** — v1 modelled rung-4+ push notification as
   cost-free while fully costing status polling (asymmetric costing,
   RESULTS §10). Whether the waiting room retains *any* advantage under
   realistically costed push is an open question raised by the
   Antigravity seat — and it cuts at v1's strongest arm.
3. **Two-phase inventory / seat-hold expiry** — changes the drain
   arithmetic itself (holds slow the effective drain), so it interacts
   with both F5 and the goodput-floor derivation.
4. **Adversarial bot co-evolution** — bounded by F5: co-evolution only
   matters in regimes where the contest lasts. Sensible only *after* a
   mechanism from (1) lengthens the contest.
5. **Real distributed load / autoscaling cold-start** — infra-heavy;
   tests transferability of v1's directions, not new mechanisms.

Likely still deferred: payment processing, multi-region, production
auth, CAPTCHA, production traffic replay, anything contacting IRCTC.

## 3. Pre-registration constraints (retro + review carry-forwards)

Binding once ratified; each traces to a v1 miss:

- **Floor-aware bars.** Derive the inventory-drain physics floor and
  state each bar's distance from it *before* registering the bar. v1's
  winners bar sat ~4% above the floor by accident (retro pushback item).
- **Sensitivity center cells reuse main-sweep data.** v1's 10-seed
  center cell contradicted the 20-seed main sweep in P9; never re-run
  the center at lower seed count.
- **Metric design vs horizon-censoring.** v1's retry-after-reject cell
  was uninformative because the definitive-outcome metric ran to the end
  of the retry/backoff chain, swamping any mechanism difference
  (RESULTS §4). Register censoring-robust metrics for retry regimes.
- **Error taxonomy in the harness.** Per F6, record resets, timeouts,
  and rejects as distinct streams from day one; an error-rate-only
  metric would have hidden v1's fitted-regime failure mode.
- **Variant bracketing.** Any headline claim is evaluated across the
  server-shape variants (plateau / fitted / cliff) and reported as
  variant-dependent when it is. (The "survives all three" drafting error
  was caught at review; make bracketing structural, not narrative.)
- **Multiplicity policy up front.** v1 reported ~20 paired comparisons
  uncorrected; register the comparison count and correction policy (or
  the explicit decision not to correct) before any run.

## 4. Standing conventions (carried from v1 unchanged)

- **Chair model:** Patrick rules; append-only decision entries; nothing
  binds without an entry; reversals get new entries.
- **Pre-registration discipline:** constants/thresholds fixed before
  runs; misses reported, never adjusted; paired per-seed stats only (no
  CI-overlap API, by design).
- **Safety boundary (verbatim from v1):** simulation/calibration only;
  MUST NOT send load or automated booking requests to IRCTC; synthetic
  workloads and locally controlled calibration service/database only; no
  claim of having solved production IRCTC without independent evidence.
- **Honest framing:** this is a scarcity-allocation problem, not only a
  throughput problem. v2's mechanism-design arms simulate allocation
  mechanisms; they still carry no authority over the real system's
  policy.

## 5. Open decisions for the ratification pass

- **Q1 — Scope:** which of §2's candidates are in v1 of v2? (Draft
  recommendation: 1 + 2; both are pure simulation, both attack v1's
  actual conclusions.)
- **Q2 — Ledger:** fresh `decisions.md` in a new spec dir with numbering
  restarted at D1, or continue D18+ in the v1 ledger? (Draft
  recommendation: new dir `docs/specs/tatkal-v2/`, restart at D1, with a
  D1 entry ratifying this starter's carried conventions.)
- **Q3 — Success-bar derivation:** ratify the floor-aware procedure in
  §3 as the *method*, before any specific bar values exist.
- **Q4 — Seeds/populations:** carry v1's D11 populations and 20-seed
  main sweeps, or re-derive? (Center-cell rule from §3 applies either
  way.)
- **Q5 — Fairness metric under mechanism design:** v1's F-ratio measured
  bot advantage in a latency contest; a lottery or paced drain changes
  what "advantage" means. Define the fairness metric per mechanism
  before registering guards.
- **Q6 — Push-costing model** (if candidate 2 is in scope): what does a
  "realistically costed" push edge mean — shared worker pool, separate
  pool, per-connection cost? This is the load-bearing modelling choice.

---

*Drafted from: D17 (decisions.md), RESULTS.md post-review (§§4, 5, 9,
10, 11), requirements.md "Explicitly deferred to v2", retro
carry-forwards recorded in project memory.*
