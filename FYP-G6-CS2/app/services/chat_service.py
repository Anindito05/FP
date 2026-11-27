"""Dialogue manager: stores encrypted turns and routes risk before companion replies."""
from datetime import datetime,timezone
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import User,ChatSession,Message,MessageAnalysis,RiskEvent,Feedback,MoodState
from ..schemas import SessionCreate,SessionOut,MessageIn,MessageOut,EscalationOffer,FeedbackIn
from ..security import encrypt_text,decrypt_text
from ..ml.nlu import analyze_message,Analysis
from ..ml.safety import build_crisis_reply,check_response,safe_fallback,is_human_question,honest_identity_reply
from ..llm import build_llm_client,with_resilience,UpstreamLLMError
from ..rag import get_context,build_messages
from ..prompts import get_prompt
from ..config import get_settings
from .. import prompts
from . import escalation_service

async def start_session(user:User,data:SessionCreate,db:AsyncSession)->SessionOut:
    if data.mode!="text": raise HTTPException(400,"Only text mode is supported")
    row=ChatSession(user_id=user.id,title=data.title,status="active",mode=data.mode);db.add(row);await db.flush();return SessionOut.model_validate(row)
async def list_sessions(user:User,limit:int,db:AsyncSession):
    return (await db.scalars(select(ChatSession).where(ChatSession.user_id==user.id).order_by(ChatSession.started_at.desc()).limit(limit))).all()
async def get_owned_session(user:User,session_id,db:AsyncSession)->ChatSession:
    row=await db.scalar(select(ChatSession).where(ChatSession.id==session_id,ChatSession.user_id==user.id))
    if row is None: raise HTTPException(404,"Session not found")
    return row
async def history(user:User,session_id,limit:int,db:AsyncSession)->list[MessageOut]:
    s=await get_owned_session(user,session_id,db); rows=(await db.scalars(select(Message).where(Message.session_id==s.id).order_by(Message.turn_index.desc()).limit(min(limit,100)))).all()
    return [MessageOut(id=m.id,role=m.role,content=decrypt_text(m.content_enc),route=m.route or "normal",created_at=m.created_at) for m in reversed(rows)]
async def close_session(user:User,session_id,db:AsyncSession)->SessionOut:
    s=await get_owned_session(user,session_id,db);s.status="closed";s.ended_at=datetime.now(timezone.utc);return SessionOut.model_validate(s)
async def handle_message(user:User,session:ChatSession,msg:MessageIn,db:AsyncSession)->MessageOut:
    await escalation_service.ensure_consent(user,"data_logging",db)
    prev=await db.scalar(select(Message).where(Message.session_id==session.id,Message.client_msg_id==msg.client_msg_id,Message.role=="user"))
    if prev:
        answer=await db.scalar(select(Message).where(Message.session_id==session.id,Message.role=="assistant",Message.turn_index==prev.turn_index+1))
        if answer:return MessageOut(id=answer.id,content=decrypt_text(answer.content_enc),route=answer.route or "normal",created_at=answer.created_at)
        text=decrypt_text(prev.content_enc); user_row=prev
    else:
        text=msg.content;user_row=Message(session_id=session.id,role="user",content_enc=encrypt_text(text),turn_index=session.message_count,client_msg_id=msg.client_msg_id);db.add(user_row);session.message_count+=1;await db.commit()
    recent_rows=(await db.scalars(select(MessageAnalysis.risk_level).join(Message,Message.id==MessageAnalysis.message_id).where(Message.session_id==session.id).order_by(Message.turn_index.desc()).limit(3))).all()
    recent_text=(await db.scalars(select(Message.content_enc).where(Message.session_id==session.id,Message.role=="user",Message.id!=user_row.id).order_by(Message.turn_index.desc()).limit(3))).all()
    history_text=[decrypt_text(x) for x in reversed(recent_text) if x]
    analysis=await analyze_message(text,history_text,session.id)
    if analysis.risk.level=="critical":return await crisis_path(session,analysis,db,user_row.id)
    return await normal_path(session,text,analysis,db,user_row.id)
async def normal_path(session:ChatSession,text:str,analysis:Analysis,db:AsyncSession,user_message_id=None)->MessageOut:
    chunks=await get_context(text,db)
    recent=(await db.scalars(select(Message).where(Message.session_id==session.id).order_by(Message.turn_index.desc()).limit(8))).all()
    history_msgs=[{"role":m.role,"content":decrypt_text(m.content_enc)} for m in reversed(recent)]
    state=analysis.state
    from ..ml.classification import classifier as runtime_classifier
    if runtime_classifier is not None:
        runtime_classifier.index.prefetch([state.emotion_top,*runtime_classifier.index.graph.get(state.emotion_top,[])[:get_settings().prefetch_neighbours]])
    mode="extra_care" if state.level==3 else "check_in" if state.level==2 else "normal"
    messages=[{"role":"system","content":get_prompt("guard.v1.md")},*build_messages(text,history_msgs[:-1],chunks,state,mode)]
    client=build_llm_client(get_settings());started=__import__('time').monotonic()
    try:
        reply=honest_identity_reply() if is_human_question(text) else (await with_resilience(lambda:client.generate(messages,400,.2),1,get_settings().llm_timeout_s)).content
        if not check_response(reply,"none",text).allowed:
            reply=(await with_resilience(lambda:client.generate(messages,400,.2),0,get_settings().llm_timeout_s)).content
            if not check_response(reply,"none",text).allowed: reply=safe_fallback(analysis.language,text)
    except Exception: reply=safe_fallback(analysis.language,text)
    out=await _save_assistant(session,reply,"normal",analysis,db,user_message_id,int((__import__('time').monotonic()-started)*1000))
    out.emotion=analysis.emotion
    if state.level==3: out.escalation_offer=await escalation_service.create_offer(session,"high",db)
    return out
async def crisis_path(session:ChatSession,analysis:Analysis,db:AsyncSession,user_message_id=None)->MessageOut:
    reply=build_crisis_reply(analysis.risk.level,analysis.language).text
    offer=await escalation_service.create_offer(session,analysis.risk.level,db)
    out=await _save_assistant(session,reply,"crisis",analysis,db,user_message_id,0)
    db.add(RiskEvent(session_id=session.id,message_id=user_message_id or out.id,risk_level=analysis.risk.level,action_taken="scripted_crisis_reply"));await db.flush();out.escalation_offer=offer;out.level=4;out.trend=analysis.state.trend if analysis.state else "rising";out.classifier_mode=analysis.state.classifier_mode if analysis.state else "degraded";return out
async def _save_assistant(session,reply,route,analysis,db,user_message_id,latency):
    row=Message(session_id=session.id,role="assistant",content_enc=encrypt_text(reply),turn_index=session.message_count,route=route,latency_ms=latency);db.add(row);session.message_count+=1
    if user_message_id:
        result=analysis.classification;state=analysis.state
        from ..ml.classification import runtime_status
        index_version=runtime_status()["index_version"]
        db.add(MessageAnalysis(message_id=user_message_id,emotion_label=analysis.emotion,emotion_scores={"intensity":analysis.emotion_intensity,"confidence":analysis.confidence,"language":"en"},intent_label=analysis.intent,risk_score=analysis.risk.score,risk_level=analysis.risk.level,risk_source=analysis.risk.source,keyword_hits=analysis.risk.keyword_hits,model_versions={"classifier":"rag-v1","risk":"keyword-v2"},prompt_versions=analysis.prompt_versions or prompts.prompt_versions(),emotion_dist=result.emotion_dist if result else {},level_dist={str(k):v for k,v in result.level_dist.items()} if result else {},instant_level=state.instant_level,level=state.level,confidence=state.confidence,novelty=result.novelty if result else 1,classifier_mode=state.classifier_mode,index_version=index_version,prompt_version="alex.v2"))
        db.add(MoodState(session_id=session.id,turn_index=session.message_count-1,level=state.level,instant_level=state.instant_level,mood_vector=state.mood_vector,emotion_top=state.emotion_top,trend=state.trend,shift_flag=state.shift_flag,index_version=index_version))
    await db.flush();return MessageOut(id=row.id,content=reply,route=route,emotion=analysis.emotion,created_at=row.created_at,level=analysis.state.level if analysis.state else 0,trend=analysis.state.trend if analysis.state else "steady",shift_flag=analysis.state.shift_flag if analysis.state else None,classifier_mode=analysis.state.classifier_mode if analysis.state else "degraded")
async def save_feedback(user:User,data:FeedbackIn,db:AsyncSession)->None:
    msg=await db.scalar(select(Message).join(ChatSession).where(Message.id==data.message_id,ChatSession.user_id==user.id))
    if not msg:raise HTTPException(404,"Message not found")
    db.add(Feedback(message_id=data.message_id,user_id=user.id,rating=data.rating,helpful=data.helpful,comment=data.comment))
