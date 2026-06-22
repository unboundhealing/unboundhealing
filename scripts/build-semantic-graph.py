import json
import os
from collections import defaultdict

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

INPUT_FILE = os.path.join(ROOT, "content-graph.json")
OUTPUT_FILE = os.path.join(ROOT, "semantic-graph.json")

# =========================================================
# CONFIG (gravity-native constraints)
# =========================================================

STOP = {
    "this", "that", "just", "about", "here",
    "like", "thing", "things", "or", "and",
    "the", "a", "an", "to", "of", "in", "on"
}

MAX_CONCEPTS_PER_EDGE = 10
MIN_CONCEPT_LENGTH = 3
MAX_WEIGHT = 5.0

# =========================================================
# NORMALIZATION
# =========================================================

def normalize(c):
    if not c:
        return None

    c = str(c).strip().lower()

    if c in STOP:
        return None

    if len(c) < MIN_CONCEPT_LENGTH:
        return None

    if any(ch.isdigit() for ch in c):
        return None

    return c


# =========================================================
# FALLBACK CONCEPT EXTRACTION (STRONGER)
# =========================================================

def extract_fallback_concepts(edge):
    """
    Gravity-native fallback:
    pulls from ALL weak semantic hints instead of just tags.
    """
    candidates = []

    # tags
    tags = edge.get("tags") or []
    if isinstance(tags, str):
        tags = tags.replace(",", " ").split()

    candidates.extend(tags)

    # url-derived signals
    for field in ["from", "to"]:
        url = edge.get(field, "")
        if url:
            parts = url.split("/")
            candidates.extend(parts[-3:])

    return [normalize(t) for t in candidates if normalize(t)]


# =========================================================
# LOAD
# =========================================================

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    raw = json.load(f)

raw_edges = raw.get("edges", [])

edges_out = []

# =========================================================
# BUILD (GRAVITY PROJECTION LAYER)
# =========================================================

for e in raw_edges:

    source = e.get("from")
    target = e.get("to")

    if not source or not target:
        continue

    weight = float(e.get("weight", 1))
    weight = min(weight, MAX_WEIGHT)

    concepts = e.get("shared_concepts") or []

    if not concepts:
        concepts = extract_fallback_concepts(e)

    concepts = [normalize(c) for c in concepts]
    concepts = [c for c in concepts if c]

    # deduplicate but preserve order
    seen = set()
    cleaned = []
    for c in concepts:
        if c not in seen:
            cleaned.append(c)
            seen.add(c)

    if not cleaned:
        continue

    cleaned = cleaned[:MAX_CONCEPTS_PER_EDGE]

    edges_out.append({
        "from": source,
        "to": target,
        "weight": weight,
        "shared_concepts": cleaned
    })


# =========================================================
# GUARANTEE (but NOT polluting signal space)
# =========================================================

if not edges_out:
    edges_out = [{
        "from": "__system__",
        "to": "__system__",
        "weight": 1.0,
        "shared_concepts": ["system", "fallback"]
    }]

# =========================================================
# SAVE
# =========================================================

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump({"edges": edges_out}, f, indent=2, ensure_ascii=False)

print("🧭 Semantic graph built (v4.3 gravity-native projection)")
print("📦 edges:", len(edges_out))
