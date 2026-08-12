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

# R4 — ablation ladder

All mechanisms MUST be implemented as pluggable strategies over the same
simulator.

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
- Results report the marginal delta from the preceding rung.
- Confidence intervals are reported.
- Adaptive and ML arms are compared against the strong baseline in R5.

---

# R5 — baselines

### Weak baseline

Naive unbounded concurrency with retries enabled.

### Strong baseline

Bounded concurrency + FIFO + fast-fail.

The strong baseline is the primary comparison point for adaptive and ML
mechanisms.

An ML or adaptive mechanism MUST NOT claim success merely because it beats the
naive baseline.

---

# R6 — pre-registered evaluation criteria

Evaluation thresholds MUST be fixed before the relevant experiment is run.

Metrics MUST be reported at p50, p95, and p99.

Where applicable, metrics MUST be split between successful and rejected users.

## Primary metric

### Tail time-to-definitive-answer

The primary metric is p99 time-to-definitive-answer.

## Guardrail

### Goodput

Goodput is confirmed bookings per second through the spike.

## Other required metrics

- inventory correctness;
- time-to-definitive-answer for winners and rejected users;
- clean-rejection rate;
- hard-error rate;
- retry amplification;
- wasted-work ratio;
- fairness;
- settling time.

Clean rejection and hard errors MUST NOT be summed.

### Success criteria

For a candidate arm at sufficiently high offered concurrency:

- p99 time-to-definitive-answer <= 50 × p99_knee;
- p99 answer time for rejected users <= p99 answer time for winners;
- goodput >= 0.8 × C_peak;
- 100% of inventory accounted for;
- zero double-sold seats;
- zero lost seats;
- retry amplification < 1.5×.

## What counts as "did not help"

A candidate arm MUST be reported as "did not help" when its primary p99
improvement falls within the 95% confidence interval of the strong baseline
across at least 20 seeded replications.

A claim of improvement requires:

- at least 10% improvement on the primary p99 metric;
- non-overlapping confidence intervals; and
- no greater than 5% regression in goodput or fairness.

Sensitivity results MUST be included.

---

# R7 — ML scope

## Explicitly out of scope

Load prediction for the known Tatkal opening instant is out of scope for v1.

## ML/control mechanisms in scope

### R7.1 — bot/automation classification

Bot classification is included because it addresses fairness rather than
primarily throughput.

If bots are generated using a known signature, the evaluation MUST acknowledge
the circularity risk. Held-out behaviours SHOULD be used where possible.

### R7.2 — adaptive concurrency limiting

Adaptive concurrency limiting is treated primarily as a control problem.

### R7.3 — per-train demand forecasting

Forecasting is limited to which trains/classes will be hot, how hot they will
be, and implications for pre-warming and shard placement.

## Equal-effort rule

Any ML arm that is included MUST receive comparable engineering effort to
classical mechanisms.

An ML mechanism MUST NOT be assumed to help before measurement.

---

# R8 — virtual waiting room hypothesis

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
- ML scope and exclusions are explicit.
- v1/v2 boundaries are explicit.
- Calibration limitations are documented.
- Waiting-room status-check traffic is explicitly included.
- No experiment requires contacting IRCTC.
- Open assumptions are identified rather than silently treated as facts.

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
