"""tatkal_sim — deterministic discrete-event simulation of a Tatkal-style
booking spike.

Spec: docs/specs/tatkal-spike-prototype (requirements ratified 2026-08-11;
design approved D12). Built along the gated ladder in tasks.md.
"""

from tatkal_sim.config import FidelityConfig

__version__ = "0.0.1"
__all__ = ["FidelityConfig", "__version__"]
