"""Session and chat endpoints."""
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..security import get_current_user,rate_limit
from ..models import User
from ..schemas import *
from ..services import chat_service, escalation_service
router=APIRouter()
@router.post("/sessions",response_model=SessionOut)
async def create_session(data:SessionCreate,user:User=Depends(get_current_user),db:AsyncSession=Depends(get_db)):return await chat_service.start_session(user,data,db)
@router.get("/sessions",response_model=list[SessionOut])
async def list_sessions(limit:int=Query(20,ge=1,le=100),cursor:str|None=None,user:User=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
 rows=await chat_service.list_sessions(user,limit,db);return [SessionOut.model_validate(x) for x in rows]
@router.get("/sessions/{session_id}/messages",response_model=list[MessageOut])
async def get_history(session_id:UUID,limit:int=Query(50,ge=1,le=100),user:User=Depends(get_current_user),db:AsyncSession=Depends(get_db)):return await chat_service.history(user,session_id,limit,db)
@router.post("/sessions/{session_id}/close",response_model=SessionOut)
async def close_session(session_id:UUID,user:User=Depends(get_current_user),db:AsyncSession=Depends(get_db)):return await chat_service.close_session(user,session_id,db)
@router.post("/chat/{session_id}/messages",response_model=MessageOut,dependencies=[Depends(rate_limit(30))])
async def send_message(session_id:UUID,msg:MessageIn,user:User=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
 s=await chat_service.get_owned_session(user,session_id,db);return await chat_service.handle_message(user,s,msg,db)
@router.post("/chat/{session_id}/escalation",response_model=MessageOut)
async def respond_to_escalation(session_id:UUID,data:EscalationResponse,user:User=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
 s=await chat_service.get_owned_session(user,session_id,db);return await escalation_service.handle_choice(user,data,db,s)
@router.post("/feedback",status_code=204)
async def submit_feedback(data:FeedbackIn,user:User=Depends(get_current_user),db:AsyncSession=Depends(get_db)):await chat_service.save_feedback(user,data,db)
