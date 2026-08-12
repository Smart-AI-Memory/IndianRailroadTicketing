"""V5.1 (tatkal-v2): engineering baselines under the v2 population.

Rungs 0, 2, 4 x {fitted, plateau, cliff} x 20 seeds (D12/D13.1/D17).
Writes per-seed metrics to docs/specs/tatkal-v2/reports/
v5-baselines-data.json — the paired-seed archive every V6 comparison
draws from. Evaluated run: full seed count, no SMOKE banner.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from tatkal_sim.runner import result_digest
from tatkal_sim.runner_v2 import V2Arm, run_arm_v2_once

OUT = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "specs"
    / "tatkal-v2"
    / "reports"
    / "v5-baselines-data.json"
)

SEEDS = list(range(20))  # D13.1 universal floor
RUNGS = (0, 2, 4)
VARIANTS = ("fitted", "plateau", "cliff")


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data: dict = {"seeds": SEEDS, "arms": {}}
    t_start = time.time()
    for rung in RUNGS:
        for variant in VARIANTS:
            name = f"rung{rung}-{variant}"
            arm = V2Arm(name, "eng", rung=rung, variant=variant)
            per_seed = {}
            for seed in SEEDS:
                r = run_arm_v2_once(arm, seed)
                per_seed[seed] = r["metrics"]
            data["arms"][name] = {
                "kind": "eng",
                "rung": rung,
                "variant": variant,
                "population": "v2-operating (D13)",
                "per_seed": per_seed,
                "digest": result_digest(per_seed[0]),
            }
            g0 = per_seed[0]["goodput"]
            print(
                f"{name}: seed0 sold={g0['seats_sold']} "
                f"goodput={g0['sold_per_s']:.0f}/s "
                f"[{time.time() - t_start:.0f}s elapsed]",
                flush=True,
            )
    data["elapsed_s"] = round(time.time() - t_start, 1)
    OUT.write_text(json.dumps(data))
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KiB)")


if __name__ == "__main__":
    sys.exit(main())
