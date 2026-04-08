import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Index
from database import Base


class CreditLedger(Base):
    __tablename__ = "credit_ledger"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    amount_usd = Column(Float, nullable=False)   # positive = credit added, negative = usage deducted
    event_type = Column(String, nullable=False)  # topup / usage / adjustment / refund
    note = Column(String)
    ts = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_credits_tenant", "tenant_id"),
    )
