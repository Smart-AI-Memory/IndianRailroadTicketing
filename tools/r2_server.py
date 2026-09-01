#!/usr/bin/env python3
"""R2 calibration endpoint — a real HTTP booking service over Postgres.

This is the "exactly one real component" that requirements.md R2 demands:
an HTTP endpoint doing a genuine `SELECT FOR UPDATE` seat decrement against
a real database. Its purpose is measurement, not demonstration — it exists
so the simulator's service-time distribution and contention curve are
measured rather than assumed.

Design notes, load-bearing:

- HTTP/1.1 keep-alive. Each client holds one persistent connection, served
  by one server thread holding one thread-local DB connection. Without
  keep-alive every request would pay TCP + backend setup, and the
  measurement would be of connection churn, not lock contention.
- The transaction is the textbook two-step: SELECT ... FOR UPDATE, then
  UPDATE, then COMMIT. Postgres queues FOR UPDATE waiters in arrival order,
  which is exactly the behaviour SQLite's busy-handler backoff ladder does
  NOT have — the difference the 2026-08-09 run's withdrawn tail result
  turned on.
- Sold-out is a clean rejection (HTTP 200, ok=false), not an error. R6
  requires clean rejections and hard errors never be summed; the server
  keeps them distinguishable at the wire level.

Usage:  python3 tools/r2_server.py --dsn postgresql://... [--port 8077]
        python3 tools/r2_server.py --dsn mysql://root@127.0.0.1:33061/r2   (v3 D11 anchor)
"""

from __future__ import annotations

import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import r2_db

_tls = threading.local()
DSN = ""


def _db():
    """One connection per server thread, created lazily on first use."""
    conn = getattr(_tls, "conn", None)
    if conn is None or conn.closed:
        conn = r2_db.connect(DSN, autocommit=False)
        _tls.conn = conn
    return conn


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"  # keep-alive: 1 client = 1 thread = 1 DB conn

    def log_message(self, *_args) -> None:
        pass  # default stderr log per request would itself be measurable overhead

    def _reply(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if urlparse(self.path).path != "/health":
            self._reply(404, {"ok": False, "reason": "not_found"})
            return
        try:
            conn = _db()
            conn.execute("SELECT 1")
            conn.rollback()
            self._reply(200, {"ok": True})
        except Exception as exc:  # noqa: BLE001 — health endpoint reports anything
            self._reply(500, {"ok": False, "reason": type(exc).__name__})

    def do_POST(self) -> None:
        url = urlparse(self.path)
        if url.path != "/book":
            self._reply(404, {"ok": False, "reason": "not_found"})
            return
        train = int(parse_qs(url.query).get("train", ["1"])[0])
        conn = _db()
        try:
            row = conn.execute(
                "SELECT remaining FROM seats WHERE id = %s FOR UPDATE", (train,)
            ).fetchone()
            if row is None:
                conn.rollback()
                self._reply(404, {"ok": False, "reason": "no_such_train"})
                return
            if row[0] <= 0:
                conn.rollback()  # clean rejection, not an error (R6)
                self._reply(200, {"ok": False, "reason": "sold_out"})
                return
            conn.execute("UPDATE seats SET remaining = remaining - 1 WHERE id = %s", (train,))
            conn.commit()
            self._reply(200, {"ok": True, "remaining": row[0] - 1})
        except Exception as exc:  # noqa: BLE001 — any failure is a hard error to the client
            try:
                conn.rollback()
            except Exception:
                pass
            self._reply(500, {"ok": False, "reason": type(exc).__name__})


def main() -> int:
    global DSN
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dsn", required=True, help="DSN (postgresql://... or mysql://...)")
    ap.add_argument("--port", type=int, default=8077)
    args = ap.parse_args()
    DSN = args.dsn

    class Server(ThreadingHTTPServer):
        daemon_threads = True
        # Default listen backlog is 5; C=256 clients connecting at once would
        # see connection refusals from the OS, not the service under test.
        request_queue_size = 512

    srv = Server(("127.0.0.1", args.port), Handler)
    print(f"r2-server listening on 127.0.0.1:{args.port}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
