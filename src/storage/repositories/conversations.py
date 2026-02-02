"""Repository for conversation data."""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from .base import BaseRepository
from ...shared.models import ConversationMessage, ConversationSession
from ...shared.utils import format_timestamp

logger = logging.getLogger(__name__)


class ConversationRepository(BaseRepository[ConversationMessage]):
    """Repository for conversation messages and sessions."""

    @property
    def table_name(self) -> str:
        return "conversations"

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        mode: Optional[str] = None,
        message_id: Optional[str] = None
    ) -> ConversationMessage:
        """
        Save a conversation message.

        Args:
            session_id: Session identifier
            role: Message role (user, assistant, system, tool)
            content: Message content
            mode: Research mode (normal, deep)
            message_id: Optional message ID (generates if None)

        Returns:
            Saved ConversationMessage
        """
        msg_id = message_id or str(uuid.uuid4())
        timestamp = datetime.utcnow()

        with self.db.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO conversations (id, session_id, role, content, mode, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (msg_id, session_id, role, content, mode, timestamp.isoformat())
            )

        logger.debug(f"Saved message {msg_id} for session {session_id}")

        return ConversationMessage(
            id=msg_id,
            role=role,
            content=content,
            timestamp=timestamp
        )

    def get_session_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[ConversationMessage]:
        """
        Get messages for a session.

        Args:
            session_id: Session identifier
            limit: Maximum messages to return
            offset: Number of messages to skip

        Returns:
            List of messages ordered by timestamp
        """
        query = """
            SELECT id, role, content, timestamp, mode
            FROM conversations
            WHERE session_id = ?
            ORDER BY timestamp ASC
        """
        params = [session_id]

        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        rows = self.db.fetch_all(query, tuple(params))

        return [
            ConversationMessage(
                id=row['id'],
                role=row['role'],
                content=row['content'],
                timestamp=datetime.fromisoformat(row['timestamp']) if row['timestamp'] else datetime.utcnow()
            )
            for row in rows
        ]

    def get_recent_messages(
        self,
        session_id: str,
        count: int = 20
    ) -> List[ConversationMessage]:
        """
        Get most recent messages for a session.

        Args:
            session_id: Session identifier
            count: Number of recent messages

        Returns:
            List of recent messages (oldest to newest)
        """
        # Get recent messages in reverse order, then reverse
        query = """
            SELECT id, role, content, timestamp, mode
            FROM conversations
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """
        rows = self.db.fetch_all(query, (session_id, count))

        # Reverse to get chronological order
        rows.reverse()

        return [
            ConversationMessage(
                id=row['id'],
                role=row['role'],
                content=row['content'],
                timestamp=datetime.fromisoformat(row['timestamp']) if row['timestamp'] else datetime.utcnow()
            )
            for row in rows
        ]

    def get_session_count(self, session_id: str) -> int:
        """
        Get message count for a session.

        Args:
            session_id: Session identifier

        Returns:
            Number of messages
        """
        return self.count("session_id = ?", (session_id,))

    def delete_session(self, session_id: str) -> int:
        """
        Delete all messages for a session.

        Args:
            session_id: Session identifier

        Returns:
            Number of messages deleted
        """
        count = self.delete_many("session_id = ?", (session_id,))
        logger.info(f"Deleted {count} messages for session {session_id}")
        return count

    def get_sessions(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get list of sessions with metadata.

        Args:
            limit: Maximum sessions to return
            offset: Number of sessions to skip

        Returns:
            List of session metadata dicts
        """
        query = """
            SELECT
                session_id,
                MIN(timestamp) as started_at,
                MAX(timestamp) as last_message_at,
                COUNT(*) as message_count,
                MAX(mode) as mode
            FROM conversations
            GROUP BY session_id
            ORDER BY MAX(timestamp) DESC
            LIMIT ? OFFSET ?
        """
        return self.db.fetch_all(query, (limit, offset))

    def session_exists(self, session_id: str) -> bool:
        """
        Check if session has any messages.

        Args:
            session_id: Session identifier

        Returns:
            True if session exists
        """
        return self.count("session_id = ?", (session_id,)) > 0

    def cleanup_old_sessions(self, days: int = 30) -> int:
        """
        Delete sessions older than specified days.

        Args:
            days: Age threshold in days

        Returns:
            Number of messages deleted
        """
        query = f"""
            DELETE FROM conversations
            WHERE session_id IN (
                SELECT session_id
                FROM conversations
                GROUP BY session_id
                HAVING MAX(timestamp) < datetime('now', '-{days} days')
            )
        """
        with self.db.get_cursor() as cursor:
            cursor.execute(query)
            count = cursor.rowcount

        logger.info(f"Cleaned up {count} old conversation messages")
        return count
