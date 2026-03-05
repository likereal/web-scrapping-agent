import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from scrapers.zepto_scrapper import run
from core.config import RAW_DIR


if __name__ == "__main__":
    print("Starting Zepto Scraper...")
    data = run()

    if not data:
        print("Zepto scraper failed to capture data.")
        raise SystemExit(1)

    file_path = os.path.join(RAW_DIR, "zepto_raw.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Success! Data saved to: {file_path}")
