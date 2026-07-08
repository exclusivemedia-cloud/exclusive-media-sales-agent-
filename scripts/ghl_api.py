#!/usr/bin/env python3
"""
GoHighLevel (GHL) API v2 helper CLI for the Exclusive Media enterprise-offer
outreach agent. Zero external dependencies (stdlib only).

Reads credentials from ../config/.env (GHL_API_TOKEN, GHL_LOCATION_ID,
GHL_API_BASE, GHL_API_VERSION, GHL_QUALIFYING_TAG, GHL_PROCESSED_TAG).

Commands:
  test                                   Verify credentials work
  find-leads                             List contacts tagged qualifying-tag
                                          but not yet processed-tag; prints JSON
  add-tag <contact_id> <tag>             Add a tag to a contact
  add-note <contact_id> <text>           Add a note to a contact
  add-task <contact_id> <title> <body>   Add a task to a contact (due tomorrow)
"""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT, "config", ".env")


def load_env(path):
    env = {}
    if not os.path.exists(path):
        return env
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    return env


ENV = {**load_env(ENV_PATH), **os.environ}
TOKEN = ENV.get("GHL_API_TOKEN", "")
LOCATION_ID = ENV.get("GHL_LOCATION_ID", "")
API_BASE = ENV.get("GHL_API_BASE", "https://services.leadconnectorhq.com")
API_VERSION = ENV.get("GHL_API_VERSION", "2021-07-28")
QUALIFYING_TAG = ENV.get("GHL_QUALIFYING_TAG", "eb-offer-lead")
PROCESSED_TAG = ENV.get("GHL_PROCESSED_TAG", "eb-offer-drafted")


def _require_creds():
    missing = [
        name
        for name, val in (("GHL_API_TOKEN", TOKEN), ("GHL_LOCATION_ID", LOCATION_ID))
        if not val
    ]
    if missing:
        print(
            f"Missing required config in config/.env: {', '.join(missing)}",
            file=sys.stderr,
        )
        sys.exit(2)


def _request(method, path, body=None, query=None):
    _require_creds()
    url = f"{API_BASE}{path}"
    if query:
        from urllib.parse import urlencode

        url = f"{url}?{urlencode(query)}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Version", API_VERSION)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    req.add_header(
        "User-Agent",
        "Mozilla/5.0 (compatible; ExclusiveMedia-SalesAgent/1.0; +https://exclusivemedia.example)",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"raw": raw}
        return e.code, parsed


def cmd_test():
    status, resp = _request(
        "POST",
        "/contacts/search",
        body={"locationId": LOCATION_ID, "pageLimit": 1},
    )
    print(f"HTTP {status}")
    print(json.dumps(resp, indent=2)[:2000])
    if status >= 400:
        sys.exit(1)
    print("\nCredentials OK.")


def _extract_contact_summary(c):
    custom_fields = {}
    for cf in c.get("customFields", []) or []:
        key = cf.get("key") or cf.get("id")
        if key:
            custom_fields[key] = cf.get("value") or cf.get("fieldValue")
    return {
        "id": c.get("id"),
        "firstName": c.get("firstName"),
        "lastName": c.get("lastName"),
        "companyName": c.get("companyName"),
        "email": c.get("email"),
        "phone": c.get("phone"),
        "tags": c.get("tags", []),
        "customFields": custom_fields,
    }


def cmd_find_leads():
    all_matches = []
    page = 1
    page_limit = 100
    while True:
        status, resp = _request(
            "POST",
            "/contacts/search",
            body={
                "locationId": LOCATION_ID,
                "page": page,
                "pageLimit": page_limit,
                "filters": [
                    {"field": "tags", "operator": "contains", "value": QUALIFYING_TAG}
                ],
            },
        )
        if status >= 400:
            print(f"GHL API error (HTTP {status}): {json.dumps(resp)}", file=sys.stderr)
            sys.exit(1)
        contacts = resp.get("contacts", [])
        if not contacts:
            break
        for c in contacts:
            tags = [t.lower() for t in (c.get("tags") or [])]
            if PROCESSED_TAG.lower() not in tags:
                all_matches.append(_extract_contact_summary(c))
        if len(contacts) < page_limit:
            break
        page += 1
    print(json.dumps(all_matches, indent=2))


def cmd_add_tag(contact_id, tag):
    status, resp = _request(
        "POST", f"/contacts/{contact_id}/tags", body={"tags": [tag]}
    )
    print(f"HTTP {status}: {json.dumps(resp)}")
    if status >= 400:
        sys.exit(1)


def cmd_add_note(contact_id, text):
    status, resp = _request(
        "POST", f"/contacts/{contact_id}/notes", body={"body": text}
    )
    print(f"HTTP {status}: {json.dumps(resp)}")
    if status >= 400:
        sys.exit(1)


def cmd_add_task(contact_id, title, body_text):
    due = (datetime.now(timezone.utc) + timedelta(days=1)).strftime(
        "%Y-%m-%dT%H:%M:%S.000Z"
    )
    status, resp = _request(
        "POST",
        f"/contacts/{contact_id}/tasks",
        body={"title": title, "body": body_text, "dueDate": due, "completed": False},
    )
    print(f"HTTP {status}: {json.dumps(resp)}")
    if status >= 400:
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    args = sys.argv[2:]
    if cmd == "test":
        cmd_test()
    elif cmd == "find-leads":
        cmd_find_leads()
    elif cmd == "add-tag" and len(args) == 2:
        cmd_add_tag(*args)
    elif cmd == "add-note" and len(args) == 2:
        cmd_add_note(*args)
    elif cmd == "add-task" and len(args) == 3:
        cmd_add_task(*args)
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
