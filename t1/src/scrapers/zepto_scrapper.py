from playwright.sync_api import sync_playwright
import json
import os

from core.config import RAW_DIR

PINCODE = "560026"
SEARCH_TERM = "Hot Wheels"


def _extract_product_from_dict(product):
    if not isinstance(product, dict):
        return None

    name = product.get("name") or product.get("display_name") or product.get("title")
    brand = product.get("brand") or product.get("brand_name")
    if isinstance(brand, dict):
        brand = brand.get("text")

    if brand and str(brand).lower() != "hot wheels":
        return None

    price = (
        product.get("price")
        or product.get("selling_price")
        or product.get("final_price")
    )
    mrp = product.get("mrp") or product.get("list_price")

    return {
        "product_id": product.get("id") or product.get("product_id") or product.get("sku"),
        "merchant_id": product.get("merchant_id"),
        "name": name,
        "brand": brand,
        "price": price,
        "mrp": mrp,
        "inventory": product.get("inventory") or product.get("stock"),
        "is_sold_out": bool(product.get("is_sold_out") or product.get("out_of_stock")),
        "deep_link": product.get("deep_link") or product.get("url"),
    }


def extract_products(raw_batches):
    products = []

    for payload in raw_batches:
        if not isinstance(payload, dict):
            continue

        candidate_lists = []
        for key in ("products", "results", "items", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                candidate_lists.append(value)
            elif isinstance(value, dict):
                for nested_key in ("products", "results", "items"):
                    nested_value = value.get(nested_key)
                    if isinstance(nested_value, list):
                        candidate_lists.append(nested_value)

        for candidates in candidate_lists:
            for candidate in candidates:
                product = _extract_product_from_dict(candidate)
                if product and product.get("product_id"):
                    products.append(product)

    unique = {}
    for product in products:
        unique[str(product["product_id"])] = product

    return list(unique.values())


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
            if "/search" not in response.url and "product" not in response.url:
                return
            if response.status != 200:
                return
            try:
                json_data = response.json()
            except Exception:
                return

            if isinstance(json_data, dict):
                captured_payloads.append(json_data)

        page.on("response", capture_response)

        page.goto("https://www.zeptonow.com/", timeout=60000)
        page.wait_for_timeout(4000)

        try:
            page.locator("input[placeholder*='pincode'], input[placeholder*='Pincode']").first.fill(PINCODE, timeout=5000)
            page.wait_for_timeout(2000)
            page.keyboard.press("Enter")
            page.wait_for_timeout(2000)
        except Exception:
            pass

        try:
            page.locator("input[placeholder*='Search']").fill(SEARCH_TERM, timeout=5000)
        except Exception:
            page.locator("input[type='search']").first.fill(SEARCH_TERM, timeout=5000)

        page.wait_for_timeout(5000)
        browser.close()

    products = extract_products(captured_payloads)
    if products:
        return {"response": {"snippets": [{"data": p} for p in products]}}
    return None


if __name__ == "__main__":
    data = run()

    if not data:
        print("No data captured")
        raise SystemExit(1)

    file_path = os.path.join(RAW_DIR, "zepto_raw.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    products = extract_products([{"products": [snippet.get("data", {}) for snippet in data["response"]["snippets"]]}])
    print(f"Saved Zepto raw JSON to: {file_path}")
    print(f"Total products found: {len(products)}")
