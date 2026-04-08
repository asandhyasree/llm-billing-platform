import hashlib
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.tenant import APIKey, Tenant
from config import ADMIN_SECRET_KEY


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def authenticate_tenant(
    x_api_key: str = Header(..., description="Client API key"),
    db: Session = Depends(get_db),
) -> Tenant:
    key_hash = _hash_key(x_api_key)
    api_key = (
        db.query(APIKey)
        .filter(APIKey.key_hash == key_hash, APIKey.is_active == True)
        .first()
    )
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    tenant = db.query(Tenant).filter(Tenant.id == api_key.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=401, detail="Tenant not found")
    return tenant


def require_admin(x_admin_key: str = Header(..., description="Admin secret key")) -> None:
    if x_admin_key != ADMIN_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")
