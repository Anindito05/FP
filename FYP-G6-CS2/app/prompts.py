"""Versioned prompt templates, loaded once per process."""
from functools import lru_cache
from pathlib import Path

@lru_cache(maxsize=None)
def get_prompt(name: str) -> str:
    return (Path(__file__).parent / "prompts" / name).read_text(encoding="utf-8")

def prompt_versions() -> dict[str, str]:
    return {"companion":"alex.v2", "guard":"guard.v1", "helpline_extract":"helpline_extract.v1", "nearby_extract":"nearby_extract.v1"}
