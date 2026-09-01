# tatkal-v3 — RESULTS (graded record)

**Status:** graded 2026-09-01 under the ratified protocol — D24 bars
and guards over D23 tail-inclusive floors (D25), Holm within family
over the 39 inventoried comparisons, paired per-seed bootstrap
(B = 10,000, seeded), 20 seeds everywhere, v2 record cells reused per
the center-cell rule (D3/R6). Data:
`reports/w5-sweeps-data.json` (63 cells × 20 seeds, 1,260 runs);
grader: `tools/w6_grading.py` → `reports/w6-grading.json`.

Framing question (requirements): *which currency of identity-pricing
— work, money, or enrollment — reclaims lottery parity under abuse,
at what honest cost, without moving the bottleneck into its own
infrastructure? Do costed bursts change the allocation story? Does
re-entry rescue paced drain?*

**Answer: at plausible price points, none of the three currencies
reclaims parity honestly — and the strongest positive result belongs
to none of them.** Work-pricing is starved by the spike it shares a
pool with and "improves" fairness only by excluding honest users;
money-pricing does nothing until the stake reaches ~15× ticket value
(exactly as pre-registered in D20), where it delivers parity cleanly;
enrollment-pricing makes fairness *worse*, Holm-distinguishably. The
reversal: **M3 paced drain, written off in v2, recovers both
inventory and fairness once rejected demand re-enters** — v2's double
negative was a property of `p_retry = 0`, not of pacing.

---

## 1. Fairness-reclaim families (advantage under mitigation − unmitigated record, same p)

Negative = fairer than unmitigated. Fitted variant, controller-level
identity-split advantage (D5 metric); record ≈ 4.07 at p = 0.2.

| cell | p=0.1 | p=0.2 | p=0.4 | Holm |
|---|---|---|---|---|
| A1 c_verify=0.25 | +0.00 | +0.00 | −0.04 | none distinguishable |
| A1 c_verify=1 | −0.18 | −0.58 | −0.96 | p=0.4 only |
| A1 c_verify=4 | **−1.49** | **−1.66** | **−2.16** | all three |
| A2 d ∈ {0.1, 0.5, 2} | ±0.000 exactly | ±0.000 | ±0.000 | none (bit-identical runs) |
| A2 d=15 | **−0.28** | **−0.75** | **−1.09** | all three |
| A3 deadline | **+0.54** | **+0.66** | **+0.47** | all three — **worse** |

- **A2 at d ≤ 2 is the D20 pre-registration confirmed to the bit:**
  k* = m, every abuser stakes everything, the draw is unchanged, the
  deltas are exactly zero. Forfeiture-only deposits cannot deter at
  low win probability — now measured, not just computed.
- **A2 at d = 15** (the D20 bracket point): abusers drop to one
  identity (median stakes 2,806.5 → 2,686.5 = 30 abusers × 4
  declined), advantage 4.07 → **0.91** — parity, at zero honest
  latency cost (B2 ratio 1.00). The mechanism works; the price is a
  stake of ~15× ticket value (see Honest framing).
- **A1's apparent gains are exclusion, not pricing** (§3).
- **A3 is an honest negative with a clean mechanism:** the
  eligibility filter removed ~500 unregistered honest users (20% at
  r_reg = 0.8) and ~105 opportunistic bot identities, while the
  patient abuser had registered all m identities — so the abuser's
  *pool share rose*. Enrollment-pricing transfers seats from
  forgetful humans to patient abusers.

## 2. The reversal: M3 under re-entry (B5)

| p_retry | 0 (v2 record) | 0.25 | 0.5 | 1.0 |
|---|---|---|---|---|
| seats sold (median) | 125 | 143 | 159 | **188** |

All three deltas Holm-distinguishable. At p_retry = 1.0:
improvement +50.4% with the paired CI excluding zero, and the
whole-run F-ratio guard **passes** (median excess vs 1.05× rung-2:
−0.73) — re-entering rejected humans re-fill late tranches and
dilute the camp bots that feasted in v2. **The registered recovery
claim is GRANTED** (D24 item 6 rule). v2's "pacing concentrates the
bot advantage and starves inventory" was a property of a population
that never came back — with any realistic retry behaviour, paced
drain recovers most inventory (188/200) *and* its fairness. This is
v3's strongest positive result, and it belongs to a mechanism no
identity-pricing arm touched.

## 3. A1: the bottleneck moves at every price (B3: 0/12)

Registered bar: last verification completion ≤ 3× the (tail-
inclusive) aggregate drain floor. Measured: **median last completion
4.5–4.7 s at every c_verify** — floors are 0.05 s (c_verify = 0.25)
to 0.76 s (c_verify = 4). **Missed in all 12 cells, by 6× to 90×.**
The verification queue shares the worker pool with the T0 booking
and polling storm, so *its own cost barely matters*: even quarter-
cost verification completes only just before the Q = 5 s draw.
The D9 question is answered in the strongest form — the bottleneck
moves at every point on the grid, not just at saturation.

At c_verify = 4 the pool saturates outright and the degradation mode
is the registered clean one (`verify-missed`, zero lost intents) —
but who gets excluded is the finding: **median 1,539.5 of 2,500
honest users (62%) priced out by congestion, vs ~43% of bot
identities** (mimic-shaped bots arrive tighter and verify earlier).
The measured fairness "gain" at c_verify = 4 (§1) is abuser ticket
attrition inside a lottery of exclusion that hits honest users
hardest. **B2 passed everywhere (36/36) — including the
pre-registered expected breach at c_verify = 4, which did not
occur** — because exclusion resolves *fast*: the harm never appears
on a latency clock. A guard that watches only latency is blind to
harm exported into a different currency; the honest-cost readout's
`verify_missed` column is what caught it.

## 4. Costed bursts close the v2 gap (R3 family)

Post-event resolution p99 delta vs each arm's c_push = 0 record:

| c_push | 0.25 | 0.5 | 1.0 | 2.0 |
|---|---|---|---|---|
| M1 | +0.00 | +0.00 | +0.00 | +0.14 |
| M2 | +0.23 | +0.30 | **+0.70** | **+1.43** |

M1 is winner-drain-dominated and essentially burst-cost-immune; M2's
2,540-loser burst degrades linearly with c_push (5 of 8 comparisons
Holm-distinguishable). Costed notification *changes the loser
experience, not the allocation*: fairness at every burst point is
carried unchanged (the draw precedes delivery by construction). The
v2 coverage gap is closed with a quantified answer.

## 5. Bars and guards — the record

- **B1:** 29/36. All 27 p > 0 cells pass the ≤ m guard. **All 7
  graded p = 0 cells nominally breach the ≤ 1.05 guard (medians
  1.09–1.12) — including cells bit-identical to the v2 record**, and
  v2's P1 (CI-based) found the same medians consistent with parity.
  Reported as registered and read for what it is: the hard-median
  guard is mis-calibrated for a ratio with ~180 controllers of
  sampling noise — a guard-registration miss, recorded (D26), not
  adjusted, and not a fairness regression (the unmitigated record
  itself fails it).
- **B2:** 36/36 pass — including the c_verify = 4 pre-registered
  expected breach that did not occur (§3 explains why passing is
  the *alarming* outcome there).
- **B3:** 0/12 — missed as registered; §3 is the analysis.
- **B4:** 0/8 — missed as registered: measured post-event p99
  (0.26–0.57 s) sits far above 3× the best-case arithmetic floors
  (14–47 ms) because winner redemption travels the congested
  rung-2 chain. The v2 record's own cells sit equally far above;
  the floor-to-congestion gap is structural (the same gap D18.2
  first exposed), and the *deltas* (§4) are the informative
  quantities.
- **B5:** recovery claim granted (§2).
- **B6:** 4/4 pass — the DC4 deadline spike is absorbed by the
  registration surface (worst final-decile wait well under 3× the
  17.2 ms floor), and the deadline-vs-uniform fairness delta is
  exactly zero at every p: the draw is timing-blind, as designed.

## 6. Expected result, graded

> *All three arms reclaim most of the parity lost to abuse…* —
> **REFUTED, in the honest direction.** At plausible prices: A1
> reclaims only via honest-user exclusion, A2 reclaims nothing
> below d = 15, A3 anti-reclaims.
> *Registration-bound cheapest for honest users but weakest against
> patient abusers* — **REFUTED, stronger than predicted:** not
> weakest — actively counterproductive (+0.5–0.7, Holm).
> *Deposit strongest against abuse economics but worst regressive
> profile* — **CONFIRMED at the bracket point** (parity at d = 15,
> zero honest latency cost); the regressive profile is unmodelled
> by design and reported as such, not as harmlessness.
> *Verification-cost effective only until c_verify moves the
> bottleneck* — **REFUTED: the bottleneck moves at every
> c_verify** (B3 0/12); "effectiveness" at high cost is exclusion.
> *Costed bursts degrade loser clocks without touching allocation
> fairness* — **CONFIRMED and quantified** (§4).
> *M3 recovers inventory partially while its fairness breach
> persists* — **half-REFUTED in the positive direction:** inventory
> recovers (+50%) AND the fairness breach dissolves (§2).

Per D1's honest framing, this graded outcome — one confirmation,
three refutations, one reversal — is a **successful** experiment.

## 7. Honest framing — who each mitigation prices out

- **A1 (work):** at deterrent strength, 62% of honest users are
  excluded by congestion roulette — more than the bots it targets.
  The poorly-connected and late-arriving pay most; the harm is
  invisible to latency guards.
- **A2 (money):** the only clean reclaim requires staking ~15× the
  ticket's value per entry. Honest users are modelled as
  deposit-insensitive, so the measured "zero honest cost" is an
  **unmodelled-harm axis, not evidence of harmlessness**: a 15×
  capital barrier is exclusion of the poor by construction, exactly
  the regressive profile the requirements warned about.
- **A3 (enrollment):** prices out the unenrolled — 20% of honest
  users at the registered uptake — and hands their pool share
  disproportionately to patient abusers. The deadline-spike surface
  itself is benign (B6); the harm is in eligibility, not load.
- **M3 + re-entry:** the one intervention that improved outcomes
  without pricing anyone out — its cost is time (retry churn), the
  most evenly distributed currency measured here.

## 8. Limitations

- One machine; fitted-variant numbers are scoped to Postgres-like
  engines (D15 falsification stands); plateau/cliff bracketing cells
  ran at arm centers only and are report-only in the archive.
- B2's comparator is the record cell's overall TTDA p99 (no
  per-cohort split exists in the v2 archive) — conservative against
  v3; a pass is a real pass.
- B6 graded the worst final-decile wait against the p99 bar
  (max ≥ p99: conservative; all cells passed under it).
- Honest deposit-insensitivity (A2) and fixed bot repertoires (D3)
  are modelling choices; adversarial adaptation to any of these
  mechanisms is unmeasured (deferred, D2).
- The B1 p = 0 guard and the B3/B4 floor-to-congestion gaps are
  registration misses recorded in D26 — grading constants for v4 to
  set floor-aware *and* congestion-aware.
- The W5 sweep executed between two Gate B registrations; runs are
  seed-deterministic and bar-independent, so the archive equals a
  post-ratification rerun (D25 note).

## 9. Verdict

v3 answers its framing question with pre-registered criteria, paired
statistics, honest negatives, and one reversal:

**Identity-pricing does not honestly reclaim the lottery at
plausible price points.** Work-pricing collapses into exclusion on
the shared pool it was told to use; money-pricing is inert until the
stake dwarfs the prize, then works perfectly and regressively;
enrollment-pricing is a gift to the patient abuser. The durable
fairness mechanism in the v3 record is the one v2 rejected —
**paced release with tolerant re-entry** — which restored both
inventory and fairness by giving rejected humans a way back in
rather than pricing anyone out. The scarcity-allocation discussion
(v1 standing note) sharpens once more: mechanisms that *add chances*
outperformed every mechanism that *charges for chances*, on every
axis this experiment measures.

The experiment is concluded pending chair sign-off; v4 candidates in
`v4-starter.md`.
