"""Named RNG streams from a master seed (R1, R6; task P1.2).

A master seed derives independent child streams via
`sha256(master_seed <US> stream_name)` -> `random.Random`. One stream per
concern (`arrivals`, `service`, `retry`, `bots`, `abandon`, `stats`, ...):
adding a mechanism, or drawing more variates in one stream, cannot perturb
any other stream — the property that keeps paired-seed comparisons (D6)
low-variance and the bootstrap (D10/S4) byte-reproducible.

The 0x1f unit-separator between seed and name prevents concatenation
ambiguity (seed 1 + name "2x" vs seed 12 + name "x").
"""

from __future__ import annotations

import hashlib
import random


def derive_stream(master_seed: int, name: str) -> random.Random:
    """A fresh, deterministic `random.Random` for (master_seed, name)."""
    digest = hashlib.sha256(f"{master_seed}\x1f{name}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


class RngStreams:
    """Per-run registry of named streams; same name -> same live stream.

    Components ask for their stream by name and keep drawing from it;
    asking again mid-run returns the SAME object (state continues), never
    a reset copy — a reset would silently replay variates.
    """

    def __init__(self, master_seed: int) -> None:
        self.master_seed = master_seed
        self._streams: dict[str, random.Random] = {}

    def get(self, name: str) -> random.Random:
        if name not in self._streams:
            self._streams[name] = derive_stream(self.master_seed, name)
        return self._streams[name]
