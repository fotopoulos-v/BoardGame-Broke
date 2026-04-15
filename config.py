import streamlit as st

FIRECRAWL_API_KEY = st.secrets["FIRECRAWL_API_KEY"]
EFANTASY_SESSION_ID = st.secrets["EFANTASY_SESSION_ID"]

# Optional overrides for Public Findbar API search.
# If left empty, code falls back to built-in defaults captured from observed traffic.
PUBLIC_FINDBAR_BEARER_TOKEN = ""
PUBLIC_FINDBAR_SESSION_ID = ""
