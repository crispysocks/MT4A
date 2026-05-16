import os
from pathlib import Path
from typing import List, Optional

WORKDIR = Path.cwd()

class ChromaStore:
    def __init__(self, persist_dir: str = None):
        self.persist_dir = persist_dir or str(WORKDIR / ".chroma")
        self._client = None
        self._collection = None

    @property
    def client(self):
        if self._client is None:
            import chromadb
            self._client = chromadb.PersistentClient(path=self.persist_dir)
        return self._client

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.client.get_or_create_collection("knowledge")
        return self._collection

    def add_documents(self, texts: List[str], ids: List[str], metadatas: List[dict] = None):
        from app.rag.embedder import Embedder
        embedder = Embedder()
        embeddings = embedder.embed(texts)
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas or [{}] * len(texts)
        )

    def query(self, query_text: str, top_k: int = 5, where: dict = None) -> List[dict]:
        from app.rag.embedder import Embedder
        embedder = Embedder()
        query_embedding = embedder.embed([query_text])[0]
        kwargs = dict(query_embeddings=[query_embedding], n_results=top_k)
        if where:
            kwargs["where"] = where
        results = self.collection.query(**kwargs)
        if not results["documents"][0]:
            return []
        return [
            {"content": doc, "distance": dist, "metadata": meta}
            for doc, dist, meta in zip(
                results["documents"][0],
                results["distances"][0],
                results["metadatas"][0]
            )
        ]