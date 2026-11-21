from app.ml.risk import escalation_trend,keyword_scan,normalize_text
from app.ml.safety import check_response,safe_fallback

def test_normalization_and_keyword_variants():
    assert normalize_text("I WANNAA D!E") == "i wannaa d e"
    for text in ("I want to kill myself","kys","I do not want to be alive","I wanna d!e"):
        assert keyword_scan(text).severity=="high"
    assert keyword_scan("I feel anxious about an exam").severity=="none"

def test_indirect_signal_and_escalation_trend():
    assert keyword_scan("I am better off dead").severity=="weak"
    assert escalation_trend(["none","low","low"])
    assert not escalation_trend(["none","none","none"])

def test_output_filter_and_fallback():
    assert not check_response("You should kill yourself","none").allowed
    assert not check_response("Some generated response","high").allowed
    assert safe_fallback("en")
