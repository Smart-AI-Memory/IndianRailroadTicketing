"""Engine adapter for the R2 calibration harness (v3 W4.1, D11).

The R2 harness was written against psycopg's convenience API
(`conn.execute(...)` returning a cursor). The v3 second-anchor run
(decisions.md D11) drives the identical HTTP endpoint and ladder
against MariaDB, so this module gives both engines that one shape.
It deliberately abstracts nothing else — same SQL, same transaction
boundaries, same placeholders — because the measurement's point is
that only the engine changes.

DSN schemes: postgresql://... → psycopg; mysql://... → PyMySQL.
"""

from __future__ import annotations

from urllib.parse import urlparse


def engine_of(dsn: str) -> str:
    scheme = urlparse(dsn).scheme
    if scheme.startswith("postgres"):
        return "postgres"
    if scheme in ("mysql", "mariadb"):
        return "mariadb"
    raise ValueError(f"unrecognized DSN scheme: {scheme!r}")


class _MySQLConn:
    """PyMySQL connection wrapped to psycopg's execute-on-connection shape."""

    def __init__(self, dsn: str, autocommit: bool):
        import pymysql

        u = urlparse(dsn)
        self._conn = pymysql.connect(
            host=u.hostname or "127.0.0.1",
            port=u.port or 3306,
            user=u.username or "root",
            password=u.password or "",
            database=u.path.lstrip("/"),
            autocommit=autocommit,
        )
        self.closed = False

    def execute(self, sql: str, params: tuple = ()):
        cur = self._conn.cursor()
        cur.execute(sql, params or None)
        return cur  # PyMySQL cursors provide fetchone(), like psycopg's

    def commit(self) -> None:
        self._conn.commit()

    def rollback(self) -> None:
        self._conn.rollback()

    def close(self) -> None:
        self._conn.close()
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        self.close()


def connect(dsn: str, autocommit: bool):
    if engine_of(dsn) == "postgres":
        import psycopg

        return psycopg.connect(dsn, autocommit=autocommit)
    return _MySQLConn(dsn, autocommit=autocommit)


def insert_seat_sql(dsn: str) -> str:
    """Idempotent seat-row insert, per engine (the one dialect difference)."""
    if engine_of(dsn) == "postgres":
        return "INSERT INTO seats VALUES (%s, %s) ON CONFLICT (id) DO NOTHING"
    return "INSERT IGNORE INTO seats VALUES (%s, %s)"


def engine_description(dsn: str, server_version: str = "") -> str:
    name = "PostgreSQL" if engine_of(dsn) == "postgres" else "MariaDB"
    return f"{name} {server_version}".strip()


def server_version(dsn: str) -> str:
    with connect(dsn, autocommit=True) as conn:
        row = conn.execute("SELECT version()").fetchone()
    return str(row[0]) if row else "unknown"
