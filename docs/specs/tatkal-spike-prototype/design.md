# tatkal-spike-prototype — design

**Status:** draft — awaiting chair approval

**Basis:** requirements.md (ratified 2026-08-11), the 2026-08-11 calibration
record, and decisions.md D1–D11. Every design element traces to a requirement;
anything not required is called out as a choice. Amended 2026-08-11 per the
round-table review (D10) and chair clarification rulings (D11).

---

## Shape of the system

One Python package, one process, no wall clock (R1). Three layers:

```
┌─────────────────────────────────────────────────────────┐
│ runner / CLI                                            │
│   seed sweep · arm selection · paired-stats · reports   │
├─────────────────────────────────────────────────────────┤
│ simulation core (deterministic, event-driven)           │
│   clock · event queue · rng streams                     │
│   workload gen → user clients → admission strategy      │
│                     ↓               (R4 rungs plug in)  │
│   server model (workers/queue/wasted work)              │
│   lock+inventory model (FIFO per pool)                  │
│   waiting room + status-check stream (rung 4, R8)       │
├─────────────────────────────────────────────────────────┤
│ measurement                                             │
│   raw event log → R6 metrics (winners/losers split)     │
│   calibration fit (2026-08-11 CSV) · knee-shape variants│
└─────────────────────────────────────────────────────────┘
```

Proposed layout:

```
src/tatkal_sim/
  core/        clock.py  events.py  rng.py
  model/       workload.py  users.py  server.py  locks.py  inventory.py
  strategies/  base.py  naive.py  bounded_fifo.py  fast_fail.py
               shard.py  waiting_room.py  adaptive.py  bot_classifier.py
  measure/     metrics.py  stats.py  fitting.py
  config.py  runner.py  cli.py
tests/
```

## Determinism (R1)

- **Virtual clock only.** Sim time is a float advanced by the event queue;
  `time.*` is banned in `src/` (enforced by a lint test).
- **Event queue** is a heap of `(time, seq, event)`; `seq` is a
  monotonically increasing tie-breaker so equal-time events pop in
  insertion order — the classic source of "same seed, different result."
- **Named RNG streams.** A master seed derives independent child streams
  via `sha256(master_seed || stream_name)` → `random.Random`: one stream
  per concern (`arrivals`, `service`, `retry`, `bots`, `abandon`,
  `stats`, …). Adding a mechanism or drawing more variates in one stream
  cannot perturb another — required for paired-seed comparisons (R6) to be
  low-variance. The `stats` stream seeds the bootstrap (D10/S4): an
  unseeded bootstrap would break byte-identical results the moment CIs
  enter a report.
- **Acceptance test:** two runs, same seed → byte-identical metrics JSON
  (hash compare). A full sweep target: laptop-scale (R1).

## Workload model (R3.1, R3.5, R3.8, R3.9, R3.10)

Intents are generated **before** the run as an open-loop schedule — arrival
times never depend on server health (R3.1). Each intent:
`(user_id, pool, cohort, t_arrival)` where `pool = (train, class, date)`.

- **Cohorts (R3.5, R3.9):** users are classified by **first arrival**
  into exactly one of `pre_fire` (trickle before T0), `t0_humans`
  (sub-second concentration at T0: truncated-normal jitter), or `bots`
  (tighter timing, e.g. uniform in [T0, T0+50 ms], and faster retry
  cadence). The retry-driven **second wave is a request-level phenomenon,
  not a user cohort** (D10/C3): it emerges from the retry model and is
  reported as offered-load-over-time, while fairness quantity 1 (seat
  share by cohort) uses the first-arrival classification only.
- **Demand (R3.8):** pools drawn Zipf(s) across trains; s is a named
  parameter; the hot key is train #1 by construction.
- **Identity (R3.10):** `user_id` persists across attempts; the metrics
  layer counts unique intents, never raw requests.
- **Scale anchor (a choice, not a trace):** default demand-to-supply
  ratio 20–50× — taken from the originating brief, not stated in
  requirements.md, and swept as a parameter.
- **C=256 operationalized (D10/S5):** offered concurrency at time t =
  intents with a request in flight at t. The default workload is sized so
  that the rung-0 measured peak in-flight during [T0, T0+1 s] is
  **256 ± 5%**, verified pre-registration on the naive arm. The per-seed
  intent trace is generated once and reused **byte-identically across
  every arm** — this is what makes paired per-seed deltas (D6) valid.

## Client model (R3.2, R3.6-adjacent)

Per-intent state machine: `submit → await response | timeout → retry?`.

- **Outcome matrix (R3.2, D10):** what the client does with each response
  class is fixed here, not left implicit:

  | Server outcome | Client behaviour | Definitive? |
  |---|---|---|
  | success (booked) | stop | yes |
  | clean rejection ("sold out") | stop | yes |
  | clean rejection ("not open", pre-T0 only) | re-fire at T0 | no |
  | mechanism rejection carrying an answer (fast-fail) | stop | yes |
  | waiting-room token / queue position | poll at interval `p`, no retry | no |
  | timeout (no response) | retry w/ `backoff(attempt)` | no |
  | hard error (reset / 5xx / shed without answer) | retry w/ backoff | no |

  A `p_retry_after_reject` parameter (default 0, sensitivity-swept) models
  users who re-try even after a definitive rejection.
- **Retries (R3.2):** retryable outcomes above retry up to `max_attempts`,
  making offered load a function of latency — the positive-feedback loop.
  Toggleable.
- **Abandonment:** each user has a patience budget; abandoning users stop
  retrying but their in-flight request still occupies the server (feeds
  R3.6 wasted work).
- TTDA is measured from *first* request of the intent to final definitive
  outcome, exactly as the R6 definition requires.

## Server model (R3.3, R3.6, R3.7)

Bounded resources, never elastic (R3.3) — all three non-optional (D10/S7):
`workers` (concurrent service slots), `accept_queue` (bounded FIFO;
**drop-newest on overflow → connection-reset hard error**), and
`conn_limit` (concurrent connections; exceeding it → immediate reset —
calibration analogue: `max_connections=450`).

**Pre-T0 semantics (D10/S2):** no inventory is allocated before T0, ever —
inventory decrements can occur only at sim time ≥ T0, assertion-checked. A
booking request arriving before T0 receives a clean "not open" rejection.
Unlike "sold out", "not open" is **not definitive for the intent**: the
pre-fire cohort's scheduled behaviour is to fire again at T0. Its TTDA
clock still starts at the *first* request, so pre-firing is not free.

Service time (R3.7) = `app_time + lock_wait + lock_hold`:

- `app_time`: lognormal body fitted from the calibration's uncontended
  levels (~0.3 ms scale on the calibration hardware), with a heavy-tail
  mixture component (parameterised, sensitivity-swept).
- `lock_wait`: **not drawn from a distribution — emergent** from the lock
  model below. This is the design's central fidelity commitment: the
  calibration showed tails are queueing, not service variance.
- **Wasted work (R3.6):** a worker slot stays occupied until service
  completes even if the client has timed out/abandoned; toggle off →
  slot freed instantly (the flattering lie, kept only as an ablation).

## Lock and inventory model (R3.4)

Per pool `(train, class, date)`: a FIFO lock (Postgres `SELECT FOR UPDATE`
semantics, per the 2026-08-11 finding that discipline determines tails) and
an integer seat count decremented inside the hold. End-of-run invariants:
`sold + remaining == initial`, zero double-sells, zero lost seats —
assertion-checked every run, reported per R6.

The **sharded** configuration (rung 3) maps pools to independent locks;
the unsharded one funnels all pools through one lock — both shapes were
measured directly (hot vs sharded8 in the calibration).

## Fidelity toggles (R3 acceptance)

`FidelityConfig` exposes every R3 item as a named boolean/parameter:

Direction-of-effect tests assert **measurable directional deltas at fixed
seeds**, never impossibility claims (D10/C4):

| Toggle | R3 | Direction-of-effect test asserts |
|---|---|---|
| `open_loop_arrivals` | 3.1 | off → peak offered load and overload depth drop measurably |
| `retries_enabled` | 3.2 | on → peak offered load rises |
| `bounded_capacity` | 3.3 | off → backend effectively infinite: queueing and overload signals vanish (**ablation-only** — never enabled in any ladder run) |
| `atomic_inventory` | 3.4 | off → double-sells appear |
| `t0_concentration` | 3.5 | off → peak concurrency falls |
| `wasted_work` | 3.6 | on → goodput falls under overload |
| `heavy_tail_service` | 3.7 | on → p99/p50 ratio rises |
| `zipf_demand` | 3.8 | off → hot-pool share falls |
| `bot_cohort` | 3.9 | on → bot win share > population share |
| `user_identity` | 3.10 | off → retry amplification hidden |

Note the separation D10/C4 requires: rung 0's "unbounded concurrency"
means unbounded **admission** over the always-finite R3.3 backend. The
`bounded_capacity` toggle ablates the backend itself and exists only to
demonstrate the flattering lie; every ladder run keeps it on.

Results reports enumerate enabled toggles (R3 acceptance).

## Strategy interface (R4, R5)

```python
class AdmissionStrategy(Protocol):
    def on_arrival(self, req, sim) -> Admit | Reject | Enqueue: ...
    def on_departure(self, req, sim) -> None: ...   # completion or abandon
```

Rungs are cumulative compositions (D5): rung k = rungs 1..k−1 + one
mechanism. Rung 0 (naive) and rung 2 (strong baseline) are the R5
baselines. Fast-fail (rung 2) consults a cached per-pool sold-out counter
with a staleness parameter — the cache being stale is part of the model,
not a bug.

**Waiting room (rung 4) + R8:** pre-issued ordered tokens; clients outside
the admitted window poll a status endpoint at interval `p`. Status checks
are first-class requests consuming the same worker pool, with their own
service-time parameter (`status_service_time`, default `app_time`/5),
reported as their own load stream and swept over several `p` values.

- **Sold-out eviction is required (D10, Antigravity's failure case):** at
  pool sell-out the waiting room immediately resolves every queued token
  for that pool with a definitive sold-out answer. Without it, rejected
  users' TTDA equals time-to-drain and rung 4 fails the D11-clarified bar
  by construction. A *pure-queuing* variant (no eviction) is admissible
  only as a labelled out-of-order run.
- **Saturation criterion (D10/S6):** the status endpoint is declared the
  new bottleneck iff, at any swept `p`, status-stream p99 in-server wait
  exceeds booking-stream p99 in-server wait at the same rung, **or** the
  status stream consumes > 50% of worker capacity. R8's hypothesis is
  answered by evaluating this criterion, either way.

**Adaptive limiter (rung 5):** gradient/AIMD on observed latency vs a
target derived from `p99_knee`. Treated as control theory (R7.2).

**Bot classifier (rung 6, R7.1):** features from per-user timing only
(arrival offset, inter-attempt intervals, retry cadence). Train/evaluate
split by *behaviour family*: the classifier never sees the generating
parameters of the held-out families (circularity guard). If held-out
evaluation is infeasible, results are labelled illustrative — per R7.1.

- **The intervention (D10/S1):** a flagged verdict feeds a two-priority
  admission queue — flagged users' requests are served only when no
  unflagged request is waiting. Never a hard reject: deprioritization
  bounds the harm of false positives, and the classifier threshold is a
  swept parameter. This is what makes rung 6 an `AdmissionStrategy` with
  a defined marginal delta; P8.2's with/without comparison toggles
  exactly this priority rule.

Equal-effort rule (R7): the classifier gets the same engineering budget as
a classical rung; an under-built ML arm is a foregone negative. R7.3
(demand forecasting) is **omitted from v1** by chair ruling (D11).

## Measurement (R6)

- **Raw event log** per request: intent id, user, cohort, pool, arrival,
  outcome, timestamps. Metrics are *derived*, never accumulated inline —
  so metric definitions can change without touching the sim.
- All R6 metrics computed exactly as defined (TTDA split winners/rejected;
  clean-rejection vs hard-error never summed; retry amplification;
  wasted-work ratio; fairness both quantities; settling time with the
  ratified 1 s window / 2× band / 5 s sustain). Per D11: the 34.2 ms
  success bar is evaluated for winners and rejected users
  **independently**, and goodput = confirmed bookings ÷ (t_sellout − T0),
  the sell-out window.
- **Paired-seed harness (D6):** runs every arm over the same ≥ 20 seeds
  and computes per-seed deltas for **both comparison families (D10/S3)**:
  (a) rung k vs rung k−1 — the marginal delta R4 requires; (b) any
  adaptive/ML arm vs the strong baseline — the R5 requirement. Bootstrap
  95% CI on the median delta: **B = 10,000, percentile method, drawn from
  the seeded `stats` stream** (D10/S4+S7). CI-overlap comparisons are not
  implemented at all, so the disallowed test cannot be run by accident.
  The report generator labels out-of-order/out-of-ladder arms distinctly
  (R4's labelling rule).

## Calibration fit (R2, carried half)

`measure/fitting.py` loads `calibration/2026-08-11-postgres-http.csv`,
fits the server model's parameters (app_time distribution; worker count
such that simulated throughput-vs-concurrency and p99-vs-concurrency match
the measured curve), and emits a fit plot (measured points vs simulated
curve, both regimes).

**Fit protocol (D10/S8 — predeclared, replacing the min–max hard gate):**

- Objective: joint log-space RMSE over per-level *medians* of steady
  throughput and steady p99.
- Target: every fitted median within ±25% of the measured median; the
  min–max band is plotted as context, not enforced as a gate.
- Overfit guard: leave-one-level-out — refit excluding each level in turn
  and check the held-out level's prediction stays within ±40%.
- Miss path: per-level residuals are reported; the chair either accepts a
  documented deviation or directs model refinement. A silent bad fit is
  the one prohibited outcome.

The fit MUST distinguish app-server queueing from row-lock queueing
(Antigravity/D10): the sharded8 control (p99 halves at equal throughput)
is the identification target separating the two queue contributions.

**Knee-shape variants (R2 acceptance):** beyond the fitted shape, results
are reported under synthetic *plateau* and *cliff* variants, so findings'
sensitivity to the curve shape is visible.

## Out of scope

Everything in requirements "Explicitly deferred to v2". The simulator
never contacts any external service; the only I/O is config in, event
logs/reports out (safety boundary).

## Design choices open for chair review

1. Python + stdlib-only core (numpy/matplotlib allowed in `measure/` only)
   — keeps the teaching goal; sim performance target is R1's "sweep on a
   laptop", estimated fine at these event counts.
2. Event-log-then-derive architecture costs memory (~10⁶ events/run) for
   auditability. Alternative (inline accumulation) is faster but freezes
   metric definitions into the sim. Recommended: event log.

*(Resolved since first draft: R7.3's disposition — omitted from v1 by
chair ruling, decisions.md D11.)*
