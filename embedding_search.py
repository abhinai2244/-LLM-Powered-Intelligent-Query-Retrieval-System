from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
import os
import numpy as np

class EmbeddingSearch:
    def __init__(self, pinecone_api_key: str, pinecone_env: str, index_name: str = "policy-index"):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        try:
            self.pc = Pinecone(api_key=pinecone_api_key)
        except Exception as e:
            raise ValueError(f"Failed to initialize Pinecone client: {str(e)}") from e
        self.index_name = index_name
        self._ensure_index(pinecone_env)

    def _ensure_index(self, pinecone_env: str):
        """Ensure the Pinecone index exists, create if it doesn't."""
        try:
            if self.index_name not in self.pc.list_indexes().names():
                self.pc.create_index(
                    name=self.index_name,
                    dimension=384,
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region=pinecone_env
                    )
                )
            self.index = self.pc.Index(self.index_name)
        except Exception as e:
            raise ValueError(f"Failed to create or access Pinecone index: {str(e)}") from e

    def generate_embeddings(self, texts: list) -> list:
        """Generate embeddings for a list of texts."""
        return self.model.encode(texts, show_progress_bar=False)

    def store_embeddings(self, chunks: list, doc_id: str):
        """Store embeddings in Pinecone."""
        embeddings = self.generate_embeddings(chunks)
        vectors = [(f"{doc_id}_{i}", emb.tolist()) for i, emb in enumerate(embeddings)]
        self.index.upsert(vectors=vectors)

    def search(self, query: str, top_k: int = 5) -> list:
        """Search for relevant chunks using query embedding."""
        query_embedding = self.generate_embeddings([query])[0]
        results = self.index.query(vector=query_embedding.tolist(), top_k=top_k)
        return [{"id": match["id"], "score": match["score"]} for match in results["matches"]]