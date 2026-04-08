import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Float, DateTime, ForeignKey
from database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String)
    tier = Column(String, default="basic")        # basic / pro / enterprise
    markup_pct = Column(Float, default=20.0)       # your margin applied at billing
    created_at = Column(DateTime, default=datetime.utcnow)


class APIKey(Base):
    __tablename__ = "api_keys"

    key_hash = Column(String, primary_key=True)    # SHA-256 of the actual key
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    label = Column(String)                         # human-readable name
    raw_key = Column(String)                       # plaintext key (admin-only access)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
