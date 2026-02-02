"""Configuration management for the B2B Account Intelligence Agent."""

import os
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from pathlib import Path
from enum import Enum


class ResearchMode(Enum):
    """Research mode determining tool availability."""
    NORMAL = "normal"  # 2-3 core tools
    DEEP = "deep"      # 5-10 tools


@dataclass
class LLMConfig:
    """LLM configuration."""
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.6
    max_tokens: int = 4096
    timeout_seconds: int = 60
    max_tool_calls: int = 15  # Max tool calls per query


@dataclass
class RateLimitConfig:
    """Rate limiting configuration per tool."""
    requests_per_second: float = 1.0
    burst_size: int = 5
    timeout_seconds: float = 30.0


@dataclass
class ToolConfig:
    """Tool-specific configurations."""
    # Web Search (DuckDuckGo)
    web_search_max_results: int = 10
    web_search_timeout: int = 10
    web_search_rate_limit: RateLimitConfig = field(
        default_factory=lambda: RateLimitConfig(requests_per_second=1.0)
    )

    # Wikipedia
    wikipedia_timeout: int = 5
    wikipedia_lang: str = "en"
    wikipedia_max_summary_length: int = 2000
    wikipedia_rate_limit: RateLimitConfig = field(
        default_factory=lambda: RateLimitConfig(requests_per_second=10.0)
    )

    # Calculator
    calculator_max_expression_length: int = 500
    calculator_timeout: float = 1.0
    calculator_allowed_functions: List[str] = field(
        default_factory=lambda: ["sqrt", "log", "log10", "sin", "cos", "tan", "abs", "round"]
    )

    # Tavily Web Search
    tavily_api_key: Optional[str] = field(default_factory=lambda: os.getenv("TAVILY_API_KEY"))
    tavily_max_results: int = 5
    tavily_timeout: int = 10

    # Yahoo Finance
    yahoo_finance_timeout: int = 10
    yahoo_finance_rate_limit: RateLimitConfig = field(
        default_factory=lambda: RateLimitConfig(requests_per_second=2.0)
    )

    # GitHub API
    github_token: Optional[str] = None
    github_timeout: int = 10
    github_max_repos: int = 10
    github_rate_limit: RateLimitConfig = field(
        default_factory=lambda: RateLimitConfig(requests_per_second=1.4)  # 83/min
    )

    # Website Scraper
    scraper_timeout: int = 15
    scraper_max_page_size: int = 1_000_000  # 1MB
    scraper_user_agent: str = "Mozilla/5.0 (compatible; ResearchBot/1.0)"
    scraper_rate_limit: RateLimitConfig = field(
        default_factory=lambda: RateLimitConfig(requests_per_second=1.0)
    )

    # SEC EDGAR (Extended - for future)
    sec_edgar_timeout: int = 15
    sec_edgar_rate_limit: RateLimitConfig = field(
        default_factory=lambda: RateLimitConfig(requests_per_second=10.0)
    )

    # HackerNews (Extended - for future)
    hackernews_timeout: int = 5
    hackernews_max_results: int = 20
    hackernews_rate_limit: RateLimitConfig = field(
        default_factory=lambda: RateLimitConfig(requests_per_second=10.0)
    )

    # Perplexity AI
    perplexity_api_key: Optional[str] = field(default_factory=lambda: os.getenv("PERPLEXITY_API_KEY"))
    perplexity_timeout: int = 60
    perplexity_default_model: str = "sonar"  # sonar, sonar-pro, sonar-reasoning
    perplexity_rate_limit: RateLimitConfig = field(
        default_factory=lambda: RateLimitConfig(requests_per_second=1.0)
    )

    # Gmail
    gmail_timeout: int = 10
    gmail_max_results: int = 10
    gmail_rate_limit: RateLimitConfig = field(
        default_factory=lambda: RateLimitConfig(requests_per_second=10.0)
    )

    # Google Calendar
    calendar_timeout: int = 10
    calendar_rate_limit: RateLimitConfig = field(
        default_factory=lambda: RateLimitConfig(requests_per_second=10.0)
    )


@dataclass
class ModeConfig:
    """Configuration for research modes."""
    # Tools available in Normal mode
    normal_mode_tools: List[str] = field(
        default_factory=lambda: ["web_search", "wikipedia", "calculator"]
    )

    # Tools available in Deep mode (all tools)
    deep_mode_tools: List[str] = field(
        default_factory=lambda: [
            "web_search", "wikipedia", "calculator",
            "perplexity_search",  # Deep research
            "yahoo_finance", "github_api", "website_scraper",
            "hackernews", "sec_edgar",
            "gmail", "google_calendar"
        ]
    )

    # Max tool calls per mode
    normal_mode_max_calls: int = 5
    deep_mode_max_calls: int = 15

    # Timeouts per mode
    normal_mode_timeout: int = 30
    deep_mode_timeout: int = 90


@dataclass
class MemoryConfig:
    """Memory configuration."""
    # Short-term memory
    max_messages: int = 20
    summarize_after: int = 15  # Summarize when this many messages

    # Session
    session_timeout_minutes: int = 60


@dataclass
class StorageConfig:
    """Storage configuration."""
    database_path: Optional[Path] = None
    cache_ttl_seconds: int = 900  # 15 minutes
    cache_max_size: int = 1000


@dataclass
class EvaluationConfig:
    """Evaluation harness configuration."""
    k_attempts: int = 10
    pass_k_values: List[int] = field(default_factory=lambda: [5, 10])
    tolerance_percent: float = 10.0  # 5-10% tolerance
    consensus_threshold: float = 0.5  # >50% for majority
    enable_tracing: bool = True
    save_traces: bool = True
    max_retries_per_tool: int = 2


@dataclass
class DashboardConfig:
    """Dashboard configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    api_rate_limit: int = 100  # requests per minute
    cors_origins: List[str] = field(default_factory=lambda: ["*"])


@dataclass
class Config:
    """Main application configuration."""
    # API Keys
    anthropic_api_key: Optional[str] = None

    # Component configs
    llm: LLMConfig = field(default_factory=LLMConfig)
    tools: ToolConfig = field(default_factory=ToolConfig)
    modes: ModeConfig = field(default_factory=ModeConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)

    # Paths
    project_root: Optional[Path] = None
    data_dir: Optional[Path] = None
    results_dir: Optional[Path] = None
    dataset_path: Optional[Path] = None

    def __post_init__(self):
        """Initialize paths and load from environment."""
        # Set up paths
        if self.project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        if self.data_dir is None:
            self.data_dir = self.project_root / "data"
        if self.results_dir is None:
            self.results_dir = self.data_dir / "results"
        if self.dataset_path is None:
            self.dataset_path = self.data_dir / "dataset.json"
        if self.storage.database_path is None:
            self.storage.database_path = self.data_dir / "agent.db"

        # Load from environment
        self._load_from_environment()

        # Create directories
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def _load_from_environment(self):
        """Load configuration from environment variables."""
        # API Keys
        self.anthropic_api_key = os.getenv(
            "ANTHROPIC_API_KEY",
            self.anthropic_api_key
        )
        self.tools.github_token = os.getenv(
            "GITHUB_TOKEN",
            self.tools.github_token
        )

        # Optional overrides
        if os.getenv("LLM_MODEL"):
            self.llm.model = os.getenv("LLM_MODEL")
        if os.getenv("LLM_TEMPERATURE"):
            self.llm.temperature = float(os.getenv("LLM_TEMPERATURE"))
        if os.getenv("DATABASE_PATH"):
            self.storage.database_path = Path(os.getenv("DATABASE_PATH"))
        if os.getenv("DASHBOARD_PORT"):
            self.dashboard.port = int(os.getenv("DASHBOARD_PORT"))

    def get_tools_for_mode(self, mode: ResearchMode) -> List[str]:
        """Get available tools for a research mode."""
        if mode == ResearchMode.NORMAL:
            return self.modes.normal_mode_tools
        return self.modes.deep_mode_tools

    def get_max_calls_for_mode(self, mode: ResearchMode) -> int:
        """Get max tool calls for a research mode."""
        if mode == ResearchMode.NORMAL:
            return self.modes.normal_mode_max_calls
        return self.modes.deep_mode_max_calls

    def get_timeout_for_mode(self, mode: ResearchMode) -> int:
        """Get timeout for a research mode."""
        if mode == ResearchMode.NORMAL:
            return self.modes.normal_mode_timeout
        return self.modes.deep_mode_timeout


def load_config() -> Config:
    """Load configuration from environment and defaults."""
    return Config()


# Singleton config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create singleton config instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reset_config():
    """Reset singleton config (useful for testing)."""
    global _config
    _config = None
