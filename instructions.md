# One-time GHL setup

This agent only drafts outreach for contacts tagged `eb-offer-lead` (see
`config/.env` — change `GHL_QUALIFYING_TAG` there if you rename it). It never
sends anything itself; it creates a Gmail draft and a GHL note/task so you can
review and send by hand.

## 1. Create the tag
In GHL: Settings → Tags → New Tag → `eb-offer-lead` (or whatever you set
`GHL_QUALIFYING_TAG` to).

## 2. Auto-apply the tag on your intake form
You said the specific form/funnel isn't picked yet. Once you know which form
captures inbound interest in this offer:

1. Go to Automation → Workflows → Create Workflow.
2. Trigger: "Form Submitted" → select that form.
3. Action: "Add Tag" → `eb-offer-lead`.
4. Publish the workflow.

Until this is wired up, you can tag qualifying contacts manually as a stopgap
and the agent will still pick them up on its next run.

## 3. Capture industry/service type on the form
The agent personalizes using `companyName` and a custom field for industry.
Make sure the form (or a custom field you set on the contact) captures the
prospect's service type (moving, cleaning, lawn care, HVAC, etc.) — map it to
a GHL custom field. Tell me the custom field's key/name once it exists so the
script can read it (`_extract_contact_summary` in `scripts/ghl_api.py` already
pulls all custom fields into a dict keyed by field key).

## 4. Fill in the Location ID
`config/.env` has `GHL_LOCATION_ID=` blank — paste yours in (Settings →
Business Info in that GHL sub-account, or visible in the URL when you're
inside it).

## 5. Test the connection
From the project folder:

```
python scripts/ghl_api.py test
```

Should print `HTTP 200` and `Credentials OK.` If you get 401, the token is
wrong/expired. If you get 422 on the search body, GHL's advanced-search filter
schema may differ slightly from what's coded — paste me the error and I'll
adjust `cmd_find_leads` in `scripts/ghl_api.py`.

## How a lead moves through the system
1. Contact fills out the form → GHL workflow tags them `eb-offer-lead`.
2. Scheduled agent run (every 30–60 min) calls `find-leads`, gets any contact
   with that tag and without `eb-offer-drafted`.
3. Agent writes a personalized email + SMS from `proposal_reference.md`.
4. Email → Gmail draft (via the Gmail MCP tool) for you to review/send.
5. SMS text → posted as a GHL task on the contact (so it shows up as a to-do,
   not just a buried note) for you to copy/send from GHL's own SMS UI.
6. Agent tags the contact `eb-offer-drafted` so it's not drafted twice.
