"""Paired per-seed statistics (task P5.2; D6, D10/S3+S4+S7).

R1's shared seeds make every arm-vs-arm comparison a PAIRED design:

    delta_i = metric(candidate, seed_i) - metric(baseline, seed_i)

The decision statistic is the distribution of delta_i across >= 20 seeded
replications, with a bootstrap 95% CI on its MEDIAN — B=10,000, percentile
method, drawn from the dedicated seeded `stats` RNG stream so CIs are
byte-identical across reruns (R1).

There is deliberately NO CI-overlap comparison anywhere in this module —
requirements.md R6 "Statistical decision rule" forbids it, and the
cleanest enforcement is for the disallowed test to have no API to call.

Both comparison families (D10/S3) are expressed through the same
`paired_compare`: rung k vs rung k-1 (R4's marginal delta) and any
adaptive/ML arm vs the strong baseline (R5). The caller picks the pair;
the statistics are identical.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from tatkal_sim.core.rng import derive_stream

B_RESAMPLES = 10_000  # D10/S7: pre-registered bootstrap parameters
CI_ALPHA = 0.05
MIN_SEEDS = 20  # R6: fewer replications cannot separate a 10% effect


@dataclass(frozen=True)
class PairedResult:
    metric: str
    n_seeds: int
    deltas: tuple[float, ...]
    median_delta: float
    ci_lo: float
    ci_hi: float
    below_replication_floor: bool  # < MIN_SEEDS: smoke only, never a claim

    @property
    def includes_zero(self) -> bool:
        return self.ci_lo <= 0.0 <= self.ci_hi

    def verdict(self) -> str:
        """Pre-registered language: 'did not help' when the CI includes 0."""
        if self.below_replication_floor:
            return "SMOKE (below pre-registered replication count)"
        return "did not help (CI includes zero)" if self.includes_zero else "distinguishable"


def bootstrap_median_ci(
    deltas: list[float], *, stats_seed: int, b: int = B_RESAMPLES, alpha: float = CI_ALPHA
) -> tuple[float, float]:
    """Percentile bootstrap CI of the median, seeded -> byte-identical."""
    rng = derive_stream(stats_seed, "stats")
    n = len(deltas)
    medians = sorted(
        statistics.median(deltas[int(rng.random() * n)] for _ in range(n)) for _ in range(b)
    )
    lo_i = int((alpha / 2) * b)
    hi_i = min(b - 1, int((1 - alpha / 2) * b))
    return medians[lo_i], medians[hi_i]


def paired_compare(
    metric_name: str,
    candidate: dict[int, float],
    baseline: dict[int, float],
    *,
    stats_seed: int = 0,
) -> PairedResult:
    """Per-seed paired deltas over the COMMON seeds of the two arms.

    `candidate`/`baseline`: {seed: metric_value}. Seeds must match — a
    missing seed on either side is an error, not a silent drop, because a
    silently unpaired comparison is exactly the mistake D6 forbids.
    """
    if set(candidate) != set(baseline):
        raise ValueError(
            f"unpaired seeds: candidate {sorted(candidate)} vs baseline {sorted(baseline)}"
        )
    seeds = sorted(candidate)
    deltas = [candidate[s] - baseline[s] for s in seeds]
    lo, hi = bootstrap_median_ci(deltas, stats_seed=stats_seed)
    return PairedResult(
        metric=metric_name,
        n_seeds=len(seeds),
        deltas=tuple(deltas),
        median_delta=statistics.median(deltas),
        ci_lo=lo,
        ci_hi=hi,
        below_replication_floor=len(seeds) < MIN_SEEDS,
    )
