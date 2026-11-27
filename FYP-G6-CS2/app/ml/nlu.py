"""Offline prompt-analysis baseline plus Phase 3 RAG and keyword fusion."""
from dataclasses import dataclass
from .risk import RiskDecision, keyword_scan
from . import classification
from .levels import LEVEL_NAMES
from .legacy_analysis import AnalysisData

@dataclass
class Analysis:
    emotion: str="unknown"
    intent: str="smalltalk"
    risk: RiskDecision|None=None
    emotion_intensity: float=0.0
    confidence: float=0.0
    language: str="en"
    wants_location_help: bool=False
    degraded: bool=False
    prompt_versions: dict|None=None
    state: object|None=None
    classification: object|None=None

def keyword_level(text: str) -> tuple[int,list[str]]:
    scan=keyword_scan(text)
    return (4 if scan.severity=="high" else 3 if scan.severity=="weak" else 0),scan.hits

async def analyze_message(text: str, history: list[str], session_id="default") -> Analysis:
    """Always run keyword net; RAG is best-effort and never the sole escalation signal."""
    level,hits=keyword_level(text)
    result=None
    if classification.classifier is not None:
        try: result=classification.classifier.classify(text,history,classification.tracker.states.get(str(session_id)).level if classification.tracker is not None and str(session_id) in classification.tracker.states else 0)
        except Exception: result=None
    if classification.tracker is None:
        from .mood_tracker import MoodTracker
        classification.tracker=MoodTracker()
    if result is None:
        from .rag_classifier import Classification
        result=Classification(mode="degraded")
    state=classification.tracker.update(session_id,result,level)
    final=max(state.level,level)
    risk_level=LEVEL_NAMES[final]
    from .prompts import prompt_versions
    degraded=result.mode in {"no_index","unknown","degraded"}
    return Analysis(result.emotion_top,result.intent,RiskDecision(risk_level,final/4,"keyword+rag" if not degraded else "keyword+trend",hits),result.emotion_intensity,result.confidence,"en",False,degraded,{"companion":"alex.v2","guard":"guard.v1","classifier":"rag-v1"},state,result)

async def _model_analysis(text: str, history: list[str]):
    """Offline-only V2 prompt baseline; deliberately never called by runtime chat."""
    from .legacy_analysis import model_analysis
    return await model_analysis(text,history)
