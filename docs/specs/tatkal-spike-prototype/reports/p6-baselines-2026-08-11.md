# tatkal-sim run report

Seeds: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

## Arms

- **rung0** — knee variant: `fitted`; enabled toggles: open_loop_arrivals, retries_enabled, bounded_capacity, atomic_inventory, t0_concentration, wasted_work, heavy_tail_service, zipf_demand, bot_cohort, user_identity
- **rung1** — knee variant: `fitted`; enabled toggles: open_loop_arrivals, retries_enabled, bounded_capacity, atomic_inventory, t0_concentration, wasted_work, heavy_tail_service, zipf_demand, bot_cohort, user_identity
- **rung2** — knee variant: `fitted`; enabled toggles: open_loop_arrivals, retries_enabled, bounded_capacity, atomic_inventory, t0_concentration, wasted_work, heavy_tail_service, zipf_demand, bot_cohort, user_identity

## Per-arm metrics (median across seeds)

| arm | ttda.winners.p99 | ttda.rejected.p99 | goodput.sold_per_s | wasted_work_ratio | settling_time_s | fairness.bots_win_share |
|---|---|---|---|---|---|---|
| rung0 | 18.83 | 1.722 | 334.5 | 0 | 3.5 | 0.2875 |
| rung1 | 18.83 | 0.05314 | 1733 | 0 | 2 | 0.2875 |
| rung2 | 18.83 | 0.0415 | 1795 | 0 | n/a | 0.2875 |

## Ladder family — rung vs predecessor (R4 marginal deltas)

| candidate | baseline | metric | median delta | 95% CI | verdict |
|---|---|---|---|---|---|
| rung1 | rung0 | ttda.winners.p99 | -0.0008384 | [-0.001463, -0.0006018] | distinguishable |
| rung1 | rung0 | ttda.rejected.p99 | -1.692 | [-3.433, -1.469] | distinguishable |
| rung1 | rung0 | goodput.sold_per_s | 1397 | [1279, 1458] | distinguishable |
| rung2 | rung1 | ttda.winners.p99 | 0 | [0, 0] | did not help (CI includes zero) |
| rung2 | rung1 | ttda.rejected.p99 | -0.01071 | [-0.01615, -0.00771] | distinguishable |
| rung2 | rung1 | goodput.sold_per_s | 130.4 | [51.4, 192.3] | distinguishable |

## Baseline family — arm vs strong baseline (R5)

(none in this run)

## Gate A profile — unthresholded metrics on the naive arm

The chair sets thresholds (or report-only status) for these before any R4 arm run; this profile is the informing input (D10).

| metric | median | min | max |
|---|---|---|---|
| wasted_work_ratio | 0 | 0 | 0 |
| settling_time_s | 3.5 | 2.5 | 10.5 |
| fairness.bots_win_share | 0.2875 | 0.235 | 0.325 |

## Sensitivity

(stub — populated by the P9 sweep: knee variants x Zipf s x retry policy x bot share. A win in one corner is not a win.)

## D14 fairness statistic (F = win-share / population-share)

- **rung0**: F median 5.25 (range 4.29-5.94)
- **rung1**: F median 5.25 (range 4.29-5.94)
- **rung2**: F median 5.25 (range 4.29-5.94)

## Flagged: pre-registration collision on winners' p99 TTDA

Winners' p99 TTDA is **18.83 s for every arm, identically** — saturated by
the pre-fire cohort, whose TTDA clock starts at their first pre-T0 poll
(~20 s before T0, "pre-firing is not free", by ratified design). With ~30
pre-fire users among ~200 winners, the winners' p99 sits in the pre-fire
range for any arm, so the ratified success bar (p99 TTDA <= 34.2 ms for
winners) is **structurally unmeetable** under the current TTDA definition
regardless of mechanism. Logged as an open question for the chair
(decisions.md); NOT adjusted here — changing either the definition or the
bar is a pre-registration decision.
