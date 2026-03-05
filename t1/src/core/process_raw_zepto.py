import json
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from core.config import RAW_DIR, PROCESSED_DIR

SCHEMA_REGISTRY_FILE = os.path.join(PROCESSED_DIR, "schema_registry.json")


def parse_price(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        value = value.replace("₹", "").replace(",", "").strip()
        try:
            return float(value)
        except Exception:
            return None
    return None


def load_schema_registry():
    if not os.path.exists(SCHEMA_REGISTRY_FILE):
        return {}
    with open(SCHEMA_REGISTRY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_schema_registry(schema):
    with open(SCHEMA_REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)


def detect_schema(data):
    snippets = data.get("response", {}).get("snippets", [])
    if not snippets:
        return []
    sample_product = snippets[0].get("data", {})
    if isinstance(sample_product, dict):
        return sorted(sample_product.keys())
    return []


def normalize_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    products = []
    snippets = raw_data.get("response", {}).get("snippets", [])

    for snippet in snippets:
        product = snippet.get("data", {})
        if not isinstance(product, dict):
            continue

        brand = product.get("brand")
        if brand and str(brand).lower() != "hot wheels":
            continue

        name = product.get("name")
        product_id = product.get("product_id")
        if not product_id:
            continue

        normalized = {
            "platform": "zepto",
            "product_id": product_id,
            "merchant_id": product.get("merchant_id"),
            "name": name,
            "brand": brand,
            "price": parse_price(product.get("price")),
            "mrp": parse_price(product.get("mrp")),
            "inventory": product.get("inventory"),
            "is_sold_out": product.get("is_sold_out"),
            "deep_link": product.get("deep_link"),
            "search_url": f"https://www.zeptonow.com/search?query={quote(name)}" if name else None,
            "extracted_at": datetime.utcnow().isoformat(),
        }
        products.append(normalized)

    return products


def process_all_raw_zepto():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    schema_registry = load_schema_registry()
    all_products = []

    for file in Path(RAW_DIR).glob("zepto_*.json"):
        print(f"Processing: {file}")
        with open(file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        current_schema = detect_schema(raw_data)
        if "zepto" not in schema_registry:
            schema_registry["zepto"] = current_schema
            print("Initial Zepto schema registered.")
        elif schema_registry["zepto"] != current_schema:
            print("⚠ Zepto schema drift detected!")
            schema_registry["zepto"] = sorted(list(set(schema_registry["zepto"]) | set(current_schema)))

        all_products.extend(normalize_file(file))

    output_file = f"{PROCESSED_DIR}/zepto_processed.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_products, f, indent=2)

    save_schema_registry(schema_registry)

    print(f"Processed {len(all_products)} Zepto products.")
    print(f"Output saved to {output_file}")


if __name__ == "__main__":
    process_all_raw_zepto()
