import json

import numpy as np
from sentence_transformers import SentenceTransformer, SentenceTransformer

from chatbot_rag.config import CHUNKS_FILE, EMBEDDING_MODEL_NAME, EMBEDDINGS_FILE, TOP_K

class Retriever: 
    def __init__(self) -> None:
        if not EMBEDDINGS_FILE.exists() : 
            raise RuntimeError("Índice não encontrado. Rode: python -m chatbot_rag.ingest")

        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        self.embeddings = np.load(EMBEDDINGS_FILE)
        self.chunks = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))

    def search(self, query: str, k: int = TOP_K) -> list[dict]:
        q = self.model.encode(query, normalize_embeddings=True)
        scores = self.embeddings @ q

        top = np.argsort(scores)[::-1][:k]

        return [{**self.chunks[i], "score": float(scores[i])} for i in top]
