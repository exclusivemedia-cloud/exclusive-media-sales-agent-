Run the Exclusive Media enterprise-offer outreach draft cycle.

Project folder: C:\Users\Emmanuel\exclusive-media-sales-agent

Steps:

1. Run `python scripts/ghl_api.py find-leads` from that folder. This returns a
   JSON array of contacts tagged as qualifying leads for the Revenue
   Operations & Enterprise Acquisition offer, not yet drafted. If the array is
   empty, stop here and report "no new leads."

2. Read `proposal_reference.md` in that folder for the offer's facts, tone,
   and personalization rules. Do not invent deliverables, numbers, or terms
   beyond what's in that file.

3. For each contact in the array:
   a. Build a personalized email (subject + body, under ~200 words) using
      companyName, firstName, and any industry/service-type custom field
      present. Reference their specific industry concretely (e.g. for a
      cleaning company: recurring janitorial contracts with office parks;
      for a moving company: corporate relocation contracts). Sign off as
      Exclusive Media.
   b. Build an SMS (under 320 characters, one clear CTA to book a call, no
      pricing/dollar figures in the text).
   c. Create a Gmail draft via the Gmail MCP create_draft tool: `to` = the
      contact's email, `subject` and `body` as composed above. Skip the
      email step (but continue with SMS/tagging) if the contact has no email
      on file.
   d. Add a GHL task via
      `python scripts/ghl_api.py add-task <contact_id> "Review & send enterprise-offer SMS" "<sms text>"`
      so it surfaces as a to-do on the contact. Skip if the contact has no
      phone on file.
   e. Tag the contact as processed via
      `python scripts/ghl_api.py add-tag <contact_id> eb-offer-drafted`
      so it isn't drafted again next run.

4. Report a one-line summary: how many leads were processed, how many emails
   drafted, how many SMS tasks created, and any leads skipped (and why —
   e.g. missing email/phone).

Do not send anything directly (no Gmail send, no GHL SMS send, no LinkedIn
messages). Only create drafts/tasks for a human to review and send.
