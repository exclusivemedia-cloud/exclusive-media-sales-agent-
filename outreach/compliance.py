"""CAN-SPAM enforcement, shared by every outbound send path.

These are correctness requirements, not optional gates: every commercial
email this pipeline sends must carry a real physical address and an
unsubscribe mechanism, and every send must be checked against the
suppression list first. Nothing here is prompt guidance — it's code that
runs regardless of what the orchestrating agent composed.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.config import require, get
from db.db_client import is_suppressed, add_suppression

OPT_OUT_PHRASES = (
    "unsubscribe", "stop", "remove me", "take me off", "opt out", "opt-out",
    "do not contact", "don't contact", "no longer interested",
)


class SuppressedRecipientError(Exception):
    """Raised when a send is attempted against a suppressed address."""


def build_footer_html():
    require("COMPLIANCE_MAILING_ADDRESS")
    address = get("COMPLIANCE_MAILING_ADDRESS")
    return (
        '<p style="font-size:11px;color:#94a3b8;margin-top:24px;'
        'border-top:1px solid #1e293b;padding-top:12px;">'
        f"Exclusive Media &middot; {address}<br>"
        "Reply STOP to this email at any time to opt out of future messages."
        "</p>"
    )


def build_list_unsubscribe_header(from_address):
    return f"<mailto:{from_address}?subject=unsubscribe>"


def detect_opt_out(text):
    if not text:
        return False
    lowered = text.lower()
    return any(phrase in lowered for phrase in OPT_OUT_PHRASES)


def ensure_not_suppressed(conn, email):
    if is_suppressed(conn, email):
        raise SuppressedRecipientError(f"{email} is suppressed — refusing to send")


def register_opt_out_if_present(conn, email, inbound_text):
    """Call this on every inbound reply before doing anything else with it."""
    if detect_opt_out(inbound_text):
        add_suppression(conn, email, reason="opt-out phrase in reply")
        return True
    return False
