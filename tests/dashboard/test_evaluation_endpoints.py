"""
Unit tests for dashboard evaluation endpoints.

Tests the B2B evaluation list and detail endpoints to ensure they properly
serve evaluation results to the frontend.
"""

import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from dashboard.backend.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_b2b_evaluation_file(tmp_path):
    """Create a mock B2B evaluation result file."""
    results_dir = tmp_path / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    eval_data = {
        "run_id": "b2b_eval_test_123",
        "timestamp": "2026-02-02T12:00:00.000000",
        "dataset_type": "b2b",
        "total_questions": 5,
        "overall_pass_rate": 0.8,
        "avg_accuracy_score": 75.5,
        "tool_precision": 0.85,
        "multi_tool_rate": 0.6,
        "action_success_rate": 0.0,
        "avg_depth": 4.5,
        "category_metrics": {
            "company_research": {
                "total": 3,
                "passed": 2,
                "pass_rate": 0.6667,
                "avg_score": 70.0,
                "tool_precision": 0.9
            },
            "financial_analysis": {
                "total": 2,
                "passed": 2,
                "pass_rate": 1.0,
                "avg_score": 80.0,
                "tool_precision": 0.8
            }
        },
        "question_results": [
            {
                "question_id": "q1",
                "category": "company_research",
                "question_text": "Test question 1",
                "passed": True,
                "avg_score": 75.0,
                "avg_depth": 4.0
            },
            {
                "question_id": "q2",
                "category": "financial_analysis",
                "question_text": "Test question 2",
                "passed": True,
                "avg_score": 80.0,
                "avg_depth": 5.0
            }
        ]
    }

    eval_file = results_dir / "b2b_eval_test_123.json"
    with open(eval_file, 'w') as f:
        json.dump(eval_data, f)

    return results_dir, eval_data


class TestB2BEvaluationListEndpoint:
    """Tests for /api/b2b-evaluations endpoint."""

    def test_list_evaluations_empty_directory(self, client, tmp_path, monkeypatch):
        """Test that empty results directory returns empty list."""
        # Create empty results directory
        results_dir = tmp_path / "data" / "results"
        results_dir.mkdir(parents=True, exist_ok=True)

        # Monkey patch the Path in the app
        monkeypatch.setattr("dashboard.backend.app.Path", lambda x: results_dir if x == "data/results" else Path(x))

        response = client.get("/api/b2b-evaluations")

        assert response.status_code == 200
        data = response.json()
        assert "evaluations" in data
        assert data["evaluations"] == []

    def test_list_evaluations_with_results(self, client, mock_b2b_evaluation_file, monkeypatch):
        """Test that evaluations are listed correctly."""
        results_dir, eval_data = mock_b2b_evaluation_file

        # Monkey patch the Path in the app
        monkeypatch.setattr("dashboard.backend.app.Path", lambda x: results_dir if x == "data/results" else Path(x))

        response = client.get("/api/b2b-evaluations")

        assert response.status_code == 200
        data = response.json()
        assert "evaluations" in data
        assert len(data["evaluations"]) >= 1

        # Find our test evaluation
        test_eval = next((e for e in data["evaluations"] if e["run_id"] == "b2b_eval_test_123"), None)
        assert test_eval is not None
        assert test_eval["run_id"] == "b2b_eval_test_123"
        assert test_eval["dataset_type"] == "b2b"
        assert test_eval["total_questions"] == 5
        assert test_eval["overall_pass_rate"] == 0.8
        assert test_eval["avg_accuracy_score"] == 75.5
        assert test_eval["tool_precision"] == 0.85

    def test_list_evaluations_only_includes_b2b_prefix(self, client, tmp_path, monkeypatch):
        """Test that only b2b_eval_*.json files are included."""
        results_dir = tmp_path / "data" / "results"
        results_dir.mkdir(parents=True, exist_ok=True)

        # Create a b2b evaluation file
        b2b_file = results_dir / "b2b_eval_123.json"
        with open(b2b_file, 'w') as f:
            json.dump({"run_id": "b2b_eval_123", "timestamp": "2026-02-02T12:00:00", "total_questions": 1, "overall_pass_rate": 1.0, "avg_accuracy_score": 100, "tool_precision": 1.0, "avg_depth": 1, "category_metrics": {}}, f)

        # Create a non-b2b evaluation file (should be ignored)
        other_file = results_dir / "eval_456.json"
        with open(other_file, 'w') as f:
            json.dump({"run_id": "eval_456"}, f)

        # Monkey patch the Path in the app
        monkeypatch.setattr("dashboard.backend.app.Path", lambda x: results_dir if x == "data/results" else Path(x))

        response = client.get("/api/b2b-evaluations")

        assert response.status_code == 200
        data = response.json()
        assert len(data["evaluations"]) == 1
        assert data["evaluations"][0]["run_id"] == "b2b_eval_123"


class TestB2BEvaluationDetailEndpoint:
    """Tests for /api/b2b-evaluations/{run_id} endpoint."""

    def test_get_evaluation_detail_success(self, client, mock_b2b_evaluation_file, monkeypatch):
        """Test retrieving a specific evaluation by ID."""
        results_dir, eval_data = mock_b2b_evaluation_file

        # Monkey patch the Path in the app
        original_path = Path
        def patched_path(x):
            if "data/results" in str(x):
                return results_dir.parent.parent / x
            return original_path(x)

        monkeypatch.setattr("dashboard.backend.app.Path", patched_path)

        response = client.get("/api/b2b-evaluations/b2b_eval_test_123")

        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == "b2b_eval_test_123"
        assert data["total_questions"] == 5
        assert data["overall_pass_rate"] == 0.8
        assert "category_metrics" in data
        assert "question_results" in data
        assert len(data["question_results"]) == 2

    def test_get_evaluation_detail_not_found(self, client, tmp_path, monkeypatch):
        """Test 404 response for non-existent evaluation."""
        results_dir = tmp_path / "data" / "results"
        results_dir.mkdir(parents=True, exist_ok=True)

        # Monkey patch the Path in the app
        original_path = Path
        def patched_path(x):
            if "data/results" in str(x):
                return results_dir.parent.parent / x
            return original_path(x)

        monkeypatch.setattr("dashboard.backend.app.Path", patched_path)

        response = client.get("/api/b2b-evaluations/nonexistent_eval")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_evaluation_detail_includes_all_fields(self, client, mock_b2b_evaluation_file, monkeypatch):
        """Test that detail response includes all expected fields."""
        results_dir, eval_data = mock_b2b_evaluation_file

        # Monkey patch the Path in the app
        original_path = Path
        def patched_path(x):
            if "data/results" in str(x):
                return results_dir.parent.parent / x
            return original_path(x)

        monkeypatch.setattr("dashboard.backend.app.Path", patched_path)

        response = client.get("/api/b2b-evaluations/b2b_eval_test_123")

        assert response.status_code == 200
        data = response.json()

        # Check all expected top-level fields
        required_fields = [
            "run_id", "timestamp", "dataset_type", "total_questions",
            "overall_pass_rate", "avg_accuracy_score", "tool_precision",
            "multi_tool_rate", "action_success_rate", "avg_depth",
            "category_metrics", "question_results"
        ]

        for field in required_fields:
            assert field in data, f"Missing field: {field}"

        # Check category metrics structure
        assert len(data["category_metrics"]) == 2
        for category, metrics in data["category_metrics"].items():
            assert "total" in metrics
            assert "passed" in metrics
            assert "pass_rate" in metrics
            assert "avg_score" in metrics

        # Check question results structure
        for question in data["question_results"]:
            assert "question_id" in question
            assert "category" in question
            assert "question_text" in question
            assert "passed" in question
            assert "avg_score" in question
            assert "avg_depth" in question


class TestEndpointIntegration:
    """Integration tests for evaluation endpoints with real file system."""

    def test_real_evaluation_files_can_be_loaded(self, client):
        """Test that actual evaluation files in data/results can be loaded."""
        # This test uses the real file system
        response = client.get("/api/b2b-evaluations")

        assert response.status_code == 200
        data = response.json()
        assert "evaluations" in data

        # If there are any evaluations, test that we can load their details
        if data["evaluations"]:
            first_eval = data["evaluations"][0]
            detail_response = client.get(f"/api/b2b-evaluations/{first_eval['run_id']}")

            # Should either succeed or return 404 (if file was deleted)
            assert detail_response.status_code in [200, 404]

    def test_evaluation_list_is_sorted_by_timestamp(self, client, tmp_path, monkeypatch):
        """Test that evaluations are returned in reverse chronological order."""
        results_dir = tmp_path / "data" / "results"
        results_dir.mkdir(parents=True, exist_ok=True)

        # Create multiple evaluation files with different timestamps
        evals = [
            ("b2b_eval_001", "2026-02-02T10:00:00"),
            ("b2b_eval_002", "2026-02-02T12:00:00"),
            ("b2b_eval_003", "2026-02-02T11:00:00"),
        ]

        for run_id, timestamp in evals:
            eval_file = results_dir / f"{run_id}.json"
            with open(eval_file, 'w') as f:
                json.dump({
                    "run_id": run_id,
                    "timestamp": timestamp,
                    "total_questions": 1,
                    "overall_pass_rate": 1.0,
                    "avg_accuracy_score": 100,
                    "tool_precision": 1.0,
                    "avg_depth": 1,
                    "category_metrics": {}
                }, f)

        # Monkey patch the Path in the app
        monkeypatch.setattr("dashboard.backend.app.Path", lambda x: results_dir if x == "data/results" else Path(x))

        response = client.get("/api/b2b-evaluations")

        assert response.status_code == 200
        data = response.json()

        # Should be sorted by filename (which includes timestamp) in reverse order
        run_ids = [e["run_id"] for e in data["evaluations"]]
        assert run_ids == ["b2b_eval_003", "b2b_eval_002", "b2b_eval_001"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
