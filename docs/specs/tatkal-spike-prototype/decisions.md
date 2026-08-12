# tatkal-spike-prototype — decisions

**Status:** living record. Entries are append-only; a reversed decision gets a
new entry pointing back, never an edit that hides the original.

Format: each entry records what was decided, by whom, on what evidence, and
what it binds. "Chair" is the project owner acting as promotion authority for
the round-table workflow.

---

## D1 — Classical traffic management is the v1 experiment; ML is confined

**Date:** 2026-08-09 · **Decided by:** round table (Claude, Antigravity,
Codex seats), chair-promoted · **Status:** ratified

The originating brief led with AI/ML traffic *prediction*. All three seats
independently rejected the prediction framing: the spike is at a known,
scheduled clock instant; there is nothing to forecast and no provisioning
horizon inside a ten-second surge. ML is scoped to exactly three roles
(requirements R7): bot classification, adaptive concurrency limiting, and
per-train demand forecasting.

**Binds:** requirements R7; the "Experimental framing" section.
**Recorded so that** the narrowing of the original goal is deliberate, not
silently forgotten.

## D2 — A negative result on ML counts as success

**Date:** 2026-08-09 · **Decided by:** chair ruling, round-table promotion ·
**Status:** ratified

The deliverable is a defensible systems experiment. If a correctly built,
equal-effort ML arm shows no statistically meaningful improvement over the
strong baseline, that is a *successful* outcome, not a failure to be
massaged.

**Binds:** requirements "Expected result"; R7 equal-effort rule.

## D3 — The 2026-08-09 SQLite tail result is withdrawn as a harness artifact

**Date:** 2026-08-11 · **Decided by:** review (Opus), verified independently
(Fable) · **Status:** ratified, recorded in requirements R2

The recorded p99 ≈ 2050 ms at C=64 was shown to be a synchronized-start
transient: every sample above 100 ms was a worker's *first* transaction
(start offset 0.000), stretched by SQLite's unfair busy-wait backoff ladder.
The slow-sample count tracked worker count, not window length; whether p99
captured it was pure sampling arithmetic that flipped with run-to-run
throughput variance. A same-machine re-run gave p99 = 1.62 ms.

**Consequence:** the then-primary metric (tail latency) lost its evidential
basis and was marked provisional until R2 was rerun (see D8).
**Binds:** requirements R2 "Calibration status", withdrawn subsection.

## D4 — R2 must measure two regimes, separately

**Date:** 2026-08-11 · **Decided by:** review recommendation (Fable),
adopted in the rerun harness · **Status:** ratified by execution

The withdrawn transient was not garbage — it was an accidental measurement
of the T0 convoy, the phenomenon R3.5 requires the simulator to model. The
rerun therefore measures: (a) **steady state**, first post-T0 request
excluded, which fits the service model and sets constants; (b) **T0
convoy**, exactly those first requests fired at a shared instant with
connection setup paid pre-window, which calibrates R3.5.

**Binds:** `tools/calibrate_r2.py`; R2 acceptance interpretation.

## D5 — The ablation ladder is cumulative

**Date:** 2026-08-11 · **Decided by:** review finding, adopted into
requirements · **Status:** ratified

Rung k enables rungs 1..k−1 plus one new mechanism, so each delta isolates
one addition. Evidence this was always intended: R5's strong baseline is
literally cumulative rung 2. Marginal deltas are conditional on the stack
order; results must say so; clearly-labelled out-of-order runs are allowed
when an interaction is suspected.

**Binds:** requirements R4.

## D6 — Paired per-seed statistics; CI-overlap testing disallowed

**Date:** 2026-08-11 · **Decided by:** review finding, adopted into
requirements · **Status:** ratified

R1's shared seeds make every arm-vs-baseline comparison a paired design.
The decision rule is the distribution of per-seed deltas across ≥ 20
replications with a 95% CI; comparing independently computed CIs for
overlap is explicitly not acceptable (discards pairing; overlap is not a
significance test).

**Binds:** requirements R6 "Statistical decision rule", R4 acceptance.

## D7 — Postgres over Docker-Postgres; throwaway local instance

**Date:** 2026-08-11 · **Decided by:** execution constraint · **Status:**
environmental note, not load-bearing

Docker Desktop's daemon would not start headless on the host. The R2 rerun
used Homebrew `postgresql@17` (17.10) as a throwaway instance: scratchpad
data dir, port 54329, `max_connections=450` (must exceed top concurrency —
capping connections below offered load would itself be an admission
mechanism), `LC_ALL=C` for the macOS multithreaded-postmaster issue, no
service registered. Reproduction commands are in `tools/calibrate_r2.py`.

## D8 — Constants fixed; operating point C=256; p99 TTDA primary

**Date:** 2026-08-11 · **Decided by:** chair · **Status:** **ratified —
binds R4 runs**

On the 2026-08-11 calibration (183 runs, zero hard errors):

- `N_knee` = 2 (knee region 2–8), `C_peak` = 4865 ops/s,
  `p99_knee` = 0.684 ms — fixed.
- Operating point: **C=256** (128 × `N_knee`, deepest calibrated overload),
  replacing the pre-measurement 8 × `N_knee`, where the success threshold
  coincided with unmitigated performance.
- **Primary metric: p99 time-to-definitive-answer.** Evidence: tail grows
  ~1000× (0.68 → 689 ms) and queue discipline — not capacity — determines
  whether a synchronized stampede produces catastrophic tails (the
  convoy/steady split existed under SQLite's unfair backoff and vanished
  under Postgres FIFO).
- **Goodput is the guardrail** (≥ 0.8 × `C_peak` = 3892 ops/s) and it
  bites: unmitigated delivers 1537 ops/s at C=256.
- The 50× threshold multiplier was retained after re-checking against
  measurement (≈ 34 ms bar vs ~689 ms unmitigated).

Constants MUST NOT be revised to accommodate a result; they recalibrate
only via an R2 rerun on different hardware/engine, with re-ratification.

**Binds:** requirements R6 (constants table, success criteria); R4 runs.

## D9 — Carried to the build phase (not blockers of requirements)

**Date:** 2026-08-11 · **Decided by:** chair (implicit in D8 ratification
closing the requirements phase) · **Status:** open items, tracked in
tasks.md

1. Simulator-fit half of R2 acceptance (fit server model, plot fit, report
   multiple knee shapes) — requires the simulator to exist. → task P4.
2. Thresholds for wasted-work ratio, fairness, settling time: MUST be set
   or designated report-only **before any R4 arm runs**. Fairness is
   load-bearing (R7.1 rests the ML case on it; the improvement rule
   references a 5% fairness regression bound). → Gate A in tasks.md.

## D10 — Round-table review of design/tasks/decisions: approve with amendments

**Date:** 2026-08-11 · **Decided by:** round table (thread
`q-tatkal-spec-docs-review-001`, board msgs 2, 3, 4, 8; halted round 1 on
convergence), chair-promoted · **Status:** ratified

All three seats independently approved the architecture, determinism
design, 10/10 R3 toggle mapping, Gate A placement, and buildability — and
independently converged on an amendment set applied under this decision:

- **C3** retry-wave is a request-level phenomenon, not a user cohort:
  fairness classifies users by *first-arrival* cohort.
- **C4** direction-of-effect tests assert measurable deltas, not
  absolutes; rung 0's "unbounded concurrency" means unbounded *admission*
  over the always-finite R3.3 backend.
- **S1** rung 6's intervention defined: two-priority deprioritization of
  flagged users, never hard rejection.
- **S2** pre-T0 semantics: no inventory allocation before T0; early
  requests get a clean "not open" rejection.
- **S3** both comparison families computed and reported: rung-vs-
  predecessor and arm-vs-strong-baseline.
- **S4/S7** bootstrap: seeded `stats` RNG stream, B=10,000, percentile
  method; accept-queue overflow policy explicit; `conn_limit`
  non-optional.
- **S5** C=256 operationalized: rung-0 measured peak in-flight in
  [T0, T0+1 s] = 256 ± 5%; identical per-seed intent traces across arms.
- **S6** status-endpoint saturation criterion defined (see design.md
  waiting room).
- **S8** P4 fit gets a predeclared objective, tolerance, miss path, and
  overfit guard.
- Sold-out eviction is REQUIRED in the rung-4 waiting room (Antigravity's
  failure case); a pure-queuing variant is admissible only as a labelled
  out-of-order run. Gate A must define the fairness *statistic and
  regression calculation*, not merely a value (Codex). A rung-0 profile
  of the three unthresholded metrics is added to P5 to inform Gate A
  (Antigravity).

Full transcript: `~/.attune/reports/roundtable/q-tatkal-spec-docs-review-001.md`
(machine-local).

## D11 — Chair clarification rulings on ratified criteria; R7.3 omitted

**Date:** 2026-08-11 · **Decided by:** chair (board msg 10) · **Status:**
**ratified — clarifications only, no ratified constant value changed**

1. **The 34.2 ms p99 TTDA success bar binds winners AND rejected users
   independently.** Coherent with the existing "rejected ≤ winners"
   criterion; resolves the C1 ambiguity all three seats flagged.
2. **Goodput is measured over the sell-out window** — T0 until inventory
   exhausted. Goodput is thereby a *rate* of converting scarcity
   (mechanism-sensitive), not an inventory-capped total; "through the
   spike" in R6 means this window.
3. **R7.3 (per-train demand forecasting) is omitted from v1**, recorded
   per Codex's condition. The R7.3 scope definition stands for v2. If
   ever built, it is an out-of-order interaction arm paired against
   rung 3 — never a ladder rung (D5).

**Binds:** requirements R6 (clarifying notes), design.md measurement,
tasks.md P8.

## D12 — Chair sign-off: design.md and tasks.md approved; build phase opens

**Date:** 2026-08-11 · **Decided by:** chair · **Status:** ratified

design.md and tasks.md, as amended under D10/D11 and unanimously
approve-with-amendments'd by the round table (thread
`q-tatkal-spec-docs-review-001`), are **approved**. The task ladder is
binding as gated: P0 begins immediately; Gate A remains the only chair
decision standing between P5 and the first R4 arm run.

**Binds:** design.md (status: approved), tasks.md (status: approved,
ladder active).

## D13 — P4 fit: miss path invoked; one refinement round; best-of accepted

**Date:** 2026-08-11 · **Decided by:** chair (miss-path ruling), executed
per D10/S8 protocol · **Status:** ratified

The round-1 fit (congestion model: `app_time × (1 + k·conns^γ)`, fitted
W=2, service 0.077 ms, k=0.24, γ=0.67, hold 0.09 ms, 1% × 5 ms app-tail)
reproduced the throughput curve within ±25% at 6 of 9 levels and the
qualitative shape everywhere, but missed the p99 band at 5 levels — the
measured mid-range tails carry Python-scheduler burstiness (p99/p50 up to
25×) that a clean FIFO model does not contain. Per the predeclared miss
path the chair directed **one refinement round**: a hold-stall mechanism
(rare stall inside the lock hold, blocking the queue behind it) plus
`sigma` freed as a fit parameter.

**The refinement made the fit worse** (final loss 0.611 vs 0.370; 9 vs 7
miss levels): the 1 s grid-search duration systematically penalises stall
configurations, driving the search into a no-tail corner that generalises
badly at the 2 s evaluation. An honest negative — recorded, not hidden.

**Ruling executed: best-of = round 1.** Its residual misses are
chair-accepted deviations, recorded in `calibration/fit-2026-08-11.json`
(`meta.chair_accepted_deviations`). The hold-stall mechanism stays in the
model (inert in the fitted profile) for future sensitivity work. Two
model extensions are hereby part of the server model: `congestion_k/γ`
and `hold_stall_p/mean` — both default-zero outside calibrated profiles.

**Consequence for interpretation:** the fitted profile is faithful on
throughput and on tail *direction*, conservative on tail *magnitude*
(model p99 ≈ 0.6–0.7× measured at high C). Mechanism comparisons remain
valid — every arm runs on the same conservative model — and the knee
variants (plateau/cliff) bracket the shape uncertainty per R2.

## D14 — Gate A rulings; C=256 operationalization amended (chair, 2026-08-11)

**Date:** 2026-08-11 · **Decided by:** chair, on the rung-0 fitted-profile
20-seed Gate A profile · **Status:** ratified — unblocks R4 arm runs

**C=256 operationalization (amending D10/S5's realization).** Measurement
showed "peak in-flight = 256 ± 5%" is unsatisfiable: congestion feedback
makes peak in-flight bistable (sub-critical bursts stay ≤ ~180; anything
past the knife-edge blows through to the 451 connection ceiling; at the
edge, seeds swing 30↔398). Ruling: the operating point is realized as the
**supercritical spike** — operating workload 2650 users (2500 t0-humans,
150 bots, 30 pre-fire), binding check: **in-flight ≥ 256 sustained for
≥ 1 s** at the calibration-analogue conn ceiling (450). Measured: 1.3–2.1 s
sustained across seeds. The ratified *evaluation point* (deepest calibrated
overload) is unchanged; only its workload realization is amended.

**Gate A dispositions** (profile: F ≈ 5.1, wasted-work 0.0 with 47%
hard-error rate, settling uncomputable 0/20):

1. **Fairness — thresholded.** Scalar `F = bot win-share ÷ bot population
   share` (rung-0 naive measures F ≈ 5.1). Success direction: reduce F
   toward 1. Regression bound: F MUST NOT rise > 5% *relative* vs the
   strong baseline — this makes R6's "no > 5% regression in fairness"
   computable.
2. **Wasted-work ratio — report-only** in v1. In the fitted regime
   overload manifests as connection resets, not stale work; the metric
   bites under knee variants and slow-service sensitivity runs, where it
   is reported.
3. **Settling time — report-only**, plus a workload amendment: a small
   post-T0 `background` cohort (trickle after the spike) so recovery is
   measurable at all; on the spike-only workload the run ends with the
   spike and no 5 s quiet interval can exist.

**Binds:** requirements R6 (Gate A items), workload.py OPERATING_WORKLOAD,
tasks.md Gate A. R4 arm runs are now unblocked.

## Open questions (no decision yet)

- **Winners' p99 TTDA vs the 34.2 ms bar (found at P6, 2026-08-11).**
  The pre-fire cohort's TTDA clock starts at its first pre-T0 poll (~20 s
  before T0, by ratified design), so winners' p99 is ~18.8 s for EVERY
  arm — the D11 success bar for the winners population is structurally
  unmeetable. Needs a chair ruling before P9 evaluation: e.g. (a) TTDA
  measured from max(first request, T0); (b) pre-fire winners reported as
  their own population; or (c) the bar binds post-T0 TTDA only. The
  rejected-population bar is unaffected (rungs 1-2 meet it with room).
