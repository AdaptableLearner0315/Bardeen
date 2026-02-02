"""Tests for Gmail and Google Calendar tools."""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path


class TestGmailToolDefinition:
    """Tests for Gmail tool definition and structure."""

    def test_gmail_import(self):
        """Test that Gmail tool can be imported."""
        from src.agent.tools.gmail import Gmail, GOOGLE_API_AVAILABLE
        assert Gmail is not None

    def test_gmail_initialization(self):
        """Test Gmail tool initialization."""
        from src.agent.tools.gmail import Gmail

        gmail = Gmail()
        assert gmail is not None
        assert gmail.timeout == 10

    def test_gmail_tool_definition(self):
        """Test Gmail tool definition format."""
        from src.agent.tools.gmail import Gmail

        gmail = Gmail()
        definition = gmail.get_tool_definition()

        assert definition["name"] == "gmail"
        assert "description" in definition
        assert "input_schema" in definition
        assert definition["input_schema"]["type"] == "object"
        assert "action" in definition["input_schema"]["properties"]

    def test_gmail_actions(self):
        """Test that Gmail supports required actions."""
        from src.agent.tools.gmail import Gmail

        gmail = Gmail()
        definition = gmail.get_tool_definition()

        actions = definition["input_schema"]["properties"]["action"]["enum"]
        assert "list" in actions
        assert "read" in actions
        assert "send" in actions
        assert "summarize" in actions


class TestGoogleCalendarToolDefinition:
    """Tests for Google Calendar tool definition and structure."""

    def test_calendar_import(self):
        """Test that Calendar tool can be imported."""
        from src.agent.tools.google_calendar import GoogleCalendar, GOOGLE_API_AVAILABLE
        assert GoogleCalendar is not None

    def test_calendar_initialization(self):
        """Test Calendar tool initialization."""
        from src.agent.tools.google_calendar import GoogleCalendar

        calendar = GoogleCalendar()
        assert calendar is not None
        assert calendar.timeout == 10

    def test_calendar_tool_definition(self):
        """Test Calendar tool definition format."""
        from src.agent.tools.google_calendar import GoogleCalendar

        calendar = GoogleCalendar()
        definition = calendar.get_tool_definition()

        assert definition["name"] == "google_calendar"
        assert "description" in definition
        assert "input_schema" in definition
        assert definition["input_schema"]["type"] == "object"
        assert "action" in definition["input_schema"]["properties"]

    def test_calendar_actions(self):
        """Test that Calendar supports required actions."""
        from src.agent.tools.google_calendar import GoogleCalendar

        calendar = GoogleCalendar()
        definition = calendar.get_tool_definition()

        actions = definition["input_schema"]["properties"]["action"]["enum"]
        assert "list" in actions
        assert "create" in actions
        assert "find_free" in actions


class TestGmailMockedOperations:
    """Tests for Gmail operations with mocked Google API."""

    @patch('src.agent.tools.gmail.GOOGLE_API_AVAILABLE', True)
    def test_gmail_not_authenticated_without_credentials(self):
        """Test Gmail reports not authenticated without credentials."""
        from src.agent.tools.gmail import Gmail

        gmail = Gmail(credentials_path="/nonexistent/path")
        assert gmail.is_authenticated() is False

    @patch('src.agent.tools.gmail.GOOGLE_API_AVAILABLE', True)
    @patch('src.agent.tools.gmail.build')
    @patch('src.agent.tools.gmail.InstalledAppFlow')
    def test_gmail_list_emails_mock(self, mock_flow, mock_build):
        """Test Gmail list emails with mocked API."""
        from src.agent.tools.gmail import Gmail

        # Setup mocks
        mock_service = MagicMock()
        mock_service.users().messages().list().execute.return_value = {
            'messages': [
                {'id': 'msg1'},
                {'id': 'msg2'}
            ]
        }
        mock_service.users().messages().get().execute.return_value = {
            'id': 'msg1',
            'snippet': 'Test email preview',
            'payload': {
                'headers': [
                    {'name': 'From', 'value': 'test@example.com'},
                    {'name': 'Subject', 'value': 'Test Subject'},
                    {'name': 'Date', 'value': '2024-01-01'}
                ]
            }
        }
        mock_build.return_value = mock_service

        # Mock credentials flow
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_flow.from_client_secrets_file().run_local_server.return_value = mock_creds

        gmail = Gmail()
        gmail._service = mock_service  # Inject mock service

        result = gmail.list_emails(max_results=5)

        assert result["success"] is True
        assert "emails" in result

    @patch('src.agent.tools.gmail.GOOGLE_API_AVAILABLE', False)
    def test_gmail_without_google_api(self):
        """Test Gmail gracefully handles missing Google API."""
        from src.agent.tools.gmail import Gmail

        gmail = Gmail()
        result = gmail(action="list")

        assert result["success"] is False
        assert "not available" in result["error"].lower()


class TestCalendarMockedOperations:
    """Tests for Calendar operations with mocked Google API."""

    @patch('src.agent.tools.google_calendar.GOOGLE_API_AVAILABLE', True)
    def test_calendar_not_authenticated_without_credentials(self):
        """Test Calendar reports not authenticated without credentials."""
        from src.agent.tools.google_calendar import GoogleCalendar

        calendar = GoogleCalendar(credentials_path="/nonexistent/path")
        assert calendar.is_authenticated() is False

    @patch('src.agent.tools.google_calendar.GOOGLE_API_AVAILABLE', True)
    @patch('src.agent.tools.google_calendar.build')
    def test_calendar_list_events_mock(self, mock_build):
        """Test Calendar list events with mocked API."""
        from src.agent.tools.google_calendar import GoogleCalendar

        # Setup mocks
        mock_service = MagicMock()
        mock_service.events().list().execute.return_value = {
            'items': [
                {
                    'id': 'event1',
                    'summary': 'Test Meeting',
                    'start': {'dateTime': '2024-01-01T10:00:00Z'},
                    'end': {'dateTime': '2024-01-01T11:00:00Z'}
                }
            ]
        }
        mock_build.return_value = mock_service

        calendar = GoogleCalendar()
        calendar._service = mock_service  # Inject mock service

        result = calendar.list_events(max_results=5)

        assert result["success"] is True
        assert "events" in result

    @patch('src.agent.tools.google_calendar.GOOGLE_API_AVAILABLE', False)
    def test_calendar_without_google_api(self):
        """Test Calendar gracefully handles missing Google API."""
        from src.agent.tools.google_calendar import GoogleCalendar

        calendar = GoogleCalendar()
        result = calendar(action="list")

        assert result["success"] is False
        assert "not available" in result["error"].lower()


class TestDateTimeParsing:
    """Tests for Calendar datetime parsing."""

    def test_parse_iso_datetime(self):
        """Test parsing ISO format datetime."""
        from src.agent.tools.google_calendar import GoogleCalendar

        calendar = GoogleCalendar()

        # Test ISO format
        result = calendar._parse_datetime("2024-06-15T14:30:00")
        assert result is not None
        assert result.hour == 14
        assert result.minute == 30

    def test_parse_simple_datetime(self):
        """Test parsing simple datetime format."""
        from src.agent.tools.google_calendar import GoogleCalendar

        calendar = GoogleCalendar()

        result = calendar._parse_datetime("2024-06-15 14:30")
        assert result is not None
        assert result.hour == 14

    def test_parse_natural_language_tomorrow(self):
        """Test parsing 'tomorrow' in datetime."""
        from src.agent.tools.google_calendar import GoogleCalendar

        calendar = GoogleCalendar()

        result = calendar._parse_natural_datetime("tomorrow at 2pm")
        assert result is not None
        assert result.date() == (datetime.now() + timedelta(days=1)).date()
        assert result.hour == 14

    def test_parse_natural_language_weekday(self):
        """Test parsing weekday in datetime."""
        from src.agent.tools.google_calendar import GoogleCalendar

        calendar = GoogleCalendar()

        result = calendar._parse_natural_datetime("next monday at 10am")
        assert result is not None
        assert result.weekday() == 0  # Monday
        assert result.hour == 10


class TestToolRegistration:
    """Tests for Gmail and Calendar registration in tool registry."""

    def test_gmail_registered_in_registry(self):
        """Test that Gmail tool is registered when available."""
        from src.agent.tool_registry import ToolRegistry
        from src.shared.config import load_config, reset_config

        reset_config()
        config = load_config()

        registry = ToolRegistry(config)

        # Gmail should be registered if Google API is available
        from src.agent.tools.gmail import GOOGLE_API_AVAILABLE
        if GOOGLE_API_AVAILABLE:
            assert "gmail" in registry.get_available_tools()

    def test_calendar_registered_in_registry(self):
        """Test that Calendar tool is registered when available."""
        from src.agent.tool_registry import ToolRegistry
        from src.shared.config import load_config, reset_config

        reset_config()
        config = load_config()

        registry = ToolRegistry(config)

        # Calendar should be registered if Google API is available
        from src.agent.tools.google_calendar import GOOGLE_API_AVAILABLE
        if GOOGLE_API_AVAILABLE:
            assert "google_calendar" in registry.get_available_tools()

    def test_tools_have_definitions(self):
        """Test that all tools have proper definitions."""
        from src.agent.tool_registry import ToolRegistry
        from src.shared.config import load_config, reset_config

        reset_config()
        config = load_config()

        registry = ToolRegistry(config)
        definitions = registry.get_tool_definitions()

        for definition in definitions:
            assert "name" in definition
            assert "description" in definition
            assert "input_schema" in definition


class TestGmailCallValidation:
    """Tests for Gmail call parameter validation."""

    def test_gmail_send_requires_params(self):
        """Test that send action requires to, subject, body."""
        from src.agent.tools.gmail import Gmail

        gmail = Gmail()
        result = gmail(action="send")

        assert result["success"] is False
        assert "required" in result["error"].lower()

    def test_gmail_read_requires_email_id(self):
        """Test that read action requires email_id."""
        from src.agent.tools.gmail import Gmail

        gmail = Gmail()
        result = gmail(action="read")

        assert result["success"] is False
        assert "email_id" in result["error"].lower()

    def test_gmail_unknown_action(self):
        """Test that unknown action returns error."""
        from src.agent.tools.gmail import Gmail

        gmail = Gmail()
        result = gmail(action="unknown_action")

        assert result["success"] is False
        assert "unknown" in result["error"].lower()


class TestCalendarCallValidation:
    """Tests for Calendar call parameter validation."""

    def test_calendar_create_requires_params(self):
        """Test that create action requires summary and start_time."""
        from src.agent.tools.google_calendar import GoogleCalendar

        calendar = GoogleCalendar()
        result = calendar(action="create")

        assert result["success"] is False
        assert "required" in result["error"].lower()

    def test_calendar_unknown_action(self):
        """Test that unknown action returns error."""
        from src.agent.tools.google_calendar import GoogleCalendar

        calendar = GoogleCalendar()
        result = calendar(action="unknown_action")

        assert result["success"] is False
        assert "unknown" in result["error"].lower()


class TestConfigSettings:
    """Tests for Gmail and Calendar config settings."""

    def test_config_has_gmail_settings(self):
        """Test that config includes Gmail settings."""
        from src.shared.config import ToolConfig

        config = ToolConfig()

        assert hasattr(config, 'gmail_timeout')
        assert hasattr(config, 'gmail_max_results')
        assert config.gmail_timeout == 10

    def test_config_has_calendar_settings(self):
        """Test that config includes Calendar settings."""
        from src.shared.config import ToolConfig

        config = ToolConfig()

        assert hasattr(config, 'calendar_timeout')
        assert config.calendar_timeout == 10

    def test_deep_mode_includes_gmail_calendar(self):
        """Test that deep mode tools include Gmail and Calendar."""
        from src.shared.config import ModeConfig

        config = ModeConfig()

        assert "gmail" in config.deep_mode_tools
        assert "google_calendar" in config.deep_mode_tools
