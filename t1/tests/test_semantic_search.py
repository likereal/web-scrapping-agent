import sys
import os

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(current_dir), "src")
sys.path.append(src_dir)

from model.semantic_search import get_best_candidates
from model.mistral import predict_element_from_candidates

# Mock DOM nodes
sample_nodes = [
    {"tag": "div", "class": ["Header__Logo"], "text": "Blinkit", "id": "logo"},
    {"tag": "input", "class": ["LocationBar__Input"], "text": "", "id": "loc-input", "name": "select-locality"},
    {"tag": "button", "class": ["CartButton"], "text": "My Cart", "id": "cart"},
    {"tag": "span", "class": ["LocationText"], "text": "Select Location", "id": "loc-text"},
    {"tag": "a", "class": ["FooterLink"], "text": "Privacy Policy", "id": "privacy"}
]

query = "input for pincode or locality"

print(f"Testing Semantic Search for query: '{query}'")
candidates = get_best_candidates(sample_nodes, query, k=3)

print("\nTop Candidates found:")
for i, c in enumerate(candidates):
    print(f"{i+1}. Tag: {c['tag']}, ID: {c.get('id')}, Text: {c.get('text')}, Score: {c['score']:.4f}")

print("\nAsking LLM to pick the best selector from these candidates...")
try:
    best_selector = predict_element_from_candidates(candidates, query)
    print(f"\nResulting Selector: {best_selector}")
except Exception as e:
    print(f"\nLLM Call failed (is Ollama running?): {e}")
