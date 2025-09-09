from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from typing import Iterable, List, Optional
import threading
from loguru import logger

SCHEMA = """    PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS chats (
  peer_id INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS bans (
  user_id INTEGER PRIMARY KEY
);
"""

class DB:
    def __init__(self, path: str):
        self.path = path
        # allow connections from multiple threads
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.execute('PRAGMA foreign_keys=ON;')
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self._init_schema()

    def _init_schema(self):
        with self._lock:
            cur = self._conn.cursor()
            cur.executescript(SCHEMA)
            self._conn.commit()

    @contextmanager
    def connect(self):
        # Return the shared connection (thread-safe via lock)
        try:
            self._lock.acquire()
            yield self._conn
        finally:
            self._lock.release()

    def add_chat(self, peer_id: int) -> bool:
        with self.connect() as con:
            cur = con.execute('INSERT OR IGNORE INTO chats(peer_id) VALUES (?)', (peer_id,))
            con.commit()
            return cur.rowcount > 0

    def remove_chat(self, peer_id: int) -> bool:
        with self.connect() as con:
            cur = con.execute('DELETE FROM chats WHERE peer_id=?', (peer_id,))
            con.commit()
            return cur.rowcount > 0

    def list_chats(self) -> List[int]:
        with self.connect() as con:
            return [r['peer_id'] for r in con.execute('SELECT peer_id FROM chats').fetchall()]

    def add_ban(self, user_id: int) -> bool:
        with self.connect() as con:
            cur = con.execute('INSERT OR IGNORE INTO bans(user_id) VALUES (?)', (user_id,))
            con.commit()
            return cur.rowcount > 0

    def unban(self, user_id: int) -> bool:
        with self.connect() as con:
            cur = con.execute('DELETE FROM bans WHERE user_id=?', (user_id,))
            con.commit()
            return cur.rowcount > 0

    def is_banned(self, user_id: int) -> bool:
        with self.connect() as con:
            row = con.execute('SELECT 1 FROM bans WHERE user_id=?', (user_id,)).fetchone()
            return bool(row)

    def list_bans(self) -> List[int]:
        with self.connect() as con:
            return [r['user_id'] for r in con.execute('SELECT user_id FROM bans').fetchall()]
