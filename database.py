import sqlite3
from contextlib import closing
import threading
import logging
from typing import List, Optional, Dict
import time
from functools import lru_cache

class Database:
    def __init__(self, db_path: str):
        # Configure logging first
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('Database')
        
        # Then initialize other attributes
        self.db_path = db_path
        self.lock = threading.Lock()
        self._initialized = False
        self._init_db()
        self._create_indexes()

    def _check_table_structure(self, cursor, table_name):
        """Check if table has the required columns"""
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = {row[1] for row in cursor.fetchall()}
        return columns

    def _migrate_table(self, cursor, table_name, required_columns):
        """Migrate table to new structure if needed"""
        current_columns = self._check_table_structure(cursor, table_name)
        
        # If table doesn't exist or is missing columns, recreate it
        if not current_columns or not all(col in current_columns for col in required_columns):
            self.logger.info(f"Migrating table {table_name} to new structure")
            
            # Backup old data if table exists
            if current_columns:
                temp_table = f"temp_{table_name}"
                cursor.execute(f"ALTER TABLE {table_name} RENAME TO {temp_table}")
            
            # Create new table structure
            if table_name == 'visitors':
                cursor.execute('''
                    CREATE TABLE visitors (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER UNIQUE NOT NULL,
                        visit_count INTEGER DEFAULT 1,
                        last_visit TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            elif table_name == 'overall_average':
                cursor.execute('''
                    CREATE TABLE overall_average (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        count INTEGER DEFAULT 0,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            elif table_name == 'user_stats':
                cursor.execute('''
                    CREATE TABLE user_stats (
                        user_id INTEGER PRIMARY KEY,
                        total_calculations INTEGER DEFAULT 0,
                        last_calculation TIMESTAMP,
                        average_grade REAL,
                        FOREIGN KEY (user_id) REFERENCES visitors(user_id)
                    )
                ''')
            
            # Migrate data if old table existed
            if current_columns:
                common_columns = current_columns.intersection(required_columns)
                if common_columns:
                    columns_str = ', '.join(common_columns)
                    cursor.execute(f"INSERT INTO {table_name} ({columns_str}) SELECT {columns_str} FROM {temp_table}")
                cursor.execute(f"DROP TABLE {temp_table}")

    def _init_db(self):
        """Initialize database with proper schema and indexes"""
        if self._initialized:
            return
            
        with self.lock:
            with closing(sqlite3.connect(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # Define required columns for each table
                visitors_columns = {'id', 'user_id', 'visit_count', 'last_visit', 'created_at'}
                overall_average_columns = {'id', 'count', 'last_updated'}
                user_stats_columns = {'user_id', 'total_calculations', 'last_calculation', 'average_grade'}
                
                # Migrate tables if needed
                self._migrate_table(cursor, 'visitors', visitors_columns)
                self._migrate_table(cursor, 'overall_average', overall_average_columns)
                self._migrate_table(cursor, 'user_stats', user_stats_columns)
                
                conn.commit()
                self._initialized = True
                self.logger.info("Database initialized successfully")

    def _create_indexes(self):
        """Create necessary indexes for better query performance"""
        if not self._initialized:
            return
            
        with self.lock:
            with closing(sqlite3.connect(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # Create indexes for visitors table
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_visitors_user_id ON visitors(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_visitors_last_visit ON visitors(last_visit)')
                
                # Create indexes for user_stats table
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_stats_last_calculation ON user_stats(last_calculation)')
                
                conn.commit()
                self.logger.info("Indexes created successfully")

    @lru_cache(maxsize=1000)
    def get_visitor_count(self) -> int:
        """Get total visitor count with caching"""
        try:
            with self.lock:
                with closing(sqlite3.connect(self.db_path)) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(DISTINCT user_id) FROM visitors')
                    return cursor.fetchone()[0]
        except sqlite3.Error as e:
            self.logger.error(f"Error getting visitor count: {str(e)}")
            return 0

    def update_visitors(self, user_id: int):
        """Update visitor count with proper error handling and logging"""
        try:
            with self.lock:
                with closing(sqlite3.connect(self.db_path)) as conn:
                    cursor = conn.cursor()
                    
                    # Check if user exists
                    cursor.execute('SELECT id FROM visitors WHERE user_id = ?', (user_id,))
                    exists = cursor.fetchone()
                    
                    if exists:
                        # Update existing user
                        cursor.execute('''
                            UPDATE visitors 
                            SET visit_count = visit_count + 1,
                                last_visit = CURRENT_TIMESTAMP
                            WHERE user_id = ?
                        ''', (user_id,))
                    else:
                        # Insert new user
                        cursor.execute('''
                            INSERT INTO visitors (user_id, visit_count, last_visit)
                            VALUES (?, 1, CURRENT_TIMESTAMP)
                        ''', (user_id,))
                    
                    conn.commit()
                    self.logger.info(f"Updated visitor count for user {user_id}")
        except sqlite3.Error as e:
            self.logger.error(f"Error updating visitor count: {str(e)}")
            raise

    @lru_cache(maxsize=100)
    def get_overall_average_count(self) -> int:
        """Get overall average count with caching"""
        with self.lock:
            with closing(sqlite3.connect(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT count FROM overall_average ORDER BY id DESC LIMIT 1')
                result = cursor.fetchone()
                return result[0] if result else 0

    def increment_overall_average_count(self):
        """Increment overall average count with proper error handling"""
        try:
            with self.lock:
                with closing(sqlite3.connect(self.db_path)) as conn:
                    cursor = conn.cursor()
                    
                    # Use UPSERT for better performance
                    cursor.execute('''
                        INSERT INTO overall_average (count, last_updated)
                        VALUES (1, CURRENT_TIMESTAMP)
                        ON CONFLICT(id) DO UPDATE SET
                            count = count + 1,
                            last_updated = CURRENT_TIMESTAMP
                    ''')
                    
                    conn.commit()
                    self.logger.info("Incremented overall average count")
        except sqlite3.Error as e:
            self.logger.error(f"Error incrementing overall average count: {str(e)}")
            raise

    def get_all_user_ids(self) -> List[int]:
        """Get all user IDs with proper error handling"""
        try:
            with self.lock:
                with closing(sqlite3.connect(self.db_path)) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT user_id FROM visitors')
                    return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            self.logger.error(f"Error getting user IDs: {str(e)}")
            return []

    def update_user_stats(self, user_id: int, average_grade: float):
        """Update user statistics with caching"""
        try:
            with self.lock:
                with closing(sqlite3.connect(self.db_path)) as conn:
                    cursor = conn.cursor()
                    
                    # Update user stats with UPSERT
                    cursor.execute('''
                        INSERT INTO user_stats (user_id, total_calculations, last_calculation, average_grade)
                        VALUES (?, 1, CURRENT_TIMESTAMP, ?)
                        ON CONFLICT(user_id) DO UPDATE SET
                            total_calculations = total_calculations + 1,
                            last_calculation = CURRENT_TIMESTAMP,
                            average_grade = (average_grade * total_calculations + ?) / (total_calculations + 1)
                    ''', (user_id, average_grade, average_grade))
                    
                    conn.commit()
                    self.logger.info(f"Updated stats for user {user_id}")
        except sqlite3.Error as e:
            self.logger.error(f"Error updating user stats: {str(e)}")
            raise

    def get_user_stats(self, user_id: int) -> Optional[Dict]:
        """Get user statistics with caching"""
        try:
            with self.lock:
                with closing(sqlite3.connect(self.db_path)) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT total_calculations, last_calculation, average_grade
                        FROM user_stats
                        WHERE user_id = ?
                    ''', (user_id,))
                    result = cursor.fetchone()
                    
                    if result:
                        return {
                            'total_calculations': result[0],
                            'last_calculation': result[1],
                            'average_grade': result[2]
                        }
                    return None
        except sqlite3.Error as e:
            self.logger.error(f"Error getting user stats: {str(e)}")
            return None

    def cleanup_old_data(self, days: int = 30):
        """Clean up old data to maintain database performance"""
        try:
            with self.lock:
                with closing(sqlite3.connect(self.db_path)) as conn:
                    cursor = conn.cursor()
                    
                    # Delete old visitor records
                    cursor.execute('''
                        DELETE FROM visitors
                        WHERE last_visit < datetime('now', ?)
                    ''', (f'-{days} days',))
                    
                    # Delete old user stats
                    cursor.execute('''
                        DELETE FROM user_stats
                        WHERE last_calculation < datetime('now', ?)
                    ''', (f'-{days} days',))
                    
                    conn.commit()
                    self.logger.info(f"Cleaned up data older than {days} days")
        except sqlite3.Error as e:
            self.logger.error(f"Error cleaning up old data: {str(e)}")
            raise 