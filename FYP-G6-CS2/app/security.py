"""Password hashing, tokens, message encryption, authorization and throttling."""
from datetime import datetime, timedelta, timezone
from collections import defaultdict, deque
from functools import wraps
from hashlib import sha256
from uuid import UUID
import time
import jwt
from argon2 import PasswordHasher
from cryptography.fernet import Fernet, InvalidToken
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .config import get_settings
from .database import get_db
from .models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
_hasher = PasswordHasher()
_rates: dict[str, deque] = defaultdict(deque)

def hash_password(plain: str) -> str: return _hasher.hash(plain)
def verify_password(plain: str, hashed: str) -> bool:
    try: return _hasher.verify(hashed, plain)
    except Exception: return False
def _secret() -> str:
    s = get_settings().jwt_secret
    if len(s) < 32: raise RuntimeError("JWT_SECRET must contain at least 32 characters")
    return s
def create_access_token(subject: UUID, role: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": str(subject), "role": role, "typ": "access", "iat": now, "exp": now + timedelta(minutes=get_settings().access_ttl_min)}, _secret(), algorithm="HS256")
def create_refresh_token(subject: UUID, family_id: UUID) -> tuple[str, datetime]:
    now = datetime.now(timezone.utc); exp = now + timedelta(days=get_settings().refresh_ttl_days)
    return jwt.encode({"sub": str(subject), "family": str(family_id), "typ": "refresh", "iat": now, "exp": exp, "jti": __import__('secrets').token_urlsafe(32)}, _secret(), algorithm="HS256"), exp
def decode_token(token: str, expected_type: str) -> dict:
    try:
        data = jwt.decode(token, _secret(), algorithms=["HS256"])
        if data.get("typ") != expected_type: raise ValueError()
        return data
    except Exception as e: raise HTTPException(401, "Invalid or expired token") from e
def _fernet() -> Fernet:
    key = get_settings().field_encryption_key
    if not key: raise RuntimeError("FIELD_ENCRYPTION_KEY is required for message storage")
    try: return Fernet(key.encode())
    except Exception as e: raise RuntimeError("FIELD_ENCRYPTION_KEY must be a Fernet key") from e
def encrypt_text(plaintext: str) -> bytes: return _fernet().encrypt(plaintext.encode())
def decrypt_text(ciphertext: bytes) -> str:
    try: return _fernet().decrypt(ciphertext).decode()
    except InvalidToken as e: raise ValueError("Stored message cannot be decrypted") from e
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    data = decode_token(token, "access")
    user = await db.scalar(select(User).where(User.id == UUID(data["sub"]), User.is_active.is_(True), User.deleted_at.is_(None)))
    if user is None: raise HTTPException(401, "Inactive or unknown account")
    return user
def require_role(*roles: str):
    async def check(user: User = Depends(get_current_user)):
        if user.role not in roles: raise HTTPException(403, "Insufficient role")
        return user
    return check
def rate_limit(limit_per_min: int):
    async def check(request: Request):
        host=request.client.host if request.client else "unknown"
        key=sha256(host.encode()).hexdigest()
        now = time.monotonic(); q = _rates[key]
        while q and q[0] < now - 60: q.popleft()
        if len(q) >= limit_per_min: raise HTTPException(429, "Rate limit exceeded")
        q.append(now)
    return check
def token_digest(token: str) -> str: return sha256(token.encode()).hexdigest()
