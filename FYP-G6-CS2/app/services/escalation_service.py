"""Consent-first support offers, verified resources and consent management."""
from datetime import datetime,timezone
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import ChatSession,User,Consent,Message
from ..schemas import EscalationOffer,EscalationResponse,MessageOut,ConsentIn,ConsentOut
from ..security import encrypt_text
from .help_search_service import search_support

async def create_offer(session:ChatSession,level:str,db:AsyncSession)->EscalationOffer:
    return EscalationOffer(offer_id=uuid4(),text="Would you like help finding support resources?",options=["helpline","nearby_services","decline"])
async def ensure_consent(user:User,type:str,db:AsyncSession)->None:
    consent=await db.scalar(select(Consent).where(Consent.user_id==user.id,Consent.type==type,Consent.granted.is_(True),Consent.revoked_at.is_(None)).order_by(Consent.created_at.desc()))
    if not consent: raise HTTPException(403,"Consent required")
async def set_consent(user:User,data:ConsentIn,db:AsyncSession)->ConsentOut:
    allowed={"terms","data_logging","location_lookup","research_use"}
    if data.type not in allowed: raise HTTPException(400,"Unknown consent type")
    now=datetime.now(timezone.utc)
    active=(await db.scalars(select(Consent).where(Consent.user_id==user.id,Consent.type==data.type,Consent.revoked_at.is_(None)))).all()
    for previous in active: previous.revoked_at=now
    row=await db.scalar(select(Consent).where(Consent.user_id==user.id,Consent.type==data.type,Consent.version==data.version))
    if row is None:
        row=Consent(user_id=user.id,type=data.type,granted=data.granted,version=data.version,granted_at=now if data.granted else None,revoked_at=None if data.granted else now);db.add(row)
    else:
        row.granted=data.granted;row.granted_at=now if data.granted else None;row.revoked_at=None if data.granted else now
    await db.flush()
    return ConsentOut(type=row.type,granted=row.granted,version=row.version,updated_at=row.created_at)
async def handle_choice(user:User,data:EscalationResponse,db:AsyncSession,session:ChatSession)->MessageOut:
    if data.choice not in {"helpline","nearby_services","decline"}: raise HTTPException(400,"Invalid escalation choice")
    if data.choice=="decline":
        resources=[];text="That’s okay. We can keep talking, or you can ask for support resources later."
    else:
        await ensure_consent(user,"location_lookup",db)
        country=data.country or user.region_code
        if not country: raise HTTPException(400,"Please provide a country or region.")
        resources=await search_support(country,data.region,data.city,data.choice=="nearby_services",db)
        if any(r.get("phone") for r in resources): text="Here are sourced support options. Please verify details with each source. If you are in immediate danger, contact your local emergency number or someone you trust."
        else: text="I could not verify a phone number. Contact your local emergency number or a trusted person if you may be in immediate danger. These source links may help you find local support."
        text += "\n"+"\n".join(r.get("source_url","") for r in resources if r.get("source_url"))
    row=Message(session_id=session.id,role="assistant",content_enc=encrypt_text(text),turn_index=session.message_count,route="crisis");db.add(row);session.message_count+=1;await db.flush()
    return MessageOut(id=row.id,content=text,route="crisis",created_at=row.created_at)
