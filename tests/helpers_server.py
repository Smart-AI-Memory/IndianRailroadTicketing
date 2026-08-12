"""P3 test harnesses: manual request batches and engine+real-server worlds."""

from __future__ import annotations

from tatkal_sim.config import FidelityConfig
from tatkal_sim.core import Clock, EventQueue, RngStreams
from tatkal_sim.model.server import Server, ServerConfig
from tatkal_sim.model.users import ClientConfig, ClientEngine
from tatkal_sim.model.workload import WorkloadConfig, generate_intents

T0 = WorkloadConfig().t0


def pct(xs: list[float], p: float) -> float:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(len(xs) * p))]


def manual_batch(
    n: int,
    *,
    fidelity: FidelityConfig | None = None,
    scfg: ServerConfig | None = None,
    seed: int = 1,
    pool_of=lambda i: (1, "AC", "D0"),
    at: float = T0,
):
    """Submit n bare requests at the same instant; return (latencies, outcomes, server).

    No client engine: measures the server pipeline in isolation.
    """
    fidelity = fidelity or FidelityConfig()
    scfg = scfg or ServerConfig()
    clock = Clock()
    queue = EventQueue(clock)
    streams = RngStreams(seed)
    server = Server(clock, queue, streams, fidelity, scfg, T0)
    latencies: list[float] = []
    outcomes: list[str] = []

    def fire(i: int) -> None:
        t_start = clock.now()

        def respond(outcome) -> None:
            latencies.append(clock.now() - t_start)
            outcomes.append(outcome.value)

        server.submit(i, pool_of(i), respond)

    for i in range(n):
        queue.schedule_at(at, lambda i=i: fire(i))
    queue.run(max_events=1_000_000)
    return latencies, outcomes, server


def server_world(
    *,
    seed: int = 1,
    fidelity: FidelityConfig | None = None,
    wcfg: WorkloadConfig | None = None,
    ccfg: ClientConfig | None = None,
    scfg: ServerConfig | None = None,
    max_events: int = 2_000_000,
):
    """Full engine + real Server world; returns (intents, engine, server)."""
    fidelity = fidelity or FidelityConfig()
    wcfg = wcfg or WorkloadConfig()
    ccfg = ccfg or ClientConfig()
    scfg = scfg or ServerConfig()
    clock = Clock()
    queue = EventQueue(clock)
    streams = RngStreams(seed)
    intents = generate_intents(wcfg, fidelity, streams)
    log: list = []  # shared: engine and server interleave into one stream
    server = Server(clock, queue, streams, fidelity, scfg, wcfg.t0, log=log)
    engine = ClientEngine(clock, queue, streams, fidelity, ccfg, wcfg, server, log=log)
    engine.start(intents)
    queue.run(max_events=max_events)
    return intents, engine, server
