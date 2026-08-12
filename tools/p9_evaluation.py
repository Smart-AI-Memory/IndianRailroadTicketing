#!/usr/bin/env python3
"""P9 — the pre-registered evaluation (tasks P9.1 + P9.2 data).

Runs the full ladder under the ratified protocol and writes
`reports/p9-evaluation-data.json`:

- stage 1: rungs 0-6 x knee variants (fitted/plateau/cliff) x 20 seeds;
- stage 2: success criteria evaluated EXACTLY as ratified (D8 values,
  D11 populations, D15 operand, D14 operating point) on the fitted
  variant — met-or-not, never adjusted;
- stage 3: paired verdicts (D6) for both comparison families;
- stage 4: one-at-a-time sensitivity sweep (knee variant, Zipf s, retry
  policy, bot share) on rung2 vs rung4, 10 seeds per cell — reduced
  replication is LABELLED, per the no-silent-caps rule.

The write-up (RESULTS.md) is composed from this data; this script never
renders prose.

Usage: .venv/bin/python tools/p9_evaluation.py
"""

from __future__ import annotations

import dataclasses as dc
import json
import statistics as st
import sys
from pathlib import Path

from tatkal_sim.measure.stats import paired_compare
from tatkal_sim.model.users import ClientConfig
from tatkal_sim.model.workload import OPERATING_WORKLOAD
from tatkal_sim.runner import ladder_arm, metric_series, run_arm_once, sweep

OUT = Path("docs/specs/tatkal-spike-prototype/reports/p9-evaluation-data.json")
SEEDS = list(range(1, 21))
SENS_SEEDS = list(range(1, 11))  # sensitivity: 10 seeds, labelled reduced

# ratified constants (D8/D11/D14/D15) — restated, never derived from results
BAR_P99_S = 0.0342  # 50 x p99_knee
GOODPUT_GUARD = 0.8 * 4865.0  # 0.8 x C_peak (seats/s == calibration ops/s: 1 op = 1 seat)
AMP_BAR = 1.5


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def med(results: dict, path: str) -> float | None:
    vals = []
    for m in results.values():
        v: object = m
        for part in path.split("."):
            v = v[part]  # type: ignore[index]
        if v is not None:  # settling_time_s is None when never settled
            vals.append(float(v))  # type: ignore[arg-type]
    return st.median(vals) if vals else None


def main() -> int:
    data: dict = {"seeds": SEEDS, "sens_seeds": SENS_SEEDS}

    log("=== stage 1: main sweep — 7 rungs x 3 variants x 20 seeds ===")
    main_sweep: dict = {}
    for variant in ("fitted", "plateau", "cliff"):
        arms = [ladder_arm(k, variant=variant) for k in range(7)]
        res = sweep(arms, SEEDS)
        for arm in arms:
            r = res[arm.name]
            main_sweep[arm.name] = {
                "variant": variant,
                "rung": arm.rung,
                "res_win_p99": med(r, "resolution.winners.p99"),
                "res_rej_p99": med(r, "resolution.rejected.p99"),
                "ttda_win_p99": med(r, "ttda.winners.p99"),
                "goodput": med(r, "goodput.sold_per_s"),
                "retry_amp": med(r, "retry_amplification"),
                "hard_err": med(r, "hard_error_rate"),
                "wasted": med(r, "wasted_work_ratio"),
                "settling": med(r, "settling_time_s"),
                "fairness_F": st.median(
                    m["fairness"]["bots_win_share"] / m["fairness"]["bots_population_share"]
                    for m in r.values()
                ),
                "violations": sum(len(m["inventory"]["violations"]) for m in r.values()),
            }
            log(
                f"  {arm.name}: win {main_sweep[arm.name]['res_win_p99']*1000:.1f}ms "
                f"rej {main_sweep[arm.name]['res_rej_p99']*1000:.1f}ms "
                f"goodput {main_sweep[arm.name]['goodput']:.0f}"
            )
        if variant == "fitted":
            fitted_results = res
    data["main_sweep"] = main_sweep

    log("=== stage 2: ratified success criteria (fitted variant) ===")
    criteria: dict = {}
    for k in range(7):
        m = main_sweep[f"rung{k}"]
        criteria[f"rung{k}"] = {
            "win_p99_le_bar": m["res_win_p99"] <= BAR_P99_S,
            "rej_p99_le_bar": m["res_rej_p99"] <= BAR_P99_S,
            "rej_le_win": m["res_rej_p99"] <= m["res_win_p99"],
            "goodput_ge_guard": m["goodput"] >= GOODPUT_GUARD,
            "inventory_clean": m["violations"] == 0,
            "amp_lt_bar": m["retry_amp"] < AMP_BAR,
        }
    data["criteria"] = criteria

    log("=== stage 3: paired verdicts, both families (fitted) ===")
    verdicts: dict = {}
    metrics = ("resolution.rejected.p99", "resolution.winners.p99", "goodput.sold_per_s")
    pairs = [(f"rung{k}", f"rung{k-1}", "ladder") for k in range(1, 7)]
    pairs += [(f"rung{k}", "rung2", "baseline") for k in (3, 4, 5, 6)]
    for cand, base, family in pairs:
        for path in metrics:
            r = paired_compare(
                path,
                metric_series(fitted_results[cand], path),
                metric_series(fitted_results[base], path),
            )
            verdicts[f"{family}:{cand}vs{base}:{path}"] = {
                "median_delta": r.median_delta,
                "ci": [r.ci_lo, r.ci_hi],
                "verdict": r.verdict(),
            }
    data["verdicts"] = verdicts

    log("=== stage 4: sensitivity (one-at-a-time, 10 seeds, rung2 vs rung4) ===")

    def cell(name: str, variant="fitted", zipf=None, p_retry=None, bots=None):
        wcfg = OPERATING_WORKLOAD
        if zipf is not None:
            wcfg = dc.replace(wcfg, zipf_s=zipf)
        if bots is not None:
            wcfg = dc.replace(wcfg, n_bots=bots)
        ccfg = ClientConfig(p_retry_after_reject=p_retry) if p_retry else ClientConfig()
        out = {}
        for k in (2, 4):
            arm = dc.replace(ladder_arm(k, variant=variant), wcfg=wcfg, ccfg=ccfg)
            rr = {s: run_arm_once(arm, s) for s in SENS_SEEDS}
            out[f"rung{k}"] = {
                "rej_p99": med(rr, "resolution.rejected.p99"),
                "goodput": med(rr, "goodput.sold_per_s"),
            }
        out["headline_holds"] = (
            out["rung4"]["rej_p99"] <= BAR_P99_S
            and out["rung4"]["rej_p99"] < out["rung2"]["rej_p99"]
        )
        log(
            f"  {name}: rung4 rej {out['rung4']['rej_p99']*1000:.1f}ms "
            f"holds={out['headline_holds']}"
        )
        return out

    sens = {"center": cell("center")}
    sens["variant=plateau"] = cell("variant=plateau", variant="plateau")
    sens["variant=cliff"] = cell("variant=cliff", variant="cliff")
    sens["zipf=0.7"] = cell("zipf=0.7", zipf=0.7)
    sens["zipf=1.5"] = cell("zipf=1.5", zipf=1.5)
    sens["p_retry=0.3"] = cell("p_retry=0.3", p_retry=0.3)
    sens["bots=75"] = cell("bots=75", bots=75)
    sens["bots=300"] = cell("bots=300", bots=300)
    data["sensitivity"] = sens

    OUT.write_text(json.dumps(data, indent=1, sort_keys=True))
    log(f"data written: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
