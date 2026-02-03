"""Gmail tool for email operations."""

import os
import base64
import pickle
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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


# Gmail API scopes
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose',
]


class Gmail:
    """
    Gmail tool for reading and sending emails.

    Supports:
    - Reading/summarizing emails from specific senders
    - Sending emails
    - Listing recent emails
    """

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        token_path: Optional[str] = None,
        timeout: int = 10
    ):
        """
        Initialize Gmail tool.

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
            "GOOGLE_TOKEN_PATH",
            str(project_root / "data" / "gmail_token.pickle")
        )

        # Ensure data directory exists
        Path(self.token_path).parent.mkdir(parents=True, exist_ok=True)

    def _get_service(self):
        """Get or create Gmail API service."""
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
                self.credentials_path, GMAIL_SCOPES
            )
            creds = flow.run_local_server(port=0)

            # Save credentials for next run
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)

        self._service = build('gmail', 'v1', credentials=creds)
        self._authenticated = True
        return self._service

    def is_authenticated(self) -> bool:
        """Check if Gmail is authenticated."""
        if self._authenticated:
            return True

        # Check if we have a valid token
        if os.path.exists(self.token_path):
            try:
                with open(self.token_path, 'rb') as token:
                    creds = pickle.load(token)
                    return creds and creds.valid
            except Exception:
                pass
        return False

    def list_emails(
        self,
        sender: Optional[str] = None,
        subject: Optional[str] = None,
        max_results: int = 10,
        unread_only: bool = False
    ) -> Dict[str, Any]:
        """
        List emails matching criteria.

        Args:
            sender: Filter by sender email address
            subject: Filter by subject contains
            max_results: Maximum number of emails to return
            unread_only: Only return unread emails

        Returns:
            Dictionary with email list or error
        """
        try:
            service = self._get_service()

            # Build query
            query_parts = []
            if sender:
                query_parts.append(f"from:{sender}")
            if subject:
                query_parts.append(f"subject:{subject}")
            if unread_only:
                query_parts.append("is:unread")

            query = " ".join(query_parts) if query_parts else None

            # Fetch messages
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])

            if not messages:
                return {
                    "success": True,
                    "emails": [],
                    "count": 0,
                    "message": f"No emails found matching criteria"
                }

            # Fetch details for each message
            email_list = []
            for msg in messages[:max_results]:
                msg_detail = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'To', 'Subject', 'Date']
                ).execute()

                headers = {h['name']: h['value'] for h in msg_detail.get('payload', {}).get('headers', [])}

                email_list.append({
                    "id": msg['id'],
                    "from": headers.get('From', 'Unknown'),
                    "to": headers.get('To', 'Unknown'),
                    "subject": headers.get('Subject', 'No Subject'),
                    "date": headers.get('Date', ''),
                    "snippet": msg_detail.get('snippet', '')[:200]
                })

            return {
                "success": True,
                "emails": email_list,
                "count": len(email_list),
                "query": query
            }

        except HttpError as e:
            return {
                "success": False,
                "error": f"Gmail API error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error listing emails: {str(e)}"
            }

    def read_email(self, email_id: str) -> Dict[str, Any]:
        """
        Read full email content.

        Args:
            email_id: Gmail message ID

        Returns:
            Dictionary with email content or error
        """
        try:
            service = self._get_service()

            msg = service.users().messages().get(
                userId='me',
                id=email_id,
                format='full'
            ).execute()

            headers = {h['name']: h['value'] for h in msg.get('payload', {}).get('headers', [])}

            # Extract body
            body = self._extract_body(msg.get('payload', {}))

            return {
                "success": True,
                "id": email_id,
                "from": headers.get('From', 'Unknown'),
                "to": headers.get('To', 'Unknown'),
                "subject": headers.get('Subject', 'No Subject'),
                "date": headers.get('Date', ''),
                "body": body,
                "snippet": msg.get('snippet', '')
            }

        except HttpError as e:
            return {
                "success": False,
                "error": f"Gmail API error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error reading email: {str(e)}"
            }

    def _extract_body(self, payload: Dict) -> str:
        """Extract email body from payload."""
        body = ""

        if 'body' in payload and payload['body'].get('data'):
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
        elif 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    if part.get('body', {}).get('data'):
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                        break
                elif 'parts' in part:
                    body = self._extract_body(part)
                    if body:
                        break

        return body[:5000]  # Limit body length

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an email.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            cc: CC recipients (comma-separated)
            bcc: BCC recipients (comma-separated)

        Returns:
            Dictionary with send result or error
        """
        try:
            service = self._get_service()

            # Create message
            message = MIMEMultipart()
            message['To'] = to
            message['Subject'] = subject

            if cc:
                message['Cc'] = cc
            if bcc:
                message['Bcc'] = bcc

            message.attach(MIMEText(body, 'plain'))

            # Encode message
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            # Send
            result = service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()

            return {
                "success": True,
                "message_id": result.get('id'),
                "thread_id": result.get('threadId'),
                "to": to,
                "subject": subject
            }

        except HttpError as e:
            return {
                "success": False,
                "error": f"Gmail API error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error sending email: {str(e)}"
            }

    def summarize_emails(
        self,
        sender: Optional[str] = None,
        max_emails: int = 5
    ) -> Dict[str, Any]:
        """
        Get a summary of recent emails from a sender.

        Args:
            sender: Filter by sender email address
            max_emails: Maximum number of emails to summarize

        Returns:
            Dictionary with email summaries
        """
        try:
            # List emails
            list_result = self.list_emails(sender=sender, max_results=max_emails)

            if not list_result.get('success'):
                return list_result

            emails = list_result.get('emails', [])

            if not emails:
                return {
                    "success": True,
                    "summary": f"No emails found from {sender}" if sender else "No emails found",
                    "count": 0
                }

            # Build summary
            summaries = []
            for email in emails:
                summaries.append({
                    "from": email.get('from'),
                    "subject": email.get('subject'),
                    "date": email.get('date'),
                    "preview": email.get('snippet', '')[:100]
                })

            return {
                "success": True,
                "emails": summaries,
                "count": len(summaries),
                "sender_filter": sender
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error summarizing emails: {str(e)}"
            }

    def get_tool_definition(self) -> Dict[str, Any]:
        """Get tool definition for LLM tool calling."""
        return {
            "name": "gmail",
            "description": (
                "Access Gmail to read, summarize, and send emails. "
                "Use this tool to check emails from specific senders, "
                "summarize recent communications, or send new emails. "
                "Requires Google OAuth authentication."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "read", "send", "summarize"],
                        "description": "Action to perform: list emails, read specific email, send email, or summarize emails"
                    },
                    "sender": {
                        "type": "string",
                        "description": "Email address to filter by sender (for list/summarize)"
                    },
                    "to": {
                        "type": "string",
                        "description": "Recipient email address (for send action)"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject (for send action or search filter)"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body content (for send action)"
                    },
                    "email_id": {
                        "type": "string",
                        "description": "Gmail message ID (for read action)"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of emails to return (default: 10)",
                        "default": 10
                    }
                },
                "required": ["action"]
            }
        }

    def __call__(
        self,
        action: str,
        sender: Optional[str] = None,
        to: Optional[str] = None,
        subject: Optional[str] = None,
        body: Optional[str] = None,
        email_id: Optional[str] = None,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Execute Gmail tool.

        Args:
            action: Action to perform (list, read, send, summarize)
            sender: Filter by sender
            to: Recipient for send
            subject: Subject for send or filter
            body: Body for send
            email_id: Message ID for read
            max_results: Max emails to return

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
                    "Gmail integration is not configured. "
                    "This feature requires Google OAuth setup which is not available in the demo. "
                    "Please try other queries like company research or financial analysis."
                )
            }

        # Check if we have a valid token (don't trigger auth flow)
        if not self.is_authenticated():
            return {
                "success": False,
                "error": (
                    "Gmail authentication required. "
                    "This feature requires Google OAuth which is not configured for public use. "
                    "Please try other queries like company research or financial analysis."
                )
            }

        if action == "list":
            return self.list_emails(sender=sender, subject=subject, max_results=max_results)
        elif action == "read":
            if not email_id:
                return {"success": False, "error": "email_id required for read action"}
            return self.read_email(email_id)
        elif action == "send":
            if not to or not subject or not body:
                return {"success": False, "error": "to, subject, and body required for send action"}
            return self.send_email(to=to, subject=subject, body=body)
        elif action == "summarize":
            return self.summarize_emails(sender=sender, max_emails=max_results)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
