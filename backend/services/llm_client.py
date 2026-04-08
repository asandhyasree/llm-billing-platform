"""
Thin LLM client that calls Gemini for internal AI features (NL query, RAG advisor).
"""
import httpx
from config import GEMINI_API_KEY


async def complete(prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, json=body, headers={"Content-Type": "application/json"})
        resp.raise_for_status()
        data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]
