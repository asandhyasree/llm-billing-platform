import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Index
from database import Base


class UsageEvent(Base):
    __tablename__ = "usage_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    model = Column(String, nullable=False)          # e.g. "gpt-4o", "claude-sonnet-4-6"
    provider = Column(String, nullable=False)        # openai / anthropic / gemini
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    input_cost_usd = Column(Float, nullable=False)   # at provider rate
    output_cost_usd = Column(Float, nullable=False)
    total_cost_usd = Column(Float, nullable=False)   # input + output at provider rate
    billed_cost_usd = Column(Float, nullable=False)  # after markup
    request_id = Column(String)                      # provider's request ID for reconciliation
    ts = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_usage_tenant_ts", "tenant_id", "ts"),
        Index("idx_usage_model", "model"),
    )
