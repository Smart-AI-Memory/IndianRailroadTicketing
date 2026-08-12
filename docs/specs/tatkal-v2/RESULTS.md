# tatkal-v2 — RESULTS (graded record)

**Status:** graded 2026-08-12 under the ratified protocol — D17 bars
and guards, D13 population, D14 windows, Holm within family (D17.3)
over the 22 inventoried comparisons, paired per-seed bootstrap CIs
(B = 10,000, seeded), 20 seeds everywhere. Chair rulings applied: D18.
Data: `reports/v5-baselines-data.json`, `reports/v6-sweeps-data.json`,
`reports/v7-grading.json` (grader: `tools/v7_grading.py`).

Framing question (requirements): *do mechanism-design interventions
produce durable fairness where engineering alone did not — and does
the waiting room survive realistically costed push?*

**Answer: yes, and no, respectively** — with one honest negative (M3)
and the caveats below.

---

## 1. Headline: allocation mechanisms deliver fairness; engineering did not

D7 comparisons, fitted variant, paired per-seed deltas of
controller-level bot advantage (mechanism) minus F-ratio (baseline);
negative = fairer than engineering. Every allocation-arm comparison is
Holm-distinguishable:

| cell | vs rung 2 | vs rung 4 |
|---|---|---|
| M1 r_reg=0.5 | −2.91 [−3.28, −2.66] | −2.91 [−3.26, −2.66] |
| M1 r_reg=0.8 | −2.93 [−3.28, −2.71] | −2.96 [−3.23, −2.71] |
| M1 r_reg=0.95 | −2.89 [−3.38, −2.28] | −2.89 [−3.34, −2.33] |
| M2 p=0 | −2.96 [−3.17, −2.77] | −2.92 [−3.17, −2.81] |
| M2 p=0.1 | −2.49 [−2.67, −2.34] | −2.48 [−2.71, −2.30] |
| M2 p=0.2 | −2.22 [−2.42, −1.91] | −2.22 [−2.37, −1.87] |
| M2 p=0.4 | −1.93 [−2.15, −1.74] | −1.96 [−2.10, −1.78] |
| **M3** | **+1.40 [+1.00, +1.87]** | **+1.36 [+1.00, +1.87]** |

Under the engineering baselines bots hold a ~3.9× advantage (the
latency contest); under M1 and M2 at zero abuse they hold ~1.0× —
parity. Even at the heaviest abuse cell (p = 0.4) M2 remains ~1.9
fairer than engineering. M3 is the reverse: see §4.

## 2. P1 and the abuse curve (M2)

- **P1 confirmed (D18.1):** at p = 0, mimic advantage 0.964 and race
  1.090, both with excess-over-1 CIs including zero; the draw is
  uniform over active identities by construction and no leak exists.
  Pooling erases timing and cadence — mimic bots and honest humans are
  one class under M2, as predicted before any run.
- **Abuse pays ≈ m at low prevalence and self-dilutes at scale:**
  identity-split controller advantage 4.46 (p = 0.1) → 4.07 (0.2) →
  3.46 (0.4), every cell under the ≤ m = 5 guard (GB2b). An
  unmitigated lottery pays an abuser almost proportionally to
  identities held when abusers are rare; abusers crowd each other out
  as prevalence grows. Fairness *for honest users* still degrades
  monotonically with p (§1 table) — self-dilution is not mitigation.

## 3. The waiting room does not survive costing (R3′)

Rejected-resolution p99, paired vs rung 2 (fitted):

| c_push (× status check) | median delta | verdict (Holm) |
|---|---|---|
| 0 (v1's free-push model) | −8.3 ms [−10.5, +4.0] | **did not help** (CI includes 0) |
| 0.25 | +15.6 ms [+3.1, +40.5] | worse, distinguishable |
| 0.5 | +17.6 ms [+8.7, +54.9] | worse, distinguishable |
| 1.0 | +55.4 ms [+31.0, +208.2] | worse, distinguishable |
| 2.0 | +251.8 ms [+78.9, +480.0] | worse, distinguishable |

The Antigravity seat's question has its answer: **the break-even is at
or below one quarter of a status check per push** — and under the v2
population even free push is not distinguishable from plain fast-fail
on the primary metric. The v1 rung-4 story survives only in the
regime v1 modelled: pushes costing exactly nothing. R3′'s fairness
guards all pass (no F regression at any cost).

## 4. M3 — honest negative, both barrels

- **Fairness guard BREACHED:** whole-run F exceeds 1.05× rung 2 by
  +1.21 median. Pacing concentrates the entire bot advantage into the
  early tranches (per-tranche F: 2.77 in tranche 0 → 0.00 in tranche
  3) and the whole-run aggregate is *worse* than engineering. Camping
  works: re-arriving within 50 ms of each open, camp bots feast on
  every fresh tranche.
- **Inventory starves (report-only per D17.6):** 125/200 median seats
  sold. With p_retry = 0, users rejected in tranche i take the
  definitive and leave; late tranches open onto a drained population
  plus campers. The whole-run drain bar is **not evaluable** —
  sell-out never occurs.
- Stands per D2 conventions exactly as v1's adaptive-limiting negative
  did: reported, not rescued.

## 5. Bars (D17.1, c_push = 0 cells; D18.2 applied)

- **Loser clocks: pass by construction.** Post-event resolution for
  losers is 0 at free push (instant burst); absolute TTDA equals each
  user's deliberate wait (M2 p99 6.39 s — the Q wait plus pre-fire
  polling lead; M1 p99 19.8 s — dominated by pre-fire polling from up
  to 20 s before T0).
- **Combined post-event p99: MISS as registered (D18.2).** The
  registered 3×-burst floor is degenerate at c = 0 (winner-redemption
  drain was omitted from the floor derivation): measured combined p99
  is winner-dominated — M1 ≈ 0.91 s (200 bookings through the bounded
  rung-2 chain), M2 ≈ 0.05 s. Miss recorded, never adjusted; floor
  definition amended prospectively to max(burst, winner-drain).
- **M1 sells 200/200 at every uptake cell**; M2 sells 200 with a
  ghost_sales race of ~1 (patience expiring between draw and
  confirmation — report-only, D17.6; the two-phase-inventory deferral
  is exactly what would fix it).

## 6. Expected result, graded

> *Mechanisms that lengthen the contest enable fairness measures to
> bind* — **confirmed**, and stronger: they don't just enable
> measurement, they deliver parity outright (M1/M2 at p = 0).
> *The pre-registration window shifts the contest to the registration
> surface* — **not observed**: the registration surface absorbed
> ~2,000 one-shots over 5 minutes trivially, and camping it bought
> nothing (lottery allocation is timing-blind; the leak diagnostic
> held). The predicted new contest did not materialize at this scale.
> *The lottery's fairness gain is confiscated by multi-identity
> abuse* — **partially**: abuse pays ≈ m per abuser at low prevalence
> (honest-user fairness degrades with p) but stays under the
> no-super-linear guard and self-dilutes at scale.
> *The waiting room's advantage shrinks monotonically with push cost
> with a break-even in the plausible range* — **confirmed at the
> strongest reading**: break-even ≤ 0.25× a status check, and the
> zero-cost advantage itself is not distinguishable under the v2
> population.
> *(Unhypothesized)* M3 worsens whole-run fairness and starves
> inventory — an honest negative.

## 7. Limitations

- One machine, one calibrated engine lineage; absolute numbers are
  laptop-specific; directions and orderings are the transferable
  claims (v1 limitation carries).
- Fitted-variant tables shown here; plateau/cliff tables ship in the
  archives, and v1's cliff catastrophe reproduces under the v2
  population (rung4-cliff ≈ rung0-cliff ≈ 23 seats/s) — every rung-4
  claim above is variant-dependent in exactly v1's way.
- M1/M2 cells ran at c_push = 0 only; the costed-burst cells the D14.2
  shared grid contemplates for M1/M2 were not part of the V6 cell list
  (tasks.md V6.1/V6.2 as approved). The R3′ sweep carries the costing
  conclusion; extending it to allocation-arm bursts is v3 work.
- The registration surface's triviality (§6) is scale-dependent: 2,530
  humans over W = 300 s. A population × window regime where
  registration itself spikes was not probed.
- Grading uses bootstrap p-values from the registered seeded bootstrap
  for the Holm step; the CI machinery is otherwise v1's unchanged.

## 8. Verdict

v2 answers its framing question with pre-registered criteria, paired
statistics, honest negatives, and one recorded process miss:

**Allocation mechanisms — not engineering — produce fairness.** A
lottery over a qualification window delivers bot parity at zero abuse
and stays multiplicatively fairer than engineering even under heavy
identity abuse; a pre-registration window does the same at every
uptake level while selling every seat. Deliberately paced drains do
the opposite of their intent. And the strongest engineering result of
v1 — the virtual waiting room — does not survive the costing of its
own notification channel: its advantage is indistinguishable at free
push and significantly negative at a quarter of a status check per
push.

The experiment is concluded pending chair sign-off; v3 candidates:
costed M1/M2 notification bursts (the un-run grid), identity
mitigation mechanisms for M2 (the D2-deferred infra), retry-model
sensitivity for M3, and the standing v1 deferrals.
