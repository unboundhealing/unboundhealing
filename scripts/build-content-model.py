import json
import os
from collections import Counter, defaultdict

# =========================================================
# CONFIG / PATHS
# =========================================================

ROOT_DIR = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

INPUT_FILE = os.path.join(ROOT_DIR, "content-graph.json")
OUTPUT_FILE = os.path.join(ROOT_DIR, "concept-model.json")

# =========================================================
# SAFE LOAD
# =========================================================

def safe_load(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

raw = safe_load(INPUT_FILE)

if not raw:
    print("⚠️ content-graph missing or unreadable")
    raw = {"nodes": [], "edges": []}

edges = raw.get("edges") or []
nodes = raw.get("nodes") or []

# =========================================================
# NORMALIZATION
# =========================================================

def normalize_concept(c):
    if not c:
        return None

    c = str(c).strip().lower()

    # hard filters
    if len(c) < 2:
        return None

    if c in {"and", "or", "the", "a", "an"}:
        return None

    if any(ch.isdigit() for ch in c):
        return None

    return c

# =========================================================
# CONCEPT EXTRACTION
# =========================================================

concept_counter = Counter()
concept_to_pages = defaultdict(set)
concept_edges = []

valid_edge_count = 0
dropped_edge_count = 0

for e in edges:
    src = e.get("from")
    tgt = e.get("to")

    if not src or not tgt:
        dropped_edge_count += 1
        continue

    concepts = e.get("shared_concepts") or []

    if not isinstance(concepts, list):
        concepts = []

    cleaned = []
    for c in concepts:
        nc = normalize_concept(c)
        if nc:
            cleaned.append(nc)

    cleaned = list(dict.fromkeys(cleaned))  # dedupe stable

    if not cleaned:
        dropped_edge_count += 1
        continue

    valid_edge_count += 1

    # update stats
    for c in cleaned:
        concept_counter[c] += 1
        concept_to_pages[c].add(src)
        concept_to_pages[c].add(tgt)

    concept_edges.append({
        "from": src,
        "to": tgt,
        "concepts": cleaned,
        "weight": float(e.get("weight", 1.0))
    })

# =========================================================
# BUILD CONCEPT NODES
# =========================================================

concepts = []

for concept, count in concept_counter.items():

    concepts.append({
        "concept": concept,
        "frequency": count,
        "connected_pages": len(concept_to_pages.get(concept, []))
    })

# stable sort (important for deterministic salience)
concepts.sort(key=lambda x: (-x["frequency"], x["concept"]))

# =========================================================
# SAFE FALLBACK (CRITICAL FOR PIPELINE STABILITY)
# =========================================================

if not concepts:
    print("⚠️ no concepts detected — injecting fallback layer")

    concepts = [{
        "concept": "system",
        "frequency": 1,
        "connected_pages": 0
    }]

    concept_edges = []

# =========================================================
# DEBUG REPORT
# =========================================================

print("\n🧠 CONCEPT MODEL DEBUG")
print("edges input:", len(edges))
print("edges valid:", valid_edge_count)
print("edges dropped:", dropped_edge_count)

print("concepts:", len(concepts))
print("unique concepts:", len(concept_counter))

print("\nTOP 20 CONCEPTS")

for c in concepts[:20]:
    print(c["concept"], c["frequency"])

# =========================================================
# OUTPUT
# =========================================================

output = {
    "concepts": concepts,
    "edges": concept_edges
}

try:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("\n✅ concept model written:", OUTPUT_FILE)

except Exception as e:
    print("❌ failed to write concept model:", str(e))

# =========================================================
# PIPELINE SAFETY SIGNAL
# =========================================================

print("🧭 concept-model pipeline complete (derivative layer, non-authoritative)")
