"""W6.1 (tatkal-v3): pre-registered grading — D24 bars/guards as
ratified by D25, over D23 tail-inclusive floors, Holm within family
over the 39-comparison inventory, the D20 deposit hypothesis graded
as registered.

Reads the W5 archive + the v2 record (center-cell rule, D3/R6).
Statistical machinery is v2's registered one verbatim (v7_grading:
paired per-seed deltas, seeded percentile bootstrap B=10,000, Holm).
Writes docs/specs/tatkal-v3/reports/w6-grading.json.

Measurement notes (recorded, per-metric honesty):
- B2 comparator is the record cell's overall absolute-TTDA p99 (the
  v2 archive has no per-cohort split); v3 side is the honest cohort.
  Bots skew faster, so the proxy is conservative against v3.
- B6 grades the WORST final-decile registration wait (the archive's
  captured quantity) against the p99 bar — max >= p99, so a pass is
  a fortiori a p99 pass; a miss would trigger a p99 re-derivation
  before being reported as a miss.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v3_floors import light_drain, pool_identities, rates  # noqa: E402
from v7_grading import boot, bot_advantage, f_ratio, holm  # noqa: E402

from tatkal_sim.measure.fitting import FIT_JSON, knee_variant, load_fit  # noqa: E402

V3R = Path(__file__).resolve().parent.parent / "docs" / "specs" / "tatkal-v3" / "reports"
V2R = Path(__file__).resolve().parent.parent / "docs" / "specs" / "tatkal-v2" / "reports"
SEEDS = [str(s) for s in range(20)]
P_ALL = ("0.0", "0.1", "0.2", "0.4")
P_POS = ("0.1", "0.2", "0.4")
CV_GRID = ("0.25", "1.0", "4.0")
D_GRID = ("0.1", "0.5", "2.0", "15.0")
C_PUSH = ("0.25", "0.5", "1.0", "2.0")
P_RETRY = ("0.25", "0.5", "1.0")


def med(xs):
    return statistics.median(xs)


def main() -> None:
    w5 = json.loads((V3R / "w5-sweeps-data.json").read_text())["cells"]
    v6 = json.loads((V2R / "v6-sweeps-data.json").read_text())["cells"]
    v5 = json.loads((V2R / "v5-baselines-data.json").read_text())["arms"]
    scfg = knee_variant("fitted", load_fit(FIT_JSON)["params"])
    winner_drain = 200 / rates(scfg)["drain_rate"]

    def w5s(cell, seed):
        return w5[cell]["per_seed"][seed]

    def rec_adv(p, seed):
        return bot_advantage(v6[f"m2-p{p}-fitted"]["per_seed"][seed]["fairness"])

    out: dict = {"families": {}, "bars": {}, "d20": {}, "notes": []}

    # ---- reclaim families (p > 0 only, D24 item 2/4) ----
    fam_a1, fam_a2, fam_a3 = {}, {}, {}
    for cv in CV_GRID:
        for p in P_POS:
            deltas = [
                bot_advantage(w5s(f"a1-cv{cv}-p{p}-fitted", s)["fairness"]) - rec_adv(p, s)
                for s in SEEDS
            ]
            fam_a1[f"a1-cv{cv}-p{p}"] = boot(deltas)
    for d in D_GRID:
        for p in P_POS:
            deltas = [
                bot_advantage(w5s(f"a2-d{d}-p{p}-fitted", s)["fairness"]) - rec_adv(p, s)
                for s in SEEDS
            ]
            fam_a2[f"a2-d{d}-p{p}"] = boot(deltas)
    for p in P_POS:
        deltas = [
            bot_advantage(w5s(f"a3-deadline-p{p}-fitted", s)["fairness"]) - rec_adv(p, s)
            for s in SEEDS
        ]
        fam_a3[f"a3-deadline-p{p}"] = boot(deltas)
    fam_a3u = {}
    for p in P_ALL:  # all p — honest-surface delta, unchanged (D24 item 4)
        deltas = [
            bot_advantage(w5s(f"a3-deadline-p{p}-fitted", s)["fairness"])
            - bot_advantage(w5s(f"a3-uniform-p{p}-fitted", s)["fairness"])
            for s in SEEDS
        ]
        fam_a3u[f"a3-deadline-vs-uniform-p{p}"] = boot(deltas)

    fam_r3 = {}
    for c in C_PUSH:
        for arm, reccell in (("m1", "m1-r0.8-fitted"), ("m2", "m2-p0.1-fitted")):
            deltas = [
                w5s(f"r3-{arm}-c{c}-fitted", s)["two_clock"]["post_event_resolution"]["p99"]
                - v6[reccell]["per_seed"][s]["two_clock"]["post_event_resolution"]["p99"]
                for s in SEEDS
            ]
            fam_r3[f"r3-{arm}-c{c}"] = boot(deltas)

    fam_m3 = {}
    for pr in P_RETRY:
        deltas = [
            w5s(f"m3-pr{pr}-fitted", s)["metrics"]["inventory"]["sold"]
            - v6["m3-fitted"]["per_seed"][s]["metrics"]["inventory"]["sold"]
            for s in SEEDS
        ]
        fam_m3[f"m3-pr{pr}"] = boot(deltas)

    for name, fam in (
        ("A1 reclaim", fam_a1),
        ("A2 reclaim", fam_a2),
        ("A3 reclaim", fam_a3),
        ("A3 profile delta", fam_a3u),
        ("R3 bursts", fam_r3),
        ("M3 recovery", fam_m3),
    ):
        holm(fam)
        out["families"][name] = fam
    n = sum(len(f) for f in out["families"].values())
    assert n == 39, f"registered inventory is 39, graded {n}"
    out["notes"].append("comparisons graded: 39 (D24 item 4)")

    # ---- B1 guards: <= 1.05 at p = 0; <= m (5) at p > 0 ----
    b1 = {}
    cells_all = (
        [(f"a1-cv{cv}-p{p}-fitted", p) for cv in CV_GRID for p in P_ALL]
        + [(f"a2-d{d}-p{p}-fitted", p) for d in D_GRID for p in P_ALL]
        + [(f"a3-{pr}-p{p}-fitted", p) for pr in ("deadline", "uniform") for p in P_ALL]
    )
    for cell, p in cells_all:
        if p == "0.0":
            # aggregate controller-level bot advantage (the D5 metric;
            # per-strategy max would fail on small-sample noise alone)
            vals = [bot_advantage(w5s(cell, s)["fairness"]) for s in SEEDS]
            b1[cell] = {"median": med(vals), "guard": 1.05, "pass": med(vals) <= 1.05}
        else:
            vals = [
                w5s(cell, s)["fairness"].get("identity_split", {}).get("advantage", 0.0)
                for s in SEEDS
            ]
            b1[cell] = {"median": med(vals), "guard": 5.0, "pass": med(vals) <= 5.0}
    out["bars"]["B1"] = b1

    # ---- B2 honest-cost guards (per arm, D24 item 3) ----
    b2 = {}
    for cv in CV_GRID:
        for p in P_ALL:
            cell = f"a1-cv{cv}-p{p}-fitted"
            floor = light_drain(scfg, pool_identities(float(p)), float(cv))
            hon = med(
                [w5s(cell, s)["honest_cost"]["t0_humans"]["absolute_ttda"]["p99"] for s in SEEDS]
            )
            ref = med(
                [
                    v6[f"m2-p{p}-fitted"]["per_seed"][s]["two_clock"]["absolute_ttda"]["p99"]
                    for s in SEEDS
                ]
            )
            entry = {
                "regression_s": hon - ref,
                "guard_s": 3 * floor,
                "pass": (hon - ref) <= 3 * floor,
            }
            if cv == "4.0":
                entry["pre_registered_expected_breach"] = True
            b2[cell] = entry
    for fam_cells, label in (
        ([(f"a2-d{d}-p{p}-fitted", p) for d in D_GRID for p in P_ALL], "a2"),
        (
            [(f"a3-{pr}-p{p}-fitted", p) for pr in ("deadline", "uniform") for p in P_ALL],
            "a3",
        ),
    ):
        for cell, p in fam_cells:
            hon = med(
                [w5s(cell, s)["honest_cost"]["t0_humans"]["absolute_ttda"]["p99"] for s in SEEDS]
            )
            ref = med(
                [
                    v6[f"m2-p{p}-fitted"]["per_seed"][s]["two_clock"]["absolute_ttda"]["p99"]
                    for s in SEEDS
                ]
            )
            ratio = hon / ref if ref else float("inf")
            b2[cell] = {"ratio": ratio, "guard": 1.05, "pass": ratio <= 1.05}
    out["bars"]["B2"] = b2

    # ---- B3: last verify_done - t0 <= 3x tail-inclusive floor ----
    b3 = {}
    for cv in CV_GRID:
        for p in P_ALL:
            floor = light_drain(scfg, pool_identities(float(p)), float(cv))
            vals = [
                w5s(f"a1-cv{cv}-p{p}-fitted", s)["gate_b"]["b3_last_verify_offset"] for s in SEEDS
            ]
            vals = [v for v in vals if v is not None]
            b3[f"a1-cv{cv}-p{p}"] = {
                "median_s": med(vals),
                "floor_s": floor,
                "pass": med(vals) <= 3 * floor,
            }
    out["bars"]["B3"] = b3

    # ---- B4: post-event p99 <= 3x amended tail-inclusive floor ----
    b4 = {}
    n_humans = 30 + 2500
    m1_losers = round(0.8 * n_humans) - 200
    m2_losers = pool_identities(0.1) - 200
    for c in C_PUSH:
        for arm, losers in (("m1", m1_losers), ("m2", m2_losers)):
            burst = light_drain(scfg, losers, float(c) * scfg.status_cost_factor)
            floor = max(burst, winner_drain)
            vals = [
                w5s(f"r3-{arm}-c{c}-fitted", s)["two_clock"]["post_event_resolution"]["p99"]
                for s in SEEDS
            ]
            b4[f"r3-{arm}-c{c}"] = {
                "median_s": med(vals),
                "floor_s": floor,
                "pass": med(vals) <= 3 * floor,
            }
    out["bars"]["B4"] = b4

    # ---- B5: recovery — primary inventory (improvement rule) + F guard
    sold = [w5s("m3-pr1.0-fitted", s)["metrics"]["inventory"]["sold"] for s in SEEDS]
    rec_sold = [v6["m3-fitted"]["per_seed"][s]["metrics"]["inventory"]["sold"] for s in SEEDS]
    b = fam_m3["m3-pr1.0"]
    improvement = (med(sold) - med(rec_sold)) / med(rec_sold) if med(rec_sold) else 0.0
    f_m3 = [f_ratio(w5s("m3-pr1.0-fitted", s)["metrics"]) for s in SEEDS]
    f_r2 = [f_ratio(v5["rung2-fitted"]["per_seed"][s]) for s in SEEDS]
    f_guard_excess = med([f_m3[i] - 1.05 * f_r2[i] for i in range(20)])
    out["bars"]["B5"] = {
        "median_sold": med(sold),
        "record_sold": med(rec_sold),
        "improvement": improvement,
        "ci_excludes_zero": not b["includes_zero"],
        "F_guard_excess": f_guard_excess,
        "F_guard_pass": f_guard_excess <= 0.0,
        "recovery_claim": improvement >= 0.10 and not b["includes_zero"] and f_guard_excess <= 0.0,
    }

    # ---- B6: worst final-decile reg wait vs 3x floor (conservative) ----
    reg_floor = light_drain(scfg, round(0.6 * round(0.8 * n_humans)), scfg.status_cost_factor)
    b6 = {}
    for p in P_ALL:
        vals = [
            w5s(f"a3-deadline-p{p}-fitted", s)["gate_b"]["b6_worst_final_decile_reg_wait"]
            for s in SEEDS
        ]
        vals = [v for v in vals if v is not None]
        b6[f"a3-deadline-p{p}"] = {
            "worst_s": med(vals),
            "floor_s": reg_floor,
            "pass": med(vals) <= 3 * reg_floor,
        }
    out["bars"]["B6"] = b6

    # ---- D20 deposit hypothesis, graded as registered ----
    for d in D_GRID:
        stakes = [w5s(f"a2-d{d}-p0.2-fitted", s)["streams"]["stake_in"] for s in SEEDS]
        adv = [
            w5s(f"a2-d{d}-p0.2-fitted", s)["fairness"]
            .get("identity_split", {})
            .get("advantage", 0.0)
            for s in SEEDS
        ]
        out["d20"][f"d={d} (p=0.2)"] = {
            "median_stakes": med(stakes),
            "median_split_advantage": med(adv),
        }

    (V3R / "w6-grading.json").write_text(json.dumps(out, indent=1))
    print(f"wrote {V3R / 'w6-grading.json'}")
    for bar in ("B1", "B2", "B3", "B4", "B6"):
        res = out["bars"][bar]
        passes = sum(1 for v in res.values() if v["pass"])
        print(f"{bar}: {passes}/{len(res)} pass")
    print("B5 ->", {k: v for k, v in out["bars"]["B5"].items()})
    for name, fam in out["families"].items():
        dist = sum(1 for v in fam.values() if v["distinguishable_holm"])
        meds = [round(v["median"], 3) for v in fam.values()]
        print(f"family {name}: {dist}/{len(fam)} Holm-distinguishable; medians {meds}")
    print("D20:", json.dumps(out["d20"], indent=0))


if __name__ == "__main__":
    main()
