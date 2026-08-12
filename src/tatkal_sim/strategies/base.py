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
    room_window: int = 8  # rung 4: concurrent forwarded tokens
    # rung 5: the static bound moves inside and becomes adaptive; the room
    # window widens so the limiter is the binding constraint (part of the
    # one-mechanism swap, documented in reports)
    room_window_adaptive: int = 64
    adaptive_target_s: float = 0.00684  # 10 x p99_knee (D8)
    classifier_params: object | None = None  # rung 6: None -> FROZEN_PARAMS
    force_classifier: bool = False  # out-of-order arms: classifier below rung 6


def build_rung(
    k: int,
    server: Service,
    clock: Clock,
    queue: EventQueue,
    params: RungParams | None = None,
) -> Service:
    """The cumulative chain for rung k (D5).

    rung 0: server (naive)
    rung 1: BoundedFifo(server)
    rung 2: FastFail(BoundedFifo(server))            <- R5 strong baseline
    rung 3: rung 2 chain; sharding lives in the Arm's ServerConfig
    rung 4: WaitingRoom(FastFail(BoundedFifo(server)))
    rung 5: WaitingRoom(FastFail(AdaptiveLimit(server)))
    """
    from tatkal_sim.strategies.adaptive import AdaptiveLimit
    from tatkal_sim.strategies.bounded_fifo import BoundedFifo
    from tatkal_sim.strategies.fast_fail import FastFail
    from tatkal_sim.strategies.waiting_room import WaitingRoom

    params = params or RungParams()
    svc: Service = server  # rung 0: naive — unbounded admission, bare server
    if k >= 1:
        if k >= 5:  # the one-mechanism swap: static bound -> adaptive
            svc = AdaptiveLimit(
                svc,
                clock,
                target_s=params.adaptive_target_s,
                start=float(params.admit_limit),
            )
        else:
            svc = BoundedFifo(svc, limit=params.admit_limit)
    if k >= 2:
        svc = FastFail(
            svc,
            clock,
            queue,
            staleness=params.fastfail_staleness,
            reject_cost=params.fastfail_reject_cost,
        )
    # k >= 3: sharding is a ServerConfig change, applied by ladder_arm
    if k >= 4:
        classifier = None
        if k >= 6 or params.force_classifier:  # verdict -> two-priority queue
            from tatkal_sim.strategies.bot_classifier import (
                FROZEN_PARAMS,
                BotClassifier,
            )

            cp = params.classifier_params or FROZEN_PARAMS
            classifier = BotClassifier(cp, server.t0)
        svc = WaitingRoom(
            svc,
            server,
            clock,
            queue,
            window=params.room_window if k < 5 else params.room_window_adaptive,
            classifier=classifier,
        )
    if k >= 7:
        raise NotImplementedError(f"no rung {k} exists (R7.3 omitted, D11)")
    return svc
