"""Synthetic-only pipeline evaluation. Results are engineering checks, not clinical evidence."""
import argparse,json,statistics,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.ml.risk import keyword_scan
from app.ml.embedder import load_embedder
from app.ml.index_store import IndexStore,build_index
from app.ml.rag_classifier import RAGClassifier
from app.ml.mood_tracker import MoodTracker

def load_rows():
    return [json.loads(x) for x in (Path(__file__).resolve().parents[1]/"tests/fixtures/synthetic_classification.jsonl").read_text(encoding="utf-8").splitlines()]
def score(y,p):
    tp=sum(a and b for a,b in zip(y,p));fp=sum((not a) and b for a,b in zip(y,p));fn=sum(a and not b for a,b in zip(y,p));precision=tp/(tp+fp) if tp+fp else 0;recall=tp/(tp+fn) if tp+fn else 0
    return precision,recall,5*precision*recall/(4*precision+recall) if precision+recall else 0,fn/(tp+fn) if tp+fn else 0
def main():
    parser=argparse.ArgumentParser();parser.add_argument("--prompt-baseline",action="store_true");options=parser.parse_args()
    rows=load_rows();embedder=load_embedder("hashing-n-gram-v1");root=Path(__file__).resolve().parents[1]/"models_store/eval"
    manifest=build_index(rows,embedder,root,"synthetic-eval");store=IndexStore(root,32,2);store.load();clf=RAGClassifier(embedder,store,top_k=8,min_similarity=.01,confidence_threshold=.01)
    true=[r["level"]>=3 for r in rows];kw=[];rag=[];combined=[];emo_true=[];emo_pred=[];lat=[]
    for row in rows:
        start=time.perf_counter();k=keyword_scan(row["text"]).severity!="none";out=clf.classify(row["text"]);lat.append((time.perf_counter()-start)*1000)
        kw.append(k);rag.append(out.instant_level>=3);combined.append(k or out.instant_level>=3);emo_true.append(row["emotion"]);emo_pred.append(out.emotion_top)
    prompt=[False]*len(rows); baseline_available=False
    if options.prompt_baseline:
        print("Prompt baseline unavailable in synthetic-only run; V2 prompt is retained for a separately configured fake-client harness.")
    print("Ablation (synthetic only): mode         precision recall F2    FNR")
    for name,pred in (("keyword-only",kw),("prompt-only (V2 baseline)",prompt),("RAG-only",rag),("combined",combined)):
        p,r,f,fn=score(true,pred);print(f"{name:15} {p:.3f}     {r:.3f}  {f:.3f} {fn:.3f}")
    classes=sorted(set(emo_true));f1=[]
    for c in classes:
        tp=sum(y==c and p==c for y,p in zip(emo_true,emo_pred));fp=sum(y!=c and p==c for y,p in zip(emo_true,emo_pred));fn=sum(y==c and p!=c for y,p in zip(emo_true,emo_pred));pr=tp/(tp+fp) if tp+fp else 0;re=tp/(tp+fn) if tp+fn else 0;f1.append(2*pr*re/(pr+re) if pr+re else 0)
    print(f"Emotion macro-F1={statistics.mean(f1):.3f}; per-class="+", ".join(f"{c}:{v:.3f}" for c,v in zip(classes,f1)))
    st=store.stats();print(f"Retrieval p50={statistics.median(lat):.3f}ms p95={sorted(lat)[int(.95*(len(lat)-1))]:.3f}ms RAM={st['ram_used_mb']:.3f}MB cache-hit={st['cache_hit_rate']:.3f} pages/query={st['pages_loaded_per_query']:.2f}")
    print("V2 prompt-analysis prompt retained for offline baseline; live calls are intentionally disabled in this synthetic evaluator.")
    print("Trajectory scripts: synthetic gradual escalation / abrupt spike / confusion / recovery; see tests/test_phase3_classifier.py")
    print("LIMIT: hand-authored synthetic fixture only; not real users and not clinically validated. Tier B labels are not clinician-validated.")
if __name__=="__main__": main()
