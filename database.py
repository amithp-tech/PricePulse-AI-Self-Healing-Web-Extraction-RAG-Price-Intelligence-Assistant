import json
import sqlite3
from pathlib import Path

from schemas import ProductData

DB_PATH = Path("pricepulse.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                price REAL NOT NULL,
                currency TEXT NOT NULL,
                in_stock INTEGER NOT NULL,
                key_specs TEXT NOT NULL,
                extracted_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def save_snapshot(product: ProductData) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO snapshots (url, title, price, currency, in_stock, key_specs, extracted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product.url,
                product.title,
                product.price,
                product.currency,
                int(product.in_stock),
                json.dumps(product.key_specs),
                product.extracted_at,
            ),
        )
        conn.commit()


def get_all_snapshots(limit: int = 50) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, url, title, price, currency, in_stock, key_specs, extracted_at
            FROM snapshots
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    results = []
    for row in rows:
        item = dict(row)
        item["in_stock"] = bool(item["in_stock"])
        item["key_specs"] = json.loads(item["key_specs"])
        results.append(item)
    return results
