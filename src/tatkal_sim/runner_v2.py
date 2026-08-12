"""v2 run orchestration (tatkal-v2 V2/V3): arms, wiring, one seeded run.

A `V2Arm` is (kind, workload, c_push grid value, knee variant [+ rung
for engineering arms]). Kinds:

    eng  — v1 ladder rung under the v2 population (V5 baselines, D12)
    m1   — PreRegAllocation over the rung-2 chain
    m2   — LotteryPool over the rung-2 chain
    m3   — PacedDrain over the rung-2 chain (+ camp re-arrival client)
    r3p  — v1 rung 4 with pushes routed through CostedPush (R3')

`c_push` is the D14.2 grid value in units of `status_service_time`;
the effective server cost factor is c_push * status_cost_factor. The
zero cell is the v1-continuity anchor (V3.4 acceptance).
"""

from __future__ import annotations

import dataclasses as dc
from dataclasses import dataclass, field

from tatkal_sim.config import FidelityConfig
from tatkal_sim.core import Clock, EventQueue, RngStreams
from tatkal_sim.measure import metrics as metrics_mod
from tatkal_sim.measure.fitting import FIT_JSON, knee_variant, load_fit
from tatkal_sim.model.server import Server
from tatkal_sim.model.users import ClientConfig
from tatkal_sim.model.users_v2 import V2ClientEngine
from tatkal_sim.model.workload_v2 import (
    OPERATING_WORKLOAD_V2,
    V2WorkloadConfig,
    generate_intents_v2,
)
from tatkal_sim.strategies.allocation import (
    CostedPush,
    LotteryPool,
    PacedDrain,
    PreRegAllocation,
)
from tatkal_sim.strategies.base import build_rung

#: D14.2 registered grid, units of status_service_time.
C_PUSH_GRID = (0.0, 0.25, 0.5, 1.0, 2.0)

V2_KINDS = ("eng", "m1", "m2", "m3", "r3p")


@dataclass(frozen=True)
class V2Arm:
    name: str
    kind: str  # eng | m1 | m2 | m3 | r3p
    wcfg: V2WorkloadConfig = field(default_factory=lambda: OPERATING_WORKLOAD_V2)
    ccfg: ClientConfig = field(default_factory=ClientConfig)
    fidelity: FidelityConfig = field(default_factory=FidelityConfig)
    variant: str = "fitted"
    rung: int = 2  # eng kind only
    c_push: float = 0.0  # D14.2 grid value (x status_service_time)
    seats: int = 25


def _server_cfg(arm: V2Arm):
    scfg = knee_variant(arm.variant, load_fit(FIT_JSON)["params"])
    # cumulative ladder (v1 D5): sharding applies from rung 3 up, and r3p
    # IS rung 4 — it must carry sharding or it re-runs a different arm
    sharded = arm.kind == "r3p" or (arm.kind == "eng" and arm.rung >= 3)
    return dc.replace(scfg, seats_per_pool=arm.seats, sharded=sharded)


def run_arm_v2_once(arm: V2Arm, seed: int) -> dict:
    """One seeded run -> v1 R6 metrics dict + the raw log for v2 metrics."""
    if arm.kind not in V2_KINDS:
        raise ValueError(f"unknown v2 arm kind: {arm.kind}")
    clock = Clock()
    queue = EventQueue(clock)
    streams = RngStreams(seed)
    workload_kind = {"eng": "eng", "r3p": "eng"}.get(arm.kind, arm.kind)
    wcfg = arm.wcfg
    if arm.kind == "m1" and wcfg.t0 < wcfg.reg_window:
        # the registration window must fit inside sim time (clock starts
        # at 0); all workload times are t0-relative, so shifting t0 is
        # free in event-driven time and changes no physics
        wcfg = dc.replace(wcfg, t0=wcfg.reg_window + 30.0)
    arm = dc.replace(arm, wcfg=wcfg)
    intents = generate_intents_v2(arm.wcfg, arm.fidelity, streams, workload_kind)
    log: list = []
    server = Server(clock, queue, streams, arm.fidelity, _server_cfg(arm), arm.wcfg.t0, log=log)

    cost_factor = arm.c_push * server.cfg.status_cost_factor
    push = CostedPush(server, clock, queue, cost_factor=cost_factor, log=log)

    rung = arm.rung if arm.kind == "eng" else (4 if arm.kind == "r3p" else 2)
    chain = build_rung(rung, server, clock, queue, None)

    alloc = None
    if arm.kind == "m1":
        service = PreRegAllocation(
            chain, server, clock, queue, streams, arm.wcfg, intents, push, log
        )
        alloc = service
    elif arm.kind == "m2":
        service = LotteryPool(chain, server, clock, queue, streams, arm.wcfg, intents, push, log)
        alloc = service
    elif arm.kind == "m3":
        service = PacedDrain(chain, server, clock, queue, arm.wcfg, log)
    else:
        service = chain

    engine = V2ClientEngine(
        clock,
        queue,
        streams,
        arm.fidelity,
        arm.ccfg,
        arm.wcfg,
        service,
        log=log,
        arm_kind=arm.kind,
    )
    engine.bind_camp_rng(streams)
    if alloc is not None:
        alloc.bind_engine(engine)
    push.bind(engine.push_definitive)

    # waiting-room pushes (eng rung>=4, r3p) route through CostedPush:
    # at c_push=0 that is exactly the v1 free-push channel (V3.4).
    layer = service
    while layer is not server:
        if hasattr(layer, "bind_push"):
            layer.bind_push(push.deliver)
        layer = getattr(layer, "inner", server)

    engine.start(intents)
    queue.run(max_events=5_000_000)
    server.inventory.assert_ok()
    result = metrics_mod.compute(
        log,
        intents,
        t0=arm.wcfg.t0,
        inventory_totals=server.inventory.totals(),
        inventory_violations=server.inventory.violations(),
        identity_on=arm.fidelity.user_identity,
        run_end=clock.now(),
    )
    return {"metrics": result, "log": log, "intents": intents}


def sweep_v2(arms: list[V2Arm], seeds: list[int]) -> dict[str, dict[int, dict]]:
    return {arm.name: {s: run_arm_v2_once(arm, s)["metrics"] for s in seeds} for arm in arms}
