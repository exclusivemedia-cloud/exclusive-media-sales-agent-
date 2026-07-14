#!/usr/bin/env python3
"""
Writes a personalized AI Operations Manager demo site to the DB and marks
the lead DEMO_READY. The creative content (chat script, copy) is composed by
whoever calls this script (the orchestrating agent, per
ai_ops_offer_reference.md) — this script is a mechanical persistence +
slug-assignment layer only.

Usage:
  python demo_site/generate_demo.py <lead_id> <content.json>
  python demo_site/generate_demo.py <lead_id> -   (reads content JSON from stdin)

content.json required keys:
  business_name, category, city, owner_first_name, chat_script
  (chat_script: list of {"sender": "customer"|"ai", "text": "..."})
"""
import json
import os
import re
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.config import get
from db.db_client import (
    get_connection, get_lead, insert_demo_site, slug_exists, set_pipeline_state,
)

REQUIRED_KEYS = {"business_name", "category", "city", "owner_first_name", "chat_script"}


def slugify(text):
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text or "business"


def unique_slug(conn, business_name):
    base = slugify(business_name)
    slug = base
    while slug_exists(conn, slug):
        slug = f"{base}-{uuid.uuid4().hex[:6]}"
    return slug


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    lead_id, content_arg = sys.argv[1], sys.argv[2]
    raw = sys.stdin.read() if content_arg == "-" else open(content_arg, encoding="utf-8").read()
    content = json.loads(raw)

    missing = REQUIRED_KEYS - content.keys()
    if missing:
        print(f"content.json missing required keys: {', '.join(sorted(missing))}", file=sys.stderr)
        sys.exit(1)

    conn = get_connection()
    lead = get_lead(conn, lead_id)
    if not lead:
        print(f"No lead found with id {lead_id}", file=sys.stderr)
        sys.exit(1)

    slug = unique_slug(conn, content["business_name"])
    insert_demo_site(conn, lead_id, slug, content)
    set_pipeline_state(conn, lead_id, "DEMO_READY")
    conn.close()

    base_url = get("DEMO_SITE_BASE_URL", "").rstrip("/")
    url = f"{base_url}/demo/{slug}" if base_url else f"/demo/{slug}"
    print(url)


if __name__ == "__main__":
    main()
