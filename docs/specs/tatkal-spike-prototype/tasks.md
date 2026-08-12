# tatkal-spike-prototype — tasks

**Status:** draft — awaiting chair approval of the ladder

**Basis:** requirements.md (ratified 2026-08-11), design.md (draft),
decisions.md D1–D11. Amended 2026-08-11 per round-table review (D10) and
chair rulings (D11). Tasks are gated: a phase's exit criteria must hold
before the next phase starts. **Gate A is a chair decision, not a task.**

Sizes: S (≤ half day), M (~1 day), L (multi-day). Every task names its
requirement trace and its acceptance check.

---

## P0 — scaffold

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| P0.1 | Package skeleton `src/tatkal_sim/` per design layout; pytest wired; ruff/black config | S | R1 | `pytest` runs green on an empty suite; package imports |
| P0.2 | `FidelityConfig` dataclass with all ten R3 toggles, defaults = all fidelity ON | S | R3 | config round-trips to/from JSON; unknown keys rejected |
| P0.3 | Wall-clock lint test: `time.*`/`datetime.now` banned in `src/` | S | R1 | test fails on a planted violation, passes clean |

**Exit:** CI-runnable test suite; config schema frozen enough to build on.

## P1 — deterministic core

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| P1.1 | Virtual clock + event heap with `(time, seq)` ordering | M | R1 | equal-time events pop in insertion order (test) |
| P1.2 | Named RNG streams from master seed (`sha256(seed‖name)`) | S | R1, R6 | same seed → identical draws; streams independent (add a draw to one, others unchanged) |
| P1.3 | Determinism harness: run twice, hash metrics JSON | S | R1 | byte-identical across two runs; test in CI |

**Exit:** R1 acceptance ("identical seeds → byte-identical results") holds
for a trivial workload.

## P2 — workload and clients

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| P2.1 | Open-loop intent generator: first-arrival cohorts (pre-fire, T0 humans, bots), Zipf pools, persistent user ids | M | R3.1, 3.5, 3.8, 3.9, 3.10, D10/S5 | generated schedule independent of any server state; cohort timing histograms match config; rung-0 peak in-flight during [T0, T0+1 s] = 256 ± 5% at the operating workload; per-seed trace byte-identical across arms; pre-T0 arrival density sufficient for the settling-time baseline window |
| P2.2 | Client state machine: outcome matrix (design), retry w/ backoff, patience/abandonment | M | R3.2, D10 | retry storm reproduces: offered load rises with induced latency; every outcome class's client behaviour asserted per the design matrix (incl. "not open" re-fire and `p_retry_after_reject`) |
| P2.3 | Direction-of-effect tests for toggles 3.1, 3.2, 3.5, 3.8, 3.9, 3.10 | M | R3 acceptance | each toggle's documented direction asserted (design table) |

**Exit:** every workload-side R3 toggle named, toggleable, direction-tested.

## P3 — server, locks, inventory

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| P3.1 | Bounded server: workers, accept queue (drop-newest → hard error), `conn_limit` — all three non-optional; pre-T0 "not open" path | M | R3.3, D10/S2+S7 | past-knee degradation exists; no infinite elasticity; overflow and conn-limit produce hard errors (tests); zero inventory decrements before T0 (test) |
| P3.2 | FIFO lock per pool; `lock_wait` emergent from queueing, not drawn | M | R3.4, D8 evidence | at N contenders with `heavy_tail_service` pinned OFF, p99 ≈ queue-depth × hold time (tolerance band) |
| P3.3 | Atomic inventory + end-of-run invariants (sold+remaining==initial, no double-sell/lost) | S | R3.4, R6 | invariant assertions run on every sim run; violation on toggle-off (test) |
| P3.4 | Wasted work: slot held past client abandonment; heavy-tail service mixture | M | R3.6, 3.7 | goodput falls when enabled under overload; p99/p50 rises with tail component (tests) |
| P3.5 | Direction-of-effect tests for toggles 3.3, 3.4, 3.6, 3.7 | S | R3 acceptance | as design table |

**Exit:** all ten R3 toggles complete with direction tests; unmitigated
(rung-0) sim runs end-to-end at C=256-equivalent load on a laptop.

## P4 — calibration fit (closes R2)

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| P4.1 | Fit server params to `calibration/2026-08-11-postgres-http.csv` (both regimes) per the design's fit protocol | L | R2, D10/S8 | predeclared objective (joint log-RMSE on medians); every fitted median within ±25% of measured; leave-one-level-out guard within ±40%; per-level residuals reported; on miss, chair review path — never a silent bad fit |
| P4.2 | Fit plot: measured points vs simulated curve, steady + convoy | S | R2 | plot artifact committed alongside the fit params |
| P4.3 | Knee-shape variants (fitted / plateau / cliff) as selectable server profiles | M | R2 | sweep can run under each variant; variant named in every report |

**Exit:** R2 acceptance fully satisfied — the carried half lands here.

## P5 — metrics and statistics

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| P5.1 | Raw event log + derived R6 metrics, exactly per definitions (TTDA split evaluated per-population per D11, clean-reject vs hard-error never summed, retry amp, wasted-work, fairness ×2 by first-arrival cohort, settling time w/ ratified window params, goodput over the sell-out window per D11) | L | R6, D10/C3, D11 | golden-file test: hand-computed metrics on a tiny scripted run match |
| P5.2 | Paired-seed harness: ≥20 seeds × arms, per-seed deltas for BOTH comparison families (rung-vs-predecessor; arm-vs-strong-baseline), bootstrap CI (B=10,000, percentile, seeded `stats` stream) | M | R6, D6, D10/S3+S4+S7 | on synthetic data with known effect, CI covers truth; byte-identical CIs across reruns; no CI-overlap API exists |
| P5.3 | Report generator: both comparison families w/ CIs, out-of-order arm labelling, enabled-toggles list, sensitivity table stub, rung-0 profile of the three unthresholded metrics (Gate A input) | M | R4, R6, D10 | report renders from a 2-arm smoke run; Gate A profile section present |

**Exit:** a naive-vs-anything comparison produces a correct, pre-registered
-format report.

---

## GATE A — chair decision (blocks all R4 arm runs)

Set thresholds, or designate report-only, for: **wasted-work ratio,
fairness, settling time** (decisions.md D9.2; fairness is load-bearing for
R7.1 and the 5% regression bound). Per D10 (Codex), the fairness decision
MUST define the **scalar statistic and how "5% regression" is computed**
over the two fairness quantities — not merely a pass/fail value. P5.3's
rung-0 profile of these three metrics is the informing input. Record the
decision in decisions.md.

---

## P6 — baselines (rungs 0–2)

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| P6.1 | Strategy interface + rung 0 (naive) | S | R4, R5 | rung 0 at C=256 reproduces calibration-shaped collapse (fit sanity) |
| P6.2 | Rung 1: bounded admission + FIFO | S | R4 | paired delta vs rung 0 reported with CI |
| P6.3 | Rung 2: fast-fail w/ stale-able sold-out cache (= strong baseline) | M | R4, R5 | strong baseline fixed; staleness param swept |

**Exit:** both R5 baselines runnable; every later arm compares against
rung 2 via the paired harness.

## P7 — mechanism rungs 3–5

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| P7.1 | Rung 3: shard by pool | M | R4 | hot vs sharded delta consistent in *direction* with the measured sharded8 control |
| P7.2 | Rung 4: waiting room — ordered tokens, **sold-out eviction**, status-check load stream | L | R4, R8, D10 | eviction resolves all queued tokens at sell-out (test); status traffic reported as own stream; swept over ≥3 polling intervals; the design's saturation criterion evaluated and reported at each interval — that evaluation IS the R8 answer |
| P7.3 | Rung 5: adaptive limiter (AIMD/gradient on latency vs `p99_knee`-derived target) | M | R4, R7.2 | paired delta vs rung 4 stack; limiter stability shown across knee-shape variants |

**Exit:** classical ladder complete, every rung's marginal delta + CI in
the report.

## P8 — ML arm (rung 6)

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| P8.1 | Bot classifier on timing features + the two-priority deprioritization intervention (design D10/S1); train/held-out split by behaviour family | L | R4, R7.1, D10 | intervention implemented as an `AdmissionStrategy`; held-out evaluation, or results labelled illustrative; equal-effort note recorded |
| P8.2 | Fairness impact: bot win share vs population share, with/without the priority rule | M | R6, R7.1 | fairness deltas reported against Gate A thresholds |

*(P8.3 removed: R7.3 demand forecasting omitted from v1 by chair ruling —
decisions.md D11.)*

**Exit:** R7.1 and R7.2 delivered per the equal-effort rule; R7.3 omitted
per D11 — recorded, not silently dropped.

## P9 — pre-registered evaluation and write-up

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| P9.1 | Full sweep: all rungs × ≥20 seeds × knee-shape variants at C=256 operating point | M (compute) | R4, R6 | success criteria evaluated exactly as ratified (D8); reported met-or-not, never adjusted |
| P9.2 | Sensitivity table (knee shapes, Zipf s, retry policy, bot share) | M | R2, R6 | "a win in one corner is not a win" — table ships with the result |
| P9.3 | Write-up: findings vs the expected-result hypothesis; honest-framing section (scarcity/mechanism-design discussion); R3 toggle enumeration | M | Expected result, Honest framing | negative results reported per D2; no claim beyond the evidence |

**Exit:** the experiment answers its framing question with pre-registered
criteria, at which point the spec's "Expected result" section is graded.

---

## Standing rules (apply to every phase)

- Determinism test and inventory invariants run in CI on every commit.
- No constant from R6 is touched outside an R2 rerun + re-ratification.
- Every report lists enabled fidelity toggles (R3 acceptance).
- Drift from this ladder gets named in-session before it happens, not
  discovered after.
