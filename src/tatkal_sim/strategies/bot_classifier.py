"""Rung 6 — bot classification on timing features (R4, R7.1; task P8.1).

Features are per-user TIMING only — the classifier never sees cohorts,
pools, or generator parameters:

- `offset`: first post-T0 request time − T0 (snipers/burst cluster tight);
- `min_gap`: smallest gap between consecutive requests seen so far
  (bots poll and back off at a faster cadence, R3.9).

Verdict rule (deliberately simple and interpretable — the equal-effort
rule cuts both ways: classical rungs are single mechanisms with one or
two tuned constants, so the classifier gets the same budget, recorded):

    flagged  iff  offset <= o_thr  OR  min_gap <= g_thr

Training = deterministic grid search over (o_thr, g_thr) maximizing
Youden's J (TPR − FPR) on labelled runs of ONE behaviour family. The
circularity guard (R7.1): evaluation runs use HELD-OUT families the
tuning never saw; per-family TPR/FPR is reported so evasion (the mimic
family) is visible, not averaged away.

The verdict feeds the two-priority queue in the waiting room (D10/S1):
flagged users are deprioritized, never hard-rejected — a false positive
costs delay, not a seat denied outright.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClassifierParams:
    o_thr: float  # arrival-offset threshold, seconds after T0
    g_thr: float  # min inter-request gap threshold, seconds
    trained_on: str = "untrained"  # behaviour family provenance


@dataclass
class _UserStats:
    first_post_t0: float | None = None
    last_seen: float | None = None
    min_gap: float = float("inf")


class BotClassifier:
    """Online scorer: observe every submission, answer flagged/not now."""

    def __init__(self, params: ClassifierParams, t0: float) -> None:
        self.params = params
        self.t0 = t0
        self._stats: dict[int, _UserStats] = {}

    def observe(self, user_id: int, now: float) -> None:
        st = self._stats.setdefault(user_id, _UserStats())
        if now >= self.t0 and st.first_post_t0 is None:
            st.first_post_t0 = now
        if st.last_seen is not None:
            st.min_gap = min(st.min_gap, now - st.last_seen)
        st.last_seen = now

    def is_flagged(self, user_id: int) -> bool:
        st = self._stats.get(user_id)
        if st is None:
            return False
        if st.first_post_t0 is not None and st.first_post_t0 - self.t0 <= self.params.o_thr:
            return True
        return st.min_gap <= self.params.g_thr


# ---------------------------------------------------------------- training
def extract_user_features(log: list, t0: float) -> dict[int, dict]:
    """Per-user timing features from a run's raw event log."""
    out: dict[int, dict] = {}
    last: dict[int, float] = {}
    for e in sorted((e for e in log if e[0] == "request"), key=lambda e: e[1]):
        uid, t = e[2], e[1]
        f = out.setdefault(uid, {"offset": None, "min_gap": float("inf")})
        if t >= t0 and f["offset"] is None:
            f["offset"] = t - t0
        if uid in last:
            f["min_gap"] = min(f["min_gap"], t - last[uid])
        last[uid] = t
    return out


O_GRID = (0.010, 0.020, 0.040, 0.060, 0.080)
G_GRID = (0.20, 0.30, 0.40, 0.50, 0.60, 0.70)


def evaluate(params: ClassifierParams, features: dict[int, dict], labels: dict[int, bool]):
    """(TPR, FPR) of the rule over labelled features."""
    tp = fp = pos = neg = 0
    for uid, f in features.items():
        flagged = (f["offset"] is not None and f["offset"] <= params.o_thr) or f[
            "min_gap"
        ] <= params.g_thr
        if labels.get(uid, False):
            pos += 1
            tp += flagged
        else:
            neg += 1
            fp += flagged
    return (tp / pos if pos else 0.0, fp / neg if neg else 0.0)


def tune(features: dict[int, dict], labels: dict[int, bool], trained_on: str) -> ClassifierParams:
    """Deterministic grid search maximizing Youden's J = TPR − FPR."""
    best, best_j = None, float("-inf")
    for o in O_GRID:
        for g in G_GRID:
            p = ClassifierParams(o, g, trained_on)
            tpr, fpr = evaluate(p, features, labels)
            if tpr - fpr > best_j:
                best, best_j = p, tpr - fpr
    return best


#: Frozen deployment params — tuned on the SNIPER family only (training
#: seeds 101-103, rung-4 observation runs; train TPR 1.00 / FPR 0.16).
#: Burst and mimic are HELD OUT of tuning; per-family evaluation in
#: reports/p8-rung6-2026-08-11.md is the circularity-guard record.
FROZEN_PARAMS = ClassifierParams(o_thr=0.060, g_thr=0.20, trained_on="sniper")
