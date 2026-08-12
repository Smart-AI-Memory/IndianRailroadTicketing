"""V4.3/V4.4 (tatkal-v2): compute the floor document + multiplicity
inventory for Gate B, from model constants only (D3: floors are
arithmetic, not empirical).

Writes docs/specs/tatkal-v2/floors.md.

Floors are BEST-CASE by construction (no congestion, no stalls, no
contention beyond the stated serialization): a bar registered against a
floor states its distance from physics, not from an observed run.
"""

from __future__ import annotations

import math
from pathlib import Path

from tatkal_sim.measure.fitting import FIT_JSON, KNEE_VARIANTS, knee_variant, load_fit
from tatkal_sim.model.workload_v2 import OPERATING_WORKLOAD_V2
from tatkal_sim.runner_v2 import C_PUSH_GRID
from tatkal_sim.strategies.allocation import M3_POOL_ALLOTMENT

OUT = Path(__file__).resolve().parent.parent / "docs" / "specs" / "tatkal-v2" / "floors.md"

WCFG = OPERATING_WORKLOAD_V2
SEATS = 200  # 8 pools x 25 (v2 arms; ladder seats param)
SEATS_PER_POOL = 25


def rates(scfg) -> dict:
    """Best-case service rates from config arithmetic."""
    mean_app = math.exp(scfg.app_mu + scfg.app_sigma**2 / 2) + scfg.tail_p * scfg.tail_mean
    worker_rate = scfg.workers / mean_app  # bookings/s, zero congestion
    hold = scfg.lock_hold + scfg.hold_stall_p * scfg.hold_stall_mean
    lock_rate = WCFG.n_trains / hold if hold > 0 else float("inf")  # pools in parallel
    return {
        "mean_app_s": mean_app,
        "worker_rate": worker_rate,
        "lock_rate": lock_rate,
        "drain_rate": min(worker_rate, lock_rate),
    }


def burst_floor(scfg, n_deliveries: int, c_push: float) -> float:
    """Notification-burst drain floor: n light work items at
    c_push * status_cost_factor * mean_app over the worker pool."""
    if c_push <= 0:
        return 0.0
    mean_app = math.exp(scfg.app_mu + scfg.app_sigma**2 / 2)
    per_push = c_push * scfg.status_cost_factor * mean_app
    return n_deliveries * per_push / scfg.workers


def main() -> None:
    fitted = load_fit(FIT_JSON)["params"]
    lines = [
        "# tatkal-v2 — floor document (V4.3) and multiplicity inventory (V4.4)",
        "",
        "**Status:** computed 2026-08-12 from model constants (arithmetic,",
        "not empirical); input to Gate B. Every bar registered at Gate B",
        "states its distance from the relevant floor below (D3).",
        "",
        "Population: operating v2 (D13); seats = 200 (8 pools x 25).",
        "Losers counted at the operating point: M1 ~ registered - 200;",
        "M2 ~ pool - 200 (identity entries inflate the M2 burst with p).",
        "",
    ]
    n_humans = WCFG.n_pre_fire + WCFG.n_t0_humans
    m1_losers = round(0.8 * n_humans) - SEATS  # center uptake cell
    m2_pool = n_humans + WCFG.n_bots + 30 * (WCFG.m_identities - 1)  # p=0.2 center
    m2_losers = m2_pool - SEATS

    for variant in KNEE_VARIANTS:
        scfg = knee_variant(variant, fitted)
        r = rates(scfg)
        drain = SEATS / r["drain_rate"]
        lines += [
            f"## Variant: {variant}",
            "",
            f"- mean app time (best case): {r['mean_app_s'] * 1000:.4f} ms",
            f"- worker-bound rate: {r['worker_rate']:.0f} bookings/s;"
            f" lock-bound rate: {r['lock_rate']:.0f}/s",
            f"- **inventory-drain floor (engineering, R3'): {drain * 1000:.3f} ms**"
            f" (200 seats at {r['drain_rate']:.0f}/s)",
            "",
            "| clock / arm | floor | derivation |",
            "|---|---|---|",
            f"| eng/R3' absolute & resolution | {drain * 1000:.3f} ms | drain arithmetic |",
        ]
        for c in C_PUSH_GRID:
            bf_m1 = burst_floor(scfg, m1_losers, c)
            bf_m2 = burst_floor(scfg, m2_losers, c)
            lines.append(
                f"| M1 post-event (c_push={c}) | {bf_m1 * 1000:.3f} ms |"
                f" {m1_losers} pushes / {scfg.workers} workers |"
            )
            lines.append(
                f"| M2 post-event (c_push={c}) | {bf_m2 * 1000:.3f} ms |"
                f" {m2_losers} pushes / {scfg.workers} workers |"
            )
        per_tranche = [WCFG.n_trains * a / r["drain_rate"] * 1000 for a in M3_POOL_ALLOTMENT]
        whole = WCFG.pace_horizon + per_tranche[-1] / 1000
        lines += [
            "| M3 per-tranche drain | "
            + ", ".join(f"{t:.3f} ms" for t in per_tranche)
            + " | global allotment {56,48,48,48} at drain rate |",
            f"| M3 whole-run | {whole:.3f} s | H + last-tranche drain |",
            "| M1/M2 absolute (losers) | >= deliberate wait | W or Q by design (D14.5) |",
            "",
        ]

    lines += [
        "## Multiplicity inventory (V4.4)",
        "",
        "Planned paired comparisons (primary metric, fitted variant,",
        "per clock where two clocks exist). Gate B registers the count",
        "and the correction policy over exactly this list:",
        "",
        "| family | cells | baselines | comparisons |",
        "|---|---|---|---|",
        "| M1 vs eng (D7) | 3 uptake | rung 2, rung 4 | 6 |",
        "| M2 vs eng (D7) | 4 abuse | rung 2, rung 4 | 8 |",
        "| M3 vs eng (D7) | 1 | rung 2, rung 4 | 2 |",
        "| R3' break-even (D6) | 5 c_push | rung 2 | 5 |",
        "| P1 diagnostic (D13.5) | 1 (p=0) | — | 1 |",
        "",
        "**Total primary-metric comparisons: 22** (x2 clocks for the",
        "allocation arms' latency bars where registered; fairness guards",
        "are per-arm gates, not comparisons, and are listed at Gate B).",
        "",
        "Registered constants used: D13 population, D14 windows/grid;",
        "M3 allotment deviation [7,6,6,6] per pool as flagged in",
        "strategies/allocation.py (awaiting chair entry).",
    ]
    OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
