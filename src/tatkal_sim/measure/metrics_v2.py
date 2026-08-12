"""v2 metrics (tatkal-v2 V4.1/V4.2): two clocks, per-mechanism fairness,
error taxonomy, and the three-variant report gate.

All derived from the raw event log (v1 rule: metrics are computed,
never accumulated inline). Fairness definitions are the D5-proposed
ones from design.md — guard VALUES are Gate B's, not this module's.
"""

from __future__ import annotations

from tatkal_sim.measure.metrics import _pcts
from tatkal_sim.model.workload_v2 import V2Intent

# ----------------------------------------------------------- V4.1 clocks


def two_clock(log: list, intents: list[V2Intent]) -> dict:
    """Absolute TTDA and post-event resolution for allocation-arm
    members (D14.5). Non-members appear only in the absolute clock."""
    t_event: dict[int, float] = {}
    for e in log:
        if e[0] in ("alloc_win", "alloc_lose"):
            t_event[e[2]] = e[1]
    first_req: dict[int, float] = {}
    for e in log:
        if e[0] == "request" and e[2] not in first_req:
            first_req[e[2]] = e[1]
    absolute: list[float] = []
    post_event: list[float] = []
    for e in log:
        if e[0] != "definitive":
            continue
        uid, t = e[2], e[1]
        if uid in first_req:
            absolute.append(t - first_req[uid])
        if uid in t_event:
            post_event.append(t - t_event[uid])
    return {
        "absolute_ttda": _pcts(absolute),
        "post_event_resolution": _pcts(post_event),
        "n_members": len(t_event),
    }


# --------------------------------------------------------- V4.1 fairness


def draw_share_advantage(log: list, intents: list[V2Intent]) -> dict:
    """M1/M2 (D5): bot-controlled win share / bot population share,
    per strategy, at the CONTROLLER level (identity-split rolls up)."""
    by_uid = {i.user_id: i for i in intents}
    winners = {e[2] for e in log if e[0] == "alloc_win"}
    members = winners | {e[2] for e in log if e[0] == "alloc_lose"}
    ctrl_strategy: dict[int, str] = {}
    ctrl_won: dict[int, bool] = {}
    for uid in members:
        i = by_uid[uid]
        key = i.controller_id
        ctrl_strategy[key] = i.strategy if i.cohort == "bots" else "human"
        ctrl_won[key] = ctrl_won.get(key, False) or (uid in winners)
    n_controllers = len(ctrl_strategy)
    n_winning = sum(1 for w in ctrl_won.values() if w)
    out: dict[str, dict] = {}
    for strategy in sorted(set(ctrl_strategy.values())):
        ids = [c for c, s in ctrl_strategy.items() if s == strategy]
        wins = sum(1 for c in ids if ctrl_won[c])
        pop_share = len(ids) / n_controllers if n_controllers else 0.0
        win_share = wins / n_winning if n_winning else 0.0
        out[strategy] = {
            "controllers": len(ids),
            "controller_wins": wins,
            "pop_share": pop_share,
            "win_share": win_share,
            "advantage": (win_share / pop_share) if pop_share else 0.0,
        }
    return out


def per_tranche_fairness(log: list, intents: list[V2Intent], wcfg) -> list[dict]:
    """M3 (D5): the v1 F-ratio (win share / pop share for bots) per
    tranche window, plus seats sold in each."""
    cohort = {i.user_id: i.cohort for i in intents}
    opens = sorted(e[1] for e in log if e[0] == "tranche_open")
    edges = opens + [float("inf")]
    pop_bots = sum(1 for i in intents if i.cohort == "bots")
    pop_share = pop_bots / len(intents) if intents else 0.0
    out = []
    for j in range(len(opens)):
        sold = [e for e in log if e[0] == "sold" and edges[j] <= e[1] < edges[j + 1]]
        bot_sold = sum(1 for e in sold if cohort.get(e[2]) == "bots")
        win_share = bot_sold / len(sold) if sold else 0.0
        out.append(
            {
                "tranche": j,
                "t_open": opens[j],
                "seats_sold": len(sold),
                "bot_win_share": win_share,
                "f_ratio": (win_share / pop_share) if pop_share else 0.0,
            }
        )
    return out


# --------------------------------------------------------- V2.3 taxonomy


def error_taxonomy(log: list) -> dict:
    """Distinct outcome streams (R4.1): never summed anywhere."""
    losers = {e[2] for e in log if e[0] == "alloc_lose"}
    counts = {
        "booked": 0,
        "clean_reject": 0,  # sold_out / mech_reject outside a draw
        "lottery_loss": 0,  # sold_out delivered to a draw loser
        "timeouts": sum(1 for e in log if e[0] == "timeout"),
        "hard_errors": sum(1 for e in log if e[0] == "response" and e[3] == "hard_error"),
        "abandons": sum(1 for e in log if e[0] == "abandon"),
    }
    for e in log:
        if e[0] != "definitive":
            continue
        if e[3] == "booked":
            counts["booked"] += 1
        elif e[3] in ("sold_out", "mech_reject"):
            if e[2] in losers:
                counts["lottery_loss"] += 1
            else:
                counts["clean_reject"] += 1
    return counts


# ----------------------------------------------------- V4.2 variant gate

REQUIRED_VARIANTS = ("fitted", "plateau", "cliff")


def three_variant_table(per_variant: dict[str, dict], metric_label: str) -> dict:
    """R4.3: a headline table MUST carry all three variants; a missing
    one fails generation rather than shipping a partial table."""
    missing = [v for v in REQUIRED_VARIANTS if v not in per_variant]
    if missing:
        raise ValueError(f"three-variant table '{metric_label}' missing variants: {missing}")
    return {"metric": metric_label, **{v: per_variant[v] for v in REQUIRED_VARIANTS}}
