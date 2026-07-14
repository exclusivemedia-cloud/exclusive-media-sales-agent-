#!/usr/bin/env python3
"""
Prints leads in a given pipeline_state as JSON — the orchestrating agent's
way to enumerate work at each pipeline stage without writing raw SQL.

Usage:
  python db/list_leads.py <STATE>
  python db/list_leads.py ANY
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.db_client import get_connection, list_leads


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    state = sys.argv[1].upper()
    conn = get_connection()
    leads = list_leads(conn, None if state == "ANY" else state)
    conn.close()
    print(json.dumps([dict(l) for l in leads], default=str, indent=2))


if __name__ == "__main__":
    main()
