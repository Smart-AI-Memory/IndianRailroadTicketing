"""V6 (tatkal-v2): mechanism and sweep runs — the registered cells.

    V6.1  M1 x r_reg {0.5, 0.8, 0.95}      x 3 variants x 20 seeds
    V6.2  M2 x p {0, 0.1, 0.2, 0.4}        x 3 variants x 20 seeds
    V6.3  M3                                x 3 variants x 20 seeds
    V6.4  R3' x c_push {0, .25, .5, 1, 2}   x 3 variants x 20 seeds

780 runs total (D13.1: 20-seed floor everywhere). Per-seed archive
carries the v1 R6 metrics dict plus the v2 metrics (two-clock,
controller-level fairness, per-tranche F for M3, taxonomy) — raw logs
are derived at run time and not stored.

Writes docs/specs/tatkal-v2/reports/v6-sweeps-data.json.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from tatkal_sim.measure.metrics_v2 import (
    draw_share_advantage,
    error_taxonomy,
    per_tranche_fairness,
    two_clock,
)
from tatkal_sim.model.workload_v2 import OPERATING_WORKLOAD_V2, with_abuse, with_uptake
from tatkal_sim.runner_v2 import C_PUSH_GRID, V2Arm, run_arm_v2_once

OUT = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "specs"
    / "tatkal-v2"
    / "reports"
    / "v6-sweeps-data.json"
)

SEEDS = list(range(20))
VARIANTS = ("fitted", "plateau", "cliff")


def cells() -> list[V2Arm]:
    arms: list[V2Arm] = []
    for variant in VARIANTS:
        for r in (0.5, 0.8, 0.95):
            arms.append(
                V2Arm(
                    f"m1-r{r}-{variant}",
                    "m1",
                    wcfg=with_uptake(OPERATING_WORKLOAD_V2, r),
                    variant=variant,
                )
            )
        for p in (0.0, 0.1, 0.2, 0.4):
            arms.append(
                V2Arm(
                    f"m2-p{p}-{variant}",
                    "m2",
                    wcfg=with_abuse(OPERATING_WORKLOAD_V2, p),
                    variant=variant,
                )
            )
        arms.append(V2Arm(f"m3-{variant}", "m3", variant=variant))
        for c in C_PUSH_GRID:
            arms.append(V2Arm(f"r3p-c{c}-{variant}", "r3p", c_push=c, variant=variant))
    return arms


def run_cell(arm: V2Arm) -> dict:
    per_seed = {}
    for seed in SEEDS:
        r = run_arm_v2_once(arm, seed)
        log, intents = r["log"], r["intents"]
        rec: dict = {"metrics": r["metrics"]}
        if arm.kind in ("m1", "m2"):
            rec["two_clock"] = two_clock(log, intents)
            rec["fairness"] = draw_share_advantage(log, intents)
            rec["taxonomy"] = error_taxonomy(log)
        elif arm.kind == "m3":
            rec["per_tranche"] = per_tranche_fairness(log, intents, arm.wcfg)
            rec["taxonomy"] = error_taxonomy(log)
        per_seed[seed] = rec
    return per_seed


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data: dict = {"seeds": SEEDS, "cells": {}}
    t0 = time.time()
    arms = cells()
    for i, arm in enumerate(arms, 1):
        data["cells"][arm.name] = {
            "kind": arm.kind,
            "variant": arm.variant,
            "r_reg": arm.wcfg.r_reg,
            "abuse_p": arm.wcfg.abuse_p,
            "c_push": arm.c_push,
            "per_seed": run_cell(arm),
        }
        print(f"[{i}/{len(arms)}] {arm.name} done ({time.time() - t0:.0f}s)", flush=True)
    data["elapsed_s"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(data))
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KiB)")


if __name__ == "__main__":
    sys.exit(main())
