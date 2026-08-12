"""Event heap with (time, seq) ordering (R1; task P1.1).

The queue is a heap of `(time, seq, fn)`. `seq` is a monotonically
increasing tie-breaker: equal-time events pop in insertion order — the
classic source of "same seed, different result" in naive DES loops, closed
here by construction (heapq never compares `fn` because `seq` is unique).

Events are zero-argument callables; callers close over their own state
(lambda / functools.partial). An event may schedule further events — the
cascade is how the whole simulation runs.
"""

from __future__ import annotations

import heapq
import itertools
from typing import Callable

from tatkal_sim.core.clock import Clock

Event = Callable[[], None]


class EventQueue:
    """Deterministic future-event list driving a Clock."""

    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self._heap: list[tuple[float, int, Event]] = []
        self._seq = itertools.count()

    def __len__(self) -> int:
        return len(self._heap)

    def schedule_at(self, t: float, fn: Event) -> None:
        """Schedule `fn` at absolute sim time `t` (>= now)."""
        if t < self._clock.now():
            raise ValueError(f"cannot schedule in the past: {t} < {self._clock.now()}")
        heapq.heappush(self._heap, (float(t), next(self._seq), fn))

    def schedule_in(self, delay: float, fn: Event) -> None:
        """Schedule `fn` after a non-negative delay from now."""
        if delay < 0:
            raise ValueError(f"negative delay: {delay}")
        self.schedule_at(self._clock.now() + delay, fn)

    def step(self) -> bool:
        """Pop and run the next event, advancing the clock. False if empty."""
        if not self._heap:
            return False
        t, _seq, fn = heapq.heappop(self._heap)
        self._clock._advance(t)
        fn()
        return True

    def run(self, *, until: float | None = None, max_events: int | None = None) -> int:
        """Run events in order; return how many were processed.

        `until` — process only events with time <= until (later events stay
        queued; the clock ends at the last processed event's time).
        `max_events` — hard stop after N events (runaway guard).
        """
        processed = 0
        while self._heap:
            if until is not None and self._heap[0][0] > until:
                break
            if max_events is not None and processed >= max_events:
                break
            self.step()
            processed += 1
        return processed
