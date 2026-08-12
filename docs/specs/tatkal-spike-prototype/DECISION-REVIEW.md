# Decision review — a student's guide to the chair rulings

This project was built under a chair model: the AI presents evidence and
options at genuine decision points; the human chair rules; the ruling is
recorded (decisions.md D1–D17) and binds later work. This document lists
the **key decision questions as they were actually asked**, so a student
can evaluate each ruling with what was known *at the time* — and then
against what the evidence showed *afterward*. That before/after gap is the
whole lesson.

For each: the situation, the options offered, the ruling, the outcome, and
questions for you to argue.

---

## Q1 — The calibration fit missed its target. What now? (→ D13)

**Situation.** The simulator's server model was fitted to a real measured
curve under a pre-declared protocol (±25% per level). It missed the p99
band at 5 of 9 levels — the real system's tails carry Python-scheduler
burstiness a clean queue model lacks.

**Options offered:** (a) one bounded refinement round — add a stall
mechanism, refit once, accept best-of *(recommended)*; (b) accept now with
documented deviations; (c) defer.

**Ruling:** refinement round.

**Outcome:** the refinement made the fit *worse* (loss 0.611 vs 0.370) —
the short grid-search duration systematically penalized stall
configurations. Best-of reverted to round 1; the negative was recorded,
not hidden.

**Evaluate:** Was the refinement round worth its cost, given the failure
mode (1 s search window vs 15 ms stalls) was foreseeable? What cheap check
would have predicted the outcome? Is "accept with documented deviations"
more or less honest than "try once more, then accept"?

---

## Q2 — Round-table review of the spec docs: promote what? (→ D10, D11)

**Situation.** Three independent AI models reviewed design/tasks/decisions
against the requirements; all three said "approve with amendments" and
converged on defects — including two ambiguities in already-ratified
success criteria.

**Questions asked (one form, four rulings):**
1. Promote the review outcome and apply the amendment pass? → **both**
2. Which population does the 34.2 ms bar bind? → **winners AND rejected
   independently**
3. What interval defines goodput "through the spike"? → **the sell-out
   window (T0 → inventory exhausted)**
4. Demand forecasting (R7.3) in v1? → **omitted, recorded**

**Outcome:** the population ruling later interacted with the pre-fire
cohort to produce the D15 collision (see Q4); the sell-out-window ruling
made goodput a rate mechanisms could actually move; the omission stayed
clean.

**Evaluate:** Rulings 2 and 3 were *clarifications of already-ratified
criteria*. Where is the line between clarifying a pre-registered threshold
and quietly changing it? What makes these two defensible (or not)?

---

## Q3 — Gate A: the operating point is unachievable and two metrics have
no signal (→ D14)

**Situation.** The ratified operating point ("peak in-flight = 256 ± 5%")
proved *bistable-unsatisfiable*: below a critical burst the server keeps
up (~30–180 in flight); above it, in-flight blows through to the
connection ceiling (451); at the knife-edge, identical configs swing
30↔398 across seeds. Separately: wasted-work measured 0.0 (overload
manifests as connection resets, not stale work) and settling time was
uncomputable (the workload ended with the spike).

**Questions asked (one form, four rulings):**
1. Amend the operating point how? → **supercritical spike** (in-flight
   ≥ 256 *sustained* ≥ 1 s), over pinning conn_limit=256 or deferring
2. Fairness statistic and bar? → **F = bot win-share ÷ population share;
   no >5% relative rise vs strong baseline**
3. Wasted-work: threshold or report-only? → **report-only**
4. Settling: disposition? → **report-only + add a post-spike background
   cohort so it is measurable at all**

**Outcome:** the supercritical realization was stable and reproducible;
the F statistic later caught a real guard breach (Q5); the background
cohort made settling compute in 20/20 runs.

**Evaluate:** The amendment changed how a ratified quantity is *realized*,
justified by "the target is physically unsatisfiable." Is that a legitimate
amendment or a goalpost move? What evidence distinguishes the two? Would
pinning conn_limit=256 have been more faithful to the calibration?

---

## Q4 — Winners' p99 is 18.8 s for every arm: the bar is unmeetable (→ D15)

**Situation.** Two individually-ratified choices collided: the TTDA clock
starts at a user's *first request*, and pre-fire users deliberately start
~20 s before opening ("pre-firing is not free"). Nothing can resolve
before T0, so every arm's winners-p99 saturated at the campers' wait —
the bar had zero discriminating power.

**Options offered:** (a) redefine TTDA itself; (b) split populations;
(c) **bar binds a new derived quantity — resolution latency (definitive −
max(first request, T0)) — while TTDA stays reported** *(recommended)*;
(d) defer to evaluation time.

**Ruling:** (c).

**Outcome:** the operand discriminated (511→43→42 ms across rungs) and
stayed honest — the strong baseline *misses* the bar. Key defense: the
replaced operand was identical across all arms, so the change could not
favor any mechanism.

**Evaluate:** Rank the four options yourself before reading the defense.
Does the arm-invariance argument fully answer "you changed the metric
after seeing results"? What would have made it fail?

---

## Q5 — Findings that arrived *without* being asked

Not every consequential moment was a question — several rulings' quality
only became visible when later evidence tested them:

- **The paired statistics (a D6 ruling) killed a headline.** Rung 4's
  bar-met median (31.1 ≤ 34.2 ms) did not survive the paired CI test and
  held in only 2 of 8 sensitivity cells. The decision to mandate paired
  per-seed deltas — made months of decisions earlier, with no result in
  sight — is what blocked the overclaim.
- **The circularity guard (an R7.1 requirement) exposed the mimic
  breach.** Fairness "improved" on the trained family and on one held-out
  family, and *regressed past the guard* on the human-mimicking family.
  Without held-out evaluation this ships as a clean win.
- **The sensitivity rule ("a win in one corner is not a win") exposed the
  cliff catastrophe**: the best mechanism on the fitted server is the
  worst on a congestion-collapsing one — its own status traffic strangles
  the drain.

**Evaluate:** These three guards were all ratified *before* any result
existed. For each: what would the report have claimed without it? Which
was cheapest per overclaim prevented?

---

## Q6 — The meta-question a reviewer should ask

Across the session, **every recommended option was accepted** — the chair
never diverged from the presenter's marked recommendation. The retro
flagged this openly.

**Evaluate:** Is that evidence of good recommendations, of anchoring, or
indistinguishable? What process change would let you tell the difference
(e.g., unmarked options for contestable calls, independent seats for chair
decisions)? When the same party frames the options *and* argues a
recommendation, who is really deciding?

---

## Where to check the record

- `decisions.md` — every ruling, dated, append-only, with rationale.
- `RESULTS.md` — the graded outcome, including both negatives.
- `reports/` — the evidence each ruling was later tested against.
