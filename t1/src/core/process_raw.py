import os
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import quote


from core.config import RAW_DIR, PROCESSED_DIR, DATA_DIR

SCHEMA_REGISTRY_FILE = os.path.join(PROCESSED_DIR, "schema_registry.json")




def parse_price(value):
    """
    Safely parse price.
    Handles int OR string like '₹1,600'
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        value = value.replace("₹", "").replace(",", "").strip()
        try:
            return float(value)
        except:
            return None

    return None




# ----------------------------
# Utility: Safe nested get
# ----------------------------
def safe_get(d, *keys):
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key)
        else:
            return None
    return d


# ----------------------------
# Load schema registry
# ----------------------------
def load_schema_registry():
    if not os.path.exists(SCHEMA_REGISTRY_FILE):
        return {}
    with open(SCHEMA_REGISTRY_FILE, "r") as f:
        return json.load(f)


# ----------------------------
# Save schema registry
# ----------------------------
def save_schema_registry(schema):
    with open(SCHEMA_REGISTRY_FILE, "w") as f:
        json.dump(schema, f, indent=2)


# ----------------------------
# Detect schema changes
# ----------------------------
def detect_schema(data):
    """
    Detect top-level product schema keys
    """
    snippets = data.get("response", {}).get("snippets", [])
    if not snippets:
        return {}

    sample_product = snippets[0].get("data", {})
    return sorted(sample_product.keys())


# ----------------------------
# Normalize single file
# ----------------------------

def normalize_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    products = []
    snippets = raw_data.get("response", {}).get("snippets", [])

    for snippet in snippets:
        if safe_get(snippet.get("data", {}), "brand_name", "text")=='Hot Wheels':
            product = snippet.get("data", {})

            product_id = safe_get(product, "product_id")
            merchant_id = safe_get(product, "merchant_id")

            name = safe_get(product, "display_name", "text")
            brand = safe_get(product, "brand_name", "text")

            # Primary price source
            price = safe_get(product, "atc_action", "add_to_cart", "cart_item", "price")

            # Fallback price
            if price is None:
                price = safe_get(product, "normal_price", "text")

            price = parse_price(price)

            mrp = safe_get(product, "atc_action", "add_to_cart", "cart_item", "mrp")
            if mrp is None:
                mrp = safe_get(product, "mrp", "text")

            mrp = parse_price(mrp)

            inventory = safe_get(product, "inventory")
            is_sold_out = safe_get(product, "is_sold_out")

            deep_link = safe_get(product, "click_action", "blinkit_deeplink", "url")

            search_url = None
            if name:
                search_url = f"https://blinkit.com/s/?q={quote(name)}"

            normalized = {
                "platform": "blinkit",
                "product_id": product_id,
                "merchant_id": merchant_id,
                "name": name,
                "brand": brand,
                "price": price,
                "mrp": mrp,
                "inventory": inventory,
                "is_sold_out": is_sold_out,
                "deep_link": deep_link,
                "search_url": search_url,
                "extracted_at": datetime.utcnow().isoformat()
            }

            if product_id:
                products.append(normalized)
            

    return products

# ----------------------------
# Main processing logic
# ----------------------------
def process_all_raw():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    schema_registry = load_schema_registry()
    all_products = []

    for file in Path(RAW_DIR).glob("*.json"):
        print(f"Processing: {file}")

        with open(file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        # 1️⃣ Detect schema
        current_schema = detect_schema(raw_data)

        if "blinkit" not in schema_registry:
            schema_registry["blinkit"] = current_schema
            print("Initial schema registered.")
        else:
            if schema_registry["blinkit"] != current_schema:
                print("⚠ Schema drift detected!")
                print("Old:", schema_registry["blinkit"])
                print("New:", current_schema)

                # Update schema registry (schema evolution)
                schema_registry["blinkit"] = sorted(
                    list(set(schema_registry["blinkit"]) | set(current_schema))
                )

        # 2️⃣ Normalize
        normalized_products = normalize_file(file)
        all_products.extend(normalized_products)

    # Save processed output
    output_file = f"{PROCESSED_DIR}/blinkit_processed.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_products, f, indent=2)

    save_schema_registry(schema_registry)

    print(f"\nProcessed {len(all_products)} products.")
    print(f"Output saved to {output_file}")


if __name__ == "__main__":
    process_all_raw()
