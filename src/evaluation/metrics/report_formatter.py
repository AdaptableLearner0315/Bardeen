"""Utility for consistent report formatting.

This module provides standardized report formatting to eliminate
duplication across evaluation and metrics modules.

Key Classes:
    ReportFormatter: Static methods for report formatting

Usage:
    from src.evaluation.metrics.report_formatter import ReportFormatter

    content = ReportFormatter.section("Metrics", "precision: 0.85\\nrecall: 0.90")
    print(content)

Notes:
    - All methods are static (no instance needed)
    - Supports color-coded values for terminal output
    - Consistent section headers and dividers
"""

from typing import Dict, List, Any, Optional


class ReportFormatter:
    """Utility for consistent report formatting.

    Provides:
    - Section headers with dividers
    - Metric tables
    - Summary statistics
    - Color-coded values (for terminal output)

    All methods are static and can be called without instantiation.

    Class Attributes:
        HEADER_WIDTH: Width of section headers (default: 60)
        DIVIDER_WIDTH: Width of subsection dividers (default: 40)
    """

    HEADER_WIDTH = 60
    DIVIDER_WIDTH = 40

    @staticmethod
    def section(title: str, content: str) -> str:
        """Format a report section with header.

        Creates a section with top and bottom dividers:
        ============================================================
        Title
        ============================================================
        Content

        Args:
            title: Section title text
            content: Section content (can be multi-line)

        Returns:
            Formatted section string

        Examples:
            >>> print(ReportFormatter.section("Metrics", "precision: 0.85"))
            ============================================================
            Metrics
            ============================================================
            precision: 0.85
            <BLANKLINE>
        """
        header = "=" * ReportFormatter.HEADER_WIDTH
        return f"{header}\n{title}\n{header}\n{content}\n"

    @staticmethod
    def subsection(title: str, content: str) -> str:
        """Format a report subsection with divider.

        Creates a subsection with a divider:
        ----------------------------------------
        Title
        ----------------------------------------
        Content

        Args:
            title: Subsection title text
            content: Subsection content (can be multi-line)

        Returns:
            Formatted subsection string

        Examples:
            >>> print(ReportFormatter.subsection("Details", "value: 100"))
            ----------------------------------------
            Details
            ----------------------------------------
            value: 100
            <BLANKLINE>
        """
        divider = "-" * ReportFormatter.DIVIDER_WIDTH
        return f"{divider}\n{title}\n{divider}\n{content}\n"

    @staticmethod
    def metric_table(
        metrics: Dict[str, Any],
        format_spec: str = ".2f",
        indent: int = 2
    ) -> str:
        """Format metrics as aligned key-value table.

        Creates an aligned table:
          precision: 0.85
          recall   : 0.90
          f1_score : 0.87

        Args:
            metrics: Dictionary of metric names to values
            format_spec: Format specification for float values (default: ".2f")
            indent: Number of spaces to indent each line (default: 2)

        Returns:
            Formatted table string

        Examples:
            >>> metrics = {"precision": 0.85, "recall": 0.90}
            >>> print(ReportFormatter.metric_table(metrics))
              precision: 0.85
              recall   : 0.90

        Note:
            Keys are left-aligned, values are formatted according to type
        """
        if not metrics:
            return f"{' ' * indent}No metrics available"

        lines = []
        max_key_len = max(len(str(k)) for k in metrics.keys())

        for key, value in metrics.items():
            key_str = str(key).ljust(max_key_len)

            if isinstance(value, float):
                value_str = f"{value:{format_spec}}"
            elif isinstance(value, (int, bool)):
                value_str = str(value)
            elif isinstance(value, (list, dict)):
                value_str = str(value)
            else:
                value_str = str(value) if value is not None else "N/A"

            lines.append(f"{' ' * indent}{key_str}: {value_str}")

        return "\n".join(lines)

    @staticmethod
    def color_value(
        value: float,
        threshold_good: float,
        threshold_warning: float,
        format_spec: str = ".2f"
    ) -> str:
        """Color-code a value based on thresholds (for terminal).

        Uses ANSI color codes:
        - Green: value >= threshold_good
        - Yellow: threshold_warning <= value < threshold_good
        - Red: value < threshold_warning

        Args:
            value: Numeric value to format
            threshold_good: Threshold for green (good) values
            threshold_warning: Threshold for yellow (warning) values
            format_spec: Format specification for the value (default: ".2f")

        Returns:
            Formatted string with ANSI color codes

        Examples:
            >>> ReportFormatter.color_value(0.95, 0.90, 0.70)
            '\\x1b[92m0.95\\x1b[0m'  # Green

            >>> ReportFormatter.color_value(0.75, 0.90, 0.70)
            '\\x1b[93m0.75\\x1b[0m'  # Yellow

            >>> ReportFormatter.color_value(0.60, 0.90, 0.70)
            '\\x1b[91m0.60\\x1b[0m'  # Red

        Note:
            Color codes only work in terminals that support ANSI colors
        """
        if value >= threshold_good:
            return f"\033[92m{value:{format_spec}}\033[0m"  # Green
        elif value >= threshold_warning:
            return f"\033[93m{value:{format_spec}}\033[0m"  # Yellow
        else:
            return f"\033[91m{value:{format_spec}}\033[0m"  # Red

    @staticmethod
    def format_percentage(value: float, decimals: int = 1) -> str:
        """Format a value as a percentage string.

        Args:
            value: Value between 0.0 and 1.0
            decimals: Number of decimal places (default: 1)

        Returns:
            Formatted percentage string (e.g., "85.5%")

        Examples:
            >>> ReportFormatter.format_percentage(0.855)
            '85.5%'

            >>> ReportFormatter.format_percentage(0.855, decimals=2)
            '85.50%'
        """
        return f"{value * 100:.{decimals}f}%"

    @staticmethod
    def format_list(
        items: List[Any],
        bullet: str = "  - ",
        max_items: Optional[int] = None
    ) -> str:
        """Format a list of items with bullets.

        Args:
            items: List of items to format
            bullet: Bullet character/string (default: "  - ")
            max_items: Maximum number of items to display (None = all)

        Returns:
            Formatted bulleted list string

        Examples:
            >>> items = ["item1", "item2", "item3"]
            >>> print(ReportFormatter.format_list(items))
              - item1
              - item2
              - item3

            >>> print(ReportFormatter.format_list(items, max_items=2))
              - item1
              - item2
              ... (1 more)

        Note:
            If max_items is exceeded, shows "... (N more)" message
        """
        if not items:
            return f"{bullet}No items"

        display_items = items[:max_items] if max_items else items
        lines = [f"{bullet}{item}" for item in display_items]

        if max_items and len(items) > max_items:
            remaining = len(items) - max_items
            lines.append(f"  ... ({remaining} more)")

        return "\n".join(lines)

    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in seconds to human-readable string.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted duration string (e.g., "1h 23m 45s")

        Examples:
            >>> ReportFormatter.format_duration(45.5)
            '45.5s'

            >>> ReportFormatter.format_duration(125)
            '2m 5s'

            >>> ReportFormatter.format_duration(3665)
            '1h 1m 5s'
        """
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours}h {minutes}m {secs}s"

    @staticmethod
    def format_size(bytes_count: int) -> str:
        """Format byte count to human-readable string.

        Args:
            bytes_count: Number of bytes

        Returns:
            Formatted size string (e.g., "1.5 MB")

        Examples:
            >>> ReportFormatter.format_size(1024)
            '1.0 KB'

            >>> ReportFormatter.format_size(1536000)
            '1.5 MB'

            >>> ReportFormatter.format_size(500)
            '500 B'
        """
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = float(bytes_count)
        unit_index = 0

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.1f} {units[unit_index]}"
