#!/usr/bin/env python3
"""R2 calibration sweep — drive tools/r2_server.py and measure BOTH regimes.

Why two regimes (see requirements.md R2, "Calibration status"): the 2026-08-09
SQLite run conflated a synchronized-start transient with the steady-state
curve, and its headline tail number was withdrawn. This harness measures the
two things separately, on purpose:

  STEADY STATE — each worker's first post-T0 request is EXCLUDED. This is the
  throughput-vs-concurrency curve that fits the simulator's service model and
  sets N_knee / C_peak / p99_knee.

  T0 CONVOY — each worker's first post-T0 request, all fired at a shared
  wall-clock instant, reported as its own distribution. This is a deliberate
  miniature of the Tatkal opening stampede (R3.5), not noise: it shows what
  an N-deep simultaneous arrival does under the engine's queueing discipline.

Worker model: min(12, N) OS processes, each running its share of N client
threads. Threads block on HTTP I/O (GIL released), so threads-per-process is
safe; processes bound the GIL's share of the measurement. Each thread makes
one UNTIMED warmup request before T0 so TCP setup, server-thread spawn, and
DB-backend fork are paid before the window — the convoy measures lock
queueing, not connection setup.

The database is a throwaway local Postgres instance (Homebrew binaries, data
dir outside the repo, no service registered):

  PGBIN=/opt/homebrew/opt/postgresql@17/bin
  $PGBIN/initdb -D /tmp/r2-pgdata -U r2 --auth=trust -E UTF8
  LC_ALL=C $PGBIN/pg_ctl -D /tmp/r2-pgdata \
    -o "-p 54329 -c max_connections=450 -c listen_addresses=127.0.0.1" start
  $PGBIN/createdb -p 54329 -U r2 r2

(LC_ALL=C works around macOS "postmaster became multithreaded" at startup.
max_connections must exceed the top concurrency level: one server thread and
one DB backend per client connection, and capping connections below offered
concurrency would itself be an admission mechanism — the thing the naive
measurement must not contain.)

Usage:
  .venv/bin/python tools/calibrate_r2.py --out calibration.csv [--quick]

Writes CSV to --out, human summary + derived constants to stderr.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import platform
import statistics
import subprocess
import sys
import threading
import time
from http.client import HTTPConnection

import psycopg

DEFAULT_DSN = "postgresql://r2@127.0.0.1:54329/r2"
TRAINS = 8  # rows pre-created; hot-key mode uses only id=1
SEATS = 10_000_000  # large: measures service capacity, not the sell-out race


# ----------------------------------------------------------------- client side
def _one_request(hc: HTTPConnection, train: int) -> tuple[float, bool]:
    t0 = time.perf_counter()
    hc.request("POST", f"/book?train={train}")
    resp = hc.getresponse()
    resp.read()
    return (time.perf_counter() - t0) * 1000.0, resp.status == 200


def _proc_worker(
    port: int, trains: list[int], start_at: float, duration: float
) -> tuple[list[tuple[float, bool]], int]:
    """Run len(trains) client threads; return ([(latency_ms, is_first)...], errors)."""
    samples: list[tuple[float, bool]] = []
    errs = [0]
    lock = threading.Lock()

    def run_thread(train: int) -> None:
        hc = HTTPConnection("127.0.0.1", port, timeout=60)
        local: list[tuple[float, bool]] = []
        my_errs = 0
        try:
            _one_request(hc, train)  # warmup: TCP + server thread + DB backend
        except Exception:
            my_errs += 1
            hc.close()
            hc = HTTPConnection("127.0.0.1", port, timeout=60)
        # sleep to just before the shared instant, then spin — a pure spin
        # across many threads would thrash the GIL and skew the start
        delay = start_at - time.time() - 0.05
        if delay > 0:
            time.sleep(delay)
        while time.time() < start_at:
            pass
        first = True
        deadline = time.perf_counter() + duration
        while time.perf_counter() < deadline:
            try:
                lat, ok = _one_request(hc, train)
                if ok:
                    local.append((lat, first))
                else:
                    my_errs += 1
            except Exception:
                my_errs += 1
                hc.close()
                hc = HTTPConnection("127.0.0.1", port, timeout=60)
            first = False
        with lock:
            samples.extend(local)
            errs[0] += my_errs

    threads = [threading.Thread(target=run_thread, args=(t,)) for t in trains]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    return samples, errs[0]


# ------------------------------------------------------------------- measuring
def _pct(xs: list[float], p: float) -> float:
    if not xs:
        return float("nan")
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(len(xs) * p))]


def _reset_seats(dsn: str) -> None:
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute("UPDATE seats SET remaining = %s", (SEATS,))


def run_level(
    pool: cf.ProcessPoolExecutor,
    port: int,
    concurrency: int,
    duration: float,
    sharded: bool,
) -> dict:
    procs = min(12, concurrency)
    counts = [concurrency // procs + (1 if i < concurrency % procs else 0) for i in range(procs)]
    train_lists, g = [], 0
    for c in counts:
        train_lists.append([(g + j) % TRAINS + 1 if sharded else 1 for j in range(c)])
        g += c
    start_at = time.time() + 0.8 + 0.012 * concurrency

    all_samples: list[tuple[float, bool]] = []
    errors = 0
    futs = [pool.submit(_proc_worker, port, tl, start_at, duration) for tl in train_lists]
    for fut in futs:
        s, e = fut.result(timeout=duration + 60 + 0.05 * concurrency)
        all_samples.extend(s)
        errors += e

    convoy = [lat for lat, is_first in all_samples if is_first]
    steady = [lat for lat, is_first in all_samples if not is_first]
    return {
        "steady_thr": len(steady) / duration,
        "steady_n": len(steady),
        "steady_p50": _pct(steady, 0.50),
        "steady_p95": _pct(steady, 0.95),
        "steady_p99": _pct(steady, 0.99),
        "convoy_p50": _pct(convoy, 0.50),
        "convoy_p95": _pct(convoy, 0.95),
        "convoy_p99": _pct(convoy, 0.99),
        "convoy_max": max(convoy) if convoy else float("nan"),
        "errors": errors,
    }


# ---------------------------------------------------------------- orchestration
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dsn", default=DEFAULT_DSN)
    ap.add_argument("--port", type=int, default=8077)
    ap.add_argument("--out", required=True, help="CSV output path")
    ap.add_argument("--quick", action="store_true", help="smoke test: 3 levels, 2 reps")
    args = ap.parse_args()

    levels = [1, 8, 64] if args.quick else [1, 2, 4, 8, 16, 32, 64, 128, 256]
    reps = 2 if args.quick else 20
    duration = 1.0 if args.quick else 2.0

    with psycopg.connect(args.dsn, autocommit=True) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS seats (id int PRIMARY KEY, remaining bigint)")
        for i in range(1, TRAINS + 1):
            conn.execute(
                "INSERT INTO seats VALUES (%s, %s) ON CONFLICT (id) DO NOTHING", (i, SEATS)
            )

    server = subprocess.Popen(
        [sys.executable, "tools/r2_server.py", "--dsn", args.dsn, "--port", str(args.port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(150):  # wait for /health
            try:
                hc = HTTPConnection("127.0.0.1", args.port, timeout=2)
                hc.request("GET", "/health")
                if hc.getresponse().status == 200:
                    break
            except Exception:
                time.sleep(0.1)
        else:
            print("server never became healthy", file=sys.stderr)
            return 1

        rows: list[str] = []
        curve: dict[int, list[float]] = {}
        p99_by_level: dict[int, list[float]] = {}
        plan: list[tuple[int, bool, int]] = [(c, False, reps) for c in levels]
        if not args.quick:
            plan.append((64, True, 3))  # sharded control: same C, 8 rows not 1

        for concurrency, sharded, n_reps in plan:
            mode = "sharded8" if sharded else "hot"
            with cf.ProcessPoolExecutor(max_workers=min(12, concurrency)) as pool:
                for rep in range(n_reps):
                    _reset_seats(args.dsn)
                    r = run_level(pool, args.port, concurrency, duration, sharded)
                    rows.append(
                        f"{concurrency},{rep},{mode},{r['steady_thr']:.1f},{r['steady_n']},"
                        f"{r['steady_p50']:.3f},{r['steady_p95']:.3f},{r['steady_p99']:.3f},"
                        f"{r['convoy_p50']:.3f},{r['convoy_p95']:.3f},{r['convoy_p99']:.3f},"
                        f"{r['convoy_max']:.3f},{r['errors']}"
                    )
                    if not sharded:
                        curve.setdefault(concurrency, []).append(r["steady_thr"])
                        p99_by_level.setdefault(concurrency, []).append(r["steady_p99"])
                    print(
                        f"C={concurrency:<4} rep={rep:<2} {mode:<8} "
                        f"thr={r['steady_thr']:8.1f}  p99={r['steady_p99']:8.3f}  "
                        f"convoy_p99={r['convoy_p99']:9.3f}  err={r['errors']}",
                        file=sys.stderr,
                        flush=True,
                    )
    finally:
        server.terminate()
        server.wait(timeout=10)

    header = [
        "# R2 calibration run — HTTP + Postgres SELECT FOR UPDATE, two regimes",
        f"# date: {dt.date.today().isoformat()}",
        f"# host: {platform.platform()}, {platform.machine()}, Python {platform.python_version()}",
        f"# harness: tools/calibrate_r2.py ({'--quick' if args.quick else 'full'}: "
        f"{reps} reps, {duration}s per level), server: tools/r2_server.py",
        "# engine: PostgreSQL 17.10 (Homebrew, throwaway local instance, "
        "max_connections=450), psycopg 3",
        "# STEADY regime excludes each worker's first post-T0 request;",
        "# CONVOY regime is exactly those first requests (synchronized start).",
        "# sharded8 mode: same offered concurrency spread over 8 rows, not 1.",
        "concurrency,rep,mode,steady_thr_ops_s,steady_n,steady_p50_ms,steady_p95_ms,"
        "steady_p99_ms,convoy_p50_ms,convoy_p95_ms,convoy_p99_ms,convoy_max_ms,errors",
    ]
    with open(args.out, "w") as f:
        f.write("\n".join(header + rows) + "\n")

    med = {c: statistics.median(v) for c, v in curve.items()}
    knee = max(med, key=lambda k: med[k])
    peak, tail = med[knee], med[max(med)]
    p99s = p99_by_level[knee]
    print("\n--- DERIVED CONSTANTS (steady state) ---", file=sys.stderr)
    print(f"N_knee   = {knee}", file=sys.stderr)
    print(f"C_peak   = {peak:.1f} ops/s (median of {len(curve[knee])} reps)", file=sys.stderr)
    print(
        f"p99_knee = {statistics.median(p99s):.3f} ms " f"(range {min(p99s):.3f}–{max(p99s):.3f})",
        file=sys.stderr,
    )
    print(f"retention at C={max(med)}: {tail / peak:.1%} of peak", file=sys.stderr)
    print(
        "curve shape: " + ("COLLAPSE" if tail / peak < 0.75 else "PLATEAU") + " (threshold 0.75)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
