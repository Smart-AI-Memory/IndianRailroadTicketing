"""v2 allocation mechanisms and costed push (tatkal-v2 V2/V3).

Three middleware arms over the v1 `Service` chain (design.md, D14):

- `PreRegAllocation` (M1): registration in [T0-W, T0), uniform lottery
  over registered identities at T0, auto-redeem, walk-up fast answers.
- `LotteryPool` (M2): arrivals in [T0, T0+Q] pooled; draw at T0+Q over
  unique ACTIVE identities; post-draw arrivals fall through to the
  serving layer.
- `PacedDrain` (M3): per-pool tranche release gate over the rung-2
  serving layer.

`CostedPush` is the one costing model (D14.2): definitive answers
delivered out-of-band (waiting-room pushes, M1/M2 notification bursts)
are light work items on the SHARED worker pool at
`cost_factor = c_push_grid_value * status_cost_factor`. At factor 0 the
push is instantaneous — the v1-continuity anchor cell.

Log events added by this module (JSON-able tuples, v1 convention):
    ("alloc_event", t, kind, pool, n_entries, n_winners)
    ("alloc_win",  t_event, user_id)
    ("alloc_lose", t_event, user_id)        # resolve initiation (2-clock)
    ("push_enqueue", t, user_id)
    ("push_delivered", t, user_id)
    ("tranche_open", t, index)

KNOWN REGISTERED-CONSTANT DEVIATION (report, never adjust — D1): D14.1
registers "4 equal 50-seat tranches", but 200 seats live as 8 pools x
25 and 25/4 is not integral. Implemented per-pool allotment is
[7, 6, 6, 6] (global [56, 48, 48, 48]). Flagged for a chair entry.
"""

from __future__ import annotations

from typing import Callable

from tatkal_sim.core import Clock, EventQueue, RngStreams
from tatkal_sim.model.users import Outcome, Service
from tatkal_sim.model.workload import Pool
from tatkal_sim.model.workload_v2 import V2Intent, V2WorkloadConfig

#: M3 per-pool tranche allotment for 25 seats / 4 tranches (see module doc).
M3_POOL_ALLOTMENT = (7, 6, 6, 6)


class CostedPush:
    """Out-of-band definitive delivery, costed on the shared pool (D6)."""

    def __init__(
        self,
        server,
        clock: Clock,
        queue: EventQueue,
        *,
        cost_factor: float,
        log: list,
        retry_backoff: float = 0.05,
    ) -> None:
        self.server = server
        self.clock = clock
        self.queue = queue
        self.cost_factor = cost_factor
        self.log = log
        self.retry_backoff = retry_backoff
        self.deliver_cb: Callable[[int, Outcome], None] | None = None

    def bind(self, cb: Callable[[int, Outcome], None]) -> None:
        self.deliver_cb = cb

    def deliver(self, user_id: int, outcome: Outcome) -> None:
        self.log.append(("push_enqueue", self.clock.now(), user_id))
        if self.cost_factor <= 0.0:
            self._delivered(user_id, outcome)  # v1-continuity: free push
            return
        self._attempt(user_id, outcome)

    def _attempt(self, user_id: int, outcome: Outcome) -> None:
        def respond(o: Outcome) -> None:
            if o is Outcome.HARD_ERROR:  # delivery infra saturated: retry
                self.queue.schedule_in(self.retry_backoff, lambda: self._attempt(user_id, outcome))
            else:
                self._delivered(user_id, o)

        self.server.submit_light_at(user_id, outcome, respond, self.cost_factor)

    def _delivered(self, user_id: int, outcome: Outcome) -> None:
        self.log.append(("push_delivered", self.clock.now(), user_id))
        assert self.deliver_cb is not None, "CostedPush not bound"
        self.deliver_cb(user_id, outcome)


class _AllocBase:
    """Shared draw machinery for M1/M2 (identity-level uniform draw,
    controller data comes from the workload's V2Intent index)."""

    def __init__(
        self,
        inner: Service,
        server,
        clock: Clock,
        queue: EventQueue,
        streams: RngStreams,
        wcfg: V2WorkloadConfig,
        intents: list[V2Intent],
        push: CostedPush,
        log: list,
        *,
        kind: str,
        edge_cost: float = 0.0005,
    ) -> None:
        self.inner = inner
        self.server = server
        self.clock = clock
        self.queue = queue
        self.rng = streams.get("lottery")
        self.wcfg = wcfg
        self.push = push
        self.log = log
        self.kind = kind
        self.edge_cost = edge_cost
        self.by_uid: dict[int, V2Intent] = {i.user_id: i for i in intents}
        self.engine = None  # bound post-construction (active-intent view)
        self.winners: set[int] = set()
        self.resolved: set[int] = set()
        self.drawn = False

    def bind_engine(self, engine) -> None:
        self.engine = engine

    def _active(self, uid: int) -> bool:
        if self.engine is None:
            return True
        st = self.engine._by_uid.get(uid)
        return st is not None and not st.done

    def _draw_pools(self, entries: list[int]) -> None:
        """Uniform per-pool draw over ACTIVE identities; winners forward,
        losers resolve via the costed push burst."""
        by_pool: dict[Pool, list[int]] = {}
        for uid in entries:
            if self._active(uid):
                by_pool.setdefault(self.by_uid[uid].pool, []).append(uid)
        now = self.clock.now()
        for pool in sorted(by_pool):
            uids = by_pool[pool]
            seats = self.server.inventory.read(pool)
            n_win = min(seats, len(uids))
            win = set(self.rng.sample(uids, n_win)) if n_win else set()
            self.log.append(("alloc_event", now, self.kind, pool, len(uids), len(win)))
            for uid in uids:
                if uid in win:
                    self.winners.add(uid)
                    self.log.append(("alloc_win", now, uid))
                else:
                    self.resolved.add(uid)
                    self.log.append(("alloc_lose", now, uid))
                    self.push.deliver(uid, Outcome.SOLD_OUT)
        self.drawn = True


class PreRegAllocation(_AllocBase):
    """M1 (D14.1/D14.4): draw over registered identities at T0; winners
    auto-redeem through the serving layer at their natural arrival;
    losers resolve in the T0 push burst; walk-ups get edge answers once
    allocation covers the inventory. Registration one-shots are costed
    as light server work at their registered instants (R2.1)."""

    def __init__(self, *args, **kw) -> None:
        super().__init__(*args, kind="m1", **kw)
        self._registered = [i for i in self.by_uid.values() if i.t_register is not None]
        for i in self._registered:
            self.queue.schedule_at(i.t_register, lambda uid=i.user_id: self._register_work(uid))
        self.queue.schedule_at(self.wcfg.t0, self._draw)
        self._alloc_by_pool: dict[Pool, int] = {}

    def _register_work(self, uid: int) -> None:
        # one-shot registration request: costed, no client interaction
        self.server.submit_light_at(
            uid, Outcome.QUEUE_POSITION, lambda o: None, self.server.cfg.status_cost_factor
        )

    def _draw(self) -> None:
        self._draw_pools([i.user_id for i in self._registered])
        for uid in self.winners:
            pool = self.by_uid[uid].pool
            self._alloc_by_pool[pool] = self._alloc_by_pool.get(pool, 0) + 1

    def submit(self, user_id: int, pool: Pool, respond: Callable[[Outcome], None]) -> None:
        if self.clock.now() < self.wcfg.t0:
            self.inner.submit(user_id, pool, respond)  # NOT_OPEN plumbing
            return
        if user_id in self.winners:
            self.inner.submit(user_id, pool, respond)  # auto-redeem
            return
        # loser (already resolved by push) or walk-up: seats beyond the
        # allocation, if any, are contested through the serving layer
        if self._alloc_by_pool.get(pool, 0) >= self.server.inventory.read(pool):
            self.queue.schedule_in(self.edge_cost, lambda: respond(Outcome.SOLD_OUT))
        else:
            self.inner.submit(user_id, pool, respond)


class LotteryPool(_AllocBase):
    """M2 (D14.1): pool [T0, T0+Q]; entry and every poll are real status
    requests (honest ack cost); draw at T0+Q over unique active
    identities; post-draw arrivals fall through to the serving layer."""

    def __init__(self, *args, **kw) -> None:
        super().__init__(*args, kind="m2", **kw)
        self.entries: list[int] = []
        self._entered: set[int] = set()
        self.queue.schedule_at(self.wcfg.t0 + self.wcfg.qual_window, self._draw)

    def _draw(self) -> None:
        self._draw_pools(self.entries)
        # winners' bookings execute immediately after the draw (D14.4
        # analogue): forwarded in identity order on the user's behalf;
        # results return by push — entrants are pollers, not requesters.
        for uid in sorted(self.winners):
            pool = self.by_uid[uid].pool
            self.inner.submit(uid, pool, lambda o, u=uid: self.push.deliver(u, o))

    def submit(self, user_id: int, pool: Pool, respond: Callable[[Outcome], None]) -> None:
        now = self.clock.now()
        if now < self.wcfg.t0:
            self.inner.submit(user_id, pool, respond)
            return
        if not self.drawn:
            if user_id not in self._entered:
                self._entered.add(user_id)
                self.entries.append(user_id)
            self.server.submit_light(user_id, Outcome.QUEUE_POSITION, respond)
            return
        if user_id in self.winners or user_id in self.resolved:
            # resolution already travelling by push; this is a stale poll
            self.server.submit_light(user_id, Outcome.QUEUE_POSITION, respond)
            return
        self.inner.submit(user_id, pool, respond)  # post-draw arrival


class PacedDrain:
    """M3 (D14.1/D14.3): per-pool tranche release gate over the rung-2
    chain. A pool's current allotment exhausted (booked + in-flight)
    answers a retryable MECH_REJECT at edge cost while tranches remain;
    the final tranche lets the server's organic SOLD_OUT through."""

    def __init__(
        self,
        inner: Service,
        server,
        clock: Clock,
        queue: EventQueue,
        wcfg: V2WorkloadConfig,
        log: list,
        *,
        edge_cost: float = 0.0005,
    ) -> None:
        self.inner = inner
        self.server = server
        self.clock = clock
        self.queue = queue
        self.wcfg = wcfg
        self.log = log
        self.edge_cost = edge_cost
        self.allowed: dict[Pool, int] = {}
        self.booked: dict[Pool, int] = {}
        self.inflight: dict[Pool, int] = {}
        self.tranche = 0
        # pool universe from config (inventory pools are created lazily)
        self.pools: list[Pool] = [
            (train, klass, wcfg.date)
            for train in range(1, wcfg.n_trains + 1)
            for klass in wcfg.classes
        ]
        spacing = wcfg.pace_horizon / wcfg.pace_tranches
        for j in range(wcfg.pace_tranches):
            self.queue.schedule_at(wcfg.t0 + j * spacing, lambda j=j: self._open(j))

    def _open(self, index: int) -> None:
        self.tranche = index + 1
        self.log.append(("tranche_open", self.clock.now(), index))
        for pool in self.pools:
            self.allowed[pool] = self.allowed.get(pool, 0) + M3_POOL_ALLOTMENT[index]

    def _final(self) -> bool:
        return self.tranche >= self.wcfg.pace_tranches

    def submit(self, user_id: int, pool: Pool, respond: Callable[[Outcome], None]) -> None:
        if self.clock.now() < self.wcfg.t0:
            self.inner.submit(user_id, pool, respond)
            return
        if not self._final():
            permits = (
                self.allowed.get(pool, 0) - self.booked.get(pool, 0) - self.inflight.get(pool, 0)
            )
            if permits <= 0:
                # this tranche is spoken for: retryable mechanism reject
                self.queue.schedule_in(self.edge_cost, lambda: respond(Outcome.MECH_REJECT))
                return
        self.inflight[pool] = self.inflight.get(pool, 0) + 1

        def wrapped(o: Outcome) -> None:
            self.inflight[pool] -= 1
            if o is Outcome.BOOKED:
                self.booked[pool] = self.booked.get(pool, 0) + 1
            respond(o)

        self.inner.submit(user_id, pool, wrapped)
