"""v3 run orchestration (tatkal-v3 W1/W2): priced-entry arms.

A `V3Arm` is the v2 M2 lattice plus a mitigation:

    none     — PricedLotteryPool with policy=None: bit-identical to the
               v2 m2 arm (W1.1 acceptance; also the d = 0 and the
               unpriced continuity cells)
    verify   — A1: VerificationPolicy at `c_verify` (DC1)
    deposit  — A2: DepositPolicy at `d` (DC2/DC3, D17-corrected)
    regbound — A3: RegistrationBoundPolicy over the "a3" workload
               (DC4 deadline profile; "uniform" labelled variant)

Wiring mirrors `run_arm_v2_once` exactly — same streams, same server,
same push, same engine — so the policy is the only degree of freedom.
"""

from __future__ import annotations

import dataclasses as dc
from dataclasses import dataclass, field

from tatkal_sim.config import FidelityConfig
from tatkal_sim.core import Clock, EventQueue, RngStreams
from tatkal_sim.measure import metrics as metrics_mod
from tatkal_sim.measure.fitting import FIT_JSON, knee_variant, load_fit
from tatkal_sim.model.server import Server
from tatkal_sim.model.users import ClientConfig, Outcome
from tatkal_sim.model.users_v2 import V2ClientEngine
from tatkal_sim.model.workload_v2 import (
    OPERATING_WORKLOAD_V2,
    V2WorkloadConfig,
    generate_intents_v2,
)
from tatkal_sim.strategies.allocation import CostedPush
from tatkal_sim.strategies.base import build_rung
from tatkal_sim.strategies.mitigation import (
    DepositPolicy,
    PricedLotteryPool,
    RegistrationBoundPolicy,
    VerificationPolicy,
)

MITIGATIONS = ("none", "verify", "deposit", "regbound")


@dataclass(frozen=True)
class V3Arm:
    name: str
    mitigation: str = "none"
    c_verify: float = 1.0  # DC1 grid value (verify only)
    d: float = 0.5  # DC3 grid value (deposit only; d=0 -> use "none")
    wcfg: V2WorkloadConfig = field(default_factory=lambda: OPERATING_WORKLOAD_V2)
    ccfg: ClientConfig = field(default_factory=ClientConfig)
    fidelity: FidelityConfig = field(default_factory=FidelityConfig)
    variant: str = "fitted"
    c_push: float = 0.0
    seats: int = 25


def _policy(arm: V3Arm, seats_total: int):
    if arm.mitigation == "none":
        return None
    if arm.mitigation == "verify":
        return VerificationPolicy(arm.c_verify)
    if arm.mitigation == "deposit":
        return DepositPolicy(arm.d, arm.wcfg, seats_total)
    if arm.mitigation == "regbound":
        return RegistrationBoundPolicy()
    raise ValueError(f"unknown mitigation: {arm.mitigation}")


def run_arm_v3_once(arm: V3Arm, seed: int) -> dict:
    """One seeded v3 run — mirrors run_arm_v2_once with a priced pool."""
    if arm.mitigation not in MITIGATIONS:
        raise ValueError(f"unknown mitigation: {arm.mitigation}")
    clock = Clock()
    queue = EventQueue(clock)
    streams = RngStreams(seed)
    workload_kind = "a3" if arm.mitigation == "regbound" else "m2"
    wcfg = arm.wcfg
    if workload_kind == "a3" and wcfg.t0 < wcfg.reg_window:
        # registration window must fit inside sim time (m1 precedent:
        # t0-relative shift is free in event time, changes no physics)
        wcfg = dc.replace(wcfg, t0=wcfg.reg_window + 30.0)
    arm = dc.replace(arm, wcfg=wcfg)
    intents = generate_intents_v2(arm.wcfg, arm.fidelity, streams, workload_kind)
    log: list = []
    scfg = knee_variant(arm.variant, load_fit(FIT_JSON)["params"])
    scfg = dc.replace(scfg, seats_per_pool=arm.seats, sharded=False)
    server = Server(clock, queue, streams, arm.fidelity, scfg, arm.wcfg.t0, log=log)

    cost_factor = arm.c_push * server.cfg.status_cost_factor
    push = CostedPush(server, clock, queue, cost_factor=cost_factor, log=log)

    chain = build_rung(2, server, clock, queue, None)
    seats_total = arm.seats * arm.wcfg.n_trains * len(arm.wcfg.classes)
    service = PricedLotteryPool(
        chain,
        server,
        clock,
        queue,
        streams,
        arm.wcfg,
        intents,
        push,
        log,
        policy=_policy(arm, seats_total),
    )

    if workload_kind == "a3":
        # registration one-shots are costed server work (v2 M1 carry;
        # design §A3, B6's measured stream): submit + completion logged
        # so the deadline-surface drain is derivable per registrant
        def _reg_work(uid: int) -> None:
            log.append(("reg_submit", clock.now(), uid))
            server.submit_light_at(
                uid,
                Outcome.QUEUE_POSITION,
                lambda o, u=uid: log.append(("reg_done", clock.now(), u)),
                server.cfg.status_cost_factor,
            )

        for i in intents:
            if i.t_register is not None:
                queue.schedule_at(i.t_register, lambda uid=i.user_id: _reg_work(uid))

    engine = V2ClientEngine(
        clock,
        queue,
        streams,
        arm.fidelity,
        arm.ccfg,
        arm.wcfg,
        service,
        log=log,
        arm_kind="m2",  # a3 keeps M2 client semantics (poll-until-push)
    )
    engine.bind_camp_rng(streams)
    service.bind_engine(engine)
    push.bind(engine.push_definitive)

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
