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

## Open questions (no decision yet)

- **Fairness threshold value** — needs a chair decision at Gate A; the
  metric definition (seat share by cohort; bot win share vs population
  share) is fixed, the pass/fail bar is not.
- **Whether R7.3 (demand forecasting) ships in v1** — R4's ladder has no
  rung for it; it only feeds shard pre-warming. Proposed disposition in
  tasks.md P8 (optional, chair call).
