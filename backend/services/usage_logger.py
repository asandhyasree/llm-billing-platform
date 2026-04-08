from datetime import datetime
from database import SessionLocal
from models.usage import UsageEvent
from services.budget_guard import deduct_credits


def log_usage_event(
    tenant_id: str,
    usage: dict,
    costs: dict,
    request_id: str | None = None,
) -> None:
    """
    Write a usage event to the ledger and deduct credits.
    Intended to be called as a FastAPI BackgroundTask so it never blocks the response.
    Opens its own DB session since it runs outside the request lifecycle.
    """
    db = SessionLocal()
    try:
        event = UsageEvent(
            tenant_id=tenant_id,
            model=usage["model"],
            provider=usage["provider"],
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
            input_cost_usd=costs["input_cost"],
            output_cost_usd=costs["output_cost"],
            total_cost_usd=costs["total_cost"],
            billed_cost_usd=costs["billed_cost"],
            request_id=request_id,
            ts=datetime.utcnow(),
        )
        db.add(event)
        db.commit()

        deduct_credits(tenant_id, costs["billed_cost"], db)
    finally:
        db.close()
