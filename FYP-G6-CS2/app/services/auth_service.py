"""Authentication workflows with rotating refresh tokens."""
from datetime import datetime, timezone
from uuid import uuid4, UUID
from fastapi import HTTPException
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import User, RefreshToken, Consent
from ..schemas import RegisterRequest, LoginRequest, GuestRequest, RefreshRequest, TokenPair, UserOut
from ..security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token, token_digest
from ..config import get_settings

def _pair(user: User, db: AsyncSession, family_id=None):
    import asyncio
    family = family_id or uuid4(); token, exp = create_refresh_token(user.id, family)
    db.add(RefreshToken(user_id=user.id, family_id=family, token_hash=token_digest(token), expires_at=exp))
    return TokenPair(access_token=create_access_token(user.id, user.role), refresh_token=token, expires_in=get_settings().access_ttl_min*60)

async def register(payload: RegisterRequest, db: AsyncSession) -> UserOut:
    """Create account. Incoming: payload/db. Outgoing: UserOut."""
    if not payload.accepted_terms: raise HTTPException(400, "Terms consent is required")
    email = str(payload.email).lower()
    if await db.scalar(select(User).where(User.email == email)): raise HTTPException(409, "Email already registered")
    user = User(email=email, password_hash=hash_password(payload.password), display_name=payload.display_name, region_code=payload.region_code, role="user")
    db.add(user); await db.flush(); db.add(Consent(user_id=user.id, type="terms", granted=True, version="1", granted_at=datetime.now(timezone.utc)))
    return UserOut.model_validate(user)

async def login(payload: LoginRequest, db: AsyncSession) -> TokenPair:
    """Authenticate account. Incoming: payload/db. Outgoing: TokenPair."""
    user = await db.scalar(select(User).where(User.email == str(payload.email).lower(), User.is_active.is_(True), User.deleted_at.is_(None)))
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash): raise HTTPException(401, "Invalid credentials")
    user.last_login_at = datetime.now(timezone.utc); return _pair(user, db)

async def create_guest(payload: GuestRequest, db: AsyncSession) -> TokenPair:
    """Create pseudonymous account. Incoming: payload/db. Outgoing: TokenPair."""
    if not payload.accepted_terms: raise HTTPException(400, "Terms consent is required")
    user = User(is_guest=True, role="user", region_code=payload.region_code); db.add(user); await db.flush()
    db.add(Consent(user_id=user.id, type="terms", granted=True, version="1", granted_at=datetime.now(timezone.utc)))
    return _pair(user, db)

async def refresh(payload: RefreshRequest, db: AsyncSession) -> TokenPair:
    """Rotate refresh token; reuse revokes entire family. Incoming: payload/db. Outgoing: TokenPair."""
    data = decode_token(payload.refresh_token, "refresh"); digest = token_digest(payload.refresh_token)
    row = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == digest).with_for_update())
    if row is None: raise HTTPException(401, "Invalid refresh token")
    if row.revoked_at is not None:
        await db.execute(update(RefreshToken).where(RefreshToken.family_id == row.family_id).values(revoked_at=datetime.now(timezone.utc)))
        await db.commit()  # Persist family revocation before returning the reuse error.
        raise HTTPException(401, "Refresh token reuse detected; sign in again")
    if row.expires_at <= datetime.now(timezone.utc): raise HTTPException(401, "Expired refresh token")
    user = await db.get(User, row.user_id)
    if user is None or not user.is_active: raise HTTPException(401, "Inactive account")
    row.revoked_at = datetime.now(timezone.utc)
    pair = _pair(user, db, row.family_id)
    new_data = decode_token(pair.refresh_token, "refresh")
    row.replaced_by = (await db.scalar(select(RefreshToken.id).where(RefreshToken.token_hash == token_digest(pair.refresh_token))))
    return pair

async def logout(user: User, refresh_token: str, db: AsyncSession) -> None:
    """Revoke user's token. Incoming: user/token/db. Outgoing: None."""
    data=decode_token(refresh_token,"refresh")
    if data.get("sub") != str(user.id): raise HTTPException(401,"Invalid refresh token")
    row = await db.scalar(select(RefreshToken).where(RefreshToken.user_id == user.id, RefreshToken.token_hash == token_digest(refresh_token)))
    if row: row.revoked_at = datetime.now(timezone.utc)

async def delete_account(user: User, db: AsyncSession) -> None:
    """Erase account's associated data. Incoming: user/db. Outgoing: None."""
    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
    # Session foreign keys cascade to encrypted messages, analyses and risk events.
    from ..models import ChatSession
    await db.execute(delete(ChatSession).where(ChatSession.user_id == user.id))
    await db.execute(delete(Consent).where(Consent.user_id == user.id))
    user.email = None; user.password_hash = None; user.display_name = None; user.is_active = False; user.deleted_at = datetime.now(timezone.utc)
