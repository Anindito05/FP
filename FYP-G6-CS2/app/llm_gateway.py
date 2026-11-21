"""Small Ollama-compatible HTTP gateway for a local Ollama daemon.

Run with: uvicorn app.llm_gateway:app --host 127.0.0.1 --port 8001
The gateway keeps the backend's upstream URL stable; model execution remains
owned by the Ollama daemon on OLLAMA_LOCAL_URL.
"""
import os
from fastapi import FastAPI, HTTPException, Request
import httpx

LOCAL_OLLAMA_URL = os.getenv("OLLAMA_LOCAL_URL", "http://127.0.0.1:11434").rstrip("/")
GATEWAY_TIMEOUT = float(os.getenv("OLLAMA_GATEWAY_TIMEOUT_S", "180"))

app = FastAPI(title="Local Ollama Gateway", version="1.0.0")


@app.get("/health")
async def health():
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{LOCAL_OLLAMA_URL}/api/tags")
            response.raise_for_status()
        return {"status": "ok", "ollama": "reachable"}
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Local Ollama is unavailable") from exc


@app.post("/api/chat")
async def chat(request: Request):
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Expected a JSON chat request") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("messages"), list):
        raise HTTPException(status_code=422, detail="A messages array is required")
    payload["stream"] = False
    try:
        async with httpx.AsyncClient(timeout=GATEWAY_TIMEOUT) as client:
            response = await client.post(f"{LOCAL_OLLAMA_URL}/api/chat", json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="Local Ollama timed out") from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail="Local Ollama rejected the request") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Could not reach local Ollama") from exc
