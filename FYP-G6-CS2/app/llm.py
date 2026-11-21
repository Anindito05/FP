"""Ollama Cloud Gemma client and resilient generation helpers."""
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
import asyncio, random
import httpx
from .config import Settings

class UpstreamLLMError(RuntimeError):
    def __init__(self,message:str,retryable:bool=True):
        super().__init__(message);self.retryable=retryable
@dataclass
class LLMResult:
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0
class BaseLLMClient(ABC):
    @abstractmethod
    async def generate(self, messages: list[dict], max_tokens: int, temperature: float) -> LLMResult: ...
    async def stream(self, messages: list[dict], max_tokens: int) -> AsyncIterator[str]:
        result=await self.generate(messages,max_tokens,.2); yield result.content
class OllamaClient(BaseLLMClient):
    def __init__(self, settings: Settings): self.settings=settings
    async def generate(self, messages: list[dict], max_tokens: int, temperature: float) -> LLMResult:
        headers={"Authorization":f"Bearer {self.settings.ollama_api_key}"} if self.settings.ollama_api_key and self.settings.ollama_host.startswith("https://") else {}
        async with httpx.AsyncClient(timeout=self.settings.llm_timeout_s) as client:
            payload={"model":self.settings.llm_model,"messages":messages,"stream":False,"options":{"temperature":temperature,"num_predict":max_tokens}}
            if messages and messages[-1].get("format"):
                payload["format"]=messages[-1]["format"]; payload["messages"]=messages[:-1]
            response=await client.post(self.settings.ollama_host.rstrip("/")+"/api/chat",headers=headers,json=payload)
        if response.status_code >= 400: raise UpstreamLLMError(f"Ollama returned HTTP {response.status_code} for model {self.settings.llm_model}",retryable=response.status_code not in (400,401))
        data=response.json(); return LLMResult(data.get("message",{}).get("content", ""),data.get("prompt_eval_count",0),data.get("eval_count",0))
    async def stream(self, messages: list[dict], max_tokens: int) -> AsyncIterator[str]:
        headers={"Authorization":f"Bearer {self.settings.ollama_api_key}"} if self.settings.ollama_api_key else {}
        async with httpx.AsyncClient(timeout=self.settings.llm_timeout_s) as client:
            async with client.stream("POST",self.settings.ollama_host.rstrip("/")+"/api/chat",headers=headers,json={"model":self.settings.llm_model,"messages":messages,"stream":True,"options":{"num_predict":max_tokens}}) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if line:
                        import json
                        content=json.loads(line).get("message",{}).get("content", "")
                        if content: yield content
class FakeLLMClient(BaseLLMClient):
    def __init__(self, content="I’m sorry this has been difficult. What feels most important to talk about?"): self.content=content; self.calls=0; self.prompts=[]
    async def generate(self,messages,max_tokens,temperature): self.calls+=1; self.prompts.append(messages); return LLMResult(self.content)

class FakeWebSearch:
    """Injectable search fake for deterministic phone-verification tests."""
    def __init__(self, results=None): self.results=results or []; self.queries=[]
    async def search(self, query: str, max_results: int = 5): self.queries.append(query); return self.results
    async def fetch(self, url: str): return next((r for r in self.results if r.get("url")==url), {})
def build_llm_client(settings: Settings) -> BaseLLMClient: return OllamaClient(settings)
async def with_resilience(call: Callable, retries: int, timeout_s: float) -> LLMResult:
    for attempt in range(retries+1):
        try: return await asyncio.wait_for(call(),timeout=timeout_s)
        except Exception as exc:
            if isinstance(exc,UpstreamLLMError) and not exc.retryable: raise
            status=getattr(getattr(exc,"response",None),"status_code",None)
            if status in (400,401): raise UpstreamLLMError("LLM request rejected; check model configuration and credentials") from exc
            if attempt >= retries: raise UpstreamLLMError("LLM is temporarily unavailable") from exc
            await asyncio.sleep(random.uniform(.1,.35)*(attempt+1))
