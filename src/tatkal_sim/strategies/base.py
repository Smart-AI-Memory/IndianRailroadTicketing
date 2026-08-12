"""Admission strategies as service middleware (R4; task P6.1).

A strategy WRAPS a `Service` (ultimately the server) and intercepts
`submit`. Rungs compose cumulatively (D5): rung k's chain is rung k-1's
chain plus one mechanism, so each marginal delta isolates one addition:

    rung 0: server                       (naive: unbounded admission)
    rung 1: BoundedFifo(server)          (+ bounded concurrency + FIFO)
    rung 2: FastFail(BoundedFifo(...))   (+ cached sold-out fast reject)

The middleware pattern keeps the server model untouched: an admission
mechanism can only do what a real edge layer could — hold, forward, or
answer requests. It cannot reach into the server's internals.
"""

from __future__ import annotations

from dataclasses import dataclass

from tatkal_sim.core import Clock, EventQueue
from tatkal_sim.model.users import Service


@dataclass(frozen=True)
class RungParams:
    admit_limit: int = 8  # rung 1: knee-region concurrency bound (swept at P9)
    fastfail_staleness: float = 0.05  # rung 2: cache learning lag, seconds
    fastfail_reject_cost: float = 0.0005  # edge reject latency, seconds


def build_rung(
    k: int,
    server: Service,
    clock: Clock,
    queue: EventQueue,
    params: RungParams | None = None,
) -> Service:
    """The cumulative chain for rung k (0..2 at P6; P7 extends)."""
    from tatkal_sim.strategies.bounded_fifo import BoundedFifo
    from tatkal_sim.strategies.fast_fail import FastFail

    params = params or RungParams()
    svc: Service = server  # rung 0: naive — unbounded admission, bare server
    if k >= 1:
        svc = BoundedFifo(svc, limit=params.admit_limit)
    if k >= 2:
        svc = FastFail(
            svc,
            clock,
            queue,
            staleness=params.fastfail_staleness,
            reject_cost=params.fastfail_reject_cost,
        )
    if k >= 3:
        raise NotImplementedError(f"rung {k} lands in P7/P8")
    return svc
