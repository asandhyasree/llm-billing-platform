"""
Billing endpoints.

GET  /tenants/{id}/credits            Current balance + ledger history
POST /tenants/{id}/credits/topup      Add credits
GET  /tenants/{id}/invoice/preview    JSON invoice for a billing period
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from auth import require_admin
from database import get_db
from models.billing import CreditLedger
from models.usage import UsageEvent

router = APIRouter()


class TopUpRequest(BaseModel):
    amount_usd: float
    note: str | None = None


@router.get("/{tenant_id}/credits", dependencies=[Depends(require_admin)])
def get_credits(tenant_id: str, db: Session = Depends(get_db)):
    balance = db.query(func.sum(CreditLedger.amount_usd)).filter(
        CreditLedger.tenant_id == tenant_id
    ).scalar() or 0.0

    ledger = (
        db.query(CreditLedger)
        .filter(CreditLedger.tenant_id == tenant_id)
        .order_by(CreditLedger.ts.desc())
        .limit(100)
        .all()
    )
    return {"balance_usd": round(balance, 6), "ledger": ledger}


@router.post("/{tenant_id}/credits/topup", dependencies=[Depends(require_admin)], status_code=201)
def topup_credits(tenant_id: str, payload: TopUpRequest, db: Session = Depends(get_db)):
    if payload.amount_usd <= 0:
        raise HTTPException(status_code=422, detail="amount_usd must be positive")
    entry = CreditLedger(
        tenant_id=tenant_id,
        amount_usd=payload.amount_usd,
        event_type="topup",
        note=payload.note or "Manual top-up",
    )
    db.add(entry)
    db.commit()

    new_balance = db.query(func.sum(CreditLedger.amount_usd)).filter(
        CreditLedger.tenant_id == tenant_id
    ).scalar() or 0.0

    return {"status": "ok", "new_balance_usd": round(new_balance, 6)}


@router.get("/{tenant_id}/invoice/preview", dependencies=[Depends(require_admin)])
def invoice_preview(
    tenant_id: str,
    year:  int = datetime.utcnow().year,
    month: int = datetime.utcnow().month,
    db: Session = Depends(get_db),
):
    start = datetime(year, month, 1)
    end   = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)

    events = (
        db.query(UsageEvent)
        .filter(UsageEvent.tenant_id == tenant_id, UsageEvent.ts >= start, UsageEvent.ts < end)
        .all()
    )

    by_model: dict[str, dict] = {}
    for e in events:
        if e.model not in by_model:
            by_model[e.model] = {"model": e.model, "requests": 0, "input_tokens": 0, "output_tokens": 0, "billed_cost_usd": 0.0}
        by_model[e.model]["requests"]       += 1
        by_model[e.model]["input_tokens"]   += e.input_tokens
        by_model[e.model]["output_tokens"]  += e.output_tokens
        by_model[e.model]["billed_cost_usd"] = round(by_model[e.model]["billed_cost_usd"] + e.billed_cost_usd, 8)

    total = sum(v["billed_cost_usd"] for v in by_model.values())
    return {
        "tenant_id":    tenant_id,
        "period":       f"{year}-{month:02d}",
        "total_billed": round(total, 6),
        "line_items":   list(by_model.values()),
    }
