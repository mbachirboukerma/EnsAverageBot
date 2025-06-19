import sqlite3
import threading
import logging
from contextlib import contextmanager
from typing import List, Optional, Tuple
import time

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager for visitor IDs and usage count."""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.lock = threading.RLock()
        self._init_db()

    def _init_db(self):
        with self.lock, sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # جدول الزوار (user_id فقط)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS visitor_ids (
                    user_id INTEGER PRIMARY KEY
                )
            ''')
            # جدول عداد الاستخدامات (صف واحد فقط)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usage_count (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    count INTEGER NOT NULL
                )
            ''')
            # تأكد من وجود صف usage_count
            cursor.execute('INSERT OR IGNORE INTO usage_count (id, count) VALUES (1, 0)')
            conn.commit()

    def add_visitor(self, user_id: int):
        """Add a user_id if not exists."""
        with self.lock, sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR IGNORE INTO visitor_ids (user_id) VALUES (?)', (user_id,))
            conn.commit()

    def remove_visitor(self, user_id: int):
        """Remove a user_id from the database."""
        with self.lock, sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM visitor_ids WHERE user_id = ?', (user_id,))
            conn.commit()

    def get_all_user_ids(self) -> List[int]:
        """Return all user_ids."""
        with self.lock, sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM visitor_ids')
            rows = cursor.fetchall()
            return [row[0] for row in rows]

    def get_visitor_count(self) -> int:
        """Return the number of unique visitors."""
        with self.lock, sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM visitor_ids')
            return cursor.fetchone()[0]

    def increment_usage_count(self):
        """Increment the usage count by 1."""
        with self.lock, sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE usage_count SET count = count + 1 WHERE id = 1')
            conn.commit()

    def get_usage_count(self) -> int:
        """Return the usage count."""
        with self.lock, sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT count FROM usage_count WHERE id = 1')
            row = cursor.fetchone()
            return row[0] if row else 0

    def close(self):
        pass  # No persistent connection to close in this design 
