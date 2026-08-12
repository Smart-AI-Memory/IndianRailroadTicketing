"""P8 acceptance — rung 6: classifier units, two-priority queue, fairness."""

import dataclasses as dc

from tatkal_sim.model.workload import OPERATING_WORKLOAD
from tatkal_sim.runner import ladder_arm, run_arm_once
from tatkal_sim.strategies.bot_classifier import (
    FROZEN_PARAMS,
    BotClassifier,
    ClassifierParams,
)


def family_arm(k: int, family: str):
    arm = ladder_arm(k)
    return dc.replace(arm, wcfg=dc.replace(OPERATING_WORKLOAD, bot_family=family))


def F(m: dict) -> float:
    return m["fairness"]["bots_win_share"] / m["fairness"]["bots_population_share"]


# -- classifier units --------------------------------------------------------
def test_classifier_flags_tight_offsets_and_fast_cadence():
    clf = BotClassifier(ClassifierParams(o_thr=0.06, g_thr=0.2, trained_on="test"), t0=30.0)
    clf.observe(1, 30.010)  # sniper-tight arrival
    assert clf.is_flagged(1)
    clf.observe(2, 30.500)  # human-ish arrival...
    assert not clf.is_flagged(2)
    clf.observe(2, 30.650)  # ...but machine-fast follow-up (gap 0.15 < 0.2)
    assert clf.is_flagged(2)
    clf.observe(3, 30.800)
    clf.observe(3, 31.900)  # slow human polling: stays clean
    assert not clf.is_flagged(3)
    assert not clf.is_flagged(999)  # never seen -> never flagged


def test_classifier_ignores_pre_t0_offset():
    clf = BotClassifier(FROZEN_PARAMS, t0=30.0)
    clf.observe(1, 25.0)  # pre-fire poll: offset feature must not fire
    assert not clf.is_flagged(1)
    clf.observe(1, 30.5)  # first POST-T0 contact is what counts
    assert not clf.is_flagged(1)


# -- two-priority queue ------------------------------------------------------
def test_flagged_tokens_served_only_when_no_unflagged_waits():
    from tatkal_sim.core import Clock, EventQueue
    from tatkal_sim.strategies.waiting_room import WaitingRoom

    class HoldingInner:
        """Responds only when released — so a queue actually FORMS (a
        synchronous inner serves everyone at submit time, and serving a
        flagged token when nobody unflagged waits is correct behavior)."""

        def __init__(self):
            self.order = []
            self.responders = []

        def submit(self, uid, pool, respond):
            from tatkal_sim.model.users import Outcome

            self.order.append(uid)
            self.responders.append(lambda: respond(Outcome.BOOKED))

    class StubServer:
        t0 = 0.0

        def submit_light(self, uid, outcome, respond):
            respond(outcome)

    class OddFlagger:
        def observe(self, uid, now):
            pass

        def is_flagged(self, uid):
            return uid % 2 == 1

    clock = Clock()
    clock._advance(1.0)  # room open
    queue = EventQueue(clock)
    inner = HoldingInner()
    room = WaitingRoom(inner, StubServer(), clock, queue, window=1, classifier=OddFlagger())
    room.bind_push(lambda uid, o: None)
    for uid in (1, 2, 3, 4, 5, 6):  # odd = flagged
        room.submit(uid, (1, "AC", "D0"), lambda o: None)
    while inner.responders:  # release one at a time; queue persists
        inner.responders.pop(0)()
        queue.run()
    # uid 1 forwarded first (window empty, nobody unflagged waiting — OK);
    # then every even beats every remaining odd; FIFO within each class
    assert inner.order == [1, 2, 4, 6, 3, 5]


# -- rung 6 end-to-end -------------------------------------------------------
def test_rung6_recovers_fairness_on_trained_family():
    r5 = run_arm_once(family_arm(5, "sniper"), seed=1)
    r6 = run_arm_once(family_arm(6, "sniper"), seed=1)
    assert F(r6) < 0.5 * F(r5)  # deprioritization guts the bot advantage
    assert r6["inventory"]["violations"] == []


def test_rung6_mimic_family_evades_honestly():
    """The circularity guard's point: human-shaped bots must NOT be
    magically caught. Fairness recovery on mimic is limited."""
    r6 = run_arm_once(family_arm(6, "mimic"), seed=1)
    r5 = run_arm_once(family_arm(5, "mimic"), seed=1)
    assert F(r6) > 0.5 * F(r5)  # nowhere near the sniper-family reduction


def test_out_of_order_rung4_plus_classifier_documents_the_drain_finding():
    """FINDING (P8): at rung 4's fast drain (~100 ms sell-out), timing-only
    classification is structurally blind — everyone present is 'early', so
    the offset feature flags the whole contending population (two-priority
    degenerates to FIFO) and no second request exists yet for cadence.
    Fairness is UNCHANGED. The classifier earns its keep only when the
    contest lasts (rung 6 over the slow adaptive stack) — the spec's
    standing note made empirical: the race is over before the population
    differentiates."""
    from tatkal_sim.strategies.base import RungParams

    arm = dc.replace(
        ladder_arm(4),
        name="rung4+clf",
        rung_params=RungParams(force_classifier=True),
        out_of_order=True,
    )
    base = run_arm_once(ladder_arm(4), seed=1)
    with_clf = run_arm_once(arm, seed=1)
    assert abs(F(with_clf) - F(base)) < 0.1 * F(base)  # no material change
