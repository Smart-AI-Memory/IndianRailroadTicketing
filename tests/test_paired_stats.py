"""P5.2 acceptance — paired deltas: known effect covered, byte-identical
CIs, unpaired seeds rejected, and no CI-overlap API to misuse."""

import pytest

from tatkal_sim.measure import stats as stats_mod
from tatkal_sim.measure.stats import MIN_SEEDS, paired_compare


def series(effect: float, seeds=range(1, 21)):
    baseline = {s: 100.0 + (s % 5) for s in seeds}
    candidate = {s: v + effect for s, v in baseline.items()}
    return candidate, baseline


def test_known_effect_is_recovered_exactly():
    cand, base = series(-10.0)
    r = paired_compare("m", cand, base)
    assert r.median_delta == pytest.approx(-10.0)
    assert r.ci_lo == pytest.approx(-10.0) and r.ci_hi == pytest.approx(-10.0)
    assert not r.includes_zero
    assert r.verdict() == "distinguishable"
    assert not r.below_replication_floor  # 20 seeds meets the floor


def test_zero_effect_reads_did_not_help():
    cand, base = series(0.0)
    r = paired_compare("m", cand, base)
    assert r.includes_zero
    assert r.verdict() == "did not help (CI includes zero)"


def test_noisy_effect_ci_covers_truth():
    # per-seed noise around a true -5 shift; pairing removes the seed term
    base = {s: 100.0 + 7.0 * (s % 7) for s in range(1, 21)}
    cand = {s: v - 5.0 + ((s * 13) % 3 - 1) for s, v in base.items()}
    r = paired_compare("m", cand, base)
    assert r.ci_lo <= -5.0 <= r.ci_hi


def test_cis_are_byte_identical_across_reruns():
    cand, base = series(-3.0)
    a = paired_compare("m", cand, base, stats_seed=7)
    b = paired_compare("m", cand, base, stats_seed=7)
    assert a == b  # frozen dataclass, exact equality
    assert repr(a.ci_lo) == repr(b.ci_lo) and repr(a.ci_hi) == repr(b.ci_hi)


def test_unpaired_seeds_are_an_error_not_a_silent_drop():
    cand, base = series(-1.0)
    del cand[3]
    with pytest.raises(ValueError, match="unpaired"):
        paired_compare("m", cand, base)


def test_below_replication_floor_is_flagged():
    cand, base = series(-10.0, seeds=range(1, 6))
    r = paired_compare("m", cand, base)
    assert r.below_replication_floor
    assert "SMOKE" in r.verdict()
    assert MIN_SEEDS == 20  # the pre-registered floor itself


def test_no_ci_overlap_api_exists():
    """R6 forbids CI-overlap testing; the cleanest enforcement is that the
    module offers nothing to call."""
    names = [n.lower() for n in dir(stats_mod)]
    assert not any("overlap" in n for n in names)
