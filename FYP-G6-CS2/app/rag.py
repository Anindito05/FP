"""Wellness-knowledge RAG seam; classification retrieval is implemented in app.ml."""
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

@dataclass
class ContextChunk:
    text:str
    source:str|None=None

async def get_context(query:str,db:AsyncSession)->list[ContextChunk]:
    """Next semester's reviewed wellness-content retrieval insertion point."""
    return []

def build_messages(user_text,history,chunks,state,mode="normal"):
    from .prompts import get_prompt
    system=get_prompt("companion.v2.md").replace("{{MODE}}",mode).replace("{{MOOD_TREND}}",f"emotion={state.emotion_top}; trend={state.trend}; shift={state.shift_flag or 'none'}; level={state.level}")
    if chunks: system += "\nReviewed wellness context (only use when directly relevant):\n"+"\n".join(c.text for c in chunks)
    return [{"role":"system","content":system},*history,{"role":"user","content":user_text}]
