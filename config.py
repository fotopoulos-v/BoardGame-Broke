"""Runtime configuration.

No secrets are stored in this file — it is tracked in git. Values are resolved
at import time from, in order:

1. **Streamlit secrets** — ``.streamlit/secrets.toml`` when running locally, or
   the *Secrets* panel in the Streamlit Cloud app settings when deployed.
   ``.streamlit/`` is git-ignored, so nothing secret is ever committed.
2. **Environment variables** of the same name, for running the scraper outside
   Streamlit (plain ``python BoardGame-Broke.py``, tests, cron jobs).
"""

import os


def get_secret(key, default=""):
    """Return secret *key* from Streamlit secrets, falling back to the environment."""
    try:
        import streamlit as st
        if key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        # Streamlit missing, or no secrets file configured — fall through to env.
        pass
    return str(os.getenv(key, default)).strip()


FIRECRAWL_API_KEY = get_secret("FIRECRAWL_API_KEY")

# Optional overrides for Public Findbar API search.
# If left empty, code falls back to built-in defaults captured from observed traffic.
PUBLIC_FINDBAR_BEARER_TOKEN = get_secret("PUBLIC_FINDBAR_BEARER_TOKEN")
PUBLIC_FINDBAR_SESSION_ID = get_secret("PUBLIC_FINDBAR_SESSION_ID")
