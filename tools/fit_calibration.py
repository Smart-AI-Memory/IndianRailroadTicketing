#!/usr/bin/env python3
"""P4 offline fit runner — fits the server model to the 2026-08-11 CSV.

Runs the predeclared protocol end to end and writes the committed
artifacts:

  calibration/fit-2026-08-11.json  (params, residuals, LOLO, sharded check)
  calibration/fit-2026-08-11.svg   (measured vs fitted, both panels)

The unit suite then VALIDATES these artifacts (fast); this script is the
only thing that produces them. Deterministic: fixed seeds, fixed grids.

Usage: .venv/bin/python tools/fit_calibration.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from tatkal_sim.measure.fitting import (
    fit,
    knee_variant,
    load_calibration,
    model_curve,
    objective,
    refine,
    replica_config,
    replica_run,
    residuals,
    save_fit,
    write_fit_svg,
)

OUT_DIR = Path("docs/specs/tatkal-spike-prototype/calibration")
FINAL_SEEDS = (1, 2, 3)
FINAL_DURATION = 2.0


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--params",
        help="JSON param dict: skip search stages and evaluate/record these "
        "exact params (best-of selection per the chair's P4 ruling)",
    )
    args = ap.parse_args()

    targets, sharded64 = load_calibration()
    levels = [t.concurrency for t in targets]

    if args.params:
        import json as _json

        params = _json.loads(args.params)
        loss = float("nan")
        log(f"=== pinned params (best-of selection): {params} ===")
        return finish(params, loss, targets, sharded64, levels)

    log("=== stage 1: grid search (1 seed, 1 s) — refinement round grid ===")
    # Round-2 grid (chair-directed refinement, D8 miss path): centered on
    # the round-1 optimum; app-tail replaced by the hold-stall mechanism,
    # app_sigma freed as a fit parameter.
    grid = {
        "workers": [2, 3],
        "service_ms": [0.06, 0.08, 0.10],
        "congestion_k": [0.18, 0.24, 0.32],
        "gamma": [0.60, 0.67, 0.75],
        "hold_ms": [0.07, 0.09, 0.12],
        "sigma": [0.35, 0.60, 0.90],
        "stall_mean_ms": [0.0, 5.0, 15.0],
        "tail_mean_ms": [0.0],
    }
    params, loss = fit(targets, grid=grid, seeds=(1,), duration=1.0, log=log)
    log(f"grid best: {params} loss={loss:.4f}")

    log("=== stage 2: local refinement ===")
    params, loss = refine(params, targets, steps=2, seeds=(1,), duration=1.0, log=log)
    log(f"refined: {params} loss={loss:.4f}")
    return finish(params, loss, targets, sharded64, levels)


def finish(params: dict, loss: float, targets, sharded64, levels) -> int:
    log("=== stage 3: final evaluation (3 seeds, 2 s) ===")
    curve = model_curve(replica_config(params), levels, seeds=FINAL_SEEDS, duration=FINAL_DURATION)
    final_loss = objective(curve, targets)
    res = residuals(curve, targets)
    misses = {
        c: r
        for c, r in res.items()
        if not (0.75 <= r["thr_ratio"] <= 1.25 and 0.75 <= r["p99_ratio"] <= 1.25)
    }
    for t in targets:
        m, r = curve[t.concurrency], res[t.concurrency]
        log(
            f"C={t.concurrency:<4} thr {m['thr']:7.0f}/{t.thr:7.0f} ({r['thr_ratio']:.2f})"
            f"  p99 {m['p99']:8.2f}/{t.p99:8.2f} ({r['p99_ratio']:.2f})"
            f"  convoy {m['convoy_p99']:8.2f}/{t.convoy_p99:8.2f}"
        )

    log("=== stage 4: leave-one-level-out guard ===")
    lolo = {}
    for held in levels:
        sub = [t for t in targets if t.concurrency != held]
        p_lolo, _ = refine(params, sub, steps=1, seeds=(1,), duration=1.0)
        held_curve = model_curve(replica_config(p_lolo), [held], seeds=(1,), duration=1.0)
        t = next(t for t in targets if t.concurrency == held)
        lolo[held] = {
            "thr_ratio": held_curve[held]["thr"] / t.thr,
            "p99_ratio": held_curve[held]["p99"] / t.p99,
        }
        log(
            f"  held-out C={held}: thr x{lolo[held]['thr_ratio']:.2f} "
            f"p99 x{lolo[held]['p99_ratio']:.2f}"
        )

    log("=== stage 5: sharded8 identification check ===")
    sh = replica_run(
        64, replica_config(params, sharded=True), seed=1, duration=FINAL_DURATION, sharded_pools=8
    )
    sharded_check = {
        "model_thr": sh["thr"],
        "measured_thr": sharded64["thr"],
        "model_p99": sh["p99"],
        "measured_p99": sharded64["p99"],
    }
    log(
        f"  sharded64 model thr={sh['thr']:.0f} p99={sh['p99']:.1f} "
        f"vs measured thr={sharded64['thr']:.0f} p99={sharded64['p99']:.1f}"
    )

    log("=== stage 6: knee variants sanity ===")
    variants = {}
    for name in ("fitted", "plateau", "cliff"):
        vc = model_curve(knee_variant(name, params), [2, 64, 256], seeds=(1,), duration=1.0)
        variants[name] = {c: round(v["thr"]) for c, v in vc.items()}
        log(
            f"  {name}: thr(2)={variants[name][2]} thr(64)={variants[name][64]} "
            f"thr(256)={variants[name][256]}"
        )

    save_fit(
        OUT_DIR / "fit-2026-08-11.json",
        params,
        final_loss,
        res,
        lolo,
        {
            "misses_beyond_25pct": misses,
            # Chair ruling (2026-08-11, P4 miss path): ONE refinement round
            # (hold-stall mechanism + freed sigma), then accept best-of with
            # documented deviations. Residual misses after this round are
            # therefore chair-accepted by that ruling.
            "chair_accepted_deviations": sorted(misses, key=int),
            "chair_ruling": "2026-08-11: one refinement round then accept best-of "
            "with documented deviations (see decisions.md)",
            "sharded64_check": sharded_check,
            "variant_thr": variants,
            "seeds": list(FINAL_SEEDS),
            "duration_s": FINAL_DURATION,
            "protocol": "design.md fit protocol (D10/S8): joint log-RMSE on medians; "
            "target +/-25%/level; LOLO +/-40%; misses -> chair review",
            "model_note": "best-of selection per chair ruling: round-1 params "
            "(congestion app_time x (1 + k*conns^gamma), 1% app-tail 5ms, sigma 0.6) "
            "beat the round-2 hold-stall variant (final loss 0.370 vs 0.611, "
            "7 vs 9 miss levels); hold-stall mechanism retained in the model, "
            "inert (stall params 0) in the fitted profile",
        },
    )
    write_fit_svg(OUT_DIR / "fit-2026-08-11.svg", targets, curve)
    log(
        f"artifacts written to {OUT_DIR}/  (loss={final_loss:.4f}, "
        f"{len(misses)} level(s) beyond +/-25%)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
