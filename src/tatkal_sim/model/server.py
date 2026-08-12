"""Bounded server model (R3.3, R3.6, R3.7; tasks P3.1, P3.4).

Implements the `Service` protocol the client engine talks to. Request
path, all bounds non-optional (D10/S7):

  submit -> conn_limit gate -> worker or accept_queue (drop-newest) ->
  app_time -> pool lock (FIFO, worker HELD while waiting) -> lock_hold ->
  inventory decrement -> respond

The worker being held during lock wait is deliberate and load-bearing:
that is how the calibrated system behaved (a Postgres backend holds its
connection and server slot while waiting on the row lock), and it is what
couples the two queueing regimes the sharded8 control separated.

Pre-T0 (D10/S2): requests before T0 take a worker for app_time only and
get a clean NOT_OPEN — no lock, no inventory, ever.

Toggles consulted:
- `bounded_capacity` OFF (ablation-only): conn/worker/queue limits vanish;
  the lock still queues — capacity is the lie being ablated, not atomicity.
- `wasted_work` ON (default): a request occupies its worker to completion
  even if the client timed out. OFF (the flattering lie): a request whose
  client has certainly timed out is shed the moment it would start
  service, instantly freeing capacity.
- `heavy_tail_service`: app_time gains a rare heavy component (R3.7).
- `atomic_inventory` OFF: read-then-write race instead of the lock —
  P3.3's invariants catch what it breaks.

Sharding (rung 3 flips it): `sharded=False` funnels every pool through
one global lock (the hot-key case); `sharded=True` gives each pool its
own lock.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from tatkal_sim.config import FidelityConfig
from tatkal_sim.core import Clock, EventQueue, RngStreams
from tatkal_sim.model.inventory import Inventory
from tatkal_sim.model.locks import FifoLock
from tatkal_sim.model.users import Outcome
from tatkal_sim.model.workload import Pool


@dataclass(frozen=True)
class ServerConfig:
    workers: int = 8
    accept_queue: int = 64
    conn_limit: int = 450
    # app_time: lognormal body; median exp(mu). Calibration scale ~0.3 ms.
    app_mu: float = -8.1  # exp(-8.1) ~ 0.0003 s
    app_sigma: float = 0.3
    tail_p: float = 0.02  # heavy-tail mixture (R3.7): P(extra draw)
    tail_mean: float = 0.010  # exponential extra, mean 10 ms
    lock_hold: float = 0.0002  # fixed hold inside the lock (fit tunes it)
    seats_per_pool: int = 50
    sharded: bool = False
    assumed_client_timeout: float = 2.0  # wasted_work-OFF shedding horizon


@dataclass
class _Req:
    user_id: int
    pool: Pool
    respond: Callable[[Outcome], None]
    t_submit: float


class Server:
    def __init__(
        self,
        clock: Clock,
        queue: EventQueue,
        streams: RngStreams,
        fidelity: FidelityConfig,
        cfg: ServerConfig,
        t0: float,
    ) -> None:
        self.clock, self.queue = clock, queue
        self.fidelity, self.cfg, self.t0 = fidelity, cfg, t0
        self.rng = streams.get("service")
        self.inventory = Inventory(cfg.seats_per_pool, t0)
        self._locks: dict[Pool, FifoLock] = {}
        self._global_lock = FifoLock()
        self._busy = 0
        self._conns = 0
        self._accept: list[_Req] = []
        # counters for tests/metrics
        self.hard_errors_conn = 0
        self.hard_errors_queue = 0
        self.shed_stale = 0
        self.busy_seconds = 0.0

    # -- knobs ---------------------------------------------------------------
    def _bounded(self) -> bool:
        return self.fidelity.bounded_capacity

    def _lock_for(self, pool: Pool) -> FifoLock:
        if not self.cfg.sharded:
            return self._global_lock
        if pool not in self._locks:
            self._locks[pool] = FifoLock()
        return self._locks[pool]

    def _app_time(self) -> float:
        t = self.rng.lognormvariate(self.cfg.app_mu, self.cfg.app_sigma)
        if self.fidelity.heavy_tail_service and self.rng.random() < self.cfg.tail_p:
            t += self.rng.expovariate(1.0 / self.cfg.tail_mean)
        return t

    # -- Service protocol ----------------------------------------------------
    def submit(self, user_id: int, pool: Pool, respond: Callable[[Outcome], None]) -> None:
        req = _Req(user_id, pool, respond, self.clock.now())
        if self._bounded() and self._conns >= self.cfg.conn_limit:
            self.hard_errors_conn += 1
            self.queue.schedule_in(0.0, lambda: respond(Outcome.HARD_ERROR))
            return
        self._conns += 1
        if not self._bounded() or self._busy < self.cfg.workers:
            self._start(req)
        elif len(self._accept) < self.cfg.accept_queue:
            self._accept.append(req)  # bounded FIFO
        else:
            self._conns -= 1
            self.hard_errors_queue += 1  # drop-newest -> connection reset
            self.queue.schedule_in(0.0, lambda: respond(Outcome.HARD_ERROR))

    # -- service pipeline ----------------------------------------------------
    def _start(self, req: _Req) -> None:
        # wasted_work OFF: shed work whose client has certainly timed out —
        # the flattering lie where dead requests free capacity instantly
        if (
            not self.fidelity.wasted_work
            and self.clock.now() > req.t_submit + self.cfg.assumed_client_timeout
        ):
            self.shed_stale += 1
            self._conns -= 1
            self._pull_next()
            return
        self._busy += 1
        t_service_start = self.clock.now()
        app = self._app_time()
        if self.clock.now() < self.t0:
            # pre-T0 fast path: app logic only, clean "not open" (D10/S2)
            self.queue.schedule_in(
                app, lambda: self._finish(req, Outcome.NOT_OPEN, t_service_start)
            )
            return
        self.queue.schedule_in(app, lambda: self._acquire(req, t_service_start))

    def _acquire(self, req: _Req, t_service_start: float) -> None:
        if not self.fidelity.atomic_inventory:
            # read-then-write race (ablation): snapshot now, blind write later
            snapshot = self.inventory.read(req.pool)
            self.queue.schedule_in(
                self.cfg.lock_hold,
                lambda: self._complete_nonatomic(req, snapshot, t_service_start),
            )
            return
        lock = self._lock_for(req.pool)
        lock.acquire(self.queue, lambda: self._hold(req, lock, t_service_start))

    def _hold(self, req: _Req, lock: FifoLock, t_service_start: float) -> None:
        self.queue.schedule_in(
            self.cfg.lock_hold, lambda: self._complete(req, lock, t_service_start)
        )

    def _complete(self, req: _Req, lock: FifoLock, t_service_start: float) -> None:
        booked = self.inventory.try_book(req.pool, self.clock.now())
        lock.release(self.queue)
        self._finish(req, Outcome.BOOKED if booked else Outcome.SOLD_OUT, t_service_start)

    def _complete_nonatomic(self, req: _Req, snapshot: int, t_service_start: float) -> None:
        if snapshot > 0:
            self.inventory.write_nonatomic(req.pool, snapshot, self.clock.now())
            outcome = Outcome.BOOKED
        else:
            outcome = Outcome.SOLD_OUT
        self._finish(req, outcome, t_service_start)

    def _finish(self, req: _Req, outcome: Outcome, t_service_start: float) -> None:
        self.busy_seconds += self.clock.now() - t_service_start
        self._busy -= 1
        self._conns -= 1
        req.respond(outcome)
        self._pull_next()

    def _pull_next(self) -> None:
        while self._accept and self._busy < self.cfg.workers:
            self._start(self._accept.pop(0))
