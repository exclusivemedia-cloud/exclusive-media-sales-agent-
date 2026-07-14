# AI Operations Manager Autonomous Agency — Manual Prerequisites

Before the pipeline can run for real (send real emails, deploy real demo sites,
collect real payments), you need to set up the following accounts and paste
the resulting keys into `config/.env`. None of this can be done on your
behalf — each involves creating an external account and/or agreeing to a
third party's terms.

## 1. Vercel (demo site hosting)
1. Create an account at vercel.com (GitHub login is easiest).
2. Nothing to configure yet — the Next.js app in `demo_site/web/` will be
   connected and deployed during Phase 2.
3. A custom domain is optional to start. `<project>.vercel.app` works fine
   for early testing; add a real domain later in Vercel's dashboard once you
   own one.
4. Env var to add once deployed: `DEMO_SITE_BASE_URL` (e.g.
   `https://ai-ops-demos.vercel.app`).

## 2. Supabase (shared database)
1. Create a free project at supabase.com.
2. From Project Settings → Database, copy the connection string (use the
   "Session pooler" URI for serverless-friendly connections).
3. Env var: `DATABASE_URL`.

## 3. Stripe (payment collection)
1. Create/use a Stripe account at stripe.com. Start in **test mode**.
2. Dashboard → Products → create a recurring Price: "AI Operations Manager",
   $997.00/month.
3. Copy the Price ID (`price_...`). Env var: `STRIPE_PRICE_ID`. Also copy the
   Product ID (`prod_...`) shown on the same product — env var
   `STRIPE_PRODUCT_ID` — it's used to create one-off negotiated-price Prices
   under the same product when a deal closes below list price.
4. Developers → API keys → copy the secret key. Env var: `STRIPE_SECRET_KEY`.
5. Developers → Webhooks → add an endpoint pointing at
   `https://<your-vercel-domain>/api/stripe-webhook` (created in Phase 5),
   listening for `checkout.session.completed`. Copy the signing secret. Env
   var: `STRIPE_WEBHOOK_SECRET`.
6. Only switch to live mode (and swap in live keys) once Phase 5 has been
   fully verified in test mode.

## 4. Google Cloud OAuth (real Gmail sending)
The Gmail MCP already connected to this environment can only draft and read
email — it cannot send. Sending requires a separate, dedicated OAuth client:
1. Create a project at console.cloud.google.com.
2. Enable the Gmail API.
3. OAuth consent screen → configure as "Internal" (or "External" + add your
   own address as a test user) → add the `gmail.send` scope.
4. Credentials → Create OAuth client ID → type "Desktop app". Download the
   client secret JSON.
5. Save it as `config/gmail_oauth_client.json` (already covered by
   `.gitignore` — verify before committing anything).
6. `outreach/oauth_setup.py` will use this file to run a one-time interactive
   consent flow and produce a token for the sending account.
7. Env var: `SENDING_GMAIL_ADDRESS` — the Gmail address you authorized above
   (used as the `From` header on every send).

## 5. Telegram bot (owner control interface)
1. Message @BotFather on Telegram, run `/newbot`, follow the prompts.
2. Copy the bot token. Env var: `TELEGRAM_BOT_TOKEN`.
3. Message your new bot once (anything) so it can see your chat, then visit
   `https://api.telegram.org/bot<token>/getUpdates` in a browser and copy
   your numeric `chat.id` from the JSON response. Env var: `TELEGRAM_CHAT_ID`.

## 6. CAN-SPAM mailing address
Federal law requires a real physical postal address in every commercial
email. Decide what address to use (business address, registered agent, or a
P.O. box) and add it as env var `COMPLIANCE_MAILING_ADDRESS`.

## Env var summary
Add all of these to `config/.env` (never commit this file):

```
DATABASE_URL=
DEMO_SITE_BASE_URL=
STRIPE_SECRET_KEY=
STRIPE_PRICE_ID=
STRIPE_PRODUCT_ID=
STRIPE_WEBHOOK_SECRET=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
COMPLIANCE_MAILING_ADDRESS=
SENDING_GMAIL_ADDRESS=
```

(Gmail OAuth uses a token file, not an env var — see §4 above.)

## What's safe to build before all of this is done
Phases 1-2 (DB schema, lead sync, demo site generator/app) can be built and
partially tested as soon as items 1-2 above exist. Phases 3-5 (real sending,
negotiation, payments) need items 3-6 in place before they can be tested for
real — until then they'll run in dry-run/test mode only.
