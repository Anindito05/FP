from app.security import hash_password, verify_password
import pytest
from datetime import datetime,timezone,timedelta
from uuid import uuid4
from types import SimpleNamespace
from fastapi import HTTPException
from app.services.auth_service import refresh
from app.schemas import RefreshRequest
from app.security import create_refresh_token,token_digest

def test_password_hash_verification():
    hashed=hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"
    assert verify_password("correct horse battery staple",hashed)
    assert not verify_password("incorrect",hashed)

@pytest.mark.asyncio
async def test_refresh_reuse_revokes_family(monkeypatch):
    from app.config import get_settings
    settings=get_settings();monkeypatch.setattr(settings,"jwt_secret","x"*48)
    user_id=uuid4();family=uuid4();token,expires=create_refresh_token(user_id,family)
    row=SimpleNamespace(token_hash=token_digest(token),revoked_at=datetime.now(timezone.utc),family_id=family)
    class DB:
        executed=False
        async def scalar(self,*_):return row
        async def execute(self,*_):self.executed=True
        async def commit(self):pass
    db=DB()
    with pytest.raises(HTTPException) as exc:await refresh(RefreshRequest(refresh_token=token),db)
    assert exc.value.status_code==401 and db.executed
