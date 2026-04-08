"""
Tenant management endpoints.

GET  /tenants             List all tenants
POST /tenants             Create a tenant and generate an API key
GET  /tenants/{id}        Get tenant details
PUT  /tenants/{id}        Update tier or markup
"""
import hashlib
import secrets
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import require_admin
from database import get_db
from models.tenant import Tenant, APIKey

router = APIRouter()


class TenantCreate(BaseModel):
    name: str
    email: str | None = None
    tier: str = "basic"
    markup_pct: float = 20.0


class TenantUpdate(BaseModel):
    tier: str | None = None
    markup_pct: float | None = None


@router.get("", dependencies=[Depends(require_admin)])
def list_tenants(db: Session = Depends(get_db)):
    return db.query(Tenant).all()


@router.post("", dependencies=[Depends(require_admin)], status_code=201)
def create_tenant(payload: TenantCreate, db: Session = Depends(get_db)):
    tenant = Tenant(
        name=payload.name,
        email=payload.email,
        tier=payload.tier,
        markup_pct=payload.markup_pct,
    )
    db.add(tenant)
    db.flush()

    # Generate a random API key and store only its hash
    raw_key  = f"llmbill-{secrets.token_hex(24)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    api_key  = APIKey(key_hash=key_hash, tenant_id=tenant.id, label="default", raw_key=raw_key)
    db.add(api_key)
    db.commit()
    db.refresh(tenant)

    return {
        "tenant": tenant,
        "api_key": raw_key,
    }


@router.get("/{tenant_id}", dependencies=[Depends(require_admin)])
def get_tenant(tenant_id: str, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.get("/{tenant_id}/keys", dependencies=[Depends(require_admin)])
def get_tenant_keys(tenant_id: str, db: Session = Depends(get_db)):
    keys = db.query(APIKey).filter(APIKey.tenant_id == tenant_id).all()
    return [
        {
            "label": k.label,
            "api_key": k.raw_key,
            "is_active": k.is_active,
            "created_at": k.created_at,
        }
        for k in keys
    ]


@router.put("/{tenant_id}", dependencies=[Depends(require_admin)])
def update_tenant(tenant_id: str, payload: TenantUpdate, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if payload.tier is not None:
        tenant.tier = payload.tier
    if payload.markup_pct is not None:
        tenant.markup_pct = payload.markup_pct
    db.commit()
    db.refresh(tenant)
    return tenant
