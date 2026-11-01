-- Reports for showing stores what BoardGame Broke sends them.
-- Run each block on its own in the Supabase SQL Editor, which shows only the
-- last result. Set the dates in each block before running it.
--
-- Clicks are counted once per search and link, so a double click counts once.
-- Click rate is the share of a store's appearances with at least one click on
-- it, so two products clicked in one search count once there.
-- Traffic marked with ?internal=1 is left out.


-- 1) One row per store for the period.
with period as (
    select timestamptz '2026-11-01 00:00 Europe/Athens' as starts,
           timestamptz '2026-12-01 00:00 Europe/Athens' as ends
),
searches as (
    select e.payload->>'search_id' as search_id, e.payload
    from public.usage_events e, period p
    where e.event = 'search'
      and e.created_at >= p.starts and e.created_at < p.ends
      and e.payload ? 'search_id'
      and coalesce(e.payload->>'internal', 'false') <> 'true'
),
clicks as (
    select distinct
        e.payload->>'search_id' as search_id,
        e.payload->>'url' as url,
        e.payload->>'store' as store,
        e.payload->>'section' as section
    from public.usage_events e, period p
    where e.event = 'click'
      and e.created_at >= p.starts and e.created_at < p.ends
      and coalesce(e.payload->>'internal', 'false') <> 'true'
),
listed as (
    select
        s.search_id,
        store,
        s.payload->'exact_in_stock_stores' ? store as exact_in_stock,
        s.payload->'cheapest_in_stock_stores' ? store as cheapest
    from searches s
    cross join lateral jsonb_array_elements_text(s.payload->'stores_with_results') as store
),
store_clicks as (
    select store, count(*) as clicks
    from clicks
    group by store
),
clicked_searches as (
    select distinct search_id, store
    from clicks
),
-- Clicks that went elsewhere when this store also had the game in stock.
lost as (
    select l.store, count(*) as lost_clicks
    from listed l
    join clicks c
      on c.search_id = l.search_id and c.store <> l.store and c.section = 'exact'
    where l.exact_in_stock
      and not exists (
          select 1 from clicks own
          where own.search_id = l.search_id and own.store = l.store
      )
    group by l.store
)
select
    l.store,
    count(*) as appearances,
    count(*) filter (where l.exact_in_stock) as searches_with_game_in_stock,
    count(*) filter (where l.cheapest) as times_cheapest_in_stock,
    coalesce(sc.clicks, 0) as clicks,
    round(100.0 * count(cs.search_id) / count(*), 1) as click_rate_pct,
    coalesce(lo.lost_clicks, 0) as clicks_lost_to_other_stores
from listed l
left join clicked_searches cs on cs.search_id = l.search_id and cs.store = l.store
left join store_clicks sc on sc.store = l.store
left join lost lo on lo.store = l.store
group by l.store, sc.clicks, lo.lost_clicks
order by clicks desc, appearances desc;


-- 2) Games one store did not have in stock. Set the store name below.
select lower(trim(e.query)) as game, count(*) as searches
from public.usage_events e
where e.event = 'search'
  and e.created_at >= timestamptz '2026-11-01 00:00 Europe/Athens'
  and e.created_at <  timestamptz '2026-12-01 00:00 Europe/Athens'
  and e.payload ? 'search_id'
  and coalesce(e.payload->>'internal', 'false') <> 'true'
  and not coalesce(e.payload->'exact_in_stock_stores' ? 'Store Name', false)
group by 1
order by searches desc, game
limit 10;


-- 3) Weekly check of searches and clicks, for watching a promotion's effect.
select
    date_trunc('week', created_at at time zone 'Europe/Athens')::date as week,
    count(*) filter (where event = 'search') as searches,
    count(distinct (payload->>'search_id', payload->>'url')) filter (where event = 'click') as clicks
from public.usage_events
where event in ('search', 'click')
  and created_at >= timestamptz '2026-11-01 00:00 Europe/Athens'
  and coalesce(payload->>'internal', 'false') <> 'true'
group by 1
order by 1 desc;
