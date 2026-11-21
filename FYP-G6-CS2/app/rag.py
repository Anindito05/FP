"""RAG insertion point for the next semester; retrieval is intentionally disabled today."""
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

@dataclass
class ContextChunk:
    text: str
    source: str | None = None

async def get_context(query: str, db: AsyncSession) -> list[ContextChunk]:
    """Next-semester RAG insertion point. No corpus is used in this semester's build."""
    return []

def build_messages(user_text: str, history: list[dict], chunks: list[ContextChunk], analysis) -> list[dict]:
    from .prompts import get_prompt
    system = get_prompt("companion.v1.md").format(emotion=analysis.emotion, intent=analysis.intent,
        context="\n".join(c.text for c in chunks))
    return [{"role":"system","content":system}, *history, {"role":"user","content":user_text}]
