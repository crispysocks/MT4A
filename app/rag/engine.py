import os
import shutil
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
load_dotenv(override=True)

import dashscope

_api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("EMBEDDINGS_API_KEY")
if _api_key and not os.getenv("DASHSCOPE_API_KEY"):
    os.environ["DASHSCOPE_API_KEY"] = _api_key
    dashscope.api_key = _api_key

from llama_index.core import (
    Settings,
    StorageContext,
    VectorStoreIndex,
    SimpleDirectoryReader,
    load_index_from_storage,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.dashscope import (
    DashScopeEmbedding,
    DashScopeTextEmbeddingModels,
    DashScopeTextEmbeddingType,
)
from llama_index.postprocessor.dashscope_rerank import DashScopeRerank

WORKDIR = Path.cwd()

ROLE_KB_MAP = {
    "student": ["public", "business", "policy"],
    "employee": ["public", "internal", "business", "policy"],
    "guest": ["public", "business", "policy"],
}


class RAGEngine:
    def __init__(
        self,
        persist_dir: str = None,
        chunk_size: int = 1024,
        chunk_overlap: int = 50,
    ):
        self.persist_dir = persist_dir or str(WORKDIR / "VectorStore")
        self._embed_model = DashScopeEmbedding(
            model_name=DashScopeTextEmbeddingModels.TEXT_EMBEDDING_V2,
            text_type=DashScopeTextEmbeddingType.TEXT_TYPE_DOCUMENT,
        )
        Settings.embed_model = self._embed_model
        self._splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def create_kb(self, name: str, source_paths: List[str]) -> None:
        """Create a knowledge base from source directories/files."""
        documents = []
        for p in source_paths:
            path = Path(p)
            if not path.exists():
                print(f"[RAG] Source not found: {p}")
                continue
            if path.is_dir():
                documents.extend(SimpleDirectoryReader(str(path)).load_data())
            else:
                documents.extend(
                    SimpleDirectoryReader(input_files=[str(path)]).load_data()
                )
        if not documents:
            print(f"[RAG] No documents found for KB '{name}'")
            return
        nodes = self._splitter.get_nodes_from_documents(documents)
        index = VectorStoreIndex(nodes)
        db_path = os.path.join(self.persist_dir, name)
        os.makedirs(db_path, exist_ok=True)
        index.storage_context.persist(db_path)
        print(f"[RAG] KB '{name}' created with {len(nodes)} nodes from {len(documents)} docs")

    def delete_kb(self, name: str) -> None:
        path = os.path.join(self.persist_dir, name)
        if os.path.exists(path):
            shutil.rmtree(path)

    def list_kbs(self) -> List[str]:
        if not os.path.exists(self.persist_dir):
            return []
        return [
            d for d in os.listdir(self.persist_dir)
            if os.path.isdir(os.path.join(self.persist_dir, d))
        ]

    def get_kbs_for_role(self, role: str) -> List[str]:
        return ROLE_KB_MAP.get(role, ROLE_KB_MAP.get("guest", []))

    def query(
        self,
        query_text: str,
        kb_names: List[str],
        top_k: int = 5,
        similarity_threshold: float = 0.2,
    ) -> List[dict]:
        """Two-stage retrieval across KBs. Returns [{"content", "score", "metadata"}]."""
        all_nodes = []
        for kb_name in kb_names:
            kb_path = os.path.join(self.persist_dir, kb_name)
            if not os.path.exists(kb_path):
                continue
            storage_context = StorageContext.from_defaults(persist_dir=kb_path)
            index = load_index_from_storage(storage_context)
            retriever = index.as_retriever(similarity_top_k=20)
            nodes = retriever.retrieve(query_text)
            all_nodes.extend(nodes)

        if not all_nodes:
            return []

        reranker = DashScopeRerank(top_n=top_k, return_documents=True)
        try:
            results = reranker.postprocess_nodes(all_nodes, query_str=query_text)
        except Exception:
            all_nodes.sort(key=lambda n: n.score or 0, reverse=True)
            results = all_nodes[:top_k]

        formatted = []
        for r in results:
            if r.score and r.score >= similarity_threshold:
                formatted.append({
                    "content": r.text,
                    "score": round(r.score, 4),
                    "metadata": r.metadata,
                })
        return formatted
