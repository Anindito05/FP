"""Authentication endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..security import get_current_user, rate_limit
from ..models import User
from ..schemas import RegisterRequest, LoginRequest, GuestRequest, RefreshRequest, TokenPair, UserOut
from ..services import auth_service

router = APIRouter()

@router.post("/auth/register", response_model=UserOut, dependencies=[Depends(rate_limit(10))])
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)): return await auth_service.register(payload, db)
@router.post("/auth/login", response_model=TokenPair, dependencies=[Depends(rate_limit(10))])
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)): return await auth_service.login(payload, db)
@router.post("/auth/guest", response_model=TokenPair, dependencies=[Depends(rate_limit(10))])
async def guest(payload: GuestRequest, db: AsyncSession = Depends(get_db)): return await auth_service.create_guest(payload, db)
@router.post("/auth/refresh", response_model=TokenPair, dependencies=[Depends(rate_limit(20))])
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)): return await auth_service.refresh(payload, db)
@router.post("/auth/logout", status_code=204)
async def logout(payload: RefreshRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)): await auth_service.logout(user, payload.refresh_token, db)
@router.get("/users/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)): return UserOut.model_validate(user)
@router.delete("/users/me", status_code=204)
async def delete_me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)): await auth_service.delete_account(user, db)
