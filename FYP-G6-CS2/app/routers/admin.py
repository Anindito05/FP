"""Administrative and reviewer endpoints."""
from uuid import UUID
from fastapi import APIRouter,Depends,Query
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
@router.post("/admin/eval")
async def run_eval(dataset:str="data/eval_risk.csv",user:User=Depends(require_role("admin")),db:AsyncSession=Depends(get_db)):
 row=await admin_service.run_risk_eval(dataset,.3,db)
 return {"id":str(row.id),"precision":row.precision,"recall":row.recall,"f2":row.f2,"fnr":row.fnr,"latency_p95_ms":row.latency_p95_ms,"note":"Combined synthetic evaluation; use scripts/run_eval.py for ablations."}
