"""FIFO lock per pool — lock_wait emergent from queueing (R3.4; task P3.2).

Postgres `SELECT FOR UPDATE` semantics per the 2026-08-11 calibration
finding: waiters are granted in arrival order, so a synchronized stampede
produces bounded, fair tails (~queue-depth x hold time) — not the unfair
backoff explosion the withdrawn SQLite run showed. Discipline, not
capacity, decides the tail; this class IS that discipline in the model.

`lock_wait` is never drawn from a distribution anywhere in the simulator —
it emerges from this queue. That is the design's central fidelity
commitment (design.md "Server model").
"""

from __future__ import annotations

from collections import deque
from typing import Callable

from tatkal_sim.core.events import EventQueue


class FifoLock:
    """Grant-in-arrival-order lock driven by the event queue."""

    __slots__ = ("_held", "_waiters")

    def __init__(self) -> None:
        self._held = False
        self._waiters: deque[Callable[[], None]] = deque()

    @property
    def queue_depth(self) -> int:
        return len(self._waiters)

    def acquire(self, queue: EventQueue, grant: Callable[[], None]) -> None:
        """Run `grant` when the lock is ours; immediately if free."""
        if not self._held:
            self._held = True
            grant()
        else:
            self._waiters.append(grant)

    def release(self, queue: EventQueue) -> None:
        if self._waiters:
            nxt = self._waiters.popleft()
            # same-time grant; (time, seq) ordering keeps this deterministic
            queue.schedule_in(0.0, nxt)
        else:
            self._held = False
