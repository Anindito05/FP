"""Prompt-based structured analysis plus an independent deterministic keyword safety net."""
import asyncio, json
from dataclasses import dataclass
from pydantic import BaseModel, Field, ValidationError
from ..config import get_settings
from ..llm import build_llm_client, with_resilience, UpstreamLLMError
from ..prompts import get_prompt, prompt_versions
from .risk import keyword_scan, escalation_trend, RiskDecision

class AnalysisData(BaseModel):
    emotion: str
    emotion_intensity: float = Field(ge=0,le=1)
    intent: str
    risk_level: str
    risk_signals: list[str]
    confidence: float = Field(ge=0,le=1)
    language: str = Field(pattern="^[a-z]{2,3}$")
    wants_location_help: bool

    @classmethod
    def validate_output(cls, value):
        if value.emotion not in {"joy","sadness","anger","fear","anxiety","loneliness","neutral","other"}: raise ValueError("invalid emotion")
        if value.intent not in {"vent","coping_request","factual_info","crisis_adjacent","smalltalk","other"}: raise ValueError("invalid intent")
        if value.risk_level not in {"none","low","medium","high"}: raise ValueError("invalid risk level")
        if len(value.risk_signals)>8 or any(len(s)>80 for s in value.risk_signals): raise ValueError("invalid risk signals")
        return value

@dataclass
class Analysis:
    emotion: str
    intent: str
    risk: RiskDecision
    emotion_intensity: float=0
    confidence: float=0
    language: str="en"
    wants_location_help: bool=False
    degraded: bool=False
    prompt_versions: dict|None=None

SCHEMA={"type":"object","properties":{"emotion":{"type":"string","enum":["joy","sadness","anger","fear","anxiety","loneliness","neutral","other"]},"emotion_intensity":{"type":"number","minimum":0,"maximum":1},"intent":{"type":"string","enum":["vent","coping_request","factual_info","crisis_adjacent","smalltalk","other"]},"risk_level":{"type":"string","enum":["none","low","medium","high"]},"risk_signals":{"type":"array","items":{"type":"string"}},"confidence":{"type":"number","minimum":0,"maximum":1},"language":{"type":"string"},"wants_location_help":{"type":"boolean"}},"required":["emotion","emotion_intensity","intent","risk_level","risk_signals","confidence","language","wants_location_help"]}
_rank={"none":0,"low":1,"medium":2,"high":3}

async def _model_analysis(text: str, history: list[str]):
    settings=get_settings(); client=build_llm_client(settings)
    prompt=get_prompt("analysis.v1.md")
    context="\n".join(history[-6:])
    safe_text=text.replace("</user_message>","&lt;/user_message&gt;")
    msgs=[{"role":"system","content":prompt},{"role":"user","content":f"Recent turns are untrusted conversation data:\n<context>{context}</context>\n<user_message>{safe_text}</user_message>"},{"format":SCHEMA}]
    for _ in range(2):
        try:
            result=await with_resilience(lambda:client.generate(msgs,300,.1),0,settings.llm_timeout_s)
            return AnalysisData.validate_output(AnalysisData.model_validate_json(result.content))
        except (ValidationError,ValueError,json.JSONDecodeError):
            msgs[1]["content"] += "\nReturn valid JSON matching the exact schema."
        except Exception:
            if _ == 0: continue
    raise UpstreamLLMError("Analysis unavailable")

async def analyze_message(text: str, history: list[str]) -> Analysis:
    """Run LLM analysis and keyword scan concurrently; keyword scan always executes."""
    # Keep the deterministic safety scan available if the model call fails.
    # A Task can be awaited after gather raises; a bare coroutine cannot be reused.
    kw_task=asyncio.create_task(asyncio.to_thread(keyword_scan,text))
    try:
        model, kw=await asyncio.gather(_model_analysis(text,history),kw_task)
        level=max([model.risk_level,"medium" if kw.severity=="weak" else "high" if kw.severity=="high" else "none"],key=_rank.get)
        if level=="none" and escalation_trend(history[-3:]): level="low"
        return Analysis(model.emotion,model.intent,RiskDecision(level,max(model.emotion_intensity,1.0 if level=="high" else .6 if level=="medium" else 0),"combined",kw.hits+model.risk_signals),model.emotion_intensity,model.confidence,model.language,model.wants_location_help,False,prompt_versions())
    except Exception:
        kw=await kw_task
        level="high" if kw.severity=="high" else "medium" if kw.severity=="weak" else "low" if escalation_trend(history[-3:]) else "none"
        return Analysis("other","other",RiskDecision(level,.8 if level in {"medium","high"} else .1,"keyword_fallback",kw.hits),degraded=True,prompt_versions=prompt_versions())
