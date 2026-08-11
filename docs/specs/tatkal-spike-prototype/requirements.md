# tatkal-spike-prototype — requirements

**Status:** draft — updated for review (2026-08-11)

**Purpose:** defensible systems experiment for evaluating traffic-management
mechanisms under a realistic Tatkal-style scarcity spike.

**Source:** round table thread `q-tatkal-spike-prototype-spec-001`

Three seats — Claude, Antigravity, Codex — deliberated one round and
converged on the experiment framing. A negative result on ML is an
acceptable and successful outcome if the experiment is correctly designed
and measured.

---

## Problem

India's IRCTC Tatkal booking opens at a fixed clock instant:

- 10:00 for AC classes
- 11:00 for Sleeper

A very large number of users submit within the same few seconds, producing
an extreme short-duration concurrency spike. The resulting symptoms of
interest are slow responses, failed requests, retry amplification, and poor
user experience.

The structural fact that shapes the experiment is that demand can greatly
exceed available inventory. Most requests therefore cannot succeed,
regardless of system capacity.

The system's relevant job at T0 is therefore not simply to serve everyone.
It is to:

1. allocate scarce inventory correctly;
2. preserve inventory correctness;
3. keep the service stable under the spike;
4. give successful users a definitive answer;
5. give rejected users a definitive answer quickly and cleanly; and
6. avoid turning rejection into unnecessary server work.

Metrics must distinguish winners from rejected users. A single average across
both populations can hide the actual behaviour of the system.

---

## Experimental framing

The original project question proposed AI/ML for traffic/load prediction.

The round table rejected load prediction as the primary mechanism because the
spike occurs at a known scheduled time. There is no meaningful surprise
arrival time to forecast inside the short surge.

Therefore:

- **Classical traffic management is the primary v1 experiment.**
- ML is included only where it has a defensible role.
- A negative ML result is a valid result.
- No mechanism is assumed to work before measurement.

The experiment is designed to answer:

> Which mechanisms actually improve behaviour during a realistic,
> short-duration scarcity spike, and what is the marginal contribution of
> each mechanism?

---

# Requirements

## R1 — discrete-event simulator, not a distributed testbed

v1 MUST be a single-process, seeded and deterministic discrete-event
simulation.

v1 MUST NOT require:

- Kubernetes;
- cloud infrastructure;
- multi-machine load generation; or
- a distributed load-testing environment.

### Acceptance

- Identical seeds produce byte-identical results across runs.
- A complete parameter sweep completes on a laptop.
- The same seeds and workloads can be reused across every mechanism.

---

## R2 — one real-code calibration experiment

Exactly one real service component is required for calibration:

- a small HTTP endpoint;
- approximately 150 lines;
- a genuine database inventory decrement;
- atomic row-level locking using `SELECT FOR UPDATE`;
- concurrency levels of 1, 2, 4, ... 256.

The purpose of this component is **measurement, not demonstration**.

The measurement MUST provide:

1. service-time characteristics;
2. contention behaviour;
3. throughput-versus-concurrency behaviour; and
4. the saturation region.

These measurements parameterise the simulator.

### Acceptance

- A measured throughput-vs-concurrency curve is produced.
- The knee is identified.
- The simulator's server model is fitted against the measured behaviour.
- The fit is plotted.
- Results are reported across multiple knee shapes.
- Provisional calibration assumptions are documented.

### Calibration status (2026-08-11)

R2 is **not yet satisfied.** One calibration run exists and is retained for
provenance, but it does not meet this requirement and its headline result does
not survive review.

Artifacts:

- harness — `tools/calibrate_lock_contention.py`
- raw data — `docs/specs/tatkal-spike-prototype/calibration/2026-08-09-sqlite-hotkey.csv`

#### Gaps against R2 as specified

| R2 requires | The 2026-08-09 run |
|---|---|
| HTTP endpoint, ~150 lines | no HTTP layer; in-process database calls only |
| `SELECT FOR UPDATE` row locking | SQLite `BEGIN IMMEDIATE`, a database-wide writer lock |
| concurrency 1, 2, 4, ... 256 | 1, 2, 4, ... 64 |

#### The recorded tail result is a harness artifact and MUST NOT be used

The run reported p99 ≈ 2050 ms at concurrency 64 against ≈ 1.8 ms at the knee,
and an earlier revision of this document promoted tail latency to primary metric
on that basis.

Re-running the harness with each latency sample tagged by the offset at which
its transaction started shows that every sample above 100 ms is a worker's
*first* transaction, at offset 0.000. All workers busy-spin to a shared start
timestamp and then contend simultaneously; SQLite's busy-handler backoff ladder
stretches the unlucky ones to roughly two seconds. This is a one-shot startup
transient, not steady-state contention:

- the count of slow samples tracks the worker count, not the window length —
  64 slow samples in a 2 s window, 80 in a 20 s window;
- whether p99 captures the transient depends only on whether the worker count
  exceeds 1% of total samples — which flips with ordinary run-to-run throughput
  variance (2226–4033 ops/s at fixed concurrency, on one machine);
- a re-run at the same concurrency on the same machine gave p99 = 1.62 ms
  against the 2049 ms recorded here: the re-run's higher throughput (~7,800
  samples vs ~5,700) pushed the 1% rank past the worker count.

Corrected, the run shows throughput plateauing at ~80% of peak past the knee
with a flat tail; the harness's own summary classifies this shape as `PLATEAU`.
That is the case in which admission control has least to recover, so R2's rerun
determines whether the ablation ladder has a measurable subject at all.

**Consequently the current choice of primary metric is unjustified.** This
document retains p99 time-to-definitive-answer as primary (R6); that choice
inherits from the withdrawn result and MUST be re-decided against R2's rerun.

#### Standing limitations of the SQLite approach

Applicable to any rerun that keeps SQLite:

- SQLite serialises **all** writes database-wide; Postgres locks per row. For
  the hot-key case (one train, everyone contending) SQLite is a fair analogue.
  For the sharded case (R4 rung 3) it **overstates** contention, because
  different trains would not block each other under Postgres.
- Measured service time is ~0.2 ms — a bare row update with no application
  logic, network hop, or serialisation cost. Real per-request service time will
  be substantially larger, which moves `N_knee` down and may change the shape
  of the curve.
- Run-to-run variance is large: throughput ranged 2226–4033 ops/s at fixed
  concurrency. This is why R6 requires at least 20 replications; constants
  derived from 3 replications are not usable.
- Zero errors were observed at every level. With a busy timeout set, overload
  manifests as latency and never as failure, so an error-rate threshold would
  measure nothing until an admission mechanism introduces deliberate rejection.
- One machine, one run, no cross-hardware check. Absolute numbers are
  laptop-specific; the transferable finding is the *shape* of the curve.

---

## R3 — simulator fidelity / anti-requirements

The simulator MUST avoid producing a flattering result by modelling overload
incorrectly.

### R3.1 — partly open-loop arrivals

User intents MUST arrive according to a schedule that is at least partly
independent of server health.

The simulator MUST NOT require every user to receive a response before
issuing the next scheduled intent.

### R3.2 — retry amplification

The simulator MUST model retries caused by timeouts or unsuccessful
attempts.

Retry behaviour MUST be capable of increasing offered load as latency
increases.

### R3.3 — bounded service capacity

The simulator MUST model finite capacity, including appropriate limits for
workers, connections, and queue/accept capacity.

The service MUST degrade beyond the calibrated operating region.

### R3.4 — atomic finite inventory

Inventory MUST be finite and MUST be contended atomically by:

`(train, class, date)`

The simulator MUST detect double-sold inventory, lost inventory, and incorrect
inventory accounting.

### R3.5 — concentrated T0 arrival pattern

Arrivals MUST be concentrated around the opening instant and include:

- a pre-fire cohort;
- a sub-second T0 spike; and
- a retry-driven second wave.

### R3.6 — wasted work

The simulator MUST charge server capacity for work that continues after a
client has abandoned or timed out.

### R3.7 — heavy-tailed / multimodal service times

Service times MUST support heavy-tailed or multimodal behaviour.

### R3.8 — hot-key demand

Demand MUST be distributable using a Zipf-like distribution across trains so
that hot trains/classes can create concentrated contention.

### R3.9 — bot/automation cohort

The workload MUST include a scripted automation cohort with timing
characteristics that differ from ordinary human arrivals.

### R3.10 — persistent user identity

The simulator MUST preserve per-user identity so duplicate attempts remain
distinguishable from independent user intents.

### R3 acceptance

Every R3 mechanism MUST be implemented as a named, toggleable simulation
parameter.

Each parameter MUST have a test demonstrating its documented directional
effect.

The final results MUST report which R3 parameters were enabled for each
experiment.

---

## R4 — ablation ladder

All mechanisms MUST be implemented as pluggable strategies over the same
simulator.

**The ladder is cumulative.** Rung k enables every mechanism of rungs 1
through k−1 plus one new mechanism, so each rung's delta isolates exactly one
addition. (This is already implicit in R5: the strong baseline is rung 2 —
bounded admission + fast-fail stacked.) An arm evaluated outside the ladder,
e.g. a mechanism run standalone, MUST be labelled as such and MUST NOT be
reported as a rung.

**Ordering caveat.** Marginal deltas are conditional on this ordering: a
mechanism added late inherits interaction effects with everything below it,
so "rung 5 added 3%" means "given rungs 1–4 were already present." The
results MUST state this. Where an interaction is suspected of hiding or
inflating a mechanism's contribution, a targeted out-of-order run MAY be
reported alongside the ladder, clearly labelled.

### Rung 0 — Naive

- unbounded concurrency;
- retries enabled.

### Rung 1 — bounded admission

- bounded concurrency;
- FIFO ordering.

### Rung 2 — fast-fail

- cached per-pool sold-out counter;
- early rejection when the pool is known to be unavailable.

### Rung 3 — sharding

Shard work by:

`(train, class, date)`

### Rung 4 — virtual waiting room

Use pre-issued ordered tokens and explicit queue-status behaviour.

### Rung 5 — adaptive concurrency limiting

Evaluate an adaptive mechanism such as CoDel-style or gradient-style
concurrency limiting.

### Rung 6 — bot classifier

Evaluate the ML bot/automation classification arm described in R7.

### Acceptance

- Every rung runs against the same seeds.
- Every rung runs against the same workload definitions.
- Results report the marginal delta from the preceding rung, computed as
  paired per-seed differences (see R6, *Statistical decision rule*).
- A confidence interval on the paired delta is reported for every rung.
- Adaptive and ML arms are compared against the strong baseline in R5.

---

## R5 — baselines

### Weak baseline

Naive unbounded concurrency with retries enabled.

### Strong baseline

Bounded concurrency + FIFO + fast-fail.

The strong baseline is the primary comparison point for adaptive and ML
mechanisms.

An ML or adaptive mechanism MUST NOT claim success merely because it beats the
naive baseline.

---

## R6 — pre-registered evaluation criteria

Evaluation thresholds MUST be fixed before the relevant experiment is run.

R2 is itself an experiment, and it supplies the constants these thresholds are
written against. The required ordering is therefore:

1. R2 runs and its constants are reported;
2. the thresholds below are fixed against those constants and recorded;
3. R4's arms are run.

Pre-registration binds step 3. Constants MUST NOT be revised after step 2 to
accommodate a result.

Metrics MUST be reported at p50, p95, and p99.

Where applicable, metrics MUST be split between successful and rejected users.

### Primary metric — tail time-to-definitive-answer

The primary metric is p99 time-to-definitive-answer.

> **Provisional.** This choice inherits from a calibration result since
> withdrawn as a harness artifact — see R2, *Calibration status*. It MUST be
> re-decided once R2 is rerun.

### Guardrail — goodput

Goodput is confirmed bookings per second through the spike.

### Other required metrics

- inventory correctness;
- time-to-definitive-answer for winners and rejected users;
- clean-rejection rate;
- hard-error rate;
- retry amplification;
- wasted-work ratio;
- fairness;
- settling time.

Clean rejection and hard errors MUST NOT be summed.

### Metric definitions

Every metric MUST be computed as defined here, and these definitions MUST be
fixed before the relevant experiment runs.

**Time-to-definitive-answer (TTDA)** — elapsed time from a user's first request
to the point at which that user receives a final, non-retryable outcome: booked,
sold out, or rejected. Reported separately for winners and for rejected users,
and never averaged across both populations.

**Goodput** — confirmed bookings per second through the spike.

**Inventory correctness** — seats sold as a percentage of inventory, together
with counts of double-sold seats and lost seats.

**Clean-rejection rate** — share of requests that receive a definitive,
well-formed rejection, for example "sold out" or a queue position.

**Hard-error rate** — share of requests that fail without a definitive answer:
connection reset, timeout with no response, or 5xx.

**Retry amplification** — total requests / unique user intents.

**Wasted-work ratio** — server-seconds spent on abandoned or timed-out requests
/ total server-seconds.

**Fairness** — two quantities, both reported:

1. seat share by arrival cohort (pre-fire, T0, retry wave); and
2. the bot cohort's win share relative to its share of the population.

**Settling time** — seconds from T0 until latency has returned to its
pre-spike level and stayed there, computed as:

- p99 latency over a **1-second rolling window**;
- the pre-spike level is that same windowed p99 measured over the interval
  ending 10 seconds before T0;
- settled means the windowed p99 remains within **2× the pre-spike level for
  5 consecutive seconds**; settling time is measured to the *start* of that
  sustained interval.

The window width, tolerance factor, and sustain duration are part of the
pre-registered definition; runs MUST NOT alter them per-arm. If a sweep
changes timescales enough to justify different values, the change applies to
every arm and is recorded.

### Calibration-derived constants

Success criteria are stated as formulas over quantities measured by R2, so that
they recalibrate when R2 is rerun on different hardware or against a different
engine.

- **`N_knee`** — offered concurrency at which median throughput peaks.
- **`C_peak`** — median throughput at `N_knee`, in operations per second.
- **`p99_knee`** — p99 service latency at `N_knee`.

Each MUST be reported as a median across at least 20 replications, together with
its observed range.

**Status: unset.** The 2026-08-09 run does not supply usable values — see R2,
*Calibration status*. No values are currently carried in this document. R2 MUST
be completed and these constants fixed before any R4 arm is run.

### Success criteria

For a candidate arm at >= 8 × `N_knee` offered concurrency, measured against the
strong baseline (R5):

- p99 TTDA <= 50 × `p99_knee`;
- p99 TTDA for rejected users <= p99 TTDA for winners;
- goodput >= 0.8 × `C_peak` — a guardrail, not a success signal; an arm that
  fails it has traded throughput for latency and MUST justify that;
- 100% of inventory accounted for;
- zero double-sold seats;
- zero lost seats;
- retry amplification < 1.5×.

A win in one corner of the parameter sweep is not a win; the sensitivity table
ships with the result.

### Thresholds not yet set

The following metrics are required but have no pre-registered threshold. Each
MUST be given one before R4 runs, or be explicitly designated report-only:

- wasted-work ratio;
- fairness — note that R7.1 rests the ML case on fairness, and the improvement
  rule below already references a 5% fairness regression bound, so this gap is
  load-bearing;
- settling time.

### Statistical decision rule

R1 mandates identical seeds across arms, which makes every comparison a
**paired** design. Comparisons MUST exploit this: for each seed i, compute
the per-seed difference

`delta_i = metric(candidate, seed_i) − metric(baseline, seed_i)`

and report the distribution of `delta_i` across at least 20 seeded
replications, with a 95% confidence interval on its median (or mean, stated
in advance).

Comparing the two arms' independently computed confidence intervals and
checking for overlap is NOT an acceptable test: it discards the pairing the
shared seeds exist to provide, and CI overlap is not equivalent to any
stated significance level.

### What counts as "did not help"

A candidate arm MUST be reported as "did not help" when the 95% confidence
interval of its paired per-seed delta on the primary metric includes zero.

A claim of improvement requires:

- at least 10% improvement on the primary p99 metric;
- the paired delta's 95% confidence interval excluding zero; and
- no greater than 5% regression in goodput or fairness.

Sensitivity results MUST be included.

---

## R7 — ML scope

### Explicitly out of scope

Load prediction for the known Tatkal opening instant is out of scope for v1.

### ML/control mechanisms in scope

#### R7.1 — bot/automation classification

Bot classification is included because it addresses fairness rather than
primarily throughput.

If bots are generated using a known signature, the evaluation MUST acknowledge
the circularity risk. Held-out behaviours SHOULD be used where possible.

#### R7.2 — adaptive concurrency limiting

Adaptive concurrency limiting is treated primarily as a control problem.

#### R7.3 — per-train demand forecasting

Forecasting is limited to which trains/classes will be hot, how hot they will
be, and implications for pre-warming and shard placement.

### Equal-effort rule

Any ML arm that is included MUST receive comparable engineering effort to
classical mechanisms.

An ML mechanism MUST NOT be assumed to help before measurement.

---

## R8 — virtual waiting room hypothesis

The waiting room is explicitly treated as a hypothesis rather than an assumed
solution.

The experiment MUST answer whether the waiting room reduces the original
server bottleneck or whether queue-status polling creates a new bottleneck.

### Acceptance

Waiting-room experiments MUST:

- model queue status-check traffic explicitly;
- report status-check traffic as its own load stream;
- evaluate multiple polling intervals;
- use the same underlying workload and seeds;
- measure whether the status endpoint itself becomes saturated.

---

# Explicitly deferred to v2

The following are outside v1:

- real distributed load testing;
- autoscaling with cold-start behaviour;
- payment processing;
- seat-hold expiry / two-phase inventory;
- multi-region deployment;
- production authentication;
- CAPTCHA;
- adversarial bot co-evolution;
- production traffic replay;
- anything that contacts IRCTC.

---

# Safety and experimental boundary

This prototype MUST remain a simulation/calibration experiment.

It MUST NOT send load or automated booking requests to IRCTC.

The v1 experiment MUST use synthetic workloads and a locally controlled
calibration service/database.

No claim should be made that the prototype has solved the production IRCTC
system unless independently supported by evidence.

---

# Honest framing

This is fundamentally a **scarcity-allocation problem**, not only a
throughput problem.

Engineering mechanisms may improve service stability and fairness, but they
may not solve the underlying allocation problem.

Potential mechanism-design alternatives such as staggered opening times,
pre-registration, or lottery-based allocation are outside the prototype's
authority and scope.

---

# Expected result

The experiment is designed so that the following outcome is acceptable:

> Classical admission control plus a virtual waiting room recovers much of
> the lost goodput/stability; adaptive limiting provides a smaller additional
> improvement; and ML earns its place primarily through bot detection and
> fairness rather than raw throughput.

This is a hypothesis, not a guaranteed result.

A negative result for any mechanism is a valid outcome if the experiment
demonstrates that the mechanism did not provide a statistically meaningful
improvement over the appropriate baseline.

---

# Definition of done for the requirements phase

Before implementation is considered complete for the requirements phase:

- R1–R8 have been reviewed.
- Every required mechanism has a measurable acceptance condition.
- R3 fidelity parameters are explicitly named and toggleable.
- Baselines are fixed.
- Primary metrics and guardrails are fixed before experiments.
- Every metric named in R6 has a definition.
- Every constant used in a threshold is either fixed or explicitly marked unset.
- Metrics required but not yet thresholded are listed as such.
- ML scope and exclusions are explicit.
- v1/v2 boundaries are explicit.
- Calibration limitations are documented.
- Waiting-room status-check traffic is explicitly included.
- No experiment requires contacting IRCTC.
- Open assumptions are identified rather than silently treated as facts.

Two items are **not** yet satisfied and block the requirements phase:

- R2 is incomplete (see *Calibration status*), so `N_knee`, `C_peak`, and
  `p99_knee` are unset.
- The primary metric is inherited from a withdrawn result and must be
  re-decided against R2's rerun.

---

# Provenance

Based on:

`q-tatkal-spike-prototype-spec-001`

Round-table participants:

- Claude
- Antigravity
- Codex

This document is a requirements draft for review and is not itself evidence
that any mechanism improves the production system.
