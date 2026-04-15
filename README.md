<p align="center">
  <img src="assets/images/Broke_logo_down.png" alt="BoardGame Broke Logo" width="110"/>
</p>

<h1 align="center">BoardGame Broke</h1>

**Hunt the best deal before your wallet gives up!**  
A Streamlit web app that searches for a board game across **26 Greek online stores** simultaneously and shows you prices, availability, and direct product links — all in one place.

---

## 🚀 Try It Live

👉 **[Launch BoardGame Broke on Streamlit →](https://boardgame-broke.streamlit.app/)**  

If you enjoy it, consider showing your support — it helps keep the app online and improving!  
☕ **[Buy Me a Coffee](https://buymeacoffee.com/vasileios)**  

---

## 💡 Features

✅ Search any board game by name across **26 Greek stores** in a single query  
✅ Results split into **Exact Matches** and **Partial Matches** for clarity  
✅ Prices sorted from lowest to highest automatically  
✅ In-stock / out-of-stock badge for each result  
✅ Direct product links so you can go straight to checkout  
✅ **Select / Deselect** individual stores to narrow your search  
✅ Export results as a **PDF report** with clickable links  
✅ Clean, modern interface built with Streamlit  

---

## 🏪 Supported Stores

| | | |
|---|---|---|
| Ozon.gr | Meeple On Board | The Game Rules |
| Fantasy Shop | Boards of Madness | Nerdom |
| eFantasy | Mystery Bay | Meeple Planet |
| epitrapez.io | No Label X | GamesUniverse |
| SoHotTCG | RollnPlay | PlayceShop |
| Politeia | Crystal Lotus | Kaissa |
| Tech City | Game Theory | Gaming Galaxy |
| The Dragonphoenix Inn | Lex Hobby Store | GenX |
| Public | VP shop | |

---

## 🧩 How It Works

<p align="justify">
BoardGame Broke uses <b>Firecrawl</b> to scrape search result pages and a set of custom HTML parsers — one per store — to extract product names, prices, and stock status. Several stores (eFantasy, Public, Ozon.gr, RollnPlay, Meeple Planet, Crystal Lotus, Gaming Galaxy, The Dragonphoenix Inn) are queried directly through their own APIs or search endpoints, bypassing the scraper entirely for faster and more reliable results.</p>

Here's what happens behind the scenes:

1. **Type** a board game name and press Search.
2. The app queries all selected stores **simultaneously**, either via Firecrawl or direct API calls.
3. Each store's response is parsed by a **dedicated HTML parser** that knows the store's layout.
4. Results are **normalized** and deduplicated, then matched against your query using fuzzy word-boundary logic.
5. Matches are split into **Exact** and **Partial** tables and sorted by price.
6. You can optionally **export the results to PDF** for easy sharing or offline reference.

---

## 🛠️ Tech Stack

| Component | Library / Tool |
|------------|----------------|
| Web app | [Streamlit](https://streamlit.io/) |
| Web scraping | [Firecrawl](https://www.firecrawl.dev/) |
| Direct store APIs | `requests` (custom per-store logic) |
| Data models | [Pydantic](https://docs.pydantic.dev/) |
| PDF export | [ReportLab](https://www.reportlab.com/) |
| HTML parsing | Python `re`, `html` (standard library) |

---

## ⚙️ Configuration

The app requires the following secrets (set via Streamlit secrets or a local `config.py`):

| Secret | Description |
|--------|-------------|
| `FIRECRAWL_API_KEY` | API key for Firecrawl web scraping |
| `EFANTASY_SESSION_ID` | Session ID for eFantasy Findbar search |

---

## ⚠️ Disclaimer

The prices, availability, and links shown in this app are collected automatically and may not always be fully accurate. Store websites can change their structure, product pages, or stock information at any time, which may affect the results displayed here. Please verify all details directly on the store's website before making any purchase decision.
