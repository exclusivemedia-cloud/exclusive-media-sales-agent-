# Negotiation Guardrails

These rules bound every automated reply sent by `negotiation_engine.py`.
The price floor and discount-round cap below are enforced in code
(`negotiation/price_floor.py`) — a violation is a script error, not a
prompt suggestion the agent could talk itself out of.

## Discount rules
- Full price is $997/mo. See `price_floor.py` for the exact floor and
  round cap — do not restate the numbers elsewhere, reference this file and
  that module instead so there's one source of truth.
- Never offer a discount unprompted. Only respond to an explicit price
  objection ("too expensive," "can you do better," etc.).
- Never offer anything beyond price (no free months, no custom feature
  promises, no deliverables changes) — deliverables are fixed, only price
  within the floor can move.
- Each concession must be smaller than the last.

## Tone
- Confident, brief, no desperation language ("please," "last chance,"
  excessive exclamation points).
- Always re-anchor to the demo site the prospect already saw — the value
  argument, not the price argument, does the persuading.

## Escalate to a human instead of auto-replying (`pipeline_state = NEEDS_HUMAN`)
Route to a human and send a Telegram alert, do not draft or send anything
automated, when a reply contains:
- A legal threat, complaint, or regulatory mention (BBB, lawyer, "report
  you," etc.).
- A refund or chargeback dispute on an existing payment.
- A request for contract terms, deliverables, or pricing structure not
  covered in `ai_ops_offer_reference.md`.
- Anything hostile, abusive, or clearly not a good-faith business reply.
- A price offer already at or below the floor being pushed further (i.e.
  the prospect won't accept the floor price at all).

## Enforcement
`negotiation_engine.py` calls `price_floor.validate_offer()` and
`price_floor.validate_discount_round()` before sending any reply that
contains a price. If either check fails, the script refuses to send, sets
the lead to `NEEDS_HUMAN`, and exits non-zero — the calling agent must not
retry with a lower number, only escalate.
