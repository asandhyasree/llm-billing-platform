"""
Usage query endpoints.

GET /usage/platform-summary       Platform-wide KPIs (MTD spend, active tenants, etc.)
GET /usage/platform-daily         Daily spend per tenant for the last 30 days
GET /tenants/{id}/usage           Raw usage events with optional filters
GET /tenants/{id}/usage/summary   Daily/monthly aggregated totals
GET /tenants/{id}/usage/by-model  Breakdown by model
GET /tenants/{id}/usage/by-day    Daily time series
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

from auth import require_admin
from database import get_db
from models.usage import UsageEvent
from models.tenant import Tenant

router = APIRouter()


@router.get("/platform-summary", dependencies=[Depends(require_admin)])
def platform_summary(db: Session = Depends(get_db)):
    start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
    today_start    = datetime.utcnow().replace(hour=0, minute=0, second=0)

    total_spend_mtd = db.query(func.sum(UsageEvent.billed_cost_usd)).filter(
        UsageEvent.ts >= start_of_month
    ).scalar() or 0.0

    active_tenants = db.query(func.count(distinct(UsageEvent.tenant_id))).filter(
        UsageEvent.ts >= start_of_month
    ).scalar() or 0

    calls_today = db.query(func.count(UsageEvent.id)).filter(
        UsageEvent.ts >= today_start
    ).scalar() or 0

    avg_cost = db.query(func.avg(UsageEvent.billed_cost_usd)).filter(
        UsageEvent.ts >= start_of_month
    ).scalar() or 0.0

    return {
        "total_spend_mtd":      round(total_spend_mtd, 4),
        "active_tenants":       active_tenants,
        "calls_today":          calls_today,
        "avg_cost_per_request": round(avg_cost, 6),
    }


@router.get("/platform-daily", dependencies=[Depends(require_admin)])
def platform_daily(db: Session = Depends(get_db)):
    since = datetime.utcnow() - timedelta(days=30)
    rows = (
        db.query(
            func.to_char(UsageEvent.ts, 'YYYY-MM-DD').label("date"),
            UsageEvent.tenant_id,
            func.sum(UsageEvent.billed_cost_usd).label("billed_cost_usd"),
        )
        .filter(UsageEvent.ts >= since)
        .group_by(func.to_char(UsageEvent.ts, 'YYYY-MM-DD'), UsageEvent.tenant_id)
        .all()
    )
    return [{"date": r.date, "tenant_id": r.tenant_id, "billed_cost_usd": round(r.billed_cost_usd, 6)} for r in rows]


@router.get("/{tenant_id}/usage", dependencies=[Depends(require_admin)])
def tenant_usage_events(
    tenant_id: str,
    start: datetime | None = None,
    end:   datetime | None = None,
    model: str | None = None,
    provider: str | None = None,
    limit: int = Query(500, le=2000),
    db: Session = Depends(get_db),
):
    q = db.query(UsageEvent).filter(UsageEvent.tenant_id == tenant_id)
    if start:
        q = q.filter(UsageEvent.ts >= start)
    if end:
        q = q.filter(UsageEvent.ts <= end)
    if model:
        q = q.filter(UsageEvent.model == model)
    if provider:
        q = q.filter(UsageEvent.provider == provider)
    return q.order_by(UsageEvent.ts.desc()).limit(limit).all()


@router.get("/{tenant_id}/usage/by-model", dependencies=[Depends(require_admin)])
def usage_by_model(tenant_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(
            UsageEvent.model,
            func.sum(UsageEvent.input_tokens).label("input_tokens"),
            func.sum(UsageEvent.output_tokens).label("output_tokens"),
            func.sum(UsageEvent.billed_cost_usd).label("billed_cost_usd"),
            func.count(UsageEvent.id).label("requests"),
        )
        .filter(UsageEvent.tenant_id == tenant_id)
        .group_by(UsageEvent.model)
        .all()
    )
    return [dict(r._mapping) for r in rows]


@router.get("/{tenant_id}/usage/by-day", dependencies=[Depends(require_admin)])
def usage_by_day(tenant_id: str, days: int = 30, db: Session = Depends(get_db)):
    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(
            func.to_char(UsageEvent.ts, 'YYYY-MM-DD').label("date"),
            func.sum(UsageEvent.total_cost_usd).label("total_cost_usd"),
            func.sum(UsageEvent.billed_cost_usd).label("billed_cost_usd"),
            func.sum(UsageEvent.input_tokens).label("input_tokens"),
            func.sum(UsageEvent.output_tokens).label("output_tokens"),
            func.count(UsageEvent.id).label("requests"),
        )
        .filter(UsageEvent.tenant_id == tenant_id, UsageEvent.ts >= since)
        .group_by(func.to_char(UsageEvent.ts, 'YYYY-MM-DD'))
        .order_by("date")
        .all()
    )
    return [dict(r._mapping) for r in rows]
