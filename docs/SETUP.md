# Setup

Everything needed to run and maintain BoardGame Broke. Real values never go in
this file or anywhere else in the repository, only the placeholders shown here.

## 1. Firecrawl key

The Firecrawl API key is **required** — the app will not start without it. It is
never stored in the repository; `config.py` resolves it at runtime from Streamlit
secrets first, then from an environment variable of the same name.

**Streamlit Cloud:** add it under *App settings → Secrets*:

```toml
FIRECRAWL_API_KEY = "<your-firecrawl-key>"
```

**Local development:** put the same line in `.streamlit/secrets.toml` (git-ignored),
or export it in your shell for running the scraper outside Streamlit:

```bash
export FIRECRAWL_API_KEY="<your-firecrawl-key>"
```

The optional `PUBLIC_FINDBAR_BEARER_TOKEN` and `PUBLIC_FINDBAR_SESSION_ID`
overrides are resolved the same way, and fall back to built-in defaults.

### Stores that refuse direct requests

Most stores are searched over plain HTTP, which uses no Firecrawl credits. A store
can refuse those requests from Streamlit's servers while still working from a home
connection. It then shows as ❌ in *Store Coverage Details*, with the reason.

To send such a store through Firecrawl, name it in the Streamlit secrets. This
needs no redeploy, and each named store uses one more credit per search:

```toml
BGB_FORCE_FIRECRAWL = "Store One,Store Two"
```

Nerdom and Meeple Planet already go through Firecrawl for this reason. Ozon.gr's
search needs a key that lasts a day. The app reads it from Ozon's site, through
Firecrawl if Ozon refuses the request, which then costs one credit a day.

## 2. Usage analytics (Supabase)

The app can log anonymous usage events to Supabase for permanent analytics storage.

Open **SQL Editor** in Supabase and run the SQL from `supabase_usage_events.sql`.

Then add these to the Streamlit secrets:

```toml
SUPABASE_URL = "https://<your-project-ref>.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "<your-service-role-key>"
SUPABASE_EVENTS_TABLE = "usage_events"
```

Optional runtime flags:

```toml
BGB_USAGE_LOGGING = "1"
BGB_USAGE_LOCAL_FALLBACK = "1"
```

- `BGB_USAGE_LOGGING=0` disables analytics.
- `BGB_USAGE_LOCAL_FALLBACK=1` writes local JSONL when Supabase is unavailable.

### What gets logged

- One event per search action: `search`
- `status` is `completed` or `failed`
- Includes timestamp, anonymous session ID, query, and summary fields
  (duration, results, error count, selected store count), plus which stores
  returned results, had the game in stock, and were cheapest.
- One event per click on a store link: `click` (once click tracking is set up)

## 3. Click tracking

Store links can go through the `go` Edge Function, which logs the click and
forwards the visitor to the store. Clicks use the existing `usage_events` table,
so no database change is needed. No IP address or browser details are stored.

Until `CLICK_REDIRECT_URL` and `CLICK_SIGNING_SECRET` are both set, links go
straight to the store with UTM tags and clicks are not counted.

To set it up, generate a secret, then run the rest from the project folder.
`<your-project-ref>` is the first part of your `SUPABASE_URL`.

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
npx supabase login
npx supabase secrets set CLICK_SIGNING_SECRET=<generated-value> --project-ref <your-project-ref>
npx supabase functions deploy go --no-verify-jwt --use-api --project-ref <your-project-ref>
```

Then add the same secret to the Streamlit secrets:

```toml
CLICK_REDIRECT_URL = "https://<your-project-ref>.supabase.co/functions/v1/go"
CLICK_SIGNING_SECRET = "<generated-value>"
```

Open the app with `?internal=1` to keep your own testing out of the numbers.

### Troubleshooting

| What you see after clicking View | Cause |
|---|---|
| `Invalid link` | The secret in Streamlit and Supabase is not the same. |
| `Not configured` | `CLICK_SIGNING_SECRET` is missing from the Supabase secrets. |
| An error about a missing authorization header | The function was deployed without `--no-verify-jwt`. |
| The store opens but no click is saved | Check the `go` function logs in Supabase. |

## 4. Store reports

`supabase_store_report.sql` holds the per-store, missing-games and weekly reports.
Run each block on its own in the Supabase SQL Editor, after setting its dates.
