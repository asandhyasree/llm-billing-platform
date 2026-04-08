import os
import httpx

BASE_URL  = os.getenv("FASTAPI_URL", "http://localhost:8000")
ADMIN_KEY = os.getenv("ADMIN_SECRET_KEY", "")
_HEADERS  = {"X-Admin-Key": ADMIN_KEY}


def api_get(path: str, params: dict | None = None) -> dict | list:
    r = httpx.get(f"{BASE_URL}{path}", params=params or {}, headers=_HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def api_post(path: str, body: dict | None = None) -> dict | list:
    r = httpx.post(f"{BASE_URL}{path}", json=body or {}, headers=_HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()
