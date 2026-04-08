"""
AI feature endpoints.

GET  /ai/anomalies/{tenant_id}    Flagged anomaly days with severity
GET  /ai/forecast/{tenant_id}     Month-end spend projection
POST /ai/explain                  RAG advisor: explain an anomaly
POST /ai/query                    Natural language → SQL → answer
GET  /ai/insights/{tenant_id}     Combined: anomalies + forecast + top recommendation
GET  /ai/platform-anomalies       Recent anomalies across all tenants (for dashboard banner)
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from auth import require_admin
from database import get_db
from models.usage import UsageEvent
from services.anomaly import detect_anomalies
from services.forecaster import forecast_month_end
from services.nl_query import nl_to_sql_to_answer

router = APIRouter()


def _get_daily_costs(tenant_id: str, days: int, db: Session) -> list[dict]:
    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(
            func.to_char(UsageEvent.ts, 'YYYY-MM-DD').label("date"),
            UsageEvent.model,
            func.sum(UsageEvent.total_cost_usd).label("total_cost"),
            func.sum(UsageEvent.input_tokens).label("input_tokens"),
            func.sum(UsageEvent.output_tokens).label("output_tokens"),
        )
        .filter(UsageEvent.tenant_id == tenant_id, UsageEvent.ts >= since)
        .group_by(func.to_char(UsageEvent.ts, 'YYYY-MM-DD'), UsageEvent.model)
        .order_by("date")
        .all()
    )
    return [dict(r._mapping) for r in rows]


@router.get("/anomalies/{tenant_id}", dependencies=[Depends(require_admin)])
def get_anomalies(tenant_id: str, days: int = 60, db: Session = Depends(get_db)):
    daily = _get_daily_costs(tenant_id, days, db)
    return detect_anomalies(daily)


@router.get("/forecast/{tenant_id}", dependencies=[Depends(require_admin)])
def get_forecast(tenant_id: str, db: Session = Depends(get_db)):
    since = datetime.utcnow() - timedelta(days=14)
    rows = (
        db.query(
            func.to_char(UsageEvent.ts, 'YYYY-MM-DD').label("date"),
            func.sum(UsageEvent.billed_cost_usd).label("cost"),
        )
        .filter(UsageEvent.tenant_id == tenant_id, UsageEvent.ts >= since)
        .group_by(func.to_char(UsageEvent.ts, 'YYYY-MM-DD'))
        .order_by("date")
        .all()
    )
    daily_costs = [r.cost for r in rows]
    if not daily_costs:
        return {"error": "Not enough data to forecast"}
    return forecast_month_end(daily_costs)


class ExplainRequest(BaseModel):
    anomaly: dict


class QueryRequest(BaseModel):
    question: str
    tenant_id: str


@router.post("/explain", dependencies=[Depends(require_admin)])
async def explain_anomaly(payload: ExplainRequest):
    """
    Generate a plain English explanation for an anomaly using the RAG advisor.
    Requires an LLM client to be wired in (see rag_advisor.py).
    """
    # Stub: wire up your preferred LLM client in production
    return {"explanation": "RAG advisor not yet configured — wire up an LLM client in services/rag_advisor.py"}


@router.post("/query", dependencies=[Depends(require_admin)])
async def nl_query(payload: QueryRequest, db: Session = Depends(get_db)):
    """Convert a natural language question to SQL and return the answer."""
    return await nl_to_sql_to_answer(payload.question, payload.tenant_id, db)


@router.get("/insights/{tenant_id}", dependencies=[Depends(require_admin)])
def get_insights(tenant_id: str, db: Session = Depends(get_db)):
    daily = _get_daily_costs(tenant_id, 60, db)
    anomalies = detect_anomalies(daily)

    since = datetime.utcnow() - timedelta(days=14)
    rows = (
        db.query(
            func.to_char(UsageEvent.ts, 'YYYY-MM-DD').label("date"),
            func.sum(UsageEvent.billed_cost_usd).label("cost"),
        )
        .filter(UsageEvent.tenant_id == tenant_id, UsageEvent.ts >= since)
        .group_by(func.to_char(UsageEvent.ts, 'YYYY-MM-DD'))
        .order_by("date")
        .all()
    )
    forecast = forecast_month_end([r.cost for r in rows]) if rows else {}

    return {
        "anomalies": anomalies[:3],
        "forecast":  forecast,
    }


@router.get("/platform-anomalies", dependencies=[Depends(require_admin)])
def platform_anomalies(db: Session = Depends(get_db)):
    """Return anomalies detected in the last 24 hours across all tenants."""
    since = datetime.utcnow() - timedelta(hours=24)
    tenant_ids = [
        r[0] for r in db.query(UsageEvent.tenant_id).filter(UsageEvent.ts >= since).distinct().all()
    ]
    all_anomalies = []
    for tid in tenant_ids:
        daily = _get_daily_costs(tid, 60, db)
        for a in detect_anomalies(daily):
            if a["date"] >= (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d"):
                all_anomalies.append({**a, "tenant_id": tid})
    return all_anomalies
