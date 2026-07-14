# AI Operations Manager demo site

Single Next.js app, one dynamic route (`/demo/[slug]`) that reads live from
the shared Supabase DB — new demos go live the instant
`../generate_demo.py` inserts a row, no redeploy needed.

## Local dev
```
npm install
cp .env.example .env.local   # fill in DATABASE_URL at minimum
npm run dev
```

## Deploy
1. Push this repo to GitHub (or connect the existing `exclusive-media-sales-agent`
   repo directly — set the Vercel project's "Root Directory" to `demo_site/web`).
2. In Vercel: New Project → import the repo → set Root Directory to
   `demo_site/web` → add the env vars from `.env.example` (Project Settings →
   Environment Variables) → Deploy.
3. Set `DEMO_SITE_BASE_URL` in the main repo's `config/.env` to the resulting
   Vercel URL (or your custom domain once attached).
4. The Stripe webhook route (`/api/stripe-webhook`, added in Phase 5) needs
   `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` set here too.
