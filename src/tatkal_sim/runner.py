"""Run orchestration.

P1.3 puts the determinism harness here: `run_trivial` exercises the whole
core (clock, event cascade, two rng streams) and returns a plain dict;
`result_digest` canonicalises it to a sha256 over sorted-key JSON. R1's
acceptance — identical seeds, byte-identical results — is asserted over
this digest in tests/test_determinism.py.

The seed-sweep runner (arms x seeds, byte-identical traces per seed) lands
here in task P5.2 and reuses the same digest discipline.
"""

from __future__ import annotations

import hashlib
import json

from tatkal_sim.core import Clock, EventQueue, RngStreams


def result_digest(result: dict) -> str:
    """Canonical digest: sha256 of sorted-key JSON. Byte-level, on purpose."""
    return hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()


def run_trivial(master_seed: int, n_arrivals: int = 100) -> dict:
    """A trivial workload exercising clock + cascade + rng streams (P1.3).

    n_arrivals arrivals at exponential inter-arrival times; each schedules
    its completion after an exponential service draw. No server, no
    inventory — this exists purely so determinism is testable before P2/P3
    give the events any meaning.
    """
    clock = Clock()
    queue = EventQueue(clock)
    streams = RngStreams(master_seed)
    arrivals = streams.get("arrivals")
    service = streams.get("service")

    completion_log: list[tuple[int, float]] = []

    def complete(i: int) -> None:
        completion_log.append((i, clock.now()))

    def arrive(i: int) -> None:
        queue.schedule_in(service.expovariate(1.0), lambda: complete(i))

    t = 0.0
    for i in range(n_arrivals):
        t += arrivals.expovariate(1.0)
        queue.schedule_at(t, lambda i=i: arrive(i))

    processed = queue.run()

    return {
        "master_seed": master_seed,
        "events_processed": processed,
        "completions": len(completion_log),
        "final_time": repr(clock.now()),  # repr: full float precision, byte-stable
        "log_sha256": hashlib.sha256(repr(completion_log).encode()).hexdigest(),
    }
