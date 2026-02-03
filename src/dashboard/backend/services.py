"""Business logic services for dashboard backend.

This module provides service layer abstractions to eliminate duplication
in API endpoints. Separates business logic from route handlers.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json


class DatasetService:
    """Service for dataset operations."""

    @staticmethod
    def load_dataset(dataset_name: str) -> Dict[str, Any]:
        """Load dataset by name.

        Args:
            dataset_name: Name of dataset file (e.g., "dataset", "b2b_dataset")

        Returns:
            Dict with metadata, statistics, and questions

        Raises:
            FileNotFoundError: If dataset doesn't exist
        """
        dataset_path = Path(f"data/{dataset_name}.json")
        if not dataset_path.exists():
            raise FileNotFoundError(f"{dataset_name} not found")

        with open(dataset_path, 'r') as f:
            data = json.load(f)

        return {
            "metadata": data.get("metadata", {}),
            "questions": data.get("questions", []),
            "statistics": {
                "total_questions": len(data.get("questions", [])),
                "version": data.get("metadata", {}).get("version", "unknown")
            }
        }


class EvaluationService:
    """Service for evaluation results operations."""

    @staticmethod
    def list_evaluations(pattern: str = "*.json") -> List[Dict[str, Any]]:
        """List evaluation results matching pattern.

        Args:
            pattern: Glob pattern (e.g., "eval_*.json", "b2b_eval_*.json")

        Returns:
            List of evaluation summaries sorted by timestamp
        """
        results_dir = Path("data/results")
        if not results_dir.exists():
            return []

        evaluations = []
        for result_file in sorted(results_dir.glob(pattern), reverse=True):
            try:
                with open(result_file, 'r') as f:
                    data = json.load(f)
                    evaluations.append({
                        "run_id": data.get("run_id"),
                        "timestamp": data.get("timestamp"),
                        "overall_pass_rate": data.get("overall_pass_rate", 0.0)
                    })
            except Exception:
                continue

        return evaluations


class StaticFileService:
    """Service for serving static frontend files."""

    @staticmethod
    def serve_file(filename: str) -> str:
        """Generic static file serving.

        Args:
            filename: File to serve (e.g., "style.css", "app.js")

        Returns:
            File content as string

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        frontend_dir = Path(__file__).parent.parent / "frontend"
        file_path = frontend_dir / filename

        if not file_path.exists():
            raise FileNotFoundError(f"{filename} not found")

        with open(file_path, 'r') as f:
            return f.read()
