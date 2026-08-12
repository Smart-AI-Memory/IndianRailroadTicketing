"""Rung 5 — adaptive concurrency limiting (R4, R7.2; task P7.3).

AIMD control, treated as control theory per R7.2: the static admission
bound (rung 1's hand-tuned constant, "wrong for every workload but one")
becomes a dynamic limit driven by observed in-chain latency against a
target derived from the ratified `p99_knee`:

- latency <= target  -> additive probe upward (+`add` per completion);
- latency  > target  -> multiplicative back-off (x`beta`), rate-limited
  by a cooldown so one bad sample cannot collapse the limit.

Deterministic (no randomness) — R1 holds. `limit` is exposed for the
stability acceptance across knee variants (P7.3).
"""

from __future__ import annotations

from collections import deque
from typing import Callable

from tatkal_sim.core import Clock
from tatkal_sim.model.users import Outcome, Service
from tatkal_sim.model.workload import Pool

#: 10 x p99_knee (0.684 ms, D8): an order above the single-op tail, an
#: order below the 34.2 ms success bar. Swept in the P9 sensitivity table.
DEFAULT_TARGET_S = 0.00684


class AdaptiveLimit:
    def __init__(
        self,
        inner: Service,
        clock: Clock,
        *,
        target_s: float = DEFAULT_TARGET_S,
        start: float = 8.0,
        min_limit: float = 1.0,
        max_limit: float = 256.0,
        add: float = 0.25,
        beta: float = 0.7,
        cooldown_s: float = 0.02,
    ) -> None:
        self.inner = inner
        self.clock = clock
        self.target_s = target_s
        self.limit = start
        self.min_limit, self.max_limit = min_limit, max_limit
        self.add, self.beta, self.cooldown_s = add, beta, cooldown_s
        self.in_service = 0
        self.pending: deque[tuple[int, Pool, Callable[[Outcome], None]]] = deque()
        self._last_backoff = float("-inf")

    def submit(self, user_id: int, pool: Pool, respond: Callable[[Outcome], None]) -> None:
        if self.in_service < int(self.limit):
            self._dispatch(user_id, pool, respond)
        else:
            self.pending.append((user_id, pool, respond))

    def _dispatch(self, user_id: int, pool: Pool, respond: Callable[[Outcome], None]) -> None:
        self.in_service += 1
        t_forward = self.clock.now()

        def releasing_respond(outcome: Outcome) -> None:
            self.in_service -= 1
            self._adapt(self.clock.now() - t_forward)
            while self.pending and self.in_service < int(self.limit):
                self._dispatch(*self.pending.popleft())
            respond(outcome)

        self.inner.submit(user_id, pool, releasing_respond)

    def _adapt(self, latency: float) -> None:
        now = self.clock.now()
        if latency > self.target_s:
            if now - self._last_backoff >= self.cooldown_s:
                self.limit = max(self.min_limit, self.limit * self.beta)
                self._last_backoff = now
        else:
            self.limit = min(self.max_limit, self.limit + self.add)
