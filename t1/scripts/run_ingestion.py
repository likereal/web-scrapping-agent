import sys
import os

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from core.load_landing import load_into_landing
from core.merge_to_current import merge_to_current

def run_pipeline():
    print("Starting ingestion pipeline...")
    load_into_landing()
    merge_to_current()
    print("Pipeline run complete.")

if __name__ == "__main__":
    run_pipeline()
