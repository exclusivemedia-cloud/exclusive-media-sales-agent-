#!/usr/bin/env python3
"""
Mechanical pre-flight for each scheduled AI Operations Manager run. Run
this first, via Bash, at the start of every orchestrator invocation (see
ai_ops_agency_prompt.md):

  1. Poll Telegram for owner commands (/status, /pause, /resume, /leads) so
     a /pause takes effect before anything else happens this run.
  2. If paused, stop here — no lead sync, no sends.
  3. Otherwise, sync new leads from exclusive-media-lead-gen's CSV output
     into the DB and GHL.

The creative per-lead work (demo copy, pitch copy, reading replies via the
Gmail MCP, negotiation) is NOT done here — it needs judgment a plain script
can't provide, so it's driven directly by the calling agent per
ai_ops_agency_prompt.md, using generate_demo.py / send_pitches.py /
record_reply.py / negotiation_engine.py / create_payment_link.py.

Usage:
  python orchestrator/run_pipeline.py
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.db_client import get_connection, is_paused
from telegram.command_handler import poll_and_handle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    conn = get_connection()
    poll_and_handle(conn)  # owner commands first, so /pause takes effect immediately
    paused = is_paused(conn)
    conn.close()

    print(f"Pipeline state: {'PAUSED' if paused else 'RUNNING'}")
    if paused:
        print("Paused via Telegram — skipping lead sync and all sends this run.")
        return

    sync_script = os.path.join(ROOT, "pipeline", "sync_leads_to_ghl.py")
    result = subprocess.run([sys.executable, sync_script], capture_output=True, text=True)
    print(result.stdout.strip())
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
