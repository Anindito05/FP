"""Build governed local vector shards; restricted corpora are never fetched."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.config import get_settings
from app.ml.embedder import load_embedder
from app.ml.index_store import build_index
from app.ml.levels import RISK_LABEL_TO_LEVEL, DATASET_LABEL_MAPPINGS
import yaml

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--manifest",default="data/datasets.yaml");parser.add_argument("--version",default=None);parser.add_argument("--synthetic",action="store_true");args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]; manifest=yaml.safe_load((root/args.manifest).read_text(encoding="utf-8")); settings=get_settings(); rows=[]
    if args.synthetic:
        fixture=root/"tests/fixtures/synthetic_classification.jsonl"
        rows=[json.loads(line) for line in fixture.read_text(encoding="utf-8").splitlines() if line.strip()]
    else:
        for entry in manifest.get("datasets",[]):
            if not entry.get("enabled"): continue
            tier=entry.get("validity_tier")
            if tier=="C" or not entry.get("verified_by_human"):
                raise SystemExit(f"Refusing dataset {entry['id']}: Tier C or not human verified")
            if tier=="A" and ("TODO_VERIFY" in str(entry) or not entry.get("citation")):
                raise SystemExit(f"Refusing dataset {entry['id']}: manifest contains TODO_VERIFY")
            if tier=="B" and not settings.allow_peer_reviewed_non_clinical:
                print(f"Skipping Tier B dataset {entry['id']}; ALLOW_PEER_REVIEWED_NON_CLINICAL=false");continue
            if tier not in {"A","B"}: raise SystemExit(f"Refusing dataset {entry['id']}: validity tier {tier!r} is not indexable")
            data=root/entry["local_path"]
            files=list(data.glob("*.jsonl")) if data.is_dir() else []
            for file in files:
                for line in file.read_text(encoding="utf-8").splitlines():
                    obj=json.loads(line); label=str(obj.get("label",obj.get("risk_label","none"))).lower()
                    emotion=str(obj.get("emotion",obj.get("emotion_label","other"))).lower()
                    mapping=DATASET_LABEL_MAPPINGS.get(entry["id"],RISK_LABEL_TO_LEVEL)
                    level=obj.get("level",mapping.get(label) if tier=="A" else None)
                    rows.append({"dataset_id":entry["id"],"item_id":str(obj.get("id",obj.get("item_id",""))),"text":str(obj["text"]),"emotion":emotion,"level":level,"intent":obj.get("intent"),"tier":tier})
    if not rows: raise SystemExit("No governed data available. Add verified data or pass --synthetic for a demo index.")
    version=args.version or settings.index_version
    output=Path(settings.index_dir)/version
    if not output.is_absolute(): output=root/output
    emb=load_embedder(settings.embed_model)
    built=build_index(rows,emb,output,version)
    print(f"Built {built['count']} labeled examples at {output}; datasets={','.join(built['dataset_ids'])}; tier={','.join(built['tiers'])}")
if __name__=="__main__": main()
