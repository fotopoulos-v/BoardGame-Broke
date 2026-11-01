"""Outbound click tracking for store links.

Result links point at the ``go`` Supabase Edge Function, which logs the click
and forwards the visitor to the store. The link carries its details in a signed
token, so clicks cannot be forged and the function cannot be used to redirect
people to arbitrary sites. The signature format here must match
``supabase/functions/go/index.ts``.
"""

import base64
import hashlib
import hmac
import json
import math

UTM_PARAMS = "utm_source=boardgamebroke&utm_medium=referral&utm_campaign=price_compare"


def add_utm(url):
    """Append the UTM tags to *url* without re-encoding what is already there."""
    if not url or "utm_source=" in url:
        return url
    base, hash_sign, fragment = url.partition("#")
    joiner = "&" if "?" in base else "?"
    return f"{base}{joiner}{UTM_PARAMS}{hash_sign}{fragment}"


def build_redirect_url(redirect_url, secret, target_url, details):
    """Return a signed link that logs *details* and then opens *target_url*."""
    payload = json.dumps(
        {**details, "url": target_url},
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    token = base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")
    signature = hmac.new(secret.encode("utf-8"), token.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{redirect_url}?d={token}&sig={signature}"


def summarize_store_results(exact_matches, all_results, price_value):
    """Per-store facts for one search; *price_value* turns a price into a float."""
    exact_in_stock = [item for item in exact_matches if item.get("in_stock")]
    priced = [
        (price_value(item.get("price")), item["store"])
        for item in exact_in_stock
    ]
    priced = [(price, store) for price, store in priced if math.isfinite(price)]
    cheapest_price = min((price for price, _ in priced), default=None)
    return {
        "stores_with_results": sorted({item["store"] for item in all_results}),
        "exact_in_stock_stores": sorted({item["store"] for item in exact_in_stock}),
        "cheapest_in_stock_stores": sorted(
            {store for price, store in priced if price == cheapest_price}
        ),
        "cheapest_in_stock_price": cheapest_price,
    }
