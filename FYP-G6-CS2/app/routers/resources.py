"""Public helpline search and authenticated consent-gated location search."""
from fastapi import APIRouter,Depends,Query
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..security import get_current_user
from ..models import User
from ..schemas import ConsentOut,ConsentIn
from ..services import escalation_service
from ..services.help_search_service import search_support
router=APIRouter()
@router.get("/resources/helplines")
async def helplines(country:str,city:str|None=None,region:str|None=None,db:AsyncSession=Depends(get_db)):
    return await search_support(country,region,city,False,db)
@router.get("/resources/nearby")
async def nearby(country:str|None=None,city:str|None=None,region:str|None=None,user:User=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    await escalation_service.ensure_consent(user,"location_lookup",db)
    if not country and not user.region_code: from fastapi import HTTPException; raise HTTPException(400,"Country is required")
    return await search_support(country or user.region_code,region,city,True,db)
@router.get("/consents",response_model=list[ConsentOut])
async def list_consents(user:User=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    from sqlalchemy import select
    from ..models import Consent
    rows=(await db.scalars(select(Consent).where(Consent.user_id==user.id).order_by(Consent.created_at.desc()))).all()
    return [ConsentOut(type=x.type,granted=x.granted and x.revoked_at is None,version=x.version,updated_at=x.created_at) for x in rows]
@router.put("/consents",response_model=ConsentOut)
async def set_consent(data:ConsentIn,user:User=Depends(get_current_user),db:AsyncSession=Depends(get_db)):return await escalation_service.set_consent(user,data,db)
