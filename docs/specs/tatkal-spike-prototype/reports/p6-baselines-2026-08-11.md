# tatkal-sim run report

Seeds: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

## Arms

- **rung0** — knee variant: `fitted`; enabled toggles: open_loop_arrivals, retries_enabled, bounded_capacity, atomic_inventory, t0_concentration, wasted_work, heavy_tail_service, zipf_demand, bot_cohort, user_identity
- **rung1** — knee variant: `fitted`; enabled toggles: open_loop_arrivals, retries_enabled, bounded_capacity, atomic_inventory, t0_concentration, wasted_work, heavy_tail_service, zipf_demand, bot_cohort, user_identity
- **rung2** — knee variant: `fitted`; enabled toggles: open_loop_arrivals, retries_enabled, bounded_capacity, atomic_inventory, t0_concentration, wasted_work, heavy_tail_service, zipf_demand, bot_cohort, user_identity

## Per-arm metrics (median across seeds)

| arm | resolution.winners.p99 | resolution.rejected.p99 | ttda.winners.p99 | goodput.sold_per_s | wasted_work_ratio | settling_time_s | fairness.bots_win_share |
|---|---|---|---|---|---|---|---|
| rung0 | 0.5107 | 1.722 | 18.83 | 334.5 | 0 | 3.5 | 0.2875 |
| rung1 | 0.04275 | 0.05314 | 18.83 | 1733 | 0 | 2 | 0.2875 |
| rung2 | 0.04168 | 0.0415 | 18.83 | 1795 | 0 | n/a | 0.2875 |

## Ladder family — rung vs predecessor (R4 marginal deltas)

| candidate | baseline | metric | median delta | 95% CI | verdict |
|---|---|---|---|---|---|
| rung1 | rung0 | resolution.winners.p99 | -0.4653 | [-0.4987, -0.4075] | distinguishable |
| rung1 | rung0 | resolution.rejected.p99 | -1.692 | [-3.433, -1.469] | distinguishable |
| rung1 | rung0 | ttda.winners.p99 | -0.0008384 | [-0.001463, -0.0006018] | distinguishable |
| rung1 | rung0 | goodput.sold_per_s | 1397 | [1279, 1458] | distinguishable |
| rung2 | rung1 | resolution.winners.p99 | -9.021e-05 | [-0.0009634, 0] | did not help (CI includes zero) |
| rung2 | rung1 | resolution.rejected.p99 | -0.01071 | [-0.01615, -0.00771] | distinguishable |
| rung2 | rung1 | ttda.winners.p99 | 0 | [0, 0] | did not help (CI includes zero) |
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

## Success-bar evaluation (D15 operand: resolution latency)

| arm | winners p99 (bar 34.2 ms) | rejected p99 (bar 34.2 ms) |
|---|---|---|
| rung0 | 510.7 ms miss | 1721.8 ms miss |
| rung1 | 42.8 ms miss | 53.1 ms miss |
| rung2 | 41.7 ms miss | 41.5 ms miss |

> The former winners' p99 TTDA saturation (18.8 s across all arms,
> pre-fire lead time) was resolved by chair ruling D15: the bars bind
> resolution latency = definitive − max(first request, T0); TTDA
> remains reported (pre-firing is not free). The 34.2 ms winners bar
> sits ~4% above the inventory-drain physics floor (~33 ms) — a
> recorded finding for the write-up.
