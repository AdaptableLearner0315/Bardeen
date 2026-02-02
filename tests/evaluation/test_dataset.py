"""Tests for dataset loader module."""

import pytest
import json
import tempfile
from pathlib import Path

from src.evaluation.dataset import DatasetLoader, load_dataset
from src.shared.models import DatasetQuestion


class TestDatasetLoader:
    """Tests for DatasetLoader class."""

    @pytest.fixture
    def sample_dataset(self):
        """Create a sample dataset for testing."""
        return {
            "metadata": {
                "version": "1.0",
                "name": "Test Dataset"
            },
            "questions": [
                {
                    "id": "geo_001",
                    "question": "What is the capital of France?",
                    "category": "geography",
                    "difficulty": "easy",
                    "expected_behavior": {
                        "tools": ["wikipedia"],
                        "sequence": ["lookup"]
                    },
                    "ground_truth": {
                        "answer": "Paris",
                        "variants": ["Paris, France"]
                    },
                    "evaluation": {
                        "correctness_threshold": 0.85,
                        "requires_citation": False
                    }
                },
                {
                    "id": "hist_001",
                    "question": "When did World War II end?",
                    "category": "history",
                    "difficulty": "medium",
                    "expected_behavior": {
                        "tools": ["wikipedia", "web_search"],
                        "sequence": ["search", "verify"]
                    },
                    "ground_truth": {
                        "answer": "1945",
                        "variants": ["September 1945", "1945 (September 2)"]
                    },
                    "evaluation": {
                        "correctness_threshold": 0.8,
                        "requires_citation": True
                    }
                },
                {
                    "id": "sci_001",
                    "question": "What is the speed of light?",
                    "category": "science",
                    "difficulty": "easy",
                    "expected_behavior": {
                        "tools": ["calculator", "wikipedia"],
                        "sequence": ["lookup"]
                    },
                    "ground_truth": {
                        "answer": "299,792,458 m/s",
                        "variants": ["300,000 km/s", "~3x10^8 m/s"]
                    },
                    "evaluation": {
                        "correctness_threshold": 0.9,
                        "requires_citation": False
                    }
                }
            ]
        }

    @pytest.fixture
    def dataset_file(self, sample_dataset):
        """Create a temporary dataset file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_dataset, f)
            return Path(f.name)

    def test_initialization(self):
        """Test basic initialization."""
        loader = DatasetLoader()
        assert loader.dataset_path is None
        assert loader.questions == []
        assert loader.metadata == {}

    def test_initialization_with_path(self, dataset_file):
        """Test initialization with path."""
        loader = DatasetLoader(dataset_path=dataset_file)
        assert loader.dataset_path == dataset_file

    def test_load_success(self, dataset_file):
        """Test successful dataset loading."""
        loader = DatasetLoader(dataset_file)
        questions = loader.load()

        assert len(questions) == 3
        assert all(isinstance(q, DatasetQuestion) for q in questions)
        assert loader.metadata["version"] == "1.0"

    def test_load_with_override_path(self, dataset_file):
        """Test loading with path override."""
        loader = DatasetLoader()
        questions = loader.load(dataset_file)

        assert len(questions) == 3

    def test_load_file_not_found(self):
        """Test loading non-existent file."""
        loader = DatasetLoader(Path("/nonexistent/path/dataset.json"))

        with pytest.raises(FileNotFoundError):
            loader.load()

    def test_load_no_path(self):
        """Test loading without any path."""
        loader = DatasetLoader()

        with pytest.raises(FileNotFoundError):
            loader.load()

    def test_load_stores_questions(self, dataset_file):
        """Test that loaded questions are stored."""
        loader = DatasetLoader(dataset_file)
        loader.load()

        assert len(loader.questions) == 3
        assert loader.questions[0].id == "geo_001"

    def test_question_properties(self, dataset_file):
        """Test loaded question properties."""
        loader = DatasetLoader(dataset_file)
        questions = loader.load()

        geo_q = questions[0]
        assert geo_q.id == "geo_001"
        assert geo_q.question == "What is the capital of France?"
        assert geo_q.category == "geography"
        assert geo_q.difficulty == "easy"
        assert geo_q.expected_behavior["tools"] == ["wikipedia"]
        assert geo_q.ground_truth["answer"] == "Paris"
        assert geo_q.evaluation["correctness_threshold"] == 0.85

    def test_filter_by_category(self, dataset_file):
        """Test filtering questions by category."""
        loader = DatasetLoader(dataset_file)
        loader.load()

        geo_questions = loader.filter_by_category("geography")
        assert len(geo_questions) == 1
        assert geo_questions[0].category == "geography"

        hist_questions = loader.filter_by_category("history")
        assert len(hist_questions) == 1
        assert hist_questions[0].category == "history"

    def test_filter_by_category_no_match(self, dataset_file):
        """Test filtering with no matching category."""
        loader = DatasetLoader(dataset_file)
        loader.load()

        questions = loader.filter_by_category("nonexistent")
        assert len(questions) == 0

    def test_filter_by_difficulty(self, dataset_file):
        """Test filtering questions by difficulty."""
        loader = DatasetLoader(dataset_file)
        loader.load()

        easy_questions = loader.filter_by_difficulty("easy")
        assert len(easy_questions) == 2

        medium_questions = loader.filter_by_difficulty("medium")
        assert len(medium_questions) == 1

    def test_filter_by_difficulty_no_match(self, dataset_file):
        """Test filtering with no matching difficulty."""
        loader = DatasetLoader(dataset_file)
        loader.load()

        questions = loader.filter_by_difficulty("hard")
        assert len(questions) == 0

    def test_get_question_by_id(self, dataset_file):
        """Test getting question by ID."""
        loader = DatasetLoader(dataset_file)
        loader.load()

        question = loader.get_question_by_id("geo_001")
        assert question is not None
        assert question.question == "What is the capital of France?"

    def test_get_question_by_id_not_found(self, dataset_file):
        """Test getting non-existent question."""
        loader = DatasetLoader(dataset_file)
        loader.load()

        question = loader.get_question_by_id("nonexistent")
        assert question is None

    def test_get_categories(self, dataset_file):
        """Test getting all categories."""
        loader = DatasetLoader(dataset_file)
        loader.load()

        categories = loader.get_categories()
        assert set(categories) == {"geography", "history", "science"}

    def test_get_statistics(self, dataset_file):
        """Test getting dataset statistics."""
        loader = DatasetLoader(dataset_file)
        loader.load()

        stats = loader.get_statistics()

        assert stats["total_questions"] == 3
        assert stats["categories"]["geography"] == 1
        assert stats["categories"]["history"] == 1
        assert stats["categories"]["science"] == 1
        assert stats["difficulties"]["easy"] == 2
        assert stats["difficulties"]["medium"] == 1
        assert "wikipedia" in stats["tools_required"]

    def test_get_statistics_tools_count(self, dataset_file):
        """Test tool requirement counting."""
        loader = DatasetLoader(dataset_file)
        loader.load()

        stats = loader.get_statistics()

        # wikipedia is in all 3 questions
        assert stats["tools_required"]["wikipedia"] == 3
        # calculator only in 1 question
        assert stats["tools_required"]["calculator"] == 1
        # web_search in 1 question
        assert stats["tools_required"]["web_search"] == 1

    def test_print_statistics(self, dataset_file, capsys):
        """Test printing statistics to console."""
        loader = DatasetLoader(dataset_file)
        loader.load()
        loader.print_statistics()

        captured = capsys.readouterr()
        assert "Dataset Statistics" in captured.out
        assert "Total Questions: 3" in captured.out
        assert "geography" in captured.out
        assert "wikipedia" in captured.out


class TestLoadDatasetFunction:
    """Tests for load_dataset convenience function."""

    @pytest.fixture
    def dataset_file(self):
        """Create a temporary dataset file."""
        data = {
            "metadata": {},
            "questions": [
                {
                    "id": "test_001",
                    "question": "Test question?",
                    "category": "test",
                    "difficulty": "easy",
                    "expected_behavior": {"tools": []},
                    "ground_truth": {"answer": "test"},
                    "evaluation": {}
                }
            ]
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            return Path(f.name)

    def test_load_dataset_success(self, dataset_file):
        """Test convenience function."""
        questions = load_dataset(dataset_file)

        assert len(questions) == 1
        assert questions[0].id == "test_001"

    def test_load_dataset_file_not_found(self):
        """Test convenience function with invalid path."""
        with pytest.raises(FileNotFoundError):
            load_dataset(Path("/nonexistent/dataset.json"))


class TestDatasetLoaderEdgeCases:
    """Tests for edge cases in DatasetLoader."""

    def test_empty_dataset(self):
        """Test loading empty dataset."""
        data = {"metadata": {}, "questions": []}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            path = Path(f.name)

        loader = DatasetLoader(path)
        questions = loader.load()

        assert len(questions) == 0
        assert loader.get_categories() == []

    def test_missing_metadata(self):
        """Test loading dataset without metadata."""
        data = {
            "questions": [
                {
                    "id": "test",
                    "question": "Q?",
                    "category": "cat",
                    "difficulty": "easy",
                    "expected_behavior": {},
                    "ground_truth": {"answer": "A"},
                    "evaluation": {}
                }
            ]
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            path = Path(f.name)

        loader = DatasetLoader(path)
        questions = loader.load()

        assert len(questions) == 1
        assert loader.metadata == {}

    def test_unicode_content(self):
        """Test loading dataset with unicode content."""
        data = {
            "metadata": {},
            "questions": [
                {
                    "id": "unicode_001",
                    "question": "What is 日本語?",
                    "category": "language",
                    "difficulty": "medium",
                    "expected_behavior": {"tools": []},
                    "ground_truth": {"answer": "Japanese: 日本語"},
                    "evaluation": {}
                }
            ]
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
            path = Path(f.name)

        loader = DatasetLoader(path)
        questions = loader.load()

        assert "日本語" in questions[0].question
        assert "日本語" in questions[0].ground_truth["answer"]

    def test_reload_clears_previous(self):
        """Test that reloading clears previous data."""
        data1 = {
            "metadata": {"version": "1"},
            "questions": [
                {
                    "id": "q1",
                    "question": "Q1?",
                    "category": "cat1",
                    "difficulty": "easy",
                    "expected_behavior": {},
                    "ground_truth": {"answer": "A1"},
                    "evaluation": {}
                }
            ]
        }
        data2 = {
            "metadata": {"version": "2"},
            "questions": [
                {
                    "id": "q2",
                    "question": "Q2?",
                    "category": "cat2",
                    "difficulty": "hard",
                    "expected_behavior": {},
                    "ground_truth": {"answer": "A2"},
                    "evaluation": {}
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f1:
            json.dump(data1, f1)
            path1 = Path(f1.name)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f2:
            json.dump(data2, f2)
            path2 = Path(f2.name)

        loader = DatasetLoader(path1)
        loader.load()
        assert loader.metadata["version"] == "1"
        assert loader.questions[0].id == "q1"

        loader.load(path2)
        assert loader.metadata["version"] == "2"
        assert loader.questions[0].id == "q2"
