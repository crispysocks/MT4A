import os
from typing import List

from dotenv import load_dotenv
load_dotenv(override=True)

class Embedder:
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key or os.getenv("EMBEDDINGS_API_KEY")
        self.base_url = base_url or os.getenv("EMBEDDINGS_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.model = model or os.getenv("EMBEDDINGS_MODEL", "text-embedding-v3")

    def embed(self, texts: List[str]) -> List[List[float]]:
        import httpx
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        results = []
        batch_size = 10
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            payload = {
                "model": self.model,
                "input": batch[0] if len(batch) == 1 else batch
            }
            resp = httpx.post(
                f"{self.base_url}/embeddings",
                json=payload,
                headers=headers,
                timeout=60
            )
            resp.raise_for_status()
            data = resp.json()
            results.extend([item["embedding"] for item in data["data"]])
        return results