"""Risk review, synthetic evaluation, metrics and retention."""
from datetime import datetime,timezone,timedelta
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select,func,delete
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import RiskEvent,EvalRun,Message,ChatSession,MessageAnalysis,MoodState
from ..schemas import MetricsOut

async def review_risk_event(event_id:UUID,reviewer_id:UUID,label:str,db:AsyncSession)->None:
    if label not in {"true_positive","false_positive","missed"}:raise HTTPException(400,"Invalid review label")
    row=await db.get(RiskEvent,event_id)
    if not row:raise HTTPException(404,"Risk event not found")
    row.reviewed_by=reviewer_id;row.review_label=label
async def live_metrics(db:AsyncSession)->MetricsOut:
    lat=await db.scalar(select(func.avg(Message.latency_ms)).where(Message.role=="assistant"))
    total=await db.scalar(select(func.count()).select_from(RiskEvent)) or 0
    sessions=await db.scalar(select(func.count()).select_from(ChatSession)) or 0
    return MetricsOut(avg_latency_ms=float(lat) if lat is not None else None,escalation_rate=total/sessions if sessions else 0.0)

async def mood_timeline(session_id:UUID,db:AsyncSession):
    rows=(await db.scalars(select(MoodState).where(MoodState.session_id==session_id).order_by(MoodState.turn_index))).all()
    return [{"turn_index":r.turn_index,"level":r.level,"instant_level":r.instant_level,"emotion_top":r.emotion_top,"trend":r.trend,"shift_flag":r.shift_flag,"index_version":r.index_version} for r in rows]
async def run_risk_eval(dataset_path:str,threshold:float,db:AsyncSession)->EvalRun:
    import csv, time
    from pathlib import Path
    from ..ml.risk import keyword_scan
    from ..ml.nlu import _model_analysis
    path=Path(dataset_path)
    if not path.is_absolute(): path=Path(__file__).resolve().parents[2]/path
    if not path.exists(): raise HTTPException(404,"Evaluation dataset not found")
    with path.open(encoding="utf-8",newline="") as f: rows=[(r["text"],r["label"]=="1",r["category"]) for r in csv.DictReader(f)]
    lat=[]; kw_preds=[]; llm_preds=[]; combined_preds=[]
    for text,label,category in rows:
        started=time.perf_counter();kw=keyword_scan(text).severity!="none"
        try: model=(await _model_analysis(text,[])).risk_level in {"medium","high"}
        except Exception:model=False
        lat.append((time.perf_counter()-started)*1000);kw_preds.append(kw);llm_preds.append(model);combined_preds.append(kw or model)
    created=[]
    for name,predictions in (("keyword-only",kw_preds),("LLM-only",llm_preds),("combined",combined_preds)):
        tp=sum(y and p for (_,y,_),p in zip(rows,predictions));fp=sum((not y) and p for (_,y,_),p in zip(rows,predictions));fn=sum(y and not p for (_,y,_),p in zip(rows,predictions));precision=tp/(tp+fp) if tp+fp else 0;recall=tp/(tp+fn) if tp+fn else 0
        row=EvalRun(name=name,dataset=str(path),model_versions={"analysis":"prompted","keyword":"keyword-v1","n":len(rows),"synthetic":True},precision=precision,recall=recall,f2=5*precision*recall/(4*precision+recall) if precision+recall else 0,fnr=fn/(tp+fn) if tp+fn else 0,latency_p95_ms=sorted(lat)[max(0,int(.95*(len(lat)-1)))] if lat else None)
        db.add(row);created.append(row)
    await db.flush();return created[-1]
async def run_groundedness_eval(samples:list[dict])->float:
    return 0.0 if not samples else sum(bool(s.get("citations")) for s in samples)/len(samples)
async def purge_expired(days:int,db:AsyncSession)->int:
    if days<1:raise ValueError("Retention days must be positive")
    cutoff=datetime.now(timezone.utc)-timedelta(days=days)
    rows=(await db.scalars(select(Message).where(Message.created_at<cutoff))).all();count=len(rows)
    await db.execute(delete(Message).where(Message.created_at<cutoff));return count
