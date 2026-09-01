"""W3.2–W3.4 (tatkal-v3): compute the floor document, multiplicity
inventory, and bar-cell coverage table for Gate B — from model
constants only (D3 carry: floors are arithmetic, not empirical).

Writes docs/specs/tatkal-v3/floors.md.

D4 rule 2 (floor completeness): every derivation enumerates its drain
components and states why omitted ones are irrelevant. D17 finding 3:
floors are named PER METRIC — an aggregate-drain number never grades a
wait distribution.
"""

from __future__ import annotations

import math
from pathlib import Path

from tatkal_sim.measure.fitting import FIT_JSON, KNEE_VARIANTS, knee_variant, load_fit
from tatkal_sim.model.workload_v2 import OPERATING_WORKLOAD_V2
from tatkal_sim.strategies.allocation import M3_POOL_ALLOTMENT
from tatkal_sim.strategies.mitigation import C_VERIFY_GRID, D_GRID

OUT = Path(__file__).resolve().parent.parent / "docs" / "specs" / "tatkal-v3" / "floors.md"

WCFG = OPERATING_WORKLOAD_V2
SEATS = 200  # 8 pools x 25
P_GRID = (0.0, 0.1, 0.2, 0.4)
C_PUSH_POINTS = (0.25, 0.5, 1.0, 2.0)  # zero cells are the v2 record
P_RETRY_GRID = (0.0, 0.25, 0.5, 1.0)


def rates(scfg) -> dict:
    mean_app = math.exp(scfg.app_mu + scfg.app_sigma**2 / 2) + scfg.tail_p * scfg.tail_mean
    worker_rate = scfg.workers / mean_app
    hold = scfg.lock_hold + scfg.hold_stall_p * scfg.hold_stall_mean
    lock_rate = WCFG.n_trains / hold if hold > 0 else float("inf")
    return {
        "mean_app_s": mean_app,
        "worker_rate": worker_rate,
        "lock_rate": lock_rate,
        "drain_rate": min(worker_rate, lock_rate),
    }


def pool_identities(p: float) -> int:
    """M2-family draw-pool identities at abuse prevalence p (humans +
    all bot identities; background overlap excluded — see enumeration
    in the document)."""
    n_split = round(p * WCFG.n_bots)
    return WCFG.n_pre_fire + WCFG.n_t0_humans + WCFG.n_bots + (WCFG.m_identities - 1) * n_split


def light_drain(scfg, n_items: int, cost_factor: float) -> float:
    if cost_factor <= 0 or n_items <= 0:
        return 0.0
    mean_app = math.exp(scfg.app_mu + scfg.app_sigma**2 / 2)
    return n_items * cost_factor * mean_app / scfg.workers


def main() -> None:
    fitted = load_fit(FIT_JSON)["params"]
    n_humans = WCFG.n_pre_fire + WCFG.n_t0_humans
    m1_losers = round(0.8 * n_humans) - SEATS
    lines = [
        "# tatkal-v3 — floor document (W3.2), multiplicity inventory (W3.3), coverage table (W3.4)",
        "",
        "**Status:** computed 2026-09-01 from model constants (arithmetic,",
        "not empirical); the Gate B packet. Every bar registered at Gate B",
        "states its distance from the relevant floor, per metric (D17.3).",
        "",
        "Population: v2 D13 carried verbatim (D3); seats = 200 (8 pools x 25).",
        "",
        "## Drain-component enumeration (D4 rule 2)",
        "",
        "- **A1 verification drain** includes: one light work item per",
        "  entering identity at `c_verify x mean app time`, served by the",
        "  shared worker pool. Excluded: entry-poll traffic (charged to the",
        "  booking path's own floors), retry-on-saturation re-submissions",
        "  (congestion, not physics — floors are best-case). Draw-pool",
        "  identity counts EXCLUDE the background overlap (~<=60 arrivals in",
        "  [T0+2, T0+Q]): including them would raise floors by < 2.3%, and",
        "  floors must under- not over-state physics.",
        "- **M1/M2 post-event floors (amended rule, D1/D18.2)**:",
        "  max(loser-burst drain, winner-redemption drain). Components:",
        "  burst = losers x c_push x status_cost x mean_app / workers;",
        "  winner drain = 200 bookings at the inventory drain rate.",
        "  Excluded: stake-ledger bookkeeping (A2) — pure accounting, no",
        "  server work by design (D5: utility parameter, not payment flow).",
        "- **M3 floors**: per-tranche allotment drain + whole-run",
        "  H + last-tranche drain (v2 carry). p_retry adds OFFERED LOAD,",
        "  not floor components: re-entered demand contends for the same",
        "  seats at the same drain rate, so floors are p_retry-invariant;",
        "  what re-entry changes is measured, not floored.",
        "- **A3 registration-surface drain**: one registration one-shot per",
        "  registrant at status cost (v2 M1 carry); under DC4 ~60% of it",
        "  concentrates near the window close. Floor stated for the final",
        "  decile of W. Excluded: camp-bot registrations (first 5% of W,",
        "  disjoint in time).",
        "- **A2**: no infrastructure floors — the deposit is a utility",
        "  parameter (D5); its price shows up in the honest-cost readout",
        "  (stake exposure), not in any latency floor.",
        "",
    ]

    for variant in KNEE_VARIANTS:
        scfg = knee_variant(variant, fitted)
        r = rates(scfg)
        drain = SEATS / r["drain_rate"]
        winner_drain_ms = drain * 1000
        lines += [
            f"## Variant: {variant}",
            "",
            f"- mean app time (best case): {r['mean_app_s'] * 1000:.4f} ms;"
            f" workers: {scfg.workers}",
            f"- winner-redemption drain (200 seats): {winner_drain_ms:.3f} ms",
            "",
            "### A1 — verification aggregate-drain floor (per c_verify x p)",
            "",
            "Grades TOTAL verification drain and the last entry's completion",
            "ONLY. Per-identity wait-distribution bars (p50/p99) take the",
            "work-conservation lower bound of 0 under spread arrivals — a",
            "distribution bar at Gate B binds against the measured",
            "distribution with THIS aggregate floor as context, never as a",
            "per-identity floor (D17.3).",
            "",
            "| c_verify \\\\ p | " + " | ".join(str(p) for p in P_GRID) + " |",
            "|---|" + "---|" * len(P_GRID),
        ]
        for cv in C_VERIFY_GRID:
            cells = [f"{light_drain(scfg, pool_identities(p), cv) * 1000:.1f} ms" for p in P_GRID]
            lines.append(f"| {cv} | " + " | ".join(cells) + " |")
        lines += [
            "",
            "### M1/M2 post-event floors per c_push (amended: max(burst, winner drain))",
            "",
            "| arm (losers) | " + " | ".join(str(c) for c in C_PUSH_POINTS) + " |",
            "|---|" + "---|" * len(C_PUSH_POINTS),
        ]
        m2_losers = pool_identities(0.1) - SEATS  # v3 burst cells run at center p=0.1
        for label, losers in (
            (f"M1 ({m1_losers})", m1_losers),
            (f"M2 p=0.1 ({m2_losers})", m2_losers),
        ):
            cells = []
            for c in C_PUSH_POINTS:
                burst = light_drain(scfg, losers, c * scfg.status_cost_factor)
                floor = max(burst * 1000, winner_drain_ms)
                cells.append(f"{floor:.3f} ms")
            lines.append(f"| {label} | " + " | ".join(cells) + " |")
        per_tranche = [WCFG.n_trains * a / r["drain_rate"] * 1000 for a in M3_POOL_ALLOTMENT]
        whole = WCFG.pace_horizon + per_tranche[-1] / 1000
        reg_final_decile = light_drain(
            scfg, round(0.6 * round(0.8 * n_humans)), scfg.status_cost_factor
        )
        lines += [
            "",
            "### M3 (all p_retry points — floors are p_retry-invariant, see enumeration)",
            "",
            "| metric | floor |",
            "|---|---|",
            "| per-tranche drain | " + ", ".join(f"{t:.3f} ms" for t in per_tranche) + " |",
            f"| whole-run | {whole:.3f} s (H + last-tranche drain) |",
            "",
            "### A3 registration surface (DC4 deadline profile)",
            "",
            f"| final-decile registration drain | {reg_final_decile * 1000:.3f} ms"
            " | ~60% of registrants x status cost / workers |",
            "",
        ]

    n_split_cells = {p: round(p * WCFG.n_bots) for p in P_GRID}
    lines += [
        "## Multiplicity inventory (W3.3)",
        "",
        "Planned paired comparisons, primary metric per family, fitted",
        "variant. Gate B registers the count and the correction policy",
        "(proposed: Holm within family, v2 precedent) over exactly this list:",
        "",
        "| family | comparisons | against |",
        "|---|---|---|",
        "| A1 fairness reclaim | 12 (3 c_verify x 4 p) | unmitigated M2, same p (v2 record) |",
        "| A2 fairness reclaim | 16 (4 d x 4 p) | unmitigated M2, same p (v2 record) |",
        "| A3 fairness reclaim | 4 (deadline profile x 4 p) | unmitigated M2, same p (v2 record) |",
        "| A3 deadline-vs-uniform delta (R5.1) | 4 (per p) | A3 uniform variant |",
        "| R3 burst bars | 8 (2 arms x 4 c_push) | each arm's c_push=0 record cell |",
        "| M3 retry recovery | 3 (p_retry > 0) | M3 p_retry=0 record cell |",
        "",
        "**Total primary-metric comparisons: 47.** Honest-cost guards are",
        "per-arm gates, not comparisons (v2 precedent); bracketing-variant",
        "tables are report-only (R4.3).",
        "",
        "## Bar-cell coverage table (W3.4 — Gate B blocker, D4 rule 1)",
        "",
        "Bars are PROPOSED here; values register only by the Gate B entry.",
        "Every proposed bar maps to planned cells; zero uncovered bars.",
        "",
        "| bar (proposed) | metric | floor reference | covered by cells |",
        "|---|---|---|---|",
        "| B1 fairness reclaim: identity-split controller advantage <= GUARD under mitigation | draw-share advantage (D5 carry) | n/a (ratio guard) | all A1/A2/A3 cells with p > 0 (27 cells) |",
        "| B2 honest-cost guard: honest p99 absolute TTDA regression vs unmitigated M2 same-p <= GUARD | honest_cost absolute clock | deliberate wait Q | all A1/A2/A3 cells (36 cells) |",
        "| B3 A1 verification total drain <= GUARD x aggregate floor | verify_done last-completion | A1 table above | A1 cells (12) |",
        "| B4 burst bars: post-event p99 <= 3x amended floor per grid point (v2 D17.1 carry) | post-event resolution | M1/M2 table above | R3 cells (8) |",
        "| B5 M3 recovery: inventory sold and whole-run F vs p_retry=0 record | inventory + F-ratio | M3 floors above | M3 cells (9) |",
        "| B6 A3 deadline-surface: registration-path p99 during final decile <= GUARD | registration wait stream | A3 table above | A3 deadline cells (4) |",
        "",
        f"Registered constants used: D13 population (n_split per p: {n_split_cells}),",
        "D14.2 c_push grid, DC1-DC5 as amended (D17, D20), M3 allotment",
        "[7,6,6,6] per pool (v2 flagged constant, carried).",
        "",
    ]
    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
