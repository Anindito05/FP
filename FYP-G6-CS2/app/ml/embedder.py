"""Local, deterministic fallback embedder; the interface also supports sentence-transformers."""
import hashlib
import re
import math

class HashingEmbedder:
    """Small feature hashing embedder for offline/synthetic demos, not semantic evidence."""
    def __init__(self, dimension: int = 384): self.dimension = dimension
    def encode(self, texts):
        vectors = [[0.0]*self.dimension for _ in texts]
        for row, text in enumerate(texts):
            words = re.findall(r"[a-z]+", text.lower())
            features = words + [" ".join(words[i:i+2]) for i in range(max(0, len(words)-1))]
            for feature in features:
                digest = hashlib.blake2b(feature.encode(), digest_size=8).digest()
                index = int.from_bytes(digest[:4], "little") % self.dimension
                vectors[row][index] += 1 if digest[4] & 1 else -1
            norm = math.sqrt(sum(v*v for v in vectors[row]))
            if norm: vectors[row]=[v/norm for v in vectors[row]]
        return vectors

class SentenceTransformerEmbedder:
    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
    def encode(self, texts):
        return self.model.encode(texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False).tolist()

def load_embedder(model_name: str):
    if model_name == "hashing-n-gram-v1": return HashingEmbedder()
    return SentenceTransformerEmbedder(model_name)
