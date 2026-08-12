"""V2/V3 acceptance (tatkal-v2 tasks.md V2.1-V2.4, V3.1-V3.4)."""


from tatkal_sim.model.workload_v2 import OPERATING_WORKLOAD_V2, with_abuse
from tatkal_sim.runner_v2 import V2Arm, run_arm_v2_once


def _events(log, kind):
    return [e for e in log if e[0] == kind]


def _definitive_t(log):
    return {e[2]: e[1] for e in log if e[0] == "definitive"}


# ---------------------------------------------------------------- V2.1
def test_no_resolution_before_allocation_event():
    r = run_arm_v2_once(V2Arm("m2", "m2"), 0)
    log = r["log"]
    t_events = {e[1] for e in _events(log, "alloc_event")}
    assert len(t_events) == 1  # all pools draw at T0+Q
    t_draw = t_events.pop()
    resolved = {e[2] for e in _events(log, "alloc_win")} | {
        e[2] for e in _events(log, "alloc_lose")
    }
    assert resolved  # the draw resolved someone
    d = _definitive_t(log)
    for uid in resolved:
        if uid in d:  # abandoners have no definitive; none may PRECEDE the draw
            assert d[uid] >= t_draw


def test_m1_draw_at_t0_and_winners_book():
    r = run_arm_v2_once(V2Arm("m1", "m1"), 0)
    log = r["log"]
    assert len(_events(log, "alloc_event")) == 8  # one per pool
    assert r["metrics"]["goodput"]["seats_sold"] == 200
    winners = {e[2] for e in _events(log, "alloc_win")}
    assert len(winners) == 200


# ---------------------------------------------------------------- V2.2
def test_costed_push_zero_is_instantaneous():
    r = run_arm_v2_once(V2Arm("m2-c0", "m2", c_push=0.0), 0)
    enq = {(e[2]): e[1] for e in _events(r["log"], "push_enqueue")}
    for e in _events(r["log"], "push_delivered"):
        assert e[1] == enq[e[2]]  # same instant: v1-continuity


def test_costed_push_burst_drains_slower_with_cost():
    def burst_span(c):
        r = run_arm_v2_once(V2Arm(f"m2-c{c}", "m2", c_push=c), 0)
        deliveries = [e[1] for e in _events(r["log"], "push_delivered")]
        return max(deliveries) - min(deliveries)

    spans = [burst_span(c) for c in (0.25, 1.0, 2.0)]
    assert spans[0] < spans[1] < spans[2]


# ---------------------------------------------------------------- V2.3
def test_error_taxonomy_streams_distinct():
    r = run_arm_v2_once(V2Arm("m3", "m3"), 0)
    log = r["log"]
    # tranche-gate rejects (mech_reject definitives) vs organic sold-out
    # vs timeouts are all separable from the raw log
    kinds = {e[0] for e in log}
    assert "definitive" in kinds
    mech = [e for e in log if e[0] == "definitive" and e[3] == "mech_reject"]
    sold_out = [e for e in log if e[0] == "definitive" and e[3] == "sold_out"]
    assert mech and sold_out  # both streams present and distinct
    # lottery-loss stream: alloc_lose ∩ definitive(sold_out) in m2
    r2 = run_arm_v2_once(V2Arm("m2", "m2"), 0)
    losers = {e[2] for e in _events(r2["log"], "alloc_lose")}
    lottery_losses = [
        e for e in r2["log"] if e[0] == "definitive" and e[3] == "sold_out" and e[2] in losers
    ]
    assert lottery_losses


# ---------------------------------------------------------------- V2.4
def test_two_clock_hand_check():
    r = run_arm_v2_once(V2Arm("m2", "m2"), 0)
    log = r["log"]
    t_draw = _events(log, "alloc_event")[0][1]
    d = _definitive_t(log)
    first_req = {}
    for e in log:
        if e[0] == "request" and e[2] not in first_req:
            first_req[e[2]] = e[1]
    losers = [e[2] for e in _events(log, "alloc_lose")]
    uid = next(u for u in losers if u in d and u in first_req)
    absolute = d[uid] - first_req[uid]
    post_event = d[uid] - t_draw
    # hand-checkable relations: the absolute clock contains the deliberate
    # wait; the post-event clock does not
    assert absolute >= post_event >= 0
    assert absolute >= t_draw - first_req[uid]


# ---------------------------------------------------------------- V3.1
def test_m1_leak_diagnostic_camp_buys_nothing():
    """Camp registers early; the lottery is timing-independent, so camp
    and race win-rates among REGISTRANTS must be statistically alike."""
    camp_rate = race_rate = 0.0
    camp_n = race_n = camp_w = race_w = 0
    for seed in range(8):
        r = run_arm_v2_once(V2Arm("m1", "m1"), seed)
        winners = {e[2] for e in _events(r["log"], "alloc_win")}
        by_strategy = {}
        for i in r["intents"]:
            if i.cohort == "bots" and i.t_register is not None:
                by_strategy.setdefault(i.strategy, []).append(i.user_id)
        camp_ids = by_strategy.get("camp", [])
        race_regs = [u for s, ids in by_strategy.items() if s == "race" for u in ids]
        camp_n += len(camp_ids)
        camp_w += sum(1 for u in camp_ids if u in winners)
        race_n += len(race_regs)
        race_w += sum(1 for u in race_regs if u in winners)
    camp_rate = camp_w / camp_n if camp_n else 0.0
    assert camp_n >= 200  # 30 camp bots x 8 seeds, all registered
    # race bots don't register in m1 (only camp does, D13.3) — compare camp
    # against the human registrant win rate instead
    human_rate_num = human_rate_den = 0
    for seed in range(8):
        r = run_arm_v2_once(V2Arm("m1", "m1"), seed)
        winners = {e[2] for e in _events(r["log"], "alloc_win")}
        regs = [i.user_id for i in r["intents"] if i.cohort != "bots" and i.t_register is not None]
        human_rate_den += len(regs)
        human_rate_num += sum(1 for u in regs if u in winners)
    human_rate = human_rate_num / human_rate_den
    assert abs(camp_rate - human_rate) < 0.5 * human_rate  # no camping edge


# ---------------------------------------------------------------- V3.2
def test_m2_leak_diagnostic_p1_no_advantage_at_zero_abuse():
    """P1 (D13.5): at p = 0, per-strategy draw-share advantage ~ 1."""
    bot_w = bot_n = pool_w = pool_n = 0
    for seed in range(8):
        r = run_arm_v2_once(V2Arm("m2-p0", "m2", wcfg=with_abuse(OPERATING_WORKLOAD_V2, 0.0)), seed)
        winners = {e[2] for e in _events(r["log"], "alloc_win")}
        entrants = {e[2] for e in _events(r["log"], "alloc_win")} | {
            e[2] for e in _events(r["log"], "alloc_lose")
        }
        cohort = {i.user_id: i.cohort for i in r["intents"]}
        bot_entr = [u for u in entrants if cohort[u] == "bots"]
        bot_n += len(bot_entr)
        bot_w += sum(1 for u in bot_entr if u in winners)
        pool_n += len(entrants)
        pool_w += len(winners)
    bot_rate = bot_w / bot_n
    overall_rate = pool_w / pool_n
    advantage = bot_rate / overall_rate
    assert 0.7 < advantage < 1.3  # ~1: pooling neutralizes timing and cadence


# ---------------------------------------------------------------- V3.3
def test_m3_tranches_and_camp_rearrival():
    r = run_arm_v2_once(V2Arm("m3", "m3"), 0)
    log = r["log"]
    opens = _events(log, "tranche_open")
    assert [e[2] for e in opens] == [0, 1, 2, 3]
    t_opens = [e[1] for e in opens]
    assert t_opens == [30.0, 32.0, 34.0, 36.0]
    # camp re-arrivals: rearm logged, next request within 50 ms of an open
    rearms = _events(log, "camp_rearm")
    assert rearms
    reqs = sorted((e[1], e[2]) for e in log if e[0] == "request")
    camp_ids = {i.user_id for i in r["intents"] if i.strategy == "camp"}
    for t_open in t_opens[1:]:
        window_reqs = [u for (t, u) in reqs if t_open <= t <= t_open + 0.055 and u in camp_ids]
        assert window_reqs  # campers present at every subsequent open
    # inventory invariants held across tranche boundaries (assert_ok ran
    # inside run_arm_v2_once); the gate never oversells a tranche
    assert r["metrics"]["goodput"]["ghost_sales"] == 0


# ---------------------------------------------------------------- V3.4
def test_r3p_zero_cost_is_plumbing_noop():
    """D16 continuity: at c_push = 0 the CostedPush channel must be a
    bit-exact no-op vs binding the engine's push directly. (The v2
    population intentionally differs from v1's — D13 — so continuity is
    proven at the plumbing level, same workload both sides.)"""
    from tatkal_sim.runner import result_digest

    a = run_arm_v2_once(V2Arm("r3p-c0", "r3p", c_push=0.0), 0)
    b = run_arm_v2_once(V2Arm("eng-r4", "eng", rung=4, c_push=0.0), 0)
    assert result_digest(a["metrics"]) == result_digest(b["metrics"])


def test_r3p_costed_push_changes_physics():
    a = run_arm_v2_once(V2Arm("r3p-c0", "r3p", c_push=0.0), 0)
    b = run_arm_v2_once(V2Arm("r3p-c2", "r3p", c_push=2.0), 0)
    from tatkal_sim.runner import result_digest

    assert result_digest(a["metrics"]) != result_digest(b["metrics"])
