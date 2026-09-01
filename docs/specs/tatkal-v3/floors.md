# tatkal-v3 — floor document (W3.2), multiplicity inventory (W3.3), coverage table (W3.4)

**Status:** computed 2026-09-01 from model constants (arithmetic,
not empirical); the Gate B packet. Every bar registered at Gate B
states its distance from the relevant floor, per metric (D17.3).

Population: v2 D13 carried verbatim (D3); seats = 200 (8 pools x 25).

All mean-app-time terms are TAIL-INCLUSIVE (D23): every server
work item — heavy or light — samples the R3.7 heavy-tail mixture,
so floors use the same service law the simulator runs.

Floors are identical across fitted/plateau/cliff BY CONSTRUCTION:
the variants share all below-knee service parameters and differ
only above the knee — congestion, which floors exclude (D23).

## Drain-component enumeration (D4 rule 2)

- **A1 verification drain** includes: one light work item per
  entering identity at `c_verify x mean app time`, served by the
  shared worker pool. Excluded: entry-poll traffic (charged to the
  booking path's own floors), retry-on-saturation re-submissions
  (congestion, not physics — floors are best-case). Draw-pool
  identity counts EXCLUDE the background overlap (~<=60 arrivals in
  [T0+2, T0+Q]): including them would raise floors by < 2.3%, and
  floors must under- not over-state physics.
- **M1/M2 post-event floors (amended rule, D1/D18.2)**:
  max(loser-burst drain, winner-redemption drain). Components:
  burst = losers x c_push x status_cost x mean_app / workers;
  winner drain = 200 bookings at the inventory drain rate.
  Excluded: stake-ledger bookkeeping (A2) — pure accounting, no
  server work by design (D5: utility parameter, not payment flow).
- **M3 floors**: per-tranche allotment drain + whole-run
  H + last-tranche drain (v2 carry). p_retry adds OFFERED LOAD,
  not floor components: re-entered demand contends for the same
  seats at the same drain rate, so floors are p_retry-invariant;
  what re-entry changes is measured, not floored.
- **A3 registration-surface drain**: one registration one-shot per
  registrant at status cost (v2 M1 carry); under DC4 ~60% of it
  concentrates near the window close. Floor stated for the final
  decile of W. Excluded: camp-bot registrations (first 5% of W,
  disjoint in time).
- **A2**: no infrastructure floors — the deposit is a utility
  parameter (D5); its price shows up in the honest-cost readout
  (stake exposure), not in any latency floor.

## Variant: fitted

- mean app time (best case): 0.1419 ms; workers: 2
- winner-redemption drain (200 seats): 14.195 ms

### A1 — verification aggregate-drain floor (per c_verify x p)

Grades TOTAL verification drain and the last entry's completion
ONLY. Per-identity wait-distribution bars (p50/p99) take the
work-conservation lower bound of 0 under spread arrivals — a
distribution bar at Gate B binds against the measured
distribution with THIS aggregate floor as context, never as a
per-identity floor (D17.3).

| c_verify \\ p | 0.0 | 0.1 | 0.2 | 0.4 |
|---|---|---|---|---|
| 0.25 | 47.6 ms | 48.6 ms | 49.7 ms | 51.8 ms |
| 1.0 | 190.2 ms | 194.5 ms | 198.7 ms | 207.2 ms |
| 4.0 | 760.8 ms | 777.9 ms | 794.9 ms | 829.0 ms |

### M1/M2 post-event floors per c_push (amended: max(burst, winner drain))

| arm (losers) | 0.25 | 0.5 | 1.0 | 2.0 |
|---|---|---|---|---|
| M1 (1824) | 14.195 ms | 14.195 ms | 25.891 ms | 51.782 ms |
| M2 p=0.1 (2540) | 14.195 ms | 18.027 ms | 36.054 ms | 72.109 ms |

### M3 (all p_retry points — floors are p_retry-invariant, see enumeration)

| metric | floor |
|---|---|
| per-tranche drain | 3.974 ms, 3.407 ms, 3.407 ms, 3.407 ms |
| whole-run | 8.003 s (H + last-tranche drain) |

### A3 registration surface (DC4 deadline profile)

| final-decile registration drain | 17.232 ms | ~60% of registrants x status cost / workers |

## Variant: plateau

- mean app time (best case): 0.1419 ms; workers: 2
- winner-redemption drain (200 seats): 14.195 ms

### A1 — verification aggregate-drain floor (per c_verify x p)

Grades TOTAL verification drain and the last entry's completion
ONLY. Per-identity wait-distribution bars (p50/p99) take the
work-conservation lower bound of 0 under spread arrivals — a
distribution bar at Gate B binds against the measured
distribution with THIS aggregate floor as context, never as a
per-identity floor (D17.3).

| c_verify \\ p | 0.0 | 0.1 | 0.2 | 0.4 |
|---|---|---|---|---|
| 0.25 | 47.6 ms | 48.6 ms | 49.7 ms | 51.8 ms |
| 1.0 | 190.2 ms | 194.5 ms | 198.7 ms | 207.2 ms |
| 4.0 | 760.8 ms | 777.9 ms | 794.9 ms | 829.0 ms |

### M1/M2 post-event floors per c_push (amended: max(burst, winner drain))

| arm (losers) | 0.25 | 0.5 | 1.0 | 2.0 |
|---|---|---|---|---|
| M1 (1824) | 14.195 ms | 14.195 ms | 25.891 ms | 51.782 ms |
| M2 p=0.1 (2540) | 14.195 ms | 18.027 ms | 36.054 ms | 72.109 ms |

### M3 (all p_retry points — floors are p_retry-invariant, see enumeration)

| metric | floor |
|---|---|
| per-tranche drain | 3.974 ms, 3.407 ms, 3.407 ms, 3.407 ms |
| whole-run | 8.003 s (H + last-tranche drain) |

### A3 registration surface (DC4 deadline profile)

| final-decile registration drain | 17.232 ms | ~60% of registrants x status cost / workers |

## Variant: cliff

- mean app time (best case): 0.1419 ms; workers: 2
- winner-redemption drain (200 seats): 14.195 ms

### A1 — verification aggregate-drain floor (per c_verify x p)

Grades TOTAL verification drain and the last entry's completion
ONLY. Per-identity wait-distribution bars (p50/p99) take the
work-conservation lower bound of 0 under spread arrivals — a
distribution bar at Gate B binds against the measured
distribution with THIS aggregate floor as context, never as a
per-identity floor (D17.3).

| c_verify \\ p | 0.0 | 0.1 | 0.2 | 0.4 |
|---|---|---|---|---|
| 0.25 | 47.6 ms | 48.6 ms | 49.7 ms | 51.8 ms |
| 1.0 | 190.2 ms | 194.5 ms | 198.7 ms | 207.2 ms |
| 4.0 | 760.8 ms | 777.9 ms | 794.9 ms | 829.0 ms |

### M1/M2 post-event floors per c_push (amended: max(burst, winner drain))

| arm (losers) | 0.25 | 0.5 | 1.0 | 2.0 |
|---|---|---|---|---|
| M1 (1824) | 14.195 ms | 14.195 ms | 25.891 ms | 51.782 ms |
| M2 p=0.1 (2540) | 14.195 ms | 18.027 ms | 36.054 ms | 72.109 ms |

### M3 (all p_retry points — floors are p_retry-invariant, see enumeration)

| metric | floor |
|---|---|
| per-tranche drain | 3.974 ms, 3.407 ms, 3.407 ms, 3.407 ms |
| whole-run | 8.003 s (H + last-tranche drain) |

### A3 registration surface (DC4 deadline profile)

| final-decile registration drain | 17.232 ms | ~60% of registrants x status cost / workers |

## Multiplicity inventory (W3.3)

Planned paired comparisons, primary metric per family, fitted
variant. Gate B registers the count and the correction policy
(proposed: Holm within family, v2 precedent) over exactly this list:

| family | comparisons | against |
|---|---|---|
| A1 fairness reclaim | 9 (3 c_verify x 3 p > 0) | unmitigated M2, same p (v2 record) |
| A2 fairness reclaim | 12 (4 d x 3 p > 0) | unmitigated M2, same p (v2 record) |
| A3 fairness reclaim | 3 (deadline profile x 3 p > 0) | unmitigated M2, same p (v2 record) |
| A3 deadline-vs-uniform delta (R5.1) | 4 (per p) | A3 uniform variant |
| R3 burst bars | 8 (2 arms x 4 c_push) | each arm's c_push=0 record cell |
| M3 retry recovery | 3 (p_retry > 0) | M3 p_retry=0 record cell |

**Total primary-metric comparisons: 39** (D24 item 4: the eight
p = 0 reclaim rows became per-arm B1 guard gradings — null
controls cost Holm power). Honest-cost guards are per-arm gates,
not comparisons; bracketing-variant tables are report-only (R4.3).

## Bar-cell coverage table (W3.4 — Gate B blocker, D4 rule 1)

Bars are PROPOSED here; values register only by the Gate B entry.
Every proposed bar maps to planned cells; zero uncovered bars.

| bar (proposed) | metric | floor reference | covered by cells |
|---|---|---|---|
| B1 fairness reclaim: identity-split controller advantage <= GUARD under mitigation | draw-share advantage (D5 carry) | n/a (ratio guard) | all A1/A2/A3 cells with p > 0 (27 cells) |
| B2 honest-cost guard: honest p99 absolute TTDA regression vs unmitigated M2 same-p <= GUARD | honest_cost absolute clock | deliberate wait Q | all A1/A2/A3 cells (36 cells) |
| B3 A1 verification total drain <= GUARD x aggregate floor | verify_done last-completion | A1 table above | A1 cells (12) |
| B4 burst bars: post-event p99 <= 3x amended floor per grid point (v2 D17.1 carry) | post-event resolution | M1/M2 table above | R3 cells (8) |
| B5 M3 recovery: inventory sold and whole-run F vs p_retry=0 record | inventory + F-ratio | M3 floors above | M3 cells (9) |
| B6 A3 deadline-surface: registration-path p99 during final decile <= GUARD | registration wait stream | A3 table above | A3 deadline cells (4) |

Registered constants used: D13 population (n_split per p: {0.0: 0, 0.1: 15, 0.2: 30, 0.4: 60}),
D14.2 c_push grid, DC1-DC5 as amended (D17, D20), M3 allotment
[7,6,6,6] per pool (v2 flagged constant, carried).
