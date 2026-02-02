"""Base repository class."""

import logging
from typing import Optional, List, Dict, Any, TypeVar, Generic
from abc import ABC, abstractmethod

from ..database import Database, get_database

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository with common CRUD operations.

    Provides:
    - Database access
    - Common query patterns
    - Logging
    """

    def __init__(self, db: Optional[Database] = None):
        """
        Initialize repository.

        Args:
            db: Database instance (uses singleton if None)
        """
        self._db = db or get_database()

    @property
    def db(self) -> Database:
        """Get database instance."""
        return self._db

    @property
    @abstractmethod
    def table_name(self) -> str:
        """Get the table name for this repository."""
        pass

    def count(self, where: Optional[str] = None, params: tuple = ()) -> int:
        """
        Count rows in table.

        Args:
            where: Optional WHERE clause (without 'WHERE' keyword)
            params: Query parameters

        Returns:
            Row count
        """
        query = f"SELECT COUNT(*) as count FROM {self.table_name}"
        if where:
            query += f" WHERE {where}"

        result = self.db.fetch_one(query, params)
        return result['count'] if result else 0

    def exists(self, id: str) -> bool:
        """
        Check if record exists by ID.

        Args:
            id: Record ID

        Returns:
            True if exists
        """
        result = self.db.fetch_one(
            f"SELECT 1 FROM {self.table_name} WHERE id = ?",
            (id,)
        )
        return result is not None

    def delete_by_id(self, id: str) -> bool:
        """
        Delete record by ID.

        Args:
            id: Record ID

        Returns:
            True if deleted
        """
        with self.db.get_cursor() as cursor:
            cursor.execute(
                f"DELETE FROM {self.table_name} WHERE id = ?",
                (id,)
            )
            deleted = cursor.rowcount > 0

        if deleted:
            logger.debug(f"Deleted {self.table_name} record: {id}")

        return deleted

    def delete_many(self, where: str, params: tuple) -> int:
        """
        Delete multiple records.

        Args:
            where: WHERE clause
            params: Query parameters

        Returns:
            Number of rows deleted
        """
        with self.db.get_cursor() as cursor:
            cursor.execute(
                f"DELETE FROM {self.table_name} WHERE {where}",
                params
            )
            return cursor.rowcount
