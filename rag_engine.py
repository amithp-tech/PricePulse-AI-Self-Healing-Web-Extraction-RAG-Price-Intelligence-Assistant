import os
import numpy as np
from openai import OpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from database import get_all_snapshots
from schemas import ProductData

_indexed_docs: list[dict] = []


def _format_record(item: dict) -> str:
    specs = ", ".join(item.get("key_specs", []))
    return (
        f"Product: {item['title']} | Price: {item['currency']} {item['price']} | "
        f"In Stock: {item['in_stock']} | Specs: {specs} | "
        f"Date: {item['extracted_at']} | URL: {item['url']}"
    )


def index_product(product: ProductData) -> None:
    _indexed_docs.append(
        {
            "url": product.url,
            "title": product.title,
            "price": product.price,
            "currency": product.currency,
            "in_stock": product.in_stock,
            "key_specs": product.key_specs,
            "extracted_at": product.extracted_at,
        }
    )


def _retrieve_relevant(question: str, top_k: int = 5) -> list[dict]:
    records = get_all_snapshots(limit=100) or _indexed_docs
    if not records:
        return []

    corpus = [_format_record(r) for r in records]
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(corpus + [question])
    scores = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [records[i] for i in top_indices]


def ask_price_assistant(question: str) -> tuple[str, list[dict]]:
    relevant = _retrieve_relevant(question)
    if not relevant:
        return "No tracked products found yet. Track a URL first.", []

    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise ValueError("LLM_API_KEY is missing in .env")

    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
    )
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    context = "\n".join(_format_record(r) for r in relevant)
    completion = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": (
                    "Answer the user's question using ONLY the retrieved product price records below. "
                    "Cite exact prices and product titles."
                ),
            },
            {"role": "user", "content": f"Records:\n{context}\n\nQuestion: {question}"},
        ],
    )

    answer = completion.choices[0].message.content
    return answer, relevant
