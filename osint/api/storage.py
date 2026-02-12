"""SQLite-backed investigation storage."""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

logger = logging.getLogger(__name__)

_DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_DB_PATH = _DB_DIR / "investigations.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS investigations (
    id TEXT PRIMARY KEY,
    name TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    subject_name TEXT,
    aliases TEXT,
    date_of_birth TEXT,
    age_range TEXT,
    location TEXT,
    address TEXT,
    nationality TEXT,
    gender TEXT,
    email TEXT,
    phone TEXT,
    ip TEXT,
    domain TEXT,
    company TEXT,
    employer TEXT,
    occupation TEXT,
    education TEXT,
    social_media TEXT,
    vehicle TEXT,
    physical_description TEXT,
    notes TEXT,
    photo_ids TEXT,
    results TEXT
);

CREATE TABLE IF NOT EXISTS investigation_timeline (
    id TEXT PRIMARY KEY,
    investigation_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    description TEXT,
    data TEXT,
    FOREIGN KEY (investigation_id) REFERENCES investigations(id)
);
"""

# All subject-info columns in the investigations table
_SUBJECT_FIELDS = [
    "subject_name", "aliases", "date_of_birth", "age_range", "location",
    "address", "nationality", "gender", "email", "phone", "ip", "domain",
    "company", "employer", "occupation", "education", "social_media",
    "vehicle", "physical_description", "notes", "photo_ids",
]

# Fields stored as JSON
_JSON_FIELDS = {"aliases", "social_media", "photo_ids"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class InvestigationStore:
    """Thin wrapper around a SQLite database for investigation persistence."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self._db_path = Path(db_path) if db_path else _DB_PATH
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    # ── helpers ──────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _ensure_schema(self) -> None:
        conn = self._connect()
        try:
            conn.executescript(_SCHEMA)
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        d = dict(row)
        # Deserialise JSON columns
        for field in _JSON_FIELDS:
            raw = d.get(field)
            if raw is not None:
                try:
                    d[field] = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    pass
            else:
                if field == "aliases" or field == "photo_ids":
                    d[field] = []
                elif field == "social_media":
                    d[field] = {}
        # Deserialise results
        if d.get("results"):
            try:
                d["results"] = json.loads(d["results"])
            except (json.JSONDecodeError, TypeError):
                pass
        return d

    @staticmethod
    def _timeline_row_to_dict(row: sqlite3.Row) -> dict:
        d = dict(row)
        if d.get("data"):
            try:
                d["data"] = json.loads(d["data"])
            except (json.JSONDecodeError, TypeError):
                pass
        return d

    def _encode_field(self, key: str, value) -> str | None:
        """Encode a value for storage."""
        if value is None:
            return None
        if key in _JSON_FIELDS:
            return json.dumps(value)
        return str(value)

    # ── public API ───────────────────────────────────────────

    def create(self, request_data: dict, results: dict | None = None) -> str:
        """Create a new investigation record. Returns the new UUID."""
        inv_id = str(uuid4())
        now = _now_iso()

        # Map request fields → DB columns
        values: dict[str, str | None] = {
            "id": inv_id,
            "name": request_data.get("investigation_name"),
            "created_at": now,
            "updated_at": now,
            "status": "active",
            "subject_name": request_data.get("name"),
        }
        for field in _SUBJECT_FIELDS:
            if field == "subject_name":
                continue  # already handled
            val = request_data.get(field)
            values[field] = self._encode_field(field, val)

        if results is not None:
            values["results"] = json.dumps(results, default=str)

        cols = ", ".join(values.keys())
        placeholders = ", ".join(["?"] * len(values))
        conn = self._connect()
        try:
            conn.execute(
                f"INSERT INTO investigations ({cols}) VALUES ({placeholders})",
                list(values.values()),
            )
            conn.commit()
        finally:
            conn.close()

        return inv_id

    def get(self, inv_id: str) -> dict | None:
        """Load an investigation by ID, including timeline."""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM investigations WHERE id = ?", (inv_id,)
            ).fetchone()
            if row is None:
                return None
            d = self._row_to_dict(row)
            d["timeline"] = self.get_timeline(inv_id)
            return d
        finally:
            conn.close()

    def list(self, status: str | None = None, limit: int = 50) -> list[dict]:
        """List investigations, optionally filtered by status."""
        conn = self._connect()
        try:
            if status:
                rows = conn.execute(
                    "SELECT * FROM investigations WHERE status = ? ORDER BY updated_at DESC LIMIT ?",
                    (status, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM investigations ORDER BY updated_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [self._row_to_dict(r) for r in rows]
        finally:
            conn.close()

    def update(self, inv_id: str, fields: dict) -> None:
        """Partial update of subject fields."""
        if not fields:
            return
        allowed = set(_SUBJECT_FIELDS) | {"name"}
        sets: list[str] = []
        vals: list = []
        for key, value in fields.items():
            if key not in allowed:
                continue
            sets.append(f"{key} = ?")
            vals.append(self._encode_field(key, value))
        if not sets:
            return
        sets.append("updated_at = ?")
        vals.append(_now_iso())
        vals.append(inv_id)
        conn = self._connect()
        try:
            conn.execute(
                f"UPDATE investigations SET {', '.join(sets)} WHERE id = ?",
                vals,
            )
            conn.commit()
        finally:
            conn.close()

    def save_results(self, inv_id: str, results: dict) -> None:
        """Save/overwrite investigation results."""
        now = _now_iso()
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE investigations SET results = ?, updated_at = ? WHERE id = ?",
                (json.dumps(results, default=str), now, inv_id),
            )
            conn.commit()
        finally:
            conn.close()

    def add_timeline_event(
        self,
        inv_id: str,
        event_type: str,
        description: str | None = None,
        data: dict | None = None,
    ) -> str:
        """Add a timeline event. Returns the event UUID."""
        event_id = str(uuid4())
        now = _now_iso()
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO investigation_timeline (id, investigation_id, timestamp, event_type, description, data) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    event_id,
                    inv_id,
                    now,
                    event_type,
                    description,
                    json.dumps(data) if data else None,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return event_id

    def get_timeline(self, inv_id: str) -> list[dict]:
        """Get all timeline events for an investigation."""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM investigation_timeline WHERE investigation_id = ? ORDER BY timestamp ASC",
                (inv_id,),
            ).fetchall()
            return [self._timeline_row_to_dict(r) for r in rows]
        finally:
            conn.close()

    def delete(self, inv_id: str) -> None:
        """Soft-delete (archive) an investigation."""
        now = _now_iso()
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE investigations SET status = 'archived', updated_at = ? WHERE id = ?",
                (now, inv_id),
            )
            conn.commit()
        finally:
            conn.close()

    def search(self, query: str, limit: int = 50) -> list[dict]:
        """Search investigations by name, subject_name, email, or phone."""
        like = f"%{query}%"
        conn = self._connect()
        try:
            rows = conn.execute(
                """SELECT * FROM investigations
                   WHERE (name LIKE ? OR subject_name LIKE ? OR email LIKE ? OR phone LIKE ?)
                   ORDER BY updated_at DESC LIMIT ?""",
                (like, like, like, like, limit),
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]
        finally:
            conn.close()


# Module-level singleton
store = InvestigationStore()
