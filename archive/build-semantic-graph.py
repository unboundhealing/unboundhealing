import json
import os
import re

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

INPUT_FILE = os.path.join(ROOT, "content-graph.json")
OUTPUT_FILE = os.path.join(ROOT, "semantic-graph.json")

STOP = {
    "this","that","just","about","here",
    "like","thing","things","or","and",
    "the","a","an","to","of","in","on"
}

MAX_CONCEPTS_PER_EDGE = 12

def normalize(c):
    if not c:
        return None

    c = str(c).strip().lower()

    if c in STOP or len(c) < 2:
        return None

    c = re.sub(r"[^a-z0-9\- ]+", "", c)
    return c.strip() or None


def extract_fallback(edge):
    concepts = []

    for part in [edge.get("from", ""), edge.get("to", "")]:
        if part:
            concepts.extend(part.replace(".html", "").split("/"))

    return [normalize(c) for c in concepts if normalize(c)]


with open(INPUT_FILE, "r", encoding="utf-8") as f:
    raw = json.load(f)

edges = raw.get("edges", [])
output_edges = []

for e in edges:

    src = e.get("from")
    tgt = e.get("to")

    if not src or not tgt:
        continue

    concepts = e.get("shared_concepts") or extract_fallback(e)

    cleaned = []
    seen = set()

    for c in concepts:
        c = normalize(c)
        if not c or c in seen:
            continue
        seen.add(c)
        cleaned.append(c)

    cleaned = cleaned[:MAX_CONCEPTS_PER_EDGE]

    if not cleaned:
        continue

    output_edges.append({
        "from": src,
        "to": tgt,
        "weight": float(e.get("weight", 1.0)),
        "shared_concepts": cleaned
    })

if not output_edges:
    output_edges = [{
        "from": "__system__",
        "to": "__system__",
        "weight": 1.0,
        "shared_concepts": ["system"]
    }]

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump({"edges": output_edges}, f, indent=2, ensure_ascii=False)

print("🧭 semantic graph built")
print("📦 edges:", len(output_edges))
