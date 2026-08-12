# tatkal-spike-prototype — v1 results

**Status:** final (P9 evaluation, 2026-08-11). Composed from
`reports/p9-evaluation-data.json` (tools/p9_evaluation.py — deterministic,
committed) and the phase reports (`reports/p6-…`, `p7-…`, `p8-…`).
Pre-registration chain: D8 (constants) → D11 (populations, goodput window)
→ D14 (operating point, Gate A) → D15 (resolution-latency operand). No
constant or threshold was revised after any result existed; every
clarification is decision-logged with its rationale and arm-invariance
defense.

## 1. What was run

- **System under test:** seeded deterministic DES calibrated against the
  2026-08-11 Postgres/HTTP measurement (fit record
  `calibration/fit-2026-08-11.json`, chair-accepted deviations per D13 —
  the model is faithful on throughput and tail *direction*, conservative
  ~0.6–0.7× on tail *magnitude*; every arm runs on the same conservative
  model, so comparisons stand).
- **Operating point:** the supercritical realization of C=256 (D14):
  2,650-user spike + 60-user background trickle, in-flight ≥ 256 sustained
  ≥ 1 s on rung 0; ~13× overall / ~40× hot-pool oversubscription; 200
  seats.
- **The ladder (cumulative, D5):** rung 0 naive → 1 bounded FIFO → 2
  +fast-fail (strong baseline) → 3 +sharding → 4 +waiting room → 5
  adaptive swap → 6 +bot classifier.
- **Replication:** 20 seeds per arm per variant (sensitivity cells: 10
  seeds, labelled reduced). Paired per-seed statistics throughout (D6);
  CI-overlap testing has no API to call.
- **R3 fidelity enumeration (acceptance):** all ten toggles ON in every
  evidentiary run — open-loop arrivals, retries, bounded capacity, atomic
  inventory, T0 concentration, wasted work, heavy-tailed service, Zipf
  demand, bot cohort, user identity.

## 2. Pre-registered success criteria (fitted variant, 20 seeds)

| rung | winners p99 | rejected p99 | goodput | retry amp | fairness F | criteria met |
|---|---|---|---|---|---|---|
| rung0 | 510.7 ms | 1721.8 ms | 335/s | 2.17 | 5.25 | 1/6 |
| rung1 | 42.8 ms | 53.1 ms | 1733/s | 1.15 | 5.25 | 2/6 |
| rung2 | 41.7 ms | 41.5 ms | 1795/s | 1.15 | 5.25 | 3/6 |
| rung3 | 39.8 ms | 39.6 ms | 1838/s | 1.15 | 5.25 | 3/6 |
| rung4 | 41.0 ms | 31.1 ms | 2079/s | 1.15 | 5.21 | 4/6 |
| rung5 | 257.9 ms | 246.3 ms | 666/s | 1.15 | 5.21 | 3/6 |
| rung6 | 234.1 ms | 275.0 ms | 650/s | 1.15 | 2.65 | 2/6 |

*(Retry amplification is 1.15 for every rung ≥ 1 because with hard
errors eliminated it is carried entirely by pre-fire polling and T0
re-fires — workload structure, mechanism-invariant by design.)*

**No arm meets the winners bar (34.2 ms)** — it sits ~4% above the
inventory-drain physics floor. **No arm meets the goodput guardrail**
(3892 seats/s; ceiling arithmetic: 200 seats over the fastest observed
drain gives ~2100/s — the guardrail constant, derived from steady-state
calibration capacity, is unreachable at this inventory size; the
classical arms, rungs 1-4, exceed naive 5-6x; the adaptive-stack arms
(rungs 5-6) reach only ~2x). Rung 4's **rejected-bar MET is
a fragile median**: 31.1 <= 34.2 ms at 20 seeds, but the paired
improvement vs rung 2 is NOT distinguishable (§3) and the bar flips in
6 of 8 sensitivity cells (§4). Under the ratified decision rule the
bar-met may be reported; the *improvement claim* may not.

## 3. Ladder — marginal deltas and verdicts (paired, both families)

(A CI including zero is labelled **not distinguishable** below; R6's
pre-registered term for this outcome is "did not help".)

| family | pair | rejected p99 delta [CI] | goodput delta [CI] |
|---|---|---|---|
| ladder | rung1vsrung0 | -1691.9ms [-3432.9,-1468.8] distinguishable | +1397.3/s [+1279.3,+1457.7] distinguishable |
| ladder | rung2vsrung1 | -10.7ms [-16.1,-7.7] distinguishable | +130.4/s [+51.4,+192.3] distinguishable |
| ladder | rung3vsrung2 | -2.0ms [-2.2,-1.8] distinguishable | +36.3/s [+32.3,+47.7] distinguishable |
| ladder | rung4vsrung3 | -3.7ms [-12.2,+12.7] **not distinguishable** | +294.3/s [+64.1,+379.6] distinguishable |
| ladder | rung5vsrung4 | +193.9ms [+138.8,+243.8] distinguishable | -1456.6/s [-1732.4,-1112.2] distinguishable |
| ladder | rung6vsrung5 | +20.5ms [+16.5,+26.2] distinguishable | -0.8/s [-7.8,+9.2] **not distinguishable** |
| baseline | rung3vsrung2 | -2.0ms [-2.2,-1.8] distinguishable | +36.3/s [+32.3,+47.7] distinguishable |
| baseline | rung4vsrung2 | -6.0ms [-14.5,+10.7] **not distinguishable** | +337.6/s [+89.5,+440.1] distinguishable |
| baseline | rung5vsrung2 | +207.3ms [+179.4,+249.8] distinguishable | -1147.0/s [-1217.4,-1104.6] distinguishable |
| baseline | rung6vsrung2 | +233.8ms [+200.4,+279.4] distinguishable | -1152.8/s [-1220.2,-1082.2] distinguishable |

## 4. Sensitivity — a win in one corner is not a win

Cells vary ONE dimension from center; 10 seeds each (reduced replication,
labelled per the no-silent-caps rule). Headline = rung 4 meets the
rejected bar AND beats rung 2.

| cell | rung2 rej p99 | rung4 rej p99 | headline holds |
|---|---|---|---|
| bots=300 | 72.9 ms | 202.5 ms | no |
| bots=75 | 26.9 ms | 35.3 ms | no |
| center | 48.3 ms | 42.8 ms | no |
| p_retry=0.3 | 3502.0 ms | 3502.0 ms | no |
| variant=cliff | 186.7 ms | 8519.1 ms | no |
| variant=plateau | 11.2 ms | 0.5 ms | **yes** |
| zipf=0.7 | 49.3 ms | 79.4 ms | no |
| zipf=1.5 | 45.5 ms | 24.7 ms | **yes** |

**The headline holds in 2 of 8 cells.** Per the spec's own
rule — *a win in one corner is not a win* — rung 4's bar-met is reported
as corner-dependent, not general. Two structural discoveries:

- **Cliff catastrophe:** under the congestion-collapse (cliff) server,
  the waiting room's own status stream strangles the drain: rung4-cliff
  resolves in ~8.5 s at 23 seats/s vs rung2-cliff's 178 ms at 850/s —
  R8's dark corner realized: on a congestion-collapsing backend the
  status endpoint IS the fatal bottleneck, and fast-fail without a room
  is the better mechanism there.
- **Retry-after-reject** (p_retry=0.3) is **horizon-censored** — both
  arms report the identical 3502.0 ms because the metric runs to the
  final definitive across the retry/backoff chain, which dominates any
  mechanism difference. The cell is *uninformative*, not a "no"; noted
  for v2 metric design.

## 5. Fairness (R7.1) — from the P8 evaluation

| family | status | TPR | F: rung 2 → rung 6 | Gate A guard |
|---|---|---|---|---|
| sniper | trained-on | 1.00 | 5.25 → 2.65 | pass (−49%) |
| burst | held-out | 1.00 | 6.67 → 3.65 | pass (−45%) |
| mimic | held-out | 0.25 | 1.51 → 1.60 | **BREACH +5.9%** |

The classifier halves the bot advantage against machine-shaped automation
— including a held-out family it never saw — and *slightly worsens*
fairness against human-mimicking automation, breaching the pre-registered
5% guard: it pays its false-positive cost without finding the bots. The
improvement claim is therefore **limited to non-mimicking automation**.
The R7.1 circularity guard forced this limit into the open.

## 6. The waiting-room hypothesis (R8) — from the P7 evaluation

The status endpoint becomes a **co-equal load stream, not a collapse**:
its p99 wait tracks (and under drain-heavy load exceeds) the booking
stream's because both queue on the same workers — tripping the
pre-registered wait-comparison clause in 20/20 drain-heavy runs — while
capacity share peaks at ~39%, under the 50% clause. Sub-second polling
creates the storm; at ≥ 1 s intervals the queue drains faster than
clients poll. Antigravity's hypothesis: **partially confirmed**.

## 7. Findings register

- **F1 — Bounded admission recovers the collapse.** Rung 1 alone: hard
  errors 47% → 0, goodput 335 → 1733 seats/s, rejected p99 1.72 s →
  53 ms. Most of the achievable gain, from the simplest mechanism — as R5
  predicted when it made "bounded + FIFO + fast-fail" the bar.
- **F2 — The waiting room is the strongest classical arm — on goodput.**
  Its +338 seats/s over the strong baseline is the ladder's largest
  distinguishable improvement above that baseline (sharding's +36/s is
  also distinguishable, an order of magnitude smaller). Its rejected-bar
  attainment is **inconclusive** (median below the bar; median CI
  [16.9, 54.0] ms spans it; paired improvement not distinguishable; 6 of
  8 sensitivity cells fail — including a catastrophic reversal under the
  cliff server, where its own status stream strangles the drain). Winners'
  p99 41 ms misses the bar, which sits ~4% above the inventory-drain
  physics floor (~33 ms; D15 finding).
- **F3 — Adaptive limiting is a negative result.** The AIMD swap (rung 5)
  performs far worse than the hand-tuned static bound it replaced
  (258 ms / 666 seats/s vs 41 ms / 2079). Stability across knee variants:
  yes. Benefit: none, at this target and controller. Reported per D2.
- **F4 — Timing classification generalizes to same-shaped automation and
  fails against mimics** (§5).
- **F5 — The drain-speed blindness.** At a ~100 ms sell-out, timing-only
  classification is structurally blind: everyone present is "early" and
  nobody has a second request yet — two-priority degenerates to FIFO and
  fairness is untouched. Classification only works where the contest
  lasts. The spec's standing note made empirical: *the race is over
  before the population differentiates.*
- **F6 — Overload's failure mode is regime-dependent.** In the fitted
  regime the naive arm fails by connection resets (47%), not timeouts —
  wasted work measures 0.0 and an error-rate metric would have seen
  everything; the calibration's zero-error finding was engine-specific.
- **F7 — The goodput guardrail (≥ 3892 seats/s) is met by no arm**,
  including naive. See §2 discussion.

## 8. The expected-result hypothesis, graded

The spec pre-stated (requirements "Expected result"):

> "Classical admission control plus a virtual waiting room recovers much
> of the lost goodput/stability; adaptive limiting provides a smaller
> additional improvement; and ML earns its place primarily through bot
> detection and fairness rather than raw throughput."

- **"Classical admission control … recovers much of the lost
  goodput/stability"** — **CONFIRMED**: rung 1 alone recovers 5× goodput
  and eliminates hard errors; the waiting room adds a distinguishable
  further goodput gain and the fastest rejected-answer latency
  measured (bar attainment inconclusive per §2).
- **"Adaptive limiting provides a smaller additional improvement"** —
  **REFUTED, in the honest direction**: it provided a large *regression*,
  not a small improvement. A negative result, reportable per D2.
- **"ML earns its place primarily through bot detection and fairness"** —
  **CONFIRMED WITH A MEASURED LIMIT**: fairness roughly halves against
  machine-shaped automation (held-out included); against human-mimicking
  automation the effect inverts slightly and breaches the guard. ML
  contributed nothing to throughput or latency, as expected.

Per the chair's original ruling (D2), this graded outcome — including
both negatives — is a **successful** experiment.

## 9. Honest framing — the mechanism-design discussion

The engineering results sharpen, rather than solve, the underlying
scarcity-allocation problem (requirements "Honest framing"):

- Every mechanism that improved latency did so by *ordering* the race,
  not by changing its nature: FIFO admission, tokens, eviction. The
  distributional outcome — who wins — remained a function of arrival
  timing at every classical rung (F ≈ 5.2 at every rung through 5 on the evaluation family — §2 table —
  and 5.2–6.7 across families, §5).
- Fairness moved only when two conditions held at once: a mechanism that
  *lengthens the contest* (paced drain) **and** automation that behaves
  unlike humans. F5 shows the first condition is structural: no
  classifier can act inside a contest shorter than the population's
  arrival spread; F4 shows the second is adversarial and will erode as
  bots converge on human behaviour.
- The round table's original escalation therefore stands as the open
  question: whether **mechanism design** — pre-registration windows,
  lotteries over a qualification window, deliberately paced drains —
  produces durable fairness is an **untested hypothesis**: none of those
  mechanisms were simulated in v1, and nothing here demonstrates they
  work. What v1 *does* license: engineering alone converted a latency
  contest into an orderly latency contest, not into a fair allocation —
  and any fairness intervention needs the contest to last longer than
  the population's arrival spread (F5). They are the first v2
  candidates for exactly that reason.

## 10. Limitations

- The server model is conservative on tail magnitude (~0.6–0.7× measured
  at high C; chair-accepted deviations, D13). The knee variants bracket
  the shape uncertainty and show the headline is **variant-dependent**
  (§4): plateau clean, fitted inconclusive, cliff a catastrophic
  reversal. (An earlier draft claimed the headline "survives all three"
  — corrected at the results review; the drafting lesson is recorded in
  the review thread.)
- One machine, one calibrated engine lineage (Postgres semantics; the
  SQLite run is withdrawn provenance). Absolute numbers are
  laptop-specific; directions and orderings are the transferable claims.
- Push delivery (rung 4+) is modelled cost-free at the notification edge;
  status polling is fully costed, pushes are not.
- The classifier is deliberately equal-effort (two features, grid-tuned);
  a stronger learner might move the mimic result — but F5's structural
  blindness at fast drains is feature-independent.
- Goodput ceilings interact with inventory size (200 seats) and drain
  arithmetic; see §2's guardrail discussion.
- Sensitivity sweep is one-at-a-time (10 seeds/cell, labelled), not a
  full factorial.
- ~20 paired comparisons are reported with no multiplicity correction;
  isolated marginal results should be read cautiously.
- Asymmetric costing: status polling is fully costed on the shared
  worker pool, push delivery is modelled cost-free — whether rung 4
  retains any distinguishable advantage under realistically costed push
  is an open v2 question (raised by the Antigravity seat).

## 11. Verdict

v1 answers its framing question — *which mechanisms actually improve
behaviour during a realistic scarcity spike, and by how much* — with
pre-registered criteria, paired statistics, and honest negatives — with
no bar claimably met, and the near-misses honestly bounded. The experiment is concluded; v2 candidates (real distributed
load, two-phase inventory, adversarial co-evolution, mechanism-design
simulations) are listed in requirements "Explicitly deferred to v2".
