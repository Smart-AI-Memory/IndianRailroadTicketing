"""Simulation configuration (task P0.2).

`FidelityConfig` exposes every R3 fidelity item as a named, toggleable
parameter (R3 acceptance). Defaults are ALL ON: the simulator's default
posture is maximum fidelity, and each toggle exists to measure the
direction of the flattering lie it would otherwise hide — see design.md
"Fidelity toggles" for the direction-of-effect table.

`bounded_capacity=False` is ablation-only (D10/C4): it is never enabled in
any ladder run, and exists to demonstrate what an infinitely elastic
backend hides.
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class FidelityConfig:
    """The ten R3 fidelity toggles. One field per R3 item, in order."""

    open_loop_arrivals: bool = True  # R3.1
    retries_enabled: bool = True  # R3.2
    bounded_capacity: bool = True  # R3.3 (off = ablation-only, never in ladder runs)
    atomic_inventory: bool = True  # R3.4
    t0_concentration: bool = True  # R3.5
    wasted_work: bool = True  # R3.6
    heavy_tail_service: bool = True  # R3.7
    zipf_demand: bool = True  # R3.8
    bot_cohort: bool = True  # R3.9
    user_identity: bool = True  # R3.10

    def to_json(self) -> str:
        """Serialise deterministically (sorted keys — R1 byte-identity)."""
        return json.dumps(dataclasses.asdict(self), sort_keys=True)

    @classmethod
    def from_json(cls, raw: str) -> FidelityConfig:
        """Parse from JSON; unknown keys are an error, never ignored.

        A silently dropped toggle would be a fidelity lie of its own —
        a config that claims a fidelity posture it does not have.
        """
        data = json.loads(raw)
        known = {f.name for f in dataclasses.fields(cls)}
        unknown = set(data) - known
        if unknown:
            raise ValueError(f"unknown FidelityConfig keys: {sorted(unknown)}")
        return cls(**data)

    def enabled_toggles(self) -> list[str]:
        """Names of enabled toggles — reports enumerate these (R3 acceptance)."""
        return [f.name for f in dataclasses.fields(self) if getattr(self, f.name)]
