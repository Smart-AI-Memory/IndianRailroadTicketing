"""Shared P2 test fixtures: stub services and a world-runner.

Stubs implement the `Service` protocol from model/users.py. They are
test-only stand-ins; P3's real server model replaces them everywhere
except these unit tests.
"""

from __future__ import annotations

from dataclasses import dataclass

from tatkal_sim.config import FidelityConfig
from tatkal_sim.core import Clock, EventQueue, RngStreams
from tatkal_sim.model.users import ClientConfig, ClientEngine, Outcome
from tatkal_sim.model.workload import WorkloadConfig, generate_intents


class StubService:
    """Fixed-delay service: pre-T0 -> NOT_OPEN; optional first-come capacity.

    `silent=True` never responds (drives the client-timeout path).
    `capacity=N` books the first N post-T0 submitters, SOLD_OUT after.
    """

    def __init__(
        self,
        clock: Clock,
        queue: EventQueue,
        t0: float,
        delay: float = 0.05,
        pre_t0_delay: float = 0.005,
        capacity: int | None = None,
        silent: bool = False,
    ) -> None:
        self.clock, self.queue, self.t0 = clock, queue, t0
        self.delay, self.pre_t0_delay = delay, pre_t0_delay
        self.capacity, self.silent = capacity, silent

    def submit(self, user_id, pool, respond) -> None:
        if self.silent:
            return
        if self.clock.now() < self.t0:
            self.queue.schedule_in(self.pre_t0_delay, lambda: respond(Outcome.NOT_OPEN))
            return
        if self.capacity is None:
            outcome = Outcome.BOOKED
        elif self.capacity > 0:
            self.capacity -= 1  # submit-order first-come
            outcome = Outcome.BOOKED
        else:
            outcome = Outcome.SOLD_OUT
        self.queue.schedule_in(self.delay, lambda: respond(outcome))


class ScriptService:
    """Responds per-request from a fixed outcome script (last repeats)."""

    def __init__(self, clock: Clock, queue: EventQueue, script: list[Outcome], delay=0.01):
        self.clock, self.queue, self.script, self.delay = clock, queue, list(script), delay
        self.calls = 0

    def submit(self, user_id, pool, respond) -> None:
        outcome = self.script[min(self.calls, len(self.script) - 1)]
        self.calls += 1
        self.queue.schedule_in(self.delay, lambda: respond(outcome))


@dataclass
class World:
    clock: Clock
    queue: EventQueue
    streams: RngStreams
    intents: list
    engine: ClientEngine
    service: object


def run_world(
    *,
    seed: int = 1,
    fidelity: FidelityConfig | None = None,
    wcfg: WorkloadConfig | None = None,
    ccfg: ClientConfig | None = None,
    service_factory=None,
    max_events: int = 1_000_000,
) -> World:
    fidelity = fidelity or FidelityConfig()
    wcfg = wcfg or WorkloadConfig()
    ccfg = ccfg or ClientConfig()
    clock = Clock()
    queue = EventQueue(clock)
    streams = RngStreams(seed)
    intents = generate_intents(wcfg, fidelity, streams)
    if service_factory is None:
        service = StubService(clock, queue, wcfg.t0)
    else:
        service = service_factory(clock, queue, wcfg)
    engine = ClientEngine(clock, queue, streams, fidelity, ccfg, wcfg, service)
    engine.start(intents)
    queue.run(max_events=max_events)
    return World(clock, queue, streams, intents, engine, service)
