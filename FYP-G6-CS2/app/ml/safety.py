"""Crisis templates and generated-output safety checks."""
from dataclasses import dataclass

@dataclass
class CrisisReply:
    text: str
    locale: str = "en"

@dataclass
class FilterResult:
    allowed: bool
    reason: str = ""

def build_crisis_reply(level: str, locale: str) -> CrisisReply:
    """Build reviewed-needed static response. Incoming: level, locale. Outgoing: CrisisReply."""
    # NEEDS HUMAN/CLINICAL REVIEW: do not present as therapy or emergency service.
    if locale.startswith("en"):
        text = ("I’m sorry this feels so difficult. I’m here with you. Are you in immediate danger right now? "
                "If you may act on these thoughts or cannot stay safe, please contact your local emergency service or go to a nearby emergency department, and consider reaching out to someone you trust to stay with you. "
                "Would you like me to show available support resources?")
    else:
        text = "I’m sorry you’re going through this. If you may be in immediate danger, contact your local emergency service or go to an emergency department. Would you like support resources?"
    return CrisisReply(text, locale)

def build_followup(choice: str, helplines: list, locale: str) -> str:
    """Create a factual consent follow-up. Incoming: choice/resources/locale. Outgoing: str."""
    if choice == "decline":
        return "That’s okay. We can keep talking, or you can ask for support resources later."
    if not helplines:
        return "I don’t have verified local resources available here. If you may be in immediate danger, contact your local emergency service."
    return "Here are the support resources available for your region. If you may be in immediate danger, contact your local emergency service."

def check_response(reply: str, risk_level: str, user_text: str = "") -> FilterResult:
    """Reject dangerous advice and crisis disclosures. Incoming: reply, risk_level. Outgoing: FilterResult."""
    import re
    unsafe = (r"\bkill yourself\b", r"\bhow to (?:die|commit suicide)\b", r"\bignore (?:your|the) (?:doctor|therapist)\b", r"\bguarantee(?:d)? (?:confidentiality|you will be safe)\b",r"\b(?:i am|i'm) (?:a )?(?:human|person|therapist|doctor|clinician)\b",r"\b(?:my therapist|my patients|i went through this myself)\b",r"\b(?:i will|i'll) (?:call|contact|message) (?:someone|your family|emergency services)\b")
    blocked = any(re.search(p, reply, re.I) for p in unsafe)
    if risk_level in {"critical", "high", "medium"}:
        blocked = True
    human_question=is_human_question(user_text)
    list_output=bool(re.search(r"(?:^|\n)\s*(?:[-*•]|\d+[.)])\s+",reply))
    boilerplate=bool(re.search(r"as an ai language model|i'm just an ai",reply,re.I))
    if human_question: return FilterResult(True)
    blocked=blocked or list_output or boilerplate
    return FilterResult(not blocked, "high_risk" if risk_level in {"critical", "high", "medium"} else "unsafe_content" if blocked else "")

def is_human_question(text: str) -> bool:
    import re
    return bool(re.search(r"\b(?:are you|r u) (?:a )?(?:human|person|bot|ai)\b|\bwhat are you\b",text,re.I))

def honest_identity_reply() -> str:
    return "I’m Alex, an AI companion, not a person. I can still listen and talk things through with you."

def safe_fallback(locale: str, user_text: str = "") -> str:
    """Return a brief contextual, non-clinical reply if model generation fails."""
    import re
    text = user_text.casefold().strip()
    if re.search(r"\b(?:hello|hi|hey|hei)\b|\bwhat'?s up\b|\bgood (?:morning|evening)\b", text):
        return "Hi, I’m here with you. How has your day been going?"
    if any(phrase in text for phrase in ("cant take", "can't take", "cannot take", "cant handle", "can't handle", "cannot handle", "cant go on", "can't go on", "cannot go on", "dont know what i will do", "don't know what i will do", "idk what i will do")):
        return "I hear how overwhelmed you feel, especially with the job loss and pressure at home. When you say you can’t take this anymore, are you thinking about hurting yourself, or are you in immediate danger right now? If you might act on those thoughts, please contact emergency services and get someone you trust to stay with you now."
    if any(phrase in text for phrase in ("lost my job", "lost my job", "got fired", "being fired", "family pressure", "pressure from my family")):
        return "That’s a lot to carry at once: losing your job and feeling responsible for your family. We don’t have to solve everything right now. What feels most urgent today: the practical next step, or having someone hear how this is affecting you?"
    if any(word in text for word in ("down", "sad", "low", "depressed", "rough", "hard day", "upset", "lonely")):
        return "I’m sorry today feels so heavy. Do you want to tell me what’s been weighing on you, or would it help to focus on one small thing that might make this moment easier?"
    if locale.startswith("en"):
        return "I’m here with you. Could you tell me a little more about what’s on your mind, or what kind of support would feel helpful right now?"
    return "I’m here with you. Tell me a little more about what’s on your mind, and we can take it one step at a time."
