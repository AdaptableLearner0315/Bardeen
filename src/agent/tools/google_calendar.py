"""Google Calendar tool for scheduling and viewing events."""

import os
import pickle
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timedelta
import re

# Google API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False


# Calendar API scopes
CALENDAR_SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
]


class GoogleCalendar:
    """
    Google Calendar tool for scheduling and viewing events.

    Supports:
    - Creating calendar events
    - Listing upcoming events
    - Finding free time slots
    - Checking for conflicts
    """

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        token_path: Optional[str] = None,
        timeout: int = 10
    ):
        """
        Initialize Google Calendar tool.

        Args:
            credentials_path: Path to Google OAuth credentials.json
            token_path: Path to store/load OAuth token
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self._service = None
        self._authenticated = False

        # Set default paths
        project_root = Path(__file__).parent.parent.parent.parent
        self.credentials_path = credentials_path or os.getenv(
            "GOOGLE_CREDENTIALS_PATH",
            str(project_root / "credentials.json")
        )
        self.token_path = token_path or os.getenv(
            "GOOGLE_CALENDAR_TOKEN_PATH",
            str(project_root / "data" / "calendar_token.pickle")
        )

        # Ensure data directory exists
        Path(self.token_path).parent.mkdir(parents=True, exist_ok=True)

    def _get_service(self):
        """Get or create Calendar API service."""
        if self._service is not None:
            return self._service

        if not GOOGLE_API_AVAILABLE:
            raise RuntimeError(
                "Google API libraries not installed. "
                "Run: pip install google-api-python-client google-auth-oauthlib"
            )

        creds = None

        # Load existing token if available
        if os.path.exists(self.token_path):
            try:
                with open(self.token_path, 'rb') as token:
                    creds = pickle.load(token)
            except Exception:
                creds = None

        # Refresh or get new credentials
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds or not creds.valid:
            if not os.path.exists(self.credentials_path):
                raise RuntimeError(
                    f"Google credentials file not found at {self.credentials_path}. "
                    "Please download OAuth credentials from Google Cloud Console."
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path, CALENDAR_SCOPES
            )
            creds = flow.run_local_server(port=0)

            # Save credentials for next run
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)

        self._service = build('calendar', 'v3', credentials=creds)
        self._authenticated = True
        return self._service

    def is_authenticated(self) -> bool:
        """Check if Calendar is authenticated."""
        if self._authenticated:
            return True

        if os.path.exists(self.token_path):
            try:
                with open(self.token_path, 'rb') as token:
                    creds = pickle.load(token)
                    return creds and creds.valid
            except Exception:
                pass
        return False

    def list_events(
        self,
        max_results: int = 10,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        List upcoming calendar events.

        Args:
            max_results: Maximum number of events to return
            time_min: Start time filter (default: now)
            time_max: End time filter (default: 7 days from now)

        Returns:
            Dictionary with event list or error
        """
        try:
            service = self._get_service()

            # Set time bounds
            if time_min is None:
                time_min = datetime.utcnow()
            if time_max is None:
                time_max = time_min + timedelta(days=7)

            time_min_str = time_min.isoformat() + 'Z'
            time_max_str = time_max.isoformat() + 'Z'

            # Fetch events
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min_str,
                timeMax=time_max_str,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            event_list = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))

                event_list.append({
                    "id": event.get('id'),
                    "summary": event.get('summary', 'No Title'),
                    "start": start,
                    "end": end,
                    "location": event.get('location', ''),
                    "attendees": [a.get('email') for a in event.get('attendees', [])],
                    "status": event.get('status', 'confirmed')
                })

            return {
                "success": True,
                "events": event_list,
                "count": len(event_list),
                "time_range": {
                    "from": time_min_str,
                    "to": time_max_str
                }
            }

        except HttpError as e:
            return {
                "success": False,
                "error": f"Calendar API error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error listing events: {str(e)}"
            }

    def create_event(
        self,
        summary: str,
        start_time: str,
        end_time: Optional[str] = None,
        duration_minutes: int = 30,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a calendar event.

        Args:
            summary: Event title
            start_time: Start time (ISO format or natural language like "next Monday 2pm")
            end_time: End time (optional, uses duration if not provided)
            duration_minutes: Duration in minutes (default: 30)
            description: Event description
            location: Event location
            attendees: List of attendee email addresses

        Returns:
            Dictionary with created event or error
        """
        try:
            service = self._get_service()

            # Parse start time
            start_dt = self._parse_datetime(start_time)
            if not start_dt:
                return {
                    "success": False,
                    "error": f"Could not parse start time: {start_time}"
                }

            # Check for past date
            if start_dt < datetime.now():
                return {
                    "success": False,
                    "error": "Cannot schedule events in the past"
                }

            # Calculate end time
            if end_time:
                end_dt = self._parse_datetime(end_time)
                if not end_dt:
                    return {
                        "success": False,
                        "error": f"Could not parse end time: {end_time}"
                    }
            else:
                end_dt = start_dt + timedelta(minutes=duration_minutes)

            # Build event body
            event = {
                'summary': summary,
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': 'UTC',
                },
            }

            if description:
                event['description'] = description
            if location:
                event['location'] = location
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]

            # Check for conflicts
            conflicts = self._check_conflicts(start_dt, end_dt)
            if conflicts:
                return {
                    "success": False,
                    "error": f"Time slot conflicts with existing event: {conflicts[0].get('summary')}",
                    "conflicts": conflicts
                }

            # Create event
            result = service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all' if attendees else 'none'
            ).execute()

            return {
                "success": True,
                "event_id": result.get('id'),
                "summary": summary,
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "link": result.get('htmlLink'),
                "attendees": attendees or []
            }

        except HttpError as e:
            return {
                "success": False,
                "error": f"Calendar API error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error creating event: {str(e)}"
            }

    def _parse_datetime(self, time_str: str) -> Optional[datetime]:
        """Parse datetime from string (ISO format or natural language)."""
        # Try ISO format first
        try:
            return datetime.fromisoformat(time_str.replace('Z', '+00:00').replace('+00:00', ''))
        except ValueError:
            pass

        # Try common formats
        formats = [
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%m/%d/%Y %H:%M",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue

        # Try natural language parsing
        return self._parse_natural_datetime(time_str)

    def _parse_natural_datetime(self, time_str: str) -> Optional[datetime]:
        """Parse natural language datetime like 'next Monday 2pm'."""
        time_str = time_str.lower().strip()
        now = datetime.now()

        # Day mapping
        day_mapping = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }

        # Parse "next <day> at <time>"
        for day_name, day_num in day_mapping.items():
            if day_name in time_str:
                days_ahead = day_num - now.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                if 'next' in time_str:
                    days_ahead += 7 if days_ahead <= 7 else 0

                target_date = now + timedelta(days=days_ahead)

                # Parse time
                hour = 9  # Default to 9am
                time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', time_str)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2) or 0)
                    period = time_match.group(3)

                    if period == 'pm' and hour < 12:
                        hour += 12
                    elif period == 'am' and hour == 12:
                        hour = 0
                else:
                    minute = 0

                return target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Parse "tomorrow at <time>"
        if 'tomorrow' in time_str:
            target_date = now + timedelta(days=1)
            hour = 9
            time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', time_str)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2) or 0)
                period = time_match.group(3)
                if period == 'pm' and hour < 12:
                    hour += 12
            else:
                minute = 0
            return target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

        return None

    def _check_conflicts(
        self,
        start_dt: datetime,
        end_dt: datetime
    ) -> List[Dict]:
        """Check for conflicting events."""
        try:
            service = self._get_service()

            events_result = service.events().list(
                calendarId='primary',
                timeMin=start_dt.isoformat() + 'Z',
                timeMax=end_dt.isoformat() + 'Z',
                singleEvents=True
            ).execute()

            conflicts = []
            for event in events_result.get('items', []):
                conflicts.append({
                    "id": event.get('id'),
                    "summary": event.get('summary', 'No Title'),
                    "start": event['start'].get('dateTime', event['start'].get('date')),
                    "end": event['end'].get('dateTime', event['end'].get('date'))
                })

            return conflicts
        except Exception:
            return []

    def find_free_slots(
        self,
        duration_minutes: int = 60,
        days_ahead: int = 7,
        working_hours_start: int = 9,
        working_hours_end: int = 17
    ) -> Dict[str, Any]:
        """
        Find free time slots.

        Args:
            duration_minutes: Required slot duration
            days_ahead: Number of days to search
            working_hours_start: Start of working hours (24h format)
            working_hours_end: End of working hours (24h format)

        Returns:
            Dictionary with free slots or error
        """
        try:
            service = self._get_service()

            now = datetime.now()
            end_search = now + timedelta(days=days_ahead)

            # Get all events in range
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now.isoformat() + 'Z',
                timeMax=end_search.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            # Find free slots
            free_slots = []
            current_date = now.date()

            while current_date <= end_search.date() and len(free_slots) < 10:
                # Check each hour during working hours
                for hour in range(working_hours_start, working_hours_end):
                    slot_start = datetime.combine(current_date, datetime.min.time().replace(hour=hour))
                    slot_end = slot_start + timedelta(minutes=duration_minutes)

                    if slot_start < now:
                        continue

                    # Check if slot conflicts with any event
                    is_free = True
                    for event in events:
                        event_start = event['start'].get('dateTime', event['start'].get('date'))
                        event_end = event['end'].get('dateTime', event['end'].get('date'))

                        try:
                            ev_start = datetime.fromisoformat(event_start.replace('Z', ''))
                            ev_end = datetime.fromisoformat(event_end.replace('Z', ''))

                            # Check overlap
                            if not (slot_end <= ev_start or slot_start >= ev_end):
                                is_free = False
                                break
                        except Exception:
                            continue

                    if is_free:
                        free_slots.append({
                            "start": slot_start.isoformat(),
                            "end": slot_end.isoformat(),
                            "date": current_date.strftime("%A, %B %d"),
                            "time": slot_start.strftime("%I:%M %p")
                        })

                current_date += timedelta(days=1)

            return {
                "success": True,
                "free_slots": free_slots[:10],
                "duration_minutes": duration_minutes,
                "search_range": f"Next {days_ahead} days"
            }

        except HttpError as e:
            return {
                "success": False,
                "error": f"Calendar API error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error finding free slots: {str(e)}"
            }

    def get_tool_definition(self) -> Dict[str, Any]:
        """Get tool definition for LLM tool calling."""
        return {
            "name": "google_calendar",
            "description": (
                "Access Google Calendar to schedule meetings, view upcoming events, "
                "and find free time slots. Use this to schedule meetings, check availability, "
                "or see what's coming up on the calendar. Requires Google OAuth authentication."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "create", "find_free"],
                        "description": "Action: list upcoming events, create new event, or find free slots"
                    },
                    "summary": {
                        "type": "string",
                        "description": "Event title (for create action)"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Event start time (ISO format or natural language like 'next Monday 2pm')"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "Event end time (optional)"
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "description": "Event duration in minutes (default: 30)",
                        "default": 30
                    },
                    "description": {
                        "type": "string",
                        "description": "Event description"
                    },
                    "location": {
                        "type": "string",
                        "description": "Event location"
                    },
                    "attendees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of attendee email addresses"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of events to return (default: 10)",
                        "default": 10
                    }
                },
                "required": ["action"]
            }
        }

    def __call__(
        self,
        action: str,
        summary: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        duration_minutes: int = 30,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Execute Google Calendar tool.

        Args:
            action: Action to perform (list, create, find_free)
            summary: Event title
            start_time: Event start time
            end_time: Event end time
            duration_minutes: Event duration
            description: Event description
            location: Event location
            attendees: List of attendee emails
            max_results: Max events to return

        Returns:
            Dictionary with result or error
        """
        if not GOOGLE_API_AVAILABLE:
            return {
                "success": False,
                "error": "Google API libraries not installed. This feature requires additional setup."
            }

        # Check if OAuth is configured before attempting authentication
        if not os.path.exists(self.credentials_path):
            return {
                "success": False,
                "error": (
                    "Google Calendar integration is not configured. "
                    "This feature requires Google OAuth setup which is not available in the demo. "
                    "Please try other queries like company research or financial analysis."
                )
            }

        # Check if we have a valid token (don't trigger auth flow)
        if not self.is_authenticated():
            return {
                "success": False,
                "error": (
                    "Google Calendar authentication required. "
                    "This feature requires Google OAuth which is not configured for public use. "
                    "Please try other queries like company research or financial analysis."
                )
            }

        if action == "list":
            return self.list_events(max_results=max_results)
        elif action == "create":
            if not summary or not start_time:
                return {"success": False, "error": "summary and start_time required for create action"}
            return self.create_event(
                summary=summary,
                start_time=start_time,
                end_time=end_time,
                duration_minutes=duration_minutes,
                description=description,
                location=location,
                attendees=attendees
            )
        elif action == "find_free":
            return self.find_free_slots(duration_minutes=duration_minutes)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
