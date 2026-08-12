"""Rung 1 — bounded admission + FIFO (R4; task P6.2).

At most `limit` requests are inside the server at once; the rest wait in
an admission FIFO. Waiting is the mechanism: instead of feeding the
congestion-collapse regime (service time grows with connections), the
server runs near its knee while the queue absorbs the spike in order.

The admission queue is unbounded in v1 — user-side patience and timeouts
bound it in practice; a request whose client has left still occupies its
slot to completion (that is R3.6's wasted work, not the strategy's to
hide).
"""

from __future__ import annotations

from collections import deque
from typing import Callable

from tatkal_sim.model.users import Outcome, Service
from tatkal_sim.model.workload import Pool


class BoundedFifo:
    def __init__(self, inner: Service, *, limit: int = 8) -> None:
        self.inner = inner
        self.limit = limit
        self.in_service = 0
        self.pending: deque[tuple[int, Pool, Callable[[Outcome], None]]] = deque()

    def submit(self, user_id: int, pool: Pool, respond: Callable[[Outcome], None]) -> None:
        if self.in_service < self.limit:
            self._dispatch(user_id, pool, respond)
        else:
            self.pending.append((user_id, pool, respond))

    def _dispatch(self, user_id: int, pool: Pool, respond: Callable[[Outcome], None]) -> None:
        self.in_service += 1

        def releasing_respond(outcome: Outcome) -> None:
            self.in_service -= 1
            if self.pending:
                self._dispatch(*self.pending.popleft())
            respond(outcome)

        self.inner.submit(user_id, pool, releasing_respond)
