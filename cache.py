import json
import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).parent / "cache.db"
TTL_SECONDS = 6 * 60 * 60  # how long a cached result stays (6 hours)


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            fetched_at REAL NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def get_cached(key: str):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT data, fetched_at FROM cache WHERE key = ?", (key,)
    ).fetchone()
    conn.close()

    if not row:
        return None

    data, fetched_at = row
    if time.time() - fetched_at > TTL_SECONDS:
        return None  # stale, treat as a miss so caller re-scrapes

    return json.loads(data)


def set_cache(key: str, data: list) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO cache (key, data, fetched_at) VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
            data = excluded.data,
            fetched_at = excluded.fetched_at
        """,
        (key, json.dumps(data), time.time()),
    )
    conn.commit()
    conn.close()
