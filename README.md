# PricePulse AI — Self-Healing Web Extraction & RAG Price Assistant

A focused re-imagination of a traditional e-commerce price tracker, inspired by [Firecrawl](https://www.ycombinator.com/companies/firecrawl) and [Browser Use](https://www.ycombinator.com/companies/browser-use).

Instead of relying on brittle CSS selectors (`span.a-offscreen`, `span#productTitle`) and hardcoded price thresholds, **PricePulse AI** converts any product page into clean Markdown, extracts structured JSON using an LLM with Pydantic validation, logs historical snapshots in SQLite, and supports natural-language Q&A over tracked items.

## Why Re-Imagine a Traditional Scraper?
- **No Brittle Selectors:** Hardcoded BeautifulSoup rules break whenever a storefront updates its HTML or when tracking non-Amazon sites.
- **Structured & Validated Output:** Schema-driven LLM extraction ensures consistent `title`, `price`, `currency`, `availability`, and `key_specs` across different storefronts.
- **Interactive Price Intelligence:** Historical snapshots are indexed for RAG-based Q&A (e.g., *"Which tracked item dropped the most this week?"*) alongside automated SMTP alerts.

## Key Features & Concepts
- **HTML-to-Markdown Normalization:** Strips boilerplate scripts, navbars, and styling with BeautifulSoup/Trafilatura before LLM processing.
- **Schema-Driven LLM Extraction:** Uses an LLM API + Pydantic schemas to parse unstructured product pages into validated JSON.
- **Time-Series Storage & RAG:** Logs price snapshots in SQLite and indexes product metadata in FAISS/Chroma for natural-language comparisons.
- **Smart Alert Pipeline:** Evaluates user-defined drop conditions and sends automated email notifications via `smtplib`.

## Tech Stack
- **Language:** Python 3.10+
- **Backend & UI:** FastAPI, Streamlit
- **Extraction & Validation:** BeautifulSoup4, Trafilatura, Pydantic, LLM API
- **Storage & RAG:** SQLite, FAISS / Chroma
- **Notifications & Testing:** `smtplib`, `python-dotenv`, `pytest`

## Architecture
1. **Ingest:** Fetch target product URL with browser-like headers and convert HTML to clean Markdown.
2. **Extract:** Pass Markdown + Pydantic schema to the LLM to return structured product JSON.
3. **Store & Index:** Save the timestamped price snapshot to SQLite and update vector embeddings.
4. **Query & Alert:** Answer user questions via RAG in the Streamlit UI and trigger SMTP email alerts on qualifying price drops.

## Quick Start
1. Clone the repository and create a virtual environment:
   ```bash
   git clone [https://github.com/amithp-tech/Amazon-Price-Tracker.git](https://github.com/amithp-tech/Amazon-Price-Tracker.git)
   cd Amazon-Price-Tracker
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
