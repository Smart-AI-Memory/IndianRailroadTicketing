"""W5 (tatkal-v3): the registered sweep — 63 cells x 20 seeds.

Cell list per design §Cell-budget as amended by D20, gated by D23:
  A1  c_verify {0.25,1,4} x p {0,.1,.2,.4}, fitted            12
  A2  d {0.1,0.5,2,15}   x p {0,.1,.2,.4}, fitted             16
  A3  profile {deadline,uniform} x p {0,.1,.2,.4}, fitted      8
  arm-center bracketing (3 arms x plateau/cliff)                6
  R3  bursts: m1 r0.8 / m2 p0.1 x c_push {.25,.5,1,2}, fitted  8
  R3  bracketing at c_push=1 (2 arms x plateau/cliff)           4
  M3  p_retry {.25,.5,1} x 3 variants                           9

v2 record cells (c_push = 0, p_retry = 0, unmitigated M2) are reused,
never re-run (center-cell rule, D3/R6).

Writes docs/specs/tatkal-v3/reports/w5-sweeps-data.json.
"""

from __future__ import annotations

import dataclasses as dc
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
from tatkal_sim.measure.metrics_v3 import honest_cost
from tatkal_sim.model.users import ClientConfig
from tatkal_sim.model.workload_v2 import OPERATING_WORKLOAD_V2, with_abuse, with_uptake
from tatkal_sim.runner_v2 import V2Arm, run_arm_v2_once
from tatkal_sim.runner_v3 import V3Arm, run_arm_v3_once
from tatkal_sim.strategies.mitigation import C_VERIFY_GRID, D_GRID

OUT = Path(__file__).resolve().parent.parent / "docs" / "specs" / "tatkal-v3" / "reports"
SEEDS = list(range(20))
P_GRID = (0.0, 0.1, 0.2, 0.4)
C_PUSH_POINTS = (0.25, 0.5, 1.0, 2.0)
P_RETRY = (0.25, 0.5, 1.0)


def v3_cells() -> list[V3Arm]:
    arms: list[V3Arm] = []
    for cv in C_VERIFY_GRID:
        for p in P_GRID:
            arms.append(
                V3Arm(
                    f"a1-cv{cv}-p{p}-fitted",
                    mitigation="verify",
                    c_verify=cv,
                    wcfg=with_abuse(OPERATING_WORKLOAD_V2, p),
                )
            )
    for d in D_GRID:
        for p in P_GRID:
            arms.append(
                V3Arm(
                    f"a2-d{d}-p{p}-fitted",
                    mitigation="deposit",
                    d=d,
                    wcfg=with_abuse(OPERATING_WORKLOAD_V2, p),
                )
            )
    for prof in ("deadline", "uniform"):
        for p in P_GRID:
            arms.append(
                V3Arm(
                    f"a3-{prof}-p{p}-fitted",
                    mitigation="regbound",
                    wcfg=dc.replace(with_abuse(OPERATING_WORKLOAD_V2, p), reg_profile=prof),
                )
            )
    for variant in ("plateau", "cliff"):
        arms.append(
            V3Arm(
                f"a1-cv1.0-p0.1-{variant}",
                mitigation="verify",
                c_verify=1.0,
                wcfg=with_abuse(OPERATING_WORKLOAD_V2, 0.1),
                variant=variant,
            )
        )
        arms.append(
            V3Arm(
                f"a2-d0.5-p0.1-{variant}",
                mitigation="deposit",
                d=0.5,
                wcfg=with_abuse(OPERATING_WORKLOAD_V2, 0.1),
                variant=variant,
            )
        )
        arms.append(
            V3Arm(
                f"a3-deadline-p0.1-{variant}",
                mitigation="regbound",
                wcfg=with_abuse(OPERATING_WORKLOAD_V2, 0.1),
                variant=variant,
            )
        )
    return arms


def v2_cells() -> list[V2Arm]:
    arms: list[V2Arm] = []
    for c in C_PUSH_POINTS:
        arms.append(
            V2Arm(
                f"r3-m1-c{c}-fitted",
                "m1",
                wcfg=with_uptake(OPERATING_WORKLOAD_V2, 0.8),
                c_push=c,
            )
        )
        arms.append(
            V2Arm(
                f"r3-m2-c{c}-fitted",
                "m2",
                wcfg=with_abuse(OPERATING_WORKLOAD_V2, 0.1),
                c_push=c,
            )
        )
    for variant in ("plateau", "cliff"):
        arms.append(
            V2Arm(
                f"r3-m1-c1.0-{variant}",
                "m1",
                wcfg=with_uptake(OPERATING_WORKLOAD_V2, 0.8),
                c_push=1.0,
                variant=variant,
            )
        )
        arms.append(
            V2Arm(
                f"r3-m2-c1.0-{variant}",
                "m2",
                wcfg=with_abuse(OPERATING_WORKLOAD_V2, 0.1),
                c_push=1.0,
                variant=variant,
            )
        )
    for pr in P_RETRY:
        for variant in ("fitted", "plateau", "cliff"):
            arms.append(
                V2Arm(
                    f"m3-pr{pr}-{variant}",
                    "m3",
                    ccfg=ClientConfig(p_retry_after_reject=pr),
                    variant=variant,
                )
            )
    return arms


def _stream_counts(log: list) -> dict:
    names = (
        "verify_start",
        "verify_done",
        "verify_missed",
        "stake_in",
        "stake_refund",
        "stake_return",
        "stake_forfeit",
        "ineligible",
        "reg_submit",
        "reg_done",
    )
    return {n: sum(1 for e in log if e[0] == n) for n in names}


def _b3_b6(log: list, t0: float, reg_window: float) -> dict:
    """Gate B measured quantities: B3 last-verification completion
    offset; B6 worst registration wait in the final decile of W."""
    vd = [e[1] for e in log if e[0] == "verify_done"]
    b3 = max(vd) - t0 if vd else None
    submits = {e[2]: e[1] for e in log if e[0] == "reg_submit"}
    decile_start = t0 - 0.1 * reg_window
    waits = [
        e[1] - submits[e[2]]
        for e in log
        if e[0] == "reg_done" and e[2] in submits and submits[e[2]] >= decile_start
    ]
    b6 = max(waits) if waits else None
    return {"b3_last_verify_offset": b3, "b6_worst_final_decile_reg_wait": b6}


def run_v3_cell(arm: V3Arm) -> dict:
    per_seed = {}
    for seed in SEEDS:
        r = run_arm_v3_once(arm, seed)
        log, intents = r["log"], r["intents"]
        wcfg_t0 = (
            arm.wcfg.t0
            if arm.mitigation != "regbound"
            else max(arm.wcfg.t0, arm.wcfg.reg_window + 30.0)
        )
        per_seed[seed] = {
            "metrics": r["metrics"],
            "two_clock": two_clock(log, intents),
            "fairness": draw_share_advantage(log, intents),
            "taxonomy": error_taxonomy(log),
            "honest_cost": honest_cost(log, intents, t0=wcfg_t0),
            "streams": _stream_counts(log),
            "gate_b": _b3_b6(log, wcfg_t0, arm.wcfg.reg_window),
        }
    return per_seed


def run_v2_cell(arm: V2Arm) -> dict:
    per_seed = {}
    for seed in SEEDS:
        r = run_arm_v2_once(arm, seed)
        log, intents = r["log"], r["intents"]
        rec: dict = {"metrics": r["metrics"], "taxonomy": error_taxonomy(log)}
        if arm.kind in ("m1", "m2"):
            rec["two_clock"] = two_clock(log, intents)
            rec["fairness"] = draw_share_advantage(log, intents)
        elif arm.kind == "m3":
            rec["per_tranche"] = per_tranche_fairness(log, intents, arm.wcfg)
        per_seed[seed] = rec
    return per_seed


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    data: dict = {"seeds": SEEDS, "cells": {}}
    t_start = time.time()
    v3, v2 = v3_cells(), v2_cells()
    total = len(v3) + len(v2)
    assert total == 63, f"registered plan is 63 cells, built {total}"
    i = 0
    for arm in v3:
        i += 1
        data["cells"][arm.name] = {
            "family": arm.mitigation,
            "variant": arm.variant,
            "per_seed": run_v3_cell(arm),
        }
        print(f"[{i}/{total}] {arm.name} done ({time.time() - t_start:.0f}s)", flush=True)
    for arm in v2:
        i += 1
        data["cells"][arm.name] = {
            "family": arm.kind,
            "variant": arm.variant,
            "c_push": arm.c_push,
            "per_seed": run_v2_cell(arm),
        }
        print(f"[{i}/{total}] {arm.name} done ({time.time() - t_start:.0f}s)", flush=True)
    data["elapsed_s"] = round(time.time() - t_start, 1)
    out = OUT / "w5-sweeps-data.json"
    out.write_text(json.dumps(data))
    print(f"wrote {out} ({out.stat().st_size // 1024} KiB)")


if __name__ == "__main__":
    sys.exit(main())
