from sqlalchemy.orm import Session
from sqlalchemy import func
from models.billing import CreditLedger


def get_credit_balance(tenant_id: str, db: Session) -> float:
    """Return the current credit balance for a tenant (sum of all ledger entries)."""
    result = (
        db.query(func.sum(CreditLedger.amount_usd))
        .filter(CreditLedger.tenant_id == tenant_id)
        .scalar()
    )
    return round(result or 0.0, 8)


def deduct_credits(tenant_id: str, amount_usd: float, db: Session) -> None:
    """Write a negative ledger entry to deduct usage cost from the tenant's balance."""
    entry = CreditLedger(
        tenant_id=tenant_id,
        amount_usd=-abs(amount_usd),
        event_type="usage",
        note="Deducted for LLM API usage",
    )
    db.add(entry)
    db.commit()
