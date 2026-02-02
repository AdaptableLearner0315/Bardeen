"""Unit tests for shared/config.py."""

import os
import pytest
from pathlib import Path
from unittest.mock import patch

from src.shared.config import (
    Config,
    LLMConfig,
    ToolConfig,
    ModeConfig,
    MemoryConfig,
    StorageConfig,
    EvaluationConfig,
    DashboardConfig,
    RateLimitConfig,
    ResearchMode,
    load_config,
    get_config,
    reset_config,
)


class TestResearchMode:
    """Tests for ResearchMode enum."""

    def test_normal_mode_value(self):
        """Test NORMAL mode has correct value."""
        assert ResearchMode.NORMAL.value == "normal"

    def test_deep_mode_value(self):
        """Test DEEP mode has correct value."""
        assert ResearchMode.DEEP.value == "deep"

    def test_mode_from_string(self):
        """Test creating mode from string."""
        assert ResearchMode("normal") == ResearchMode.NORMAL
        assert ResearchMode("deep") == ResearchMode.DEEP

    def test_invalid_mode_raises(self):
        """Test invalid mode raises ValueError."""
        with pytest.raises(ValueError):
            ResearchMode("invalid")


class TestLLMConfig:
    """Tests for LLMConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = LLMConfig()
        assert config.provider == "anthropic"
        assert "claude-sonnet-4" in config.model
        assert config.temperature == 0.6
        assert config.max_tokens == 4096
        assert config.timeout_seconds == 60
        assert config.max_tool_calls == 15

    def test_custom_values(self):
        """Test custom configuration values."""
        config = LLMConfig(
            model="custom-model",
            temperature=0.8,
            max_tokens=2048
        )
        assert config.model == "custom-model"
        assert config.temperature == 0.8
        assert config.max_tokens == 2048


class TestRateLimitConfig:
    """Tests for RateLimitConfig."""

    def test_default_values(self):
        """Test default rate limit values."""
        config = RateLimitConfig()
        assert config.requests_per_second == 1.0
        assert config.burst_size == 5
        assert config.timeout_seconds == 30.0

    def test_custom_values(self):
        """Test custom rate limit values."""
        config = RateLimitConfig(
            requests_per_second=10.0,
            burst_size=20,
            timeout_seconds=60.0
        )
        assert config.requests_per_second == 10.0
        assert config.burst_size == 20
        assert config.timeout_seconds == 60.0


class TestToolConfig:
    """Tests for ToolConfig."""

    def test_default_values(self):
        """Test default tool configuration."""
        config = ToolConfig()
        assert config.web_search_max_results == 10
        assert config.wikipedia_lang == "en"
        assert config.calculator_max_expression_length == 500

    def test_rate_limits_initialized(self):
        """Test rate limits are initialized for all tools."""
        config = ToolConfig()
        assert config.web_search_rate_limit.requests_per_second == 1.0
        assert config.wikipedia_rate_limit.requests_per_second == 10.0
        assert config.yahoo_finance_rate_limit.requests_per_second == 2.0
        assert config.github_rate_limit.requests_per_second == 1.4

    def test_allowed_calculator_functions(self):
        """Test calculator allowed functions are set."""
        config = ToolConfig()
        assert "sqrt" in config.calculator_allowed_functions
        assert "log" in config.calculator_allowed_functions
        assert "sin" in config.calculator_allowed_functions


class TestModeConfig:
    """Tests for ModeConfig."""

    def test_normal_mode_tools(self):
        """Test Normal mode has correct tools."""
        config = ModeConfig()
        assert "web_search" in config.normal_mode_tools
        assert "wikipedia" in config.normal_mode_tools
        assert "calculator" in config.normal_mode_tools
        assert len(config.normal_mode_tools) == 3

    def test_deep_mode_tools(self):
        """Test Deep mode has more tools."""
        config = ModeConfig()
        assert len(config.deep_mode_tools) > len(config.normal_mode_tools)
        assert "yahoo_finance" in config.deep_mode_tools
        assert "github_api" in config.deep_mode_tools
        assert "website_scraper" in config.deep_mode_tools

    def test_max_calls_per_mode(self):
        """Test max tool calls per mode."""
        config = ModeConfig()
        assert config.normal_mode_max_calls == 5
        assert config.deep_mode_max_calls == 15

    def test_timeouts_per_mode(self):
        """Test timeouts per mode."""
        config = ModeConfig()
        assert config.normal_mode_timeout == 30
        assert config.deep_mode_timeout == 90


class TestMemoryConfig:
    """Tests for MemoryConfig."""

    def test_default_values(self):
        """Test default memory configuration."""
        config = MemoryConfig()
        assert config.max_messages == 20
        assert config.summarize_after == 15
        assert config.session_timeout_minutes == 60


class TestStorageConfig:
    """Tests for StorageConfig."""

    def test_default_values(self):
        """Test default storage configuration."""
        config = StorageConfig()
        assert config.cache_ttl_seconds == 900  # 15 minutes
        assert config.cache_max_size == 1000


class TestEvaluationConfig:
    """Tests for EvaluationConfig."""

    def test_default_values(self):
        """Test default evaluation configuration."""
        config = EvaluationConfig()
        assert config.k_attempts == 10
        assert config.pass_k_values == [5, 10]
        assert config.tolerance_percent == 10.0
        assert config.consensus_threshold == 0.5
        assert config.enable_tracing is True
        assert config.max_retries_per_tool == 2


class TestDashboardConfig:
    """Tests for DashboardConfig."""

    def test_default_values(self):
        """Test default dashboard configuration."""
        config = DashboardConfig()
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.api_rate_limit == 100
        assert "*" in config.cors_origins


class TestConfig:
    """Tests for main Config class."""

    def test_default_initialization(self):
        """Test config initializes with defaults."""
        # Reset singleton first
        reset_config()

        config = Config()
        assert config.llm is not None
        assert config.tools is not None
        assert config.modes is not None
        assert config.memory is not None
        assert config.storage is not None
        assert config.evaluation is not None
        assert config.dashboard is not None

    def test_paths_initialized(self):
        """Test paths are initialized."""
        reset_config()
        config = Config()
        assert config.project_root is not None
        assert config.data_dir is not None
        assert config.results_dir is not None
        assert config.dataset_path is not None
        assert config.storage.database_path is not None

    def test_results_dir_created(self):
        """Test results directory is created."""
        reset_config()
        config = Config()
        assert config.results_dir.exists()

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    def test_api_key_from_environment(self):
        """Test API key loaded from environment."""
        reset_config()
        config = Config()
        assert config.anthropic_api_key == "test-key"

    @patch.dict(os.environ, {"GITHUB_TOKEN": "gh-test-token"})
    def test_github_token_from_environment(self):
        """Test GitHub token loaded from environment."""
        reset_config()
        config = Config()
        assert config.tools.github_token == "gh-test-token"

    @patch.dict(os.environ, {"LLM_TEMPERATURE": "0.9"})
    def test_llm_temperature_override(self):
        """Test LLM temperature can be overridden."""
        reset_config()
        config = Config()
        assert config.llm.temperature == 0.9

    @patch.dict(os.environ, {"DASHBOARD_PORT": "9000"})
    def test_dashboard_port_override(self):
        """Test dashboard port can be overridden."""
        reset_config()
        config = Config()
        assert config.dashboard.port == 9000

    def test_get_tools_for_normal_mode(self):
        """Test getting tools for Normal mode."""
        reset_config()
        config = Config()
        tools = config.get_tools_for_mode(ResearchMode.NORMAL)
        assert len(tools) == 3
        assert "web_search" in tools

    def test_get_tools_for_deep_mode(self):
        """Test getting tools for Deep mode."""
        reset_config()
        config = Config()
        tools = config.get_tools_for_mode(ResearchMode.DEEP)
        assert len(tools) > 3
        assert "yahoo_finance" in tools

    def test_get_max_calls_for_mode(self):
        """Test getting max calls for mode."""
        reset_config()
        config = Config()
        assert config.get_max_calls_for_mode(ResearchMode.NORMAL) == 5
        assert config.get_max_calls_for_mode(ResearchMode.DEEP) == 15

    def test_get_timeout_for_mode(self):
        """Test getting timeout for mode."""
        reset_config()
        config = Config()
        assert config.get_timeout_for_mode(ResearchMode.NORMAL) == 30
        assert config.get_timeout_for_mode(ResearchMode.DEEP) == 90


class TestConfigSingleton:
    """Tests for config singleton pattern."""

    def test_get_config_returns_same_instance(self):
        """Test get_config returns singleton."""
        reset_config()
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_reset_config_clears_singleton(self):
        """Test reset_config clears the singleton."""
        reset_config()
        config1 = get_config()
        reset_config()
        config2 = get_config()
        assert config1 is not config2

    def test_load_config_returns_new_instance(self):
        """Test load_config always returns new instance."""
        config1 = load_config()
        config2 = load_config()
        assert config1 is not config2


class TestConfigEdgeCases:
    """Edge case tests for configuration."""

    def test_empty_api_key_is_none(self):
        """Test empty API key is handled."""
        reset_config()
        config = Config()
        # API key should be None if not set
        assert config.anthropic_api_key is None or config.anthropic_api_key == os.getenv("ANTHROPIC_API_KEY")

    def test_invalid_temperature_type(self):
        """Test invalid temperature type from env."""
        with patch.dict(os.environ, {"LLM_TEMPERATURE": "invalid"}):
            reset_config()
            with pytest.raises(ValueError):
                Config()

    def test_invalid_port_type(self):
        """Test invalid port type from env."""
        with patch.dict(os.environ, {"DASHBOARD_PORT": "invalid"}):
            reset_config()
            with pytest.raises(ValueError):
                Config()

    def test_all_modes_have_core_tools(self):
        """Test all modes include core tools."""
        reset_config()
        config = Config()
        normal_tools = set(config.get_tools_for_mode(ResearchMode.NORMAL))
        deep_tools = set(config.get_tools_for_mode(ResearchMode.DEEP))

        # Normal tools should be subset of deep tools
        assert normal_tools.issubset(deep_tools)
