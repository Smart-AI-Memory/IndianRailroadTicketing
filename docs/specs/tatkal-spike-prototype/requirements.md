# tatkal-spike-prototype — requirements

**Status:** draft (2026-08-09 — chair-promoted from round table thread
`q-tatkal-spike-prototype-spec-001`, messages 2, 3, 4, 8, 9. Three seats
— Claude, Antigravity, Codex — deliberated one round; halted on
convergence. Chair ruled the deliverable is a defensible systems
experiment in which a negative result on ML counts as success.)

## Problem

India's IRCTC Tatkal (same-day quota) booking opens at a fixed clock
instant: 10:00 for AC classes, 11:00 for Sleeper. A very large number of
users submit within the same few seconds, producing an extreme
short-duration concurrency spike — slow responses, failed requests, and
poor user experience.

The structural fact that shapes every requirement below: **demand exceeds
supply by roughly 20–50×.** Most requests *cannot* succeed, no matter how
the system is built. The system's real job at T0 is therefore not to
serve everyone — it is to allocate scarcity correctly and tell the losers
**quickly and clearly**. Any metric that averages winners and losers
together measures nothing.

## What the round table changed about the original goal

The originating brief listed five candidate areas, led by *traffic/load
prediction*, and asked whether AI/ML plus intelligent traffic management
handles the spike better. All three seats independently rejected the
prediction framing, for the same reason:

> The spike is at a **known, scheduled** clock instant. There is nothing
> to forecast, and no useful forecast horizon — you cannot provision
> inside a ten-second surge. A lookup table beats a learned model here.

This spec therefore scopes **classical traffic management as the v1
experiment** and confines ML to the three places the table agreed it
genuinely earns its keep (R7). This is a deliberate narrowing of the
original goal, recorded so it is not silently forgotten.

## Requirements

### R1 — a discrete-event simulator, not a distributed system

v1 is a single-process, **seeded and deterministic** discrete-event
simulation. No Kubernetes, no cloud, no multi-machine load generation.

Rationale: a student can finish a simulator; a distributed testbed
becomes a project about infrastructure, and the load generator becomes
the bottleneck long before the system under test does.

**Acceptance**
- Identical seed produces byte-identical results across runs.
- A full parameter sweep completes on a laptop.

### R2 — one calibration experiment against real code

Exactly one real component: a small HTTP endpoint (~150 lines) doing a
genuine `SELECT FOR UPDATE` seat decrement against a real database,
driven at concurrency 1, 2, 4, … 256.

Its purpose is **measurement, not demonstration**: it produces the
service-time distribution and the lock-contention curve that
parameterise R1's simulator.

Rationale: the single most decisive parameter in the whole experiment is
the shape of the throughput-versus-concurrency curve past its knee —
whether throughput *plateaus* or *collapses*. If it plateaus, admission
control has nothing to save and the headline result evaporates. Assuming
that curve rather than measuring it makes every downstream number an
artifact of the modeller's choice.

**Acceptance**
- A measured throughput-vs-concurrency curve, with the knee identified.
- The simulator's server model is fitted to it, and the fit is plotted.
- Results are reported at **multiple knee shapes**, not just the measured
  one, so the finding's sensitivity to this parameter is visible.

### R3 — simulator fidelity (stated as anti-requirements)

Each item below is a way a simulator produces a **flattering lie** — a
result that makes a mechanism look good because the simulation was
unfaithful. All three seats independently named the first five.

The simulator MUST:

1. **Be partly open-loop.** If every user waits for a response before
   sending again, offered load self-throttles and congestive collapse is
   *mathematically impossible* — every admission mechanism then "works"
   because there was never an overload. Intents must arrive on a schedule
   independent of server health.
2. **Model retry amplification.** Retry-on-timeout makes offered load a
   function of latency: positive feedback. Without it the spike is a
   one-shot pulse any queue absorbs.
3. **Model bounded capacity** — workers, connections, accept queue — and
   degrade past the knee per R2. Never infinitely elastic.
4. **Contend for finite inventory atomically**, per (train, class, date).
   Parallel decrement deletes the hardest serialisation point in the
   system.
5. **Concentrate arrivals sub-second at T0**, with a pre-fire cohort and
   a retry-driven second wave. Uniform or plain-Poisson arrival turns a
   stampede into an ordinary load test.
6. **Charge for wasted work.** A timed-out request that instantly frees
   its worker means goodput never collapses; real servers keep computing
   for clients that have left.
7. **Use heavy-tailed / multimodal service times**, not exponential.
   Tails are the entire question.
8. **Distribute demand by Zipf across trains**, creating a hot key.
   Uniform demand deletes the sharding question.
9. **Include a scripted-bot cohort** with tighter timing than humans.
10. **Preserve per-user identity**, so duplicate attempts cannot be
    counted as independent users.

**Acceptance**
- Each item is a named, toggleable parameter with a test asserting the
  documented direction of effect (e.g. disabling retries measurably
  reduces peak offered load).
- The spec's results section reports which of these were enabled.

### R4 — the deliverable is an ablation ladder

Mechanisms are implemented as **pluggable strategies** over one
simulator, and the result is each rung's **marginal contribution**:

0. Naive — unbounded concurrency, retries on.
1. Bounded concurrency + FIFO.
2. Fast-fail from a cached per-pool sold-out counter.
3. Shard by (train, class, date).
4. **Virtual waiting room** with pre-issued ordered tokens.
5. Adaptive concurrency limiting (CoDel / gradient style).
6. Bot classifier (see R7).

Rationale: the ladder produces a credible answer whether or not any
given mechanism helps. A single "our system versus naive" comparison
cannot attribute the gain.

**Acceptance**
- Every rung runs against the same seeds and workloads.
- Results table gives each rung's marginal delta with confidence
  intervals.

### R5 — two baselines, and the strong one is the bar

- **Weak baseline:** naive unbounded concurrency, retries on.
- **Strong baseline:** bounded concurrency + FIFO + fast-fail.

Any adaptive or ML arm MUST be compared against the **strong** baseline.

Rationale: beating the naive strawman proves nothing; most of the
achievable gain is available from a hand-written bounded queue.

### R6 — pre-registered acceptance criteria

Thresholds are fixed **before** any run, and reported whether or not they
are met.

Metrics, at p50/p95/p99, **split by outcome** (winners vs rejected):

- Goodput — confirmed bookings/sec through the spike.
- Seats sold as % of inventory. Correctness floor: ~100%, with **zero**
  double-sold or lost seats.
- Time-to-definitive-answer, reported separately for winners and losers.
- Clean-rejection rate vs hard-error rate — **never summed**. "Position
  21,340, sold out in ~40s" is a success; a connection reset is a
  failure.
- Retry amplification = total requests / unique intents.
- Wasted-work ratio = server-seconds on abandoned requests / total.
- Fairness — seat share by arrival cohort; bot-cohort win share vs its
  population share.
- Settling time — seconds to return to normal latency after the spike.

#### Calibrated from measurement — 2026-08-09

These thresholds were **calibrated against a real contention measurement**,
not chosen by feel. `tools/calibrate_lock_contention.py` ran 64 concurrent
OS processes contending for one row (the hot key) through
`BEGIN IMMEDIATE / UPDATE / COMMIT`; 7 concurrency levels × 3 reps.
Raw data: `calibration/2026-08-09-sqlite-hotkey.csv`.

| Concurrency | Throughput (median) | p50 | p95 | **p99** |
|---:|---:|---:|---:|---:|
| 1 | 2287 ops/s | 0.23 ms | 0.37 ms | 5.9 ms |
| 8 | **3552 ops/s** (peak) | 0.23 ms | 0.33 ms | 1.8 ms |
| 32 | 3376 ops/s | 0.24 ms | 0.39 ms | 2.3 ms |
| 64 | 2850 ops/s | 0.22 ms | 0.33 ms | **2049 ms** |

**The measurement overturned this spec's original primary metric.**
Throughput does **not** collapse past the knee — it retains ~80% of peak
at 8× the knee concurrency, and p50/p95 stay flat at ~0.2/0.3 ms
throughout. The original threshold ("goodput within 10% of the
uncongested maximum") would have been *nearly satisfied by doing
nothing*, making it useless for distinguishing any mechanism from the
naive baseline.

What *does* collapse is the **tail**: p99 goes from ~2 ms at the knee to
**~2050 ms at 64× — roughly a 1000× degradation** — reproducibly, across
all three reps (2049/2067/2093 ms), while median latency does not move.
The distribution is bimodal: most requests are served immediately, a
minority wait behind the lock for seconds.

**Therefore: tail latency is the primary metric, and goodput is demoted
to a guardrail.** This is the calibration's main finding and it changes
what the experiment is measuring.

Also learned, and folded into the requirements above:

- **Zero errors at every level.** With a busy-timeout set, overload
  manifests entirely as *latency*, never as failures. An error-rate
  threshold would have measured nothing. R3's "clean rejection vs hard
  error" split still matters, but only once an admission mechanism
  introduces deliberate rejection.
- **Run-to-run variance is large** (throughput ranged 2226–4033 ops/s at
  fixed concurrency). R6's ≥ 20 replications requirement is vindicated;
  anything less cannot separate a 10% effect from noise.
- **The knee is shallow and wide** (peak at concurrency ~8, no sharp
  cliff), so "the knee" is a region, not a point. Report the curve.

#### Thresholds

Stated as formulas over measured quantities, so they recalibrate when R2
is rerun on different hardware or a different engine. Current constants
from the run above: `C_peak` = 3552 ops/s, `N_knee` = 8,
`p99_knee` = 1.8 ms.

**Succeeded** — the candidate arm, versus the *strong* baseline (R5), at
≥ 8× `N_knee` offered concurrency:

- **p99 time-to-definitive-answer ≤ 50 × `p99_knee`** (≈ 90 ms with
  today's constants) — versus ~2050 ms unmitigated. This is the headline.
- p99 answer for **rejected** users ≤ p99 for winners. Losers must learn
  they lost at least as fast as winners learn they won.
- Goodput ≥ 0.8 × `C_peak` — a **guardrail**, not a success signal. The
  naive baseline already meets it; an arm that *fails* it has traded away
  throughput for latency and must justify that.
- 100% of inventory sold; zero double-sold or lost seats.
- Retry amplification < 1.5×.

**Did not help** — an acceptable, reportable outcome: p99 improvement
falls within the 95% CI of the strong baseline across ≥ 20 seeded
replications. A claim of improvement requires ≥ 10% gain on p99 with
non-overlapping CIs and no > 5% regression on goodput or fairness.

A win in one corner of the parameter sweep is **not** a win. The
sensitivity table ships with the result.

#### What these numbers are not

Honest limits, so the constants are not over-trusted:

- **SQLite, not Postgres.** SQLite's writer lock serialises the whole
  database; Postgres locks per row. For the **hot-key** case (one train,
  everyone contending) that is a fair analogue. For the **sharded** case
  (R4 rung 3) it *overstates* contention, since different trains would
  not block each other under Postgres. R2's Postgres run is still owed
  and these constants are provisional until it lands.
- **Service time here is ~0.2 ms** — a bare row update with no
  application logic, network hop, or serialisation cost. Real per-request
  service time will be orders of magnitude larger, which moves `N_knee`
  down and may change the curve's shape entirely.
- **One machine, one run, no cross-hardware check.** The absolute numbers
  are laptop-specific; the *shape* (flat median, exploding tail) is the
  transferable finding.

### R7 — where ML is in scope, and where it is not

**Out of scope for v1: load prediction.** The instant is in the
timetable. Documented here so the exclusion is deliberate rather than an
oversight.

In scope only where the table agreed learning earns its place:

1. **Bot / automation classification** — a real adversarial problem, and
   the one that moves **fairness** rather than throughput. Carries a
   documented caveat: injecting bots with a signature and then detecting
   that signature is **circular**. Either evaluate against held-out
   behaviours the classifier was not shown, or report the result as
   illustrative only.
2. **Adaptive concurrency limiting** — control theory more than ML. Earns
   its place because the alternative is a hand-tuned constant that is
   wrong for every workload but one.
3. **Per-train demand forecasting** — not *when* the spike comes (known)
   but *which* trains and classes run hot and how hot, for pre-warming
   and shard placement. Quantile regression over historical bookings.

**Equal-effort rule.** If an ML arm is built, it gets the same
engineering effort as the classical arms. An under-built ML arm produces
a foregone negative, which is as dishonest as a flattering lie pointed
the other way.

### R8 — hypothesis: does the waiting room move the bottleneck?

Raised by the Antigravity seat and unresolved by deliberation, so it is
recorded as something v1 **tests** rather than assumes:

> Under realistic retry storms, does an edge-side virtual waiting room
> with deterministic token issuance actually solve server collapse — or
> does client polling of the queue **status-check** endpoint become the
> new single point of failure?

**Acceptance:** status-check traffic is modelled explicitly and reported
as its own load stream, with the waiting room evaluated at several
polling intervals.

## Explicitly deferred to v2

Real distributed load testing; autoscaling with cold-start (note: with a
30–90s cold start against a ten-second spike, autoscaling is expected to
be *useless* — demonstrating that is itself a legitimate finding);
payment step and seat-hold expiry (two-phase inventory); multi-region;
auth and CAPTCHA; adversarial bot co-evolution; production traffic
replay; anything that contacts IRCTC.

## Standing note — the honest framing

Two seats independently escalated to the same structural point, recorded
here because it will otherwise resurface late:

> This is a **scarcity-allocation** problem, not only a throughput
> problem. A race converts scarcity into a latency contest, which
> automation wins. The strongest available fixes may be **mechanism
> design** — staggered per-train opening times, or a pre-registration
> window with a lottery — rather than engineering at all.

Such mechanism changes are out of scope for a prototype that cannot alter
IRCTC policy. They belong in the write-up's discussion, so the
engineering result is not mistaken for a claim that the underlying
allocation problem has been solved.

## Expected headline result

Stated in advance so that finding it is not mistaken for a
disappointment:

> "Classical admission control plus a virtual waiting room recovered most
> of the lost goodput; adaptive limiting added a few percent; ML earned
> its keep only in bot detection, and only on fairness."

Per the chair's ruling, that is a **successful** outcome for this
prototype.

## Provenance

Round table thread `q-tatkal-spike-prototype-spec-001` (board messages
2, 3, 4, 8, 9). Seats: Claude (143s), Antigravity (74s), Codex (54s);
no absences; halted at round 1 on convergence. Chair ruling recorded as
board message 9. Declined at promotion: the full transcript report and a
lessons-corpus entry.
