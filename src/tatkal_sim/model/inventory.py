"""Atomic inventory with end-of-run invariants (R3.4; task P3.3).

Per pool `(train, class, date)`: integer seats decremented inside a lock
hold. Invariants — `sold + remaining == initial`, zero double-sells, zero
lost seats — are checkable after every run via `violations()`; the P5
runner calls it unconditionally, tests call it directly until then.

Pre-T0 guard (D10/S2): a decrement before T0 raises immediately — not a
recorded violation but a hard stop, because nothing legitimate can reach
it and continuing would corrupt every downstream number.

The non-atomic path (`read`/`write_nonatomic`) exists ONLY for the
`atomic_inventory=False` ablation: it models the read-then-write race
whose lost updates and oversells the invariants are built to catch.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tatkal_sim.model.workload import Pool


@dataclass
class _PoolState:
    initial: int
    remaining: int
    sold: int = 0


@dataclass
class Inventory:
    seats_per_pool: int
    t0: float
    _pools: dict[Pool, _PoolState] = field(default_factory=dict)
    first_decrement_t: float | None = None

    def _pool(self, pool: Pool) -> _PoolState:
        if pool not in self._pools:
            self._pools[pool] = _PoolState(self.seats_per_pool, self.seats_per_pool)
        return self._pools[pool]

    def _guard_t0(self, now: float) -> None:
        if now < self.t0:
            raise RuntimeError(f"inventory decrement before T0: t={now} < {self.t0}")

    # -- atomic path (inside a FifoLock hold) --------------------------------
    def try_book(self, pool: Pool, now: float) -> bool:
        st = self._pool(pool)
        if st.remaining <= 0:
            return False
        self._guard_t0(now)
        st.remaining -= 1
        st.sold += 1
        if self.first_decrement_t is None:
            self.first_decrement_t = now
        return True

    # -- non-atomic ablation path (atomic_inventory OFF) ---------------------
    def read(self, pool: Pool) -> int:
        return self._pool(pool).remaining

    def write_nonatomic(self, pool: Pool, snapshot_remaining: int, now: float) -> None:
        """Lost-update write: remaining := snapshot - 1, blind to interleaving."""
        self._guard_t0(now)
        st = self._pool(pool)
        st.remaining = snapshot_remaining - 1
        st.sold += 1
        if self.first_decrement_t is None:
            self.first_decrement_t = now

    # -- accounting ----------------------------------------------------------
    def totals(self) -> dict[str, int]:
        return {
            "initial": sum(p.initial for p in self._pools.values()),
            "remaining": sum(p.remaining for p in self._pools.values()),
            "sold": sum(p.sold for p in self._pools.values()),
        }

    def violations(self) -> list[str]:
        out = []
        for pool, st in sorted(self._pools.items()):
            if st.sold + st.remaining != st.initial:
                out.append(
                    f"{pool}: sold({st.sold}) + remaining({st.remaining}) != initial({st.initial})"
                )
            if st.sold > st.initial:
                out.append(f"{pool}: double-sell — sold({st.sold}) > initial({st.initial})")
            if st.remaining < 0:
                out.append(f"{pool}: negative remaining ({st.remaining})")
        return out

    def assert_ok(self) -> None:
        v = self.violations()
        if v:
            raise AssertionError("inventory invariants violated:\n" + "\n".join(v))
