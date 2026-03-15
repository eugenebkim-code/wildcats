"""SQLite database layer — all queries in one place."""

import json
import sqlite3
from contextlib import contextmanager
from typing import Any

from config import DATABASE_PATH


# ── connection helper ────────────────────────────────────────────────────────

@contextmanager
def _conn():
    con = sqlite3.connect(DATABASE_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


# ── schema ───────────────────────────────────────────────────────────────────

def init_db() -> None:
    with _conn() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id  INTEGER PRIMARY KEY,
                username     TEXT,
                language     TEXT    NOT NULL DEFAULT 'ru',
                created_at   TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS observations (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id      INTEGER NOT NULL,
                species          TEXT    NOT NULL,
                observation_type TEXT    NOT NULL,
                date             TEXT    NOT NULL,
                latitude         REAL,
                longitude        REAL,
                location_name    TEXT,
                observer_name    TEXT,
                notes            TEXT,
                photos           TEXT    NOT NULL DEFAULT '[]',
                status           TEXT    NOT NULL DEFAULT 'pending',
                language         TEXT    NOT NULL DEFAULT 'ru',
                created_at       TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
            );
        """)


# ── users ────────────────────────────────────────────────────────────────────

def upsert_user(telegram_id: int, username: str | None, language: str) -> None:
    with _conn() as con:
        con.execute(
            """
            INSERT INTO users (telegram_id, username, language)
            VALUES (?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE
                SET username = excluded.username,
                    language = excluded.language
            """,
            (telegram_id, username, language),
        )


def get_user_language(telegram_id: int) -> str | None:
    with _conn() as con:
        row = con.execute(
            "SELECT language FROM users WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()
    return row["language"] if row else None


# ── observations ─────────────────────────────────────────────────────────────

def save_observation(data: dict[str, Any]) -> int:
    with _conn() as con:
        cur = con.execute(
            """
            INSERT INTO observations
                (telegram_id, species, observation_type, date,
                 latitude, longitude, location_name, observer_name,
                 notes, photos, language)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                data["telegram_id"],
                data["species"],
                data["observation_type"],
                data["date"],
                data.get("latitude"),
                data.get("longitude"),
                data.get("location_name"),
                data.get("observer_name"),
                data.get("notes"),
                json.dumps(data.get("photos", [])),
                data.get("language", "ru"),
            ),
        )
    return cur.lastrowid  # type: ignore[return-value]


def get_observation(obs_id: int) -> dict | None:
    with _conn() as con:
        row = con.execute(
            "SELECT * FROM observations WHERE id = ?", (obs_id,)
        ).fetchone()
    return dict(row) if row else None


def get_observations(
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
    with _conn() as con:
        if status:
            rows = con.execute(
                "SELECT * FROM observations WHERE status=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (status, limit, offset),
            ).fetchall()
        else:
            rows = con.execute(
                "SELECT * FROM observations ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
    return [dict(r) for r in rows]


def count_observations(status: str | None = None) -> int:
    with _conn() as con:
        if status:
            row = con.execute(
                "SELECT COUNT(*) AS n FROM observations WHERE status=?", (status,)
            ).fetchone()
        else:
            row = con.execute("SELECT COUNT(*) AS n FROM observations").fetchone()
    return row["n"]


def update_status(obs_id: int, status: str) -> None:
    with _conn() as con:
        con.execute(
            "UPDATE observations SET status=? WHERE id=?", (status, obs_id)
        )


def get_stats() -> dict[str, int]:
    with _conn() as con:
        total    = con.execute("SELECT COUNT(*) AS n FROM observations").fetchone()["n"]
        verified = con.execute("SELECT COUNT(*) AS n FROM observations WHERE status='verified'").fetchone()["n"]
        doubtful = con.execute("SELECT COUNT(*) AS n FROM observations WHERE status='doubtful'").fetchone()["n"]
        pending  = con.execute("SELECT COUNT(*) AS n FROM observations WHERE status='pending'").fetchone()["n"]
        users    = con.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
    return {
        "total": total,
        "verified": verified,
        "doubtful": doubtful,
        "pending": pending,
        "users": users,
    }
