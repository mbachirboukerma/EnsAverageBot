import sqlite3
import threading
import logging
from contextlib import contextmanager
from typing import List, Optional, Tuple
import time

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Improved database manager with connection pooling and better error handling"""
    
    def __init__(self, db_path: str, max_connections: int = 5):
        self.db_path = db_path
        self.max_connections = max_connections
        self._connections = []
        self._lock = threading.RLock()
        self._visitor_count_cache = None
        self._usage_count_cache = None
        self._cache_timestamp = 0
        self._cache_ttl = 300  # 5 minutes cache TTL
        
        self._init_connections()
        self._init_tables()
    
    def _init_connections(self):
        """Initialize connection pool"""
        for _ in range(self.max_connections):
            conn = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                timeout=30.0
            )
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=MEMORY")
            self._connections.append(conn)
    
    @contextmanager
    def get_connection(self):
        """Get a database connection from the pool"""
        conn = None
        try:
            with self._lock:
                if self._connections:
                    conn = self._connections.pop()
                else:
                    # Create new connection if pool is empty
                    conn = sqlite3.connect(
                        self.db_path, 
                        check_same_thread=False,
                        timeout=30.0
                    )
            
            yield conn
        except Exception as e:
            logger.error(f"Database error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                try:
                    conn.commit()
                    with self._lock:
                        if len(self._connections) < self.max_connections:
                            self._connections.append(conn)
                        else:
                            conn.close()
                except Exception as e:
                    logger.error(f"Error returning connection to pool: {e}")
                    conn.close()
    
    def _init_tables(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create tables with proper indexes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS visitors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_visitors_user_id 
                ON visitors(user_id)
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS overall_average_count (
                    id INTEGER PRIMARY KEY,
                    count INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                INSERT OR IGNORE INTO overall_average_count (id, count) 
                VALUES (1, 0)
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS visitor_count_table (
                    id INTEGER PRIMARY KEY,
                    count INTEGER NOT NULL DEFAULT 2000,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                INSERT OR IGNORE INTO visitor_count_table (id, count) 
                VALUES (1, 2000)
            ''')
            
            conn.commit()
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        return (self._cache_timestamp + self._cache_ttl) > time.time()
    
    def _invalidate_cache(self):
        """Invalidate cache"""
        self._visitor_count_cache = None
        self._usage_count_cache = None
        self._cache_timestamp = 0
    
    def update_visitor(self, user_id: int) -> bool:
        """Update visitor information"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO visitors (user_id, last_activity) 
                    VALUES (?, CURRENT_TIMESTAMP)
                ''', (user_id,))
                
                self._invalidate_cache()
                logger.info(f"Updated visitor: {user_id}")
                return True
        except Exception as e:
            logger.error(f"Error updating visitor {user_id}: {e}")
            return False
    
    def get_visitor_count(self) -> int:
        """Get visitor count with caching"""
        if self._visitor_count_cache is not None and self._is_cache_valid():
            return self._visitor_count_cache
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM visitors")
                count = cursor.fetchone()[0]
                
                self._visitor_count_cache = count
                self._cache_timestamp = time.time()
                return count
        except Exception as e:
            logger.error(f"Error getting visitor count: {e}")
            return 0
    
    def get_all_user_ids(self) -> List[int]:
        """Get all user IDs"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id FROM visitors ORDER BY last_activity DESC")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting user IDs: {e}")
            return []
    
    def get_overall_average_count(self) -> int:
        """Get overall average count with caching"""
        if self._usage_count_cache is not None and self._is_cache_valid():
            return self._usage_count_cache
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT count FROM overall_average_count WHERE id = 1")
                count = cursor.fetchone()[0]
                
                self._usage_count_cache = count
                self._cache_timestamp = time.time()
                return count
        except Exception as e:
            logger.error(f"Error getting average count: {e}")
            return 0
    
    def increment_overall_average_count(self) -> bool:
        """Increment overall average count"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE overall_average_count 
                    SET count = count + 1, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = 1
                ''')
                
                self._invalidate_cache()
                return True
        except Exception as e:
            logger.error(f"Error incrementing average count: {e}")
            return False
    
    def remove_user(self, user_id: int) -> bool:
        """Remove user from database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM visitors WHERE user_id = ?", (user_id,))
                
                self._invalidate_cache()
                logger.info(f"Removed user: {user_id}")
                return True
        except Exception as e:
            logger.error(f"Error removing user {user_id}: {e}")
            return False
    
    def cleanup_inactive_users(self, days_inactive: int = 30) -> int:
        """Clean up users inactive for specified days"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM visitors 
                    WHERE last_activity < datetime('now', '-{} days')
                '''.format(days_inactive))
                
                deleted_count = cursor.rowcount
                self._invalidate_cache()
                logger.info(f"Cleaned up {deleted_count} inactive users")
                return deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up inactive users: {e}")
            return 0
    
    def close(self):
        """Close all database connections"""
        with self._lock:
            for conn in self._connections:
                try:
                    conn.close()
                except Exception as e:
                    logger.error(f"Error closing connection: {e}")
            self._connections.clear() 
