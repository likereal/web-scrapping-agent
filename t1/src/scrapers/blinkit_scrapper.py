import sys
import os

# Add src to python path so it can find "core" and "model"
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.append(src_dir)

from playwright.sync_api import sync_playwright
import json
from core.config import RAW_DIR
from model.mistral import predict_element_from_candidates
from model.semantic_search import get_best_candidates
from bs4 import BeautifulSoup


PINCODE = "560026"
SEARCH_TERM = "Hot Wheels"


def extract_products(data):
    products = []

    snippets = data.get("response", {}).get("snippets", [])

    for snippet in snippets:
        product = snippet.get("data", {})
        
        # Check brand name - more flexible (case-insensitive)
        brand_name = product.get("brand_name", {}).get("text", "")
        display_name = product.get("display_name", {}).get("text", "")
        
        # We also check display name as a fallback
        is_match = "hot wheels" in brand_name.lower() or "hot wheels" in display_name.lower()

        if is_match:
            products.append({
                "product_id": product.get("product_id"),
                "name": display_name,
                "brand": brand_name,
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


def extract_nodes(html):
    soup = BeautifulSoup(html, "html.parser")

    nodes = []

    for element in soup.find_all(True):
        nodes.append({
            "tag": element.name,
            "class": element.get("class"),
            "id": element.get("id"),
            "text": element.get_text(strip=True)
        })

    return nodes

def node_to_text(node):
    return f"""
    tag: {node['tag']}
    class: {node['class']}
    text: {node['text']}
    """

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
            print(f"Attempting to set location to {PINCODE}...")
            # We use a short 5-second timeout here. 
            # If the site already knows your location, this input won't exist.
            page.locator("input[name='select-locality']").fill(PINCODE, timeout=5000)
            page.wait_for_timeout(2000)

            page.locator(
                "div.LocationSearchList__LocationListContainer-sc-93rfr7-0"
            ).first.click()

            page.wait_for_timeout(4000)
            print("Location selected via direct locator.")
        except Exception as e:
            print(f"Direct location selection failed: {e}. Attempting AI-assisted semantic discovery...")
            try:
                reference_element = "input for pincode or locality"
                html_content = page.content()
                nodes = extract_nodes(html_content)
                
                # Use Semantic Search to find candidates
                print(f"Finding top candidates for '{reference_element}'...")
                candidates = get_best_candidates(nodes, reference_element, k=5)
                
                # Ask Mistral to pick from candidates
                element_id = predict_element_from_candidates(candidates, reference_element)
                
                print(f"AI picked locator: {element_id}")
                page.locator(element_id).fill(PINCODE, timeout=5000)
                page.wait_for_timeout(2000)

                page.locator(
                    "div.LocationSearchList__LocationListContainer-sc-93rfr7-0"
                ).first.click()
                page.wait_for_timeout(4000)
                print("Location selected via Semantic Search + AI.")
            except Exception as e2:
                print(f"Semantic discovery also failed: {e2}. Proceeding anyway.")

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
