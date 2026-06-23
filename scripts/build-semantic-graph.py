import json
import os
import re
from collections import defaultdict

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

MAX_CONCEPTS_PER_EDGE = 12
MIN_LEN = 2
MAX_WEIGHT = 5.0

# =========================================================
# NORMALIZATION (LESS AGGRESSIVE = FIXED CORE ISSUE)
# =========================================================

def normalize(c):
    if c is None:
        return None

    c = str(c).strip().lower()

    if not c:
        return None

    if c in STOP:
        return None

    if len(c) < MIN_LEN:
        return None

    # allow numbers (important for real-world tags)
    c = re.sub(r"[^a-z0-9\- ]+", "", c)

    if not c.strip():
        return None

    return c.strip()

# =========================================================
# FALLBACK EXTRACTION (FIXED: NOW ACTUALLY USES PAGE DATA)
# =========================================================

def extract_fallback(edge):
    """
    IMPORTANT FIX:
    content-graph edges do NOT reliably contain tags,
    so we derive weak concepts from structural metadata.
    """

    concepts = []

    # URL/path signals (VERY IMPORTANT SIGNAL YOU WERE LOSING)
    src = edge.get("from", "")
    tgt = edge.get("to", "")

    for part in [src, tgt]:
        if part:
            concepts.extend(part.replace(".html", "").split("/"))

    # optional tags if present
    tags = edge.get("tags") or []
    if isinstance(tags, str):
        tags = re.split(r"[,\s]+", tags)

    concepts.extend(tags)

    return [normalize(c) for c in concepts if normalize(c)]

# =========================================================
# LOAD CONTENT GRAPH
# =========================================================

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    raw = json.load(f)

edges = raw.get("edges", [])
output_edges = []

# =========================================================
# METRICS
# =========================================================

dropped_no_concepts = 0
dropped_missing_nodes = 0

# =========================================================
# CORE TRANSFORMATION
# =========================================================

for e in edges:

    src = e.get("from")
    tgt = e.get("to")

    if not src or not tgt:
        dropped_missing_nodes += 1
        continue

    weight = min(float(e.get("weight", 1)), MAX_WEIGHT)

    concepts = e.get("shared_concepts")

    # FIX: always fallback if missing OR empty
    if not concepts:
        concepts = extract_fallback(e)

    # normalize
    cleaned = []
    seen = set()

    for c in concepts:
        c = normalize(c)
        if not c:
            continue
        if c in seen:
            continue
        seen.add(c)
        cleaned.append(c)

    cleaned = cleaned[:MAX_CONCEPTS_PER_EDGE]

    if not cleaned:
        dropped_no_concepts += 1
        continue

    output_edges.append({
        "from": src,
        "to": tgt,
        "weight": weight,
        "shared_concepts": cleaned
    })

# =========================================================
# DEBUG REPORT
# =========================================================

print("\n🧪 SEMANTIC GRAPH DEBUG")
print("input edges:", len(edges))
print("valid edges:", len(output_edges))
print("dropped (no nodes):", dropped_missing_nodes)
print("dropped (no concepts):", dropped_no_concepts)

# =========================================================
# GUARANTEED MINIMUM GRAPH (CRITICAL FIX)
# =========================================================

if len(output_edges) == 0:
    print("⚠️ WARNING: no valid semantic edges found")
    print("🧱 injecting structural fallback graph (non-fatal)")

    output_edges = [
        {
            "from": "__system__",
            "to": "__system__",
            "weight": 1.0,
            "shared_concepts": ["system", "fallback"]
        }
    ]

# =========================================================
# SAVE
# =========================================================

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump({"edges": output_edges}, f, indent=2, ensure_ascii=False)

print("🧭 Semantic graph built (v5 resilient projection)")
print("📦 edges:", len(output_edges))
