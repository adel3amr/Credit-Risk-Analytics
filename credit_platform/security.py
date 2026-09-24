"""High-entropy, expiring, revocable credentials. No role is accepted from clients."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, update
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from . import schema as s, audit
from .common import uid, now

PERMISSIONS = {
    "analyst": {"read", "ingest", "run", "override"},
    "manager": {"read", "ingest", "run", "override", "approve", "finding"},
    "validator": {"read", "validate", "finding"},
    "audit": {"read", "audit"},
    "admin": {"read", "audit", "finding"},
}
bearer = HTTPBearer(auto_error=False)


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def issue(db, name, role, days=30):
    if role not in PERMISSIONS or not 1 <= days <= 90:
        raise ValueError("Invalid role or expiry")
    token = secrets.token_urlsafe(48)
    entry = {
        "id": uid(),
        "name": name,
        "role": role,
        "token_hash": token_hash(token),
        "active": 1,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=days)).isoformat(),
        "created_at": now(),
    }
    with db.begin() as conn:
        conn.execute(s.principals.insert().values(**entry))
        audit.append(
            conn,
            "local-operator",
            "CREDENTIAL_ISSUED",
            entry["id"],
            {"role": role, "expires_at": entry["expires_at"]},
        )
    return token


def revoke(db, name):
    with db.begin() as conn:
        result = conn.execute(
            update(s.principals).where(s.principals.c.name == name).values(active=0)
        )
        if not result.rowcount:
            raise ValueError("Principal not found")
        audit.append(conn, "local-operator", "CREDENTIAL_REVOKED", name, {})


def principal(
    request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer)
):
    if credentials is None or len(credentials.credentials) > 200:
        raise HTTPException(
            401, "Authentication required", headers={"WWW-Authenticate": "Bearer"}
        )
    with request.app.state.db.connect() as conn:
        row = (
            conn.execute(
                select(s.principals).where(
                    s.principals.c.token_hash == token_hash(credentials.credentials)
                )
            )
            .mappings()
            .first()
        )
    if (
        not row
        or not row["active"]
        or datetime.fromisoformat(row["expires_at"]) <= datetime.now(timezone.utc)
    ):
        raise HTTPException(
            401, "Invalid or expired credential", headers={"WWW-Authenticate": "Bearer"}
        )
    return dict(row)


def allow(permission):
    def check(p=Depends(principal)):
        if permission not in PERMISSIONS[p["role"]]:
            raise HTTPException(403, "Role does not permit this action")
        return p

    return check
