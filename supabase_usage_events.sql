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

create index if not exists idx_usage_events_created_at on public.usage_events (created_at desc);
create index if not exists idx_usage_events_event on public.usage_events (event);
create index if not exists idx_usage_events_session_id on public.usage_events (session_id);

comment on table public.usage_events is 'Anonymous usage events emitted by BoardGame Broke Streamlit app.';
