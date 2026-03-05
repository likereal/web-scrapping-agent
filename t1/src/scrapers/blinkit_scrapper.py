from playwright.sync_api import sync_playwright
import json
import os
from core.config import RAW_DIR

PINCODE = "560026"
SEARCH_TERM = "Hot Wheels"


def extract_products(data):
    products = []

    snippets = data.get("response", {}).get("snippets", [])

    for snippet in snippets:
        product = snippet.get("data", {})

        if product.get("brand_name", {}).get("text") == "Hot Wheels":
            products.append({
                "product_id": product.get("product_id"),
                "name": product.get("display_name", {}).get("text"),
                "brand": product.get("brand_name", {}).get("text"),
                "price": product.get("atc_action", {})
                                .get("add_to_cart", {})
                                .get("cart_item", {})
                                .get("price"),
                "mrp": product.get("atc_action", {})
                              .get("add_to_cart", {})
                              .get("cart_item", {})
                              .get("mrp"),
                "inventory": product.get("inventory"),
                "is_sold_out": product.get("is_sold_out")
            })

    return products


def run():
    search_data = {"snippets": []}  # ✅ changed

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Added a real User-Agent to prevent bot detection in headless mode
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # 1️⃣ Open homepage
        page.goto("https://blinkit.com/", timeout=60000)
        page.wait_for_timeout(3000)

        # 2️⃣ Set location
        try:
            # We use a short 5-second timeout here. 
            # If the site already knows your location, this input won't exist.
            page.locator("input[name='select-locality']").fill(PINCODE, timeout=5000)
            page.wait_for_timeout(2000)

            page.locator(
                "div.LocationSearchList__LocationListContainer-sc-93rfr7-0"
            ).first.click()

            page.wait_for_timeout(4000)
            print("Location selected")
        except:
            print("Location input not found or already set. Proceeding to search.")

        # 3️⃣ Click search button
        page.locator("a[href='/s/']").click()
        page.wait_for_timeout(3000)

        # 4️⃣ Prepare response capture
        def capture_response(response):
            if response.status == 200:
                try:
                    json_data = response.json()

                    if (
                        isinstance(json_data, dict)
                        and "response" in json_data
                        and "snippets" in json_data["response"]
                        and len(json_data["response"]["snippets"]) > 0
                    ):
                        snippets = json_data["response"]["snippets"]

                        # ✅ Instead of overwrite → append
                        search_data["snippets"].extend(snippets)

                        print(f"Captured batch: {len(snippets)}")

                except:
                    pass

        page.on("response", capture_response)

        # 5️⃣ Type search term
        search_input = page.locator("input[placeholder*='Search']")
        search_input.fill(SEARCH_TERM)
        page.wait_for_timeout(3000)

        # 6️⃣ Click suggestion row
        page.locator("div:has-text('Hot wheels')").first.click()
        page.wait_for_timeout(5000)

        browser.close()

        # ✅ Proper return structure
        if search_data["snippets"]:
            return {"response": {"snippets": search_data["snippets"]}}
        return None


if __name__ == "__main__":
    data = run()

    if not data:
        print("No data captured")
        exit()

    print("Raw JSON captured")

    file_path = os.path.join(RAW_DIR, "blinkit_raw.json")
    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(data, f, indent=2)

    products = extract_products(data)

    print("\n===== Extracted Products =====\n")

    for p in products:
        print(p)

    print(f"\nTotal products found: {len(products)}")
