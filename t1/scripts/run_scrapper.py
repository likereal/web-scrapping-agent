import sys
import os

# Add src to python path so it can find "core"
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

# Now we can import the scraper and run it
from scrapers.blinkit_scrapper import run, extract_products, RAW_DIR
import json

if __name__ == "__main__":
    print("Starting Blinkit Scraper...")
    data = run()
    
    if data:
        file_path = os.path.join(RAW_DIR, "blinkit_raw.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Success! Data saved to: {file_path}")
    else:
        print("Scraper failed to capture data.")
