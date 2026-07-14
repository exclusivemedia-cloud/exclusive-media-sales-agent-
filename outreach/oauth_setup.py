#!/usr/bin/env python3
"""
One-time interactive OAuth flow for real Gmail sending. The Gmail MCP
already connected to this environment can only draft/read — it has no send
scope — so this produces a separate token specifically for send access.

Prerequisite: config/gmail_oauth_client.json (a Desktop app OAuth client
downloaded from Google Cloud Console — see PREREQUISITES.md section 4).

Usage:
  python outreach/oauth_setup.py

Opens a browser for the Google consent screen, then writes
config/gmail_token.json. Re-run any time to re-authorize (e.g. if the
client JSON changes or the scope list grows).
"""
import os
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENT_SECRETS_PATH = os.path.join(ROOT, "config", "gmail_oauth_client.json")
TOKEN_PATH = os.path.join(ROOT, "config", "gmail_token.json")
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def main():
    if not os.path.exists(CLIENT_SECRETS_PATH):
        print(
            f"Missing {CLIENT_SECRETS_PATH}. Download a Desktop-app OAuth "
            "client from Google Cloud Console first (PREREQUISITES.md section 4).",
            file=sys.stderr,
        )
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_PATH, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        f.write(creds.to_json())
    print(f"Saved Gmail send token to {TOKEN_PATH}")


if __name__ == "__main__":
    main()
