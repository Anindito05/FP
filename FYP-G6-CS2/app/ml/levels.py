"""Shared severity scale. Structure draws on C-SSRS, PHQ-9 item 9 and WHO mhGAP emergency criteria.

Those instruments inform ordering and escalation concepts only. This mapping is not a
diagnostic instrument and requires clinical review before any real-world use.
"""
# NEEDS CLINICAL REVIEW
LEVEL_NAMES = {0: "calm", 1: "mild", 2: "elevated", 3: "high", 4: "critical"}
RISK_LABEL_TO_LEVEL = {
    "none": 0, "low": 1, "mild": 1, "passive_ideation": 3,
    "elevated": 2, "active_ideation": 4, "plan": 4, "intent": 4,
    "behaviour": 4, "attempt": 4,
}

DATASET_LABEL_MAPPINGS = {
    "cssrs_reddit": {"no_risk":0,"passive_ideation":3,"active_ideation":4,"plan":4,"intent":4,"behaviour":4},
    "umd_clpsych": {"none":0,"low":1,"moderate":3,"high":4},
    "daic_woz": {"phq_below_threshold":0,"phq_above_threshold":2},
    "clef_erisk": {"no_risk":0,"low":1,"moderate":3,"high":4},
}
EMOTIONS = ("neutral", "joy", "sadness", "anger", "fear", "anxiety", "loneliness", "confusion", "frustration", "hope", "other")
INTENTS = ("vent", "seek_advice", "seek_info", "seek_reassurance", "crisis_adjacent", "smalltalk")
