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
    # App-server congestion (P4 model extension, flagged to chair): effective
    # app_time scales by (1 + congestion_k * active_conns). This is the
    # app-tier component the sharded8 control identified — the calibrated
    # system's throughput DECLINES with concurrency (GIL/thread scheduling),
    # which no fixed-service-time queue can reproduce. Default 0: inert
    # everywhere except calibration-fitted profiles.
    congestion_k: float = 0.0
    congestion_gamma: float = 1.0  # factor = 1 + k * conns**gamma (sublinear GIL shape)
    # Hold-stall (P4 refinement round, chair-directed): a rare long stall
    # drawn INSIDE the lock hold. A stalled writer blocks every queued
    # waiter — the GIL-convoy burstiness the measured p99 S-curve carries.
    # Zero by default: inert outside calibration-fitted profiles.
    hold_stall_p: float = 0.0
    hold_stall_mean: float = 0.0
    status_cost_factor: float = 0.2  # R8: status check = app_time / 5 (design)
    seats_per_pool: int = 50
    sharded: bool = False
    assumed_client_timeout: float = 2.0  # wasted_work-OFF shedding horizon


@dataclass
class _Req:
    user_id: int
    pool: Pool
    respond: Callable[[Outcome], None]
    t_submit: float
    # status-check path (R8): when set, the request takes a worker for
    # app_time * cost_factor and answers with this outcome — no lock, no
    # inventory. Status checks contend for the SAME capacity as bookings.
    light_outcome: Outcome | None = None
    cost_factor: float = 1.0


class Server:
    def __init__(
        self,
        clock: Clock,
        queue: EventQueue,
        streams: RngStreams,
        fidelity: FidelityConfig,
        cfg: ServerConfig,
        t0: float,
        log: list | None = None,
    ) -> None:
        self.clock, self.queue = clock, queue
        self.fidelity, self.cfg, self.t0 = fidelity, cfg, t0
        self.log = log if log is not None else []  # shared with the engine
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
        if (
            self.fidelity.heavy_tail_service
            and self.cfg.tail_mean > 0
            and self.rng.random() < self.cfg.tail_p
        ):
            t += self.rng.expovariate(1.0 / self.cfg.tail_mean)
        if self.cfg.congestion_k:
            t *= 1.0 + self.cfg.congestion_k * self._conns**self.cfg.congestion_gamma
        return t

    # -- Service protocol ----------------------------------------------------
    def submit(self, user_id: int, pool: Pool, respond: Callable[[Outcome], None]) -> None:
        self._submit_req(_Req(user_id, pool, respond, self.clock.now()))

    def submit_light(
        self, user_id: int, outcome: Outcome, respond: Callable[[Outcome], None]
    ) -> None:
        """Status-check request (R8): same conn/worker gauntlet as a
        booking, a fraction of the app time, the caller's outcome back.
        The waiting room uses this so its status stream genuinely contends
        for server capacity."""
        self._submit_req(
            _Req(
                user_id,
                (0, "status", "-"),
                respond,
                self.clock.now(),
                light_outcome=outcome,
                cost_factor=self.cfg.status_cost_factor,
            )
        )

    def submit_light_at(
        self,
        user_id: int,
        outcome: Outcome,
        respond: Callable[[Outcome], None],
        cost_factor: float,
    ) -> None:
        """v2: light request at an explicit cost factor (costed push /
        registration work, decisions.md D6/D14.2). Same gauntlet as
        submit_light; additive — v1 paths never call it."""
        self._submit_req(
            _Req(
                user_id,
                (0, "push", "-"),
                respond,
                self.clock.now(),
                light_outcome=outcome,
                cost_factor=cost_factor,
            )
        )

    def _submit_req(self, req: _Req) -> None:
        respond = req.respond
        if self._bounded() and self._conns >= self.cfg.conn_limit:
            self.hard_errors_conn += 1
            self.queue.schedule_in(0.0, lambda: respond(Outcome.HARD_ERROR))
            return
        self._conns += 1
        # fast path only when NO ONE is already waiting: a new arrival must
        # not barge past the accept queue into a just-freed worker slot
        # (closed-loop clients would otherwise starve queued requests)
        if not self._bounded() or (self._busy < self.cfg.workers and not self._accept):
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
        app = self._app_time() * req.cost_factor
        if req.light_outcome is not None:
            # status path (R8): worker held for the light app time, no lock
            self.queue.schedule_in(
                app, lambda: self._finish(req, req.light_outcome, t_service_start)
            )
            return
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
        hold = self.cfg.lock_hold
        if self.cfg.hold_stall_mean > 0 and self.rng.random() < self.cfg.hold_stall_p:
            # convoy: this stall is served to every waiter queued behind it
            hold += self.rng.expovariate(1.0 / self.cfg.hold_stall_mean)
        self.queue.schedule_in(hold, lambda: self._complete(req, lock, t_service_start))

    def _complete(self, req: _Req, lock: FifoLock, t_service_start: float) -> None:
        booked = self.inventory.try_book(req.pool, self.clock.now())
        if booked:
            self.log.append(("sold", self.clock.now(), req.user_id, req.pool))
        lock.release(self.queue)
        self._finish(req, Outcome.BOOKED if booked else Outcome.SOLD_OUT, t_service_start)

    def _complete_nonatomic(self, req: _Req, snapshot: int, t_service_start: float) -> None:
        if snapshot > 0:
            self.inventory.write_nonatomic(req.pool, snapshot, self.clock.now())
            self.log.append(("sold", self.clock.now(), req.user_id, req.pool))
            outcome = Outcome.BOOKED
        else:
            outcome = Outcome.SOLD_OUT
        self._finish(req, outcome, t_service_start)

    def _finish(self, req: _Req, outcome: Outcome, t_service_start: float) -> None:
        busy = self.clock.now() - t_service_start
        self.busy_seconds += busy
        self._busy -= 1
        self._conns -= 1
        # served BEFORE respond: metrics pair a served entry with a
        # stale_response at the same (t, uid) to attribute wasted work.
        # 6th field: full in-server wait (submit -> response) for the R8
        # per-stream saturation criterion.
        self.log.append(
            (
                "served",
                self.clock.now(),
                req.user_id,
                repr(busy),
                outcome.value,
                repr(self.clock.now() - req.t_submit),
            )
        )
        req.respond(outcome)
        self._pull_next()

    def _pull_next(self) -> None:
        while self._accept and self._busy < self.cfg.workers:
            self._start(self._accept.pop(0))
