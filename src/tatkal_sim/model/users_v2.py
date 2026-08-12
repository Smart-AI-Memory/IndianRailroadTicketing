"""v2 client engine: camp re-arrival under M3 (tatkal-v2 V3.3, D13.3).

Everything else is v1 `ClientEngine` behaviour unchanged. Camp bots in
an M3 arm treat a retryable reject (MECH_REJECT from the tranche gate,
or SOLD_OUT mid-pacing) as "wait for the next tranche": they re-submit
within 50 ms of the next tranche open instead of taking the definitive.
Once the final tranche has opened, v1 semantics resume — the last
sold-out is the real one.
"""

from __future__ import annotations

from tatkal_sim.model.users import ClientEngine, Outcome, _IntentState
from tatkal_sim.model.workload_v2 import V2Intent, V2WorkloadConfig

_CAMP_RETRYABLE = {Outcome.MECH_REJECT, Outcome.SOLD_OUT}


class V2ClientEngine(ClientEngine):
    def __init__(self, *args, arm_kind: str = "eng", **kw) -> None:
        super().__init__(*args, **kw)
        self.arm_kind = arm_kind
        # dedicated stream: v1 draws stay anchored
        self._camp_rng = None

    def bind_camp_rng(self, streams) -> None:
        self._camp_rng = streams.get("camp")

    def _next_tranche_open(self, now: float) -> float | None:
        wcfg = self.wcfg
        if not isinstance(wcfg, V2WorkloadConfig):
            return None
        spacing = wcfg.pace_horizon / wcfg.pace_tranches
        for j in range(1, wcfg.pace_tranches):
            t = wcfg.t0 + j * spacing
            if t > now:
                return t
        return None

    def _on_outcome(self, st: _IntentState, outcome: Outcome) -> None:
        intent = st.intent
        if (
            self.arm_kind == "m3"
            and isinstance(intent, V2Intent)
            and intent.strategy == "camp"
            and outcome in _CAMP_RETRYABLE
        ):
            t_next = self._next_tranche_open(self.clock.now())
            if t_next is not None:
                jitter = self._camp_rng.uniform(0.0, 0.05) if self._camp_rng else 0.0
                self.log.append(("camp_rearm", self.clock.now(), intent.user_id))
                self.queue.schedule_at(t_next + jitter, lambda: self._submit(st))
                return
        super()._on_outcome(st, outcome)
