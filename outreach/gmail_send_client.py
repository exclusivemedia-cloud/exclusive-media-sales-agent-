"""Real Gmail sending via the Gmail API (gmail.send OAuth token), distinct
from the read-only/draft-only Gmail MCP tools available to the agent.
Requires config/gmail_token.json — see outreach/oauth_setup.py.
"""
import base64
import os
import sys
from email.mime.text import MIMEText

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.config import get, require

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_PATH = os.path.join(ROOT, "config", "gmail_token.json")
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def _get_credentials():
    if not os.path.exists(TOKEN_PATH):
        raise RuntimeError(
            f"No Gmail send token at {TOKEN_PATH} — run outreach/oauth_setup.py first"
        )
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return creds


def send_email(to, subject, html_body, thread_id=None, list_unsubscribe=None):
    """Sends a real email. Returns {"id": ..., "threadId": ...}."""
    require("SENDING_GMAIL_ADDRESS")
    from_address = get("SENDING_GMAIL_ADDRESS")

    creds = _get_credentials()
    service = build("gmail", "v1", credentials=creds)

    message = MIMEText(html_body, "html")
    message["to"] = to
    message["from"] = from_address
    message["subject"] = subject
    if list_unsubscribe:
        message["List-Unsubscribe"] = list_unsubscribe

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    body = {"raw": raw}
    if thread_id:
        body["threadId"] = thread_id

    return service.users().messages().send(userId="me", body=body).execute()
