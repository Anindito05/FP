"""Per-session level hysteresis and smoothed emotion trajectory."""
from dataclasses import dataclass, field
import math
from .levels import EMOTIONS

@dataclass
class MoodState:
    level: int=0
    instant_level: int=0
    emotion_top: str="neutral"
    emotion_intensity: float=0.0
    intent: str="smalltalk"
    trend: str="steady"
    shift_flag: str|None=None
    confidence: float=0.0
    classifier_mode: str="no_index"
    mood_vector: dict[str,float]=field(default_factory=lambda:{x:0.0 for x in EMOTIONS})
    rising_turns: int=0
    calmer_turns: int=0
    _previous_instant: int=0
    _previous_top: str="neutral"

class MoodTracker:
    def __init__(self,hysteresis_turns=3,decay=.8,smoothing=.55,neighbours=None):
        self.hysteresis_turns=hysteresis_turns;self.decay=decay;self.smoothing=smoothing;self.neighbours=neighbours or {};self.states={}
    def update(self,session_id,classification,keyword_level=0):
        state=self.states.setdefault(str(session_id),MoodState()); old_level=state.level
        state.instant_level=int(classification.instant_level); state.classifier_mode=classification.mode; state.confidence=classification.confidence
        state.intent=classification.intent; state.emotion_top=classification.emotion_top; state.emotion_intensity=classification.emotion_intensity
        target=max(state.instant_level,int(keyword_level))
        known=classification.mode=="ready" and classification.confidence>=.35
        if not known: target=max(int(keyword_level),int(math.floor(state.level*self.decay)))
        if target>=4 and not (keyword_level>=4 or (state.instant_level==4 and classification.confidence>=.65)): target=3
        if target>state.level: state.level=target;state.calmer_turns=0
        elif target<state.level:
            state.calmer_turns+=1
            if state.calmer_turns>=self.hysteresis_turns: state.level=max(target,state.level-1);state.calmer_turns=0
            target=state.level
        if known and target>state._previous_instant: state.rising_turns+=1
        else: state.rising_turns=0
        if state.rising_turns>=3: state.level=min(3,max(state.level,old_level+1));state.rising_turns=0
        incoming=classification.emotion_dist or {}
        prev=state.mood_vector.copy()
        for emotion in EMOTIONS: state.mood_vector[emotion]=self.smoothing*float(incoming.get(emotion,0))+(1-self.smoothing)*state.mood_vector.get(emotion,0)
        distance=math.sqrt(sum((state.mood_vector[x]-prev.get(x,0))**2 for x in EMOTIONS))
        adjacent=state.emotion_top in self.neighbours.get(state._previous_top,[])
        sudden=state.emotion_intensity>.8 and state._previous_instant<=1
        state.shift_flag="abrupt" if distance>.65 and not adjacent or sudden else "gradual" if state.emotion_top!=state._previous_top else None
        state.trend="rising" if state.level>old_level or state.rising_turns else "falling" if state.level<old_level else "steady"
        state._previous_instant=state.instant_level;state._previous_top=state.emotion_top
        # Confusion and mild frustration cannot elevate without a direct risk/trajectory signal.
        if state.emotion_top in {"confusion","frustration"} and state.level<=1 and keyword_level<2: state.level=min(state.level,1)
        return state
