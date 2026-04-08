import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://billing:billing@localhost:5432/billing")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "change-me")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# USD per 1 million tokens
MODEL_RATES: dict[str, dict[str, float]] = {
    "gpt-4o":             {"input": 2.50,   "output": 10.00},
    "gpt-4o-mini":        {"input": 0.15,   "output": 0.60},
    "o1":                 {"input": 15.00,  "output": 60.00},
    "o1-mini":            {"input": 3.00,   "output": 12.00},
    "claude-opus-4-6":    {"input": 15.00,  "output": 75.00},
    "claude-sonnet-4-6":  {"input": 3.00,   "output": 15.00},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
    "gemini-2.0-flash":   {"input": 0.10,   "output": 0.40},
    "gemini-2.5-flash":   {"input": 0.15,   "output": 0.60},
    "gemini-2.5-pro":     {"input": 1.25,   "output": 10.00},
}

PROVIDER_URLS: dict[str, str] = {
    "openai":    "https://api.openai.com/v1/chat/completions",
    "anthropic": "https://api.anthropic.com/v1/messages",
    "gemini":    "https://generativelanguage.googleapis.com/v1beta/models",
}

PROVIDER_BY_MODEL_PREFIX: dict[str, str] = {
    "gpt":     "openai",
    "o1":      "openai",
    "claude":  "anthropic",
    "gemini":  "gemini",
}


def detect_provider(model: str) -> str:
    for prefix, provider in PROVIDER_BY_MODEL_PREFIX.items():
        if model.startswith(prefix):
            return provider
    return "openai"
