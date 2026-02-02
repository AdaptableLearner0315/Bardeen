"""Dataset loader and manager."""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..shared.models import DatasetQuestion


class DatasetLoader:
    """Loads and manages evaluation datasets."""

    def __init__(self, dataset_path: Optional[Path] = None):
        """
        Initialize dataset loader.

        Args:
            dataset_path: Path to dataset JSON file
        """
        self.dataset_path = dataset_path
        self.metadata: Dict[str, Any] = {}
        self.questions: List[DatasetQuestion] = []

    def load(self, dataset_path: Optional[Path] = None) -> List[DatasetQuestion]:
        """
        Load dataset from JSON file.

        Args:
            dataset_path: Optional path override

        Returns:
            List of DatasetQuestion objects
        """
        path = dataset_path or self.dataset_path

        if not path or not Path(path).exists():
            raise FileNotFoundError(f"Dataset file not found: {path}")

        with open(path, 'r') as f:
            data = json.load(f)

        # Store metadata
        self.metadata = data.get("metadata", {})

        # Load questions
        questions = []
        for q_data in data.get("questions", []):
            question = DatasetQuestion(
                id=q_data["id"],
                question=q_data["question"],
                category=q_data["category"],
                difficulty=q_data["difficulty"],
                expected_behavior=q_data["expected_behavior"],
                ground_truth=q_data["ground_truth"],
                evaluation=q_data["evaluation"]
            )
            questions.append(question)

        self.questions = questions
        return questions

    def filter_by_category(self, category: str) -> List[DatasetQuestion]:
        """
        Filter questions by category.

        Args:
            category: Category name (e.g., "geography", "history")

        Returns:
            Filtered list of questions
        """
        return [q for q in self.questions if q.category == category]

    def filter_by_difficulty(self, difficulty: str) -> List[DatasetQuestion]:
        """
        Filter questions by difficulty.

        Args:
            difficulty: Difficulty level (e.g., "easy", "medium", "hard")

        Returns:
            Filtered list of questions
        """
        return [q for q in self.questions if q.difficulty == difficulty]

    def get_question_by_id(self, question_id: str) -> Optional[DatasetQuestion]:
        """
        Get a specific question by ID.

        Args:
            question_id: Question ID

        Returns:
            DatasetQuestion or None if not found
        """
        for q in self.questions:
            if q.id == question_id:
                return q
        return None

    def get_categories(self) -> List[str]:
        """Get list of all categories in the dataset."""
        return list(set(q.category for q in self.questions))

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get dataset statistics.

        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_questions": len(self.questions),
            "categories": {},
            "difficulties": {},
            "tools_required": {}
        }

        for q in self.questions:
            # Count by category
            stats["categories"][q.category] = stats["categories"].get(q.category, 0) + 1

            # Count by difficulty
            stats["difficulties"][q.difficulty] = stats["difficulties"].get(q.difficulty, 0) + 1

            # Count required tools
            for tool in q.expected_behavior.get("tools", []):
                stats["tools_required"][tool] = stats["tools_required"].get(tool, 0) + 1

        return stats

    def print_statistics(self):
        """Print dataset statistics to console."""
        stats = self.get_statistics()

        print("=" * 80)
        print("Dataset Statistics")
        print("=" * 80)
        print(f"Total Questions: {stats['total_questions']}")
        print()

        print("By Category:")
        for category, count in sorted(stats['categories'].items()):
            print(f"  - {category}: {count}")
        print()

        print("By Difficulty:")
        for difficulty, count in sorted(stats['difficulties'].items()):
            print(f"  - {difficulty}: {count}")
        print()

        print("Tools Required:")
        for tool, count in sorted(stats['tools_required'].items()):
            print(f"  - {tool}: {count} questions")
        print("=" * 80)


def load_dataset(path: Optional[Path] = None) -> List[DatasetQuestion]:
    """
    Convenience function to load a dataset.

    Args:
        path: Path to dataset JSON file

    Returns:
        List of DatasetQuestion objects
    """
    loader = DatasetLoader(path)
    return loader.load()
