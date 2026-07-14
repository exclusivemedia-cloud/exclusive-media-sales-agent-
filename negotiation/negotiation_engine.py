#!/usr/bin/env python3
"""
Sends a negotiation reply for one lead. The reply copy is composed by the
calling agent after reading the prospect's message (via the Gmail MCP) and
`ai_ops_offer_reference.md`/`guardrails.md` — this script enforces the price
floor and discount-round cap in code before anything goes out, and handles
the mechanical send + logging.

Usage:
  python negotiation/negotiation_engine.py <lead_id> <reply_body.html|-> [offered_price_cents]

If offered_price_cents is omitted, the reply is sent as-is (no price
guardrail applies — e.g. answering a non-price objection). If provided, the
floor/round-cap checks run first; on failure the lead is routed to
NEEDS_HUMAN and nothing is sent.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.config import get
from db.db_client import (
    get_connection, get_lead, insert_email_thread, insert_negotiation_event,
    set_pipeline_state, count_discount_rounds, get_latest_email_thread, is_paused,
)
from outreach.compliance import (
    build_footer_html, build_list_unsubscribe_header,
    ensure_not_suppressed, SuppressedRecipientError,
)
from outreach.gmail_send_client import send_email
from negotiation.price_floor import validate_offer, validate_discount_round, GuardrailViolation

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outreach", "templates")


def render_reply(body_html, payment_url=None):
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=False)
    template = env.get_template("negotiation_reply.html.j2")
    return template.render(
        body_html=body_html,
        payment_url=payment_url,
        compliance_footer=build_footer_html(),
    )


def main():
    if len(sys.argv) not in (3, 4):
        print(__doc__)
        sys.exit(1)

    lead_id, body_arg = sys.argv[1], sys.argv[2]
    offered_price_cents = int(sys.argv[3]) if len(sys.argv) == 4 else None
    body_html = sys.stdin.read() if body_arg == "-" else open(body_arg, encoding="utf-8").read()

    conn = get_connection()
    if is_paused(conn):
        print("Pipeline is paused (Telegram /pause) — refusing to send.", file=sys.stderr)
        conn.close()
        sys.exit(1)

    lead = get_lead(conn, lead_id)
    if not lead:
        print(f"No lead found with id {lead_id}", file=sys.stderr)
        sys.exit(1)

    try:
        ensure_not_suppressed(conn, lead["email"])
    except SuppressedRecipientError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    round_number = 0
    if offered_price_cents is not None:
        round_number = count_discount_rounds(conn, lead_id) + 1
        try:
            validate_offer(offered_price_cents)
            validate_discount_round(round_number)
        except GuardrailViolation as e:
            print(f"Guardrail violation, refusing to send: {e}", file=sys.stderr)
            set_pipeline_state(conn, lead_id, "NEEDS_HUMAN")
            conn.close()
            sys.exit(1)

    html = render_reply(body_html)
    thread = get_latest_email_thread(conn, lead_id)
    sent = send_email(
        to=lead["email"],
        subject="Re: your AI Operations Manager demo",
        html_body=html,
        thread_id=thread["gmail_thread_id"] if thread else None,
        list_unsubscribe=build_list_unsubscribe_header(get("SENDING_GMAIL_ADDRESS", "")),
    )

    email_thread_id = insert_email_thread(
        conn, lead_id,
        gmail_thread_id=sent.get("threadId"),
        gmail_message_id=sent.get("id"),
        direction="outbound",
        body=body_html,
    )
    insert_negotiation_event(
        conn, lead_id,
        email_thread_id=email_thread_id,
        direction="outbound",
        raw_text=body_html,
        classification="counter" if offered_price_cents is not None else "reply",
        discount_round=round_number,
    )
    set_pipeline_state(conn, lead_id, "NEGOTIATING")
    conn.close()
    print(f"Sent negotiation reply (gmail message id {sent.get('id')}) to {lead['email']}")


if __name__ == "__main__":
    main()
