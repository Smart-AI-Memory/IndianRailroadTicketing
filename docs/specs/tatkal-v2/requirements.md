# tatkal-v2 — requirements

**Status:** draft (2026-08-12) — awaiting chair ratification. Every
numeric constant in this document is either carried from v1 with its
source named, or explicitly marked **UNSET**; per D1's pre-registration
discipline, an UNSET constant must be fixed by a decision entry before
any run that depends on it.

**Purpose:** test whether mechanism-design interventions produce durable
fairness where v1's engineering mechanisms did not, and whether v1's
strongest engineering result survives realistic costing.

**Source:** v2 decisions ledger D1–D6 (`decisions.md`), seeded by the
ratified v2 starter; factual baseline is the v1 record post-review (D17,
RESULTS.md).

---

## Problem

v1 answered its framing question with pre-registered criteria and honest
negatives, and its central finding reframes the problem:

> Engineering alone converted a latency contest into an *orderly*
> latency contest — not into fair allocation.

Two structural findings shape v2:

- **F5 (drain-speed blindness):** at a ~100 ms sell-out, everyone
  present is "early" and nobody has a second request yet; *any*
  fairness intervention needs the contest to last longer than the
  population's arrival spread. Feature-independent.
- **The asymmetric-costing gap:** v1's strongest arm (rung 4, virtual
  waiting room) was evaluated with status polling fully costed but push
  delivery modelled cost-free. Whether it retains any advantage under
  realistically costed push is open (RESULTS §10).

v2 therefore has two jobs, fixed by D2:

1. simulate **allocation mechanisms** that deliberately lengthen the
   contest — the only untested route to durable fairness; and
2. re-test the **waiting room under costed push** — a stress test of
   v1's best engineering result.

---

## Experimental framing

The experiment is designed to answer:

> Do mechanism-design interventions — pre-registration windows, a
> lottery over a qualification window, deliberately paced drains —
> produce durable fairness where engineering alone did not? And does
> the virtual waiting room's advantage survive realistically costed
> push delivery, and up to what per-push cost?

Framing conventions carried from v1 (D1):

- No mechanism is assumed to work before measurement.
- A negative result for any mechanism is a valid and successful outcome
  if correctly designed and measured.
- Simulated mechanisms carry **no authority over real-system policy**
  (see Honest framing).

---

# Requirements

## R1 — extend the v1 simulator; no distributed testbed

v2 extends the v1 discrete-event simulator (`src/tatkal_sim/`, 118
tests at v1 close). It MUST NOT become a distributed load testbed
(carry of v1 R1).

- New arms are implemented as strategies alongside the v1 rungs.
- v1 arms MUST remain runnable unchanged — they are v2's baselines and
  the regression check that extension did not alter v1 physics.
- Identical seeds across arms (paired design) is retained.

### Acceptance

- v1's test suite passes unmodified on the v2 tree.
- A designated v1 arm re-run under the v2 tree reproduces its v1
  metrics within stated tolerance (tolerance **UNSET**).

## R2 — mechanism-design arms (D2 scope, part 1)

Three allocation mechanisms, each simulated as an arm. Per F5, **each
arm MUST state, before running, how it makes the contest outlast the
population's arrival spread** — that statement is part of the arm's
pre-registration.

### R2.1 — pre-registration window (arm M1)

Users may register interest during a window of length `W` ending at T0
(**UNSET**). At T0, allocation runs over the registered pool;
unregistered arrivals after T0 contend only for whatever the mechanism
leaves unallocated.

- The registration flow MUST be costed as server work (registration is
  itself a spike surface — model it, don't idealize it).
- Allocation rule within the registered pool: **UNSET** (candidates:
  uniform lottery over registrants; first-registered-first-served is
  explicitly disfavoured as it recreates the latency contest at
  window-open and MUST be justified if chosen).

### R2.2 — lottery over a qualification window (arm M2)

All requests arriving in `[T0, T0 + Q]` (Q **UNSET**) are pooled;
winners are drawn at `T0 + Q`. The contest length is `Q` **by
construction** — this is the cleanest direct attack on F5.

- Draw weighting: **UNSET** (default candidate: uniform over unique
  persistent identities, leaning on v1 R3.10).
- Duplicate/multi-identity submission handling MUST be specified before
  the fairness metric is registered (it is the obvious bot exploit).

### R2.3 — paced drain (arm M3)

Inventory is released in `k` tranches over a pacing horizon `H` (both
**UNSET**) instead of a single T0 drain.

- The arm MUST report contest duration achieved vs. `H` (pacing that
  the population defeats by camping is a finding, not a failure).
- Interaction with retry behaviour MUST be measured: pacing extends the
  window in which rejected users re-arrive.

### Acceptance (all of R2)

- Each arm's parameters, allocation rule, and F5 statement are fixed by
  decision entry before its first evaluated run.
- Each arm reports the same core metric set as the engineering arms so
  cross-family comparison is possible.
- Each arm's fairness metric is defined per D5 **before** its guard is
  registered: no metric, no guard, no run.

## R3 — costed push delivery (D2 scope, part 2; D6 model)

Re-run the v1 rung-4 virtual waiting room with push delivery costed per
D6:

- Push work executes on the **same shared worker pool** that costs
  status polling (symmetric costing).
- Per-push cost `c_push` is a **swept parameter**; the sweep's purpose
  is to locate the **break-even** — the cost at which the waiting
  room's advantage over the fast-fail baseline disappears.
- Sweep grid and range: **UNSET**; MUST be registered per D3 discipline
  before the run, and MUST bracket zero-cost (v1's model) so the sweep
  connects continuously to the v1 record.
- Polling-side costing carries from v1 unchanged.

### Acceptance

- Break-even reported with paired statistics per seed, or reported as
  not-found-within-range (which is a result, not a miss).
- The zero-cost cell reproduces the v1 rung-4 result within stated
  tolerance (tolerance **UNSET**; shared with R1's).

## R4 — fidelity: carry v1, plus measurement lessons

v1's fidelity requirements R3.1–R3.10 (open-loop arrivals, retry
amplification, bounded capacity, atomic inventory, T0 concentration,
wasted work, heavy-tailed service, hot-key demand, bot cohort,
persistent identity) carry unchanged, subject to R6's re-derived
populations. Three additions, each tracing to a v1 measurement miss:

### R4.1 — error taxonomy (F6)

Connection resets, timeouts, and explicit rejects are recorded as
**distinct streams** in every arm from the first run. A collapsed
error-rate metric hid v1's fitted-regime failure mode.

### R4.2 — censoring-robust metrics (RESULTS §4)

Any metric that runs to a definitive outcome across a retry/backoff
chain MUST be checked for horizon-censoring before registration; v1's
retry-after-reject cell was uninformative because the retry chain
swamped the mechanism difference. Where censoring is plausible, a
censoring-robust companion metric MUST be registered alongside.

### R4.3 — structural variant bracketing

Every headline claim is evaluated across the three server-shape
variants (plateau / fitted / cliff) and reported as variant-dependent
when it is. This is a harness requirement, not a narrative one: the
evaluation tooling MUST emit the three-variant table by default.

## R5 — baselines

Fixed before any evaluated run:

- **Engineering baseline:** v1 rung 2 (fast-fail) — v1's strong
  baseline role carries.
- **Naive floor:** v1 rung 0.
- **For R3:** v1 rung 4 at `c_push = 0` (the v1 model) is the anchor
  cell of the sweep.
- **For R2 arms:** the mechanism arms are compared against rung 2 and
  rung 4 (**engineering-best**), because the question is whether
  allocation mechanisms beat the best engineering-only treatment on
  fairness — not merely the naive floor.

## R6 — populations and seeds (D4)

Populations and seed counts are **re-derived fresh** for v2, not
carried from v1's D11/20-seed protocol.

- The derivation MUST be recorded in a population document that
  **explicitly documents the break from v1**: where v2 populations
  differ, why, and which cross-version comparisons remain legitimate.
  Cross-version comparisons are made knowingly or not at all.
- Mechanism arms motivate the re-derivation: lotteries and paced drains
  change what arrival timing means, and the bot cohort's strategy space
  differs when camping a window beats racing a drain. The bot cohort's
  v2 behaviour repertoire is part of the population derivation
  (co-evolution stays out of scope per D2 — the repertoire is fixed,
  not adaptive).
- Seed count: **UNSET** until derivation; the statistical decision rule
  (R7) constrains the minimum.
- **Center-cell rule (D4, standing):** sensitivity-sweep center cells
  reuse main-sweep data; the center is never re-run at lower seed
  count.

## R7 — pre-registered evaluation criteria (D3, D5)

### Floor-aware bars (D3 — binding)

Every success bar MUST state its distance from the relevant physics
floor **before** registration:

1. derive the floor from the arithmetic of the arm and workload
   (inventory-drain arithmetic for latency/goodput bars; the analogous
   computation for other metrics, named per bar);
2. state the proposed bar's distance from that floor;
3. only then register the bar by decision entry.

A bar without a stated floor distance cannot be registered. All bar
values are **UNSET** at requirements time by design — this section
fixes the *procedure*, not the numbers.

### Fairness metrics (D5 — binding)

Each mechanism arm defines its fairness metric — what bot advantage
means under that mechanism — before its guard value is registered.
v1's F-ratio is available as a comparator where the arm's contest is
still latency-shaped, but it is not assumed to transfer.

### Statistical decision rule (carry of v1 R6)

- Paired per-seed deltas; distribution of `delta_i` with a 95% CI on
  its median or mean, stated in advance.
- CI-overlap comparison of independently computed intervals remains
  explicitly unacceptable.
- "Did not help" = the paired delta's 95% CI on the primary metric
  includes zero. Improvement claims require the CI excluding zero plus
  pre-registered effect-size and regression bounds (values **UNSET**;
  bounds registered with the bars per D3).

### Multiplicity policy (new; RESULTS §10 lesson)

Before any evaluated run, register: the planned comparison count, and
either the correction procedure or the explicit decision not to
correct. v1 reported ~20 paired comparisons uncorrected and flagged it
as a limitation; v2 decides up front.

## R8 — ML scope

- **No new ML work in v2.** The bot classifier is not extended;
  adversarial co-evolution is deferred (D2).
- The bot cohort remains in the population (R4 carry of v1 R3.9) with a
  fixed, pre-registered behaviour repertoire per R6 — bots are a load
  and fairness *probe*, not a learning adversary.
- v1's classifier MAY be run unchanged inside engineering-arm baselines
  where v1 configured it, for comparability only; its v1 fairness
  limits (mimic-family breach) are carried as known context, not
  re-litigated.

---

# Explicitly deferred from v2 (D2)

Deferred, not rejected: two-phase inventory / seat-hold expiry;
adversarial bot co-evolution; real distributed load testing;
autoscaling with cold-start behaviour. Standing v1 deferrals remain:
payment processing, multi-region deployment, production authentication,
CAPTCHA, production traffic replay, anything that contacts IRCTC.

---

# Safety and experimental boundary

Carried verbatim from v1 (D1):

This prototype MUST remain a simulation/calibration experiment.

It MUST NOT send load or automated booking requests to IRCTC.

The v2 experiment MUST use synthetic workloads and a locally controlled
calibration service/database.

No claim should be made that the prototype has solved the production
IRCTC system unless independently supported by evidence.

---

# Honest framing

This remains a **scarcity-allocation problem**. v2 simulates allocation
mechanisms directly, which sharpens rather than relaxes the v1 caveat:

- A fairness win for a simulated lottery or paced drain is evidence
  that the mechanism *can* work under the modelled population — it is
  **not** a policy recommendation for IRCTC, whose constraints
  (regulatory, operational, equity across access levels) are not
  modelled here.
- Mechanism design reallocates who wins; it does not create seats. v2
  results MUST be reported in terms of *who* the mechanism advantages
  and disadvantages, not only aggregate fairness scores.

---

# Expected result

The experiment is designed so that the following outcome is acceptable:

> Mechanisms that lengthen the contest by construction (lottery, paced
> drain) enable fairness measures to bind where v1's timing-based
> approaches were structurally blind; the pre-registration window
> shifts the contest to the registration surface rather than removing
> it; and the waiting room's advantage shrinks monotonically with push
> cost, with a break-even inside the plausible range.

This is a hypothesis, not a guaranteed result. A negative result for
any mechanism — including "the lottery's fairness gain is confiscated
by multi-identity abuse" or "the waiting room survives all plausible
push costs" — is a valid outcome if correctly measured.

---

# Definition of done for the requirements phase

- R1–R8 reviewed and ratified by decision entry.
- Every arm has a measurable acceptance condition.
- Every UNSET constant is listed as such and traceable to the decision
  entry that must fix it.
- Baselines fixed (R5) before any evaluated run.
- The floor-aware bar procedure (R7) is ratified before any bar is
  proposed.
- Each R2 arm's F5 statement requirement is understood: no arm runs
  without its contest-lengthening claim on record.
- The population re-derivation (R6) has an owner document before
  mechanism arms are designed in detail.
- Multiplicity policy registered before evaluation.
- v2/v3 boundaries are explicit (deferred list above).
- No experiment requires contacting IRCTC.
- Open assumptions are identified rather than silently treated as
  facts.
