"""Example-retrieval classifier. User text and embeddings exist only in process memory."""
from dataclasses import dataclass, field
import math
from .levels import EMOTIONS, INTENTS
from .index_store import IndexStore

@dataclass
class Classification:
    emotion_dist: dict[str,float] = field(default_factory=dict)
    emotion_top: str = "unknown"
    emotion_intensity: float = 0.0
    level_dist: dict[int,float] = field(default_factory=dict)
    instant_level: int = 0
    intent: str = "smalltalk"
    confidence: float = 0.0
    novelty: float = 1.0
    mode: str = "no_index"
    neighbour_ids: list[str] = field(default_factory=list)

class RAGClassifier:
    def __init__(self, embedder, index: IndexStore, top_k=8, min_similarity=.12, confidence_threshold=.55):
        self.embedder,self.index=embedder,index; self.top_k=top_k; self.min_similarity=min_similarity; self.confidence_threshold=confidence_threshold
    def classify(self, text: str, recent_turns: list[str] | None=None, previous_level=0):
        if not self.index.ready: return Classification()
        top_k=max(1,int(self.top_k)); min_similarity=float(self.min_similarity)
        recent=(recent_turns or [])[-3:]; parts=[text,*recent]; weights=[1.0,*[.35/(len(recent) or 1)]*len(recent)]
        vectors=self.embedder.encode(parts); vector=[sum(vectors[j][i]*weights[j] for j in range(len(vectors))) for i in range(len(vectors[0]))]; norm=math.sqrt(sum(x*x for x in vector))
        if norm: vector=[x/norm for x in vector]
        candidates=list(self.index.centroids)
        if self.index.centroids:
            candidates=sorted(candidates,key=lambda c:sum(x*y for x,y in zip(self.index.centroids[c],vector)),reverse=True)[:max(2,top_k)]
        before=self.index.pages_loaded
        neighbors=self.index.search(vector,top_k,min_similarity,candidates)
        if neighbors and (neighbors[0].similarity<self.confidence_threshold or (neighbors and max((n.level or 0) for n in neighbors)>previous_level)):
            neighbors=self.index.search(vector,top_k,min_similarity,candidates,cold=True)
        if not neighbors: return Classification(mode="unknown",novelty=1.0)
        weights=[max(0,n.similarity)**2 for n in neighbors]; total=sum(weights) or 1
        emotions={x:0.0 for x in EMOTIONS}; levels={i:0.0 for i in range(5)}; intents={x:0.0 for x in INTENTS}; intensity=0
        for n,w in zip(neighbors,weights):
            emotions[n.emotion]=emotions.get(n.emotion,0)+float(w)
            if n.level is not None: levels[int(n.level)]+=float(w)
            if n.intent in intents: intents[n.intent]+=float(w)
            intensity+=float(w)*(int(n.level or 0)/4)
        emotions={k:v/total for k,v in emotions.items()}; levels={k:v/total for k,v in levels.items()}
        top=sorted(emotions,key=emotions.get,reverse=True)[0]; voted=max(levels,key=levels.get) if any(n.level is not None for n in neighbors) else 0
        sims=sorted((n.similarity for n in neighbors),reverse=True); margin=sims[0]-(sims[1] if len(sims)>1 else 0)
        confidence=max(0,min(1,.65*sims[0]+.35*min(1,margin*3)))
        entropy=-sum(p*math.log(p) for p in levels.values() if p>0)/math.log(5)
        confidence*=max(.25,1-entropy*.25)
        mode="ready" if confidence>=self.confidence_threshold else "low_confidence"
        return Classification(emotions,top,min(1,intensity/total),levels,int(voted),max(intents,key=intents.get),confidence,max(0,1-sims[0]),mode,[n.item_id for n in neighbors])
