"""Memory management for the agent."""

import json
import logging
import time
import threading
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from collections import deque
from datetime import datetime

from src.shared.config import get_config
from src.storage.repositories import ConversationRepository
from src.storage.database import get_database

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """A conversation message."""
    role: str  # "user", "assistant", or "system"
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls."""
        return {
            "role": self.role,
            "content": self.content
        }

    def to_storage_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class ShortTermMemory:
    """
    Short-term memory for current conversation context.

    Features:
    - Maintains recent messages within token/count limits
    - Automatic trimming of old messages
    - Thread-safe operations
    """

    DEFAULT_MAX_MESSAGES = 20
    DEFAULT_MAX_TOKENS = 8000  # Rough estimate

    def __init__(
        self,
        max_messages: Optional[int] = None,
        max_tokens: Optional[int] = None,
    ):
        """
        Initialize short-term memory.

        Args:
            max_messages: Maximum number of messages to retain
            max_tokens: Maximum estimated tokens to retain
        """
        config = get_config()

        self.max_messages = max_messages or config.memory.max_messages
        self.max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS

        self._messages: deque = deque(maxlen=self.max_messages * 2)  # Buffer for trimming
        self._lock = threading.RLock()

    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a message to memory.

        Args:
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata
        """
        with self._lock:
            message = Message(
                role=role,
                content=content,
                metadata=metadata or {}
            )
            self._messages.append(message)
            self._trim_if_needed()

    def add_user_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a user message."""
        self.add_message("user", content, metadata)

    def add_assistant_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add an assistant message."""
        self.add_message("assistant", content, metadata)

    def get_messages(self) -> List[Message]:
        """Get all messages in memory."""
        with self._lock:
            return list(self._messages)

    def get_messages_for_api(self) -> List[Dict[str, Any]]:
        """Get messages formatted for API calls."""
        with self._lock:
            return [msg.to_dict() for msg in self._messages]

    def get_recent_messages(self, count: int) -> List[Message]:
        """Get the most recent messages."""
        with self._lock:
            messages = list(self._messages)
            return messages[-count:] if len(messages) > count else messages

    def clear(self) -> int:
        """
        Clear all messages.

        Returns:
            Number of messages cleared
        """
        with self._lock:
            count = len(self._messages)
            self._messages.clear()
            return count

    def _trim_if_needed(self) -> None:
        """Trim messages if over limits."""
        # Trim by count
        while len(self._messages) > self.max_messages:
            self._messages.popleft()

        # Trim by estimated tokens (rough estimate: 4 chars = 1 token)
        total_chars = sum(len(m.content) for m in self._messages)
        estimated_tokens = total_chars // 4

        while estimated_tokens > self.max_tokens and len(self._messages) > 2:
            removed = self._messages.popleft()
            total_chars -= len(removed.content)
            estimated_tokens = total_chars // 4

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate (4 chars ≈ 1 token)."""
        return len(text) // 4

    def __len__(self) -> int:
        """Return number of messages."""
        return len(self._messages)


class LongTermMemory:
    """
    Long-term memory for persistent storage across sessions.

    Features:
    - SQLite-backed persistent storage
    - Session-based organization
    - Retrieval by recency and relevance
    """

    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize long-term memory.

        Args:
            session_id: Optional session identifier
        """
        self.session_id = session_id or self._generate_session_id()
        self._repository: Optional[ConversationRepository] = None
        self._initialized = False

    def _get_repository(self) -> ConversationRepository:
        """Get or create repository instance."""
        if self._repository is None:
            try:
                db = get_database()
                self._repository = ConversationRepository(db)
                self._initialized = True
            except Exception as e:
                logger.warning(f"Could not initialize long-term memory: {e}")
                raise
        return self._repository

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        import uuid
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    def save_message(
        self,
        role: str,
        content: str,
        mode: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Save a message to long-term storage.

        Args:
            role: Message role
            content: Message content
            mode: Research mode (normal/deep)
            metadata: Optional metadata

        Returns:
            Message ID if saved, None if storage unavailable
        """
        try:
            repo = self._get_repository()
            return repo.save_message(
                session_id=self.session_id,
                role=role,
                content=content,
                mode=mode,
                metadata=metadata
            )
        except Exception as e:
            logger.warning(f"Failed to save message to long-term memory: {e}")
            return None

    def get_session_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history for current session.

        Args:
            limit: Maximum messages to retrieve

        Returns:
            List of message dictionaries
        """
        try:
            repo = self._get_repository()
            return repo.get_session_messages(self.session_id, limit=limit)
        except Exception as e:
            logger.warning(f"Failed to retrieve session history: {e}")
            return []

    def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent session summaries.

        Args:
            limit: Maximum sessions to retrieve

        Returns:
            List of session summaries
        """
        try:
            repo = self._get_repository()
            return repo.get_sessions(limit=limit)
        except Exception as e:
            logger.warning(f"Failed to retrieve sessions: {e}")
            return []

    def search_history(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search conversation history.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            Matching messages
        """
        try:
            repo = self._get_repository()
            return repo.search_messages(query, limit=limit)
        except Exception as e:
            logger.warning(f"Failed to search history: {e}")
            return []

    def delete_session(self) -> bool:
        """
        Delete current session from storage.

        Returns:
            True if deleted successfully
        """
        try:
            repo = self._get_repository()
            return repo.delete_session(self.session_id)
        except Exception as e:
            logger.warning(f"Failed to delete session: {e}")
            return False

    def new_session(self) -> str:
        """
        Start a new session.

        Returns:
            New session ID
        """
        self.session_id = self._generate_session_id()
        return self.session_id

    @property
    def is_available(self) -> bool:
        """Check if long-term memory is available."""
        try:
            self._get_repository()
            return True
        except Exception:
            return False


class MemoryManager:
    """
    Unified memory manager combining short-term and long-term memory.

    Features:
    - Automatic synchronization between memories
    - Context window management
    - Session management
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        max_short_term_messages: int = 20,
        enable_long_term: bool = True,
    ):
        """
        Initialize memory manager.

        Args:
            session_id: Optional session ID for long-term memory
            max_short_term_messages: Max messages in short-term memory
            enable_long_term: Whether to enable long-term memory
        """
        self.short_term = ShortTermMemory(max_messages=max_short_term_messages)
        self._enable_long_term = enable_long_term

        if enable_long_term:
            try:
                self.long_term = LongTermMemory(session_id=session_id)
            except Exception as e:
                logger.warning(f"Long-term memory disabled: {e}")
                self.long_term = None
                self._enable_long_term = False
        else:
            self.long_term = None

        self._current_mode: Optional[str] = None

    def add_user_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a user message to both memories."""
        self.short_term.add_user_message(content, metadata)

        if self._enable_long_term and self.long_term:
            self.long_term.save_message("user", content, self._current_mode, metadata)

    def add_assistant_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add an assistant message to both memories."""
        self.short_term.add_assistant_message(content, metadata)

        if self._enable_long_term and self.long_term:
            self.long_term.save_message("assistant", content, self._current_mode, metadata)

    def add_system_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a system message (short-term only)."""
        self.short_term.add_message("system", content, metadata)

    def get_context_messages(self) -> List[Dict[str, Any]]:
        """Get messages for LLM context."""
        return self.short_term.get_messages_for_api()

    def get_recent_context(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages for context."""
        messages = self.short_term.get_recent_messages(count)
        return [m.to_dict() for m in messages]

    def set_mode(self, mode: str) -> None:
        """Set current research mode."""
        self._current_mode = mode

    def clear_short_term(self) -> int:
        """Clear short-term memory."""
        return self.short_term.clear()

    def new_session(self) -> Optional[str]:
        """Start a new session."""
        self.short_term.clear()
        if self.long_term:
            return self.long_term.new_session()
        return None

    def get_session_id(self) -> Optional[str]:
        """Get current session ID."""
        return self.long_term.session_id if self.long_term else None

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        stats = {
            "short_term_messages": len(self.short_term),
            "long_term_enabled": self._enable_long_term,
            "current_mode": self._current_mode,
        }

        if self.long_term:
            stats["session_id"] = self.long_term.session_id

        return stats

    def load_session_context(self, message_count: int = 10) -> int:
        """
        Load recent messages from long-term memory into short-term.

        Args:
            message_count: Number of messages to load

        Returns:
            Number of messages loaded
        """
        if not self.long_term:
            return 0

        try:
            messages = self.long_term.get_session_history(limit=message_count)

            for msg in messages:
                self.short_term.add_message(
                    role=msg.get("role", "user"),
                    content=msg.get("content", ""),
                    metadata=msg.get("metadata")
                )

            return len(messages)
        except Exception as e:
            logger.warning(f"Failed to load session context: {e}")
            return 0


class CriticalInfoExtractor:
    """Extracts critical information from conversations for long-term storage."""

    EXTRACTION_PROMPT = """Analyze this conversation exchange and extract any critical information worth remembering.

User: {user_message}
Assistant: {assistant_response}

Extract ONLY if present (return empty if nothing critical):
- User preferences (units, format, communication style)
- User context (profession, location, recurring interests)
- Corrections to previous answers
- Important facts the user wants remembered

Return JSON only: {{"items": [{{"type": "preference|context|correction|fact", "content": "...", "importance": "high|medium|low"}}]}}
Return {{"items": []}} if nothing critical.

JSON response:"""

    def __init__(self, llm_client=None):
        """Initialize extractor with optional LLM client."""
        self._llm_client = llm_client

    def extract(self, user_msg: str, assistant_msg: str, llm_client=None) -> List[Dict[str, Any]]:
        """
        Extract critical info from a conversation exchange.

        Args:
            user_msg: The user's message
            assistant_msg: The assistant's response
            llm_client: Optional LLM client override

        Returns:
            List of extracted items with type, content, and importance
        """
        client = llm_client or self._llm_client
        if not client:
            return []

        prompt = self.EXTRACTION_PROMPT.format(
            user_message=user_msg,
            assistant_response=assistant_msg[:500]  # Truncate to avoid token issues
        )

        try:
            # Use a quick query with low tokens
            response = client.client.messages.create(
                model=client.model,
                max_tokens=256,
                temperature=0.1,  # Low temperature for structured output
                messages=[{"role": "user", "content": prompt}]
            )

            # Extract text response
            response_text = ""
            for block in response.content:
                if block.type == "text":
                    response_text = block.text
                    break

            # Parse JSON
            data = json.loads(response_text.strip())
            items = data.get("items", [])

            # Filter by importance
            return [
                item for item in items
                if item.get("importance") in ("high", "medium")
            ]

        except json.JSONDecodeError:
            logger.warning("Failed to parse critical info extraction response as JSON")
            return []
        except Exception as e:
            logger.warning(f"Critical info extraction failed: {e}")
            return []

    def extract_async(self, user_msg: str, assistant_msg: str, llm_client=None):
        """
        Extract critical info asynchronously (non-blocking).

        Returns immediately with None, extraction runs in background.
        """
        import threading

        def _extract():
            return self.extract(user_msg, assistant_msg, llm_client)

        thread = threading.Thread(target=_extract, daemon=True)
        thread.start()
        return None  # Returns immediately


# Global extractor instance
_critical_extractor: Optional[CriticalInfoExtractor] = None

def get_critical_extractor() -> CriticalInfoExtractor:
    """Get or create global critical info extractor."""
    global _critical_extractor
    if _critical_extractor is None:
        _critical_extractor = CriticalInfoExtractor()
    return _critical_extractor
