"""Run the P6 strategy arms (rungs 0-2) at the pre-registered 20 seeds.

Uses the committed calibration fit with the experiment scarcity knob
(25 seats/pool) and a spike-scale workload: the operating cohorts x10,
~13x overall oversubscription (hot pool ~40x under Zipf). The canonical
experiment workload lands with P7 — until then this is a preview of the
ladder's behavior, not a registered result.

Usage: PYTHONPATH=src python3 tools/run_p6_arms.py
"""

import dataclasses
import time
from pathlib import Path

from tatkal_sim.measure.fitting import load_fit, replica_config
from tatkal_sim.model.workload import OPERATING_WORKLOAD
from tatkal_sim.runner import Arm, render_report, sweep

FIT = Path("docs/specs/tatkal-spike-prototype/calibration/fit-2026-08-11.json")


def main() -> None:
    params = load_fit(FIT)["params"]
    scfg = dataclasses.replace(replica_config(params), seats_per_pool=25)  # scarcity knob

    spike = dataclasses.replace(OPERATING_WORKLOAD, n_pre_fire=300, n_t0_humans=2150, n_bots=150)

    arms = [
        Arm(name="rung0-naive", scfg=scfg, wcfg=spike, rung=0),
        Arm(name="rung1-bounded-fifo", scfg=scfg, wcfg=spike, rung=1),
        Arm(name="rung2-fast-fail", scfg=scfg, wcfg=spike, rung=2),
    ]
    seeds = list(range(1, 21))

    t = time.time()
    results = sweep(arms, seeds)
    elapsed = time.time() - t

    report = render_report(
        arms,
        results,
        ladder_pairs=[
            ("rung1-bounded-fifo", "rung0-naive"),
            ("rung2-fast-fail", "rung1-bounded-fifo"),
        ],
        baseline_pairs=[],
    )
    print(report)
    print(f"({len(arms)} arms x {len(seeds)} seeds in {elapsed:.1f}s)")


if __name__ == "__main__":
    main()
