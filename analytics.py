import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).parent / "analytics.db"


def init_analytics_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS query_log (query TEXT NOT NULL, ts REAL NOT NULL)"
    )
    conn.commit()
    conn.close()


def log_query(query: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO query_log (query, ts) VALUES (?, ?)", (query, time.time()))
    conn.commit()
    conn.close()


def get_trending(limit: int = 10, window_hours: int = 48) -> list:
    conn = sqlite3.connect(DB_PATH)
    cutoff = time.time() - window_hours * 3600
    rows = conn.execute(
        """
        SELECT query, COUNT(*) as searches
        FROM query_log
        WHERE ts > ?
        GROUP BY query
        ORDER BY searches DESC
        LIMIT ?
        """,
        (cutoff, limit),
    ).fetchall()
    conn.close()
    return [{"query": q, "searches": c} for q, c in rows]
