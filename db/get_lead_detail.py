#!/usr/bin/env python3
"""
Prints one lead plus its demo content, discount-round count, and latest
email thread id as JSON — context the orchestrating agent needs to compose
an on-brand negotiation reply.

Usage:
  python db/get_lead_detail.py <lead_id>
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.db_client import (
    get_connection, get_lead, get_demo_site_by_lead,
    get_latest_email_thread, count_discount_rounds,
)


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    lead_id = sys.argv[1]
    conn = get_connection()
    lead = get_lead(conn, lead_id)
    if not lead:
        print(f"No lead found with id {lead_id}", file=sys.stderr)
        sys.exit(1)

    demo = get_demo_site_by_lead(conn, lead_id)
    thread = get_latest_email_thread(conn, lead_id)
    rounds = count_discount_rounds(conn, lead_id)
    conn.close()

    print(json.dumps({
        "lead": dict(lead),
        "demo": dict(demo) if demo else None,
        "latest_email_thread": dict(thread) if thread else None,
        "discount_rounds_used": rounds,
    }, default=str, indent=2))


if __name__ == "__main__":
    main()
