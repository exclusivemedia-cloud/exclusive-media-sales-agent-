"""Shared Postgres (Supabase) client for the AI Operations Manager pipeline.

Requires DATABASE_URL in config/.env. See PREREQUISITES.md.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.config import ENV, require

import psycopg2
import psycopg2.extras


def get_connection():
    require("DATABASE_URL")
    return psycopg2.connect(ENV["DATABASE_URL"])


def upsert_lead(conn, *, place_id, company_name, owner_name, phone, email, city,
                region, category, website_url, website_status, google_maps_url, source):
    """Insert a lead keyed on place_id, or return the existing row's id untouched
    if it's already known (place_id is the dedup key from lead-gen)."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            insert into leads (
                place_id, company_name, owner_name, phone, email, city, region,
                category, website_url, website_status, google_maps_url, source
            ) values (
                %(place_id)s, %(company_name)s, %(owner_name)s, %(phone)s, %(email)s,
                %(city)s, %(region)s, %(category)s, %(website_url)s, %(website_status)s,
                %(google_maps_url)s, %(source)s
            )
            on conflict (place_id) do update set place_id = excluded.place_id
            returning id, (xmax = 0) as inserted
            """,
            dict(place_id=place_id, company_name=company_name, owner_name=owner_name,
                 phone=phone, email=email, city=city, region=region, category=category,
                 website_url=website_url, website_status=website_status,
                 google_maps_url=google_maps_url, source=source),
        )
        row = cur.fetchone()
        conn.commit()
        return row["id"], row["inserted"]


def set_ghl_contact_id(conn, lead_id, ghl_contact_id):
    with conn.cursor() as cur:
        cur.execute(
            "update leads set ghl_contact_id = %s, updated_at = now() where id = %s",
            (ghl_contact_id, lead_id),
        )
        conn.commit()


def set_pipeline_state(conn, lead_id, state):
    with conn.cursor() as cur:
        cur.execute(
            "update leads set pipeline_state = %s, updated_at = now() where id = %s",
            (state, lead_id),
        )
        conn.commit()


def list_leads(conn, state=None):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        if state:
            cur.execute("select * from leads where pipeline_state = %s order by created_at", (state,))
        else:
            cur.execute("select * from leads order by created_at")
        return cur.fetchall()


def get_lead(conn, lead_id):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("select * from leads where id = %s", (lead_id,))
        return cur.fetchone()


def slug_exists(conn, slug):
    with conn.cursor() as cur:
        cur.execute("select 1 from demo_sites where slug = %s", (slug,))
        return cur.fetchone() is not None


def insert_demo_site(conn, lead_id, slug, content):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "insert into demo_sites (lead_id, slug, content) values (%s, %s, %s) returning id",
            (lead_id, slug, psycopg2.extras.Json(content)),
        )
        row = cur.fetchone()
        conn.commit()
        return row["id"]


def get_demo_site_by_lead(conn, lead_id):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "select * from demo_sites where lead_id = %s order by created_at desc limit 1",
            (lead_id,),
        )
        return cur.fetchone()


def insert_email_thread(conn, lead_id, *, gmail_thread_id=None, gmail_message_id=None,
                         direction, subject=None, body=None):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            insert into email_threads (lead_id, gmail_thread_id, gmail_message_id, direction, subject, body)
            values (%s, %s, %s, %s, %s, %s) returning id
            """,
            (lead_id, gmail_thread_id, gmail_message_id, direction, subject, body),
        )
        row = cur.fetchone()
        conn.commit()
        return row["id"]


def get_latest_email_thread(conn, lead_id):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "select * from email_threads where lead_id = %s order by created_at desc limit 1",
            (lead_id,),
        )
        return cur.fetchone()


def is_suppressed(conn, email):
    if not email:
        return False
    with conn.cursor() as cur:
        cur.execute("select 1 from suppressions where lower(email) = lower(%s)", (email,))
        return cur.fetchone() is not None


def add_suppression(conn, email, reason):
    with conn.cursor() as cur:
        cur.execute(
            "insert into suppressions (email, reason) values (%s, %s) on conflict (email) do nothing",
            (email, reason),
        )
        conn.commit()


def insert_negotiation_event(conn, lead_id, *, email_thread_id=None, direction,
                              raw_text=None, classification=None, discount_round=0):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            insert into negotiation_events (lead_id, email_thread_id, direction, raw_text, classification, discount_round)
            values (%s, %s, %s, %s, %s, %s) returning id
            """,
            (lead_id, email_thread_id, direction, raw_text, classification, discount_round),
        )
        row = cur.fetchone()
        conn.commit()
        return row["id"]


def count_discount_rounds(conn, lead_id):
    with conn.cursor() as cur:
        cur.execute(
            "select coalesce(max(discount_round), 0) from negotiation_events where lead_id = %s",
            (lead_id,),
        )
        return cur.fetchone()[0]


def get_telegram_offset(conn):
    with conn.cursor() as cur:
        cur.execute("select last_update_id from telegram_offset where id = 1")
        return cur.fetchone()[0]


def set_telegram_offset(conn, last_update_id):
    with conn.cursor() as cur:
        cur.execute("update telegram_offset set last_update_id = %s where id = 1", (last_update_id,))
        conn.commit()


def is_paused(conn):
    with conn.cursor() as cur:
        cur.execute("select paused from pause_state where id = 1")
        return cur.fetchone()[0]


def set_paused(conn, paused, updated_by=None):
    with conn.cursor() as cur:
        cur.execute(
            "update pause_state set paused = %s, updated_at = now(), updated_by = %s where id = 1",
            (paused, updated_by),
        )
        conn.commit()


def count_leads_by_state(conn):
    with conn.cursor() as cur:
        cur.execute("select pipeline_state, count(*) from leads group by pipeline_state")
        return dict(cur.fetchall())


def insert_payment(conn, lead_id, stripe_session_id, amount_cents):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            insert into payments (lead_id, stripe_session_id, amount_cents, status)
            values (%s, %s, %s, 'pending') returning id
            """,
            (lead_id, stripe_session_id, amount_cents),
        )
        row = cur.fetchone()
        conn.commit()
        return row["id"]
