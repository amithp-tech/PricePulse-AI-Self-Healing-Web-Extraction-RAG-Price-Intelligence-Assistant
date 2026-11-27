import json
import os
import re
import trafilatura
from bs4 import BeautifulSoup
from openai import OpenAI
from playwright.sync_api import sync_playwright

from schemas import ProductData

DEFAULT_HEADERS = {
    "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
}

RATES_TO_INR = {
    "INR": 1.0,
    "USD": 84.5,
    "GBP": 107.0,
    "EUR": 91.5,
    "AED": 23.0,
    "CAD": 60.5,
    "AUD": 55.0,
}


def fetch_html(url: str, timeout: int = 30) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=DEFAULT_HEADERS["User-Agent"],
            locale="en-IN",
            extra_http_headers={"Accept-Language": DEFAULT_HEADERS["Accept-Language"]},
        )
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
        page.wait_for_timeout(3000)
        html = page.content()
        browser.close()
        return html


def extract_price_hints(soup: BeautifulSoup) -> str:
    hints = []

    # 1. Check JSON-LD structured product schema (used by Amazon, Flipkart, Shopify, etc.)
    for script in soup.find_all("script", type="application/ld+json"):
        if script.string and ("price" in script.string.lower()):
            hints.append(script.string.strip()[:1200])

    # 2. Check common e-commerce price CSS selectors (Amazon, Flipkart, general stores)
    selectors = [
        "#corePriceDisplay_desktop_feature_div .a-price .a-offscreen",
        "#corePrice_feature_div .a-price .a-offscreen",
        ".priceToPay .a-offscreen",
        ".a-price .a-offscreen",
        "#priceblock_ourprice",
        "#priceblock_dealprice",
        "[itemprop='price']",
        "[data-price]",
        ".price_color",
    ]
    for sel in selectors:
        for el in soup.select(sel)[:3]:
            val = el.get("content") or el.get("data-price") or el.get_text(strip=True)
            if val:
                hints.append(f"Detected price element ({sel}): {val}")

    return "\n".join(dict.fromkeys(hints))


def html_to_markdown(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    price_hints = extract_price_hints(soup)

    extracted = trafilatura.extract(
        html, output_format="markdown", include_tables=True, include_links=False
    )
    if extracted and len(extracted.strip()) > 50:
        body = extracted[:3500]
    else:
        for tag in soup(["script", "style", "noscript", "svg", "footer", "nav"]):
            tag.decompose()
        text = "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())
        body = text[:3500]

    if price_hints:
        return f"=== EXTRACTED PRICE SIGNALS ===\n{price_hints[:1200]}\n\n=== PAGE CONTENT ===\n{body}"
    return body


def parse_product_markdown(markdown: str, url: str) -> ProductData:
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise ValueError("LLM_API_KEY is missing in .env")

    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
    )
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    system_prompt = (
        "You are a precise e-commerce data extractor. Given webpage text and price signals, return ONLY valid JSON "
        "matching this schema: "
        '{"title": str, "price": float, "currency": str, "in_stock": bool, "key_specs": list[str]}. '
        "Return price as a plain number without commas or symbols (e.g., 129999.0 for ₹1,29,999.00). "
        "Use standard 3-letter ISO currency codes (e.g., INR for ₹ or Rs., USD for $, GBP for £, EUR for €). "
        "If price is truly missing, use 0.0."
    )

    completion = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"URL: {url}\n\nContent:\n{markdown}"},
        ],
    )

    raw_json = json.loads(completion.choices[0].message.content)

    # Clean commas if the model ever returns a formatted string like "1,29,999"
    raw_price_val = str(raw_json.get("price", 0.0)).replace(",", "").strip()
    raw_price_match = re.search(r"\d+(?:\.\d+)?", raw_price_val)
    raw_price = float(raw_price_match.group()) if raw_price_match else 0.0

    raw_currency = str(raw_json.get("currency", "INR")).upper().strip()
    rate = RATES_TO_INR.get(raw_currency, 1.0)
    price_in_inr = round(raw_price * rate, 2)
    final_currency = "INR" if raw_currency in RATES_TO_INR else raw_currency

    return ProductData(
        url=url,
        title=raw_json.get("title", "Unknown Product"),
        price=price_in_inr,
        currency=final_currency,
        in_stock=bool(raw_json.get("in_stock", True)),
        key_specs=list(raw_json.get("key_specs", [])),
    )


def extract_product_data(url: str) -> ProductData:
    html = fetch_html(url)
    markdown = html_to_markdown(html)
    return parse_product_markdown(markdown, url)
