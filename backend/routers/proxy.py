"""
Proxy gateway — the core of the platform.

All client LLM requests come here. The proxy:
1. Authenticates the client via API key
2. Checks credit balance (hard block on zero)
3. Forwards the request to the correct LLM provider
4. Extracts token usage from the response
5. Calculates cost (with tenant markup)
6. Logs the usage event and deducts credits asynchronously
"""
import os
import httpx
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, Depends

from auth import authenticate_tenant
from config import PROVIDER_URLS, OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY, detect_provider
from database import get_db
from models.tenant import Tenant
from services.token_counter import extract_usage
from services.cost_engine import calculate_cost
from services.budget_guard import get_credit_balance
from services.usage_logger import log_usage_event
from sqlalchemy.orm import Session

router = APIRouter()

_PROVIDER_KEYS = {
    "openai":    OPENAI_API_KEY,
    "anthropic": ANTHROPIC_API_KEY,
    "gemini":    GEMINI_API_KEY,
}

_PROVIDER_HEADERS = {
    "openai":    lambda key: {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    "anthropic": lambda key: {"x-api-key": key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
    "gemini":    lambda key: {"Content-Type": "application/json"},
}


@router.post("/v1/chat/completions")
async def proxy_completion(
    request: Request,
    background_tasks: BackgroundTasks,
    tenant: Tenant = Depends(authenticate_tenant),
    db: Session = Depends(get_db),
):
    body = await request.json()
    model = body.get("model", "gpt-4o-mini")
    provider = detect_provider(model)

    # 1. Budget check — synchronous, must happen before forwarding
    balance = get_credit_balance(tenant.id, db)
    if balance <= 0:
        raise HTTPException(
            status_code=402,
            detail={"error": "Insufficient credits", "balance_usd": balance},
        )

    # 2. Forward to the appropriate LLM provider
    api_key = _PROVIDER_KEYS.get(provider, "")
    headers = _PROVIDER_HEADERS[provider](api_key)
    url = PROVIDER_URLS[provider]

    # Transform request body per provider
    if provider == "gemini":
        url = f"{url}/{model}:generateContent?key={api_key}"
        # Convert OpenAI messages format to Gemini contents format
        gemini_contents = []
        for msg in body.get("messages", []):
            role = "model" if msg["role"] == "assistant" else "user"
            gemini_contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}],
            })
        provider_body = {"contents": gemini_contents}
    elif provider == "anthropic":
        # Anthropic expects model, messages, and max_tokens
        messages = body.get("messages", [])
        system_msg = None
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                chat_messages.append(msg)
        provider_body = {
            "model": model,
            "messages": chat_messages,
            "max_tokens": body.get("max_tokens", 1024),
        }
        if system_msg:
            provider_body["system"] = system_msg
    else:
        # OpenAI — pass through as-is
        provider_body = body

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(url, json=provider_body, headers=headers)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        response_data = resp.json()

    # 3. Normalize token counts across providers
    usage = extract_usage(response_data, model, provider)

    # 4. Calculate cost with tenant's markup
    costs = calculate_cost(usage, markup_pct=tenant.markup_pct)

    # 5. Async: log event + deduct credits (does not block the response)
    request_id = response_data.get("id")
    background_tasks.add_task(log_usage_event, tenant.id, usage, costs, request_id)

    # 6. Normalize response to OpenAI format so clients get a consistent shape
    if provider == "gemini":
        text = response_data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        return {
            "id": request_id,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": text}}],
            "model": model,
            "usage": {
                "prompt_tokens": usage["input_tokens"],
                "completion_tokens": usage["output_tokens"],
                "total_tokens": usage["input_tokens"] + usage["output_tokens"],
            },
        }
    elif provider == "anthropic":
        text = ""
        for block in response_data.get("content", []):
            if block.get("type") == "text":
                text += block.get("text", "")
        return {
            "id": response_data.get("id"),
            "choices": [{"index": 0, "message": {"role": "assistant", "content": text}}],
            "model": model,
            "usage": {
                "prompt_tokens": usage["input_tokens"],
                "completion_tokens": usage["output_tokens"],
                "total_tokens": usage["input_tokens"] + usage["output_tokens"],
            },
        }
    else:
        return response_data
