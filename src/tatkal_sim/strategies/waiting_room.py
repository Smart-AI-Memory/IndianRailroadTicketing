"""Rung 4 — virtual waiting room (R4, R8; task P7.2).

Pre-issued ordered tokens over the rung-3 stack. Mechanics:

- Every booking arrival gets a token in one global FIFO and an immediate
  QUEUE_POSITION answer served through the server's status path — status
  traffic genuinely contends for worker capacity (R8).
- The room forwards up to `window` tokens' bookings into the inner chain
  concurrently, in token order, ON THE USER'S BEHALF: the token IS the
  request, so drain speed is the inner chain's, not the polling cadence.
  Results return by push (`push_definitive`) — the notification channel
  real waiting rooms have.
- Client polls (the engine's QUEUE_POSITION behaviour) are pure status
  load: each is a real server status request. Swept over polling
  intervals for the R8 experiment.
- **Sold-out eviction (D10, required):** the moment a forwarded booking
  answers SOLD_OUT / MECH_REJECT for a pool, every queued token for that
  pool resolves immediately by push with a definitive sold-out. Later
  arrivals for an evicted pool get an edge answer without a token.

R8's question — does the status endpoint become the new bottleneck? — is
answered by the per-stream saturation criterion over the served log
(measure/metrics.py, `r8_status_stream`).
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Callable

from tatkal_sim.core import Clock, EventQueue
from tatkal_sim.model.users import Outcome, Service
from tatkal_sim.model.workload import Pool


@dataclass
class _Token:
    user_id: int
    pool: Pool
    evicted: bool = False
    forwarded: bool = False


class WaitingRoom:
    def __init__(
        self,
        inner: Service,
        server,  # needs the status path (submit_light)
        clock: Clock,
        queue: EventQueue,
        *,
        window: int = 8,
        edge_cost: float = 0.0005,
        classifier=None,  # rung 6 (D10/S1): two-priority queue when set
    ) -> None:
        self.inner = inner
        self.server = server
        self.clock = clock
        self.queue = queue
        self.window = window
        self.edge_cost = edge_cost
        self.classifier = classifier
        self.fifo: deque[_Token] = deque()
        self.flagged_fifo: deque[_Token] = deque()  # served only when fifo empty
        self.tokens: dict[int, _Token] = {}
        self.in_flight = 0
        self.evicted_pools: set[Pool] = set()
        self.push: Callable[[int, Outcome], None] | None = None  # bound by runner

    def bind_push(self, push: Callable[[int, Outcome], None]) -> None:
        self.push = push

    # -- Service protocol ----------------------------------------------------
    def submit(self, user_id: int, pool: Pool, respond: Callable[[Outcome], None]) -> None:
        if self.clock.now() < self.server.t0:
            # the room opens AT T0: pre-T0 requests pass straight through so
            # the server's "not open" answer reaches the client normally and
            # the outcome matrix re-fires them at T0 (tokening them here
            # would push NOT_OPEN as a definitive and kill the intent)
            self.inner.submit(user_id, pool, respond)
            return
        if pool in self.evicted_pools and user_id not in self.tokens:
            # late arrival for a dead pool: edge answer, no token, no server
            self.queue.schedule_in(self.edge_cost, lambda: respond(Outcome.SOLD_OUT))
            return
        if self.classifier is not None:
            self.classifier.observe(user_id, self.clock.now())
        if user_id not in self.tokens:
            token = _Token(user_id, pool)
            self.tokens[user_id] = token
            self.fifo.append(token)
            self._pump()
        # first contact and every poll alike: a real status request through
        # the server's worker pool (R8 load stream)
        self.server.submit_light(user_id, Outcome.QUEUE_POSITION, respond)

    # -- token machinery -----------------------------------------------------
    def _next_token(self) -> _Token | None:
        """Two-priority pop (D10/S1): unflagged first; a token found flagged
        at pop time is demoted, never discarded — deprioritization costs a
        false positive delay, not the seat."""
        while self.fifo:
            token = self.fifo.popleft()
            if token.evicted:
                continue
            if self.classifier is not None and self.classifier.is_flagged(token.user_id):
                self.flagged_fifo.append(token)
                continue
            return token
        while self.flagged_fifo:
            token = self.flagged_fifo.popleft()
            if not token.evicted:
                return token
        return None

    def _pump(self) -> None:
        while self.in_flight < self.window:
            token = self._next_token()
            if token is None:
                return
            token.forwarded = True
            self.in_flight += 1
            self.inner.submit(token.user_id, token.pool, lambda o, t=token: self._on_result(t, o))

    def _on_result(self, token: _Token, outcome: Outcome) -> None:
        self.in_flight -= 1
        if (
            outcome in (Outcome.SOLD_OUT, Outcome.MECH_REJECT)
            and token.pool not in self.evicted_pools
        ):
            self._evict(token.pool)
        if self.push is not None:
            self.push(
                token.user_id, outcome if outcome is not Outcome.HARD_ERROR else Outcome.SOLD_OUT
            )
        self._pump()

    def _evict(self, pool: Pool) -> None:
        """D10: sell-out resolves every queued token for the pool NOW —
        in both priority classes; flagged users learn their fate equally
        fast (deprioritization delays service, never the answer)."""
        self.evicted_pools.add(pool)
        for token in list(self.fifo) + list(self.flagged_fifo):
            if token.pool == pool and not token.evicted:
                token.evicted = True
                if self.push is not None:
                    self.push(token.user_id, Outcome.SOLD_OUT)
