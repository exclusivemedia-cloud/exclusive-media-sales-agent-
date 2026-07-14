# Offer Reference — AI Operations Manager

Use this as the factual/tone source when drafting AI Operations Manager pitch
and negotiation copy. Do not invent numbers, deliverables, or terms beyond
what's here. Personalize only the framing (business name, category, city,
owner name) — never the price or deliverables. For how far a price can
actually move in negotiation, see `negotiation/guardrails.md` and
`negotiation/price_floor.py` (the code-enforced source of truth) — never
state a number from memory here.

PREPARED BY: Exclusive Media

## What AI Operations Manager is
An AI Employee that answers every missed call and inbound text instantly,
24/7, qualifies the lead against the business's own rules, and books
qualified jobs straight onto their calendar — so no lead goes cold waiting
for a callback.

- **Instant response**: sub-2-minute automated text reply to every inbound
  lead, day or night.
- **Qualification logic**: configurable service-area zip codes and explicit
  exclusions (services the business doesn't perform), so the AI never wastes
  the owner's time on a bad-fit lead.
- **Booking**: qualified leads get a direct link to the business's own
  calendar (GHL/Google Calendar) to self-schedule.
- **Owner visibility**: every conversation is logged and reviewable; the
  owner can take over any conversation manually at any time.

## Investment
- $997/mo, month-to-month, no long-term contract.
- Setup/onboarding included — live within 48 hours of signup.

## Personalization notes for outreach
- `{{business_name}}` — the prospect's company name.
- `{{owner_first_name}}` — first name of the owner/decision-maker (best
  effort from public listing data — if unknown, use a neutral greeting,
  never guess a name).
- `{{category}}` — their service type (HVAC, pool, landscaping, etc.). Use
  it to make the pitch concrete (e.g. for HVAC: "the 11pm no-AC text you'd
  otherwise miss until morning").
- `{{city}}` — used to reference their local service area.
- `{{demo_url}}` — every pitch must link to that specific lead's generated
  demo site (built by `demo_site/generate_demo.py`), which shows a live,
  interactive preview of their own AI Employee in action. This is the single
  most persuasive element of the pitch — always lead with it, don't bury it.
- Keep the cold pitch email under ~180 words. One clear CTA: view your demo.
- Never mention price in the first cold-pitch email — the demo does the
  selling; pricing comes up naturally once they reply with interest.
