"""P1.1 acceptance — clock monotonicity and (time, seq) event ordering."""

import pytest

from tatkal_sim.core import Clock, EventQueue


def test_equal_time_events_pop_in_insertion_order():
    clock, q = Clock(), None
    q = EventQueue(clock)
    order = []
    for tag in "abcde":
        q.schedule_at(5.0, lambda tag=tag: order.append(tag))
    q.run()
    assert order == list("abcde")


def test_equal_time_order_holds_across_interleaved_scheduling():
    clock = Clock()
    q = EventQueue(clock)
    order = []
    q.schedule_at(2.0, lambda: order.append("x1"))
    q.schedule_at(1.0, lambda: order.append("early"))
    q.schedule_at(2.0, lambda: order.append("x2"))
    q.schedule_at(2.0, lambda: order.append("x3"))
    q.run()
    assert order == ["early", "x1", "x2", "x3"]


def test_clock_advances_to_event_time_and_never_backward():
    clock = Clock()
    q = EventQueue(clock)
    seen = []
    q.schedule_at(1.5, lambda: seen.append(clock.now()))
    q.schedule_at(3.0, lambda: seen.append(clock.now()))
    q.run()
    assert seen == [1.5, 3.0]
    assert clock.now() == 3.0
    with pytest.raises(ValueError):
        clock._advance(2.9)


def test_scheduling_in_the_past_raises():
    clock = Clock()
    q = EventQueue(clock)
    q.schedule_at(2.0, lambda: None)
    q.run()
    with pytest.raises(ValueError):
        q.schedule_at(1.0, lambda: None)
    with pytest.raises(ValueError):
        q.schedule_in(-0.1, lambda: None)


def test_events_scheduled_during_execution_are_processed():
    clock = Clock()
    q = EventQueue(clock)
    log = []

    def cascade(depth: int) -> None:
        log.append((depth, clock.now()))
        if depth < 3:
            q.schedule_in(1.0, lambda: cascade(depth + 1))

    q.schedule_at(0.0, lambda: cascade(0))
    n = q.run()
    assert n == 4
    assert log == [(0, 0.0), (1, 1.0), (2, 2.0), (3, 3.0)]


def test_run_until_leaves_later_events_queued():
    clock = Clock()
    q = EventQueue(clock)
    fired = []
    for t in (1.0, 2.0, 3.0, 4.0):
        q.schedule_at(t, lambda t=t: fired.append(t))
    n = q.run(until=2.5)
    assert n == 2 and fired == [1.0, 2.0]
    assert len(q) == 2
    assert clock.now() == 2.0  # not dragged to `until`


def test_max_events_guard():
    clock = Clock()
    q = EventQueue(clock)

    def rearm() -> None:
        q.schedule_in(1.0, rearm)  # would run forever

    q.schedule_at(0.0, rearm)
    assert q.run(max_events=50) == 50
