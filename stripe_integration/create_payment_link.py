#!/usr/bin/env python3
"""
Creates a Stripe Checkout Session for one lead and emails them the payment
link. Called once a negotiation reaches explicit agreement.

A per-lead Checkout Session (not a single reusable Payment Link) is used
specifically so the webhook can attribute a completed payment back to the
right lead via client_reference_id/metadata.

Usage:
  python stripe_integration/create_payment_link.py <lead_id> [offered_price_cents]

If offered_price_cents is omitted, the full AI Operations Manager price
(STRIPE_PRICE_ID) is used. If provided, it must already have passed
negotiation.price_floor.validate_offer() during negotiation — this script
re-validates it as a second guard before ever touching Stripe.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.config import get, require
from db.db_client import get_connection, get_lead, insert_payment, set_pipeline_state, is_paused
from outreach.compliance import build_footer_html, build_list_unsubscribe_header
from outreach.gmail_send_client import send_email
from negotiation.price_floor import validate_offer, GuardrailViolation

import stripe
from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outreach", "templates")


def get_or_create_price(offered_price_cents):
    require("STRIPE_SECRET_KEY")
    stripe.api_key = get("STRIPE_SECRET_KEY")

    if offered_price_cents is None:
        require("STRIPE_PRICE_ID")
        return get("STRIPE_PRICE_ID"), 99700

    require("STRIPE_PRODUCT_ID")
    price = stripe.Price.create(
        product=get("STRIPE_PRODUCT_ID"),
        unit_amount=offered_price_cents,
        currency="usd",
        recurring={"interval": "month"},
    )
    return price.id, offered_price_cents


def main():
    if len(sys.argv) not in (2, 3):
        print(__doc__)
        sys.exit(1)

    lead_id = sys.argv[1]
    offered_price_cents = int(sys.argv[2]) if len(sys.argv) == 3 else None

    if offered_price_cents is not None:
        try:
            validate_offer(offered_price_cents)
        except GuardrailViolation as e:
            print(f"Refusing to create a checkout session: {e}", file=sys.stderr)
            sys.exit(1)

    conn = get_connection()
    if is_paused(conn):
        print("Pipeline is paused (Telegram /pause) — refusing to send.", file=sys.stderr)
        conn.close()
        sys.exit(1)

    lead = get_lead(conn, lead_id)
    if not lead:
        print(f"No lead found with id {lead_id}", file=sys.stderr)
        sys.exit(1)

    price_id, amount_cents = get_or_create_price(offered_price_cents)
    require("DEMO_SITE_BASE_URL")
    base_url = get("DEMO_SITE_BASE_URL").rstrip("/")

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        client_reference_id=str(lead_id),
        metadata={"lead_id": str(lead_id), "company_name": lead["company_name"]},
        success_url=f"{base_url}/thank-you?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{base_url}/",
        customer_email=lead["email"] or None,
    )

    insert_payment(conn, lead_id, session.id, amount_cents)
    set_pipeline_state(conn, lead_id, "AWAITING_PAYMENT")

    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=False)
    template = env.get_template("negotiation_reply.html.j2")
    price_dollars = amount_cents / 100
    body_html = (
        f"<p>You're all set — here's your secure link to get your AI Operations "
        f"Manager live for "
        f"{lead['company_name']}.</p>"
        f"<p>${price_dollars:.0f}/mo, cancel anytime.</p>"
    )
    html = template.render(
        body_html=body_html,
        payment_url=session.url,
        compliance_footer=build_footer_html(),
    )

    sent = send_email(
        to=lead["email"],
        subject=f"Your AI Operations Manager payment link — {lead['company_name']}",
        html_body=html,
        list_unsubscribe=build_list_unsubscribe_header(get("SENDING_GMAIL_ADDRESS", "")),
    )
    conn.close()
    print(f"Checkout session {session.id} created, payment link emailed "
          f"(gmail message id {sent.get('id')}) to {lead['email']}")


if __name__ == "__main__":
    main()
