"""Keyword-first risk detection; works without downloaded model weights."""
from dataclasses import dataclass, field
import re
import unicodedata

@dataclass
class KeywordScan:
    severity: str = "none"
    hits: list[str] = field(default_factory=list)

@dataclass
class RiskDecision:
    level: str
    score: float
    source: str
    keyword_hits: list[str] = field(default_factory=list)

def normalize_text(text: str) -> str:
    """Normalize obfuscation and accents. Incoming: text. Outgoing: normalized text."""
    value = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    value = re.sub(r"(.)\1{2,}", r"\1\1", value)
    return re.sub(r"[^a-z0-9\s]", " ", value)

_HIGH = (r"\bkill myself\b", r"\bkill yourself\b", r"\bend my life\b", r"\bsuicid\w*\b", r"\bwant to die\b", r"\bwanna d e\b", r"\bwant to be dead\b", r"\bdo not want to be alive\b", r"\bdont want to be alive\b", r"\bself harm\b", r"\bhurt myself\b", r"\bno reason to live\b", r"\bunalive myself\b")
_WEAK = (r"\bbetter off dead\b", r"\bcan ?t go on\b", r"\bcan ?t take (?:all of )?(?:this|it) anymore\b", r"\bcan ?t handle (?:all of )?(?:this|it) anymore\b", r"\bhopeless\b", r"\bdisappear forever\b", r"\bnot worth living\b")

def keyword_scan(text: str) -> KeywordScan:
    """Scan versioned conservative patterns. Incoming: text. Outgoing: KeywordScan."""
    value = normalize_text(text)
    value=value.replace("kys","kill yourself").replace("unalive","die")
    high = [p for p in _HIGH if re.search(p, value)]
    weak = [p for p in _WEAK if re.search(p, value)]
    return KeywordScan("high" if high else ("weak" if weak else "none"), high + weak)

def escalation_trend(history_levels: list[str]) -> bool:
    """Detect repeated/escalating recent levels. Incoming: levels. Outgoing: bool."""
    rank = {"none": 0, "low": 1, "medium": 2, "high": 3}
    recent = [rank.get(v, 0) for v in history_levels[-3:]]
    return len(recent) >= 2 and (sum(v > 0 for v in recent) >= 2 or recent[-1] > recent[0])
