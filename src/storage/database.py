"""SQLite database connection manager."""

import sqlite3
import threading
import logging
from pathlib import Path
from typing import Optional, Any, List, Dict
from contextlib import contextmanager

from ..shared.config import get_config
from ..shared.exceptions import DatabaseConnectionError, DatabaseWriteError

logger = logging.getLogger(__name__)


class Database:
    """
    SQLite database manager with connection pooling and thread safety.

    Uses WAL mode for better concurrent read/write performance.
    """

    _instance: Optional['Database'] = None
    _lock = threading.Lock()

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file. Uses config default if None.
        """
        self.db_path = db_path or get_config().storage.database_path
        self._local = threading.local()
        self._initialized = False

    @classmethod
    def get_instance(cls, db_path: Optional[Path] = None) -> 'Database':
        """Get singleton database instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(db_path)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reset singleton instance (for testing)."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance.close_all()
                cls._instance = None

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            try:
                self._local.connection = sqlite3.connect(
                    str(self.db_path),
                    check_same_thread=False,
                    timeout=30.0
                )
                # Enable WAL mode for better concurrency
                self._local.connection.execute("PRAGMA journal_mode=WAL")
                # Enable foreign keys
                self._local.connection.execute("PRAGMA foreign_keys=ON")
                # Return rows as dictionaries
                self._local.connection.row_factory = sqlite3.Row

                logger.debug(f"Created new database connection for thread {threading.current_thread().name}")
            except sqlite3.Error as e:
                raise DatabaseConnectionError(f"Failed to connect to database: {e}")

        return self._local.connection

    @contextmanager
    def get_cursor(self):
        """
        Get a database cursor with automatic commit/rollback.

        Yields:
            sqlite3.Cursor: Database cursor

        Example:
            with db.get_cursor() as cursor:
                cursor.execute("SELECT * FROM users")
                rows = cursor.fetchall()
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise DatabaseWriteError(f"Database operation failed: {e}")
        finally:
            cursor.close()

    @contextmanager
    def transaction(self):
        """
        Execute multiple operations in a single transaction.

        Yields:
            sqlite3.Connection: Database connection

        Example:
            with db.transaction() as conn:
                conn.execute("INSERT INTO ...")
                conn.execute("UPDATE ...")
        """
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Transaction failed: {e}")
            raise DatabaseWriteError(f"Transaction failed: {e}")

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        Execute a single query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Cursor with results
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor

    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """
        Execute a query with multiple parameter sets.

        Args:
            query: SQL query string
            params_list: List of parameter tuples

        Returns:
            Number of rows affected
        """
        with self.get_cursor() as cursor:
            cursor.executemany(query, params_list)
            return cursor.rowcount

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """
        Fetch a single row.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Row as dictionary or None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            cursor.close()

    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Fetch all matching rows.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of rows as dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            cursor.close()

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        result = self.fetch_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return result is not None

    def close(self):
        """Close the thread-local connection."""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
            logger.debug(f"Closed database connection for thread {threading.current_thread().name}")

    def close_all(self):
        """Close all connections (call on shutdown)."""
        self.close()

    def initialize_schema(self):
        """Initialize database schema."""
        if self._initialized:
            return

        schema = """
        -- Conversations table
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            mode TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_conversations_session
            ON conversations(session_id);
        CREATE INDEX IF NOT EXISTS idx_conversations_timestamp
            ON conversations(timestamp);

        -- Tool traces table
        CREATE TABLE IF NOT EXISTS tool_traces (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            conversation_id TEXT,
            tool_name TEXT NOT NULL,
            input_data TEXT,
            output_data TEXT,
            status TEXT,
            error_message TEXT,
            latency_ms INTEGER,
            retry_count INTEGER DEFAULT 0,
            fallback_used TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        );

        CREATE INDEX IF NOT EXISTS idx_tool_traces_session
            ON tool_traces(session_id);
        CREATE INDEX IF NOT EXISTS idx_tool_traces_tool
            ON tool_traces(tool_name);

        -- Evaluation runs table
        CREATE TABLE IF NOT EXISTS evaluation_runs (
            id TEXT PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            config TEXT,
            status TEXT DEFAULT 'running',
            total_questions INTEGER DEFAULT 0,
            questions_completed INTEGER DEFAULT 0,
            metrics TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_evaluation_runs_timestamp
            ON evaluation_runs(timestamp);
        CREATE INDEX IF NOT EXISTS idx_evaluation_runs_status
            ON evaluation_runs(status);

        -- Evaluation results table
        CREATE TABLE IF NOT EXISTS evaluation_results (
            id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            question_id TEXT NOT NULL,
            question_text TEXT,
            category TEXT,
            ground_truth TEXT,
            attempts TEXT,
            consensus_answer TEXT,
            pass_5 BOOLEAN,
            pass_10 BOOLEAN,
            tool_efficiency REAL,
            tool_success_rate REAL,
            avg_latency_ms REAL,
            FOREIGN KEY (run_id) REFERENCES evaluation_runs(id)
        );

        CREATE INDEX IF NOT EXISTS idx_evaluation_results_run
            ON evaluation_results(run_id);
        CREATE INDEX IF NOT EXISTS idx_evaluation_results_category
            ON evaluation_results(category);
        """

        with self.transaction() as conn:
            conn.executescript(schema)

        self._initialized = True
        logger.info(f"Database schema initialized at {self.db_path}")

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        stats = {}

        # Table counts
        tables = ['conversations', 'tool_traces', 'evaluation_runs', 'evaluation_results']
        for table in tables:
            if self.table_exists(table):
                result = self.fetch_one(f"SELECT COUNT(*) as count FROM {table}")
                stats[f"{table}_count"] = result['count'] if result else 0
            else:
                stats[f"{table}_count"] = 0

        # Database file size
        if self.db_path.exists():
            stats['file_size_bytes'] = self.db_path.stat().st_size
        else:
            stats['file_size_bytes'] = 0

        return stats


# Convenience function
def get_database() -> Database:
    """Get the singleton database instance."""
    db = Database.get_instance()
    db.initialize_schema()
    return db
