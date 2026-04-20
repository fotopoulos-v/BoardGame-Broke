import streamlit as st
import importlib
import sys
import os
import base64
from io import BytesIO
from datetime import datetime
# os.system("playwright install chromium")

# ── Page config (must be first Streamlit call) ──────────────────────────────
st.set_page_config(
    page_title="BoardGame Broke",
    page_icon="./assets/images/Broke_logo_down.png",
    layout="wide"
)

# ── Import scraping module ───────────────────────────────────────────────────
import importlib.util, pathlib

_mod_path = pathlib.Path(__file__).parent / "BoardGame-Broke.py"
_spec = importlib.util.spec_from_file_location("boardgame_broke", _mod_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
search_game_structured = _mod.search_game_structured

# ── Store list (mirrors the stores in BoardGame-Broke.py) ────────────────────
STORE_LIST = [
    {"name": "Ozon.gr",          "url": "https://www.ozon.gr"},
    {"name": "Meeple On Board",  "url": "https://meepleonboard.gr"},
    {"name": "The Game Rules",   "url": "https://www.thegamerules.com"},
    {"name": "Fantasy Shop",     "url": "https://www.fantasy-shop.gr"},
    {"name": "Boards of Madness","url": "https://boardsofmadness.com"},
    {"name": "Nerdom",           "url": "https://www.nerdom.gr"},
    {"name": "eFantasy",         "url": "https://www.efantasy.gr"},
    {"name": "Mystery Bay",      "url": "https://www.mystery-bay.com"},
    {"name": "Meeple Planet",    "url": "https://meeple-planet.com"},
    {"name": "epitrapez.io",     "url": "https://epitrapez.io"},
    {"name": "No Label X",       "url": "https://www.skroutz.gr/c/259/epitrapezia/shop/7101/No-Label-X.html"},
    {"name": "GamesUniverse",    "url": "https://gamesuniverse.gr"},
    {"name": "SoHotTCG",         "url": "https://www.skroutz.gr/c/259/epitrapezia/shop/27427/SoHotTCG.html"},
    {"name": "RollnPlay",        "url": "https://rollnplay.gr"},
    {"name": "PlayceShop",       "url": "https://shop.playce.gr"},
    {"name": "Politeia",         "url": "https://www.politeianet.gr/el/categories/thema-epitrapezia-paixnidia"},
    {"name": "Crystal Lotus",    "url": "https://crystallotus.eu/collections/tabletop-games"},
    {"name": "Kaissa",           "url": "https://kaissagames.com/"},
    {"name": "Tech City",        "url": "https://www.skroutz.gr/c/259/epitrapezia/shop/23412/Tech-City.html"},
    {"name": "Game Theory",      "url": "https://www.skroutz.gr/c/259/epitrapezia/shop/23636/Game-Theory.html"},
    {"name": "Gaming Galaxy",    "url": "https://ggalaxy.gr/paichnidia-me-kartes-kai-epitrapezia.html"},
    {"name": "The Dragonphoenix Inn", "url": "https://innkeeper.gr/product-category/board-games/"},
    {"name": "Lex Hobby Store",  "url": "https://www.skroutz.gr/c/259/epitrapezia/shop/29102/Lex-Hobby-Store.html"},
    {"name": "GenX",             "url": "https://www.genx.gr/epitrapezia--paixnidia-c_60.html"},
    {"name": "Public",           "url": "https://www.public.gr/cat/kids-and-toys/board-games/des-ta-ola"},
    {"name": "VP shop",          "url": "https://shop.vpsaga.com/"},
    ]


# Block for hiding Error messages in the UI
st.markdown("""
<style>
/* Hide Streamlit widget warning messages */
.stAlert, [data-testid="stAlert"] {
    display: none !important;
}
/* Alternative: more specific targeting if the above doesn't work */
div[data-testid="stAlert"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)



# ── Global CSS / Theme ───────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Base & background ── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #240E0B !important;
    color: #FCF2D9 !important;
}

/* ── Main content area ── */
[data-testid="stMain"], .main .block-container {
    background-color: #240E0B !important;
    color: #FCF2D9 !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"], [data-testid="stSidebarContent"] {
    background-color: #1C2733 !important;
}
[data-testid="stSidebar"] * {
    color: #FCF2D9 !important;
}

/* ── All text ── */
p, span, label, div, h1, h2, h3, h4, h5, h6, li, td, th {
    color: #FCF2D9 !important;
}

/* ── Input fields ── */
[data-testid="stTextInput"] input {
    background-color: #3A1A16 !important;
    color: #FCF2D9 !important;
    border: 1px solid #7A4A40 !important;
    border-radius: 6px !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #C8703A !important;
    box-shadow: 0 0 0 2px rgba(200,112,58,0.3) !important;
}
[data-testid="stTextInput"] label {
    color: #FCF2D9 !important;
    font-weight: 600 !important;
}

/* ── Caption / helper text ── */
[data-testid="stCaptionContainer"] p,
.stCaption p {
    color: #B8A898 !important;
    font-size: 13px !important;
}

/* ── Metric widgets ── */
[data-testid="stMetric"] {
    background-color: #3A1A16 !important;
    border: 1px solid #5A2A20 !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
}
[data-testid="stMetricValue"] {
    color: #F0C060 !important;
    font-size: 1.6rem !important;
}
[data-testid="stMetricLabel"] {
    color: #B8A898 !important;
}

/* ── Shared main button sizing ── */
.search-btn > button,
.reset-btn > button,
.stores-btn > button {
    border-radius: 8px !important;
    font-size: 15px !important;
    padding: 10px 16px !important;
    transition: all 0.25s ease !important;
    height: 44px !important;
    white-space: nowrap !important;
    box-sizing: border-box !important;
    margin: 0 !important;
}

/* ── Select / Deselect All buttons ── */
.selectall-btn > button,
.deselectall-btn > button {
    border-radius: 8px !important;
    font-size: 14px !important;
    padding: 8px 14px !important;
    transition: all 0.25s ease !important;
    height: 40px !important;
    white-space: nowrap !important;
    box-sizing: border-box !important;
    margin: 0 !important;
    background-color: #1A2A3A !important;
    color: #B8D0F0 !important;
    border: 1px solid #2A4A6A !important;
    font-weight: 600 !important;
}
.selectall-btn > button:hover,
.deselectall-btn > button:hover {
    background-color: #243A5A !important;
    transform: scale(1.03) !important;
}

/* ── Search button ── */
.search-btn > button {
    background-color: #C8703A !important;
    color: #FFFFFF !important;
    border: none !important;
    font-weight: 700 !important;
}
.search-btn > button:hover {
    background-color: #E08040 !important;
    transform: scale(1.03) !important;
    box-shadow: 0 4px 12px rgba(200,112,58,0.45) !important;
}

/* ── Reset button ── */
.reset-btn > button {
    background-color: #4A3030 !important;
    color: #D0B8A8 !important;
    border: 1px solid #6A4040 !important;
    font-weight: 600 !important;
}
.reset-btn > button:hover {
    background-color: #5A3838 !important;
    transform: scale(1.03) !important;
}

/* ── Stores button ── */
.stores-btn > button {
    background-color: #1A2A5A !important;
    color: #A0C0F0 !important;
    border: 1px solid #2A4A8A !important;
    font-weight: 600 !important;
}
.stores-btn > button:hover {
    background-color: #243A7A !important;
    transform: scale(1.03) !important;
}

/* ── Copy button ── */
.copy-btn > button {
    background-color: #1A3A2A !important;
    color: #A0D8B0 !important;
    border: 1px solid #2A6A4A !important;
    border-radius: 6px !important;
    font-size: 13px !important;
    padding: 6px 18px !important;
    transition: all 0.2s ease !important;
}
.copy-btn > button:hover {
    background-color: #224A34 !important;
    transform: scale(1.02) !important;
}

/* ── Info / spinner boxes ── */
[data-testid="stInfo"] {
    background-color: #1A2A3A !important;
    border-left: 4px solid #3A7ABD !important;
    color: #B8D0F0 !important;
    border-radius: 6px !important;
}
[data-testid="stInfo"] p {
    color: #B8D0F0 !important;
}

/* ── Section headers ── */
.section-header {
    font-size: 1.3rem;
    font-weight: 700;
    color: #F0C060 !important;
    margin-top: 24px;
    margin-bottom: 8px;
    border-bottom: 2px solid #5A2A20;
    padding-bottom: 6px;
}

/* ── HTML result table ── */
.result-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
    margin-top: 8px;
}
.result-table th {
    background-color: #3A1A16 !important;
    color: #F0C060 !important;
    padding: 10px 12px;
    text-align: left;
    border-bottom: 2px solid #7A4A40;
    font-weight: 700;
    white-space: nowrap;
}
.result-table td {
    background-color: #2E1210 !important;
    color: #FCF2D9 !important;
    padding: 9px 12px;
    border-bottom: 1px solid #4A2A20;
    vertical-align: middle;
}
.result-table tr:hover td {
    background-color: #3A1A16 !important;
}
.result-table a {
    color: #6AAFE6 !important;
    text-decoration: none;
}
.result-table a:hover {
    color: #90CFFF !important;
    text-decoration: underline;
}
.badge-instock {
    background-color: #1A4A2A;
    color: #70E090;
    border-radius: 12px;
    padding: 3px 10px;
    font-size: 12px;
    font-weight: 600;
    white-space: nowrap;
}
.badge-outstock {
    background-color: #4A1A1A;
    color: #E07070;
    border-radius: 12px;
    padding: 3px 10px;
    font-size: 12px;
    font-weight: 600;
    white-space: nowrap;
}
.price-cell {
    font-weight: 700;
    color: #F0C060 !important;
    white-space: nowrap;
}



# /* ── Scraping progress header ── */
# p.progress-header-text {
#     color: #4FD6D4 !important;
#     font-size: 16px !important;
#     # font-weight: bold !important;
#     # text-decoration: underline !important;
#     margin-bottom: 4px !important;
# }




/* ── Live progress area ── */
.progress-store {
    background-color: #1A1A3A;
    border-left: 3px solid #3A5ABD;
    border-radius: 4px;
    padding: 6px 12px;
    margin-bottom: 4px;
    font-size: 13px;
}
.progress-store-done {
    border-left-color: #3ABD6A !important;
}
.progress-store-skipped {
    border-left-color: #888888 !important;
    opacity: 0.55;
}
.progress-store-error {
    border-left-color: #BD3A3A !important;
}


            

/* ── Stores panel container FIX ── */
/* Target the wrapper that Streamlit creates for bordered containers */
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #1A1A3A !important;
    border: 1px solid #2A2A5A !important;
    border-radius: 10px !important;
}

/* IMPORTANT: Streamlit places a div inside the wrapper with a default 
   background. We must force it to be transparent. */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    background-color: transparent !important;
}

/* Style the checkboxes inside this container to ensure visibility */
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCheckbox"] {
    background-color: #24244A !important;
    padding: 8px !important;
    border-radius: 6px !important;
    margin-bottom: 5px !important;
}

            


/* ── Code / text area for copy ── */
[data-testid="stCode"] {
    background-color: #1A0E0C !important;
    border: 1px solid #4A2A20 !important;
    border-radius: 6px !important;
}
[data-testid="stCode"] code {
    color: #D0C0A0 !important;
}

/* ── Spinner text ── */
[data-testid="stSpinner"] p {
    color: #FCF2D9 !important;
}

/* ── Divider ── */
hr {
    border-color: #4A2A20 !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background-color: #1A1A3A !important;
    border: 1px solid #2A2A5A !important;
    border-radius: 8px !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: #1A0A08; }
::-webkit-scrollbar-thumb { background: #5A2A20; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #7A3A28; }
</style>
""", unsafe_allow_html=True)

# ── Session state initialisation ─────────────────────────────────────────────
for key, default in [
    ("query", ""),
    ("input_key", 0),
    ("results", None),
    ("show_copy_exact", False),
    ("show_copy_partial", False),
    ("trigger_search", False),
    ("show_stores", False),
    ("selected_stores", [s["name"] for s in STORE_LIST]),
]:
    if key not in st.session_state:
        st.session_state[key] = default


def _set_selected_stores(store_names):
    """Persist store selection even when the stores panel is hidden."""
    selected_lookup = set(store_names)
    st.session_state.selected_stores = [
        s["name"] for s in STORE_LIST if s["name"] in selected_lookup
    ]
    for s in STORE_LIST:
        st.session_state[f"chk_{s['name']}"] = s["name"] in selected_lookup


def _sync_selected_stores_from_checkboxes():
    """Copy checkbox values into persistent session state."""
    st.session_state.selected_stores = [
        s["name"] for s in STORE_LIST if st.session_state.get(f"chk_{s['name']}", False)
    ]


# Always rehydrate checkbox widget state from the persistent selection.
# Streamlit removes widget keys when checkboxes aren't rendered (panel closed),
# so we must force-write them every run before the panel could render.
_selected_set = set(st.session_state.selected_stores)
for s in STORE_LIST:
    st.session_state[f"chk_{s['name']}"] = s["name"] in _selected_set


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="border-top:2px solid #8F6863; margin-top:4px; margin-bottom:4px;"></div>', unsafe_allow_html=True)
    st.markdown("""
        <p style="color:#FCF2D9; font-size:16px; margin:0 0 2px 0;">
            💰 Support me!<br>
            Your support helps me maintain and improve the app.
        </p>
    """, unsafe_allow_html=True)
    st.markdown("""
        <style>
        .bmc-button {
            background-color:#3679AD; color:white; border:none;
            border-radius:8px; padding:10px 20px; font-size:16px;
            font-weight:bold; cursor:pointer; margin-top:5px;
            margin-bottom:8px; transition: all 0.3s ease;
        }
        .bmc-button:hover { background-color:#003AAB; transform: scale(1.05); }
        </style>
        <a href="https://buymeacoffee.com/vasileios" target="_blank">
            <button class="bmc-button">☕ Buy Me a Coffee</button>
        </a>
    """, unsafe_allow_html=True)

    _app_dir = os.path.dirname(os.path.abspath(__file__))
    guru_logo_path = os.path.join(_app_dir, "assets", "images", "guru_logo.png")
    scout_logo_path = os.path.join(_app_dir, "assets", "images", "scout_logo.png")

    def render_sidebar_promo_card(image_path, target_url, title, description, width=48):
        image_html = ""
        if os.path.exists(image_path):
            with open(image_path, "rb") as img_file:
                encoded_image = base64.b64encode(img_file.read()).decode()
            image_html = f'<img src="data:image/png;base64,{encoded_image}" alt="{title}" style="width:{width}px; height:auto; display:block; border-radius:8px; flex-shrink:0;">'

        st.html(
            f'''
            <style>body {{ margin:0; padding:0; }}</style>
            <a href="{target_url}" target="_blank" rel="noopener noreferrer"
               style="display:block; text-decoration:none; cursor:pointer;
                      background-color:#331D42; border:1px solid #6A2B96;
                      border-radius:10px; padding:10px 12px; margin:2px 0;">
                <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">
                    {image_html}
                    <span style="color:#FCF2D9; font-size:15px; font-weight:700;">{title}</span>
                </div>
                <p style="color:#E6D8F0; font-size:12px; margin:0; line-height:1.4;">{description}</p>
            </a>
            '''
        )

    st.markdown('<br><div style="border-top:2px solid #8F6863; margin-top:4px; margin-bottom:4px;"></div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#FCF2D9; font-size:14px; font-weight:600; margin:0 0 4px 0;">🎮 Check my other apps!</p>', unsafe_allow_html=True)
    render_sidebar_promo_card(
        guru_logo_path,
        "https://boardgame-guru.streamlit.app/",
        "BoardGame Guru",
        "Upload rulebooks and ask rules questions instantly.",
    )

    render_sidebar_promo_card(
        scout_logo_path,
        "https://boardgame-scout.streamlit.app/",
        "BoardGame Scout",
        "Discover games and get recommendations through the official BoardGameGeek API.",
    )

    st.markdown('<br><div style="border-top:2px solid #8F6863; margin-top:4px; margin-bottom:4px;"></div>', unsafe_allow_html=True)
    st.markdown("""
        <p style="color:#B8A898; font-size:13px; line-height:1.5; margin:0;">
            <strong>Disclaimer</strong><br>
            The prices, availability, and links shown in this app are collected automatically and may not always be fully accurate. Store websites can change their structure, product pages, or stock information at any time, which may affect the results displayed here. Please verify all details directly on the store’s website before making any purchase decision.
        </p>
    """, unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 6], gap="small")
with col1:
    if os.path.exists("assets/images/Broke_logo_down.png"):
        st.image("assets/images/Broke_logo_down.png", width=120)
with col2:
    st.markdown("<h1 style='color:#FAFAFA; margin-top: 10px; margin-left: -10px;'>BoardGame Broke</h1>", unsafe_allow_html=True)

st.markdown("<p style='color:#B8A898; font-size:17px; margin-top:0;'>Compare board game prices across Greek stores</p>", unsafe_allow_html=True)
st.markdown("---")

def format_price_display(price_value):
    """Render price for UI without showing misleading currency prefix for missing values."""
    if price_value is None:
        return "N/A"
    if isinstance(price_value, str) and price_value.strip().upper() == "N/A":
        return "N/A"
    return f"€{price_value}"

# ── Helper: build HTML result table ──────────────────────────────────────────
def build_html_table(items):
    rows = ""
    for item in items:
        stock_badge = (
            '<span class="badge-instock">✅ In Stock</span>'
            if item["in_stock"]
            else '<span class="badge-outstock">❌ Out of Stock</span>'
        )
        name_escaped = item["name"].replace("<", "&lt;").replace(">", "&gt;")
        price_display = format_price_display(item.get("price"))
        rows += f"""
        <tr>
            <td>{name_escaped}</td>
            <td>{item['store']}</td>
            <td class="price-cell">{price_display}</td>
            <td>{stock_badge}</td>
            <td><a href="{item['url']}" target="_blank" rel="noopener noreferrer">🔗 View</a></td>
        </tr>"""
    return f"""
    <div style="overflow-x:auto;">
    <table class="result-table">
        <thead>
            <tr>
                <th>Name</th>
                <th>Store</th>
                <th>Price (€)</th>
                <th>Availability</th>
                <th>Link</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    </div>"""

# ── Helper: build plain-text copy block ──────────────────────────────────────
def build_copy_text(items):
    lines = ["Name\t\tStore\t\tPrice (€)\tAvailability\tLink"]
    lines.append("-" * 90)
    for item in items:
        stock = "In Stock" if item["in_stock"] else "Out of Stock"
        lines.append(f"{item['name']}\t{item['store']}\t{format_price_display(item.get('price'))}\t{stock}\t{item['url']}")
    return "\n".join(lines)


def build_results_pdf(search_term, exact_matches, partial_matches):
    """Generate a styled PDF for exact and partial matches with clickable product links."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except Exception:
        return None

    # Register Unicode font to support Greek accented characters in PDF output.
    font_name = "Helvetica"
    font_name_bold = "Helvetica-Bold"
    font_candidates = [
        ("DejaVuSans", "DejaVuSans-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("NotoSans", "NotoSans-Bold", "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"),
    ]

    for regular_name, bold_name, regular_path, bold_path in font_candidates:
        if os.path.exists(regular_path):
            try:
                pdfmetrics.registerFont(TTFont(regular_name, regular_path))
                if os.path.exists(bold_path):
                    pdfmetrics.registerFont(TTFont(bold_name, bold_path))
                    font_name_bold = bold_name
                else:
                    font_name_bold = regular_name
                font_name = regular_name
                break
            except Exception:
                continue

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.2 * cm,
        rightMargin=1.2 * cm,
        topMargin=1.0 * cm,
        bottomMargin=1.0 * cm,
        title=f"BoardGame Broke Results - {search_term}",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Title"],
        fontName=font_name_bold,
        fontSize=20,
        textColor=colors.HexColor("#7578BF"),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "SubtitleCustom",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=10,
        textColor=colors.HexColor("#444444"),
        spaceAfter=4,
    )
    search_term_style = ParagraphStyle(
        "SearchTermValue",
        parent=styles["Normal"],
        fontName=font_name_bold,
        fontSize=16,
        textColor=colors.HexColor("#222222"),
        spaceAfter=10,
    )
    section_style = ParagraphStyle(
        "SectionCustom",
        parent=styles["Heading2"],
        fontName=font_name_bold,
        fontSize=13,
        textColor=colors.HexColor("#7578BF"),
        spaceBefore=8,
        spaceAfter=6,
    )
    body_style = ParagraphStyle("BodySmall", parent=styles["Normal"], fontName=font_name, fontSize=8.7, leading=10.5)
    link_style = ParagraphStyle("LinkSmall", parent=body_style, fontName=font_name, textColor=colors.HexColor("#3D56C5"))

    story = [
        Paragraph("BoardGame Broke - Search Results", title_style),
        Paragraph(
            f"Search term:",
            subtitle_style,
        ),
        Paragraph(search_term, search_term_style),
        Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            subtitle_style,
        ),
    ]

    def add_section(title, items):
        story.append(Paragraph(title, section_style))
        if not items:
            story.append(Paragraph("No results found.", body_style))
            story.append(Spacer(1, 8))
            return

        table_data = [[
            Paragraph("<b>Name</b>", body_style),
            Paragraph("<b>Store</b>", body_style),
            Paragraph("<b>Price</b>", body_style),
            Paragraph("<b>Availability</b>", body_style),
            Paragraph("<b>View</b>", body_style),
        ]]

        for item in items:
            stock_text = "In Stock" if item.get("in_stock") else "Out of Stock"
            url = item.get("url", "")
            price_value = item.get('price', '')
            price_cell = "N/A" if str(price_value).strip().upper() == "N/A" else f"€ {price_value}"
            link_cell = Paragraph(f"<link href='{url}'>View</link>", link_style) if url else Paragraph("-", body_style)
            table_data.append([
                Paragraph(str(item.get("name", "")), body_style),
                Paragraph(str(item.get("store", "")), body_style),
                Paragraph(price_cell, body_style),
                Paragraph(stock_text, body_style),
                link_cell,
            ])

        col_widths = [8.0 * cm, 3.0 * cm, 2.0 * cm, 2.4 * cm, 2.3 * cm]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7578BF")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), font_name_bold),
            ("ALIGN", (2, 1), (2, -1), "RIGHT"),
            ("ALIGN", (3, 1), (3, -1), "CENTER"),
            ("ALIGN", (4, 1), (4, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 1), (-1, -1), font_name),
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F7F7FF"), colors.HexColor("#ECECFA")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(table)
        story.append(Spacer(1, 10))

    add_section("Exact Matches", exact_matches)
    add_section("Partial Matches", partial_matches)

    doc.build(story)
    return buffer.getvalue()

# ── Search input ─────────────────────────────────────────────────────────────
_input_key = f"_search_input_{st.session_state.input_key}"

def _on_input_change():
    """Called when user presses Enter in the text input."""
    if st.session_state[_input_key].strip():
        st.session_state.trigger_search = True

query_input = st.text_input(
    "Enter board game title",
    key=_input_key,
    placeholder="e.g. Catan, Wingspan, Pandemic…",
)
st.caption("🔍 Search looks for exact title matches. Partial matches are shown separately.")

# ── Buttons ───────────────────────────────────────────────────────────────────
selected_store_count = len(st.session_state.selected_stores)
stores_button_label = f"🏪 Stores ({selected_store_count}/{len(STORE_LIST)})"

# 3 equal columns (wide enough for longest label) + spacer pushing them left
col_search, col_reset, col_stores, _ = st.columns([1, 1, 1, 2], gap="small")

with col_search:
    st.markdown('<div class="search-btn">', unsafe_allow_html=True)
    search_clicked = st.button("🔍 Search", key="btn_search", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_reset:
    st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
    reset_clicked = st.button("🔄 Reset", key="btn_reset", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_stores:
    st.markdown('<div class="stores-btn">', unsafe_allow_html=True)
    stores_clicked = st.button(stores_button_label, key="btn_stores", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── Reset logic ───────────────────────────────────────────────────────────────
if reset_clicked:
    st.session_state.query = ""
    st.session_state.input_key += 1  # forces a fresh empty text input widget
    st.session_state.results = None
    st.session_state.show_copy_exact = False
    st.session_state.show_copy_partial = False
    st.session_state.trigger_search = False
    st.session_state.show_stores = False
    # Keep selected_stores as-is on reset (user preference)
    st.rerun()


# ── Hide stores panel when Search is clicked ─────────────────────────────────
if search_clicked and st.session_state.show_stores:
    st.session_state.show_stores = False

# ── Stores panel toggle ───────────────────────────────────────────────────────
if stores_clicked:
    st.session_state.show_stores = not st.session_state.show_stores
    st.session_state.trigger_search = False  # Don't trigger search when just toggling stores panel
    st.rerun()

# ── Render stores panel ───────────────────────────────────────────────────────
if st.session_state.show_stores:
    st.markdown('<div class="section-header">🏪 Stores to Search</div>', unsafe_allow_html=True)

    sel_col1, sel_col2, _ = st.columns([1, 1, 3], gap="small")
    with sel_col1:
        st.markdown('<div class="selectall-btn">', unsafe_allow_html=True)
        if st.button("✅ Select All", key="btn_select_all", use_container_width=True):
            _set_selected_stores([s["name"] for s in STORE_LIST])
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with sel_col2:
        st.markdown('<div class="deselectall-btn">', unsafe_allow_html=True)
        if st.button("❌ Deselect All", key="btn_deselect_all", use_container_width=True):
            _set_selected_stores([])
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with st.container(border=True):
        num_cols = 3
        store_cols = st.columns(num_cols)
        for idx, store in enumerate(STORE_LIST):
            sname = store["name"]
            col = store_cols[idx % num_cols]
            with col:
                key = f"chk_{sname}"
                st.checkbox(
                    f"**{sname}**",
                    key=key,
                    on_change=_sync_selected_stores_from_checkboxes,
                )
              

    n_selected = sum(1 for s in STORE_LIST if st.session_state.get(f"chk_{s['name']}", False))
    st.markdown(
        f"<p style='color:#F0C060; font-size:13px; margin-top:8px;'>"
        f"<strong>{n_selected}</strong> of <strong>{len(STORE_LIST)}</strong> stores selected.</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    st.markdown('</div>', unsafe_allow_html=True)

# ── Hide the entire stores panel when closed ─────────────────────────────────
if not st.session_state.show_stores:
    st.markdown("""
        <style>
        #stores-panel-wrapper {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            overflow: hidden !important;
        }
        </style>
    """, unsafe_allow_html=True)



# ── Determine if we should run a search ──────────────────────────────────────
results_panel = st.empty()

run_search = search_clicked or st.session_state.trigger_search
current_query = query_input.strip()

if run_search and current_query:
    # Reset copy toggles for new search
    st.session_state.show_copy_exact = False
    st.session_state.show_copy_partial = False
    st.session_state.trigger_search = False
    st.session_state.query = current_query
    st.session_state.results = None  
    st.session_state.search_in_progress = True  
    results_panel.empty()


    # Use the persistent selection so hidden widgets do not reset the search scope
    active_stores = st.session_state.selected_stores.copy()

    if not active_stores:
        st.warning("⚠️ No stores selected. Please tick at least one store in **Stores to Search**.")


    else:
        # ── "Searching…" spinner — appears above progress panel
        spinner_ph = st.empty()

        # ── Live progress display ─────────────────────────────────────────────
        # progress_header = st.empty()
        # progress_header.markdown(
        #     "<p class='progress-header-text'>Scraping progress:</p>",
        #     unsafe_allow_html=True,
        # )
        # One placeholder per store, distributed across 3 columns
        progress_cols = st.columns(3)
        store_placeholders = {
            s["name"]: progress_cols[i % 3].empty()
            for i, s in enumerate(STORE_LIST)
        }

        # Initialise placeholders
        for s in STORE_LIST:
            sname = s["name"]
            ph = store_placeholders[sname]
            if sname in active_stores:
                ph.markdown(
                    f"<div class='progress-store'>⏳ <strong>{sname}</strong> — waiting…</div>",
                    unsafe_allow_html=True,
                )
            else:
                ph.markdown(
                    f"<div class='progress-store progress-store-skipped'>⏭️ <strong>{sname}</strong> — skipped</div>",
                    unsafe_allow_html=True,
                )

        import urllib.parse as _urlparse


        def _search_with_live_updates(game_query, active_store_names):
            """Scraping loop with live Streamlit progress updates and deferred retry."""
            import importlib.util as _ilu, pathlib as _pl
            _p = _pl.Path(__file__).parent / "BoardGame-Broke.py"
            _s = _ilu.spec_from_file_location("_bgb_live", _p)
            _m = _ilu.module_from_spec(_s)
            _s.loader.exec_module(_m)

            encoded_query = _urlparse.quote_plus(game_query)
            all_stores = [
                {"name": "Ozon.gr",          "url": f"https://www.ozon.gr/instantsearchplus/result/?q={encoded_query}"},
                {"name": "Meeple On Board",  "url": f"https://meepleonboard.gr/?s={encoded_query}&post_type=product"},
                {"name": "The Game Rules",   "url": f"https://www.thegamerules.com/index.php?route=product/search&search={encoded_query}&description=true"},
                {"name": "Fantasy Shop",     "url": f"https://www.fantasy-shop.gr/epitrapezia-paixnidia/?dispatch=products.search&q={encoded_query}&search_performed=Y&subcats=Y"},
                {"name": "Boards of Madness","url": f"https://boardsofmadness.com/?s={encoded_query}&post_type=product&dgwt_wcas=1"},
                {"name": "Nerdom",           "url": f"https://www.nerdom.gr/el/search?keyword={encoded_query}"},
                {"name": "eFantasy",         "url": f"https://www.efantasy.gr/el/search-results?αναζήτηση={encoded_query}"},
                {"name": "Mystery Bay",      "url": f"https://www.mystery-bay.com/search-results?q={encoded_query}"},
                {"name": "Meeple Planet",    "url": f"https://meeple-planet.com/?s={encoded_query}&post_type=product"},
                {"name": "epitrapez.io",     "url": f"https://epitrapez.io/?s={encoded_query}&post_type=product&dgwt_wcas=1"},
                {"name": "No Label X",       "url": f"https://www.skroutz.gr/c/259/epitrapezia/shop/7101/No-Label-X.html?keyphrase={encoded_query}"},
                {"name": "SoHotTCG",         "url": f"https://www.skroutz.gr/c/259/epitrapezia/shop/27427/SoHotTCG.html?keyphrase={encoded_query}"},
                {"name": "GamesUniverse",    "url": f"https://gamesuniverse.gr/el/module/iqitsearch/searchiqit?s={encoded_query}"},
                {"name": "RollnPlay",        "url": f"https://rollnplay.gr/?term=&s={encoded_query}&post_type=product&taxonomy=product_cat"},
                {"name": "PlayceShop",       "url": f"https://shop.playce.gr/?s={encoded_query}&post_type=product&dgwt_wcas=1"},
                {"name": "Politeia",         "url": f"https://www.politeianet.gr/el/search-results?query={encoded_query}"},
                {"name": "Crystal Lotus",    "url": f"https://crystallotus.eu/search?q={encoded_query}&type=product%2Carticle%2Cpage%2Ccollection&options%5Bprefix%5D=last"},
                {"name": "Kaissa",           "url": f"https://kaissagames.com/b2c_gr/catalogsearch/result/?q={encoded_query}"},
                {"name": "Tech City",        "url": f"https://www.skroutz.gr/c/259/epitrapezia/shop/23412/Tech-City.html?keyphrase={encoded_query}"},
                {"name": "Game Theory",      "url": f"https://www.skroutz.gr/c/259/epitrapezia/shop/23636/Game-Theory.html?keyphrase={encoded_query}"},
                {"name": "Gaming Galaxy",    "url": f"https://ggalaxy.gr/catalogsearch/result/?q={encoded_query}"},
                {"name": "The Dragonphoenix Inn", "url": f"https://innkeeper.gr/?s={encoded_query}&post_type=product&dgwt_wcas=1"},
                {"name": "Lex Hobby Store",  "url": f"https://www.skroutz.gr/c/259/epitrapezia/shop/29102/Lex-Hobby-Store.html?keyphrase={encoded_query}"},
                {"name": "GenX",             "url": f"https://www.genx.gr/index.php?act=viewCat&searchStr={encoded_query}"},
                {"name": "Public",           "url": f"https://www.public.gr/search/?text={encoded_query}&type=product"},
                {"name": "VP shop",          "url": f"https://shop.vpsaga.com/?s={encoded_query}&post_type=product"},
            ]
            stores = [s for s in all_stores if s["name"] in active_store_names]

            combined_data = {
                "search_term": game_query,
                "exact_matches": [],
                "all_results": [],
                "store_stats": {},
            }
            clean_query = game_query.lower().replace(":", "").strip()
            ozon_clean_query = _m.sanitize_ozon_name(game_query)

            # ── Helper: scrape one store and process results ──────────────────────
            def scrape_store(store, attempt_label):
                store_name = store["name"]
                ph = store_placeholders.get(store_name)

                if ph:
                    ph.markdown(
                        f"<div class='progress-store'>🔎 <strong>{store_name}</strong> — {attempt_label}…</div>",
                        unsafe_allow_html=True,
                    )
                def parse_with_query(content_value, query_value):
                    if store_name == "The Game Rules":
                        return _m.parse_thegamerules_html(content_value, query_value)
                    if store_name == "epitrapez.io":
                        return _m.parse_epitrapezio_html(content_value, query_value)
                    if store_name == "Fantasy Shop":
                        return _m.parse_fantasyshop_html(content_value, query_value)
                    if store_name == "VP shop":
                        return _m.parse_vpshop_html(content_value, query_value)
                    if store_name == "Nerdom":
                        return _m.parse_nerdom_html(content_value, query_value)
                    if store_name == "Ozon.gr":
                        return _m.parse_ozon_html(content_value, query_value)
                    if store_name == "Meeple On Board":
                        return _m.parse_meepleonboard_html(content_value, query_value)
                    if store_name == "No Label X":
                        return _m.parse_nolabelx_html(content_value, query_value)
                    if store_name == "Lex Hobby Store":
                        return _m.parse_lexhobby_html(content_value, query_value)
                    if store_name == "SoHotTCG":
                        return _m.parse_sohottcg_html(content_value, query_value)
                    if store_name == "Tech City":
                        return _m.parse_techcity_html(content_value, query_value)
                    if store_name == "Game Theory":
                        return _m.parse_gametheory_html(content_value, query_value)
                    if store_name == "Mystery Bay":
                        return _m.parse_mysterybay_html(content_value, query_value)
                    if store_name == "Meeple Planet":
                        return _m.parse_meepleplanet_html(content_value, query_value)
                    if store_name == "Boards of Madness":
                        return _m.parse_boardsofmadness_html(content_value, query_value)
                    if store_name == "GamesUniverse":
                        return _m.parse_gamesuniverse_html(content_value, query_value)
                    if store_name == "PlayceShop":
                        return _m.parse_playceshop_html(content_value, query_value)
                    if store_name == "Politeia":
                        return _m.parse_politeia_html(content_value, query_value)
                    if store_name == "Crystal Lotus":
                        return _m.parse_crystallotus_html(content_value, query_value)
                    if store_name == "Kaissa":
                        return _m.parse_kaissa_html(content_value, query_value)
                    if store_name == "Gaming Galaxy":
                        return _m.parse_gaminggalaxy_html(content_value, query_value)
                    if store_name == "The Dragonphoenix Inn":
                        return _m.parse_dragonphoenixinn_html(content_value, query_value)
                    if store_name == "GenX":
                        return _m.parse_genx_html(content_value, query_value)
                    if store_name == "Public":
                        return _m.parse_public_html(content_value, query_value)
                    return []

                def add_products(raw_products, target_query_value, seen_urls):
                    added = 0
                    added_exact = 0
                    for p in raw_products:
                        if isinstance(p, dict):
                            p_name = p.get("name", "")
                            p_price = p.get("price", 0.0)
                            p_stock = p.get("is_in_stock", False)
                            p_url = p.get("url", "")
                        else:
                            p_name = getattr(p, "name", "")
                            p_price = getattr(p, "price", 0.0)
                            p_stock = getattr(p, "is_in_stock", False)
                            p_url = getattr(p, "url", "")

                        if not p_url or p_url in seen_urls:
                            continue

                        query_norm = _m.normalize_for_match(target_query_value)
                        query_words = query_norm.split() if query_norm else []
                        name_norm = _m.normalize_for_match(p_name)
                        if not _m._query_words_in_text(query_words, name_norm):
                            continue

                        if store_name == "Ozon.gr":
                            comparison_name = _m.sanitize_ozon_name(p_name)
                            exact_target = _m.sanitize_ozon_name(target_query_value)
                        elif store_name == "eFantasy":
                            comparison_name = _m.sanitize_efantasy_name(p_name)
                            exact_target = _m.sanitize_efantasy_name(target_query_value)
                        elif store_name == "Public":
                            comparison_name = _m.sanitize_public_name(p_name)
                            exact_target = _m.sanitize_public_name(target_query_value)
                        elif store_name in ["No Label X", "SoHotTCG", "Tech City", "Game Theory", "Lex Hobby Store"]:
                            comparison_name = _m.normalize_for_match(_m.sanitize_nolabelx_name(p_name) if store_name != "Lex Hobby Store" else _m.sanitize_lexhobby_name(p_name))
                            exact_target = _m.normalize_for_match(target_query_value)
                        else:
                            comparison_name = _m.normalize_for_match(p_name)
                            exact_target = _m.normalize_for_match(target_query_value)

                        entry = {
                            "name": p_name,
                            "url": p_url,
                            "in_stock": p_stock,
                            "price": _m.format_price_for_output(p_price),
                            "store": store_name,
                        }
                        combined_data["all_results"].append(entry)
                        seen_urls.add(p_url)
                        added += 1

                        if comparison_name == exact_target:
                            combined_data["exact_matches"].append(entry)
                            added_exact += 1

                    return added, added_exact

                # Carry over URLs already added by previous retry attempts
                seen_urls_in_store = {
                    item["url"] for item in combined_data["all_results"]
                    if item.get("store") == store_name and item.get("url")
                }
                valid_store_count = 0
                exact_count = 0

                # ── Direct request-backed stores ───────────────────────────────
                if store_name in ["eFantasy", "Public", "RollnPlay", "Meeple Planet", "Crystal Lotus", "Gaming Galaxy", "The Dragonphoenix Inn"]:
                    ef_debug = {}
                    if store_name == "eFantasy":
                        fetch_func = _m.search_efantasy
                    elif store_name == "RollnPlay":
                        fetch_func = _m.search_rollnplay
                    elif store_name == "Meeple Planet":
                        fetch_func = _m.search_meepleplanet
                    elif store_name == "Crystal Lotus":
                        fetch_func = _m.search_crystallotus
                    elif store_name == "Gaming Galaxy":
                        fetch_func = _m.search_gaminggalaxy
                    elif store_name == "The Dragonphoenix Inn":
                        fetch_func = _m.search_dragonphoenixinn
                    else:
                        fetch_func = _m.search_public
                    try:
                        raw_products = fetch_func(game_query)
                        if store_name == "eFantasy":
                            ef_debug = dict(getattr(_m, "EF_DEBUG_LAST", {}) or {})
                    except Exception as e:
                        return False, str(e)

                    a, e = add_products(raw_products, game_query, seen_urls_in_store)
                    valid_store_count += a
                    exact_count += e

                    apostrophe_success = False
                    if valid_store_count == 0 and any(ch in game_query for ch in _m.APOSTROPHE_VARIANTS):
                        apostrophe_success = _m.try_apostrophe_variants(game_query, store_name, None, combined_data)
                        valid_store_count = combined_data.get("store_stats", {}).get(store_name, {}).get("total", 0)
                        exact_count = combined_data.get("store_stats", {}).get(store_name, {}).get("exact", 0)

                    if valid_store_count == 0 and not apostrophe_success and ":" in game_query:
                        query_no_colon = game_query.replace(":", "").strip()
                        if query_no_colon and query_no_colon != game_query:
                            try:
                                retry_products = fetch_func(query_no_colon)
                            except Exception:
                                retry_products = []
                            a, e = add_products(retry_products, query_no_colon, seen_urls_in_store)
                            valid_store_count += a
                            exact_count += e

                    if valid_store_count == 0 and any(ch in game_query for ch in _m.DASH_VARIANTS):
                        query_no_dash = _m.strip_dash_variants(game_query)
                        if query_no_dash and query_no_dash != game_query:
                            try:
                                retry_products = fetch_func(query_no_dash)
                                if store_name == "eFantasy":
                                    ef_debug = dict(getattr(_m, "EF_DEBUG_LAST", {}) or {})
                            except Exception:
                                retry_products = []
                            a, e = add_products(retry_products, query_no_dash, seen_urls_in_store)
                            valid_store_count += a
                            exact_count += e

                    combined_data["store_stats"][store_name] = {"total": valid_store_count, "exact": exact_count}
                    if store_name == "eFantasy" and ef_debug:
                        combined_data["store_stats"][store_name]["debug"] = ef_debug
                else:
                    use_html_fallback = store_name in [
                        "The Game Rules", "epitrapez.io", "Boards of Madness",
                        "Fantasy Shop", "Nerdom", "Ozon.gr", "GamesUniverse",
                        "Meeple On Board", "No Label X", "SoHotTCG", "Tech City", "Game Theory", "Lex Hobby Store",
                        "Mystery Bay", "Meeple Planet", "PlayceShop", "VP shop", "Politeia", "Crystal Lotus", "Kaissa", "Gaming Galaxy", "The Dragonphoenix Inn", "GenX"
                    ]

                    result, error = _m.scrape_with_retry(
                        _m.app, store["url"], store_name,
                        max_retries=1,
                        use_html_fallback=use_html_fallback,
                    )
                    if error:
                        return False, error

                    content = ""
                    if use_html_fallback:
                        html_content = result.html if hasattr(result, "html") and result.html else ""
                        markdown_content = result.markdown if hasattr(result, "markdown") and result.markdown else ""
                        content = html_content + markdown_content
                        raw_products = parse_with_query(content, game_query) if content else []
                    else:
                        raw_products = result.json.get("products", []) if (result and hasattr(result, "json") and result.json) else []

                    a, e = add_products(raw_products, game_query, seen_urls_in_store)
                    valid_store_count += a
                    exact_count += e

                    if valid_store_count == 0 and use_html_fallback and content and any(ch in game_query for ch in _m.APOSTROPHE_VARIANTS):
                        _m.try_apostrophe_variants(game_query, store_name, content, combined_data)
                        valid_store_count = combined_data.get("store_stats", {}).get(store_name, {}).get("total", 0)
                        exact_count = combined_data.get("store_stats", {}).get(store_name, {}).get("exact", 0)

                    if valid_store_count == 0 and use_html_fallback and content and ":" in game_query:
                        query_no_colon = game_query.replace(":", "").strip()
                        if query_no_colon and query_no_colon != game_query:
                            retry_products = parse_with_query(content, query_no_colon)
                            a, e = add_products(retry_products, query_no_colon, seen_urls_in_store)
                            valid_store_count += a
                            exact_count += e

                    force_dash_retry = store_name == "The Game Rules"
                    if ((valid_store_count == 0 or force_dash_retry) and
                        use_html_fallback and
                        content and
                        any(ch in game_query for ch in _m.DASH_VARIANTS)):
                        query_no_dash = _m.strip_dash_variants(game_query)
                        if query_no_dash and query_no_dash != game_query:
                            retry_content = content

                            # The Game Rules can return a narrower set for dashed queries,
                            # so fetch again with the dash-stripped query.
                            if store_name == "The Game Rules":
                                retry_url = (
                                    "https://www.thegamerules.com/index.php?route=product/search"
                                    f"&search={_urlparse.quote_plus(query_no_dash)}&description=true"
                                )
                                retry_result, retry_error = _m.scrape_with_retry(
                                    _m.app,
                                    retry_url,
                                    store_name,
                                    max_retries=1,
                                    use_html_fallback=True,
                                )
                                if not retry_error and retry_result:
                                    retry_html = retry_result.html if hasattr(retry_result, "html") and retry_result.html else ""
                                    retry_markdown = retry_result.markdown if hasattr(retry_result, "markdown") and retry_result.markdown else ""
                                    if retry_html or retry_markdown:
                                        retry_content = retry_html + retry_markdown

                            retry_products = parse_with_query(retry_content, query_no_dash)
                            a, e = add_products(retry_products, query_no_dash, seen_urls_in_store)
                            valid_store_count += a
                            exact_count += e

                    combined_data["store_stats"][store_name] = {"total": valid_store_count, "exact": exact_count}

                if ph:
                    if valid_store_count > 0:
                        ph.markdown(
                            f"<div class='progress-store progress-store-done'>"
                            f"✅ <strong>{store_name}</strong> — {valid_store_count} result(s) found "
                            f"({exact_count} exact)</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        ef_debug_note = ""
                        if store_name == "eFantasy":
                            ef_debug = combined_data.get("store_stats", {}).get(store_name, {}).get("debug", {})
                            if ef_debug:
                                ef_debug_note = (
                                    f"<br><small>[EF_DEBUG_UI] source={ef_debug.get('session_source', 'n/a')} "
                                    f"status={ef_debug.get('status', 'n/a')} body={ef_debug.get('body_len', 'n/a')} "
                                    f"blocks={ef_debug.get('result_blocks', 'n/a')} parsed={ef_debug.get('parsed_count', 'n/a')} "
                                    f"error={ef_debug.get('error', '')}</small>"
                                )
                        ph.markdown(
                            f"<div class='progress-store progress-store-done'>"
                            f"✅ <strong>{store_name}</strong> — 0 results{ef_debug_note}</div>",
                            unsafe_allow_html=True,
                        )

                return True, None

            # ── Round 1: scrape all stores ────────────────────────────────────────
            failed_stores = []

            for store in stores:
                store_name = store["name"]
                ph = store_placeholders.get(store_name)
                try:
                    success, error = scrape_store(store, "scraping")
                    if not success:
                        failed_stores.append(store)
                        combined_data["store_stats"][store_name] = {"error": error[:200]}
                        if ph:
                            ph.markdown(
                                f"<div class='progress-store progress-store-error'>"
                                f"❌ <strong>{store_name}</strong> — error (retrying later…)</div>",
                                unsafe_allow_html=True,
                            )
                except Exception as e:
                    failed_stores.append(store)
                    combined_data["store_stats"][store_name] = {"error": str(e)[:200]}
                    if ph:
                        ph.markdown(
                            f"<div class='progress-store progress-store-error'>"
                            f"❌ <strong>{store_name}</strong> — error (retrying later…)</div>",
                            unsafe_allow_html=True,
                        )

            # ── Rounds 2 & 3: deferred retries for failed stores ─────────────────
            for retry_num in range(1, 3):  # retry_num = 1, 2
                if not failed_stores:
                    break

                still_failing = []

                for store in failed_stores:
                    store_name = store["name"]
                    ph = store_placeholders.get(store_name)
                    try:
                        success, error = scrape_store(
                            store, f"retry {retry_num}/2"
                        )
                        if not success:
                            still_failing.append(store)
                            combined_data["store_stats"][store_name] = {"error": error[:200]}
                            if ph:
                                if retry_num < 2:
                                    ph.markdown(
                                        f"<div class='progress-store progress-store-error'>"
                                        f"❌ <strong>{store_name}</strong> — error (1 more retry…)</div>",
                                        unsafe_allow_html=True,
                                    )
                                else:
                                    ph.markdown(
                                        f"<div class='progress-store progress-store-error'>"
                                        f"❌ <strong>{store_name}</strong> — failed after 3 attempts</div>",
                                        unsafe_allow_html=True,
                                    )
                    except Exception as e:
                        still_failing.append(store)
                        combined_data["store_stats"][store_name] = {"error": str(e)[:200]}
                        if ph:
                            if retry_num < 2:
                                ph.markdown(
                                    f"<div class='progress-store progress-store-error'>"
                                    f"❌ <strong>{store_name}</strong> — error (1 more retry…)</div>",
                                    unsafe_allow_html=True,
                                )
                            else:
                                ph.markdown(
                                    f"<div class='progress-store progress-store-error'>"
                                    f"❌ <strong>{store_name}</strong> — failed after 3 attempts</div>",
                                    unsafe_allow_html=True,
                                )

                failed_stores = still_failing

            # ── Final sort ────────────────────────────────────────────────────────
            combined_data["exact_matches"].sort(key=lambda x: (not x["in_stock"], _m.price_sort_value(x.get("price"))))
            combined_data["all_results"].sort(key=lambda x: (not x["in_stock"], _m.price_sort_value(x.get("price"))))
            return combined_data


        with spinner_ph:
            with st.spinner("Searching across selected stores... this may take a while"):
                results = _search_with_live_updates(current_query, active_stores)



        # Clear the live progress area after completion
        spinner_ph.empty()
        # progress_header.empty()
        for ph in store_placeholders.values():
            ph.empty()

        st.session_state.results = results
        st.session_state.search_in_progress = False


# ── Display results ───────────────────────────────────────────────────────────
if not st.session_state.get("search_in_progress", False):
    data = st.session_state.results
else:
    data = None



with results_panel.container():
    if data:
        exact_matches = data.get("exact_matches", [])
        all_results = data.get("all_results", [])
        store_stats = data.get("store_stats", {})

        # Derive partial matches
        exact_urls = {item["url"] for item in exact_matches}
        partial_matches = [item for item in all_results if item["url"] not in exact_urls]

        # Best price (in-stock exact matches first, then all in-stock)
        in_stock_exact = [x for x in exact_matches if x["in_stock"]]
        in_stock_all = [x for x in all_results if x["in_stock"]]
        # best_item = in_stock_exact[0] if in_stock_exact else (in_stock_all[0] if in_stock_all else None)
        best_item = in_stock_exact[0] if in_stock_exact else None
        best_price_str = format_price_display(best_item.get("price")) if best_item else "N/A"

        total_stores = len(store_stats)

        # ── Overview metrics ──────────────────────────────────────────────────────
        st.markdown("---")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🏪 Stores Searched", total_stores)
        m2.metric("🎯 Exact Matches", len(exact_matches))
        m3.metric("🔍 Partial Matches", len(partial_matches))
        m4.metric("💰 Best Price", best_price_str)

        # Temporary eFantasy diagnostics: progress placeholders are cleared,
        # so surface debug info in the persistent results panel.
        ef_debug = store_stats.get("eFantasy", {}).get("debug", {})
        if ef_debug:
            st.info(
                "eFantasy debug: "
                f"source={ef_debug.get('session_source', 'n/a')} | "
                f"status={ef_debug.get('status', 'n/a')} | "
                f"body={ef_debug.get('body_len', 'n/a')} | "
                f"blocks={ef_debug.get('result_blocks', 'n/a')} | "
                f"parsed={ef_debug.get('parsed_count', 'n/a')} | "
                f"error={ef_debug.get('error', '')}"
            )

        # ── Single export action for all results ─────────────────────────────────
        pdf_bytes = build_results_pdf(st.session_state.query, exact_matches, partial_matches)
        if pdf_bytes:
            st.download_button(
                "📄 Download PDF Results",
                data=pdf_bytes,
                file_name=f"boardgame-broke-{st.session_state.query.strip().replace(' ', '-')}.pdf",
                mime="application/pdf",
                use_container_width=False,
            )
        else:
            st.warning("PDF export requires the `reportlab` package.")

        # ── Exact Matches ─────────────────────────────────────────────────────────
        st.markdown('<div class="section-header">🎯 Exact Matches</div>', unsafe_allow_html=True)

        if exact_matches:
            st.markdown(build_html_table(exact_matches), unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#B8A898; font-style:italic;'>No exact matches found for this title.</p>", unsafe_allow_html=True)

        # ── Partial Matches ───────────────────────────────────────────────────────
        st.markdown('<div class="section-header">🔍 Partial Matches</div>', unsafe_allow_html=True)

        if partial_matches:
            st.markdown(build_html_table(partial_matches), unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#B8A898; font-style:italic;'>No partial matches found.</p>", unsafe_allow_html=True)

        # ── Store coverage detail (collapsible) ───────────────────────────────────
        with st.expander("📊 Store Coverage Details", expanded=False):
            for store, stats in store_stats.items():
                if "error" in stats:
                    st.markdown(
                        f"<span style='color:#E07070;'>❌ **{store}** — {stats['error'][:80]}</span>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"<span style='color:#A0D8B0;'>✅ **{store}** — {stats['total']} items found ({stats['exact']} exact)</span>",
                        unsafe_allow_html=True,
                    )
