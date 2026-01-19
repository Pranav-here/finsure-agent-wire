import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Item, url_hash


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_items (
                url_hash TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                title TEXT,
                first_seen TEXT NOT NULL,
                posted INTEGER DEFAULT 0
            )
            """
        )
        self.conn.commit()

    def has_seen(self, url: str) -> bool:
        hashed = url_hash(url)
        cur = self.conn.execute("SELECT 1 FROM seen_items WHERE url_hash = ?", (hashed,))
        return cur.fetchone() is not None

    def mark_seen(self, item: Item) -> None:
        hashed = url_hash(item.url)
        self.conn.execute(
            """
            INSERT OR IGNORE INTO seen_items (url_hash, url, title, first_seen, posted)
            VALUES (?, ?, ?, ?, 0)
            """,
            (hashed, item.canonical_url(), item.title, datetime.utcnow().isoformat()),
        )
        self.conn.commit()

    def mark_posted(self, url: str) -> None:
        hashed = url_hash(url)
        self.conn.execute("UPDATE seen_items SET posted = 1 WHERE url_hash = ?", (hashed,))
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()


@contextmanager
def db_session(path: Path):
    db = Database(path)
    try:
        yield db
    finally:
        db.close()


__all__ = ["Database", "db_session"]
