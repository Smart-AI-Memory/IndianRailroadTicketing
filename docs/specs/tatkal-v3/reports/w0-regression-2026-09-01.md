# W0 — regression anchor, complete (2026-09-01)

**Tasks:** W0.1, W0.2 (tasks.md). **Tree:** `main` at the D17
amendments merge (8e3a1fe) — the v3 tree before any W1 code.

## W0.1 — full suite, untouched

`pytest tests/` on the v3 tree: **147 passed, 0 failed, 0 modified**
(84 s). The suite includes the v2 golden-snapshot anchor test
(`tests/test_v0_anchor.py`), so the v1-era anchor carries in CI-style
runs as well.

## W0.2 — designated v2 arm reproduced bit-identically

Designated arm per tasks.md: **M2, p = 0.1, fitted**, 20 seeds.
Re-run on the v3 tree via the v2 cell logic (`tools/v6_sweeps.py`
`run_cell`, unmodified) and compared against the archived record
(`../tatkal-v2/reports/v6-sweeps-data.json`, cell `m2-p0.1-fitted`,
full per-seed payload: metrics, two-clock, fairness, taxonomy).

**Result: BIT-IDENTICAL on all 20 seeds** — the registered exact
tolerance (v2 D16, carried by v3 requirements R1) is met with zero
deviation.

## Environment note (recorded, no action owed)

The project venv was missing `pytest` at W0 start despite the
`requirements.txt` pin — venv drift, presumably from a rebuild.
Reinstalled exactly the pinned version (`pytest==9.1.1`); no other
drift touched. The starter-queued CI workflow would catch this class
of drift mechanically.

## Exit

W0 exit criterion met: v3 development cannot silently alter v1/v2
physics — the anchor is fixed before W1 writes a line.
