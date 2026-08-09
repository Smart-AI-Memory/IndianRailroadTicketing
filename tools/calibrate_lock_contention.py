#!/usr/bin/env python3
"""R2 calibration — measure the throughput-vs-concurrency curve of a contended
seat decrement.

WHY THIS EXISTS. requirements.md R2 says the single most decisive parameter in
the whole experiment is the SHAPE of the throughput curve past its knee: does
throughput PLATEAU or COLLAPSE? If it plateaus, admission control has nothing
to save and the headline result evaporates. Assuming that shape rather than
measuring it makes every downstream number an artifact of the modeller.

WHAT IT MEASURES. N concurrent OS processes contend for one row — the hot key,
modelling "everybody wants the same train" — each doing:

    BEGIN IMMEDIATE; UPDATE seats SET remaining = remaining - 1 ...; COMMIT

Real processes, not threads: the GIL would serialise threads and manufacture a
flattering plateau. Real file-lock contention with a real busy-timeout, so
waiting is measured rather than assumed.

LIMITATION — READ BEFORE TRUSTING THE NUMBERS. This uses SQLite, whose writer
lock serialises ALL writes database-wide. Postgres takes a per-ROW lock, so it
serialises only same-row contention and shards cleanly across different trains.
Therefore:

  - For the HOT-KEY case (one train, everyone contending) SQLite is a fair
    analogue — that resource is serialised under either engine.
  - For the SHARDED case (R4 rung 3) SQLite OVERSTATES contention, because
    different trains would not actually block each other in Postgres.

So these numbers calibrate the hot-key knee only. Rerun against Postgres with
SELECT FOR UPDATE before trusting any sharding result. That run is still owed.

Usage:  python3 tools/calibrate_lock_contention.py [--quick]
Output: CSV on stdout, summary on stderr.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import os
import sqlite3
import statistics
import sys
import tempfile
import time

BUSY_TIMEOUT_MS = 5000
SEATS = 10_000_000  # large: we measure service capacity, not the sell-out race


def _worker(db_path: str, duration: float, start_at: float) -> tuple[list[float], int]:
    """Run contended decrements for `duration`, starting at wall-clock `start_at`.

    Synchronised by a shared start TIMESTAMP rather than a multiprocessing
    Barrier: a Barrier + Queue pair deadlocked here under fork on macOS (the
    parent blocked in Queue.get while the child never reached put). A timestamp
    needs no shared primitive and still makes every worker begin together,
    which is the point — this models a spike, not a ramp.
    """
    conn = sqlite3.connect(db_path, timeout=BUSY_TIMEOUT_MS / 1000)
    conn.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
    latencies: list[float] = []
    errors = 0
    while time.time() < start_at:  # spin to the shared instant
        pass
    deadline = time.perf_counter() + duration
    while time.perf_counter() < deadline:
        t0 = time.perf_counter()
        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "UPDATE seats SET remaining = remaining - 1 WHERE id = 1 AND remaining > 0"
            )
            conn.commit()
            latencies.append((time.perf_counter() - t0) * 1000.0)
        except sqlite3.OperationalError:
            errors += 1
            try:
                conn.rollback()
            except sqlite3.Error:
                pass
    conn.close()
    return latencies, errors


def run_level(concurrency: int, duration: float) -> dict:
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE seats (id INTEGER PRIMARY KEY, remaining INTEGER)")
    conn.execute("INSERT INTO seats VALUES (1, ?)", (SEATS,))
    conn.commit()
    conn.close()

    # Give every worker time to spawn and reach its spin loop before the shared
    # start instant, so the measurement covers steady contention rather than
    # process-startup skew. Scales with concurrency: 64 spawns are not instant.
    start_at = time.time() + 1.0 + concurrency * 0.02

    all_lat: list[float] = []
    errors = 0
    with cf.ProcessPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(_worker, db_path, duration, start_at) for _ in range(concurrency)]
        for fut in futures:
            lat, err = fut.result(timeout=60 + duration + concurrency)
            all_lat.extend(lat)
            errors += err
    # Every worker runs for exactly `duration` after the shared start instant,
    # all overlapping — so the measurement window IS duration. Using elapsed
    # wall time would fold in spawn and spin-wait and understate throughput.
    wall = duration

    os.unlink(db_path)
    all_lat.sort()

    def pct(p: float) -> float:
        if not all_lat:
            return float("nan")
        return all_lat[min(len(all_lat) - 1, int(len(all_lat) * p))]

    return {
        "concurrency": concurrency,
        "throughput": len(all_lat) / wall if wall else 0.0,
        "ops": len(all_lat),
        "errors": errors,
        "p50": pct(0.50),
        "p95": pct(0.95),
        "p99": pct(0.99),
        "mean": statistics.fmean(all_lat) if all_lat else float("nan"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="1 rep, shorter runs")
    args = ap.parse_args()

    levels = [1, 2, 4, 8, 16, 32, 64]
    reps = 1 if args.quick else 3
    duration = 1.0 if args.quick else 2.0

    print("concurrency,rep,throughput_ops_s,p50_ms,p95_ms,p99_ms,errors")
    best = {"throughput": 0.0, "concurrency": 0}
    curve: dict[int, list[float]] = {}
    for c in levels:
        for rep in range(reps):
            r = run_level(c, duration)
            print(
                f"{r['concurrency']},{rep},{r['throughput']:.1f},"
                f"{r['p50']:.3f},{r['p95']:.3f},{r['p99']:.3f},{r['errors']}"
            )
            sys.stdout.flush()
            curve.setdefault(c, []).append(r["throughput"])
            if r["throughput"] > best["throughput"]:
                best = {"throughput": r["throughput"], "concurrency": c, **r}

    med = {c: statistics.median(v) for c, v in curve.items()}
    knee_c = max(med, key=lambda k: med[k])
    peak = med[knee_c]
    tail = med[levels[-1]]
    ratio = tail / peak if peak else float("nan")

    print("\n--- SUMMARY ---", file=sys.stderr)
    print(f"peak throughput      : {peak:.1f} ops/s at concurrency {knee_c}", file=sys.stderr)
    print(f"throughput at C={levels[-1]:<9}: {tail:.1f} ops/s", file=sys.stderr)
    print(f"retention past knee  : {ratio:.1%} of peak", file=sys.stderr)
    verdict = (
        "COLLAPSE (admission control has something to save)"
        if ratio < 0.75
        else "PLATEAU (admission control saves little — headline result at risk)"
    )
    print(f"curve shape          : {verdict}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
