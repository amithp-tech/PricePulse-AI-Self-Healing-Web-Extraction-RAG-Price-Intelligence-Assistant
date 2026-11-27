import json
import os
import requests
import trafilatura
from bs4 import BeautifulSoup
from openai import OpenAI

from schemas import ProductData

DEFAULT_HEADERS = {
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
}


def fetch_html(url: str, timeout: int = 15) -> str:
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.text


def html_to_markdown(html: str) -> str:
    extracted = trafilatura.extract(
        html, output_format="markdown", include_tables=True, include_links=False
    )
    if extracted and len(extracted.strip()) > 50:
        return extracted[:12000]

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "footer", "nav"]):
        tag.decompose()
    text = "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())
    return text[:12000]


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
        "You are a precise e-commerce data extractor. Given webpage text, return ONLY valid JSON "
        "matching this schema: "
        '{"title": str, "price": float, "currency": str, "in_stock": bool, "key_specs": list[str]}. '
        "If price is missing, use 0.0."
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
    return ProductData(
        url=url,
        title=raw_json.get("title", "Unknown Product"),
        price=float(raw_json.get("price", 0.0)),
        currency=raw_json.get("currency", "USD"),
        in_stock=bool(raw_json.get("in_stock", True)),
        key_specs=list(raw_json.get("key_specs", [])),
    )


def extract_product_data(url: str) -> ProductData:
    html = fetch_html(url)
    markdown = html_to_markdown(html)
    return parse_product_markdown(markdown, url)
