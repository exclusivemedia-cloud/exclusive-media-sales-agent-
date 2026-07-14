#!/usr/bin/env python3
"""
Sends the AI Operations Manager cold pitch for one lead. The subject/body
copy is composed by the calling agent (per ai_ops_offer_reference.md) —
this script is the mechanical send + compliance-enforcement + logging layer.

Usage:
  python outreach/send_pitches.py <lead_id> <subject> <body_html.txt|->

Set DRY_RUN=1 and DRY_RUN_EMAIL_OVERRIDE=you@example.com in config/.env to
redirect sends to your own inbox for testing — dry runs never touch lead
state or the suppression/thread log.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.config import get
from db.db_client import (
    get_connection, get_lead, get_demo_site_by_lead,
    insert_email_thread, set_pipeline_state, is_paused,
)
from outreach.compliance import (
    build_footer_html, build_list_unsubscribe_header,
    ensure_not_suppressed, SuppressedRecipientError,
)
from outreach.gmail_send_client import send_email

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


def render_pitch(business_name, body_html, demo_url):
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=False)
    template = env.get_template("cold_pitch.html.j2")
    return template.render(
        business_name=business_name,
        body_html=body_html,
        demo_url=demo_url,
        compliance_footer=build_footer_html(),
    )


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)

    lead_id, subject, body_arg = sys.argv[1], sys.argv[2], sys.argv[3]
    body_html = sys.stdin.read() if body_arg == "-" else open(body_arg, encoding="utf-8").read()

    conn = get_connection()
    dry_run = get("DRY_RUN", "").lower() in ("1", "true", "yes")
    if is_paused(conn) and not dry_run:
        print("Pipeline is paused (Telegram /pause) — refusing to send.", file=sys.stderr)
        conn.close()
        sys.exit(1)

    lead = get_lead(conn, lead_id)
    if not lead:
        print(f"No lead found with id {lead_id}", file=sys.stderr)
        sys.exit(1)
    if not lead["email"]:
        print(f"Lead {lead_id} has no email on file — cannot pitch", file=sys.stderr)
        sys.exit(1)

    demo = get_demo_site_by_lead(conn, lead_id)
    demo_url = None
    if demo:
        base_url = get("DEMO_SITE_BASE_URL", "").rstrip("/")
        demo_url = f"{base_url}/demo/{demo['slug']}" if base_url else f"/demo/{demo['slug']}"

    to_address = lead["email"]

    if dry_run:
        override = get("DRY_RUN_EMAIL_OVERRIDE")
        if not override:
            print("DRY_RUN is set but DRY_RUN_EMAIL_OVERRIDE is empty", file=sys.stderr)
            sys.exit(1)
        to_address = override
        subject = f"[DRY RUN — would send to {lead['email']}] {subject}"
    else:
        try:
            ensure_not_suppressed(conn, lead["email"])
        except SuppressedRecipientError as e:
            print(str(e), file=sys.stderr)
            sys.exit(1)

    html = render_pitch(lead["company_name"], body_html, demo_url)
    sent = send_email(
        to=to_address,
        subject=subject,
        html_body=html,
        list_unsubscribe=build_list_unsubscribe_header(get("SENDING_GMAIL_ADDRESS", "")),
    )
    print(f"Sent (gmail message id {sent.get('id')}) to {to_address}")

    if dry_run:
        conn.close()
        return

    insert_email_thread(
        conn, lead_id,
        gmail_thread_id=sent.get("threadId"),
        gmail_message_id=sent.get("id"),
        direction="outbound",
        subject=subject,
        body=body_html,
    )
    set_pipeline_state(conn, lead_id, "PITCHED")
    conn.close()


if __name__ == "__main__":
    main()
