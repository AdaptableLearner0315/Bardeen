"""Repository for evaluation data."""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from .base import BaseRepository
from ...shared.models import (
    EvaluationRun,
    EvaluationMetrics,
    QuestionResult,
    EvaluationSummary,
    AttemptResult
)

logger = logging.getLogger(__name__)


class EvaluationRepository(BaseRepository[EvaluationRun]):
    """Repository for evaluation runs and results."""

    @property
    def table_name(self) -> str:
        return "evaluation_runs"

    def create_run(
        self,
        total_questions: int,
        config: Optional[Dict[str, Any]] = None
    ) -> EvaluationRun:
        """
        Create a new evaluation run.

        Args:
            total_questions: Number of questions in evaluation
            config: Evaluation configuration

        Returns:
            Created EvaluationRun
        """
        run_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()

        with self.db.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO evaluation_runs (
                    id, timestamp, config, status, total_questions, questions_completed
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    timestamp.isoformat(),
                    json.dumps(config or {}),
                    "running",
                    total_questions,
                    0
                )
            )

        logger.info(f"Created evaluation run {run_id} with {total_questions} questions")

        return EvaluationRun(
            run_id=run_id,
            timestamp=timestamp,
            status="running",
            total_questions=total_questions,
            questions_completed=0,
            config=config or {}
        )

    def update_run_status(
        self,
        run_id: str,
        status: str,
        questions_completed: Optional[int] = None,
        metrics: Optional[EvaluationMetrics] = None
    ) -> bool:
        """
        Update evaluation run status.

        Args:
            run_id: Run ID
            status: New status
            questions_completed: Number of questions completed
            metrics: Final metrics

        Returns:
            True if updated
        """
        updates = ["status = ?"]
        params = [status]

        if questions_completed is not None:
            updates.append("questions_completed = ?")
            params.append(questions_completed)

        if metrics:
            updates.append("metrics = ?")
            params.append(json.dumps(metrics.model_dump()))

        params.append(run_id)

        with self.db.get_cursor() as cursor:
            cursor.execute(
                f"UPDATE evaluation_runs SET {', '.join(updates)} WHERE id = ?",
                tuple(params)
            )
            updated = cursor.rowcount > 0

        if updated:
            logger.debug(f"Updated evaluation run {run_id} to status {status}")

        return updated

    def save_question_result(
        self,
        run_id: str,
        result: QuestionResult
    ) -> str:
        """
        Save a question result.

        Args:
            run_id: Evaluation run ID
            result: Question result to save

        Returns:
            Result ID
        """
        result_id = str(uuid.uuid4())

        # Serialize attempts
        attempts_json = json.dumps([
            {
                'attempt_number': a.attempt_number,
                'answer': a.answer,
                'is_correct': a.is_correct,
                'latency_ms': a.latency_ms,
                'error': a.error,
                'tool_calls': [tc.model_dump() for tc in a.tool_calls]
            }
            for a in result.attempts
        ])

        with self.db.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO evaluation_results (
                    id, run_id, question_id, question_text, category,
                    ground_truth, attempts, consensus_answer, pass_5, pass_10,
                    tool_efficiency, tool_success_rate, avg_latency_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result_id,
                    run_id,
                    result.question_id,
                    result.question_text,
                    result.category,
                    result.ground_truth,
                    attempts_json,
                    result.consensus_answer,
                    result.pass_5,
                    result.pass_10,
                    result.tool_efficiency,
                    result.tool_success_rate,
                    result.avg_latency_ms
                )
            )

            # Update run progress
            cursor.execute(
                """
                UPDATE evaluation_runs
                SET questions_completed = questions_completed + 1
                WHERE id = ?
                """,
                (run_id,)
            )

        logger.debug(f"Saved result for question {result.question_id} in run {run_id}")
        return result_id

    def get_run(self, run_id: str) -> Optional[EvaluationRun]:
        """
        Get evaluation run by ID.

        Args:
            run_id: Run ID

        Returns:
            EvaluationRun or None
        """
        row = self.db.fetch_one(
            "SELECT * FROM evaluation_runs WHERE id = ?",
            (run_id,)
        )

        if not row:
            return None

        # Get question results
        results_rows = self.db.fetch_all(
            "SELECT * FROM evaluation_results WHERE run_id = ?",
            (run_id,)
        )

        question_results = [
            self._row_to_question_result(r)
            for r in results_rows
        ]

        metrics = EvaluationMetrics()
        if row['metrics']:
            metrics_data = json.loads(row['metrics'])
            metrics = EvaluationMetrics(**metrics_data)

        return EvaluationRun(
            run_id=row['id'],
            timestamp=datetime.fromisoformat(row['timestamp']) if row['timestamp'] else datetime.utcnow(),
            status=row['status'],
            total_questions=row['total_questions'],
            questions_completed=row['questions_completed'],
            config=json.loads(row['config']) if row['config'] else {},
            metrics=metrics,
            question_results=question_results
        )

    def get_run_summary(self, run_id: str) -> Optional[EvaluationSummary]:
        """
        Get evaluation run summary (without detailed results).

        Args:
            run_id: Run ID

        Returns:
            EvaluationSummary or None
        """
        row = self.db.fetch_one(
            "SELECT * FROM evaluation_runs WHERE id = ?",
            (run_id,)
        )

        if not row:
            return None

        metrics = EvaluationMetrics()
        if row['metrics']:
            metrics_data = json.loads(row['metrics'])
            metrics = EvaluationMetrics(**metrics_data)

        return EvaluationSummary(
            id=row['id'],
            timestamp=datetime.fromisoformat(row['timestamp']) if row['timestamp'] else datetime.utcnow(),
            status=row['status'],
            total_questions=row['total_questions'],
            questions_completed=row['questions_completed'],
            metrics=metrics
        )

    def list_runs(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[EvaluationSummary]:
        """
        List evaluation runs.

        Args:
            limit: Maximum runs to return
            offset: Number of runs to skip
            status: Optional status filter

        Returns:
            List of EvaluationSummary
        """
        query = "SELECT * FROM evaluation_runs"
        params = []

        if status:
            query += " WHERE status = ?"
            params.append(status)

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = self.db.fetch_all(query, tuple(params))

        return [
            EvaluationSummary(
                id=row['id'],
                timestamp=datetime.fromisoformat(row['timestamp']) if row['timestamp'] else datetime.utcnow(),
                status=row['status'],
                total_questions=row['total_questions'],
                questions_completed=row['questions_completed'],
                metrics=EvaluationMetrics(**json.loads(row['metrics'])) if row['metrics'] else EvaluationMetrics()
            )
            for row in rows
        ]

    def get_results_by_category(
        self,
        run_id: str,
        category: str
    ) -> List[QuestionResult]:
        """
        Get question results by category.

        Args:
            run_id: Run ID
            category: Category filter

        Returns:
            List of QuestionResult
        """
        rows = self.db.fetch_all(
            """
            SELECT * FROM evaluation_results
            WHERE run_id = ? AND category = ?
            ORDER BY question_id
            """,
            (run_id, category)
        )

        return [self._row_to_question_result(row) for row in rows]

    def get_category_stats(self, run_id: str) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics by category for a run.

        Args:
            run_id: Run ID

        Returns:
            Dict of category -> stats
        """
        rows = self.db.fetch_all(
            """
            SELECT
                category,
                COUNT(*) as total,
                SUM(CASE WHEN pass_5 THEN 1 ELSE 0 END) as pass_5_count,
                SUM(CASE WHEN pass_10 THEN 1 ELSE 0 END) as pass_10_count,
                AVG(tool_efficiency) as avg_tool_efficiency,
                AVG(tool_success_rate) as avg_tool_success_rate,
                AVG(avg_latency_ms) as avg_latency_ms
            FROM evaluation_results
            WHERE run_id = ?
            GROUP BY category
            """,
            (run_id,)
        )

        stats = {}
        for row in rows:
            total = row['total']
            stats[row['category']] = {
                'total': total,
                'pass_5': row['pass_5_count'] / total if total > 0 else 0,
                'pass_10': row['pass_10_count'] / total if total > 0 else 0,
                'tool_efficiency': row['avg_tool_efficiency'] or 0,
                'tool_success_rate': row['avg_tool_success_rate'] or 0,
                'avg_latency_ms': row['avg_latency_ms'] or 0
            }

        return stats

    def delete_run(self, run_id: str) -> bool:
        """
        Delete an evaluation run and its results.

        Args:
            run_id: Run ID

        Returns:
            True if deleted
        """
        with self.db.transaction() as conn:
            # Delete results first (foreign key constraint)
            conn.execute(
                "DELETE FROM evaluation_results WHERE run_id = ?",
                (run_id,)
            )
            # Delete run
            cursor = conn.execute(
                "DELETE FROM evaluation_runs WHERE id = ?",
                (run_id,)
            )
            deleted = cursor.rowcount > 0

        if deleted:
            logger.info(f"Deleted evaluation run {run_id}")

        return deleted

    def _row_to_question_result(self, row: Dict[str, Any]) -> QuestionResult:
        """Convert database row to QuestionResult."""
        attempts_data = json.loads(row['attempts']) if row['attempts'] else []

        attempts = []
        for a in attempts_data:
            attempts.append(AttemptResult(
                attempt_number=a['attempt_number'],
                answer=a['answer'],
                is_correct=a.get('is_correct', False),
                latency_ms=a.get('latency_ms', 0),
                error=a.get('error'),
                tool_calls=[]  # Tool calls stored separately for simplicity
            ))

        return QuestionResult(
            question_id=row['question_id'],
            question_text=row['question_text'],
            category=row['category'],
            ground_truth=row['ground_truth'],
            attempts=attempts,
            consensus_answer=row['consensus_answer'],
            pass_5=bool(row['pass_5']),
            pass_10=bool(row['pass_10']),
            tool_efficiency=row['tool_efficiency'] or 0,
            tool_success_rate=row['tool_success_rate'] or 0,
            avg_latency_ms=row['avg_latency_ms'] or 0
        )
