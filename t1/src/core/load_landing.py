import sqlite3
import json

from core.config import DB_PATH, PROCESSED_DIR
import os

PROCESSED_FILE = os.path.join(PROCESSED_DIR, "blinkit_processed.json")


def load_into_landing():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
        products = json.load(f)

    for p in products:
        cur.execute("""
        INSERT INTO landing_products
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p["platform"],
            p["product_id"],
            p.get("merchant_id"),
            p["name"],
            p["brand"],
            p["price"],
            p["mrp"],
            p["inventory"],
            p["is_sold_out"],
            p.get("deep_link"),
            p.get("search_url"),
            p["extracted_at"]
        ))

    conn.commit()
    conn.close()

    print(f"Inserted {len(products)} rows into landing.")
