from playwright.sync_api import sync_playwright
import json
import os
from core.config import RAW_DIR

PINCODE = "560026"
SEARCH_TERM = "Hot Wheels"


def _safe_get(data, *keys):
    cur = data
    for key in keys:
        if isinstance(cur, dict):
            cur = cur.get(key)
        else:
            return None
    return cur


def _iter_product_candidates(payload):
    """
    Yield product-like dictionaries from nested Zepto API payloads.
    Zepto's response structure changes often, so we walk common list keys.
    """
    queue = [payload]

    while queue:
        node = queue.pop(0)

        if isinstance(node, dict):
            # A product candidate usually has one of these identifiers
            if any(k in node for k in ["id", "product_id", "sku", "name", "display_name"]):
                yield node

            for value in node.values():
                if isinstance(value, (dict, list)):
                    queue.append(value)

        elif isinstance(node, list):
            for item in node:
                if isinstance(item, (dict, list)):
                    queue.append(item)


def _normalize_product(product):
    name = (
        _safe_get(product, "name")
        or _safe_get(product, "display_name", "text")
        or _safe_get(product, "title")
    )
    brand = (
        _safe_get(product, "brand")
        or _safe_get(product, "brand_name")
        or _safe_get(product, "brand_name", "text")
    )

    if isinstance(brand, dict):
        brand = brand.get("text") or brand.get("name")

    price = (
        _safe_get(product, "selling_price")
        or _safe_get(product, "price")
        or _safe_get(product, "variant", "price")
    )
    mrp = (
        _safe_get(product, "mrp")
        or _safe_get(product, "list_price")
        or _safe_get(product, "variant", "mrp")
    )

    inventory = (
        _safe_get(product, "inventory")
        or _safe_get(product, "stock")
        or _safe_get(product, "available_quantity")
    )

    product_id = (
        _safe_get(product, "product_id")
        or _safe_get(product, "id")
        or _safe_get(product, "sku")
    )

    if not name:
        return None

    return {
        "product_id": product_id,
        "name": name,
        "brand": brand,
        "price": price,
        "mrp": mrp,
        "inventory": inventory,
        "is_sold_out": bool(_safe_get(product, "is_sold_out") or _safe_get(product, "out_of_stock")),
        "source": "zepto",
    }


def extract_products(payload):
    products = []
    seen = set()

    for candidate in _iter_product_candidates(payload):
        normalized = _normalize_product(candidate)
        if not normalized:
            continue

        # keep results focused on search term, same spirit as blinkit scraper
        text = f"{normalized.get('name', '')} {normalized.get('brand', '')}".lower()
        if SEARCH_TERM.lower() not in text:
            continue

        dedupe_key = normalized.get("product_id") or normalized.get("name")
        if dedupe_key in seen:
            continue

        seen.add(dedupe_key)
        products.append(normalized)

    return products


def run():
    captured_payloads = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        def capture_response(response):
            if response.status != 200:
                return

            url = response.url.lower()
            if "search" not in url and "product" not in url and "listing" not in url:
                return

            try:
                data = response.json()
            except Exception:
                return

            if isinstance(data, dict):
                captured_payloads.append({
                    "url": response.url,
                    "payload": data,
                })
                print(f"Captured Zepto API response: {response.url[:120]}")

        page.on("response", capture_response)

        page.goto("https://www.zeptonow.com/", timeout=60000)
        page.wait_for_timeout(5000)

        # Optional pincode/location step (ignored if element flow differs)
        try:
            page.locator("input[placeholder*='Enter pincode']").fill(PINCODE, timeout=4000)
            page.wait_for_timeout(1500)
            page.keyboard.press("Enter")
            page.wait_for_timeout(2500)
            print("Location step attempted")
        except Exception:
            print("Location step skipped")

        # Search flow
        try:
            page.locator("input[placeholder*='Search']").first.click(timeout=8000)
            page.locator("input[placeholder*='Search']").first.fill(SEARCH_TERM)
            page.wait_for_timeout(6000)
            page.keyboard.press("Enter")
            page.wait_for_timeout(8000)
            print("Search performed")
        except Exception:
            print("Search UI flow changed; kept captured responses so far")

        browser.close()

    return {
        "source": "zepto",
        "search_term": SEARCH_TERM,
        "captured_count": len(captured_payloads),
        "responses": captured_payloads,
    }


if __name__ == "__main__":
    data = run()

    file_path = os.path.join(RAW_DIR, "zepto_raw.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    products = extract_products(data)

    print("\n===== Extracted Zepto Products =====\n")
    for p in products:
        print(p)

    print(f"\nCaptured responses: {data.get('captured_count', 0)}")
    print(f"Total products found: {len(products)}")
    print(f"Saved raw data to: {file_path}")
