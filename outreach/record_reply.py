#!/usr/bin/env python3
"""
Records an inbound reply the calling agent already fetched via the Gmail
MCP's read tools (search_threads/get_thread — there is no way for a plain
script to call those; only the agent's own tool-calling loop can). This
script is the mechanical persistence + opt-out-enforcement layer.

Usage:
  python outreach/record_reply.py <lead_id> <gmail_thread_id> <gmail_message_id> <raw_text.txt|-> [classification]

classification (optional, set by the agent's own reading of the reply):
  interested | objection | reject | agreed | escalate
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.db_client import (
    get_connection, get_lead, insert_email_thread, insert_negotiation_event,
    set_pipeline_state,
)
from outreach.compliance import register_opt_out_if_present


def main():
    if len(sys.argv) not in (5, 6):
        print(__doc__)
        sys.exit(1)

    lead_id, thread_id, message_id, text_arg = sys.argv[1:5]
    classification = sys.argv[5] if len(sys.argv) == 6 else None
    raw_text = sys.stdin.read() if text_arg == "-" else open(text_arg, encoding="utf-8").read()

    conn = get_connection()
    lead = get_lead(conn, lead_id)
    if not lead:
        print(f"No lead found with id {lead_id}", file=sys.stderr)
        sys.exit(1)

    if register_opt_out_if_present(conn, lead["email"], raw_text):
        set_pipeline_state(conn, lead_id, "SUPPRESSED")
        print(f"Opt-out detected — {lead['email']} suppressed, lead marked SUPPRESSED")
        conn.close()
        return

    email_thread_id = insert_email_thread(
        conn, lead_id,
        gmail_thread_id=thread_id,
        gmail_message_id=message_id,
        direction="inbound",
        body=raw_text,
    )
    insert_negotiation_event(
        conn, lead_id,
        email_thread_id=email_thread_id,
        direction="inbound",
        raw_text=raw_text,
        classification=classification,
    )

    new_state = "NEEDS_HUMAN" if classification == "escalate" else "REPLIED"
    set_pipeline_state(conn, lead_id, new_state)
    conn.close()
    print(f"Recorded reply for lead {lead_id}, state -> {new_state}")


if __name__ == "__main__":
    main()
