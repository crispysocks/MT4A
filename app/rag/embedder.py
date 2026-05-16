import os
from typing import List

class Embedder:
    def __init__(self, api_key: str = None, model: str = "text-embedding-v3"):
        self.api_key = api_key or os.getenv("EMBEDDINGS_API_KEY")
        self.model = model
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def embed(self, texts: List[str]) -> List[List[float]]:
        import httpx
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "input": {"texts": texts}
        }
        resp = httpx.post(
            f"{self.base_url}/embeddings",
            json=payload,
            headers=headers,
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        return [item["embedding"] for item in data["data"]]