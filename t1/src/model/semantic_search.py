import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class SemanticSearch:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        print(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.nodes = []

    def build_index(self, nodes):
        """Builds a FAISS index from a list of DOM nodes."""
        if not nodes:
            return
        
        self.nodes = nodes
        # Use descriptive text for embedding
        node_texts = [self._node_to_text(n) for n in nodes]
        
        print(f"Generating embeddings for {len(nodes)} nodes...")
        embeddings = self.model.encode(node_texts)
        
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(embeddings).astype('float32'))
        print("Index built successfully.")

    def _node_to_text(self, node):
        """Converts a node dictionary to a string suitable for embedding."""
        tag = node.get('tag', '')
        classes = " ".join(node.get('class', [])) if isinstance(node.get('class'), list) else str(node.get('class', ''))
        text = node.get('text', '')[:200]  # Cap text length
        return f"tag: {tag} class: {classes} text: {text}".strip()

    def search(self, query, k=5):
        """Searches the index for the top k candidates matching the query."""
        if self.index is None:
            raise ValueError("Index has not been built yet.")
        
        query_embedding = self.model.encode([query])
        D, I = self.index.search(np.array(query_embedding).astype('float32'), k)
        
        results = []
        for i, idx in enumerate(I[0]):
            if idx != -1 and idx < len(self.nodes):
                node_with_score = self.nodes[idx].copy()
                node_with_score['score'] = float(D[0][i])
                results.append(node_with_score)
        
        return results

def get_best_candidates(nodes, query, k=5):
    """Convenience function to get candidates in one go."""
    searcher = SemanticSearch()
    searcher.build_index(nodes)
    return searcher.search(query, k=k)
