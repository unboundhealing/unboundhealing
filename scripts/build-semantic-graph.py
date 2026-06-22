import json
import os

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

INPUT_FILE = os.path.join(ROOT, "content-graph.json")
OUTPUT_FILE = os.path.join(ROOT, "semantic-graph.json")

# =========================================================
# CONFIG
# =========================================================

STOP = {
    "this", "that", "just", "about", "here",
    "like", "thing", "things", "or", "and",
    "the", "a", "an", "to", "of", "in", "on"
}

MAX_CONCEPTS_PER_EDGE = 10
MIN_LEN = 3
MAX_WEIGHT = 5.0

# =========================================================
# NORMALIZATION (PURE FILTER ONLY)
# =========================================================

def normalize(c):
    if not c:
        return None

    c = str(c).strip().lower()

    if c in STOP:
        return None

    if len(c) < MIN_LEN:
        return None

    if any(ch.isdigit() for ch in c):
        return None

    return c

# =========================================================
# FALLBACK EXTRACTION (NON-INTERPRETIVE)
# =========================================================

def extract_fallback(edge):
    tags = edge.get("tags") or []

    if isinstance(tags, str):
        tags = tags.replace(",", " ").split()

    return [normalize(t) for t in tags if normalize(t)]

# =========================================================
# LOAD
# =========================================================

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    raw = json.load(f)

edges = raw.get("edges", [])
output_edges = []

# =========================================================
# PROJECTION ONLY (NO SEMANTIC AUTHORITY)
# =========================================================

for e in edges:

    src = e.get("from")
    tgt = e.get("to")

    if not src or not tgt:
        continue

    weight = min(float(e.get("weight", 1)), MAX_WEIGHT)

    concepts = e.get("shared_concepts") or extract_fallback(e)

    concepts = [normalize(c) for c in concepts]
    concepts = [c for c in concepts if c]

    seen = set()
    cleaned = []

    for c in concepts:
        if c not in seen:
            cleaned.append(c)
            seen.add(c)

    if not cleaned:
        continue

    cleaned = cleaned[:MAX_CONCEPTS_PER_EDGE]

    output_edges.append({
        "from": src,
        "to": tgt,
        "weight": weight,
        "shared_concepts": cleaned
    })

# =========================================================
# SAFE FALLBACK (STRUCTURAL ONLY, NOT SEMANTIC)
# =========================================================

if not output_edges:
    output_edges = [{
        "from": "__system__",
        "to": "__system__",
        "weight": 1.0,
        "shared_concepts": ["system", "fallback"]
    }]

# =========================================================
# SAVE
# =========================================================

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump({"edges": output_edges}, f, indent=2, ensure_ascii=False)

print("🧭 Semantic graph built (v4.4 projection-only)")
print("📦 edges:", len(output_edges))
