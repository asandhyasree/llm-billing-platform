from fastapi import FastAPI
from database import init_db
from routers import proxy, tenants, usage, billing, ai

app = FastAPI(
    title="LLM Billing & Observability Platform",
    version="1.0.0",
    description="Metered billing proxy for LLM API usage across OpenAI, Anthropic, and Gemini.",
)


@app.on_event("startup")
async def startup() -> None:
    init_db()


app.include_router(proxy.router, tags=["proxy"])
app.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
app.include_router(usage.router, prefix="/usage", tags=["usage"])
app.include_router(billing.router, prefix="/billing", tags=["billing"])
app.include_router(ai.router, prefix="/ai", tags=["ai"])


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok"}
