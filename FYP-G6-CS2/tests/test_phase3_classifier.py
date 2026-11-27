import json
from pathlib import Path
from app.ml.embedder import HashingEmbedder
from app.ml.index_store import IndexStore,build_index
from app.ml.rag_classifier import RAGClassifier,Classification
from app.ml.mood_tracker import MoodTracker

def rows():
    path=Path(__file__).parent/"fixtures/synthetic_classification.jsonl"
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]

def test_synthetic_index_build_and_classify(tmp_path):
    build_index(rows(),HashingEmbedder(),tmp_path,"test")
    store=IndexStore(tmp_path,ram_budget_mb=1,page_size=2); assert store.load()
    result=RAGClassifier(HashingEmbedder(),store,min_similarity=.01).classify("I am confused about this assignment")
    assert result.mode in {"ready","low_confidence"}
    assert result.emotion_dist and result.neighbour_ids

def test_no_index_is_explicit_degraded_mode(tmp_path):
    store=IndexStore(tmp_path); assert not store.load()
    assert RAGClassifier(HashingEmbedder(),store).classify("hello").mode=="no_index"

def test_keyword_forces_critical_even_if_classifier_is_calm():
    tracker=MoodTracker()
    state=tracker.update("s",Classification(mode="ready",instant_level=0,confidence=.9),keyword_level=4)
    assert state.level==4

def test_confusion_does_not_escalate_and_level_recovers_slowly():
    tracker=MoodTracker(hysteresis_turns=2)
    high=Classification(mode="ready",instant_level=3,confidence=.9,emotion_top="sadness")
    assert tracker.update("s",high).level==3
    confused=Classification(mode="ready",instant_level=0,confidence=.9,emotion_top="confusion",emotion_dist={"confusion":1})
    assert tracker.update("s",confused).level==3
    assert tracker.update("s",confused).level==2

def test_unknown_keeps_previous_level_decayed():
    tracker=MoodTracker(hysteresis_turns=5,decay=.9)
    tracker.update("s",Classification(mode="ready",instant_level=2,confidence=.9))
    state=tracker.update("s",Classification(mode="unknown"))
    assert state.level>=1
