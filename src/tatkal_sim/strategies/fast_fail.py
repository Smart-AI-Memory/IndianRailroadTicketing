"""Rung 2 — fast-fail from a cached per-pool sold-out counter (R4; P6.3).

The cache learns a pool is sold out by OBSERVING a sold-out answer flow
through it, and its knowledge takes `staleness` seconds to become
effective — the cache being stale is part of the model, not a bug (R4).
Once effective, arrivals for that pool get a definitive mechanism
rejection (`MECH_REJECT`, a clean answer per R6) at edge cost, never
touching the server.

Composed outside BoundedFifo (rung 2 = rung 1 + this), so a fast-failed
request also never occupies an admission slot.
"""

from __future__ import annotations

from typing import Callable

from tatkal_sim.core import Clock, EventQueue
from tatkal_sim.model.users import Outcome, Service
from tatkal_sim.model.workload import Pool


class FastFail:
    def __init__(
        self,
        inner: Service,
        clock: Clock,
        queue: EventQueue,
        *,
        staleness: float = 0.05,
        reject_cost: float = 0.0005,
    ) -> None:
        self.inner = inner
        self.clock = clock
        self.queue = queue
        self.staleness = staleness
        self.reject_cost = reject_cost
        self.sold_out_seen_at: dict[Pool, float] = {}

    def submit(self, user_id: int, pool: Pool, respond: Callable[[Outcome], None]) -> None:
        seen = self.sold_out_seen_at.get(pool)
        if seen is not None and self.clock.now() >= seen + self.staleness:
            self.queue.schedule_in(self.reject_cost, lambda: respond(Outcome.MECH_REJECT))
            return

        def observing_respond(outcome: Outcome) -> None:
            if outcome is Outcome.SOLD_OUT and pool not in self.sold_out_seen_at:
                self.sold_out_seen_at[pool] = self.clock.now()
            respond(outcome)

        self.inner.submit(user_id, pool, observing_respond)
