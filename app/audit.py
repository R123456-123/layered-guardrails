import json, time, hashlib
from pathlib import Path

def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]

def write_audit(record: dict, path="logs/audit.jsonl"):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), **record}, default=str) + "\n")