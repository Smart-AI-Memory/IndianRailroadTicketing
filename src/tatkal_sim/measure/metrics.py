"""R6 metrics, derived from the raw event log (task P5.1).

Every metric is computed EXACTLY as defined in requirements.md R6 "Metric
definitions", with the D11 clarifications baked in:

- TTDA evaluated for winners and rejected users INDEPENDENTLY, never
  averaged across populations;
- goodput measured over the SELL-OUT WINDOW (T0 -> inventory exhausted);
- fairness quantity 1 uses first-arrival cohorts (D10/C3);
- clean rejections and hard errors are never summed;
- settling time uses the ratified parameters: 1 s rolling window p99,
  pre-spike level from the window ending 10 s before T0, settled = within
  2x pre-spike for 5 consecutive seconds, measured to the interval start.

Derivation is log-only plus the run's static context (intents, inventory
totals, T0) — metric definitions can change without touching the sim
(design.md "Measurement"). Ghost sales — seats sold to clients who had
already timed out — appear in goodput (the seat WAS allocated) and in
wasted work (the service answered nobody); the divergence between sold
seats and definitive-booked users is reported explicitly.
"""

from __future__ import annotations

from tatkal_sim.model.users import Outcome
from tatkal_sim.model.workload import Intent

CLEAN_REJECT_OUTCOMES = {Outcome.SOLD_OUT.value, Outcome.MECH_REJECT.value, Outcome.NOT_OPEN.value}

# ratified settling-time parameters (R6, chair 2026-08-11)
SETTLE_WINDOW = 1.0
SETTLE_BASELINE_GAP = 10.0
SETTLE_TOLERANCE = 2.0
SETTLE_SUSTAIN = 5.0
_SETTLE_STEP = 0.25


def _pct(xs: list[float], p: float) -> float | None:
    if not xs:
        return None
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(len(xs) * p))]


def _pcts(xs: list[float]) -> dict:
    return {"p50": _pct(xs, 0.50), "p95": _pct(xs, 0.95), "p99": _pct(xs, 0.99), "n": len(xs)}


def compute(
    log: list,
    intents: list[Intent],
    *,
    t0: float,
    inventory_totals: dict,
    inventory_violations: list[str],
    identity_on: bool = True,
    run_end: float | None = None,
) -> dict:
    cohort_of = {i.user_id: i.cohort for i in intents}
    log = sorted(log, key=lambda e: (e[1], 0))  # stable by time

    requests = [e for e in log if e[0] == "request"]
    responses = [e for e in log if e[0] == "response"]
    timeouts = [e for e in log if e[0] == "timeout"]
    definitive = [e for e in log if e[0] == "definitive"]
    sold = [e for e in log if e[0] == "sold"]
    served = [e for e in log if e[0] == "served"]
    stale = {(e[1], e[2]) for e in log if e[0] == "stale_response"}
    abandons = [e for e in log if e[0] == "abandon"]

    # -- TTDA, split by outcome population (never averaged) ------------------
    winners = [float(e[4]) for e in definitive if e[3] == Outcome.BOOKED.value]
    rejected = [
        float(e[4])
        for e in definitive
        if e[3] in (Outcome.SOLD_OUT.value, Outcome.MECH_REJECT.value)
    ]

    # -- resolution latency (D15): definitive - max(first request, T0) -------
    # the success-criteria bars bind THIS; TTDA above stays reported so
    # pre-firing remains visibly not-free
    first_req: dict[int, float] = {}
    for e in requests:
        if e[2] not in first_req:
            first_req[e[2]] = e[1]
    res_win, res_rej = [], []
    for e in definitive:
        lat = e[1] - max(first_req.get(e[2], e[1]), t0)
        if e[3] == Outcome.BOOKED.value:
            res_win.append(lat)
        elif e[3] in (Outcome.SOLD_OUT.value, Outcome.MECH_REJECT.value):
            res_rej.append(lat)

    # -- goodput over the sell-out window (D11) ------------------------------
    initial = inventory_totals["initial"]
    sellout_t = None
    if sold and inventory_totals["remaining"] == 0:
        sellout_t = sold[initial - 1][1] if len(sold) >= initial else sold[-1][1]
    window_end = sellout_t if sellout_t is not None else (run_end or (log[-1][1] if log else t0))
    window = max(window_end - t0, 1e-9)
    goodput = len(sold) / window

    # -- rejection vs error rates (never summed) -----------------------------
    n_req = len(requests)
    clean = sum(1 for e in responses if e[3] in CLEAN_REJECT_OUTCOMES)
    hard = sum(1 for e in responses if e[3] == Outcome.HARD_ERROR.value) + len(timeouts)

    # -- retry amplification (R3.10 identity) --------------------------------
    unique = len({i.user_id for i in intents}) if identity_on else n_req
    amplification = n_req / unique if unique else 0.0

    # -- wasted work ---------------------------------------------------------
    total_busy = sum(float(e[3]) for e in served)
    wasted_busy = sum(float(e[3]) for e in served if (e[1], e[2]) in stale)
    wasted_ratio = wasted_busy / total_busy if total_busy else 0.0

    # -- fairness (first-arrival cohorts; D10/C3) ----------------------------
    seats_by_cohort: dict[str, int] = {}
    for e in sold:
        c = cohort_of.get(e[2], "unknown")
        seats_by_cohort[c] = seats_by_cohort.get(c, 0) + 1
    pop = {c: sum(1 for i in intents if i.cohort == c) for c in {i.cohort for i in intents}}
    bots_pop_share = pop.get("bots", 0) / len(intents) if intents else 0.0
    bots_win_share = seats_by_cohort.get("bots", 0) / len(sold) if sold else 0.0

    # -- settling time (ratified parameters) ---------------------------------
    settling = _settling_time(log, t0)

    return {
        "ttda": {"winners": _pcts(winners), "rejected": _pcts(rejected)},
        "resolution": {"winners": _pcts(res_win), "rejected": _pcts(res_rej)},
        "goodput": {
            "sold_per_s": goodput,
            "window_s": window,
            "sellout_reached": sellout_t is not None,
            "seats_sold": len(sold),
            "definitive_booked_users": len(winners),
            "ghost_sales": len(sold) - len(winners),
        },
        "inventory": {
            **inventory_totals,
            "violations": list(inventory_violations),
            "sold_pct": len(sold) / initial if initial else 0.0,
        },
        "clean_rejection_rate": clean / n_req if n_req else 0.0,
        "hard_error_rate": hard / n_req if n_req else 0.0,
        "retry_amplification": amplification,
        "wasted_work_ratio": wasted_ratio,
        "fairness": {
            "seats_by_cohort": dict(sorted(seats_by_cohort.items())),
            "population_by_cohort": dict(sorted(pop.items())),
            "bots_win_share": bots_win_share,
            "bots_population_share": bots_pop_share,
        },
        "settling_time_s": settling,
        "abandon_count": len(abandons),
    }


def _settling_time(log: list, t0: float) -> float | None:
    """Ratified definition: 1 s rolling p99; baseline = window ending
    T0-10 s; settled = within 2x baseline for 5 consecutive seconds;
    reported to the START of the sustained interval. None = never settled
    (or no baseline traffic — reported, not fabricated)."""
    pending: dict[int, float] = {}
    samples: list[tuple[float, float]] = []  # (t_response, latency)
    for e in sorted(log, key=lambda e: e[1]):
        if e[0] == "request":
            pending[e[2]] = e[1]
        elif e[0] == "response" and e[2] in pending:
            samples.append((e[1], e[1] - pending.pop(e[2])))
        elif e[0] == "timeout" and e[2] in pending:
            pending.pop(e[2])
    if not samples:
        return None

    def window_p99(end: float) -> float | None:
        xs = [lat for t, lat in samples if end - SETTLE_WINDOW <= t < end]
        return _pct(xs, 0.99)

    baseline = window_p99(t0 - SETTLE_BASELINE_GAP)
    if baseline is None:
        return None
    t_last = samples[-1][0]
    t = t0
    while t + SETTLE_SUSTAIN <= t_last + _SETTLE_STEP:
        ok = True
        step = t
        while step <= t + SETTLE_SUSTAIN:
            p = window_p99(step)
            if p is not None and p > SETTLE_TOLERANCE * baseline:
                ok = False
                break
            step += _SETTLE_STEP
        if ok:
            return t - t0
        t += _SETTLE_STEP
    return None
