-- AI Operations Manager autonomous agency pipeline — shared state.
-- Run once against the Supabase Postgres instance (see PREREQUISITES.md).

create extension if not exists "pgcrypto";

create table if not exists leads (
    id uuid primary key default gen_random_uuid(),
    place_id text unique,                    -- Google Place_ID, dedup key from lead-gen
    company_name text not null,
    owner_name text,
    phone text,
    email text,
    city text,
    region text,
    category text,
    website_url text,
    website_status text,                     -- NO_WEBSITE | LOW_CONVERSION_WEBSITE | OPTIMIZED
    google_maps_url text,
    source text,                             -- google_places | outscraper
    ghl_contact_id text,
    pipeline_state text not null default 'NEW' check (pipeline_state in (
        'NEW', 'DEMO_READY', 'PITCHED', 'REPLIED', 'NEGOTIATING',
        'AWAITING_PAYMENT', 'PAID', 'NEEDS_HUMAN', 'SUPPRESSED', 'LOST'
    )),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists demo_sites (
    id uuid primary key default gen_random_uuid(),
    lead_id uuid not null references leads(id) on delete cascade,
    slug text unique not null,
    content jsonb not null,
    created_at timestamptz not null default now()
);

create table if not exists email_threads (
    id uuid primary key default gen_random_uuid(),
    lead_id uuid not null references leads(id) on delete cascade,
    gmail_thread_id text,
    gmail_message_id text,
    direction text not null check (direction in ('outbound', 'inbound')),
    subject text,
    body text,
    created_at timestamptz not null default now()
);

create table if not exists negotiation_events (
    id uuid primary key default gen_random_uuid(),
    lead_id uuid not null references leads(id) on delete cascade,
    email_thread_id uuid references email_threads(id) on delete set null,
    direction text not null check (direction in ('inbound', 'outbound')),
    raw_text text,
    classification text,                     -- interested | objection | reject | agreed | escalate
    discount_round int not null default 0,
    created_at timestamptz not null default now()
);

create table if not exists payments (
    id uuid primary key default gen_random_uuid(),
    lead_id uuid not null references leads(id) on delete cascade,
    stripe_session_id text unique not null,
    stripe_event_id text unique,
    status text not null default 'pending' check (status in ('pending', 'paid', 'failed', 'expired')),
    amount_cents int,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists suppressions (
    id uuid primary key default gen_random_uuid(),
    email text unique not null,
    reason text,
    created_at timestamptz not null default now()
);

-- Singleton rows (id always 1) for cross-run orchestrator state.
create table if not exists telegram_offset (
    id int primary key default 1 check (id = 1),
    last_update_id bigint not null default 0
);
insert into telegram_offset (id, last_update_id) values (1, 0)
    on conflict (id) do nothing;

create table if not exists pause_state (
    id int primary key default 1 check (id = 1),
    paused boolean not null default false,
    updated_at timestamptz not null default now(),
    updated_by text
);
insert into pause_state (id, paused) values (1, false)
    on conflict (id) do nothing;

create index if not exists idx_leads_pipeline_state on leads(pipeline_state);
create index if not exists idx_demo_sites_lead_id on demo_sites(lead_id);
create index if not exists idx_email_threads_lead_id on email_threads(lead_id);
create index if not exists idx_negotiation_events_lead_id on negotiation_events(lead_id);
create index if not exists idx_payments_lead_id on payments(lead_id);
