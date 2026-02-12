"""SQLite-backed response cache with TTL support."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Any


class Cache:
    """SQLite cache with per-query TTL.

    Cache key = provider + query_type + query_value.
    """

    def __init__(self, db_path: str | Path = ".osint_cache/cache.db") -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path))
        self._init_db()

    def _init_db(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                expires_at REAL NOT NULL
            )
        """)
        self._conn.commit()

    @staticmethod
    def _make_key(provider: str, query_type: str, query_value: str) -> str:
        raw = f"{provider}:{query_type}:{query_value}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, provider: str, query_type: str, query_value: str) -> dict[str, Any] | None:
        """Retrieve a cached response, or None if expired/missing."""
        key = self._make_key(provider, query_type, query_value)
        row = self._conn.execute(
            "SELECT value, expires_at FROM cache WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            return None
        value, expires_at = row
        if time.time() > expires_at:
            self._conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            self._conn.commit()
            return None
        return json.loads(value)  # type: ignore[no-any-return]

    def set(
        self,
        provider: str,
        query_type: str,
        query_value: str,
        data: dict[str, Any],
        ttl: int = 3600,
    ) -> None:
        """Store a response in the cache."""
        key = self._make_key(provider, query_type, query_value)
        expires_at = time.time() + ttl
        self._conn.execute(
            "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
            (key, json.dumps(data), expires_at),
        )
        self._conn.commit()

    def clear(self) -> None:
        """Clear all cached entries."""
        self._conn.execute("DELETE FROM cache")
        self._conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()
