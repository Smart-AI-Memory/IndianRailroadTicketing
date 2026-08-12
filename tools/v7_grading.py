"""V7.1 (tatkal-v2): pre-registered grading — D17 bars/guards, D7
comparisons with Holm within family, P1 verdict.

Reads the V5/V6 archives; re-derives loser-only clocks for the fitted
M1/M2 cells by deterministic re-run (R1: same seed, same trace — the
archive stores combined percentiles only). Writes
docs/specs/tatkal-v2/reports/v7-grading.json and prints the grading
summary.

Statistical machinery is the registered one: paired per-seed deltas,
seeded percentile bootstrap (B=10,000) on the median. Holm needs
p-values: the bootstrap two-sided p is computed from the same seeded
resample stream (p = 2*min(P(med<=0), P(med>=0)) with +1/B smoothing)
— an implementation detail of the registered bootstrap, not a new
test.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

from tatkal_sim.core.rng import derive_stream
from tatkal_sim.measure.metrics import _pcts
from tatkal_sim.model.workload_v2 import OPERATING_WORKLOAD_V2, with_abuse, with_uptake
from tatkal_sim.runner_v2 import V2Arm, run_arm_v2_once

REPORTS = Path(__file__).resolve().parent.parent / "docs" / "specs" / "tatkal-v2" / "reports"
SEEDS = list(range(20))
B = 10_000


def boot(deltas: list[float]) -> dict:
    rng = derive_stream(0, "stats")
    n = len(deltas)
    meds = sorted(
        statistics.median(deltas[int(rng.random() * n)] for _ in range(n)) for _ in range(B)
    )
    lo, hi = meds[int(0.025 * B)], meds[min(B - 1, int(0.975 * B))]
    le = sum(1 for m in meds if m <= 0.0)
    ge = sum(1 for m in meds if m >= 0.0)
    p = min(1.0, 2.0 * (min(le, ge) + 1) / (B + 1))
    return {
        "median": statistics.median(deltas),
        "ci": [lo, hi],
        "p_boot": p,
        "includes_zero": lo <= 0.0 <= hi,
    }


def holm(family: dict[str, dict]) -> None:
    """Holm–Bonferroni within family (D17.3), in place."""
    items = sorted(family.items(), key=lambda kv: kv[1]["p_boot"])
    m = len(items)
    running_reject = True
    for i, (name, r) in enumerate(items):
        adj = min(1.0, (m - i) * r["p_boot"])
        r["p_holm"] = adj
        running_reject = running_reject and adj < 0.05
        r["distinguishable_holm"] = running_reject


def bot_advantage(fairness: dict) -> float:
    """Aggregate controller-level bot advantage from per-strategy rows."""
    bw = sum(v["controller_wins"] for k, v in fairness.items() if k != "human")
    bc = sum(v["controllers"] for k, v in fairness.items() if k != "human")
    tw = sum(v["controller_wins"] for v in fairness.values())
    tc = sum(v["controllers"] for v in fairness.values())
    if not (bc and tw and tc):
        return 0.0
    return (bw / tw) / (bc / tc)


def f_ratio(metrics: dict) -> float:
    f = metrics["fairness"]
    return (f["bots_win_share"] / f["bots_population_share"]) if f["bots_population_share"] else 0.0


def main() -> None:
    v5 = json.loads((REPORTS / "v5-baselines-data.json").read_text())
    v6 = json.loads((REPORTS / "v6-sweeps-data.json").read_text())
    cells = v6["cells"]
    base = {
        name: {int(s): m for s, m in v5["arms"][name]["per_seed"].items()}
        for name in ("rung2-fitted", "rung4-fitted")
    }
    out: dict = {"families": {}, "guards": {}, "bars": {}, "p1": {}}

    # ---- D7 fairness comparisons: mechanism advantage - baseline F ----
    fam_m1, fam_m2, fam_m3 = {}, {}, {}
    for r in ("0.5", "0.8", "0.95"):
        adv = {
            s: bot_advantage(cells[f"m1-r{r}-fitted"]["per_seed"][str(s)]["fairness"])
            for s in SEEDS
        }
        for bname, bkey in (("rung2", "rung2-fitted"), ("rung4", "rung4-fitted")):
            deltas = [adv[s] - f_ratio(base[bkey][s]) for s in SEEDS]
            fam_m1[f"m1-r{r} vs {bname}"] = boot(deltas)
    for p in ("0.0", "0.1", "0.2", "0.4"):
        adv = {
            s: bot_advantage(cells[f"m2-p{p}-fitted"]["per_seed"][str(s)]["fairness"])
            for s in SEEDS
        }
        for bname, bkey in (("rung2", "rung2-fitted"), ("rung4", "rung4-fitted")):
            deltas = [adv[s] - f_ratio(base[bkey][s]) for s in SEEDS]
            fam_m2[f"m2-p{p} vs {bname}"] = boot(deltas)
    f_m3 = {s: f_ratio(cells["m3-fitted"]["per_seed"][str(s)]["metrics"]) for s in SEEDS}
    for bname, bkey in (("rung2", "rung2-fitted"), ("rung4", "rung4-fitted")):
        fam_m3[f"m3 vs {bname}"] = boot([f_m3[s] - f_ratio(base[bkey][s]) for s in SEEDS])

    # ---- R3' latency family: rejected resolution p99 vs rung2 ----
    fam_r3 = {}
    for c in ("0.0", "0.25", "0.5", "1.0", "2.0"):
        cand = {
            s: cells[f"r3p-c{c}-fitted"]["per_seed"][str(s)]["metrics"]["resolution"]["rejected"][
                "p99"
            ]
            for s in SEEDS
        }
        deltas = [cand[s] - base["rung2-fitted"][s]["resolution"]["rejected"]["p99"] for s in SEEDS]
        fam_r3[f"r3p-c{c} vs rung2"] = boot(deltas)

    for name, fam in (("M1", fam_m1), ("M2", fam_m2), ("M3", fam_m3), ("R3'", fam_r3)):
        holm(fam)
        out["families"][name] = fam

    # ---- P1 + guards ----
    p0 = [cells["m2-p0.0-fitted"]["per_seed"][str(s)]["fairness"] for s in SEEDS]
    for strat in ("race", "mimic"):
        vals = [c[strat]["advantage"] for c in p0 if strat in c]
        b = boot([v - 1.0 for v in vals])
        out["p1"][strat] = {
            "median_advantage": statistics.median(vals),
            "excess_ci": b["ci"],
            "excess_includes_zero": b["includes_zero"],
            "guard_1_05_nominal_breach": statistics.median(vals) > 1.05,
        }
    for p in ("0.1", "0.2", "0.4"):
        vals = [
            cells[f"m2-p{p}-fitted"]["per_seed"][str(s)]["fairness"]["identity_split"]["advantage"]
            for s in SEEDS
        ]
        out["guards"][f"abuse p={p} (<= m=5)"] = {
            "median": statistics.median(vals),
            "pass": statistics.median(vals) <= 5.0,
        }
    # M3 / R3' 5% F-regression guards
    for bname, bkey in (("rung2", "rung2-fitted"),):
        deltas = [f_m3[s] - 1.05 * f_ratio(base[bkey][s]) for s in SEEDS]
        out["guards"][f"m3 F vs 1.05x {bname}"] = {
            "median_excess": statistics.median(deltas),
            "pass": statistics.median(deltas) <= 0.0,
        }
    f_r4 = {s: f_ratio(base["rung4-fitted"][s]) for s in SEEDS}
    for c in ("0.25", "0.5", "1.0", "2.0"):
        fr = {s: f_ratio(cells[f"r3p-c{c}-fitted"]["per_seed"][str(s)]["metrics"]) for s in SEEDS}
        deltas = [fr[s] - 1.05 * f_r4[s] for s in SEEDS]
        out["guards"][f"r3p-c{c} F vs 1.05x rung4-c0"] = {
            "median_excess": statistics.median(deltas),
            "pass": statistics.median(deltas) <= 0.0,
        }

    # ---- bars: loser-only clocks, deterministic re-derive (fitted) ----
    t0 = time.time()
    bars = {}
    for label, arm in [
        ("m1-r0.8", V2Arm("m1-r0.8-fitted", "m1", wcfg=with_uptake(OPERATING_WORKLOAD_V2, 0.8))),
        ("m2-p0.2", V2Arm("m2-p0.2-fitted", "m2", wcfg=with_abuse(OPERATING_WORKLOAD_V2, 0.2))),
    ]:
        lose_abs, lose_post, win_post = [], [], []
        for seed in SEEDS:
            r = run_arm_v2_once(arm, seed)
            log = r["log"]
            losers = {e[2] for e in log if e[0] == "alloc_lose"}
            winners = {e[2] for e in log if e[0] == "alloc_win"}
            t_ev = {e[2]: e[1] for e in log if e[0] in ("alloc_win", "alloc_lose")}
            first = {}
            for e in log:
                if e[0] == "request" and e[2] not in first:
                    first[e[2]] = e[1]
            for e in log:
                if e[0] != "definitive":
                    continue
                uid, t = e[2], e[1]
                if uid in losers and uid in first:
                    lose_abs.append(t - first[uid])
                    lose_post.append(t - t_ev[uid])
                elif uid in winners:
                    win_post.append(t - t_ev[uid])
        bars[label] = {
            "loser_absolute_p99": _pcts(lose_abs)["p99"],
            "loser_post_event_p99": _pcts(lose_post)["p99"],
            "winner_post_event_p99": _pcts(win_post)["p99"],
            "burst_floor_c0": 0.0,
            "registered_bar_note": (
                "post-event bar 3x burst floor is degenerate at c_push=0 "
                "(floor omitted winner-redemption drain) — chair item"
            ),
        }
        print(f"bars {label} derived ({time.time() - t0:.0f}s)", flush=True)
    out["bars"] = bars
    m3_sold = statistics.median(
        [cells["m3-fitted"]["per_seed"][str(s)]["metrics"]["goodput"]["seats_sold"] for s in SEEDS]
    )
    out["bars"]["m3"] = {
        "whole_run_bar": "not evaluable: sellout not reached",
        "seats_sold_median": m3_sold,
    }

    (REPORTS / "v7-grading.json").write_text(json.dumps(out, indent=1))
    print("== families (Holm within family) ==")
    for fam, rows in out["families"].items():
        for name, r in rows.items():
            print(
                f"  {name}: median {r['median']:+.4f} CI [{r['ci'][0]:+.4f},{r['ci'][1]:+.4f}] "
                f"p_holm={r['p_holm']:.4f} -> "
                f"{'distinguishable' if r['distinguishable_holm'] else 'did not help / not distinguishable'}"
            )
    print("== P1 ==")
    for k, v in out["p1"].items():
        print(f"  {k}: {v}")
    print("== guards ==")
    for k, v in out["guards"].items():
        print(f"  {k}: {v}")
    print("== bars ==")
    for k, v in out["bars"].items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    sys.exit(main())
