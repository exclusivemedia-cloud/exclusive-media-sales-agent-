"""Hard-coded negotiation limits. Imported (not just prompted) so a floor
violation is a code-level impossibility. See guardrails.md for the rules
these enforce and the escalation policy for anything outside them.
"""

PRICE_FULL_CENTS = 99700       # $997.00/mo — the only price ever offered up front
PRICE_FLOOR_CENTS = 79700      # $797.00/mo — never go lower, no exceptions
MAX_DISCOUNT_ROUNDS = 2        # at most 2 concessions per lead


class GuardrailViolation(Exception):
    """Raised when a proposed negotiation reply violates a hard limit."""


def validate_offer(offered_cents):
    if offered_cents < PRICE_FLOOR_CENTS:
        raise GuardrailViolation(
            f"Offered {offered_cents}c is below the price floor of {PRICE_FLOOR_CENTS}c"
        )
    if offered_cents > PRICE_FULL_CENTS:
        raise GuardrailViolation(
            f"Offered {offered_cents}c exceeds the full price {PRICE_FULL_CENTS}c"
        )


def validate_discount_round(round_number):
    if round_number > MAX_DISCOUNT_ROUNDS:
        raise GuardrailViolation(
            f"Discount round {round_number} exceeds MAX_DISCOUNT_ROUNDS={MAX_DISCOUNT_ROUNDS}"
        )
