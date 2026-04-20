import json
import re
from firecrawl import Firecrawl
from pydantic import BaseModel, Field
from typing import List
import urllib.parse
import os
from config import FIRECRAWL_API_KEY
import json
import html as _html

# List of apostrophe variants for retry logic
APOSTROPHE_VARIANTS = ['\'', '’', '`', '´', '‘', '′', '＇', '᾽', '᾿']
# Dash variants that should be treated as separators for retry logic
DASH_VARIANTS = ['-', '‐', '–', '—']


def strip_dash_variants(query):
    """Replace dash variants with spaces and collapse whitespace."""
    if not query:
        return ""
    cleaned = query
    for dash_char in DASH_VARIANTS:
        cleaned = cleaned.replace(dash_char, " ")
    return ' '.join(cleaned.split()).strip()

def normalize_for_match(text):
    """Normalize punctuation/whitespace for robust title matching."""
    if not text:
        return ""
    normalized = text.lower()
    for ap in APOSTROPHE_VARIANTS:
        normalized = normalized.replace(ap, "'")
    normalized = normalized.replace('–', ' ').replace('—', ' ')
    normalized = normalized.replace(':', ' ').replace('-', ' ')
    return ' '.join(normalized.split()).strip()

def _query_words_in_text(query_words, text_norm):
    """Check that every query word appears in *text_norm* as a whole word.

    Short words (≤3 chars) are matched with word boundaries to avoid false
    substring hits (e.g. "x" matching "Pax", "men" matching "Replacement").
    Longer words still use plain substring matching for flexibility.
    """
    if not query_words:
        return True
    text_word_set = set(text_norm.split())
    for w in query_words:
        if len(w) <= 3:
            # Short word: require exact whole-word presence
            if w not in text_word_set:
                return False
        else:
            if w not in text_norm:
                return False
    return True

def format_price_for_output(price_value):
    """Format price for UI/export; return 'N/A' when missing or invalid."""
    if price_value is None:
        return "N/A"
    if isinstance(price_value, str):
        val = price_value.strip()
        if not val or val.upper() == "N/A":
            return "N/A"
        try:
            return f"{float(val):.2f}"
        except ValueError:
            return "N/A"
    try:
        return f"{float(price_value):.2f}"
    except (TypeError, ValueError):
        return "N/A"

def price_sort_value(price_value):
    """Sort helper: non-numeric prices go to the end."""
    if price_value is None:
        return float('inf')
    if isinstance(price_value, str):
        val = price_value.strip()
        if not val or val.upper() == "N/A":
            return float('inf')
        try:
            return float(val)
        except ValueError:
            return float('inf')
    try:
        return float(price_value)
    except (TypeError, ValueError):
        return float('inf')

# Initialize
app = Firecrawl(api_key=FIRECRAWL_API_KEY)

class BoardGame(BaseModel):
    name: str = Field(description="The full name of the board game product.")
    price: float = Field(description="The price in Euros.")
    is_in_stock: bool = Field(description="Availability status.")
    url: str = Field(description="The specific product page URL.")

class GameSearchResults(BaseModel):
    products: List[BoardGame]

def try_apostrophe_variants(original_query, store_name, content, combined_data):
    """Helper function to try different apostrophe variants when no results are found"""
    # Helper to get products for a store + query overlaying both HTML and API sources (eFantasy)
    def _get_products(store_name, query, content):
        if store_name == "The Game Rules":
            return parse_thegamerules_html(content, query)
        elif store_name == "epitrapez.io":
            return parse_epitrapezio_html(content, query)
        elif store_name == "Fantasy Shop":
            return parse_fantasyshop_html(content, query)
        elif store_name == "Nerdom":
            return parse_nerdom_html(content, query)
        elif store_name == "Ozon.gr":
            return search_ozon(query)
        elif store_name == "Gaming Galaxy":
            return search_gaminggalaxy(query)
        elif store_name == "Meeple On Board":
            return parse_meepleonboard_html(content, query)
        elif store_name == "No Label X":
            return parse_nolabelx_html(content, query)
        elif store_name == "Lex Hobby Store":
            return parse_lexhobby_html(content, query)
        elif store_name == "SoHotTCG":
            return parse_sohottcg_html(content, query)
        elif store_name == "Tech City":
            return parse_techcity_html(content, query)
        elif store_name == "Game Theory":
            return parse_gametheory_html(content, query)
        elif store_name == "Mystery Bay":
            return parse_mysterybay_html(content, query)
        elif store_name == "Meeple Planet":
            return search_meepleplanet(query)
        elif store_name == "Boards of Madness":
            return parse_boardsofmadness_html(content, query)
        elif store_name == "GamesUniverse":
            return parse_gamesuniverse_html(content, query)
        elif store_name == "RollnPlay":
            return search_rollnplay(query)
        elif store_name == "PlayceShop":
            return parse_playceshop_html(content, query)
        elif store_name == "VP shop":
            return parse_vpshop_html(content, query)
        elif store_name == "Politeia":
            return parse_politeia_html(content, query)
        elif store_name == "Crystal Lotus":
            return search_crystallotus(query)
        elif store_name == "Kaissa":
            return parse_kaissa_html(content, query)
        elif store_name == "Gaming Galaxy":
            return parse_gaminggalaxy_html(content, query)
        elif store_name == "The Dragonphoenix Inn":
            return search_dragonphoenixinn(query)
        elif store_name == "GenX":
            return parse_genx_html(content, query)
        elif store_name == "eFantasy":
            return search_efantasy(query)
        elif store_name == "Public":
            return search_public(query)
        return []
    from copy import deepcopy

    # Make a copy of the original query to work with
    temp_query = original_query

    # First, try each apostrophe variant in order
    for ap_char in APOSTROPHE_VARIANTS:
        # Replace all apostrophe variants with the current one
        modified_query = original_query
        for ap_variant in APOSTROPHE_VARIANTS:
            modified_query = modified_query.replace(ap_variant, ap_char)

        # Skip if the query didn't change
        if modified_query == original_query:
            continue

        # Try the modified query
        retry_products = []
        if store_name == "The Game Rules":
            retry_products = parse_thegamerules_html(content, modified_query)
        elif store_name == "epitrapez.io":
            retry_products = parse_epitrapezio_html(content, modified_query)
        elif store_name == "Fantasy Shop":
            retry_products = parse_fantasyshop_html(content, modified_query)
        elif store_name == "Nerdom":
            retry_products = parse_nerdom_html(content, modified_query)
        elif store_name == "Ozon.gr":
            retry_products = search_ozon(modified_query)
        elif store_name == "Meeple On Board":
            retry_products = parse_meepleonboard_html(content, modified_query)
        elif store_name == "No Label X":
            retry_products = parse_nolabelx_html(content, modified_query)
        elif store_name == "Lex Hobby Store":
            retry_products = parse_lexhobby_html(content, modified_query)
        elif store_name == "SoHotTCG":
            retry_products = parse_sohottcg_html(content, modified_query)
        elif store_name == "Tech City":
            retry_products = parse_techcity_html(content, modified_query)
        elif store_name == "Game Theory":
            retry_products = parse_gametheory_html(content, modified_query)
        elif store_name == "Mystery Bay":
            retry_products = parse_mysterybay_html(content, modified_query)
        elif store_name == "Meeple Planet":
            retry_products = search_meepleplanet(modified_query)
        elif store_name == "Boards of Madness":
            retry_products = parse_boardsofmadness_html(content, modified_query)
        elif store_name == "GamesUniverse":
            retry_products = parse_gamesuniverse_html(content, modified_query)
        elif store_name == "RollnPlay":
            retry_products = search_rollnplay(modified_query)
        elif store_name == "PlayceShop":
            retry_products = parse_playceshop_html(content, modified_query)
        elif store_name == "VP shop":
            retry_products = parse_vpshop_html(content, modified_query)
        elif store_name == "Politeia":
            retry_products = parse_politeia_html(content, modified_query)
        elif store_name == "Crystal Lotus":
            retry_products = search_crystallotus(modified_query)
        elif store_name == "Kaissa":
            retry_products = parse_kaissa_html(content, modified_query)
        elif store_name == "Gaming Galaxy":
            retry_products = parse_gaminggalaxy_html(content, modified_query)
        elif store_name == "The Dragonphoenix Inn":
            retry_products = search_dragonphoenixinn(modified_query)
        elif store_name == "GenX":
            retry_products = parse_genx_html(content, modified_query)
        elif store_name == "Public":
            retry_products = search_public(modified_query)

        if retry_products:
            # Process the results
            valid_count = 0
            exact_count = 0
            seen_urls = set(item['url'] for item in combined_data['all_results'] if item['store'] == store_name)

            for p in retry_products:
                if isinstance(p, dict):
                    p_name = p.get('name', '')
                    p_price = p.get('price', 0.0)
                    p_stock = p.get('is_in_stock', False)
                    p_url = p.get('url', '')
                else:
                    p_name = getattr(p, 'name', '')
                    p_price = getattr(p, 'price', 0.0)
                    p_stock = getattr(p, 'is_in_stock', False)
                    p_url = getattr(p, 'url', '')

                if p_url in seen_urls:
                    continue
                seen_urls.add(p_url)

                # Normalize for comparison
                p_name_normalized = normalize_for_match(p_name)
                modified_query_normalized = normalize_for_match(modified_query)

                # Store-specific comparison
                if store_name == "Ozon.gr":
                    comparison_name = sanitize_ozon_name(p_name)
                    target_query = sanitize_ozon_name(modified_query)
                elif store_name == "eFantasy":
                    comparison_name = sanitize_efantasy_name(p_name)
                    target_query = sanitize_efantasy_name(modified_query)
                elif store_name == "Public":
                    comparison_name = sanitize_public_name(p_name)
                    target_query = sanitize_public_name(modified_query)
                elif store_name in ["No Label X", "SoHotTCG", "Tech City", "Game Theory", "Lex Hobby Store"]:
                    comparison_name = normalize_for_match(sanitize_nolabelx_name(p_name) if store_name != "Lex Hobby Store" else sanitize_lexhobby_name(p_name))
                    target_query = normalize_for_match(modified_query)
                else:
                    comparison_name = p_name_normalized
                    target_query = modified_query_normalized

                # Check if it matches
                if target_query in comparison_name or target_query in p_name_normalized:
                    product_entry = {
                        "name": p_name,
                        "url": p_url,
                        "in_stock": p_stock,
                        "price": format_price_for_output(p_price),
                        "store": store_name
                    }

                    combined_data["all_results"].append(product_entry)
                    valid_count += 1

                    if comparison_name == target_query:
                        combined_data["exact_matches"].append(product_entry)
                        exact_count += 1

            if valid_count > 0:
                combined_data["store_stats"][store_name] = {"total": valid_count, "exact": exact_count}
                return True  # Found results, stop trying other variants

    # If no apostrophe variant worked, try removing all apostrophes
    query_no_apostrophes = original_query
    for ap_char in APOSTROPHE_VARIANTS:
        query_no_apostrophes = query_no_apostrophes.replace(ap_char, "")
    query_no_apostrophes = query_no_apostrophes.strip()

    # Skip if the query didn't change
    if query_no_apostrophes == original_query:
        return False

    # Try the query without any apostrophes
    retry_products = []
    retry_products = _get_products(store_name, query_no_apostrophes, content)

    if retry_products:
        # Process the results
        valid_count = 0
        exact_count = 0
        seen_urls = set(item['url'] for item in combined_data['all_results'] if item['store'] == store_name)

        for p in retry_products:
            if isinstance(p, dict):
                p_name = p.get('name', '')
                p_price = p.get('price', 0.0)
                p_stock = p.get('is_in_stock', False)
                p_url = p.get('url', '')
            else:
                p_name = getattr(p, 'name', '')
                p_price = getattr(p, 'price', 0.0)
                p_stock = getattr(p, 'is_in_stock', False)
                p_url = getattr(p, 'url', '')

            if p_url in seen_urls:
                continue
            seen_urls.add(p_url)

            # Normalize for comparison
            p_name_normalized = normalize_for_match(p_name)
            no_apostrophes_normalized = normalize_for_match(query_no_apostrophes)

            # Store-specific comparison
            if store_name == "Ozon.gr":
                comparison_name = sanitize_ozon_name(p_name)
                target_query = sanitize_ozon_name(query_no_apostrophes)
            elif store_name == "eFantasy":
                comparison_name = sanitize_efantasy_name(p_name)
                target_query = sanitize_efantasy_name(query_no_apostrophes)
            elif store_name == "Public":
                comparison_name = sanitize_public_name(p_name)
                target_query = sanitize_public_name(query_no_apostrophes)
            elif store_name in ["No Label X", "SoHotTCG", "Tech City", "Game Theory", "Lex Hobby Store"]:
                comparison_name = normalize_for_match(sanitize_nolabelx_name(p_name) if store_name != "Lex Hobby Store" else sanitize_lexhobby_name(p_name))
                target_query = normalize_for_match(query_no_apostrophes)
            else:
                comparison_name = p_name_normalized
                target_query = no_apostrophes_normalized

            # Check if it matches
            if target_query in comparison_name or target_query in p_name_normalized:
                product_entry = {
                    "name": p_name,
                    "url": p_url,
                    "in_stock": p_stock,
                    "price": format_price_for_output(p_price),
                    "store": store_name
                }

                combined_data["all_results"].append(product_entry)
                valid_count += 1

                if comparison_name == target_query:
                    combined_data["exact_matches"].append(product_entry)
                    exact_count += 1

        if valid_count > 0:
            combined_data["store_stats"][store_name] = {"total": valid_count, "exact": exact_count}
            return True

    return False

# Fallback HTML parser for ozon
def sanitize_ozon_name(raw_name):
    """Clean Ozon.gr product names for better matching"""
    if not raw_name: return ""
    name = raw_name.lower().replace('–', ' ').replace('—', ' ')
    prefixes = ["επέκταση επιτραπέζιου παιχνιδιού", "επιτραπέζιο παιχνίδι για δύο", "επιτραπέζιο παιχνίδι", "επέκταση"]
    for prefix in prefixes:
        if name.startswith(prefix):
            name = name[len(prefix):].strip()

    # Remove Greek descriptive suffix after the last dash (e.g. "Spirit Island-Στρατηγικό" → "Spirit Island")
    # Only strip if the part after the last dash contains Greek characters
    last_dash = name.rfind('-')
    if last_dash != -1:
        suffix = name[last_dash + 1:].strip()
        if suffix and re.search(r'[α-ωΑ-Ωά-ώΆ-Ώ]', suffix):
            name = name[:last_dash].strip()

    # Replace remaining dashes with spaces for comparison
    name = name.replace('-', ' ')

    noise_patterns = [
        r'\(.*?\)', r'\(.*$', r'\s+θεματικό.*$', r'\s+συνεργατικό.*$',
        r'\s+στρατηγικής.*$', r'\s+παρέας.*$', r'\s+kickstarter.*$',
        r'\s+deluxe edition.*$', r'\s+reset pack.*$', r'\s+adventurer\'s pledge.*$'
    ]
    for pattern in noise_patterns:
        name = re.sub(pattern, '', name).strip()

    name = re.sub(r'[:\.\!\+]+', '', name)
    return ' '.join(name.split()).strip()

# Sanitizer for eFantasy
def sanitize_efantasy_name(raw_name):
    """Clean eFantasy.gr product names"""
    if not raw_name: return ""
    name = raw_name.lower()
    prefixes = ["επιτραπέζιο παιχνίδι", "επέκταση"]
    for prefix in prefixes:
        if name.startswith(prefix):
            name = name[len(prefix):].strip()
    return ' '.join(name.split()).strip()

def sanitize_public_name(raw_name):
    """Normalize Public titles by stripping trailing 'Επιτραπέζιο (Brand)' suffix."""
    if not raw_name:
        return ""
    name = _html.unescape(str(raw_name)).strip()
    name = re.sub(r'\s+επιτραπέζιο\s*\([^)]*\)\s*$', '', name, flags=re.IGNORECASE)
    return normalize_for_match(name)

# Fallback HTML parser for eFantasy
def parse_efantasy_html(content, game_query):
    """HTML parser for eFantasy - parses Findbar API response"""
    if not content:
        return []
    products = []
    seen_urls = set()

    # Split into individual product blocks by fbr-result-container
    block_starts = [m.start() for m in re.finditer(
        r'<div class="fbr-result-container', content
    )]

    if not block_starts:
        return []

    blocks = []
    for i, start in enumerate(block_starts):
        end = block_starts[i+1] if i+1 < len(block_starts) else len(content)
        blocks.append(content[start:end])

    for block in blocks:
        # Name from product-title div
        name_match = re.search(
            r'<div class="product-title">\s*<a[^>]*>([\s\S]+?)</a>\s*</div>',
            block, re.IGNORECASE
        )
        if not name_match:
            continue
        # name = ' '.join(name_match.group(1).replace('\n', ' ').split())
        name = _html.unescape(' '.join(name_match.group(1).replace('\n', ' ').split()))

        if game_query.lower() not in name.lower():
            continue

        # URL from product-title link
        url_match = re.search(
            r'<div class="product-title">\s*<a href="(https://www\.efantasy\.gr/[^"]+)"',
            block, re.IGNORECASE
        )
        if not url_match:
            continue
        url = url_match.group(1)

        # Keep only board-game category products
        if not url.startswith("https://www.efantasy.gr/el/προϊόντα/επιτραπέζια-παιχνίδια/"):
            continue

        if url in seen_urls:
            continue
        seen_urls.add(url)

        # Price from <strong>
        price_match = re.search(r'<strong>([\d,]+)€</strong>', block, re.IGNORECASE)
        if not price_match:
            continue
        try:
            price = float(price_match.group(1).replace(',', '.'))
        except ValueError:
            continue

        # Stock detection — three cases:
        # 1. data-label="preorder" → preorder → out of stock
        # 2. Διαθέσιμα: N+ or Διαθέσιμα: N → in stock if N > 0
        # 3. Προπαραγγελία → out of stock

        if 'data-label="preorder"' in block:
            in_stock = False
        else:
            stock_match = re.search(
                r'Διαθέσιμα:\s*(\d+)\+?',
                block, re.IGNORECASE
            )
            preorder_match = re.search(r'Προπαραγγελία', block, re.IGNORECASE)
            if stock_match:
                in_stock = int(stock_match.group(1)) > 0
            elif preorder_match:
                in_stock = False
            else:
                in_stock = False

        products.append({
            'name': name,
            'price': price,
            'is_in_stock': in_stock,
            'url': url
        })

    return products

# ------ efantasy.gr SECTION ------- #
# This is based on the analysis of findbar.js and the structure of eFantasy's pages.
# It includes a request_key generator and an HTML parser that can handle both search
# results and direct product pages, with robust stock detection.
def _efantasy_request_key(query, session_id):
    """Generate Findbar request_key using the algorithm from findbar.js:
    ce(m, _, T) = md5(md5(m + '|' + sorted_params) + T)
    where m='efantasy.gr', T='y0YIfLTE8g'
    """
    import hashlib, urllib.parse
    def md5(s):
        return hashlib.md5(s.encode('utf-8')).hexdigest()
    params = urllib.parse.urlencode({
        'αναζήτηση': query,
        'initial_request': '1',
        'session_id': session_id,
    }, encoding='utf-8')
    parsed = urllib.parse.parse_qsl(params)
    parsed.sort(key=lambda x: x[0])
    sorted_params = urllib.parse.urlencode(parsed, encoding='utf-8')
    inner = md5('efantasy.gr|' + sorted_params)
    return md5(inner + 'y0YIfLTE8g')

def search_efantasy(game_query):
    """Search eFantasy directly via Findbar API"""
    import requests as _requests
    from config import EFANTASY_SESSION_ID

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:148.0) Gecko/20100101 Firefox/148.0",
        "Accept": "*/*",
        "Accept-Language": "el-GR,el;q=0.9",
        "Origin": "https://www.efantasy.gr",
        "Referer": "https://www.efantasy.gr/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "Cache-Control": "no-cache",
    }

    # Try to get session_id — first from config/secrets, then by requesting one
    session_id = ""

    # Check Streamlit secrets first (for cloud deployment)
    try:
        import streamlit as st
        session_id = st.secrets.get("EFANTASY_SESSION_ID", "")
    except Exception:
        pass

    # Fall back to config.py (for local deployment)
    if not session_id:
        session_id = EFANTASY_SESSION_ID

    # Last resort: try to get one from Findbar directly
    if not session_id:
        try:
            r0 = _requests.get(
                "https://app.findbar.io/search/efantasy.gr/full",
                params={"αναζήτηση": game_query, "initial_request": "1"},
                headers=headers,
                timeout=15
            )
            session_id = r0.headers.get('x-session-id', '')
        except Exception:
            pass

    if not session_id:
        return []
    print("SESSION ID USED:", session_id)
    # Generate request_key and search
    request_key = _efantasy_request_key(game_query, session_id)
    print("request key USED:", request_key)
    try:
        r = _requests.get(
            "https://app.findbar.io/search/efantasy.gr/full",
            params={
                "αναζήτηση": game_query,
                "initial_request": "1",
                "session_id": session_id,
                "request_key": request_key,
            },
            headers=headers,
            timeout=15
        )
        if r.status_code != 200:
            return []
        return parse_efantasy_html(r.text, game_query)
    except Exception:
        return []




def parse_public_html(content, game_query):
    """Parse Public Findbar JSON results and keep only board-game products."""
    if not content:
        return []

    try:
        payload = json.loads(content)
    except Exception:
        return []

    hits = payload.get("results", {}).get("hits", [])
    if not isinstance(hits, list):
        return []

    products = []
    seen_urls = set()
    query_norm = normalize_for_match(_html.unescape(game_query))
    query_words = query_norm.split()

    for hit in hits:
        source = hit.get("source", {}) if isinstance(hit, dict) else {}
        rel_url = str(source.get("url", "") or "").strip()
        if not rel_url:
            continue

        # Keep only board games as requested.
        if "/product/kids-and-toys/board-games" not in rel_url:
            continue

        name = _html.unescape(str(source.get("displayName", "") or "")).strip()
        if not name:
            continue

        name_norm = normalize_for_match(name)
        if not _query_words_in_text(query_words, name_norm):
            continue

        abs_url = rel_url if rel_url.startswith("http") else f"https://www.public.gr{rel_url}"
        if abs_url in seen_urls:
            continue
        seen_urls.add(abs_url)

        availability_text = str(source.get("availability", "") or "").strip().lower()
        in_stock_flag = bool(source.get("inStock", False))
        buy_button = bool(source.get("buyButton", False))

        # Public's API may mark some partner items with inconsistent inStock/isActive
        # while the textual availability clearly says they are available.
        unavailable_markers = [
            "μη διαθέσιμο",
            "εξαντλη",
            "out of stock",
            "unavailable",
        ]
        preorder_markers = [
            "προπαραγγελία",
            "preorder",
        ]
        available_markers = [
            "διαθέσιμο",
            "διαθεσιμο",
            "άμεσα διαθέσιμο",
            "διαθέσιμο για αποστολή",
            "διαθέσιμο με παραγγελία",
            "διαθέσιμο από public partner",
            "διαθέσιμο μόνο online"
        ]

        is_unavailable = any(marker in availability_text for marker in unavailable_markers)
        is_preorder = any(marker in availability_text for marker in preorder_markers)
        has_available_text = any(marker in availability_text for marker in available_markers)

        if is_unavailable or is_preorder:
            in_stock = False
        elif in_stock_flag or has_available_text or buy_button:
            in_stock = True
        else:
            in_stock = False

        price_value = (
            source.get("salePrice")
            if source.get("salePrice") is not None
            else source.get("finalPrice")
        )
        if price_value is None:
            price_value = source.get("listPrice")
        if price_value is None:
            price_value = source.get("storePriceFullVat")

        products.append({
            "name": name,
            "price": price_value,
            "is_in_stock": in_stock,
            "url": abs_url,
        })

    return products


def search_public(game_query):
    """Search Public directly through Findbar API and parse board-game results."""
    import requests as _requests

    try:
        from config import PUBLIC_FINDBAR_BEARER_TOKEN, PUBLIC_FINDBAR_SESSION_ID
    except Exception:
        PUBLIC_FINDBAR_BEARER_TOKEN = ""
        PUBLIC_FINDBAR_SESSION_ID = ""

    bearer_token = ""
    session_id = ""

    # Check Streamlit secrets first (for cloud deployment).
    try:
        import streamlit as st
        bearer_token = st.secrets.get("PUBLIC_FINDBAR_BEARER_TOKEN", "")
        session_id = st.secrets.get("PUBLIC_FINDBAR_SESSION_ID", "")
    except Exception:
        pass

    if not bearer_token:
        bearer_token = PUBLIC_FINDBAR_BEARER_TOKEN
    if not session_id:
        session_id = PUBLIC_FINDBAR_SESSION_ID

    # Fallbacks from observed network calls.
    if not bearer_token:
        bearer_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjp7IndlYnNpdGVJZCI6MTUwLCJkb21haW4iOiJwdWJsaWMuZ3IifSwiaWF0IjoxNzMyODgzMDI1LCJleHAiOjE4Mjc1NTU4MjUsImlzcyI6ImZpbmRiYXIuaW8ifQ.peqkMxCkNbE6TeNC-gSLHsiRpZL7cYWv2iOhC9uTBj4"
    if not session_id:
        session_id = "Y12JDS-6L9dZXg65C4x8Hc62gACo2nNl"

    if not bearer_token:
        return []

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:149.0) Gecko/20100101 Firefox/149.0",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://www.public.gr",
        "Referer": "https://www.public.gr/",
        "Authorization": f"Bearer {bearer_token}",
    }

    products = []
    seen_urls = set()

    # Fetch a few pages to avoid missing valid results on later pages.
    for page in range(1, 4):
        payload = {
            "query": game_query,
            "filters": [],
            "session_id": session_id,
            "initial": False,
            "page": page,
            "size": 36,
            "sort": "_score",
            "dir": "desc",
        }
        try:
            response = _requests.post(
                "https://app.findbar.io/api/v1/search",
                json=payload,
                headers=headers,
                timeout=15,
            )
            if response.status_code != 200:
                break
        except Exception:
            break

        page_products = parse_public_html(response.text, game_query)
        if not page_products:
            if page == 1:
                return []
            break

        added_this_page = 0
        for p in page_products:
            p_url = p.get("url", "")
            if not p_url or p_url in seen_urls:
                continue
            seen_urls.add(p_url)
            products.append(p)
            added_this_page += 1

        if added_this_page == 0:
            break

    return products

# Non-board-game product-type keywords for The Game Rules.
# Products whose names contain any of these are filtered out.
_THEGAMERULES_EXCLUDE_KEYWORDS = [
    "pop!",
    "funko",
    "action figure",
    "action figures",
    "vinyl figure",
    "statue",
    "q-fig",
    "mug ",          # trailing space avoids matching inside words
    " mug",          # leading space catches end-of-phrase too
    "t-shirt",
    "iron studios",
]

def _is_thegamerules_boardgame(name):
    """Return True if a The Game Rules product name looks like a board game."""
    if not name:
        return False
    lower = name.lower()
    return not any(kw in lower for kw in _THEGAMERULES_EXCLUDE_KEYWORDS)

# Fallback HTML parser for The Game Rules
def parse_thegamerules_html(content, game_query):
    """Robust parser for The Game Rules: Handles Preorders, Sale Prices, and fuzzy titles."""
    products = []
    seen_urls = set()
    query_norm = normalize_for_match(_html.unescape(game_query))
    query_words = query_norm.split()

    def _extract_price(block_text):
        """Prefer discounted/current price when both old and new prices exist."""
        if not block_text:
            return None

        text = _html.unescape(block_text)

        # Most reliable: explicit sale/new price class.
        sale_match = re.search(r'class="price-new"[^>]*>\s*(\d+[\.,]\d{2})\s?€', text, re.IGNORECASE)
        if sale_match:
            return float(sale_match.group(1).replace(',', '.'))

        # Current price in storefront scripts (used in source HTML snippets).
        script_price_match = re.search(r'"price"\s*:\s*"(\d+[\.,]\d{2})"', text, re.IGNORECASE)
        if script_price_match:
            return float(script_price_match.group(1).replace(',', '.'))

        # Remove Ex Tax fragments so they don't get mistaken for main price.
        text_no_tax = re.sub(r'ex\s*tax\s*:?\s*\d+[\.,]\d{2}\s?€?', ' ', text, flags=re.IGNORECASE)

        # Flat content (markdown/text) often has: old_price then new_price.
        pair_match = re.search(r'(\d+[\.,]\d{2})\s?€\s+(\d+[\.,]\d{2})\s?€', text_no_tax)
        if pair_match:
            first = float(pair_match.group(1).replace(',', '.'))
            second = float(pair_match.group(2).replace(',', '.'))
            if second <= first:
                return second
            return first

        # Regular price when no sale exists.
        regular_match = re.search(r'class="price"[^>]*>.*?(\d+[\.,]\d{2})\s?€', text, re.DOTALL | re.IGNORECASE)
        if regular_match:
            return float(regular_match.group(1).replace(',', '.'))

        normal_match = re.search(r'class="price-normal"[^>]*>\s*(\d+[\.,]\d{2})\s?€', text, re.IGNORECASE)
        if normal_match:
            return float(normal_match.group(1).replace(',', '.'))

        # Fallback to any visible price token.
        all_prices = [
            float(m.group(1).replace(',', '.'))
            for m in re.finditer(r'(\d+[\.,]\d{2})\s?€', text_no_tax)
        ]

        if all_prices:
            if len(all_prices) >= 2 and all_prices[1] <= all_prices[0]:
                return all_prices[1]
            return all_prices[0]

        return None

    # 1. Split the markdown/content into chunks based on the product link pattern
    # This prevents one product from 'swallowing' another in the regex.
    blocks = re.split(r'\((https://thegamerules\.com/[^/\)\s\]]+)\)', content)

    # re.split with a group returns: [text, url, text, url...]
    # We iterate through the URLs found
    for i in range(1, len(blocks), 2):
        url = blocks[i]
        # The text belonging to this URL is actually in the block BEFORE it (the name)
        # and the block AFTER it (the price and stock status)
        prev_block = blocks[i-1]
        next_block = blocks[i+1] if i+1 < len(blocks) else ""

        # Skip junk URLs
        if any(x in url for x in ['image/cache', 'login', 'cart', 'wishlist', 'contact']):
            continue
        if url in seen_urls:
            continue

        # 2. Extract Name
        # Look for the last [bracketed text] in the previous block
        name_match = re.search(r'\[([^\]]+)\]$', prev_block.strip())
        if not name_match:
            continue
        name = name_match.group(1).strip()

        # 3. Extract Price
        # Prefer discounted/current price over old price when both exist.
        price_val = _extract_price(prev_block + " " + next_block)
        if price_val is None:
            continue

        # 4. Extract Stock Status
        # Check both the previous and next blocks for status keywords
        context = (prev_block + " " + next_block).lower()

        is_preorder = 'preorder' in context
        is_oos = 'out of stock' in context or 'εξαντλημένο' in context
        is_in_stock = 'in stock' in context or 'σε απόθεμα' in context or is_preorder

        # 5. Matching Logic (Fuzzy)
        # Check if all normalized query words are in the normalized title.
        name_norm = normalize_for_match(name)
        if not _query_words_in_text(query_words, name_norm):
            continue

        if not _is_thegamerules_boardgame(name):
            continue

        display_name = name
        if is_preorder:
            display_name = f"[Preorder] {name}"

        products.append({
            'name': display_name,
            'price': price_val,
            'is_in_stock': is_in_stock and not is_oos,
            'url': url
        })
        seen_urls.add(url)

    # Also parse raw HTML/source blocks, even when markdown parsing found results,
    # because Firecrawl output can be partial and miss products in one representation.
    html_pattern = re.compile(
        r'<div class="name">\s*<a href="(https://thegamerules\.com/[^"]+)"[^>]*>([^<]+)</a>\s*</div>',
        re.IGNORECASE
    )

    for match in html_pattern.finditer(content):
        raw_url = match.group(1).strip()
        url = _html.unescape(raw_url)
        if any(x in url for x in ['image/cache', 'login', 'cart', 'wishlist', 'contact']):
            continue
        if url in seen_urls:
            continue

        name = _html.unescape(' '.join(match.group(2).split()))
        name_norm = normalize_for_match(name)
        if not _query_words_in_text(query_words, name_norm):
            continue

        if not _is_thegamerules_boardgame(name):
            continue

        # Price and stock usually appear near the product name block.
        local_start = max(0, match.start() - 1200)
        local_end = min(len(content), match.end() + 2200)
        local_context = content[local_start:local_end]

        price_val = _extract_price(local_context)
        if price_val is None:
            continue

        context_lower = local_context.lower()
        is_preorder = 'preorder' in context_lower or 'προπαραγγελία' in context_lower
        is_oos = 'out of stock' in context_lower or 'εξαντλημένο' in context_lower
        is_in_stock = (
            'in stock' in context_lower or
            'σε απόθεμα' in context_lower or
            'c--stock-label' in context_lower or
            is_preorder
        )

        display_name = f"[Preorder] {name}" if is_preorder else name
        products.append({
            'name': display_name,
            'price': price_val,
            'is_in_stock': is_in_stock and not is_oos,
            'url': url
        })
        seen_urls.add(url)

    return products

# Fallback HTML parser for boardsofmadness
def parse_boardsofmadness_html(content, game_query):
    if not content:
        return []
    products = []
    query_clean = normalize_for_match(_html.unescape(game_query))
    query_words = query_clean.split()

    def clean_price(price_str):
        cleaned = re.sub(r'[^0-9,.]', '', price_str)
        cleaned = cleaned.replace(',', '.')
        return float(cleaned.rstrip('.'))

    def extract_product_url(source_text, product_name=""):
        """Resolve the real product URL from redirected single-product pages."""
        url_patterns = [
            r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']',
            r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']',
            r'<meta[^>]+property=["\']og:url["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:url["\']',
            r'"url"\s*:\s*"((?:https?:)?//boardsofmadness\.com/product/[^"\\]+)"',
            r'"@id"\s*:\s*"((?:https?:)?//boardsofmadness\.com/product/[^"#\\]+)"',
        ]

        for pattern in url_patterns:
            url_match = re.search(pattern, source_text, re.IGNORECASE)
            if url_match:
                candidate = _html.unescape(url_match.group(1)).replace('\\/', '/').strip()
                if candidate.startswith('//'):
                    candidate = f"https:{candidate}"
                if candidate.startswith('http'):
                    return candidate.split('#', 1)[0]

        if product_name:
            product_name_pattern = re.escape(product_name).replace(r'\ ', r'\s+')
            markdown_match = re.search(
                rf'\[{product_name_pattern}\]\((https://boardsofmadness\.com/product/[^)\s#]+)',
                source_text,
                re.IGNORECASE,
            )
            if markdown_match:
                return _html.unescape(markdown_match.group(1)).strip()

        # Safe fallback: keep the working Boards search URL instead of guessing a slug.
        return f"https://boardsofmadness.com/?s={urllib.parse.quote_plus(game_query)}&post_type=product&dgwt_wcas=1"

    # ─────────────────────────────────────────────────────────────────────────
    # CASE 1: SINGLE PRODUCT PAGE (The "Lands of Galzyr" Case)
    # ─────────────────────────────────────────────────────────────────────────
    # Check for the specific single-product indicators
    if 'product_title' in content or 'et_pb_wc_title' in content or 'stock in-stock' in content:
        # 1. Extract Name (Look for H1 or et_pb_wc_title)
        name_match = re.search(r'<h1[^>]*>([^<]+)</h1>', content, re.IGNORECASE)
        if not name_match:
            name_match = re.search(r'class="[^"]*et_pb_wc_title[^"]*".*?<h[1-6][^>]*>([^<]+)</h[1-6]>', content, re.DOTALL | re.IGNORECASE)

        if name_match:
            name = _html.unescape(' '.join(name_match.group(1).split()))

            # 2. Extract Price (Look for current price, skipping original if on sale)
            price_match = re.search(r'<ins[^>]*>.*?<bdi>.*?([\d,.]+).*?</bdi>', content, re.DOTALL)
            if not price_match:
                price_match = re.search(r'<bdi>.*?([\d,.]+).*?</bdi>', content, re.DOTALL)

            # 3. Extract URL from canonical/og:url/schema/markdown, with a safe search fallback.
            product_url = extract_product_url(content, name)

            # 4. Availability (Using your "stock in-stock" tip)
            # Item is in stock if we see "in-stock" or the "Add to Cart" button
            in_stock = (
                'class="stock in-stock"' in content or
                'Σε απόθεμα' in content or
                'Προσθήκη στο καλάθι' in content or
                'name="add-to-cart"' in content
            )

            name_norm = normalize_for_match(name)
            if price_match and _query_words_in_text(query_words, name_norm):
                try:
                    products.append({
                        'name': name,
                        'price': clean_price(price_match.group(1)),
                        'is_in_stock': in_stock,
                        'url': product_url
                    })
                    return products # Found the specific redirected page, stop here
                except ValueError:
                    pass

    # ─────────────────────────────────────────────────────────────────────────
    # CASE 2: SEARCH RESULTS LIST (Multiple Products)
    # ─────────────────────────────────────────────────────────────────────────
    seen_urls = set()
    raw_blocks = content.split('<li class="product')

    for block in raw_blocks:
        if 'woocommerce-loop-product__title' not in block:
            continue

        name_match = re.search(r'class="woocommerce-loop-product__title">([^<]+)</h2>', block)
        url_match = re.search(r'href="(https://boardsofmadness\.com/product/[^"]+)"', block)
        # Look for price - prioritize sale <ins> if present in the block
        price_match = re.search(r'<ins[^>]*>.*?<bdi>(?:<span[^>]*>)?(?:&euro;|€)(?:</span>)?\s*([\d,.]+)</bdi>', block, re.DOTALL)
        if not price_match:
            price_match = re.search(r'<bdi>(?:<span[^>]*>)?(?:&euro;|€)(?:</span>)?\s*([\d,.]+)</bdi>', block, re.DOTALL)

        if not name_match or not url_match or not price_match:
            continue

        name = _html.unescape(' '.join(name_match.group(1).split()))
        url = url_match.group(1)

        name_norm = normalize_for_match(name)
        if not _query_words_in_text(query_words, name_norm) or url in seen_urls:
            continue
        seen_urls.add(url)

        # Your working stock logic
        is_oos_by_text = 'Εξαντλημένο' in block or 'Διαβάστε περισσότερα' in block
        is_oos_by_class = 'ast-shop-product-out-of-stock' in block or 'outofstock' in block.lower()
        has_cart_button = 'Προσθήκη στο καλάθι' in block or 'add_to_cart_button' in block
        if is_oos_by_text or is_oos_by_class:
            in_stock = False
        else:
            in_stock = True

        try:
            products.append({
                'name': name,
                'price': clean_price(price_match.group(1)),
                'is_in_stock': in_stock,
                'url': url
            })
        except (ValueError, IndexError):
            continue

    return products

# Fallback HTML parser for Epitrapez.io
def parse_epitrapezio_html(content, game_query):
    """HTML parser for epitrapez.io."""
    if not content:
        return []

    def _is_boardgame_related_epitrapezio_product(product_url, name, block_html):
        """Keep board/card games and expansions, reject collectibles like figures."""
        product_url_l = (product_url or '').lower()
        name_l = (name or '').lower()
        block_l = (block_html or '').lower()

        blocked_url_markers = [
            '/shop/figures/',
            '/shop/funko-pop/',
            '/shop/collectibles/',
            '/shop/merch/',
            '/shop/manga/',
            '/shop/anime/',
            '/shop/dwra/'
        ]
        if any(marker in product_url_l for marker in blocked_url_markers):
            return False

        blocked_text_markers = [
            'funko',
            'figure',
            'statue',
            'q posket',
            'nendoroid',
            'banpresto',
            'amiibo',
            'action figure',
        ]
        if any(marker in name_l for marker in blocked_text_markers):
            return False

        allowed_markers = [
            '/shop/epitrapezia/',
            '/shop/card-games/',
            '/shop/kartes/',
            '/shop/tcg/',
            '/shop/expansions/',
            '/shop/board-games/',
            'item_category',
            'epitrapez',
            'card game',
            'board game',
            'expansion',
        ]
        return any(marker in product_url_l or marker in block_l or marker in name_l for marker in allowed_markers)

    products = []
    seen_urls = set()
    query_words = normalize_for_match(_html.unescape(game_query)).split()

    # ── Case 1: Search results page (multiple products) ──────────────────
    # Look for products within div containers with class col (col-6 col-md-3)
    # Each product is inside: <div class="col-... "><li class="product ...">
    product_pattern = r'<div[^>]*class="[^"]*col-[^"]*"[^>]*>.*?<li[^>]*class="[^"]*product[^"]*"(.*?)</li>\s*</div>'

    for product_match in re.finditer(product_pattern, content, re.DOTALL | re.IGNORECASE):
        block = product_match.group(1)

        h2_match = re.search(r'<h2[^>]*woocommerce-loop-product__title[^>]*>([^<]+)</h2>', block, re.IGNORECASE)
        if not h2_match:
            continue

        name = _html.unescape(h2_match.group(1).strip())
        name_norm = normalize_for_match(name)
        if not _query_words_in_text(query_words, name_norm):
            continue

        url_match = re.search(r'<a[^>]*href="(https://epitrapez\.io/[^"]+)"[^>]*class="[^"]*woocommerce-LoopProduct-link', block)
        if not url_match:
            url_match = re.search(r'<a[^>]*class="[^"]*woocommerce-LoopProduct-link[^"]*"[^>]*href="(https://epitrapez\.io/[^"]+)"', block)
        if not url_match:
            url_match = re.search(r'href="(https://epitrapez\.io/shop/[^"]+)"', block)
        if not url_match:
            continue

        product_url = _html.unescape(url_match.group(1))
        if not _is_boardgame_related_epitrapezio_product(product_url, name, block):
            continue
        if product_url in seen_urls:
            continue
        seen_urls.add(product_url)

        price_match = re.search(
            r'<bdi>.*?([0-9]+[.,][0-9]{2})</bdi>',
            block,
            re.DOTALL | re.IGNORECASE
        )
        if not price_match:
            price_match = re.search(
                r'(?:&euro;|€)\s*([0-9]+[.,][0-9]{2})',
                block,
                re.IGNORECASE
            )
        if not price_match:
            continue

        try:
            price = float(price_match.group(1).replace(',', '.'))
        except ValueError:
            continue

        block_lower = block.lower()
        is_oos = (
            'outofstock' in block_lower or
            'out-of-stock' in block_lower or
            'epz-out-of-stock' in block_lower or
            'εξαντλη' in block_lower
        )

        products.append({
            'name': name,
            'price': price,
            'is_in_stock': not is_oos,
            'url': product_url
        })

    if products:
        return products

    # ── Case 2: Single result redirect — product page ─────────────────────
    single_name_match = re.search(
        r'<h1[^>]*class="[^"]*product_title[^"]*"[^>]*>([^<]+)</h1>',
        content, re.IGNORECASE
    )

    if single_name_match:
        name = _html.unescape(' '.join(single_name_match.group(1).split()))
        name_norm = normalize_for_match(name)
        if not _query_words_in_text(query_words, name_norm):
            return []

        h1_pos = single_name_match.start()
        product_area = content[max(0, h1_pos - 1200): min(len(content), h1_pos + 4500)]

        price_container_match = re.search(
            r'<(?:div|p)[^>]*class="[^"]*\bprice\b[^"]*"[^>]*>([\s\S]*?)</(?:div|p)>',
            product_area,
            re.IGNORECASE,
        )
        price_area = price_container_match.group(1) if price_container_match else product_area

        price_match = re.search(
            r'<ins[^>]*>[\s\S]*?<bdi>[\s\S]*?([0-9]+(?:[.,][0-9]{2})?)',
            price_area,
            re.IGNORECASE,
        )
        if not price_match:
            price_match = re.search(
                r'<bdi>[\s\S]*?([0-9]+(?:[.,][0-9]{2})?)',
                price_area,
                re.IGNORECASE,
            )
        if not price_match:
            return []

        try:
            price = float(price_match.group(1).replace(',', '.'))
        except ValueError:
            return []

        url_match = re.search(
            r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\'](https://epitrapez\.io/[^"\']+)["\']',
            content,
            re.IGNORECASE,
        )
        if not url_match:
            url_match = re.search(
                r'<meta[^>]*property=["\']og:url["\'][^>]*content=["\'](https://epitrapez\.io/[^"\']+)["\']',
                content,
                re.IGNORECASE,
            )
        if not url_match:
            url_match = re.search(
                r'href="(https://epitrapez\.io/shop/[^"#]+)',
                product_area,
                re.IGNORECASE,
            )

        product_url = _html.unescape(url_match.group(1)) if url_match else f"https://epitrapez.io/?s={game_query}"
        if not _is_boardgame_related_epitrapezio_product(product_url, name, product_area):
            return []

        product_area_lower = product_area.lower()
        is_oos = (
            'outofstock' in product_area_lower or
            'out-of-stock' in product_area_lower or
            'epz-out-of-stock' in product_area_lower or
            'εξαντλη' in product_area_lower
        )
        in_stock = not is_oos and (
            'single_add_to_cart_button' in product_area_lower or
            'προσθήκη στο καλάθι' in product_area_lower or
            'available-on-backorder' in product_area_lower or
            'διαθέσιμο σε' in product_area_lower or
            'instock' in product_area_lower or
            'in-stock' in product_area_lower
        )

        products.append({
            'name': name,
            'price': price,
            'is_in_stock': in_stock,
            'url': product_url
        })

    return products

def parse_playceshop_html(content, game_query):
    """HTML parser for PlayceShop search results.

    This parser intentionally reads only the main Woodmart product grid cards
    (wd-product/product-grid-item) to avoid false positives from mixed
    html+markdown content outside the results loop.
    """
    if not content:
        return []

    content_lower = content.lower()

    # Guard against explicit no-results pages to avoid stitched false positives
    # from mixed html+markdown content.
    no_results_markers = [
        'woocommerce-no-products-found',
        'woocommerce-info hidden-notice',
        'δεν βρέθηκε κανένα προϊόν',
        'δεν βρεθηκε κανενα προϊόν',
        'δεν βρεθηκε κανενα προϊον',
        'no products were found matching your selection',
    ]
    has_no_results_marker = any(marker in content_lower for marker in no_results_markers)
    if has_no_results_marker:
        return []

    products = []
    seen_urls = set()
    query_norm = normalize_for_match(_html.unescape(game_query))
    query_words = query_norm.split()

    # Parse only explicit product cards from the main results loop.
    card_starts = [
        m.start() for m in re.finditer(
            r'<div[^>]*class="[^"]*\bwd-product\b[^"]*\bproduct-grid-item\b[^"]*"',
            content,
            re.IGNORECASE,
        )
    ]

    if not card_starts:
        return []

    for i, start in enumerate(card_starts):
        end = card_starts[i + 1] if i + 1 < len(card_starts) else len(content)
        block = content[start:end]

        name_match = re.search(
            r'<h3[^>]*class="[^"]*wd-entities-title[^"]*"[^>]*>\s*<a href="(https://shop\.playce\.gr/[^"]+)"[^>]*>([\s\S]*?)</a>',
            block,
            re.IGNORECASE,
        )
        if not name_match:
            continue

        product_url = _html.unescape(name_match.group(1).strip())
        name = _html.unescape(' '.join(re.sub(r'<[^>]+>', ' ', name_match.group(2)).split()))
        if not name or product_url in seen_urls:
            continue

        # Deterministic board-game filter: PlayceShop product URLs include
        # category slugs. Board games live under /shop/epitrapezia.../
        # while non-board items (e.g. figures/accessories) use other categories.
        if '/shop/epitrapezia' not in product_url.lower():
            continue

        name_norm = normalize_for_match(name)
        if not _query_words_in_text(query_words, name_norm):
            continue

        # Prefer machine-readable tracking price when available.
        price = None
        data_price_match = re.search(r'&quot;price&quot;\s*:\s*([0-9]+(?:\.[0-9]+)?)', block, re.IGNORECASE)
        if data_price_match:
            try:
                price = float(data_price_match.group(1))
            except ValueError:
                price = None

        if price is None:
            price_match = re.search(r'<bdi>\s*([0-9]+(?:[\.,][0-9]{2})?)', block, re.IGNORECASE)
            if not price_match:
                price_match = re.search(r'(?:&euro;|€)\s*([0-9]+(?:[\.,][0-9]{2})?)', block, re.IGNORECASE)
            if not price_match:
                continue
            try:
                price = float(price_match.group(1).replace(',', '.'))
            except ValueError:
                continue

        block_lower = block.lower()
        is_oos = (
            'outofstock' in block_lower or
            'out-of-stock' in block_lower or
            'εξαντλημένο' in block_lower
        )
        in_stock = not is_oos

        products.append({
            'name': name,
            'price': price,
            'is_in_stock': in_stock,
            'url': product_url,
        })
        seen_urls.add(product_url)

    return products


def parse_vpshop_html(content, game_query):
    """HTML parser for VP shop WooCommerce search results."""
    if not content:
        return []

    def _extract_price_from_block(block):
        # Prefer the discounted price when a sale price is present.
        ins_match = re.search(
            r'<ins[^>]*>[\s\S]*?<bdi>\s*([0-9]+(?:[\.,][0-9]{2})?)',
            block,
            re.DOTALL | re.IGNORECASE,
        )
        if ins_match:
            return float(ins_match.group(1).replace(',', '.'))

        regular_match = re.search(
            r'<span[^>]*class="[^"]*woocommerce-Price-amount[^"]*"[^>]*>\s*<bdi>\s*([0-9]+(?:[\.,][0-9]{2})?)',
            block,
            re.DOTALL | re.IGNORECASE,
        )
        if regular_match:
            return float(regular_match.group(1).replace(',', '.'))

        fallback_match = re.search(
            r'([0-9]+(?:[\.,][0-9]{2})?)\s*(?:&nbsp;|\s)*<span[^>]*woocommerce-Price-currencySymbol',
            block,
            re.IGNORECASE,
        )
        if fallback_match:
            return float(fallback_match.group(1).replace(',', '.'))

        return None

    content_lower = content.lower()
    no_results_markers = [
        'woocommerce-no-products-found',
        'woocommerce-info hidden-notice',
        'δεν βρέθηκε κανένα προϊόν',
        'δεν βρεθηκε κανενα προϊόν',
        'δεν βρεθηκε κανενα προϊον',
        'no products were found matching your selection',
    ]
    if any(marker in content_lower for marker in no_results_markers):
        return []

    products = []
    seen_urls = set()
    query_norm = normalize_for_match(_html.unescape(game_query))
    query_words = query_norm.split()

    # Case 1: search can redirect directly to a single product page.
    single_name_match = re.search(
        r'<h1[^>]*class="[^"]*product_title[^"]*"[^>]*>([\s\S]*?)</h1>',
        content,
        re.IGNORECASE,
    )
    if single_name_match:
        name = _html.unescape(' '.join(re.sub(r'<[^>]+>', ' ', single_name_match.group(1)).split()))
        name_norm = normalize_for_match(name)
        if _query_words_in_text(query_words, name_norm):
            h1_pos = single_name_match.start()
            page_area = content[max(0, h1_pos - 1200): min(len(content), h1_pos + 9000)]

            price = _extract_price_from_block(page_area)
            if price is not None:
                url_match = re.search(
                    r'<link[^>]*rel="canonical"[^>]*href="(https://shop\.vpsaga\.com/product/[^"#]+)"',
                    content,
                    re.IGNORECASE,
                )
                if not url_match:
                    url_match = re.search(
                        r'<meta[^>]*property="og:url"[^>]*content="(https://shop\.vpsaga\.com/product/[^"#]+)"',
                        content,
                        re.IGNORECASE,
                    )
                if not url_match:
                    url_match = re.search(
                        r'href="(https://shop\.vpsaga\.com/product/[^"#]+)"',
                        page_area,
                        re.IGNORECASE,
                    )

                if url_match:
                    product_url = _html.unescape(url_match.group(1).strip())
                    page_lower = page_area.lower()
                    is_oos = (
                        'outofstock' in page_lower or
                        'out-of-stock' in page_lower or
                        'εκτός αποθέματος' in page_lower
                    )
                    in_stock = not is_oos and (
                        'single_add_to_cart_button' in page_lower or
                        'add_to_cart_button' in page_lower or
                        'προσθήκη στο καλάθι' in page_lower or
                        'instock' in page_lower or
                        'in-stock' in page_lower or
                        'σε απόθεμα' in page_lower
                    )

                    products.append({
                        'name': name,
                        'price': price,
                        'is_in_stock': in_stock,
                        'url': product_url,
                    })
                    return products

    # Case 2: parse the Woodmart search results grid.
    card_starts = [
        m.start() for m in re.finditer(
            r'<div[^>]*class="[^"]*\bwd-product\b[^"]*\bproduct-grid-item\b[^"]*"',
            content,
            re.IGNORECASE,
        )
    ]
    if not card_starts:
        return []

    for i, start in enumerate(card_starts):
        end = card_starts[i + 1] if i + 1 < len(card_starts) else len(content)
        block = content[start:end]

        name_match = re.search(
            r'<h3[^>]*class="[^"]*wd-entities-title[^"]*"[^>]*>\s*<a[^>]*href="((?:https://shop\.vpsaga\.com)?/product/[^"#]+)"[^>]*>([\s\S]*?)</a>',
            block,
            re.IGNORECASE,
        )
        if not name_match:
            continue

        raw_url = _html.unescape(name_match.group(1).strip())
        product_url = raw_url if raw_url.startswith('http') else f"https://shop.vpsaga.com{raw_url}"
        name = _html.unescape(' '.join(re.sub(r'<[^>]+>', ' ', name_match.group(2)).split()))
        if not name or product_url in seen_urls:
            continue

        name_norm = normalize_for_match(name)
        if not _query_words_in_text(query_words, name_norm):
            continue

        try:
            price = _extract_price_from_block(block)
        except ValueError:
            price = None
        if price is None:
            continue

        block_lower = block.lower()
        is_oos = (
            'outofstock' in block_lower or
            'out-of-stock' in block_lower or
            'εκτός αποθέματος' in block_lower
        )
        in_stock = not is_oos and (
            'instock' in block_lower or
            'in-stock' in block_lower or
            'σε απόθεμα' in block_lower or
            'add_to_cart_button' in block_lower or
            'προσθήκη στο καλάθι' in block_lower
        )

        products.append({
            'name': name,
            'price': price,
            'is_in_stock': in_stock,
            'url': product_url,
        })
        seen_urls.add(product_url)

    return products


def parse_dragonphoenixinn_html(content, game_query):
    """HTML parser for The Dragonphoenix Inn (innkeeper.gr)."""
    if not content:
        return []

    def _is_dragonphoenixinn_boardgame_product(block_html, name, product_url):
        """Keep tabletop products and reject merch/figures from mixed search pages."""
        name_l = normalize_for_match(_html.unescape(name or ''))
        url_l = urllib.parse.unquote(product_url or '').lower()
        text_l = normalize_for_match(_html.unescape(re.sub(r'<[^>]+>', ' ', block_html or '')))
        class_markers = ' '.join(sorted(set(re.findall(r'product_cat-[^"\s>]+|product_tag-[^"\s>]+', block_html.lower()))))
        combined_l = f"{name_l} {url_l} {text_l} {class_markers}"

        blocked_markers = [
            'product_cat-merch', 'product_cat-figures', 'product_cat-funko',
            'product_tag-merch', 'product_tag-actionfigure', 'product_tag-funko',
            'cable guy', 'airpods case', 'bookends', 'pocket pop', 'funko pop',
            'funko', 'vinyl figure', 'action figure', 'pvc figure', 'mini egg attack',
            'egg attack', 'mini co', 'keychain', 'keychains', 'figurine', 'statue',
            'bust', 'phone holder', 'cable holder'
        ]
        if any(marker in combined_l for marker in blocked_markers):
            return False

        positive_markers = [
            'product_cat-board-games', 'product_cat-card-games',
            'product_cat-card-game-accessories', 'product_cat-playmats',
            'product_cat-sleeves', 'product_cat-magic-the-gathering',
            'product_tag-boardgames', 'product_tag-card-games', 'product_tag-expansion',
            'product_tag-playmat', 'product_tag-sleeves', 'board game', 'boardgames',
            'card game', 'card games', 'playmat', 'sleeves', 'expansion', 'hero pack',
            'booster', 'jumpstart', 'commander', 'bundle', 'beginner box', 'draft night',
            'scene box', 'deck', 'magic the gathering', 'marvel champions', 'marvel d.a.g.g.e.r'
        ]
        return any(marker in combined_l for marker in positive_markers)

    products = []
    seen_urls = set()
    query_norm = normalize_for_match(_html.unescape(game_query))
    query_words = query_norm.split()

    def _extract_price_from_block(block):
        # Prefer sale price when both original and discounted exist.
        ins_match = re.search(r'<ins[^>]*>.*?<bdi>\s*([0-9]+(?:[\.,][0-9]{2})?)', block, re.DOTALL | re.IGNORECASE)
        if ins_match:
            return float(ins_match.group(1).replace(',', '.'))

        regular_match = re.search(r'<span[^>]*class="[^"]*woocommerce-Price-amount[^"]*"[^>]*>\s*<bdi>\s*([0-9]+(?:[\.,][0-9]{2})?)', block, re.DOTALL | re.IGNORECASE)
        if regular_match:
            return float(regular_match.group(1).replace(',', '.'))

        fallback_match = re.search(r'([0-9]+(?:[\.,][0-9]{2})?)\s*(?:&nbsp;|\s)*<span[^>]*woocommerce-Price-currencySymbol', block, re.IGNORECASE)
        if fallback_match:
            return float(fallback_match.group(1).replace(',', '.'))

        return None

    # Case 1: Single product page redirect
    single_name_match = re.search(
        r'<h1[^>]*class="[^"]*product_title[^"]*"[^>]*>([\s\S]*?)</h1>',
        content,
        re.IGNORECASE,
    )

    if single_name_match:
        name = _html.unescape(' '.join(re.sub(r'<[^>]+>', ' ', single_name_match.group(1)).split()))
        name_norm = normalize_for_match(name)
        if _query_words_in_text(query_words, name_norm):
            h1_pos = single_name_match.start()
            page_area = content[h1_pos:h1_pos + 9000]

            price = _extract_price_from_block(page_area)
            if price is not None:
                # Prefer cart form action URL for the current product.
                url_match = re.search(
                    r'<form[^>]*class="[^"]*cart[^"]*"[^>]*action="(https://innkeeper\.gr/product/[^"#]+)"',
                    page_area,
                    re.IGNORECASE,
                )
                if not url_match:
                    url_match = re.search(
                        r'<link[^>]*rel="canonical"[^>]*href="(https://innkeeper\.gr/product/[^"#]+)"',
                        content,
                        re.IGNORECASE,
                    )
                if not url_match:
                    url_match = re.search(
                        r'<meta[^>]*property="og:url"[^>]*content="(https://innkeeper\.gr/product/[^"#]+)"',
                        content,
                        re.IGNORECASE,
                    )
                if not url_match:
                    url_match = re.search(
                        r'href="(https://innkeeper\.gr/product/[^"#]+)"',
                        page_area,
                        re.IGNORECASE,
                    )

                if url_match:
                    product_url = url_match.group(1)
                    if not _is_dragonphoenixinn_boardgame_product(page_area, name, product_url):
                        return []

                    stock_marker_match = re.search(
                        r'<(?:p|div)[^>]*class="[^"]*stock[^"]*"[^>]*>',
                        page_area,
                        re.IGNORECASE,
                    )
                    if stock_marker_match:
                        stock_marker = stock_marker_match.group(0).lower()
                        in_stock = (
                            'in-stock' in stock_marker and
                            'out-of-stock' not in stock_marker
                        )
                    else:
                        page_lower = page_area.lower()
                        in_stock = (
                            'single_add_to_cart_button' in page_lower or
                            'add to cart' in page_lower or
                            'προσθήκη στο καλάθι' in page_lower
                        )

                    products.append({
                        'name': name,
                        'price': price,
                        'is_in_stock': in_stock,
                        'url': product_url,
                    })
                    return products

    # Case 2: Search results page (Woodmart product grid)
    card_starts = [
        m.start() for m in re.finditer(
            r'<div[^>]*class="[^"]*\bwd-product\b[^"]*\bproduct-grid-item\b[^"]*"',
            content,
            re.IGNORECASE,
        )
    ]

    for i, start in enumerate(card_starts):
        end = card_starts[i + 1] if i + 1 < len(card_starts) else len(content)
        block = content[start:end]

        name_match = re.search(
            r'<h3[^>]*class="[^"]*wd-entities-title[^"]*"[^>]*>\s*<a[^>]*href="(https://innkeeper\.gr/product/[^"#]+)"[^>]*>([\s\S]*?)</a>',
            block,
            re.IGNORECASE,
        )
        if not name_match:
            continue

        product_url = _html.unescape(name_match.group(1).strip())
        name = _html.unescape(' '.join(re.sub(r'<[^>]+>', ' ', name_match.group(2)).split()))
        if not name or product_url in seen_urls:
            continue

        name_norm = normalize_for_match(name)
        if not _query_words_in_text(query_words, name_norm):
            continue
        if not _is_dragonphoenixinn_boardgame_product(block, name, product_url):
            continue

        try:
            price = _extract_price_from_block(block)
        except ValueError:
            price = None
        if price is None:
            continue

        block_lower = block.lower()
        is_oos = (
            'outofstock' in block_lower or
            'out-of-stock' in block_lower or
            ' εξαντλη' in block_lower
        )
        in_stock = not is_oos

        products.append({
            'name': name,
            'price': price,
            'is_in_stock': in_stock,
            'url': product_url,
        })
        seen_urls.add(product_url)

    return products


def parse_crystallotus_html(content, game_query):
    """HTML parser for Crystal Lotus (Shopify collection/search cards)."""
    if not content:
        return []

    def _is_crystallotus_boardgame_product(name, raw_url, vendor, taxonomy_value=None):
        """Keep board/card games and tabletop accessories, reject merch/collectibles."""
        if taxonomy_value is True:
            return True
        if taxonomy_value is False:
            return False

        name_l = normalize_for_match(_html.unescape(name or ''))
        url_l = urllib.parse.unquote(raw_url or '').lower()
        vendor_l = normalize_for_match(_html.unescape(vendor or ''))
        combined_l = f"{name_l} {url_l} {vendor_l}"

        blocked_markers = [
            'funko', 'pop!', 'pop vinyl', 'enamel pin', 'pin wolverine',
            'notebook', 'logo light', 'neon light', 'lamp', 'mug', 'glass',
            'backpack', 'wallet', 'keychain', 't-shirt', 'plush', 'poster',
            'action figure', 'figure', 'statue', 'retro collection',
            'marvel legends', 'legends assortment', 'nintendo switch',
            'playstation', 'ps4', 'ps5', 'xbox', 'pc game', 'steam key',
            'digital code', 'blu-ray', 'dvd', 'puzzle'
        ]
        if any(marker in combined_l for marker in blocked_markers):
            return False

        positive_markers = [
            'board game', 'board-game', 'card game', 'card-game',
            'expansion', 'hero pack', 'scenario pack', 'booster',
            'starter deck', 'starter-deck', 'deck box', 'deck-box',
            'playmat', 'sleeves', 'dice', 'tcg', 'lcg', 'rpg',
            'marvel united', 'splendor', 'munchkin', 'dice throne',
            'd.a.g.g.e.r', 'marvel remix', 'villainous', 'unmatched',
            'legendary', 'champions'
        ]
        if any(marker in combined_l for marker in positive_markers):
            return True

        allowed_vendors = [
            'fantasy flight games', 'cmon', 'roxley games', 'space cowboys',
            'steve jackson games', 'mondo games', 'kaissa', 'ravensburger',
            'restoration games', 'upper deck entertainment',
            'wizards of the coast', 'ultimate guard', 'gamegenic',
            'theory11', 'legend story studios', 'chaosium inc', 'manopoulos'
        ]
        return any(vendor_marker in vendor_l for vendor_marker in allowed_vendors)

    products = []
    seen_urls = set()
    query_norm = normalize_for_match(_html.unescape(game_query))
    query_words = query_norm.split()

    # Crystal Lotus search pages sometimes embed Shopify meta taxonomy.
    # When present, use it as the strongest board-game classifier.
    boardgame_type_by_handle = {}
    meta_match = re.search(r'var\s+meta\s*=\s*(\{[\s\S]*?\})\s*;', content, re.IGNORECASE)
    if meta_match:
        try:
            meta_payload = json.loads(meta_match.group(1))
            for product in meta_payload.get('products', []):
                if not isinstance(product, dict):
                    continue
                handle = str(product.get('handle', '') or '').strip().lower()
                product_type = str(product.get('type', '') or '').strip().lower()
                if not handle:
                    continue
                boardgame_type_by_handle[handle] = product_type.startswith('tabletop games > board games')
        except Exception:
            boardgame_type_by_handle = {}

    card_starts = [
        m.start() for m in re.finditer(
            r'<div[^>]*class="[^"]*card-wrapper[^"]*"',
            content,
            re.IGNORECASE,
        )
    ]
    if not card_starts:
        return []

    for i, start in enumerate(card_starts):
        end = card_starts[i + 1] if i + 1 < len(card_starts) else len(content)
        block = content[start:end]

        name_match = re.search(
            r'<a[^>]*class="[^"]*card-information__text[^"]*"[^>]*>([\s\S]*?)</a>',
            block,
            re.IGNORECASE,
        )
        if not name_match:
            continue

        name = _html.unescape(' '.join(re.sub(r'<[^>]+>', ' ', name_match.group(1)).split()))
        if not name:
            continue

        name_norm = normalize_for_match(name)
        if not _query_words_in_text(query_words, name_norm):
            continue

        url_match = re.search(
            r'<a[^>]*class="[^"]*card-information__text[^"]*"[^>]*href="([^"]+)"',
            block,
            re.IGNORECASE,
        )
        if not url_match:
            url_match = re.search(
                r'<a[^>]*href="([^"]+)"[^>]*class="[^"]*card-information__text[^"]*"',
                block,
                re.IGNORECASE,
            )
        if not url_match:
            url_match = re.search(
                r'<a[^>]*class="[^"]*full-unstyled-link[^"]*"[^>]*href="([^"]+)"',
                block,
                re.IGNORECASE,
            )
        if not url_match:
            url_match = re.search(
                r'<a[^>]*href="([^"]+)"[^>]*class="[^"]*full-unstyled-link[^"]*"',
                block,
                re.IGNORECASE,
            )
        if not url_match:
            continue

        raw_url = _html.unescape(url_match.group(1)).strip()
        url = raw_url if raw_url.startswith('http') else f"https://crystallotus.eu{raw_url}"
        if url in seen_urls:
            continue

        vendor_match = re.search(
            r'<div[^>]*class="[^"]*card-article-info[^"]*"[^>]*>([^<]+)</div>',
            block,
            re.IGNORECASE,
        )
        vendor = _html.unescape(vendor_match.group(1).strip()) if vendor_match else ''

        handle_match = re.search(r'/products/([^/?#]+)', raw_url, re.IGNORECASE)
        handle = urllib.parse.unquote(handle_match.group(1)).strip().lower() if handle_match else ''
        taxonomy_value = boardgame_type_by_handle.get(handle) if handle else None
        if not _is_crystallotus_boardgame_product(name, raw_url, vendor, taxonomy_value):
            continue

        block_lower = block.lower()
        is_oos = (
            'sold out' in block_lower or
            'εξαντλη' in block_lower or
            'out-of-stock' in block_lower
        )
        has_add_to_cart = '<add-to-cart' in block_lower and 'προσθήκη στο καλάθι' in block_lower
        in_stock = has_add_to_cart and not is_oos

        sale_match = re.search(
            r'price-item--sale[\s\S]*?<span[^>]*price__prefix[^>]*>€</span>\s*([0-9]+)\s*(?:<sup[^>]*>([,\.]?[0-9]{2})</sup>)?',
            block,
            re.IGNORECASE,
        )
        regular_match = re.search(
            r'price-item--regular[\s\S]*?<span[^>]*price__prefix[^>]*>€</span>\s*([0-9]+)\s*(?:<sup[^>]*>([,\.]?[0-9]{2})</sup>)?',
            block,
            re.IGNORECASE,
        )

        price = "N/A"
        price_match = sale_match or regular_match
        if price_match:
            whole = price_match.group(1)
            decimals = price_match.group(2) if price_match.lastindex and price_match.lastindex >= 2 else ""
            decimals = (decimals or '').replace(',', '.').strip()
            if decimals and not decimals.startswith('.'):
                decimals = f'.{decimals}'
            price_text = f"{whole}{decimals}" if decimals else whole
            try:
                price = float(price_text)
            except ValueError:
                price = "N/A"

        products.append({
            'name': name,
            'price': price,
            'is_in_stock': in_stock,
            'url': url,
        })
        seen_urls.add(url)

    return products


# Fallback HTML parser for Fantasy Shop
def parse_fantasyshop_html(content, game_query):
    """Fallback HTML parser for Fantasy Shop - correctly extracts availability from block_avail_status_label"""
    products = []
    query_norm = normalize_for_match(_html.unescape(game_query))
    query_words = query_norm.split()
    # Deterministic case: category-scoped search pages already restrict to board games.
    content_lower = content.lower()
    is_boardgame_scoped_page = (
        'epitrapezia-paixnidia' in content_lower or
        'επιτραπέζια παιχνίδια' in content_lower
    )
    # Pattern for Fantasy Shop's CS-Cart structure
    pattern = r'<a href="(https://www\.fantasy-shop\.gr/[^"]+\.html)"[^>]*class="product-title"[^>]*title="([^"]+)"[^>]*>.*?<span[^>]*class="ty-price-num">([0-9]+,[0-9]{2})</span>'
    matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
    for match in matches:
        url = match.group(1)
        name = _html.unescape(match.group(2).strip())
        price_str = match.group(3).replace(',', '.')
        name_norm = normalize_for_match(name)
        if not _query_words_in_text(query_words, name_norm):
            continue
        # Fallback filter for generic search pages where non-board-game products may appear.
        if not is_boardgame_scoped_page and not _is_fantasyshop_boardgame(name):
            continue

        # Significantly expand context window to find stock indicators
        # The block_avail_status_label div comes AFTER the product pricing info
        context_start = max(0, match.start() - 500)
        context_end = min(len(content), match.end() + 3000)  # Extended to capture avail_status_label
        context = content[context_start:context_end]

        # NEW: Extract availability status from block_avail_status_label div
        # Structure: <div class="block_avail_status_label">
        #              <input type="hidden" name="product_data[XXXX][avail_status]" value="1" />  <!-- 1=in stock, 2=out of stock -->
        #              <div class="title" style="color: #047f0e;">In Stock</div>
        #              <div class="descr">Delivery in 2-3 working days</div>
        #           </div>
        in_stock = True  # Default to in stock

        # Method 1: Extract from hidden input avail_status value
        avail_status_match = re.search(
            r'<div class="block_avail_status_label">.*?'
            r'<input[^>]*name="product_data\[\d+\]\[avail_status\]"[^>]*value="(\d+)"',
            context, re.DOTALL | re.IGNORECASE
        )

        if avail_status_match:
            avail_status_value = avail_status_match.group(1)
            in_stock = avail_status_value == "1"  # 1 = in stock, 2 = out of stock
        else:
            # Method 2: Fallback - extract from the title text inside block_avail_status_label
            avail_label_match = re.search(
                r'<div class="block_avail_status_label">.*?'
                r'<div class="title"[^>]*>([^<]+)</div>',
                context, re.DOTALL | re.IGNORECASE
            )

            if avail_label_match:
                avail_text = avail_label_match.group(1).strip().lower()
                in_stock = 'in stock' in avail_text or 'σε απόθεμα' in avail_text
            else:
                # Method 3: Fallback to keyword search if no block_avail_status_label found
                has_out_of_stock = (
                    'out of stock' in context.lower() or
                    'out-of-stock' in context.lower() or
                    'εξαντλήθηκε' in context.lower() or
                    'εξαντλημένο' in context.lower() or
                    'μη διαθέσιμο' in context.lower() or
                    'δεν είναι διαθέσιμο' in context.lower()
                )
                in_stock = not has_out_of_stock

        products.append({
            'name': name,
            'price': float(price_str),
            'is_in_stock': in_stock,
            'url': url
        })
    return products

# Non-board-game product-type keywords for Fantasy Shop.
_FANTASYSHOP_EXCLUDE_KEYWORDS = [
    "replica",
    "keyring",
    "lamp",
    "light",
    "funko",
    "pop!",
    "figure",
    "statue",
    "mini bust",
    "poster",
    "mug",
    "t-shirt",
    "hoodie",
    "wallet",
    "pin",
    "plush",
    "mousepad",
    "dvd",
    "blu-ray",
    "ps4",
    "ps5",
    "xbox",
    "nintendo switch",
    "pc game",
]

def _is_fantasyshop_boardgame(name):
    """Return True if a Fantasy Shop product name looks like a board game."""
    if not name:
        return False
    lower = name.lower()
    return not any(kw in lower for kw in _FANTASYSHOP_EXCLUDE_KEYWORDS)

# Greek name prefixes that indicate a board game / expansion on Nerdom.
_NERDOM_BG_KEYWORDS = [
    "επιτραπέζιο",       # "board [game]"
    "επέκταση",          # "expansion"
]

def _is_nerdom_boardgame(name):
    """Return True if the Nerdom product name indicates a board game."""
    if not name:
        return False
    lower = name.lower()
    return any(kw in lower for kw in _NERDOM_BG_KEYWORDS)

# Fallback HTML parser for Nerdom
def parse_nerdom_html(content, game_query):
    """Fallback HTML parser for Nerdom"""
    products = []
    # Pattern: card__product-name with link and title, then final__price
    pattern = r'<div class="card__product-name">.*?<a href="(https://www\.nerdom\.gr/[^"]+)"[^>]*>([^<]+)</a>.*?<span class="final__price">([0-9,]+)€</span>'
    matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
    for match in matches:
        url = match.group(1)
        name = _html.unescape(match.group(2).strip())
        price_str = match.group(3).replace(',', '.')
        if game_query.lower() not in name.lower():
            continue
        if not _is_nerdom_boardgame(name):
            continue
        # Check stock in surrounding context
        context_start = max(0, match.start() - 500)
        context_end = min(len(content), match.end() + 500)
        context = content[context_start:context_end]
        # Nerdom stock indicators
        in_stock = (
            'out of stock' not in context.lower() and
            'εξαντλημένο' not in context.lower() and
            'μη διαθέσιμο' not in context.lower()
        )
        products.append({
            'name': name,
            'price': float(price_str),
            'is_in_stock': in_stock,
            'url': url
        })
    return products

# ── Ozon.gr direct FastSimon API search ──────────────────────────

# Greek name prefixes that indicate a board game / expansion on Ozon.gr.
# Products without any of these keywords (e.g. books, puzzles, figurines) are filtered out.
_OZON_BG_KEYWORDS = [
    "επιτραπέζιο",       # "board [game]"
    "επέκταση",          # "expansion"
    "επιτραπέζιων",  # "board game set"
    "ζάρια",             # "dice" - often included in board game sets, but not standalone dice or other unrelated products
    "τραπουλόχαρτα",        # "playing cards" - often included in board game sets, but not standalone card decks or unrelated products
]

def _is_ozon_boardgame(name):
    """Return True if the Ozon.gr product name indicates a board game."""
    if not name:
        return False
    lower = name.lower()
    return any(kw in lower for kw in _OZON_BG_KEYWORDS)

_OZON_FASTSIMON_UUID = "0cdd88e8-d8d1-4b9e-bfe0-c679e7f62eda"

def search_ozon(game_query):
    """Query Ozon.gr via the FastSimon search API (no Firecrawl needed)."""
    import requests as _requests
    encoded = urllib.parse.quote_plus(game_query)
    api_url = (
        f"https://fastsimon-search-service.akamaized.net/full_text_search"
        f"?UUID={_OZON_FASTSIMON_UUID}&q={encoded}&pages=1&num=36"
    )
    try:
        resp = _requests.get(api_url, timeout=15)
        if resp.status_code != 200:
            return []
        return parse_ozon_api(resp.json(), game_query)
    except Exception:
        return []


def parse_ozon_api(data, game_query):
    """Parse FastSimon JSON payload from Ozon.gr and return product dicts."""
    if not data or not isinstance(data, dict):
        return []
    items = data.get("items", [])
    if not items:
        return []

    products = []
    seen_urls = set()
    query_norm = normalize_for_match(_html.unescape(game_query))
    query_words = query_norm.split()

    for item in items:
        raw_name = (item.get("l") or "").strip()
        url = (item.get("u") or "").strip()
        if not raw_name or not url or url in seen_urls:
            continue

        if not _is_ozon_boardgame(raw_name):
            continue

        comparison = sanitize_ozon_name(raw_name)
        comparison_norm = normalize_for_match(comparison)
        if not _query_words_in_text(query_words, comparison_norm):
            continue

        seen_urls.add(url)

        # Price: prefer sale price (p), compare price (p_c) is the original
        price_str = item.get("p") or ""
        try:
            price = float(price_str.replace(",", "."))
        except (ValueError, AttributeError):
            continue

        # Stock: FastSimon field "iso" is True when item is sold-out
        in_stock = not item.get("iso", False)

        products.append({
            "name": raw_name,
            "price": price,
            "is_in_stock": in_stock,
            "url": url,
        })

    return products


# Fallback HTML parser for Ozon.gr (updated for InstantSearch Plus structure)
def parse_ozon_html(content, game_query):
    """HTML parser for Ozon.gr - updated for InstantSearch Plus structure"""
    if not content:
        return []
    products = []
    seen_urls = set()
    query_norm = normalize_for_match(_html.unescape(game_query))
    query_words = query_norm.split()

    # Each product card has:
    # - <a class="...fs-serp-product-title..."> with href and name in aria-label
    # - <div class="price-container..."> with aria-label="; regular price: X.XX €"
    # - Optionally a separate element with aria-label="; sale price: X.XX €"
    # We want sale price if present, otherwise regular price

    pattern = (
        r'<a[^>]*class="[^"]*fs-serp-product-title[^"]*"[^>]*'
        r'href="(https://www\.ozon\.gr/product/[^"]+)"[^>]*>'
        r'.*?<span[^>]*class="[^"]*fs-product-title[^"]*"[^>]*'
        r'aria-label="([^"]+)"'
    )

    for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
        url = match.group(1).strip()
        raw_name = _html.unescape(' '.join(match.group(2).split()))

        if url in seen_urls:
            continue

        if not _is_ozon_boardgame(raw_name):
            continue

        # Filter by query using normalized sanitized title.
        comparison = sanitize_ozon_name(raw_name)
        comparison_norm = normalize_for_match(comparison)
        if not _query_words_in_text(query_words, comparison_norm):
            continue

        seen_urls.add(url)

        # Search in window around this product card
        card_area = content[match.start():match.start() + 2000]

        # Try to get price from the price div first (may be discounted)
        split_match = re.search(
            r'class="[^"]*price fs-result-page[^"]*"[^>]*>\s*(\d+)\s*'
            r'<div class="price-sup"[^>]*>,([\d]+)</div>',
            card_area, re.DOTALL | re.IGNORECASE
        )
        if split_match:
            price_str = f"{split_match.group(1)}.{split_match.group(2)}"
        else:
            # Fallback to aria-label for price
            sale_match = re.search(
                r'aria-label=";\s*sale price:\s*([\d,\.]+)\s*€"',
                card_area, re.IGNORECASE
            )
            regular_match = re.search(
                r'aria-label=";\s*regular price:\s*([\d,\.]+)\s*€"',
                card_area, re.IGNORECASE
            )

            if sale_match:
                price_str = sale_match.group(1)
            elif regular_match:
                price_str = regular_match.group(1)
            else:
                continue

        price_str = price_str.replace(',', '.')
        try:
            price = float(price_str)
        except ValueError:
            continue

        # Stock detection
        in_stock = (
            'out-of-stock' not in card_area.lower() and
            'εξαντλημένο' not in card_area.lower() and
            'outofstock' not in card_area.lower()
        )

        products.append({
            'name': raw_name,
            'price': price,
            'is_in_stock': in_stock,
            'url': url
        })

    return products

# Sanitizer for No Label X product names
def sanitize_nolabelx_name(raw_name):
    """Strip age rating and all subsequent text from No Label X names.
    Example: 'Trials of Tempus Premium Edition 12+ Ετών (EN) Wizards of the Coast' → 'trials of tempus premium edition'
    """
    if not raw_name:
        return ""
    name = raw_name.strip()
    # Remove age rating and everything that follows it
    name = re.sub(r'\s+\d+\+\s*Ετών.*$', '', name, flags=re.IGNORECASE)
    # Normalize whitespace and convert to lowercase
    return ' '.join(name.split()).strip().lower()


# Sanitizer for Lex Hobby Store product names
def sanitize_lexhobby_name(raw_name):
    """Strip age rating and all subsequent text from Lex Hobby Store names.
    Example: 'Trials of Tempus Premium Edition 12+ Ετών (EN) Wizards of the Coast' → 'trials of tempus premium edition'
    """
    if not raw_name:
        return ""
    name = raw_name.strip()
    # Remove age rating and everything that follows it
    name = re.sub(r'\s+\d+\+\s*Ετών.*$', '', name, flags=re.IGNORECASE)
    # Normalize whitespace and convert to lowercase
    return ' '.join(name.split()).strip().lower()


def extract_skroutz_store_product_url(content, base_url, anchor_start):
    """Prefer store-specific Skroutz URL containing product_id for a parsed product card."""
    if not base_url:
        return ""

    # Normalize to relative + absolute forms for matching and final output.
    if base_url.startswith('http'):
        base_abs = base_url
        base_rel = re.sub(r'^https?://www\.skroutz\.gr', '', base_url, flags=re.IGNORECASE)
    else:
        base_rel = base_url if base_url.startswith('/') else '/' + base_url
        base_abs = 'https://www.skroutz.gr' + base_rel

    start = max(0, anchor_start - 300)
    end = min(len(content), anchor_start + 2200)
    snippet = _html.unescape(content[start:end])

    def choose_closest(candidates):
        if not candidates:
            return ""
        # Prefer links after the anchor; then by nearest distance to the anchor.
        candidates.sort(key=lambda item: (item[0] < anchor_start, abs(item[0] - anchor_start)))
        return candidates[0][1]

    # 1) Best match: same product path + product_id query parameter.
    base_rel_escaped = re.escape(base_rel)
    same_rel_pattern = re.compile(
        rf'({base_rel_escaped}\?[^"\'\s<>]*product_id=\d+[^"\'\s<>]*)',
        re.IGNORECASE
    )
    same_abs_pattern = re.compile(
        rf'(https?://www\.skroutz\.gr{base_rel_escaped}\?[^"\'\s<>]*product_id=\d+[^"\'\s<>]*)',
        re.IGNORECASE
    )

    same_candidates = []
    for match in same_abs_pattern.finditer(snippet):
        same_candidates.append((start + match.start(), match.group(1)))
    for match in same_rel_pattern.finditer(snippet):
        same_candidates.append((start + match.start(), match.group(1)))
    selected = choose_closest(same_candidates)
    if selected:
        return selected if selected.startswith('http') else 'https://www.skroutz.gr' + selected

    # 2) Fallback: any Skroutz product URL with product_id within the local card context.
    generic_abs_pattern = re.compile(
        r'(https?://www\.skroutz\.gr/s/[^"\'\s<>?]+/[^"\'\s<>?]+\?[^"\'\s<>]*product_id=\d+[^"\'\s<>]*)',
        re.IGNORECASE
    )
    generic_rel_pattern = re.compile(
        r'(/s/[^"\'\s<>?]+/[^"\'\s<>?]+\?[^"\'\s<>]*product_id=\d+[^"\'\s<>]*)',
        re.IGNORECASE
    )
    generic_candidates = []
    for match in generic_abs_pattern.finditer(snippet):
        generic_candidates.append((start + match.start(), match.group(1)))
    for match in generic_rel_pattern.finditer(snippet):
        generic_candidates.append((start + match.start(), match.group(1)))
    selected = choose_closest(generic_candidates)
    if selected:
        return selected if selected.startswith('http') else 'https://www.skroutz.gr' + selected

    return base_abs

# Fallback HTML parser for SoHotTCG
def parse_sohottcg_html(content, game_query):
    """HTML parser for SoHotTCG (Skroutz board games shop page)"""
    if not content:
        return []
    products = []
    seen_urls = set()

    # In scraped content: no <h2> wrapper, absolute URLs, class="js-sku-link" (not "js-sku-link pic")
    name_pattern = re.compile(
        r'<a\s[^>]*class="js-sku-link"[^>]*href="((?:https://www\.skroutz\.gr)?/s/[^"?]+)[^"]*"[^>]*>'
        r'([^<]+)</a>',
        re.IGNORECASE
    )
    price_pattern = re.compile(
        r'<a[^>]*class="js-sku-link sku-link"[^>]*>([\d,\.]+)\s*€',
        re.IGNORECASE
    )

    name_matches = list(name_pattern.finditer(content))
    price_matches = list(price_pattern.finditer(content))

    price_idx = 0
    for name_match in name_matches:
        while price_idx < len(price_matches) and price_matches[price_idx].start() < name_match.start():
            price_idx += 1
        if price_idx >= len(price_matches):
            break

        raw_url = name_match.group(1)
        url = extract_skroutz_store_product_url(content, raw_url, name_match.start())
        raw_name = _html.unescape(' '.join(name_match.group(2).split()))
        price_raw = price_matches[price_idx].group(1).replace(',', '.')

        decoded_game_query = _html.unescape(game_query).lower().replace(':', '').strip()
        clean_name = sanitize_nolabelx_name(raw_name)
        clean_name_normalized = ' '.join(clean_name.replace(':', ' ').replace('-', ' ').split())
        if not all(w in clean_name_normalized for w in decoded_game_query.split()):
            continue
        if url in seen_urls:
            continue
        seen_urls.add(url)
        try:
            price = float(price_raw)
        except ValueError:
            continue

        context_start = max(0, name_match.start() - 100)
        context_end = min(len(content), price_matches[price_idx].end() + 500)
        context = content[context_start:context_end]
        in_stock = 'out-of-stock' not in context.lower() and 'εξαντλημένο' not in context.lower()

        products.append({
            'name': raw_name,
            'price': price,
            'is_in_stock': in_stock,
            'url': url
        })
        price_idx += 1

    return products

# Fallback HTML parser for Mystery Bay (Wix store with JSON warmup data)
def parse_mysterybay_html(content, game_query):
    """Parser for Mystery Bay (Wix store - uses markdown content)"""
    if not content:
        return []
    products = []
    seen_urls = set()

    # Each product is a div with class "product-small col"
    # We capture: out-of-stock indicator, product URL+name, and price (sale or regular)
    pattern = (
        r'<div class="product-small col([^"]*?)"[^>]*?>'
        r'.*?<p class="name product-title woocommerce-loop-product__title"[^>]*?>'
        r'.*?<a href="(https://meepleonboard\.gr/[^"]+)"[^>]*?>([^<]+)</a>'
        r'.*?<span class="woocommerce-Price-amount amount"><bdi>([\d\.]+)'
    )

    matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)

    for match in matches:
        col_classes = match.group(1)
        url = match.group(2)
        name = _html.unescape(' '.join(match.group(3).split()))
        price_raw = match.group(4)

        # Normalize both the game_query and the product name for robust comparison
        # game_query might already be URL-decoded by the web server, but not HTML unescaped.
        normalized_game_query = _html.unescape(game_query).lower()
        normalized_name = name.lower()

        if normalized_game_query not in normalized_name:
            continue

        if url in seen_urls:
            continue
        seen_urls.add(url)

        # Stock: check for out-of-stock class on the wrapper div
        in_stock = 'out-of-stock' not in col_classes.lower()

        # Price: if there's a sale price, the pattern will first match
        # the original (del) price. We want the sale price (ins) instead.
        # Get context to find ins price if present
        context_start = max(0, match.start())
        context_end = min(len(content), match.end() + 200)
        context = content[context_start:context_end]

        ins_match = re.search(r'<ins[^>]*>.*?<bdi>([\d\.]+)', context, re.DOTALL)
        if ins_match:
            price_raw = ins_match.group(1)

        try:
            price = float(price_raw)
        except ValueError:
            continue

        products.append({
            'name': name,
            'price': price,
            'is_in_stock': in_stock,
            'url': url
        })

    return products

# Fallback HTML parser for No Label X
def parse_nolabelx_html(content, game_query):
    """HTML/markdown parser for No Label X (Skroutz board games shop page)."""
    if not content:
        return []
    products = []
    seen_urls = set()
    query_words = normalize_for_match(_html.unescape(game_query)).split()

    name_pattern = re.compile(
        r'<a\s[^>]*class="js-sku-link"[^>]*href="((?:https://www\.skroutz\.gr)?/s/[^"?]+)[^"]*"[^>]*>'
        r'([^<]+)</a>',
        re.IGNORECASE
    )
    price_pattern = re.compile(
        r'<a[^>]*class="js-sku-link sku-link"[^>]*>([\d,\.]+)\s*€',
        re.IGNORECASE
    )

    name_matches = list(name_pattern.finditer(content))
    price_matches = list(price_pattern.finditer(content))

    price_idx = 0
    for name_match in name_matches:
        while price_idx < len(price_matches) and price_matches[price_idx].start() < name_match.start():
            price_idx += 1
        if price_idx >= len(price_matches):
            break

        raw_url = name_match.group(1)
        url = extract_skroutz_store_product_url(content, raw_url, name_match.start())
        raw_name = _html.unescape(' '.join(name_match.group(2).split()))
        price_raw = price_matches[price_idx].group(1).replace(',', '.')

        clean_name = sanitize_nolabelx_name(raw_name)
        clean_name_normalized = normalize_for_match(clean_name)
        if not _query_words_in_text(query_words, clean_name_normalized):
            continue
        if url in seen_urls:
            continue
        seen_urls.add(url)
        try:
            price = float(price_raw)
        except ValueError:
            continue

        context_start = max(0, name_match.start() - 100)
        context_end = min(len(content), price_matches[price_idx].end() + 500)
        context = content[context_start:context_end]
        in_stock = 'out-of-stock' not in context.lower() and 'εξαντλημένο' not in context.lower()

        products.append({
            'name': raw_name,
            'price': price,
            'is_in_stock': in_stock,
            'url': url
        })
        price_idx += 1

    if products:
        return products

    # Firecrawl can return transformed markdown-like content for Skroutz pages.
    md_link_pattern = re.compile(
        r'\[([^\]]+)\]\(((?:https://www\.skroutz\.gr)?/s/[^\s\)]+)\)',
        re.IGNORECASE,
    )

    for name_match in md_link_pattern.finditer(content):
        raw_name = _html.unescape(' '.join(name_match.group(1).split()))
        if not raw_name:
            continue
        if re.fullmatch(r'[0-9]+(?:[.,][0-9]{2})?\s*€', raw_name):
            continue
        if raw_name.lower().startswith('image'):
            continue

        raw_url = name_match.group(2)
        url = extract_skroutz_store_product_url(content, raw_url, name_match.start())
        clean_name = sanitize_nolabelx_name(raw_name)
        clean_name_normalized = normalize_for_match(clean_name)
        if not _query_words_in_text(query_words, clean_name_normalized):
            continue
        if url in seen_urls:
            continue

        local_context = content[name_match.end(): min(len(content), name_match.end() + 500)]
        price_match = re.search(r'([0-9]+(?:[.,][0-9]{2}))\s*€', local_context, re.IGNORECASE)
        if not price_match:
            continue

        try:
            price = float(price_match.group(1).replace(',', '.'))
        except ValueError:
            continue

        local_lower = local_context.lower()
        in_stock = 'out-of-stock' not in local_lower and 'εξαντλη' not in local_lower

        products.append({
            'name': raw_name,
            'price': price,
            'is_in_stock': in_stock,
            'url': url
        })
        seen_urls.add(url)

    return products

# Fallback HTML parser for Lex Hobby Store
def parse_lexhobby_html(content, game_query):
    """HTML parser for Lex Hobby Store (Skroutz board games shop page)"""
    if not content:
        return []
    products = []
    seen_urls = set()

    name_pattern = re.compile(
        r'<a\s[^>]*class="js-sku-link"[^>]*href="((?:https://www\.skroutz\.gr)?/s/[^"?]+)[^"]*"[^>]*>'
        r'([^<]+)</a>',
        re.IGNORECASE
    )
    price_pattern = re.compile(
        r'<a[^>]*class="js-sku-link sku-link"[^>]*>([\d,\.]+)\s*€',
        re.IGNORECASE
    )

    name_matches = list(name_pattern.finditer(content))
    price_matches = list(price_pattern.finditer(content))

    price_idx = 0
    for name_match in name_matches:
        while price_idx < len(price_matches) and price_matches[price_idx].start() < name_match.start():
            price_idx += 1
        if price_idx >= len(price_matches):
            break

        raw_url = name_match.group(1)
        url = extract_skroutz_store_product_url(content, raw_url, name_match.start())
        raw_name = _html.unescape(' '.join(name_match.group(2).split()))
        price_raw = price_matches[price_idx].group(1).replace(',', '.')

        decoded_game_query = _html.unescape(game_query).lower().replace(':', '').strip()
        clean_name = sanitize_lexhobby_name(raw_name)
        clean_name_normalized = ' '.join(clean_name.replace(':', ' ').replace('-', ' ').split())
        if not all(w in clean_name_normalized for w in decoded_game_query.split()):
            continue
        if url in seen_urls:
            continue
        seen_urls.add(url)
        try:
            price = float(price_raw)
        except ValueError:
            continue

        context_start = max(0, name_match.start() - 100)
        context_end = min(len(content), price_matches[price_idx].end() + 500)
        context = content[context_start:context_end]
        in_stock = 'out-of-stock' not in context.lower() and 'εξαντλημένο' not in context.lower()

        products.append({
            'name': raw_name,
            'price': price,
            'is_in_stock': in_stock,
            'url': url
        })
        price_idx += 1

    return products

# Fallback HTML parser for Tech City
def parse_techcity_html(content, game_query):
    """HTML parser for Tech City (Skroutz board games shop page)"""
    if not content:
        return []
    products = []
    seen_urls = set()

    name_pattern = re.compile(
        r'<a\s[^>]*class="js-sku-link"[^>]*href="((?:https://www\.skroutz\.gr)?/s/[^"?]+)[^"]*"[^>]*>'
        r'([^<]+)</a>',
        re.IGNORECASE
    )
    price_pattern = re.compile(
        r'<a[^>]*class="js-sku-link sku-link"[^>]*>([\d,\.]+)\s*€',
        re.IGNORECASE
    )

    name_matches = list(name_pattern.finditer(content))
    price_matches = list(price_pattern.finditer(content))

    price_idx = 0
    for name_match in name_matches:
        while price_idx < len(price_matches) and price_matches[price_idx].start() < name_match.start():
            price_idx += 1
        if price_idx >= len(price_matches):
            break

        raw_url = name_match.group(1)
        url = extract_skroutz_store_product_url(content, raw_url, name_match.start())
        raw_name = _html.unescape(' '.join(name_match.group(2).split()))
        price_raw = price_matches[price_idx].group(1).replace(',', '.')

        decoded_game_query = _html.unescape(game_query).lower().replace(':', '').strip()
        clean_name = sanitize_nolabelx_name(raw_name)
        clean_name_normalized = ' '.join(clean_name.replace(':', ' ').replace('-', ' ').split())
        if not all(w in clean_name_normalized for w in decoded_game_query.split()):
            continue
        if url in seen_urls:
            continue
        seen_urls.add(url)
        try:
            price = float(price_raw)
        except ValueError:
            continue

        context_start = max(0, name_match.start() - 100)
        context_end = min(len(content), price_matches[price_idx].end() + 500)
        context = content[context_start:context_end]
        in_stock = 'out-of-stock' not in context.lower() and 'εξαντλημένο' not in context.lower()

        products.append({
            'name': raw_name,
            'price': price,
            'is_in_stock': in_stock,
            'url': url
        })
        price_idx += 1

    return products

# Fallback HTML parser for Game Theory
def parse_gametheory_html(content, game_query):
    """HTML parser for Game Theory (Skroutz board games shop page)"""
    if not content:
        return []
    products = []
    seen_urls = set()

    name_pattern = re.compile(
        r'<a\s[^>]*class="js-sku-link"[^>]*href="((?:https://www\.skroutz\.gr)?/s/[^"?]+)[^"]*"[^>]*>'
        r'([^<]+)</a>',
        re.IGNORECASE
    )
    price_pattern = re.compile(
        r'<a[^>]*class="js-sku-link sku-link"[^>]*>([\d,\.]+)\s*€',
        re.IGNORECASE
    )

    name_matches = list(name_pattern.finditer(content))
    price_matches = list(price_pattern.finditer(content))

    price_idx = 0
    for name_match in name_matches:
        while price_idx < len(price_matches) and price_matches[price_idx].start() < name_match.start():
            price_idx += 1
        if price_idx >= len(price_matches):
            break

        raw_url = name_match.group(1)
        url = extract_skroutz_store_product_url(content, raw_url, name_match.start())
        raw_name = _html.unescape(' '.join(name_match.group(2).split()))
        price_raw = price_matches[price_idx].group(1).replace(',', '.')

        decoded_game_query = _html.unescape(game_query).lower().replace(':', '').strip()
        clean_name = sanitize_nolabelx_name(raw_name)
        clean_name_normalized = ' '.join(clean_name.replace(':', ' ').replace('-', ' ').split())
        if not all(w in clean_name_normalized for w in decoded_game_query.split()):
            continue
        if url in seen_urls:
            continue
        seen_urls.add(url)
        try:
            price = float(price_raw)
        except ValueError:
            continue

        context_start = max(0, name_match.start() - 100)
        context_end = min(len(content), price_matches[price_idx].end() + 500)
        context = content[context_start:context_end]
        in_stock = 'out-of-stock' not in context.lower() and 'εξαντλημένο' not in context.lower()

        products.append({
            'name': raw_name,
            'price': price,
            'is_in_stock': in_stock,
            'url': url
        })
        price_idx += 1

    return products

# Fallback HTML parser for Mystery Bay (Wix store with JSON warmup data)
def parse_mysterybay_html(content, game_query):
    """Parser for Mystery Bay (Wix store - uses markdown content)"""
    if not content:
        return []
    products = []
    seen_urls = set()

    # Mystery Bay markdown format per product:
    # [Name](https://www.mystery-bay.com/product-page/slug "Name")
    # PRICE€Εξαντλημένο  OR  PRICE €Προσθήκη στο καλάθι
    pattern = (
        r'\[([^\]]+)\]\((https://www\.mystery-bay\.com/product-page/[^\s\)]+)'
        r'(?:\s+"[^"]*")?\)'
        r'\s*\n([\d,\.\s]+€)(.*?)(?=\n-|\Z)'
    )

    matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)

    for match in matches:
        name = ' '.join(match.group(1).split())
        url = match.group(2).strip()
        price_raw = match.group(3).strip()
        stock_text = match.group(4).strip()

        if game_query.lower() not in name.lower():
            continue

        if url in seen_urls:
            continue
        seen_urls.add(url)

        # Clean price
        price_str = re.sub(r'[€\s]', '', price_raw).replace(',', '.')
        try:
            price = float(price_str)
        except ValueError:
            continue

        # Stock detection
        in_stock = (
            'εξαντλημένο' not in stock_text.lower() and
            'εξαντλήθηκε' not in stock_text.lower() and
            'out of stock' not in stock_text.lower()
        )

        products.append({
            'name': name,
            'price': price,
            'is_in_stock': in_stock,
            'url': url
        })

    return products

# Fallback HTML parser for Meeple Planet
def parse_meepleplanet_html(content, game_query):
    """HTML parser for Meeple Planet WooCommerce search results."""
    if not content:
        return []

    def _is_meepleplanet_boardgame(block_html, name, product_url):
        """Keep only board/card-game related products and reject merch/figures."""
        name_l = normalize_for_match(_html.unescape(name or ''))
        url_l = urllib.parse.unquote(product_url or '').lower()
        block_l = normalize_for_match(_html.unescape(block_html or ''))

        category_markers = []
        category_match = re.search(r'"category":\s*\[(.*?)\]', block_html, re.DOTALL | re.IGNORECASE)
        if category_match:
            category_markers = [
                normalize_for_match(_html.unescape(item))
                for item in re.findall(r'"([^"]+)"', category_match.group(1))
            ]
        category_text = ' | '.join(category_markers)
        class_text = ' '.join(re.findall(r'product_cat-[^"\s>]+', block_html.lower()))
        combined_l = f"{name_l} {url_l} {block_l} {category_text} {class_text}"

        blocked_markers = [
            'funko pop', 'funko-pop', 'pop!', 'φιγούρα', 'φιγουρα', 'figure',
            'action figure', 'συλλεκτικές φιγούρες', 'συλλεκτικες φιγουρες',
            'mouse pad', 'mousepad', 'geek home', 'ρολόγια', 'ρολογια',
            'κούπες', 'κουπες', 'κούπα', 'κουπα', 'mug', 'lamp', 'light',
            'poster', 'product_cat-funko-pop', 'product_cat-action-figures',
            'action-figures-marvel-dc-anime', 'role playing games',
            'rpg miniatures', 'miniature', 'miniatures', 'marvelous minis',
            'nolzurs marvelous', 'select toys', 'diamond select', 'retro hulk'
        ]
        if any(marker in combined_l for marker in blocked_markers):
            return False

        positive_markers = [
            'επιτραπέζια παιχνίδια', 'επιτραπεζια παιχνιδια', 'στρατηγικής',
            'στρατηγικης', 'board game', 'board games', 'card game', 'card games',
            'παιχνίδια καρτών', 'παιχνιδια καρτων', 'expansion', 'επέκταση',
            'επεκταση', 'tcg', 'lcg', 'ccg', 'unmatched', 'marvel united',
            'splendor', 'munchkin', 'dice throne', 'zombicide', 'villainous',
            'legendary', 'champions', 'booster', 'starter deck', 'starter-deck',
            'deck box', 'deck-box', 'playmat', 'sleeves', 'dice'
        ]
        return any(marker in combined_l for marker in positive_markers)

    products = []
    seen_urls = set()
    query_norm = normalize_for_match(_html.unescape(game_query))
    query_words = query_norm.split()

    card_starts = [
        m.start() for m in re.finditer(
            r'<div[^>]*class="[^"]*\bproduct-small\b[^"]*\bproduct\b[^"]*"',
            content,
            re.IGNORECASE,
        )
    ]
    if not card_starts:
        return []

    for i, start in enumerate(card_starts):
        end = card_starts[i + 1] if i + 1 < len(card_starts) else len(content)
        block = content[start:end]

        name_match = re.search(
            r'<a[^>]*href="(https?://meeple-planet\.com/[^"]+)"[^>]*class="[^"]*woocommerce-LoopProduct-link[^"]*"[^>]*>([\s\S]*?)</a>',
            block,
            re.IGNORECASE,
        )
        if not name_match:
            name_match = re.search(
                r'<a[^>]*class="[^"]*woocommerce-LoopProduct-link[^"]*"[^>]*href="(https?://meeple-planet\.com/[^"]+)"[^>]*>([\s\S]*?)</a>',
                block,
                re.IGNORECASE,
            )
        if not name_match:
            continue

        url = _html.unescape(name_match.group(1).strip())
        name = _html.unescape(' '.join(re.sub(r'<[^>]+>', ' ', name_match.group(2)).split()))
        if not name or url in seen_urls:
            continue

        name_norm = normalize_for_match(name)
        if not _query_words_in_text(query_words, name_norm):
            continue
        if not _is_meepleplanet_boardgame(block, name, url):
            continue

        price = None
        data_price_match = re.search(r'"price":\s*([0-9]+(?:\.[0-9]+)?)', block, re.IGNORECASE)
        if data_price_match:
            try:
                price = float(data_price_match.group(1))
            except ValueError:
                price = None

        if price is None:
            price_match = re.search(
                r'woocommerce-Price-currencySymbol[^>]*>€</span>\s*([\d.,]+)',
                block,
                re.DOTALL | re.IGNORECASE,
            )
            if not price_match:
                continue
            price_raw = price_match.group(1)
            if '.' in price_raw and ',' in price_raw:
                price_str = price_raw.replace('.', '').replace(',', '.')
            elif '.' in price_raw and len(price_raw.split('.')[-1]) <= 2:
                price_str = price_raw
            elif ',' in price_raw:
                price_str = price_raw.replace(',', '.')
            else:
                price_str = price_raw
            try:
                price = float(price_str)
            except ValueError:
                continue

        block_lower = block.lower()
        is_preorder = (
            'προπαραγγελία' in block_lower or
            'pre-order' in block_lower or
            'yith-pre-order-product' in block_lower
        )
        is_positive_stock = (
            ' instock ' in block_lower or
            'status-publish instock' in block_lower or
            'σε απόθεμα' in block_lower or
            'add_to_cart_button' in block_lower
        )
        is_oos = (
            'out-of-stock' in block_lower or
            'outofstock' in block_lower or
            'εξαντλη' in block_lower or
            'μη διαθέσιμο' in block_lower
        )
        in_stock = is_preorder or (is_positive_stock and not is_oos)

        display_name = f"[Preorder] {name}" if is_preorder else name
        products.append({
            'name': display_name,
            'price': price,
            'is_in_stock': in_stock,
            'url': url,
        })
        seen_urls.add(url)

    return products

# Fallback HTML parser for GamesUniverse (WooCommerce with custom theme)
def parse_gamesuniverse_html(content, game_query):
    if not content: return []
    products = []
    seen_urls = set()
    query_clean = game_query.lower().strip()
    query_words = query_clean.split()

    # 1. Split by the product-description div to isolate each game
    blocks = content.split('class="product-description"')

    for block in blocks[1:]: # Skip the first chunk (header)
        # 2. Extract Name & URL from the product-title H2
        # Note: GamesUniverse uses class="h3 product-title" in your snippet
        name_match = re.search(r'class="[^"]*product-title[^"]*".*?<a href="([^"]+)"[^>]*>([^<]+)</a>', block, re.DOTALL | re.IGNORECASE)
        if not name_match:
            continue

        url = name_match.group(1).strip()
        name = _html.unescape(' '.join(name_match.group(2).split()))

        # Filter: only keep board game products (URL path /epitrapezia/)
        if '/epitrapezia/' not in url.lower():
            continue

        # 3. Extract Price (Targeting 'product-price' as seen in your snippet)
        # We look for the span with class "product-price"
        price_match = re.search(r'class="product-price"[^>]*>([\d,.\s]+)', block)
        if not price_match:
            # Fallback for search grid which might use just "price"
            price_match = re.search(r'class="price"[^>]*>([\d,.\s]+)', block)

        if not price_match:
            continue

        # Clean price: "55,71 €" -> 55.71
        price_raw = price_match.group(1).replace('€', '').strip().replace(',', '.')
        try:
            price_val = float(price_raw)
        except ValueError:
            continue

        # 4. Filtering (Fuzzy matching)
        if not all(word in name.lower() for word in query_words):
            continue

        if url in seen_urls:
            continue
        seen_urls.add(url)

        # 5. Availability
        # In this specific snippet, availability isn't inside the description div,
        # it's usually in the parent article.
        # But we can check for common "Out of Stock" labels in the block.
        is_oos = 'product-unavailable' in block or 'Εξαντλημένο' in block

        # If it doesn't say "Out of Stock", assume it's available or check for cart button
        # GamesUniverse usually has "Προσθήκη στο καλάθι" nearby
        in_stock = not is_oos

        products.append({
            "name": name,
            "price": price_val,
            "is_in_stock": in_stock,
            "url": url
        })

    return products

# Fallback HTML parser for Meeple On Board
def parse_meepleonboard_html(content, game_query):
    """HTML parser for Meeple On Board (WooCommerce)"""
    if not content:
        return []
    products = []
    seen_urls = set()

    # Each product is a div with class "product-small col"
    # We capture: out-of-stock indicator, product URL+name, and price (sale or regular)
    pattern = (
        r'<div class="product-small col([^"]*?)"[^>]*?>'
        r'.*?<p class="name product-title woocommerce-loop-product__title"[^>]*?>'
        r'.*?<a href="(https://meepleonboard\.gr/[^"]+)"[^>]*?>([^<]+)</a>'
        r'.*?<span class="woocommerce-Price-amount amount"><bdi>([\d\.]+)'
    )

    matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)

    for match in matches:
        col_classes = match.group(1)
        url = match.group(2)
        name = _html.unescape(' '.join(match.group(3).split()))
        price_raw = match.group(4)

        # Normalize both the game_query and the product name for robust comparison
        normalized_game_query = _html.unescape(game_query).lower()
        normalized_name = name.lower()

        if normalized_game_query not in normalized_name:
            continue

        if url in seen_urls:
            continue
        seen_urls.add(url)

        # Stock: check for out-of-stock class on the wrapper div
        in_stock = 'out-of-stock' not in col_classes.lower()

        # Price: if there's a sale price, the pattern will first match
        # the original (del) price. We want the sale price (ins) instead.
        # Get context to find ins price if present
        context_start = max(0, match.start())
        context_end = min(len(content), match.end() + 200)
        context = content[context_start:context_end]

        ins_match = re.search(r'<ins[^>]*>.*?<bdi>([\d\.]+)', context, re.DOTALL)
        if ins_match:
            price_raw = ins_match.group(1)

        try:
            price = float(price_raw)
        except ValueError:
            continue

        products.append({
            'name': name,
            'price': price,
            'is_in_stock': in_stock,
            'url': url
        })

    return products

# Fallback HTML parser for RollnPlay
def parse_rollnplay_html(content, game_query):
    """HTML parser for RollnPlay WooCommerce search results."""
    if not content:
        return []

    def clean_price(price_str):
        cleaned = _html.unescape(price_str).replace('\xa0', ' ')
        cleaned = re.sub(r'[^0-9,.]', '', cleaned)
        if not cleaned:
            raise ValueError("Missing price")
        if ',' in cleaned and '.' in cleaned:
            cleaned = cleaned.replace('.', '').replace(',', '.')
        elif ',' in cleaned:
            cleaned = cleaned.replace(',', '.')
        return float(cleaned)

    def _is_rollnplay_boardgame_product(block_html, name, product_url):
        """Reject figure/merch listings while keeping tabletop games and expansions."""
        name_l = normalize_for_match(_html.unescape(name or ''))
        url_l = urllib.parse.unquote(product_url or '').lower()
        block_text = normalize_for_match(_html.unescape(re.sub(r'<[^>]+>', ' ', block_html or '')))
        combined_l = f"{name_l} {url_l} {block_text}"

        blocked_markers = [
            'pvc figure', 'action figure', 'figure ', ' figure', 'figurine',
            'diorama', 'statue', 'bust', 'nendoroid', 'funko', 'gallery '
        ]
        if any(marker in combined_l for marker in blocked_markers):
            return False

        return True

    products = []
    seen_urls = set()
    query_norm = normalize_for_match(_html.unescape(game_query))
    query_words = query_norm.split()

    body_lower = content.lower()
    is_real_product_page = (
        'single-product' in body_lower or
        re.search(r'<meta[^>]*property="og:url"[^>]*content="https://rollnplay\.gr/product/[^"]+"', content, re.IGNORECASE) or
        re.search(r'<link[^>]*rel="canonical"[^>]*href="https://rollnplay\.gr/product/[^"]+"', content, re.IGNORECASE)
    )

    # CASE 1: actual single product page redirect
    if is_real_product_page:
        name_match = re.search(r'<h1[^>]*class="[^"]*product_title[^"]*"[^>]*>([^<]+)</h1>', content, re.IGNORECASE)
        if name_match:
            name = _html.unescape(' '.join(name_match.group(1).split()))
            name_norm = normalize_for_match(name)
            product_area = content[max(0, name_match.start() - 1200): min(len(content), name_match.start() + 7000)]
            product_area_lower = product_area.lower()

            if _query_words_in_text(query_words, name_norm) and _is_rollnplay_boardgame_product(product_area, name, ''):
                price_block_match = re.search(
                    r'<p[^>]*class=["\']price["\'][^>]*>([\s\S]*?)</p>',
                    product_area,
                    re.IGNORECASE,
                )
                price_block = price_block_match.group(1) if price_block_match else product_area

                price_match = re.search(
                    r'<ins[^>]*>[\s\S]*?<bdi>\s*([0-9]+(?:[.,][0-9]{2})?)',
                    price_block,
                    re.IGNORECASE,
                )
                if not price_match:
                    price_match = re.search(
                        r'<bdi>\s*([0-9]+(?:[.,][0-9]{2})?)',
                        price_block,
                        re.IGNORECASE,
                    )

                url_match = re.search(r'mailto:\?subject=[^"&]+&amp;body=(https://rollnplay\.gr/product/[^"&]+/)', content, re.IGNORECASE)
                if not url_match:
                    url_match = re.search(r'<meta[^>]*property=["\']og:url["\'][^>]*content=["\'](https://rollnplay\.gr/product/[^"\']+/?)', content, re.IGNORECASE)
                if not url_match:
                    url_match = re.search(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\'](https://rollnplay\.gr/product/[^"\']+/?)', content, re.IGNORECASE)

                is_out_of_stock = (
                    'availability stock out-of-stock' in product_area_lower or
                    'class="stock out-of-stock"' in product_area_lower or
                    "class='stock out-of-stock'" in product_area_lower or
                    'sold out' in product_area_lower or
                    'εξαντλημένο' in product_area_lower or
                    'out of stock' in product_area_lower
                )
                in_stock = not is_out_of_stock and (
                    'add_to_cart_button' in product_area_lower or
                    'single_add_to_cart_button' in product_area_lower or
                    'availability stock in-stock' in product_area_lower or
                    'class="stock in-stock"' in product_area_lower or
                    "class='stock in-stock'" in product_area_lower or
                    'instock' in product_area_lower or
                    'σε απόθεμα' in product_area_lower or
                    'in stock' in product_area_lower
                )

                if price_match:
                    try:
                        products.append({
                            'name': name,
                            'price': clean_price(price_match.group(1)),
                            'is_in_stock': in_stock,
                            'url': _html.unescape(url_match.group(1)) if url_match else f"https://rollnplay.gr/?s={urllib.parse.quote_plus(game_query)}&post_type=product"
                        })
                        return products
                    except ValueError:
                        pass

    # CASE 2: multiple search results
    # Use the outer <section class="product ..."> boundaries so stock classes
    # from the next card do not bleed into the current one.
    card_starts = [
        m.start() for m in re.finditer(
            r'<section[^>]*class=["\'][^"\']*\bproduct\b[^"\']*["\']',
            content,
            re.IGNORECASE
        )
    ]
    if not card_starts:
        card_starts = [
            m.start() for m in re.finditer(
                r'<div[^>]*class="[^"]*product-wrapper[^"]*"',
                content,
                re.IGNORECASE
            )
        ]

    for i, start in enumerate(card_starts):
        end = card_starts[i + 1] if i + 1 < len(card_starts) else len(content)
        block = content[start:end]

        if 'heading-title product-name' not in block:
            continue

        name_match = re.search(
            r'<h3[^>]*class="[^"]*heading-title product-name[^"]*"[^>]*>\s*<a href=["\'](https://rollnplay\.gr/product/[^"\']+/?)["\'][^>]*>([^<]+)</a>',
            block,
            re.IGNORECASE
        )
        if not name_match:
            continue

        url = _html.unescape(name_match.group(1).strip())
        name = _html.unescape(' '.join(name_match.group(2).split()))
        if not name or url in seen_urls:
            continue

        name_norm = normalize_for_match(name)
        if not _query_words_in_text(query_words, name_norm):
            continue
        if not _is_rollnplay_boardgame_product(block, name, url):
            continue

        price_match = re.search(
            r'<span class="price">.*?<ins[^>]*>.*?<bdi>([\d.,\s\xa0]+).*?<span[^>]*woocommerce-Price-currencySymbol[^>]*>(?:€|&euro;)</span>',
            block,
            re.DOTALL | re.IGNORECASE
        )
        if not price_match:
            price_match = re.search(
                r'<span class="price">.*?<span[^>]*woocommerce-Price-amount amount[^>]*><bdi>([\d.,\s\xa0]+).*?<span[^>]*woocommerce-Price-currencySymbol[^>]*>(?:€|&euro;)</span>',
                block,
                re.DOTALL | re.IGNORECASE
            )
        if not price_match:
            continue

        block_lower = block.lower()
        section_class_match = re.search(r'<section[^>]*class=["\']([^"\']+)["\']', block, re.IGNORECASE)
        section_classes = section_class_match.group(1).lower() if section_class_match else ''
        has_add_to_cart = 'add_to_cart_button' in block_lower or 'προσθήκη στο καλάθι' in block_lower
        is_explicitly_oos = (
            'outofstock' in section_classes or
            'out-of-stock' in block_lower or
            'sold out' in block_lower or
            'εξαντλημένο' in block_lower
        )
        in_stock = (
            ('instock' in section_classes or has_add_to_cart) and
            not is_explicitly_oos
        )

        try:
            products.append({
                'name': name,
                'price': clean_price(price_match.group(1)),
                'is_in_stock': in_stock,
                'url': url
            })
            seen_urls.add(url)
        except ValueError:
            continue

    return products

# Politeia board game / expansion detection.

def _is_politeia_boardgame(url, block):
    """Return True if a Politeia card looks like a board game product.

    Checks the product URL slug and the <h3> title (which often has a Greek
    subtitle like 'Επιτραπέζιο παιχνίδι …' after a <br>).  We intentionally
    avoid scanning the whole *block* because the last card's block can extend
    into unrelated footer/markdown content.
    """
    if not url and not block:
        return False
    # 1. Check the URL slug (transliterated Greek)
    url_lower = (url or "").lower()
    if "epitrapezio" in url_lower or "epektash" in url_lower:
        return True
    # 2. Check the <h3 class="title"> content (actual Greek)
    h3_match = re.search(r'<h3[^>]*class="[^"]*title[^"]*"[^>]*>([\s\S]*?)</h3>', block or "", re.IGNORECASE)
    if h3_match:
        h3_text = h3_match.group(1).lower()
        if "επιτραπέζιο" in h3_text or "επέκταση" in h3_text:
            return True
    return False

# Fallback HTML parser for Politeia
def parse_politeia_html(content, game_query):
    """HTML parser for Politeianet search results."""
    if not content:
        return []

    products = []
    seen_urls = set()
    query_norm = normalize_for_match(_html.unescape(game_query))
    query_words = query_norm.split()

    block_starts = [m.start() for m in re.finditer(r'<div class="fbr-result\b', content, re.IGNORECASE)]
    if not block_starts:
        return []

    for i, start in enumerate(block_starts):
        end = block_starts[i + 1] if i + 1 < len(block_starts) else len(content)
        block = content[start:end]

        url_match = re.search(
            r'<a[^>]*class="[^"]*overlay-link[^"]*"[^>]*href="([^"]+/el/products/[^"]+|/el/products/[^"]+)"',
            block,
            re.IGNORECASE,
        )
        if not url_match:
            continue

        url = _html.unescape(url_match.group(1).strip())
        if url.startswith('/'):
            url = f"https://www.politeianet.gr{url}"
        if url in seen_urls:
            continue

        if not _is_politeia_boardgame(url, block):
            continue

        name = ""
        title_attr_match = re.search(r'data-title="([^"]+)"', block, re.IGNORECASE)
        if title_attr_match:
            name = _html.unescape(' '.join(title_attr_match.group(1).split()))
        else:
            h3_match = re.search(r'<h3[^>]*class="[^"]*title[^"]*"[^>]*>([\s\S]*?)</h3>', block, re.IGNORECASE)
            if h3_match:
                name_html = re.sub(r'<br\s*/?>', ' ', h3_match.group(1), flags=re.IGNORECASE)
                name = _html.unescape(' '.join(re.sub(r'<[^>]+>', ' ', name_html).split()))

        if not name:
            continue

        name_norm = normalize_for_match(name)
        if not _query_words_in_text(query_words, name_norm):
            continue

        block_lower = block.lower()
        has_disabled_cart = bool(re.search(r'js-add-to-cart[^>]*disabled="disabled"', block, re.IGNORECASE))
        is_oos = (
            'εξαντλημένο' in block_lower or
            'εξαντλημένο στον εκδότη' in block_lower or
            'out of stock' in block_lower or
            'μη διαθέσιμο' in block_lower or
            'not-available-badge' in block_lower or
            has_disabled_cart
        )
        has_cart = (
            'js-add-to-cart' in block_lower or
            'add-to-cart' in block_lower or
            'προσθήκη στο καλάθι' in block_lower
        )
        in_stock = has_cart and not is_oos

        # Politeia shows no reliable price for out-of-stock cards; avoid inheriting stray prices.
        if is_oos:
            price = "N/A"
        else:
            price_match = re.search(
                r'<(?:span|div)[^>]*class="[^"]*final[^"]*"[^>]*>\s*([0-9]+(?:[\.,][0-9]{2})?)\s*€',
                block,
                re.IGNORECASE,
            )
            if not price_match:
                price_match = re.search(r'([0-9]+(?:[\.,][0-9]{2})?)\s*€', block, re.IGNORECASE)

            if price_match:
                try:
                    price = float(price_match.group(1).replace(',', '.'))
                except ValueError:
                    price = "N/A"
            else:
                price = "N/A"

        products.append({
            'name': name,
            'price': price,
            'is_in_stock': in_stock,
            'url': url,
        })
        seen_urls.add(url)

    return products


# Fallback HTML parser for Kaissa
def parse_kaissa_html(content, game_query):
    """HTML parser for Kaissa search results."""
    if not content:
        return []

    products = []
    seen_urls = set()
    query_norm = normalize_for_match(_html.unescape(game_query))
    query_words = query_norm.split()

    block_starts = [m.start() for m in re.finditer(r'<div class="product-details">', content, re.IGNORECASE)]
    if not block_starts:
        return []

    for i, start in enumerate(block_starts):
        end = block_starts[i + 1] if i + 1 < len(block_starts) else len(content)
        block = content[start:end]

        name_match = re.search(
            r'<a[^>]*class="[^"]*product-item-link[^"]*"[^>]*href="([^"]+)"[^>]*>([\s\S]*?)</a>',
            block,
            re.IGNORECASE,
        )
        if not name_match:
            continue

        url = _html.unescape(name_match.group(1).strip())
        if url.startswith('/'):
            url = f"https://kaissagames.com{url}"
        if url in seen_urls:
            continue

        name = _html.unescape(' '.join(re.sub(r'<[^>]+>', ' ', name_match.group(2)).split()))
        if not name:
            continue

        name_norm = normalize_for_match(name)
        if not _query_words_in_text(query_words, name_norm):
            continue

        price = "N/A"
        price_attr_match = re.search(r'data-price-amount="([0-9]+(?:\.[0-9]+)?)"', block, re.IGNORECASE)
        if price_attr_match:
            try:
                price = float(price_attr_match.group(1))
            except ValueError:
                price = "N/A"
        else:
            price_match = re.search(r'<span class="price">\s*([0-9]+(?:[\.,][0-9]{2})?)', block, re.IGNORECASE)
            if price_match:
                try:
                    price = float(price_match.group(1).replace(',', '.'))
                except ValueError:
                    price = "N/A"

        block_lower = block.lower()
        is_oos = (
            'stock unavailable' in block_lower or
            'μη διαθέσιμο' in block_lower or
            'coming-soon' in block_lower or
            'αναμένεται σύντομα' in block_lower or
            'out of stock' in block_lower or
            'εξαντλη' in block_lower
        )
        has_add_to_cart = (
            'product-tocart' in block_lower or
            'action tocart' in block_lower or
            '>αγορά<' in block_lower
        )
        in_stock = has_add_to_cart and not is_oos

        products.append({
            'name': name,
            'price': price,
            'is_in_stock': in_stock,
            'url': url,
        })
        seen_urls.add(url)

    return products


# Fallback HTML parser for Gaming Galaxy
def parse_gaminggalaxy_html(content, game_query):
    """HTML parser for Gaming Galaxy search results."""
    if not content:
        return []

    def _is_boardgame_related_gaminggalaxy_product(product_url, name, block_html):
        """Exclude obvious collectibles, gifts, and video-game products."""
        url_l = (product_url or '').lower()
        name_l = (name or '').lower()
        combined_l = f"{url_l} {name_l}"

        strong_blocked_markers = [
            'collectible',
            'collectibles',
            'roleplay',
            'art print',
            'unframed',
            'poster',
            'nintendo switch',
            'switch 2',
            ' for nsw',
            ' for nsw2',
            'nsw2',
            'playstation',
            'ps5',
            'ps4',
            'xbox',
            'hot toys',
            'sideshow',
            'threezero',
            'exquisite gaming',
            'cable guy',
            'funko',
            'banpresto',
            'nendoroid',
            'amiibo',
            'marvel legends series',
        ]
        if any(marker in combined_l for marker in strong_blocked_markers):
            return False

        positive_markers = [
            'board-game',
            'board game',
            'card-game',
            'card game',
            'expansion',
            'booster',
            'starter deck',
            'starter-deck',
            'deck box',
            'deck-box',
            'playmat',
            'sleeves',
            'dice',
            'rpg',
            'zombicide',
            'tcg',
            'lcg',
        ]
        if any(marker in combined_l for marker in positive_markers):
            return True

        weak_blocked_markers = ['action figure', 'figure', 'statue', 'mask']
        if any(marker in combined_l for marker in weak_blocked_markers):
            return False

        return False

    products = []
    seen_urls = set()
    query_norm = normalize_for_match(_html.unescape(game_query))
    query_words = query_norm.split()

    card_starts = [
        m.start() for m in re.finditer(
            r'<div[^>]*class="[^"]*\bitem\b[^"]*\bh-100\b[^"]*"',
            content,
            re.IGNORECASE,
        )
    ]
    if not card_starts:
        card_starts = [
            m.start() for m in re.finditer(
                r'<div[^>]*class="[^"]*product-item-info[^"]*"',
                content,
                re.IGNORECASE,
            )
        ]
    if not card_starts:
        card_starts = [
            m.start() for m in re.finditer(
                r'<li[^>]*class="[^"]*product-item[^"]*"',
                content,
                re.IGNORECASE,
            )
        ]
    if not card_starts:
        return []

    for i, start in enumerate(card_starts):
        end = card_starts[i + 1] if i + 1 < len(card_starts) else len(content)
        block = content[start:end]

        name_match = re.search(
            r'<div[^>]*class="[^"]*product-name[^"]*"[^>]*>[\s\S]*?<a[^>]*href="([^"]+)"[^>]*>([\s\S]*?)</a>',
            block,
            re.IGNORECASE,
        )
        if not name_match:
            name_match = re.search(
                r'<a[^>]*class="[^"]*product-item-link[^"]*"[^>]*href="([^"]+)"[^>]*>([\s\S]*?)</a>',
                block,
                re.IGNORECASE,
            )
        if not name_match:
            continue

        raw_url = _html.unescape(name_match.group(1).strip())
        url = raw_url if raw_url.startswith('http') else f"https://ggalaxy.gr{raw_url}"
        if url in seen_urls:
            continue

        name = _html.unescape(' '.join(re.sub(r'<[^>]+>', ' ', name_match.group(2)).split()))
        if not name:
            continue

        name_norm = normalize_for_match(name)
        if not _query_words_in_text(query_words, name_norm):
            continue

        if not _is_boardgame_related_gaminggalaxy_product(url, name, block):
            continue

        price = "N/A"
        price_attr_match = re.search(r'data-price-amount="([0-9]+(?:\.[0-9]+)?)"', block, re.IGNORECASE)
        if price_attr_match:
            try:
                price = float(price_attr_match.group(1))
            except ValueError:
                price = "N/A"
        else:
            price_match = re.search(
                r'<span[^>]*class="[^"]*price[^"]*"[^>]*>\s*([0-9]+(?:[\.,][0-9]{2})?)',
                block,
                re.IGNORECASE,
            )
            if price_match:
                try:
                    price = float(price_match.group(1).replace(',', '.'))
                except ValueError:
                    price = "N/A"

        block_lower = block.lower()
        block_norm_space = ' '.join(block_lower.split())
        is_preorder = 'προπαραγγελία' in block_norm_space
        is_positive_stock = (
            'περιορισμένη διαθεσιμότητα' in block_norm_space or
            'παράδοση σε 4 - 10 ημέρες' in block_norm_space or
            'άμεσα διαθέσιμο' in block_norm_space
        )
        is_negative_stock = (
            'μη διαθέσιμο' in block_lower or
            'εξαντλη' in block_lower or
            'out of stock' in block_lower
        )
        has_add_to_cart = (
            'tocart' in block_lower or
            'add to cart' in block_lower or
            'προσθήκη στο καλάθι' in block_lower
        )

        in_stock = is_preorder or is_positive_stock or (has_add_to_cart and not is_negative_stock)
        display_name = f"[Preorder] {name}" if is_preorder else name

        products.append({
            'name': display_name,
            'price': price,
            'is_in_stock': in_stock,
            'url': url,
        })
        seen_urls.add(url)

    return products


# Fallback HTML parser for GenX
def parse_genx_html(content, game_query):
    """Parser for GenX search results (board games only)."""
    if not content:
        return []

    products = []
    seen_urls = set()
    query_norm = normalize_for_match(_html.unescape(game_query))
    query_words = query_norm.split()

    def _to_boardgame_url(raw_href):
        if not raw_href:
            return ""
        href = _html.unescape(raw_href).strip()
        href_lower = href.lower()

        # Explicitly reject video-game paths.
        if '/video--games/' in href_lower or href_lower.startswith('video--games/'):
            return ""

        # Accept both relative and absolute board-game links.
        if href_lower.startswith('https://www.genx.gr/') or href_lower.startswith('http://www.genx.gr/'):
            rel = re.sub(r'^https?://www\.genx\.gr/?', '', href, flags=re.IGNORECASE)
            if not rel.lower().startswith('epitrapezia--paixnidia/'):
                return ""
            return f"https://www.genx.gr/{rel.lstrip('/')}"

        rel = href.lstrip('/')
        if not rel.lower().startswith('epitrapezia--paixnidia/'):
            return ""
        return f"https://www.genx.gr/{rel}"

    # Pass 1: card-based parsing (best when full HTML is available).
    card_starts = [
        m.start() for m in re.finditer(
            r'<div[^>]*class="[^"]*product-loop-viewCat[^"]*"',
            content,
            re.IGNORECASE,
        )
    ]
    for i, start in enumerate(card_starts):
        end = card_starts[i + 1] if i + 1 < len(card_starts) else len(content)
        block = content[start:end]
        block_lower = block.lower()

        link_match = re.search(r'<a[^>]*href="([^"]+)"[^>]*>', block, re.IGNORECASE)
        if not link_match:
            continue

        url = _to_boardgame_url(link_match.group(1))
        if not url or url in seen_urls:
            continue

        name_match = re.search(
            r'<a[^>]*class="[^"]*vc-product-title[^"]*"[^>]*title="([^"]+)"',
            block,
            re.IGNORECASE,
        )
        if name_match:
            name = _html.unescape(' '.join(name_match.group(1).split()))
        else:
            h2_match = re.search(r'<h2[^>]*>([\s\S]*?)</h2>', block, re.IGNORECASE)
            if not h2_match:
                continue
            name = _html.unescape(' '.join(re.sub(r'<[^>]+>', ' ', h2_match.group(1)).split()))

        if not name:
            continue

        name_norm = normalize_for_match(name)
        if not _query_words_in_text(query_words, name_norm):
            continue

        price_match = re.search(
            r'class="[^"]*vc-product-price[^"]*"[^>]*>\s*([0-9]+(?:,[0-9]{2})?)\s*€',
            block,
            re.IGNORECASE,
        )
        if not price_match:
            continue

        try:
            price = float(price_match.group(1).replace(',', '.'))
        except ValueError:
            continue

        is_oos = (
            'out-of-stock' in block_lower or
            'out of stock' in block_lower or
            'εξαντλη' in block_lower
        )

        products.append({
            'name': name,
            'price': price,
            'is_in_stock': not is_oos,
            'url': url,
        })
        seen_urls.add(url)

    # Pass 2: fallback when Firecrawl returns transformed/markdown-like output.
    if not products:
        md_link_pattern = re.compile(
            r'\[([^\]]+)\]\((https?://www\.genx\.gr/epitrapezia--paixnidia/[^\s\)]+)',
            re.IGNORECASE,
        )

        for m in md_link_pattern.finditer(content):
            name = _html.unescape(' '.join(m.group(1).split()))
            url = _to_boardgame_url(m.group(2))
            if not name or not url or url in seen_urls:
                continue

            name_norm = normalize_for_match(name)
            if not _query_words_in_text(query_words, name_norm):
                continue

            local = content[m.end(): min(len(content), m.end() + 260)]
            price_match = re.search(r'([0-9]+(?:,[0-9]{2}))\s*€', local)
            if not price_match:
                continue

            try:
                price = float(price_match.group(1).replace(',', '.'))
            except ValueError:
                continue

            local_lower = local.lower()
            is_oos = 'out of stock' in local_lower or 'εξαντλη' in local_lower

            products.append({
                'name': name,
                'price': price,
                'is_in_stock': not is_oos,
                'url': url,
            })
            seen_urls.add(url)

    return products

# scrape with retry logic
def scrape_with_retry(app, url, store_name, max_retries=3, use_html_fallback=False):
    """Scrape with retry logic and exponential backoff"""
    for attempt in range(max_retries):
        try:
            # Adjust timeout and wait based on store
            if store_name == "Boards of Madness":
                timeout = 60000
                wait_time = 15000 + (attempt * 5000)
                actions = [
                    {"type": "wait", "milliseconds": wait_time},
                    {"type": "scroll", "direction": "down"},
                    {"type": "wait", "milliseconds": 3000}
                ]

            else:
                timeout = 60000 + (attempt * 30000)
                wait_time = 4000 + (attempt * 2000)
                actions = [{"type": "wait", "milliseconds": wait_time}]

            if use_html_fallback:
                result = app.scrape(
                    url=url,
                    formats=['html', 'markdown'],
                    only_main_content=False,
                    actions=actions,
                    timeout=timeout
                )
            else:
                result = app.scrape(
                    url=url,
                    formats=[{
                        "type": "json",
                        "schema": GameSearchResults.model_json_schema(),
                        "prompt": "Extract all board game products. Capture full name, price, stock status, and URL."
                    }],
                    only_main_content=False,
                    actions=actions,
                    timeout=timeout
                )

            return result, None  # Success!

        except Exception as e:
            error_msg = str(e)
            # For Ozon, don't retry on timeout
            if store_name == "Ozon.gr":
                return None, error_msg

            if "timeout" in error_msg.lower() and attempt < max_retries - 1:
                continue
            else:
                return None, error_msg

    return None, "Max retries reached"

def search_rollnplay(game_query):
    """Search RollnPlay across multiple WooCommerce result pages using raw HTML."""
    import requests as _requests
    import time as _time

    encoded_query = urllib.parse.quote_plus(game_query)
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept-Language": "el-GR,el;q=0.9,en;q=0.8",
        "Referer": "https://rollnplay.gr/",
    }

    products = []
    seen_urls = set()
    session = _requests.Session()

    for page in range(1, 7):
        if page == 1:
            url = f"https://rollnplay.gr/?term=&s={encoded_query}&post_type=product&taxonomy=product_cat"
        else:
            url = f"https://rollnplay.gr/page/{page}/?term=&s={encoded_query}&post_type=product&taxonomy=product_cat"

        try:
            response = session.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                if page == 1:
                    return []
                break
        except Exception:
            if page == 1:
                return []
            break

        page_products = parse_rollnplay_html(response.text, game_query)
        if not page_products:
            if page == 1:
                return []
            break

        added_this_page = 0
        for p in page_products:
            p_url = p.get('url', '')
            if not p_url or p_url in seen_urls:
                continue
            seen_urls.add(p_url)
            products.append(p)
            added_this_page += 1

        page_lower = response.text.lower()
        has_next_page = (
            f'/page/{page + 1}/?term&#038;s=' in page_lower or
            f'/page/{page + 1}/?term=&s=' in page_lower or
            'next page-numbers' in page_lower
        )
        if not has_next_page or added_this_page == 0:
            break
        if page < 6:
            _time.sleep(0.25)

    return products


def search_meepleplanet(game_query):
    """Search Meeple Planet across multiple WooCommerce result pages."""
    import requests as _requests
    import time as _time

    encoded_query = urllib.parse.quote_plus(game_query)
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept-Language": "el-GR,el;q=0.9,en;q=0.8",
        "Referer": "https://meeple-planet.com/",
    }

    products = []
    seen_urls = set()
    session = _requests.Session()

    for page in range(1, 5):
        if page == 1:
            url = f"https://meeple-planet.com/?s={encoded_query}&post_type=product"
        else:
            url = f"https://meeple-planet.com/page/{page}/?s={encoded_query}&post_type=product"

        try:
            response = session.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                break
        except Exception:
            break

        page_products = parse_meepleplanet_html(response.text, game_query)
        if not page_products:
            if page == 1:
                return []
            break

        added_this_page = 0
        for p in page_products:
            p_url = p.get('url', '')
            if not p_url or p_url in seen_urls:
                continue
            seen_urls.add(p_url)
            products.append(p)
            added_this_page += 1

        page_lower = response.text.lower()
        has_next_page = (
            f'/page/{page + 1}/?s=' in page_lower or
            'class="next page-number"' in page_lower or
            'woocommerce-pagination' in page_lower
        )
        if not has_next_page or added_this_page == 0:
            break
        if page < 4:
            _time.sleep(0.25)

    return products


def search_crystallotus(game_query):
    """Search Crystal Lotus across multiple Shopify search pages."""
    import requests as _requests
    import time as _time

    encoded_query = urllib.parse.quote_plus(game_query)
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept-Language": "el-GR,el;q=0.9,en;q=0.8",
        "Referer": "https://crystallotus.eu/",
    }

    products = []
    seen_urls = set()
    session = _requests.Session()
    use_firecrawl_fallback = False

    for page in range(1, 5):
        url = (
            f"https://crystallotus.eu/search?q={encoded_query}"
            f"&type=product&options%5Bprefix%5D=last&page={page}"
        )

        page_content = ""
        if not use_firecrawl_fallback:
            try:
                response = session.get(url, headers=headers, timeout=15)
                if response.status_code == 200:
                    page_content = response.text
                elif response.status_code == 429:
                    use_firecrawl_fallback = True
                else:
                    break
            except Exception:
                use_firecrawl_fallback = True

        if use_firecrawl_fallback:
            result, error = scrape_with_retry(
                app,
                url,
                "Crystal Lotus",
                max_retries=1,
                use_html_fallback=True,
            )
            if error or not result:
                if page == 1 and not products:
                    return []
                break
            html_content = result.html if hasattr(result, 'html') and result.html else ""
            markdown_content = result.markdown if hasattr(result, 'markdown') and result.markdown else ""
            page_content = html_content + markdown_content

        page_products = parse_crystallotus_html(page_content, game_query)
        if not page_products and page == 1:
            return []

        for p in page_products:
            p_url = p.get('url', '')
            if not p_url or p_url in seen_urls:
                continue
            seen_urls.add(p_url)
            products.append(p)

        page_lower = page_content.lower()
        has_next_page = (
            f'page={page + 1}' in page_lower or
            'pagination__item--next' in page_lower or
            'pagination__next' in page_lower
        )
        if not has_next_page:
            break
        if page < 4:
            _time.sleep(0.35)

    return products


def search_gaminggalaxy(game_query):
    """Search Gaming Galaxy across multiple Magento result pages."""
    import requests as _requests

    encoded_query = urllib.parse.quote_plus(game_query)
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept-Language": "el-GR,el;q=0.9,en;q=0.8",
    }

    products = []
    seen_urls = set()

    for page in range(1, 5):
        url = (
            f"https://ggalaxy.gr/catalogsearch/result/?q={encoded_query}"
            f"&product_list_limit=36&p={page}"
        )
        try:
            response = _requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                break
        except Exception:
            break

        page_products = parse_gaminggalaxy_html(response.text, game_query)
        if not page_products:
            if page == 1:
                return []
            break

        added_this_page = 0
        for p in page_products:
            p_url = p.get('url', '')
            if not p_url or p_url in seen_urls:
                continue
            seen_urls.add(p_url)
            products.append(p)
            added_this_page += 1

        if added_this_page == 0:
            break

    return products


def search_dragonphoenixinn(game_query):
    """Search The Dragonphoenix Inn across multiple WooCommerce result pages."""
    import requests as _requests
    import time as _time

    encoded_query = urllib.parse.quote_plus(game_query)
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept-Language": "el-GR,el;q=0.9,en;q=0.8",
        "Referer": "https://innkeeper.gr/",
    }

    products = []
    seen_urls = set()
    session = _requests.Session()

    for page in range(1, 5):
        if page == 1:
            url = f"https://innkeeper.gr/?s={encoded_query}&post_type=product&dgwt_wcas=1"
        else:
            url = f"https://innkeeper.gr/page/{page}/?s={encoded_query}&post_type=product&dgwt_wcas=1"

        try:
            response = session.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                if page == 1:
                    return []
                break
        except Exception:
            if page == 1:
                return []
            break

        page_products = parse_dragonphoenixinn_html(response.text, game_query)
        if not page_products:
            if page == 1:
                return []
            break

        added_this_page = 0
        for p in page_products:
            p_url = p.get('url', '')
            if not p_url or p_url in seen_urls:
                continue
            seen_urls.add(p_url)
            products.append(p)
            added_this_page += 1

        page_lower = response.text.lower()
        has_next_page = (
            f'/page/{page + 1}/?s=' in page_lower or
            'next page-numbers' in page_lower
        )
        if not has_next_page or added_this_page == 0:
            break
        if page < 4:
            _time.sleep(0.25)

    return products


def search_game_structured(game_query):
    """Search for a board game across multiple Greek stores"""
    encoded_query = urllib.parse.quote_plus(game_query)
    stores = [
        {"name": "Ozon.gr", "url": f"https://www.ozon.gr/instantsearchplus/result/?q={encoded_query}"},
        {"name": "Meeple On Board", "url": f"https://meepleonboard.gr/?s={encoded_query}&post_type=product"},
        {"name": "The Game Rules", "url": f"https://www.thegamerules.com/index.php?route=product/search&search={encoded_query}&description=true"},
        {"name": "Fantasy Shop", "url": f"https://www.fantasy-shop.gr/epitrapezia-paixnidia/?dispatch=products.search&q={encoded_query}&search_performed=Y&subcats=Y"},
        {"name": "Boards of Madness", "url": f"https://boardsofmadness.com/?s={encoded_query}&post_type=product&dgwt_wcas=1"},
        {"name": "Nerdom", "url": f"https://www.nerdom.gr/el/search?keyword={encoded_query}"},
        {"name": "eFantasy", "url": f"https://www.efantasy.gr/el/search-results?αναζήτηση={encoded_query}"},
        {"name": "Mystery Bay", "url": f"https://www.mystery-bay.com/search-results?q={encoded_query}"},
        {"name": "Meeple Planet", "url": f"https://meeple-planet.com/?s={encoded_query}&post_type=product"},
        {"name": "epitrapez.io", "url": f"https://epitrapez.io/?s={encoded_query}&post_type=product&dgwt_wcas=1"},
        {"name": "No Label X", "url": f"https://www.skroutz.gr/c/259/epitrapezia/shop/7101/No-Label-X.html?keyphrase={encoded_query}"},
        {"name": "SoHotTCG", "url": f"https://www.skroutz.gr/c/259/epitrapezia/shop/27427/SoHotTCG.html?keyphrase={encoded_query}"},
        {"name": "GamesUniverse", "url": f"https://gamesuniverse.gr/el/module/iqitsearch/searchiqit?s={encoded_query}"},
        {"name": "RollnPlay", "url": f"https://rollnplay.gr/?term=&s={encoded_query}&post_type=product&taxonomy=product_cat"},
        {"name": "PlayceShop", "url": f"https://shop.playce.gr/?s={encoded_query}&post_type=product&dgwt_wcas=1"},
        {"name": "Politeia", "url": f"https://www.politeianet.gr/el/search-results?query={encoded_query}"},
        {"name": "Crystal Lotus", "url": f"https://crystallotus.eu/search?q={encoded_query}&type=product%2Carticle%2Cpage%2Ccollection&options%5Bprefix%5D=last"},
        {"name": "Kaissa", "url": f"https://kaissagames.com/b2c_gr/catalogsearch/result/?q={encoded_query}"},
        {"name": "Tech City",  "url": f"https://www.skroutz.gr/c/259/epitrapezia/shop/23412/Tech-City.html?keyphrase={encoded_query}"},
        {"name": "Game Theory", "url": f"https://www.skroutz.gr/c/259/epitrapezia/shop/23636/Game-Theory.html?keyphrase={encoded_query}"},
        {"name": "Gaming Galaxy", "url": f"https://ggalaxy.gr/catalogsearch/result/?q={encoded_query}"},
        {"name": "The Dragonphoenix Inn", "url": f"https://innkeeper.gr/?s={encoded_query}&post_type=product&dgwt_wcas=1"},
        {"name": "Lex Hobby Store", "url": f"https://www.skroutz.gr/c/259/epitrapezia/shop/29102/Lex-Hobby-Store.html?keyphrase={encoded_query}"},
        {"name": "GenX", "url": f"https://www.genx.gr/index.php?act=viewCat&searchStr={encoded_query}"},
        {"name": "Public", "url": f"https://www.public.gr/search/?text={encoded_query}&type=product"},
        {"name": "VP shop", "url": f"https://shop.vpsaga.com/?s={encoded_query}&post_type=product"}
    ]

    combined_data = {"search_term": game_query, "exact_matches": [], "all_results": [], "store_stats": {}}
    clean_query = normalize_for_match(game_query)
    ozon_clean_query = sanitize_ozon_name(game_query)

    for store in stores:
        store_name = store['name']
        # eFantasy, Public, Ozon.gr, RollnPlay, Meeple Planet, Crystal Lotus, Gaming Galaxy, and The Dragonphoenix Inn use direct requests
        if store_name in ["eFantasy", "Public", "Ozon.gr", "RollnPlay", "Meeple Planet", "Crystal Lotus", "Gaming Galaxy", "The Dragonphoenix Inn"]:
            try:
                if store_name == "eFantasy":
                    raw_products = search_efantasy(game_query)
                elif store_name == "Ozon.gr":
                    raw_products = search_ozon(game_query)
                elif store_name == "RollnPlay":
                    raw_products = search_rollnplay(game_query)
                elif store_name == "Meeple Planet":
                    raw_products = search_meepleplanet(game_query)
                elif store_name == "Crystal Lotus":
                    raw_products = search_crystallotus(game_query)
                elif store_name == "Gaming Galaxy":
                    raw_products = search_gaminggalaxy(game_query)
                elif store_name == "The Dragonphoenix Inn":
                    raw_products = search_dragonphoenixinn(game_query)
                else:
                    raw_products = search_public(game_query)
                valid_store_count = 0
                exact_count = 0
                seen_urls_in_store = set()
                for p in raw_products:
                    if isinstance(p, dict):
                        p_name = p.get('name', '')
                        p_price = p.get('price', 0.0)
                        p_stock = p.get('is_in_stock', False)
                        p_url = p.get('url', '')
                    else:
                        p_name = getattr(p, 'name', '')
                        p_price = getattr(p, 'price', 0.0)
                        p_stock = getattr(p, 'is_in_stock', False)
                        p_url = getattr(p, 'url', '')
                    if p_url in seen_urls_in_store:
                        continue
                    seen_urls_in_store.add(p_url)
                    if clean_query not in normalize_for_match(p_name):
                        continue
                    if store_name == "eFantasy":
                        comparison_name = sanitize_efantasy_name(p_name)
                        target_query = sanitize_efantasy_name(game_query)
                    elif store_name == "Public":
                        comparison_name = sanitize_public_name(p_name)
                        target_query = sanitize_public_name(game_query)
                    elif store_name == "Ozon.gr":
                        comparison_name = sanitize_ozon_name(p_name)
                        target_query = ozon_clean_query
                    else:
                        comparison_name = normalize_for_match(p_name)
                        target_query = normalize_for_match(game_query)
                    product_entry = {
                        "name": p_name,
                        "url": p_url,
                        "in_stock": p_stock,
                        "price": format_price_for_output(p_price),
                        "store": store_name
                    }
                    if comparison_name == target_query:
                        combined_data["exact_matches"].append(product_entry)
                        exact_count += 1
                    combined_data["all_results"].append(product_entry)
                    valid_store_count += 1
                combined_data["store_stats"][store_name] = {"total": valid_store_count, "exact": exact_count}

                # Apostrophe retry logic for Findbar-backed stores
                apostrophe_success = False
                if valid_store_count == 0 and any(ap_char in game_query for ap_char in APOSTROPHE_VARIANTS):
                    apostrophe_success = try_apostrophe_variants(game_query, store_name, None, combined_data)

                # Colon fallback for Findbar-backed stores (if still no results)
                if not apostrophe_success and (combined_data["store_stats"].get(store_name, {}).get("total", 0) == 0) and ":" in game_query:
                    query_without_colon = game_query.replace(":", "").strip()
                    if query_without_colon and query_without_colon != game_query:
                        if store_name == "eFantasy":
                            retry_products = search_efantasy(query_without_colon)
                        elif store_name == "Ozon.gr":
                            retry_products = search_ozon(query_without_colon)
                        elif store_name == "RollnPlay":
                            retry_products = search_rollnplay(query_without_colon)
                        elif store_name == "Meeple Planet":
                            retry_products = search_meepleplanet(query_without_colon)
                        elif store_name == "Crystal Lotus":
                            retry_products = search_crystallotus(query_without_colon)
                        elif store_name == "Gaming Galaxy":
                            retry_products = search_gaminggalaxy(query_without_colon)
                        elif store_name == "The Dragonphoenix Inn":
                            retry_products = search_dragonphoenixinn(query_without_colon)
                        else:
                            retry_products = search_public(query_without_colon)
                        retry_exact = 0
                        retry_total = 0
                        seen_urls_in_store = set()
                        for p in retry_products:
                            if isinstance(p, dict):
                                p_name = p.get('name', '')
                                p_price = p.get('price', 0.0)
                                p_stock = p.get('is_in_stock', False)
                                p_url = p.get('url', '')
                            else:
                                p_name = getattr(p, 'name', '')
                                p_price = getattr(p, 'price', 0.0)
                                p_stock = getattr(p, 'is_in_stock', False)
                                p_url = getattr(p, 'url', '')
                            if p_url in seen_urls_in_store:
                                continue
                            seen_urls_in_store.add(p_url)
                            if query_without_colon.lower().replace(':','').strip() not in p_name.lower().replace(':','').strip():
                                continue
                            entry = {"name": p_name, "url": p_url, "in_stock": p_stock, "price": format_price_for_output(p_price), "store": store_name}
                            combined_data["all_results"].append(entry)
                            retry_total += 1
                            if store_name == "eFantasy":
                                is_exact = sanitize_efantasy_name(p_name) == sanitize_efantasy_name(query_without_colon)
                            elif store_name == "Public":
                                is_exact = sanitize_public_name(p_name) == sanitize_public_name(query_without_colon)
                            elif store_name == "Ozon.gr":
                                is_exact = sanitize_ozon_name(p_name) == sanitize_ozon_name(query_without_colon)
                            else:
                                is_exact = normalize_for_match(p_name) == normalize_for_match(query_without_colon)
                            if is_exact:
                                combined_data["exact_matches"].append(entry)
                                retry_exact += 1
                        if retry_total > 0:
                            combined_data["store_stats"][store_name] = {"total": retry_total, "exact": retry_exact}

                # Dash fallback for Findbar-backed stores (if still no results)
                if (combined_data["store_stats"].get(store_name, {}).get("total", 0) == 0 and
                    any(dash_char in game_query for dash_char in DASH_VARIANTS)):
                    query_without_dash = strip_dash_variants(game_query)
                    if query_without_dash and query_without_dash != game_query:
                        if store_name == "eFantasy":
                            retry_products = search_efantasy(query_without_dash)
                        elif store_name == "Ozon.gr":
                            retry_products = search_ozon(query_without_dash)
                        elif store_name == "RollnPlay":
                            retry_products = search_rollnplay(query_without_dash)
                        elif store_name == "Meeple Planet":
                            retry_products = search_meepleplanet(query_without_dash)
                        elif store_name == "Crystal Lotus":
                            retry_products = search_crystallotus(query_without_dash)
                        elif store_name == "Gaming Galaxy":
                            retry_products = search_gaminggalaxy(query_without_dash)
                        elif store_name == "The Dragonphoenix Inn":
                            retry_products = search_dragonphoenixinn(query_without_dash)
                        else:
                            retry_products = search_public(query_without_dash)

                        retry_exact = 0
                        retry_total = 0
                        seen_urls_in_store = set()

                        for p in retry_products:
                            if isinstance(p, dict):
                                p_name = p.get('name', '')
                                p_price = p.get('price', 0.0)
                                p_stock = p.get('is_in_stock', False)
                                p_url = p.get('url', '')
                            else:
                                p_name = getattr(p, 'name', '')
                                p_price = getattr(p, 'price', 0.0)
                                p_stock = getattr(p, 'is_in_stock', False)
                                p_url = getattr(p, 'url', '')

                            if p_url in seen_urls_in_store:
                                continue
                            seen_urls_in_store.add(p_url)

                            if normalize_for_match(query_without_dash) not in normalize_for_match(p_name):
                                continue

                            entry = {
                                "name": p_name,
                                "url": p_url,
                                "in_stock": p_stock,
                                "price": format_price_for_output(p_price),
                                "store": store_name
                            }
                            combined_data["all_results"].append(entry)
                            retry_total += 1

                            if store_name == "eFantasy":
                                is_exact = sanitize_efantasy_name(p_name) == sanitize_efantasy_name(query_without_dash)
                            elif store_name == "Public":
                                is_exact = sanitize_public_name(p_name) == sanitize_public_name(query_without_dash)
                            elif store_name == "Ozon.gr":
                                is_exact = sanitize_ozon_name(p_name) == sanitize_ozon_name(query_without_dash)
                            else:
                                is_exact = normalize_for_match(p_name) == normalize_for_match(query_without_dash)

                            if is_exact:
                                combined_data["exact_matches"].append(entry)
                                retry_exact += 1

                        if retry_total > 0:
                            combined_data["store_stats"][store_name] = {"total": retry_total, "exact": retry_exact}
            except Exception as e:
                combined_data["store_stats"][store_name] = {"error": str(e)[:200]}
            continue

        try:
            # Sites that need HTML fallback
            use_html_fallback = store_name in [
                "The Game Rules", "epitrapez.io", "Boards of Madness",
                "Fantasy Shop", "Nerdom", "GamesUniverse",
                "Meeple On Board", "No Label X", "SoHotTCG", "Tech City", "Game Theory",
                "Mystery Bay", "Meeple Planet",
                "RollnPlay", "PlayceShop", "VP shop", "Politeia", "Crystal Lotus", "Kaissa", "Gaming Galaxy", "The Dragonphoenix Inn", "GenX"
            ]

            result, error = scrape_with_retry(app, store["url"], store_name,
                                            max_retries=1,
                                            use_html_fallback=use_html_fallback)

            if error:
                combined_data["store_stats"][store_name] = {"error": error[:200]}
                continue

            # Process result as before...
            if use_html_fallback:
                html_content = result.html if hasattr(result, 'html') and result.html else ""
                markdown_content = result.markdown if hasattr(result, 'markdown') and result.markdown else ""
                content = html_content + markdown_content

                if content:
                    if store_name == "The Game Rules":
                        raw_products = parse_thegamerules_html(content, game_query)
                    elif store_name == "epitrapez.io":
                        raw_products = parse_epitrapezio_html(content, game_query)
                    elif store_name == "Fantasy Shop":
                        raw_products = parse_fantasyshop_html(content, game_query)
                    elif store_name == "Nerdom":
                        raw_products = parse_nerdom_html(content, game_query)
                    elif store_name == "Meeple On Board":
                        raw_products = parse_meepleonboard_html(content, game_query)
                    elif store_name == "No Label X":
                        raw_products = parse_nolabelx_html(content, game_query)
                    elif store_name == "SoHotTCG":
                        raw_products = parse_sohottcg_html(content, game_query)
                    elif store_name == "Tech City":
                        raw_products = parse_techcity_html(content, game_query)
                    elif store_name == "Game Theory":
                        raw_products = parse_gametheory_html(content, game_query)
                    elif store_name == "Mystery Bay":
                        raw_products = parse_mysterybay_html(content, game_query)
                    elif store_name == "Meeple Planet":
                        raw_products = parse_meepleplanet_html(content, game_query)
                    elif store_name == "Boards of Madness":
                        raw_products = parse_boardsofmadness_html(content, game_query)
                    elif store_name == "GamesUniverse":
                        raw_products = parse_gamesuniverse_html(content, game_query)
                    elif store_name == "RollnPlay":
                        raw_products = parse_rollnplay_html(content, game_query)
                    elif store_name == "PlayceShop":
                        raw_products = parse_playceshop_html(content, game_query)
                    elif store_name == "VP shop":
                        raw_products = parse_vpshop_html(content, game_query)
                    elif store_name == "Politeia":
                        raw_products = parse_politeia_html(content, game_query)
                    elif store_name == "Crystal Lotus":
                        raw_products = parse_crystallotus_html(content, game_query)
                    elif store_name == "Kaissa":
                        raw_products = parse_kaissa_html(content, game_query)
                    elif store_name == "Gaming Galaxy":
                        raw_products = parse_gaminggalaxy_html(content, game_query)
                    elif store_name == "The Dragonphoenix Inn":
                        raw_products = parse_dragonphoenixinn_html(content, game_query)
                    elif store_name == "GenX":
                        raw_products = parse_genx_html(content, game_query)
                    else:
                        raw_products = []
                else:
                    raw_products = []
            else:
                if result and hasattr(result, 'json') and result.json:
                    raw_products = result.json.get('products', [])
                else:
                    raw_products = []

            # Process products
            valid_store_count = 0
            exact_count = 0
            seen_urls_in_store = set()

            for p in raw_products:
                # Handle both dict and object formats
                if isinstance(p, dict):
                    p_name = p.get('name', '')
                    p_price = p.get('price', 0.0)
                    p_stock = p.get('is_in_stock', False)
                    p_url = p.get('url', '')
                else:
                    p_name = getattr(p, 'name', '')
                    p_price = getattr(p, 'price', 0.0)
                    p_stock = getattr(p, 'is_in_stock', False)
                    p_url = getattr(p, 'url', '')

                # Skip duplicate URLs from the same store
                if p_url in seen_urls_in_store:
                    continue
                seen_urls_in_store.add(p_url)

                # Check if query is in product name, normalizing delimiters
                # This allows "kinfire chronicles night" to match "kinfire chronicles: nights fall"
                p_name_normalized = normalize_for_match(p_name)
                if clean_query not in p_name_normalized:
                    continue

                # Apply store-specific sanitization
                if store_name == "Ozon.gr":
                    comparison_name = sanitize_ozon_name(p_name)
                    target_query = ozon_clean_query
                elif store_name == "eFantasy":
                    comparison_name = sanitize_efantasy_name(p_name)
                    target_query = sanitize_efantasy_name(game_query)
                elif store_name == "No Label X":
                    comparison_name = normalize_for_match(sanitize_nolabelx_name(p_name))
                    target_query = normalize_for_match(game_query)
                elif store_name == "SoHotTCG":
                    comparison_name = normalize_for_match(sanitize_nolabelx_name(p_name)) # Uses No Label X sanitizer
                    target_query = normalize_for_match(game_query)
                elif store_name == "Tech City":
                    comparison_name = normalize_for_match(sanitize_nolabelx_name(p_name))
                    target_query = normalize_for_match(game_query)
                elif store_name == "Game Theory":
                    comparison_name = normalize_for_match(sanitize_nolabelx_name(p_name))
                    target_query = normalize_for_match(game_query)
                else:
                    comparison_name = normalize_for_match(p_name)
                    target_query = clean_query

                product_entry = {
                    "name": p_name,
                    "url": p_url,
                    "in_stock": p_stock,
                    "price": format_price_for_output(p_price),
                    "store": store_name
                }

                if comparison_name == target_query:
                    combined_data["exact_matches"].append(product_entry)
                    exact_count += 1

                combined_data["all_results"].append(product_entry)
                valid_store_count += 1

            combined_data["store_stats"][store_name] = {"total": valid_store_count, "exact": exact_count}

            # Apostrophe retry logic (only when no results)
            apostrophe_success = False
            if (valid_store_count == 0 and
                any(ap_char in game_query for ap_char in APOSTROPHE_VARIANTS) and
                use_html_fallback and content):
                apostrophe_success = try_apostrophe_variants(game_query, store_name, content, combined_data)

            # Colon fallback: if no products found and query contains ":", retry without ":"
            current_store_total = combined_data.get("store_stats", {}).get(store_name, {}).get("total", 0)
            if (current_store_total == 0 and
                ":" in game_query and
                use_html_fallback and content):
                query_without_colon = game_query.replace(":", "").strip()
                if query_without_colon and query_without_colon != game_query:
                    # Retry the same parser with colon-stripped query
                    retry_raw_products = []
                    if store_name == "The Game Rules":
                        retry_raw_products = parse_thegamerules_html(content, query_without_colon)
                    elif store_name == "epitrapez.io":
                        retry_raw_products = parse_epitrapezio_html(content, query_without_colon)
                    elif store_name == "Fantasy Shop":
                        retry_raw_products = parse_fantasyshop_html(content, query_without_colon)
                    elif store_name == "Nerdom":
                        retry_raw_products = parse_nerdom_html(content, query_without_colon)
                    elif store_name == "Meeple On Board":
                        retry_raw_products = parse_meepleonboard_html(content, query_without_colon)
                    elif store_name == "No Label X":
                        retry_raw_products = parse_nolabelx_html(content, query_without_colon)
                    elif store_name == "SoHotTCG":
                        retry_raw_products = parse_sohottcg_html(content, query_without_colon)
                    elif store_name == "Tech City":
                        retry_raw_products = parse_techcity_html(content, query_without_colon)
                    elif store_name == "Game Theory":
                        retry_raw_products = parse_gametheory_html(content, query_without_colon)
                    elif store_name == "Mystery Bay":
                        retry_raw_products = parse_mysterybay_html(content, query_without_colon)
                    elif store_name == "Meeple Planet":
                        retry_raw_products = parse_meepleplanet_html(content, query_without_colon)
                    elif store_name == "Boards of Madness":
                        retry_raw_products = parse_boardsofmadness_html(content, query_without_colon)
                    elif store_name == "GamesUniverse":
                        retry_raw_products = parse_gamesuniverse_html(content, query_without_colon)
                    elif store_name == "RollnPlay":
                        retry_raw_products = parse_rollnplay_html(content, query_without_colon)
                    elif store_name == "PlayceShop":
                        retry_raw_products = parse_playceshop_html(content, query_without_colon)
                    elif store_name == "VP shop":
                        retry_raw_products = parse_vpshop_html(content, query_without_colon)
                    elif store_name == "Politeia":
                        retry_raw_products = parse_politeia_html(content, query_without_colon)
                    elif store_name == "Crystal Lotus":
                        retry_raw_products = parse_crystallotus_html(content, query_without_colon)
                    elif store_name == "Kaissa":
                        retry_raw_products = parse_kaissa_html(content, query_without_colon)
                    elif store_name == "Gaming Galaxy":
                        retry_raw_products = parse_gaminggalaxy_html(content, query_without_colon)
                    elif store_name == "The Dragonphoenix Inn":
                        retry_raw_products = parse_dragonphoenixinn_html(content, query_without_colon)
                    elif store_name == "GenX":
                        retry_raw_products = parse_genx_html(content, query_without_colon)
                    else:
                        retry_raw_products = []

                    # Process retry results
                    valid_store_count_retry = 0
                    exact_count_retry = 0
                    for p in retry_raw_products:
                        if isinstance(p, dict):
                            p_name = p.get('name', '')
                            p_price = p.get('price', 0.0)
                            p_stock = p.get('is_in_stock', False)
                            p_url = p.get('url', '')
                        else:
                            p_name = getattr(p, 'name', '')
                            p_price = getattr(p, 'price', 0.0)
                            p_stock = getattr(p, 'is_in_stock', False)
                            p_url = getattr(p, 'url', '')

                        # Skip duplicate URLs from the same store
                        if p_url in seen_urls_in_store:
                            continue
                        seen_urls_in_store.add(p_url)

                        # Check if query is in product name, normalizing delimiters
                        p_name_normalized = ' '.join(p_name.lower().replace(':', ' ').replace('-', ' ').split())
                        # The target query for comparison should be the `query_without_colon`
                        # and also handle potential colon stripping for stores that do that
                        if store_name == "Ozon.gr":
                            comparison_name = sanitize_ozon_name(p_name)
                            target_query = sanitize_ozon_name(query_without_colon)
                        elif store_name == "eFantasy":
                            comparison_name = sanitize_efantasy_name(p_name)
                            target_query = sanitize_efantasy_name(query_without_colon)
                        elif store_name in ["No Label X", "SoHotTCG", "Tech City", "Game Theory"]:
                            comparison_name = sanitize_nolabelx_name(p_name)
                            target_query = normalize_for_match(query_without_colon)
                        else:
                            comparison_name = normalize_for_match(p_name)
                            target_query = normalize_for_match(query_without_colon)

                        # If the parsed product name (normalized) contains the retry query (normalized)
                        if target_query not in comparison_name and target_query not in p_name_normalized:
                            continue

                        product_entry = {
                            "name": p_name,
                            "url": p_url,
                            "in_stock": p_stock,
                            "price": format_price_for_output(p_price),
                            "store": store_name
                        }

                        if comparison_name == target_query:
                            combined_data["exact_matches"].append(product_entry)
                            exact_count_retry += 1

                        combined_data["all_results"].append(product_entry)
                        valid_store_count_retry += 1

                    # Update stats with retry results
                    if valid_store_count_retry > 0:
                        combined_data["store_stats"][store_name] = {"total": valid_store_count_retry, "exact": exact_count_retry}

            # Dash fallback: retry without dash variants.
            # For The Game Rules, force this retry even if initial results exist,
            # because the upstream search endpoint can return a narrower subset.
            current_store_total = combined_data.get("store_stats", {}).get(store_name, {}).get("total", 0)
            force_dash_retry = store_name == "The Game Rules"
            if ((current_store_total == 0 or force_dash_retry) and
                any(dash_char in game_query for dash_char in DASH_VARIANTS) and
                use_html_fallback and content):
                query_without_dash = strip_dash_variants(game_query)
                if query_without_dash and query_without_dash != game_query:
                    retry_content = content
                    if store_name == "The Game Rules":
                        retry_url = (
                            "https://www.thegamerules.com/index.php?route=product/search"
                            f"&search={urllib.parse.quote_plus(query_without_dash)}&description=true"
                        )
                        retry_result, retry_error = scrape_with_retry(
                            app,
                            retry_url,
                            store_name,
                            max_retries=1,
                            use_html_fallback=True,
                        )
                        if not retry_error and retry_result:
                            retry_html = retry_result.html if hasattr(retry_result, 'html') and retry_result.html else ""
                            retry_markdown = retry_result.markdown if hasattr(retry_result, 'markdown') and retry_result.markdown else ""
                            if retry_html or retry_markdown:
                                retry_content = retry_html + retry_markdown

                    retry_raw_products = []
                    if store_name == "The Game Rules":
                        retry_raw_products = parse_thegamerules_html(retry_content, query_without_dash)
                    elif store_name == "epitrapez.io":
                        retry_raw_products = parse_epitrapezio_html(retry_content, query_without_dash)
                    elif store_name == "Fantasy Shop":
                        retry_raw_products = parse_fantasyshop_html(retry_content, query_without_dash)
                    elif store_name == "Nerdom":
                        retry_raw_products = parse_nerdom_html(retry_content, query_without_dash)
                    elif store_name == "Meeple On Board":
                        retry_raw_products = parse_meepleonboard_html(retry_content, query_without_dash)
                    elif store_name == "No Label X":
                        retry_raw_products = parse_nolabelx_html(retry_content, query_without_dash)
                    elif store_name == "SoHotTCG":
                        retry_raw_products = parse_sohottcg_html(retry_content, query_without_dash)
                    elif store_name == "Tech City":
                        retry_raw_products = parse_techcity_html(retry_content, query_without_dash)
                    elif store_name == "Game Theory":
                        retry_raw_products = parse_gametheory_html(retry_content, query_without_dash)
                    elif store_name == "Mystery Bay":
                        retry_raw_products = parse_mysterybay_html(retry_content, query_without_dash)
                    elif store_name == "Meeple Planet":
                        retry_raw_products = parse_meepleplanet_html(retry_content, query_without_dash)
                    elif store_name == "Boards of Madness":
                        retry_raw_products = parse_boardsofmadness_html(retry_content, query_without_dash)
                    elif store_name == "GamesUniverse":
                        retry_raw_products = parse_gamesuniverse_html(retry_content, query_without_dash)
                    elif store_name == "RollnPlay":
                        retry_raw_products = parse_rollnplay_html(retry_content, query_without_dash)
                    elif store_name == "PlayceShop":
                        retry_raw_products = parse_playceshop_html(retry_content, query_without_dash)
                    elif store_name == "VP shop":
                        retry_raw_products = parse_vpshop_html(retry_content, query_without_dash)
                    elif store_name == "Politeia":
                        retry_raw_products = parse_politeia_html(retry_content, query_without_dash)
                    elif store_name == "Crystal Lotus":
                        retry_raw_products = parse_crystallotus_html(retry_content, query_without_dash)
                    elif store_name == "Kaissa":
                        retry_raw_products = parse_kaissa_html(retry_content, query_without_dash)
                    elif store_name == "Gaming Galaxy":
                        retry_raw_products = parse_gaminggalaxy_html(retry_content, query_without_dash)
                    elif store_name == "The Dragonphoenix Inn":
                        retry_raw_products = parse_dragonphoenixinn_html(retry_content, query_without_dash)
                    elif store_name == "GenX":
                        retry_raw_products = parse_genx_html(retry_content, query_without_dash)
                    else:
                        retry_raw_products = []

                    valid_store_count_retry = 0
                    exact_count_retry = 0
                    for p in retry_raw_products:
                        if isinstance(p, dict):
                            p_name = p.get('name', '')
                            p_price = p.get('price', 0.0)
                            p_stock = p.get('is_in_stock', False)
                            p_url = p.get('url', '')
                        else:
                            p_name = getattr(p, 'name', '')
                            p_price = getattr(p, 'price', 0.0)
                            p_stock = getattr(p, 'is_in_stock', False)
                            p_url = getattr(p, 'url', '')

                        if p_url in seen_urls_in_store:
                            continue
                        seen_urls_in_store.add(p_url)

                        p_name_normalized = normalize_for_match(p_name)
                        if store_name == "Ozon.gr":
                            comparison_name = sanitize_ozon_name(p_name)
                            target_query = sanitize_ozon_name(query_without_dash)
                        elif store_name == "eFantasy":
                            comparison_name = sanitize_efantasy_name(p_name)
                            target_query = sanitize_efantasy_name(query_without_dash)
                        elif store_name in ["No Label X", "SoHotTCG", "Tech City", "Game Theory"]:
                            comparison_name = sanitize_nolabelx_name(p_name)
                            target_query = normalize_for_match(query_without_dash)
                        else:
                            comparison_name = normalize_for_match(p_name)
                            target_query = normalize_for_match(query_without_dash)

                        if target_query not in comparison_name and target_query not in p_name_normalized:
                            continue

                        product_entry = {
                            "name": p_name,
                            "url": p_url,
                            "in_stock": p_stock,
                            "price": format_price_for_output(p_price),
                            "store": store_name
                        }

                        if comparison_name == target_query:
                            combined_data["exact_matches"].append(product_entry)
                            exact_count_retry += 1

                        combined_data["all_results"].append(product_entry)
                        valid_store_count_retry += 1

                    if valid_store_count_retry > 0:
                        existing_total = combined_data.get("store_stats", {}).get(store_name, {}).get("total", 0)
                        existing_exact = combined_data.get("store_stats", {}).get(store_name, {}).get("exact", 0)
                        combined_data["store_stats"][store_name] = {
                            "total": existing_total + valid_store_count_retry,
                            "exact": existing_exact + exact_count_retry,
                        }

        except Exception as e:
            combined_data["store_stats"][store_name] = {"error": str(e)[:200]}

    # Sorting
    combined_data["exact_matches"].sort(key=lambda x: (not x["in_stock"], price_sort_value(x.get("price"))))
    combined_data["all_results"].sort(key=lambda x: (not x["in_stock"], price_sort_value(x.get("price"))))

    return combined_data