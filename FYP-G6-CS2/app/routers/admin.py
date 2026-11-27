"""Administrative and reviewer endpoints."""
from uuid import UUID
from fastapi import APIRouter,Depends,Query,HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..security import require_role
from ..models import User,RiskEvent
from ..schemas import RiskEventOut,RiskReviewIn,MetricsOut
from ..services import admin_service
router=APIRouter()
@router.get("/admin/risk-events",response_model=list[RiskEventOut])
async def risk_queue(limit:int=Query(50,ge=1,le=200),user:User=Depends(require_role("reviewer","admin")),db:AsyncSession=Depends(get_db)):
 rows=(await db.scalars(select(RiskEvent).where(RiskEvent.reviewed_by.is_(None)).order_by(RiskEvent.created_at).limit(limit))).all();return [RiskEventOut.model_validate(x) for x in rows]
@router.post("/admin/risk-events/{event_id}/review",status_code=204)
async def review_risk(event_id:UUID,data:RiskReviewIn,user:User=Depends(require_role("reviewer","admin")),db:AsyncSession=Depends(get_db)):await admin_service.review_risk_event(event_id,user.id,data.review_label,db)
@router.get("/admin/metrics",response_model=MetricsOut)
async def metrics(user:User=Depends(require_role("reviewer","admin")),db:AsyncSession=Depends(get_db)):return await admin_service.live_metrics(db)
@router.get("/admin/sessions/{session_id}/mood")
async def mood(session_id:UUID,user:User=Depends(require_role("reviewer","admin")),db:AsyncSession=Depends(get_db)):return await admin_service.mood_timeline(session_id,db)
@router.post("/admin/eval")
async def run_eval(user:User=Depends(require_role("admin"))):
 from pathlib import Path
 import subprocess,sys
 script=Path(__file__).resolve().parents[2]/"scripts/run_eval.py"
 result=subprocess.run([sys.executable,str(script)],capture_output=True,text=True,timeout=30)
 if result.returncode: raise HTTPException(500,"Synthetic evaluation failed")
 return {"report":result.stdout,"note":"Synthetic fixture only; not clinical evidence."}
