"""v3 metrics (tatkal-v3 W3.1): the honest-cost readout.

Honest framing (requirements): identity-pricing is regressive by
construction until proven otherwise, so what each mitigation costs
HONEST users is a first-class readout, reported per cohort — never
only in aggregate. Derived from the raw log (v1 rule).

Per cohort (pre_fire / t0_humans / background / bots):
  - both clocks (absolute TTDA, post-event resolution — D14.5 carry)
  - the arm-specific price actually paid:
      verify_wait   per-identity verification wait (A1)
      verify_missed count of identities priced out by congestion (A1)
      stake_exposure  stake-in -> resolution time (A2, report-only)
      reg_burden    deliberate pre-window lead time t0 - t_register (A3)
      ineligible    count priced out by enrollment (A3)
"""

from __future__ import annotations

from tatkal_sim.measure.metrics import _pcts
from tatkal_sim.model.workload_v2 import V2Intent

COHORTS = ("pre_fire", "t0_humans", "background", "bots")


def honest_cost(log: list, intents: list[V2Intent], t0: float) -> dict:
    by_uid = {i.user_id: i for i in intents}
    first_req: dict[int, float] = {}
    t_event: dict[int, float] = {}
    definitive: dict[int, float] = {}
    verify_start: dict[int, float] = {}
    verify_done: dict[int, float] = {}
    verify_missed: set[int] = set()
    stake_in: dict[int, float] = {}
    stake_out: dict[int, float] = {}
    ineligible: set[int] = set()
    for e in log:
        kind = e[0]
        if kind == "request" and e[2] not in first_req:
            first_req[e[2]] = e[1]
        elif kind in ("alloc_win", "alloc_lose"):
            t_event[e[2]] = e[1]
        elif kind == "definitive" and e[2] not in definitive:
            definitive[e[2]] = e[1]
        elif kind == "verify_start":
            verify_start[e[2]] = e[1]
        elif kind == "verify_done":
            verify_done[e[2]] = e[1]
        elif kind == "verify_missed":
            verify_missed.add(e[2])
        elif kind == "stake_in":
            stake_in[e[2]] = e[1]
        elif kind in ("stake_refund", "stake_return", "stake_forfeit"):
            stake_out[e[2]] = e[1]
        elif kind == "ineligible":
            ineligible.add(e[2])

    out: dict[str, dict] = {}
    for cohort in COHORTS:
        uids = [i.user_id for i in intents if i.cohort == cohort]
        uidset = set(uids)
        absolute = [
            definitive[u] - first_req[u] for u in uids if u in definitive and u in first_req
        ]
        post = [definitive[u] - t_event[u] for u in uids if u in definitive and u in t_event]
        vwait = [verify_done[u] - verify_start[u] for u in uids if u in verify_done]
        exposure = [stake_out[u] - stake_in[u] for u in uids if u in stake_out and u in stake_in]
        burden = [t0 - by_uid[u].t_register for u in uids if by_uid[u].t_register is not None]
        out[cohort] = {
            "n": len(uids),
            "absolute_ttda": _pcts(absolute),
            "post_event_resolution": _pcts(post),
            "verify_wait": _pcts(vwait),
            "verify_missed": len(verify_missed & uidset),
            "stake_exposure": _pcts(exposure),
            "reg_burden": _pcts(burden),
            "ineligible": len(ineligible & uidset),
        }
    return out
