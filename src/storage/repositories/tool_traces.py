"""Repository for tool trace data."""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from .base import BaseRepository
from ...shared.models import ToolCall, ToolStatus

logger = logging.getLogger(__name__)


class ToolTraceRepository(BaseRepository[ToolCall]):
    """Repository for tool call traces."""

    @property
    def table_name(self) -> str:
        return "tool_traces"

    def save_trace(self, tool_call: ToolCall, session_id: str) -> ToolCall:
        """
        Save a tool call trace.

        Args:
            tool_call: ToolCall to save
            session_id: Associated session ID

        Returns:
            Saved ToolCall with ID
        """
        trace_id = tool_call.id or str(uuid.uuid4())

        with self.db.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tool_traces (
                    id, session_id, tool_name, input_data, output_data,
                    status, error_message, latency_ms, retry_count,
                    fallback_used, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trace_id,
                    session_id,
                    tool_call.tool_name,
                    json.dumps(tool_call.input_data),
                    json.dumps(tool_call.output_data) if tool_call.output_data else None,
                    tool_call.status.value if isinstance(tool_call.status, ToolStatus) else tool_call.status,
                    tool_call.error_message,
                    tool_call.latency_ms,
                    tool_call.retry_count,
                    tool_call.fallback_used,
                    tool_call.timestamp.isoformat()
                )
            )

        logger.debug(f"Saved tool trace {trace_id} for {tool_call.tool_name}")

        # Return with ID set
        tool_call.id = trace_id
        return tool_call

    def save_traces(self, tool_calls: List[ToolCall], session_id: str) -> List[ToolCall]:
        """
        Save multiple tool call traces.

        Args:
            tool_calls: List of ToolCalls to save
            session_id: Associated session ID

        Returns:
            List of saved ToolCalls
        """
        saved = []
        for tc in tool_calls:
            saved.append(self.save_trace(tc, session_id))
        return saved

    def get_by_id(self, trace_id: str) -> Optional[ToolCall]:
        """
        Get a tool trace by ID.

        Args:
            trace_id: Trace ID

        Returns:
            ToolCall or None
        """
        row = self.db.fetch_one(
            "SELECT * FROM tool_traces WHERE id = ?",
            (trace_id,)
        )

        if not row:
            return None

        return self._row_to_tool_call(row)

    def get_by_session(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[ToolCall]:
        """
        Get tool traces for a session.

        Args:
            session_id: Session ID
            limit: Maximum traces to return

        Returns:
            List of ToolCalls
        """
        query = """
            SELECT * FROM tool_traces
            WHERE session_id = ?
            ORDER BY timestamp ASC
        """
        params = [session_id]

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        rows = self.db.fetch_all(query, tuple(params))
        return [self._row_to_tool_call(row) for row in rows]

    def get_by_tool(
        self,
        tool_name: str,
        limit: int = 100
    ) -> List[ToolCall]:
        """
        Get recent traces for a specific tool.

        Args:
            tool_name: Tool name
            limit: Maximum traces to return

        Returns:
            List of ToolCalls
        """
        rows = self.db.fetch_all(
            """
            SELECT * FROM tool_traces
            WHERE tool_name = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (tool_name, limit)
        )
        return [self._row_to_tool_call(row) for row in rows]

    def get_stats_by_tool(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics grouped by tool.

        Returns:
            Dict of tool name -> stats
        """
        rows = self.db.fetch_all(
            """
            SELECT
                tool_name,
                COUNT(*) as total_calls,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count,
                SUM(CASE WHEN status = 'timeout' THEN 1 ELSE 0 END) as timeout_count,
                AVG(latency_ms) as avg_latency_ms,
                MAX(latency_ms) as max_latency_ms,
                SUM(retry_count) as total_retries
            FROM tool_traces
            GROUP BY tool_name
            """
        )

        stats = {}
        for row in rows:
            tool_name = row['tool_name']
            total = row['total_calls']
            success = row['success_count']

            stats[tool_name] = {
                'total_calls': total,
                'success_count': success,
                'error_count': row['error_count'],
                'timeout_count': row['timeout_count'],
                'success_rate': success / total if total > 0 else 0.0,
                'avg_latency_ms': row['avg_latency_ms'] or 0,
                'max_latency_ms': row['max_latency_ms'] or 0,
                'total_retries': row['total_retries'] or 0
            }

        return stats

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get tool statistics for a session.

        Args:
            session_id: Session ID

        Returns:
            Statistics dict
        """
        row = self.db.fetch_one(
            """
            SELECT
                COUNT(*) as total_calls,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                AVG(latency_ms) as avg_latency_ms,
                SUM(latency_ms) as total_latency_ms,
                COUNT(DISTINCT tool_name) as unique_tools
            FROM tool_traces
            WHERE session_id = ?
            """,
            (session_id,)
        )

        if not row:
            return {
                'total_calls': 0,
                'success_count': 0,
                'success_rate': 0.0,
                'avg_latency_ms': 0,
                'total_latency_ms': 0,
                'unique_tools': 0
            }

        total = row['total_calls']
        success = row['success_count']

        return {
            'total_calls': total,
            'success_count': success,
            'success_rate': success / total if total > 0 else 0.0,
            'avg_latency_ms': row['avg_latency_ms'] or 0,
            'total_latency_ms': row['total_latency_ms'] or 0,
            'unique_tools': row['unique_tools']
        }

    def delete_by_session(self, session_id: str) -> int:
        """
        Delete all traces for a session.

        Args:
            session_id: Session ID

        Returns:
            Number of traces deleted
        """
        return self.delete_many("session_id = ?", (session_id,))

    def _row_to_tool_call(self, row: Dict[str, Any]) -> ToolCall:
        """Convert database row to ToolCall."""
        return ToolCall(
            id=row['id'],
            tool_name=row['tool_name'],
            input_data=json.loads(row['input_data']) if row['input_data'] else {},
            output_data=json.loads(row['output_data']) if row['output_data'] else None,
            status=ToolStatus(row['status']) if row['status'] else ToolStatus.SUCCESS,
            error_message=row['error_message'],
            latency_ms=row['latency_ms'] or 0,
            retry_count=row['retry_count'] or 0,
            fallback_used=row['fallback_used'],
            timestamp=datetime.fromisoformat(row['timestamp']) if row['timestamp'] else datetime.utcnow()
        )
