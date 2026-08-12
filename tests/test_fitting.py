"""P4 acceptance — fit artifacts meet the predeclared protocol (D10/S8).

The fit itself runs offline (tools/fit_calibration.py) and commits its
artifacts; this suite VALIDATES them: residual bands, the LOLO guard,
live revalidation of two levels, knee-variant shapes, and the plot's
existence. A miss beyond +/-25% fails here unless the artifact records a
chair-accepted deviation — the protocol's "never a silent bad fit".
"""

from pathlib import Path

import pytest

from tatkal_sim.measure.fitting import (
    KNEE_VARIANTS,
    knee_variant,
    load_calibration,
    load_fit,
    model_curve,
    replica_config,
    replica_run,
)

FIT_JSON = Path("docs/specs/tatkal-spike-prototype/calibration/fit-2026-08-11.json")
FIT_SVG = Path("docs/specs/tatkal-spike-prototype/calibration/fit-2026-08-11.svg")

pytestmark = pytest.mark.skipif(
    not FIT_JSON.exists(), reason="fit artifacts not yet generated (tools/fit_calibration.py)"
)


def fit_data():
    return load_fit(FIT_JSON)


def test_calibration_csv_loads_nine_levels():
    targets, sharded = load_calibration()
    assert [t.concurrency for t in targets] == [1, 2, 4, 8, 16, 32, 64, 128, 256]
    assert sharded["thr"] > 0


def test_replica_is_deterministic():
    scfg = replica_config(fit_data()["params"])
    a = replica_run(8, scfg, seed=42, duration=0.5)
    b = replica_run(8, scfg, seed=42, duration=0.5)
    assert a == b


def test_residuals_within_25pct_or_chair_accepted():
    data = fit_data()
    accepted = set(map(int, data["meta"].get("chair_accepted_deviations", [])))
    bad = []
    for c, r in data["residuals"].items():
        ok = 0.75 <= r["thr_ratio"] <= 1.25 and 0.75 <= r["p99_ratio"] <= 1.25
        if not ok and int(c) not in accepted:
            bad.append((c, r))
    assert not bad, f"levels beyond +/-25% without chair acceptance: {bad}"


def test_lolo_guard_within_40pct():
    data = fit_data()
    accepted = set(map(int, data["meta"].get("chair_accepted_deviations", [])))
    bad = {
        c: r
        for c, r in data["lolo"].items()
        if not (0.6 <= r["thr_ratio"] <= 1.4 and 0.6 <= r["p99_ratio"] <= 1.4)
        and int(c) not in accepted
    }
    assert not bad, f"LOLO guard failed: {bad}"


def test_live_revalidation_of_two_levels():
    """Re-run the committed params at C=1 and C=64 with the recorded seeds;
    the recorded residuals must reproduce (drift here = artifact rot)."""
    data = fit_data()
    scfg = replica_config(data["params"])
    seeds = tuple(data["meta"]["seeds"])
    dur = data["meta"]["duration_s"]
    targets = {t.concurrency: t for t in load_calibration()[0]}
    curve = model_curve(scfg, [1, 64], seeds=seeds, duration=dur)
    for c in (1, 64):
        rec = data["residuals"][str(c)]
        assert curve[c]["thr"] / targets[c].thr == pytest.approx(rec["thr_ratio"], rel=1e-9)
        assert curve[c]["p99"] / targets[c].p99 == pytest.approx(rec["p99_ratio"], rel=1e-9)


def test_knee_variants_have_their_shapes():
    params = fit_data()["params"]
    assert KNEE_VARIANTS == ("fitted", "plateau", "cliff")
    thr = {
        name: {
            c: model_curve(knee_variant(name, params), [c], seeds=(1,), duration=0.5)[c]["thr"]
            for c in (64, 256)
        }
        for name in KNEE_VARIANTS
    }
    # plateau holds capacity flat past the knee; cliff collapses hard;
    # fitted sits between (it declines, but not cliff-fast)
    assert thr["plateau"][256] >= 0.8 * thr["plateau"][64]
    assert thr["cliff"][256] < 0.5 * thr["cliff"][64]
    assert thr["cliff"][256] < thr["fitted"][256] <= thr["plateau"][256] * 1.05


def test_fit_plot_exists_and_is_a_plot():
    svg = FIT_SVG.read_text()
    assert "<svg" in svg and "polyline" in svg and "circle" in svg
