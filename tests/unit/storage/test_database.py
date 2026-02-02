"""Unit tests for storage/database.py."""

import pytest
import tempfile
import os
from pathlib import Path
import threading
import time

from src.storage.database import Database, get_database
from src.shared.exceptions import DatabaseConnectionError, DatabaseWriteError
from src.shared.config import reset_config


@pytest.fixture
def temp_db_path():
    """Create a temporary database path."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        path = Path(f.name)
    yield path
    # Cleanup
    if path.exists():
        os.unlink(path)
    # Also cleanup WAL and SHM files
    for suffix in ['-wal', '-shm']:
        wal_path = Path(str(path) + suffix)
        if wal_path.exists():
            os.unlink(wal_path)


@pytest.fixture
def db(temp_db_path):
    """Create a fresh database instance."""
    Database.reset_instance()
    database = Database(temp_db_path)
    database.initialize_schema()
    yield database
    database.close_all()
    Database.reset_instance()


class TestDatabaseInitialization:
    """Tests for database initialization."""

    def test_create_database(self, temp_db_path):
        """Test creating a new database."""
        Database.reset_instance()
        db = Database(temp_db_path)
        db.initialize_schema()
        assert temp_db_path.exists()
        db.close_all()

    def test_initialize_schema_creates_tables(self, db):
        """Test schema initialization creates all tables."""
        assert db.table_exists('conversations')
        assert db.table_exists('tool_traces')
        assert db.table_exists('evaluation_runs')
        assert db.table_exists('evaluation_results')

    def test_initialize_schema_idempotent(self, db):
        """Test schema initialization can be called multiple times."""
        db.initialize_schema()
        db.initialize_schema()
        assert db.table_exists('conversations')

    def test_singleton_returns_same_instance(self, temp_db_path):
        """Test singleton pattern returns same instance."""
        Database.reset_instance()
        db1 = Database.get_instance(temp_db_path)
        db2 = Database.get_instance()
        assert db1 is db2
        db1.close_all()
        Database.reset_instance()

    def test_reset_instance_clears_singleton(self, temp_db_path):
        """Test reset clears singleton."""
        Database.reset_instance()
        db1 = Database.get_instance(temp_db_path)
        Database.reset_instance()
        db2 = Database.get_instance(temp_db_path)
        assert db1 is not db2
        db2.close_all()
        Database.reset_instance()


class TestDatabaseOperations:
    """Tests for basic database operations."""

    def test_execute_query(self, db):
        """Test executing a query."""
        db.execute(
            "INSERT INTO conversations (id, session_id, role, content) VALUES (?, ?, ?, ?)",
            ('test-id', 'session-1', 'user', 'Hello')
        )
        result = db.fetch_one("SELECT * FROM conversations WHERE id = ?", ('test-id',))
        assert result is not None
        assert result['content'] == 'Hello'

    def test_fetch_one_returns_none_for_missing(self, db):
        """Test fetch_one returns None when not found."""
        result = db.fetch_one("SELECT * FROM conversations WHERE id = ?", ('nonexistent',))
        assert result is None

    def test_fetch_all_returns_list(self, db):
        """Test fetch_all returns list of results."""
        db.execute(
            "INSERT INTO conversations (id, session_id, role, content) VALUES (?, ?, ?, ?)",
            ('id-1', 'session-1', 'user', 'Hello')
        )
        db.execute(
            "INSERT INTO conversations (id, session_id, role, content) VALUES (?, ?, ?, ?)",
            ('id-2', 'session-1', 'assistant', 'Hi')
        )

        results = db.fetch_all("SELECT * FROM conversations WHERE session_id = ?", ('session-1',))
        assert len(results) == 2

    def test_fetch_all_returns_empty_list(self, db):
        """Test fetch_all returns empty list when no results."""
        results = db.fetch_all("SELECT * FROM conversations WHERE session_id = ?", ('nonexistent',))
        assert results == []

    def test_execute_many(self, db):
        """Test executing multiple inserts."""
        data = [
            ('id-1', 'session-1', 'user', 'Hello'),
            ('id-2', 'session-1', 'assistant', 'Hi'),
            ('id-3', 'session-1', 'user', 'Bye'),
        ]
        count = db.execute_many(
            "INSERT INTO conversations (id, session_id, role, content) VALUES (?, ?, ?, ?)",
            data
        )
        assert count == 3

    def test_table_exists_true(self, db):
        """Test table_exists returns True for existing table."""
        assert db.table_exists('conversations') is True

    def test_table_exists_false(self, db):
        """Test table_exists returns False for missing table."""
        assert db.table_exists('nonexistent_table') is False


class TestDatabaseTransactions:
    """Tests for database transactions."""

    def test_cursor_commits_on_success(self, db):
        """Test cursor commits on successful operation."""
        with db.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO conversations (id, session_id, role, content) VALUES (?, ?, ?, ?)",
                ('tx-test', 'session-1', 'user', 'Test')
            )

        result = db.fetch_one("SELECT * FROM conversations WHERE id = ?", ('tx-test',))
        assert result is not None

    def test_cursor_rollbacks_on_error(self, db):
        """Test cursor rollbacks on error."""
        try:
            with db.get_cursor() as cursor:
                cursor.execute(
                    "INSERT INTO conversations (id, session_id, role, content) VALUES (?, ?, ?, ?)",
                    ('rollback-test', 'session-1', 'user', 'Test')
                )
                # This should fail - invalid table
                cursor.execute("INSERT INTO nonexistent_table VALUES (1)")
        except DatabaseWriteError:
            pass

        # The first insert should have been rolled back
        result = db.fetch_one("SELECT * FROM conversations WHERE id = ?", ('rollback-test',))
        assert result is None

    def test_transaction_context_manager(self, db):
        """Test transaction context manager."""
        with db.transaction() as conn:
            conn.execute(
                "INSERT INTO conversations (id, session_id, role, content) VALUES (?, ?, ?, ?)",
                ('tx-1', 'session-1', 'user', 'First')
            )
            conn.execute(
                "INSERT INTO conversations (id, session_id, role, content) VALUES (?, ?, ?, ?)",
                ('tx-2', 'session-1', 'assistant', 'Second')
            )

        results = db.fetch_all("SELECT * FROM conversations WHERE session_id = ?", ('session-1',))
        assert len(results) == 2


class TestDatabaseStats:
    """Tests for database statistics."""

    def test_get_stats_empty(self, db):
        """Test stats on empty database."""
        stats = db.get_stats()
        assert stats['conversations_count'] == 0
        assert stats['tool_traces_count'] == 0
        assert stats['file_size_bytes'] > 0

    def test_get_stats_with_data(self, db):
        """Test stats with data."""
        db.execute(
            "INSERT INTO conversations (id, session_id, role, content) VALUES (?, ?, ?, ?)",
            ('stats-test', 'session-1', 'user', 'Test')
        )

        stats = db.get_stats()
        assert stats['conversations_count'] == 1


class TestDatabaseThreadSafety:
    """Tests for thread safety."""

    def test_concurrent_writes(self, db):
        """Test concurrent writes from multiple threads."""
        errors = []
        success_count = [0]
        lock = threading.Lock()

        def write_record(thread_id):
            try:
                for i in range(10):
                    db.execute(
                        "INSERT INTO conversations (id, session_id, role, content) VALUES (?, ?, ?, ?)",
                        (f'thread-{thread_id}-{i}', f'session-{thread_id}', 'user', f'Message {i}')
                    )
                    with lock:
                        success_count[0] += 1
            except Exception as e:
                with lock:
                    errors.append(str(e))

        threads = [threading.Thread(target=write_record, args=(i,)) for i in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert success_count[0] == 50

    def test_concurrent_reads_writes(self, db):
        """Test concurrent reads and writes."""
        # Insert initial data
        for i in range(10):
            db.execute(
                "INSERT INTO conversations (id, session_id, role, content) VALUES (?, ?, ?, ?)",
                (f'initial-{i}', 'session-1', 'user', f'Initial {i}')
            )

        errors = []
        read_count = [0]
        lock = threading.Lock()

        def reader():
            try:
                for _ in range(20):
                    results = db.fetch_all("SELECT * FROM conversations WHERE session_id = ?", ('session-1',))
                    with lock:
                        read_count[0] += len(results)
                    time.sleep(0.01)
            except Exception as e:
                with lock:
                    errors.append(f"Read error: {e}")

        def writer(thread_id):
            try:
                for i in range(10):
                    db.execute(
                        "INSERT INTO conversations (id, session_id, role, content) VALUES (?, ?, ?, ?)",
                        (f'concurrent-{thread_id}-{i}', 'session-1', 'user', f'Concurrent {i}')
                    )
                    time.sleep(0.01)
            except Exception as e:
                with lock:
                    errors.append(f"Write error: {e}")

        threads = [
            threading.Thread(target=reader),
            threading.Thread(target=reader),
            threading.Thread(target=writer, args=(1,)),
            threading.Thread(target=writer, args=(2,)),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert read_count[0] > 0


class TestDatabaseEdgeCases:
    """Edge case tests."""

    def test_empty_string_content(self, db):
        """Test storing empty string content."""
        db.execute(
            "INSERT INTO conversations (id, session_id, role, content) VALUES (?, ?, ?, ?)",
            ('empty-test', 'session-1', 'user', '')
        )
        result = db.fetch_one("SELECT * FROM conversations WHERE id = ?", ('empty-test',))
        assert result['content'] == ''

    def test_unicode_content(self, db):
        """Test storing unicode content."""
        content = "Hello 你好 مرحبا 🚀"
        db.execute(
            "INSERT INTO conversations (id, session_id, role, content) VALUES (?, ?, ?, ?)",
            ('unicode-test', 'session-1', 'user', content)
        )
        result = db.fetch_one("SELECT * FROM conversations WHERE id = ?", ('unicode-test',))
        assert result['content'] == content

    def test_large_content(self, db):
        """Test storing large content."""
        content = "x" * 100000  # 100KB
        db.execute(
            "INSERT INTO conversations (id, session_id, role, content) VALUES (?, ?, ?, ?)",
            ('large-test', 'session-1', 'user', content)
        )
        result = db.fetch_one("SELECT * FROM conversations WHERE id = ?", ('large-test',))
        assert len(result['content']) == 100000

    def test_special_characters_in_query(self, db):
        """Test content with SQL special characters."""
        content = "Test's \"quoted\" content; DROP TABLE users;--"
        db.execute(
            "INSERT INTO conversations (id, session_id, role, content) VALUES (?, ?, ?, ?)",
            ('special-test', 'session-1', 'user', content)
        )
        result = db.fetch_one("SELECT * FROM conversations WHERE id = ?", ('special-test',))
        assert result['content'] == content

    def test_null_values(self, db):
        """Test storing NULL values."""
        db.execute(
            "INSERT INTO conversations (id, session_id, role, content, mode) VALUES (?, ?, ?, ?, ?)",
            ('null-test', 'session-1', 'user', 'Content', None)
        )
        result = db.fetch_one("SELECT * FROM conversations WHERE id = ?", ('null-test',))
        assert result['mode'] is None

    def test_close_and_reconnect(self, db):
        """Test closing and reconnecting."""
        db.execute(
            "INSERT INTO conversations (id, session_id, role, content) VALUES (?, ?, ?, ?)",
            ('close-test', 'session-1', 'user', 'Before close')
        )

        db.close()

        # Should reconnect automatically
        result = db.fetch_one("SELECT * FROM conversations WHERE id = ?", ('close-test',))
        assert result is not None
