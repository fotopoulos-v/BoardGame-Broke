-- Run this in Supabase SQL Editor
-- It creates a permanent table for Streamlit usage analytics events.

create extension if not exists pgcrypto;

create table if not exists public.usage_events (
    id uuid primary key default gen_random_uuid(),
    created_at timestamptz not null default now(),
    timestamp_utc text,
    event text not null,
    session_id text not null,
    query text,
    payload jsonb not null default '{}'::jsonb
);

alter table public.usage_events enable row level security;

-- Lock down table grants for client-facing roles.
revoke all on table public.usage_events from anon;
revoke all on table public.usage_events from authenticated;

-- Keep access for service role used by server-side Streamlit logging.
grant select, insert on table public.usage_events to service_role;

drop policy if exists usage_events_service_role_all on public.usage_events;
create policy usage_events_service_role_all
on public.usage_events
for all
to service_role
using (true)
with check (true);

create index if not exists idx_usage_events_created_at on public.usage_events (created_at desc);
create index if not exists idx_usage_events_event on public.usage_events (event);
create index if not exists idx_usage_events_session_id on public.usage_events (session_id);

comment on table public.usage_events is 'Anonymous usage events emitted by BoardGame Broke Streamlit app.';
