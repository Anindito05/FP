"""Versioned disk shards with bounded LRU page cache and in-memory prototypes."""
from collections import OrderedDict, defaultdict
from dataclasses import dataclass
import json, time
from pathlib import Path
import math, struct

def _dot(a,b): return sum(float(x)*float(y) for x,y in zip(a,b))
def _norm(a): return math.sqrt(_dot(a,a))
def _save_vectors(path,rows):
    with open(path,"wb") as f:
        f.write(struct.pack("<II",len(rows),len(rows[0]) if rows else 0))
        for row in rows:
            for value in row:f.write(struct.pack("<e",float(value)))
def _load_vectors(path):
    with open(path,"rb") as f:
        count,dim=struct.unpack("<II",f.read(8));data=f.read()
    values=struct.unpack("<"+"e"*(count*dim),data) if count else ()
    return [list(values[i*dim:(i+1)*dim]) for i in range(count)]

@dataclass
class Neighbor:
    similarity: float
    dataset_id: str
    item_id: str
    emotion: str
    level: int | None
    intent: str | None

class IndexStore:
    def __init__(self, root: Path, ram_budget_mb: int = 256, page_size: int = 256):
        self.root, self.ram_budget = Path(root), ram_budget_mb * 1024 * 1024
        self.page_size = max(1, page_size); self.cache = OrderedDict(); self.cache_bytes = 0
        self.hot = {}; self.prototypes = {}; self.graph = {}; self.centroids = {}
        self.manifest = {}; self.latencies = []; self.pages_loaded = 0; self.cache_hits = 0
        self._metadata = {}
    @property
    def ready(self): return bool(self.manifest.get("count", 0))
    @property
    def version(self): return self.manifest.get("version")
    def load(self):
        path = self.root / "manifest.json"
        if not path.exists(): return False
        self.manifest = json.loads(path.read_text(encoding="utf-8"))
        self.graph = json.loads((self.root / "neighbours.json").read_text(encoding="utf-8")) if (self.root / "neighbours.json").exists() else {}
        self.centroids = {k: _load_vectors(self.root / v)[0] for k,v in self.manifest.get("centroids", {}).items()}
        for key, meta_path in self.manifest.get("shards", {}).items():
            rows = json.loads((self.root / meta_path["metadata"]).read_text(encoding="utf-8"))
            self._metadata[key] = rows
            if meta_path.get("hot"):
                self.hot[key] = _load_vectors(self.root / meta_path["vectors"])
                self.prototypes[key] = self.hot[key][:min(16, len(rows))]
        return self.ready
    def _page(self, key, page):
        cache_key=(key,page)
        if cache_key in self.cache:
            self.cache_hits += 1; self.cache.move_to_end(cache_key); return self.cache[cache_key]
        info=self.manifest["shards"][key]; start=page*self.page_size; end=min(start+self.page_size,info["count"])
        with open(self.root/info["vectors"],"rb") as f:
            count,dimension=struct.unpack("<II",f.read(8));f.seek(8+start*dimension*2);raw=f.read((end-start)*dimension*2)
        values=struct.unpack("<"+"e"*((end-start)*dimension),raw) if raw else ()
        data=[list(values[i*dimension:(i+1)*dimension]) for i in range(end-start)]; size=sum(len(x)*4 for x in data)
        while self.cache and self.cache_bytes+size>self.ram_budget:
            _,old=self.cache.popitem(last=False); self.cache_bytes-=sum(len(x)*4 for x in old)
        if size<=self.ram_budget:
            self.cache[cache_key]=data; self.cache_bytes+=size
        self.pages_loaded+=1; return data
    def search(self, vector, top_k=8, min_similarity=.12, candidate_classes=None, cold=False):
        start=time.perf_counter()
        if not self.ready: return []
        classes=list(candidate_classes or self.manifest.get("shards",{}))
        ranked=[]
        for key in classes:
            info=self.manifest["shards"].get(key)
            if not info: continue
            if key in self.hot and not cold: matrices=[(0,self.hot[key])]
            else: matrices=[(p,self._page(key,p)) for p in range((info["count"]+self.page_size-1)//self.page_size)]
            for page, matrix in matrices:
                for ix,entry in enumerate(matrix):
                    similarity=_dot(entry,vector)
                    if similarity>=min_similarity:
                        absolute=page*self.page_size+ix; row=self._metadata[key][absolute]
                        ranked.append(Neighbor(float(similarity),row["dataset_id"],row["item_id"],row["emotion"],row.get("level"),row.get("intent")))
        ranked.sort(key=lambda n:n.similarity,reverse=True)
        self.latencies.append((time.perf_counter()-start)*1000); return ranked[:top_k]
    def prefetch(self, classes):
        for key in classes:
            if key in self.manifest.get("shards",{}) and key not in self.hot: self._page(key,0)

    def reload(self, root: Path | None=None):
        if root is not None: self.root=Path(root)
        self.cache.clear();self.cache_bytes=0;self.hot.clear();self.prototypes.clear();self.centroids.clear();self._metadata.clear();self.manifest={}
        return self.load()
    def stats(self):
        ordered=sorted(self.latencies)
        pct=lambda p: ordered[min(len(ordered)-1,int((len(ordered)-1)*p))] if ordered else 0
        return {"ram_used_mb":round((self.cache_bytes+sum(sum(len(row)*2 for row in x) for x in self.hot.values()))/1048576,3),"cache_hit_rate":self.cache_hits/max(1,self.cache_hits+self.pages_loaded),"pages_loaded_per_query":self.pages_loaded/max(1,len(self.latencies)),"retrieval_p50_ms":pct(.5),"retrieval_p95_ms":pct(.95),"pages_loaded":self.pages_loaded}

def build_index(rows, embedder, output: Path, version: str, hot_per_class=16, neighbours=3):
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    grouped=defaultdict(list)
    for row in rows: grouped[row["emotion"]].append(row)
    shards={}; centroids={}; vectors_by_class={}
    for label, items in grouped.items():
        vectors=embedder.encode([x["text"] for x in items]); vectors_by_class[label]=vectors
        _save_vectors(output/f"{label}.f16",vectors)
        metadata=[{k:x.get(k) for k in ("dataset_id","item_id","emotion","level","intent")} for x in items]
        (output/f"{label}.json").write_text(json.dumps(metadata),encoding="utf-8")
        centroids[label]=[sum(row[i] for row in vectors)/len(vectors) for i in range(len(vectors[0]))]; shards[label]={"vectors":f"{label}.f16","metadata":f"{label}.json","count":len(items),"hot":len(items)<=hot_per_class}
    centroid_arrays={k:[x/_norm(v) for x in v] if _norm(v) else v for k,v in centroids.items()}
    for key,value in centroid_arrays.items(): _save_vectors(output/f"centroid-{key}.f16",[value])
    graph={key:sorted((other for other in centroid_arrays if other!=key),key=lambda o:_dot(centroid_arrays[key],centroid_arrays[o]),reverse=True)[:neighbours] for key in centroid_arrays}
    (output/"neighbours.json").write_text(json.dumps(graph),encoding="utf-8")
    import hashlib
    checksum=hashlib.sha256("".join(sorted(x["item_id"] for x in rows)).encode()).hexdigest()
    manifest={"version":version,"count":len(rows),"embed_model":getattr(embedder,"model_name","hashing-n-gram-v1"),"built_at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"checksum":checksum,"dataset_ids":sorted({x["dataset_id"] for x in rows}),"tiers":sorted({x.get("tier","A") for x in rows}),"centroids":{k:f"centroid-{k}.f16" for k in centroid_arrays},"shards":shards}
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8"); return manifest
