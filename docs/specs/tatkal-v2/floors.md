# tatkal-v2 — floor document (V4.3) and multiplicity inventory (V4.4)

**Status:** computed 2026-08-12 from model constants (arithmetic,
not empirical); input to Gate B. Every bar registered at Gate B
states its distance from the relevant floor below (D3).

Population: operating v2 (D13); seats = 200 (8 pools x 25).
Losers counted at the operating point: M1 ~ registered - 200;
M2 ~ pool - 200 (identity entries inflate the M2 burst with p).

## Variant: fitted

- mean app time (best case): 0.1419 ms
- worker-bound rate: 14090 bookings/s; lock-bound rate: 88889/s
- **inventory-drain floor (engineering, R3'): 14.195 ms** (200 seats at 14090/s)

| clock / arm | floor | derivation |
|---|---|---|
| eng/R3' absolute & resolution | 14.195 ms | drain arithmetic |
| M1 post-event (c_push=0.0) | 0.000 ms | 1824 pushes / 2 workers |
| M2 post-event (c_push=0.0) | 0.000 ms | 2600 pushes / 2 workers |
| M1 post-event (c_push=0.25) | 4.193 ms | 1824 pushes / 2 workers |
| M2 post-event (c_push=0.25) | 5.977 ms | 2600 pushes / 2 workers |
| M1 post-event (c_push=0.5) | 8.386 ms | 1824 pushes / 2 workers |
| M2 post-event (c_push=0.5) | 11.953 ms | 2600 pushes / 2 workers |
| M1 post-event (c_push=1.0) | 16.771 ms | 1824 pushes / 2 workers |
| M2 post-event (c_push=1.0) | 23.906 ms | 2600 pushes / 2 workers |
| M1 post-event (c_push=2.0) | 33.542 ms | 1824 pushes / 2 workers |
| M2 post-event (c_push=2.0) | 47.812 ms | 2600 pushes / 2 workers |
| M3 per-tranche drain | 3.974 ms, 3.407 ms, 3.407 ms, 3.407 ms | global allotment {56,48,48,48} at drain rate |
| M3 whole-run | 8.003 s | H + last-tranche drain |
| M1/M2 absolute (losers) | >= deliberate wait | W or Q by design (D14.5) |

## Variant: plateau

- mean app time (best case): 0.1419 ms
- worker-bound rate: 14090 bookings/s; lock-bound rate: 88889/s
- **inventory-drain floor (engineering, R3'): 14.195 ms** (200 seats at 14090/s)

| clock / arm | floor | derivation |
|---|---|---|
| eng/R3' absolute & resolution | 14.195 ms | drain arithmetic |
| M1 post-event (c_push=0.0) | 0.000 ms | 1824 pushes / 2 workers |
| M2 post-event (c_push=0.0) | 0.000 ms | 2600 pushes / 2 workers |
| M1 post-event (c_push=0.25) | 4.193 ms | 1824 pushes / 2 workers |
| M2 post-event (c_push=0.25) | 5.977 ms | 2600 pushes / 2 workers |
| M1 post-event (c_push=0.5) | 8.386 ms | 1824 pushes / 2 workers |
| M2 post-event (c_push=0.5) | 11.953 ms | 2600 pushes / 2 workers |
| M1 post-event (c_push=1.0) | 16.771 ms | 1824 pushes / 2 workers |
| M2 post-event (c_push=1.0) | 23.906 ms | 2600 pushes / 2 workers |
| M1 post-event (c_push=2.0) | 33.542 ms | 1824 pushes / 2 workers |
| M2 post-event (c_push=2.0) | 47.812 ms | 2600 pushes / 2 workers |
| M3 per-tranche drain | 3.974 ms, 3.407 ms, 3.407 ms, 3.407 ms | global allotment {56,48,48,48} at drain rate |
| M3 whole-run | 8.003 s | H + last-tranche drain |
| M1/M2 absolute (losers) | >= deliberate wait | W or Q by design (D14.5) |

## Variant: cliff

- mean app time (best case): 0.1419 ms
- worker-bound rate: 14090 bookings/s; lock-bound rate: 88889/s
- **inventory-drain floor (engineering, R3'): 14.195 ms** (200 seats at 14090/s)

| clock / arm | floor | derivation |
|---|---|---|
| eng/R3' absolute & resolution | 14.195 ms | drain arithmetic |
| M1 post-event (c_push=0.0) | 0.000 ms | 1824 pushes / 2 workers |
| M2 post-event (c_push=0.0) | 0.000 ms | 2600 pushes / 2 workers |
| M1 post-event (c_push=0.25) | 4.193 ms | 1824 pushes / 2 workers |
| M2 post-event (c_push=0.25) | 5.977 ms | 2600 pushes / 2 workers |
| M1 post-event (c_push=0.5) | 8.386 ms | 1824 pushes / 2 workers |
| M2 post-event (c_push=0.5) | 11.953 ms | 2600 pushes / 2 workers |
| M1 post-event (c_push=1.0) | 16.771 ms | 1824 pushes / 2 workers |
| M2 post-event (c_push=1.0) | 23.906 ms | 2600 pushes / 2 workers |
| M1 post-event (c_push=2.0) | 33.542 ms | 1824 pushes / 2 workers |
| M2 post-event (c_push=2.0) | 47.812 ms | 2600 pushes / 2 workers |
| M3 per-tranche drain | 3.974 ms, 3.407 ms, 3.407 ms, 3.407 ms | global allotment {56,48,48,48} at drain rate |
| M3 whole-run | 8.003 s | H + last-tranche drain |
| M1/M2 absolute (losers) | >= deliberate wait | W or Q by design (D14.5) |

## Multiplicity inventory (V4.4)

Planned paired comparisons (primary metric, fitted variant,
per clock where two clocks exist). Gate B registers the count
and the correction policy over exactly this list:

| family | cells | baselines | comparisons |
|---|---|---|---|
| M1 vs eng (D7) | 3 uptake | rung 2, rung 4 | 6 |
| M2 vs eng (D7) | 4 abuse | rung 2, rung 4 | 8 |
| M3 vs eng (D7) | 1 | rung 2, rung 4 | 2 |
| R3' break-even (D6) | 5 c_push | rung 2 | 5 |
| P1 diagnostic (D13.5) | 1 (p=0) | — | 1 |

**Total primary-metric comparisons: 22** (x2 clocks for the
allocation arms' latency bars where registered; fairness guards
are per-arm gates, not comparisons, and are listed at Gate B).

Registered constants used: D13 population, D14 windows/grid;
M3 allotment deviation [7,6,6,6] per pool as flagged in
strategies/allocation.py (awaiting chair entry).
