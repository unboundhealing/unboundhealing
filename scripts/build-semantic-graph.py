import json
import os
from collections import defaultdict

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

INPUT_FILE = os.path.join(ROOT, "content-graph.json")
OUTPUT_FILE = os.path.join(ROOT, "semantic-graph.json")

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------

STOP = {
    "this", "that", "just", "about", "here",
    "like", "thing", "things", "or", "and"
}

MAX_CONCEPTS_PER_EDGE = 8
MAX_WEIGHT = 5.0

# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def normalize(c):
    if not c:
        return None
    c = str(c).strip().lower()
    if not c or c in STOP:
        return None
    if len(c) < 2:
        return None
    return c


def extract_fallback_concepts(edge):
    """
    Safety net:
    If shared_concepts is missing or empty,
    try tags if they exist in upstream structure.
    """
    tags = edge.get("tags") or []
    if isinstance(tags, str):
        tags = tags.replace(",", " ").split()

    return [normalize(t) for t in tags if normalize(t)]


# ---------------------------------------------------------
# LOAD
# ---------------------------------------------------------

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    raw = json.load(f)

raw_edges = raw.get("edges", [])

edges_out = []

# ---------------------------------------------------------
# BUILD
# ---------------------------------------------------------

for e in raw_edges:

    source = e.get("from")
    target = e.get("to")
    weight = float(e.get("weight", 1))

    if not source or not target:
        continue

    concepts = e.get("shared_concepts")

    # fallback if missing or empty
    if not concepts:
        concepts = extract_fallback_concepts(e)

    if not concepts:
        continue

    concepts = [normalize(c) for c in concepts]
    concepts = [c for c in concepts if c]

    if len(concepts) < 1:
        continue

    # cap explosion
    concepts = concepts[:MAX_CONCEPTS_PER_EDGE]

    # clamp weight
    weight = min(weight, MAX_WEIGHT)

    edges_out.append({
        "from": source,
        "to": target,
        "weight": weight,
        "shared_concepts": concepts
    })


# ---------------------------------------------------------
# GUARANTEE NON-EMPTY OUTPUT SAFETY
# ---------------------------------------------------------

if len(edges_out) == 0:
    print("⚠️ WARNING: semantic graph empty — injecting safe fallback structure")

    edges_out = [{
        "from": "__system__",
        "to": "__system__",
        "weight": 1,
        "shared_concepts": ["system", "fallback"]
    }]


# ---------------------------------------------------------
# SAVE
# ---------------------------------------------------------

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump({"edges": edges_out}, f, indent=2, ensure_ascii=False)

print("🧭 Semantic graph built (v4.2 hardened)")
print("📦 edges:", len(edges_out))
