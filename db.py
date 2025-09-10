import sqlite3
import threading
from typing import List, Optional, Tuple

class DB:
    def __init__(self, path: str):
        self.path = path
        self.lock = threading.RLock()
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self._migrate()

    def _migrate(self):
        with self.lock:
            c = self.conn.cursor()
            # Chats table: stores chat ids participating in the grid
            c.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                chat_id INTEGER PRIMARY KEY
            );
            """)
            # Bans table: banned user ids
            c.execute("""
            CREATE TABLE IF NOT EXISTS bans (
                user_id INTEGER PRIMARY KEY
            );
            """)
            # Chat settings: silence mode per chat
            c.execute("""
            CREATE TABLE IF NOT EXISTS chat_settings (
                chat_id INTEGER PRIMARY KEY,
                silence INTEGER NOT NULL DEFAULT 0
            );
            """)
            self.conn.commit()

    # Chats operations
    def add_chat(self, chat_id: int):
        with self.lock:
            self.conn.execute("INSERT OR IGNORE INTO chats(chat_id) VALUES (?)", (chat_id,))
            self.conn.commit()

    def remove_chat(self, chat_id: int):
        with self.lock:
            self.conn.execute("DELETE FROM chats WHERE chat_id = ?", (chat_id,))
            self.conn.execute("DELETE FROM chat_settings WHERE chat_id = ?", (chat_id,))
            self.conn.commit()

    def list_chats(self) -> List[int]:
        with self.lock:
            cur = self.conn.execute("SELECT chat_id FROM chats")
            return [row[0] for row in cur.fetchall()]

    # Bans operations
    def add_ban(self, user_id: int):
        with self.lock:
            self.conn.execute("INSERT OR IGNORE INTO bans(user_id) VALUES (?)", (user_id,))
            self.conn.commit()

    def remove_ban(self, user_id: int):
        with self.lock:
            self.conn.execute("DELETE FROM bans WHERE user_id = ?", (user_id,))
            self.conn.commit()

    def is_banned(self, user_id: int) -> bool:
        with self.lock:
            cur = self.conn.execute("SELECT 1 FROM bans WHERE user_id = ? LIMIT 1", (user_id,))
            return cur.fetchone() is not None

    def list_bans(self) -> List[int]:
        with self.lock:
            cur = self.conn.execute("SELECT user_id FROM bans")
            return [row[0] for row in cur.fetchall()]

    # Chat settings (silence)
    def set_silence(self, chat_id: int, enabled: bool):
        with self.lock:
            self.conn.execute("""
                INSERT INTO chat_settings(chat_id, silence)
                VALUES (?, ?)
                ON CONFLICT(chat_id) DO UPDATE SET silence=excluded.silence
            """, (chat_id, 1 if enabled else 0))
            self.conn.commit()

    def get_silence(self, chat_id: int) -> bool:
        with self.lock:
            cur = self.conn.execute("SELECT silence FROM chat_settings WHERE chat_id = ?", (chat_id,))
            row = cur.fetchone()
            return bool(row[0]) if row else False
