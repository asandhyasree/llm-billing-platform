"""
Integration tests for the proxy endpoint.
Uses FastAPI's TestClient — no separate server needed.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

# Set a test DB before importing the app
os.environ.setdefault("DATABASE_URL", "postgresql://billing:billing@localhost:5432/billing_test")
os.environ.setdefault("ADMIN_SECRET_KEY", "test-admin")

from main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_proxy_requires_api_key():
    resp = client.post("/v1/chat/completions", json={"model": "gpt-4o-mini", "messages": []})
    assert resp.status_code == 422  # missing X-API-Key header


def test_proxy_rejects_invalid_key():
    resp = client.post(
        "/v1/chat/completions",
        json={"model": "gpt-4o-mini", "messages": []},
        headers={"X-API-Key": "invalid-key"},
    )
    assert resp.status_code == 401
