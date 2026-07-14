#!/usr/bin/env python3
"""
Bridges exclusive-media-lead-gen's output into the AI Operations Manager
pipeline: reads leads.csv, keeps only the target segment (no website / weak website),
inserts each into the shared DB (leads table, dedup on Place_ID), and
mirrors it into GHL as a contact for human visibility via ghl_api.py.

Usage:
  python pipeline/sync_leads_to_ghl.py [path/to/leads.csv]

Defaults to ../exclusive-media-lead-gen/output/leads.csv (sibling repo).
"""
import csv
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.config import ENV, get
from db.db_client import get_connection, upsert_lead, set_ghl_contact_id, set_pipeline_state

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GHL_SCRIPT = os.path.join(ROOT, "scripts", "ghl_api.py")
DEFAULT_CSV = os.path.join(ROOT, "..", "exclusive-media-lead-gen", "output", "leads.csv")

TARGET_STATUSES = {"NO_WEBSITE", "LOW_CONVERSION_WEBSITE"}
AI_OPS_TAG = get("GHL_AI_OPS_TAG", "ai-ops-qualifying-lead")


def split_owner_name(owner_decision_maker, company_name):
    owner_decision_maker = (owner_decision_maker or "").strip()
    if not owner_decision_maker:
        return "Owner", company_name or "there"
    parts = owner_decision_maker.split()
    if len(parts) == 1:
        return parts[0], company_name or "there"
    return parts[0], " ".join(parts[1:])


def create_ghl_contact(first_name, last_name, company_name, email, phone):
    """Runs ghl_api.py create-contact as a subprocess (kept untouched/reused
    as-is, per plan). Returns the new contact id, or None on failure/skip."""
    if not email and not phone:
        return None
    result = subprocess.run(
        [sys.executable, GHL_SCRIPT, "create-contact", first_name, last_name,
         company_name, email or "", phone or "", AI_OPS_TAG],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  GHL create-contact failed: {result.stdout} {result.stderr}", file=sys.stderr)
        return None
    # ghl_api.py prints "HTTP <status>: <json>"
    line = result.stdout.strip()
    _, _, payload = line.partition(": ")
    try:
        resp = json.loads(payload)
        return resp.get("contact", {}).get("id")
    except (json.JSONDecodeError, AttributeError):
        print(f"  Could not parse GHL response: {line}", file=sys.stderr)
        return None


def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV
    if not os.path.exists(csv_path):
        print(f"CSV not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    conn = get_connection()
    inserted_count = 0
    skipped_count = 0
    ghl_created_count = 0

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            status = (row.get("Website_Status") or "").strip()
            if status not in TARGET_STATUSES:
                skipped_count += 1
                continue

            place_id = row.get("Place_ID") or ""
            if not place_id:
                skipped_count += 1
                continue

            lead_id, is_new = upsert_lead(
                conn,
                place_id=place_id,
                company_name=row.get("Company_Name") or "",
                owner_name=row.get("Owner_Decision_Maker") or "",
                phone=row.get("Phone_E164") or "",
                email=row.get("Email") or "",
                city=row.get("City") or "",
                region=row.get("Region") or "",
                category=row.get("Category") or "",
                website_url=row.get("Website_URL") or "",
                website_status=status,
                google_maps_url=row.get("Google_Maps_URL") or "",
                source=row.get("Source") or "",
            )

            if not is_new:
                continue  # already synced in a previous run

            inserted_count += 1
            first_name, last_name = split_owner_name(row.get("Owner_Decision_Maker"), row.get("Company_Name"))
            contact_id = create_ghl_contact(
                first_name, last_name, row.get("Company_Name") or "",
                row.get("Email") or "", row.get("Phone_E164") or "",
            )
            if contact_id:
                set_ghl_contact_id(conn, lead_id, contact_id)
                ghl_created_count += 1
            set_pipeline_state(conn, lead_id, "NEW")

    conn.close()
    print(f"Synced {inserted_count} new leads ({ghl_created_count} mirrored to GHL), "
          f"skipped {skipped_count} rows (already synced or not in the target segment).")


if __name__ == "__main__":
    main()
