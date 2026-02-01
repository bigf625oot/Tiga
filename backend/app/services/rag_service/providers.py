from typing import Protocol, List, Any, Dict, Optional

class Embedder(Protocol):
    def embed(self, texts: List[str]) -> List[List[float]]: ...

class LLMClient(Protocol):
    async def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> str: ...

class VectorStore(Protocol):
    def index(self, texts: List[str], ids: Optional[List[str]] = None): ...
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]: ...

class OpenAICompatLLM:
    def __init__(self, api_key: str, base_url: Optional[str], model: str):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
    async def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
        m = model or self.model
        resp = await self.client.chat.completions.create(model=m, messages=messages, temperature=0)
        return resp.choices[0].message.content if (resp and resp.choices) else ""

class LightRAGVectorStore:
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        from app.services.knowledge_base import kb_service
        refs, _ = kb_service.search(query, top_k=top_k)
        return refs
    def index(self, texts: List[str], ids: Optional[List[str]] = None):
        from app.services.lightrag_service import lightrag_service
        for t in texts:
            lightrag_service.insert_text(t)

class OpenAIEmbedder:
    def __init__(self, api_key: str, base_url: Optional[str], model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
    def embed(self, texts: List[str]) -> List[List[float]]:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, base_url=self.base_url) if self.base_url else OpenAI(api_key=self.api_key)
        resp = client.embeddings.create(model=self.model, input=texts)
        return [d.embedding for d in resp.data]
