#!/usr/bin/env python3
"""
Handles the owner's Telegram commands: /status, /pause, /resume,
/leads [state]. No persistent bot process — poll_and_handle() is called
once at the top of every scheduled orchestrator run (see
orchestrator/run_pipeline.py), reads any new messages via getUpdates, and
persists the offset so nothing is re-processed or lost between runs
(Telegram queues unacknowledged updates server-side for up to 24h).

Usage (manual test):
  python telegram/command_handler.py poll
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.config import get
from db.db_client import (
    get_connection, get_telegram_offset, set_telegram_offset,
    is_paused, set_paused, count_leads_by_state, list_leads,
)
from telegram.telegram_client import get_updates, send_message


def handle_command(conn, token, chat_id, text):
    text = text.strip()
    if text == "/status":
        counts = count_leads_by_state(conn)
        state_line = "PAUSED" if is_paused(conn) else "RUNNING"
        lines = [state_line] + [f"{state}: {n}" for state, n in sorted(counts.items())]
        send_message(token, chat_id, "\n".join(lines) if counts else "No leads yet.")
    elif text == "/pause":
        set_paused(conn, True, updated_by=str(chat_id))
        send_message(token, chat_id, "Paused — no sends will go out until /resume.")
    elif text == "/resume":
        set_paused(conn, False, updated_by=str(chat_id))
        send_message(token, chat_id, "Resumed.")
    elif text.startswith("/leads"):
        parts = text.split()
        state = parts[1].upper() if len(parts) > 1 else None
        leads = list_leads(conn, state)
        if not leads:
            send_message(token, chat_id, f"No leads in state {state or 'ANY'}.")
        else:
            lines = [f"{l['company_name']} — {l['pipeline_state']}" for l in leads[:25]]
            send_message(token, chat_id, "\n".join(lines))
    else:
        send_message(
            token, chat_id,
            "Unknown command. Try /status, /pause, /resume, /leads [state].",
        )


def poll_and_handle(conn):
    """Call once at the top of every scheduled orchestrator run."""
    token = get("TELEGRAM_BOT_TOKEN")
    allowed_chat_id = get("TELEGRAM_CHAT_ID")
    if not token or not allowed_chat_id:
        return  # Telegram not configured yet — skip silently

    last_offset = get_telegram_offset(conn)
    resp = get_updates(token, offset=(last_offset + 1) if last_offset else None, timeout=0)
    if not resp.get("ok"):
        return

    max_update_id = last_offset
    for update in resp.get("result", []):
        max_update_id = max(max_update_id, update["update_id"])
        message = update.get("message") or {}
        chat_id = str(message.get("chat", {}).get("id", ""))
        text = message.get("text", "")
        if chat_id != str(allowed_chat_id):
            continue  # ignore anyone but the configured owner
        if text:
            handle_command(conn, token, chat_id, text)

    if max_update_id != last_offset:
        set_telegram_offset(conn, max_update_id + 1)


def main():
    if len(sys.argv) != 2 or sys.argv[1] != "poll":
        print(__doc__)
        sys.exit(1)
    conn = get_connection()
    poll_and_handle(conn)
    conn.close()


if __name__ == "__main__":
    main()
