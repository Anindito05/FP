"""Runtime singleton loading the embedder and selected index once during lifespan."""
from pathlib import Path
from .embedder import load_embedder
from .index_store import IndexStore
from .rag_classifier import RAGClassifier
from .mood_tracker import MoodTracker
from ..config import get_settings

classifier=None; tracker=None; load_error=None
def load_runtime(base_dir: Path | None=None):
    global classifier,tracker,load_error
    settings=get_settings(); base_dir=base_dir or Path(__file__).resolve().parents[2]
    index_path=Path(settings.index_dir) / settings.index_version
    if not index_path.is_absolute(): index_path=base_dir/index_path
    store=IndexStore(index_path,settings.ram_budget_mb,settings.page_size)
    try:
        embedder=load_embedder(settings.embed_model)
        store.load()
        classifier=RAGClassifier(embedder,store,settings.top_k,settings.min_similarity,settings.level_confidence_threshold)
        tracker=MoodTracker(settings.hysteresis_turns,settings.level_decay,settings.mood_smoothing,store.graph)
        load_error=None
    except Exception as exc:
        classifier=None;tracker=MoodTracker(settings.hysteresis_turns,settings.level_decay,settings.mood_smoothing);load_error=type(exc).__name__
    return classifier,tracker

def runtime_status():
    if classifier is None: return {"mode":"degraded","index_version":None,"dataset_ids":[],"tiers":[],"stats":{},"error":load_error}
    index=classifier.index
    return {"mode":"ready" if index.ready else "degraded","index_version":index.version,"dataset_ids":index.manifest.get("dataset_ids",[]),"tiers":index.manifest.get("tiers",[]),"stats":index.stats(),"error":None}
