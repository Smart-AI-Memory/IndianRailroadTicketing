"""Virtual clock — sim time only, no wall clock (R1; task P1.1).

Sim time is a float advanced exclusively by the event queue. Nothing else
may move it, and it never goes backward. The wall-clock lint
(tests/test_no_wallclock.py) enforces that no `time.*` sneaks in anywhere
in `src/`; this class is the only source of "now".
"""

from __future__ import annotations


class Clock:
    """Holds current sim time. Advanced only by the event queue."""

    __slots__ = ("_now",)

    def __init__(self, start: float = 0.0) -> None:
        self._now = float(start)

    def now(self) -> float:
        return self._now

    def _advance(self, t: float) -> None:
        """Move time forward. Internal — the event queue is the only caller."""
        if t < self._now:
            raise ValueError(f"time cannot go backward: {t} < {self._now}")
        self._now = t
