"""Run small synthetic safety ablation. Results are a smoke test, not clinical evidence."""
import asyncio,csv,sys,time,statistics
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.ml.risk import keyword_scan
from app.ml.nlu import _model_analysis
from app.models import EvalRun
from app.config import get_settings
from app.database import build_engine
from sqlalchemy.ext.asyncio import async_sessionmaker

def metrics(rows, predictions):
    tp=sum(y and p for (_,y,_),p in zip(rows,predictions)); fp=sum((not y) and p for (_,y,_),p in zip(rows,predictions)); fn=sum(y and not p for (_,y,_),p in zip(rows,predictions))
    precision=tp/(tp+fp) if tp+fp else 0; recall=tp/(tp+fn) if tp+fn else 0
    return precision,recall,(5*precision*recall/(4*precision+recall) if precision+recall else 0),fn/(tp+fn) if tp+fn else 0

async def main():
    path=Path(__file__).resolve().parents[1]/"data/eval_risk.csv"
    with path.open(encoding="utf-8",newline="") as f: rows=[(r["text"],r["label"]=="1",r["category"]) for r in csv.DictReader(f)]
    kw=[]; llm=[]; combined=[]; lat=[]; model_lat=[]
    for text,label,cat in rows:
        started=time.perf_counter(); kw_hit=keyword_scan(text).severity!="none"; kw.append(kw_hit)
        try:
            a=await _model_analysis(text,[]); model_risk=a.risk_level in {"medium","high"}
        except Exception: model_risk=False
        model_lat.append((time.perf_counter()-started)*1000);llm.append(model_risk);combined.append(kw_hit or model_risk);lat.append((time.perf_counter()-started)*1000)
    print("mode         precision recall F2    FNR   p50_ms p95_ms")
    persisted=[]
    for name,preds in (("keyword-only",kw),("LLM-only",llm),("combined",combined)):
        p,r,f2,fnr=metrics(rows,preds);p50=statistics.median(lat);p95=sorted(lat)[int(.95*(len(lat)-1))];print(f"{name:12} {p:.3f}     {r:.3f}  {f2:.3f} {fnr:.3f} {p50:.1f} {p95:.1f}")
        persisted.append(EvalRun(name=name,dataset=str(path),model_versions={"synthetic":True,"n":len(rows),"latency_p50_ms":p50},precision=p,recall=r,f2=f2,fnr=fnr,latency_p95_ms=p95))
        cats=sorted({x[2] for x in rows});print("  per-category recall:",", ".join(f"{c}={sum(y and cat==c and pred for (_,y,cat),pred in zip(rows,preds))}/{sum(y and cat==c for _,y,cat in rows)}" for c in cats if any(y and cat==c for _,y,cat in rows)))
    if get_settings().database_url:
        engine=build_engine(get_settings().database_url);factory=async_sessionmaker(engine,expire_on_commit=False)
        try:
            async with factory() as db: db.add_all(persisted);await db.commit()
            print("Saved three evaluation rows to eval_runs.")
        finally: await engine.dispose()
    else: print("DATABASE_URL is unset; results were not persisted.")
    print("LIMIT: hand-written synthetic n=8; not a clinical or real-user evaluation. LLM-only/combined rows are not meaningful while Ollama is unavailable.")
if __name__=="__main__": asyncio.run(main())
