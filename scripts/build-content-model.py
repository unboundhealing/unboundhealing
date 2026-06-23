import json
import os
from collections import Counter, defaultdict

# =========================================================
# ROOT / SINGLE TRUTH SOURCE
# =========================================================

ROOT_DIR = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

SALIENCE_FILE = os.path.join(ROOT_DIR, "semantic-salience.json")
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


semantic = safe_load(SALIENCE_FILE)

if not semantic:
    print("❌ semantic-salience.json missing or unreadable")
    semantic = {"nodes": [], "edges": []}

# =========================================================
# SINGLE SOURCE EXTRACTION
# =========================================================
# semantic-salience is the ONLY authority

nodes = semantic.get("nodes", {})
edges = semantic.get("edges", [])

# =========================================================
# NORMALIZATION (light, defensive only)
# =========================================================

def normalize_concept(c):
    if not c:
        return None

    c = str(c).strip().lower()

    if len(c) < 2:
        return None

    # minimal noise filter (do NOT over-engineer ontology)
    if c in {"and", "or", "the", "a", "an", "of", "to", "in"}:
        return None

    return c

# =========================================================
# CONCEPT EXTRACTION (FROM NODES ONLY)
# =========================================================

concept_counter = Counter()
concept_to_pages = defaultdict(set)

node_count = 0

for url, node in nodes.items():
    node_count += 1

    concepts = node.get("concepts", []) or []
    if not isinstance(concepts, list):
        continue

    cleaned = []
    for c in concepts:
        nc = normalize_concept(c)
        if nc:
            cleaned.append(nc)

    # stable dedupe
    cleaned = list(dict.fromkeys(cleaned))

    for c in cleaned:
        concept_counter[c] += 1
        concept_to_pages[c].add(url)

# =========================================================
# EDGE WEIGHT ANALYSIS (DERIVATIVE ONLY)
# =========================================================

edge_count = len(edges)

concept_edges = []

for e in edges:
    a = e.get("a")
    b = e.get("b")

    if not a or not b:
        continue

    # edges are structural only; no concept mining here
    concept_edges.append({
        "a": str(a),
        "b": str(b),
        "weight": float(e.get("weight", 1.0))
    })

# =========================================================
# BUILD CONCEPT INDEX (DERIVATIVE VIEW)
# =========================================================

concepts = []

for concept, freq in concept_counter.items():
    concepts.append({
        "concept": concept,
        "frequency": freq,
        "connected_pages": len(concept_to_pages.get(concept, []))
    })

# deterministic ordering = consumer stability
concepts.sort(key=lambda x: (-x["frequency"], x["concept"]))

# =========================================================
# SAFE FALLBACK (pipeline stability)
# =========================================================

if not concepts:
    print("⚠️ No concepts found in semantic-salience — injecting fallback")

    concepts = [{
        "concept": "system",
        "frequency": 1,
        "connected_pages": 0
    }]

# =========================================================
# DEBUG REPORT
# =========================================================

print("\n🧠 CONTENT MODEL (CONSUMER VIEW)")
print("nodes:", node_count)
print("edges:", edge_count)
print("concepts:", len(concepts))

print("\nTOP 20 CONCEPTS")

for c in concepts[:20]:
    print(f"{c['concept']} → {c['frequency']}")

# =========================================================
# OUTPUT (DERIVED, NOT AUTHORITATIVE)
# =========================================================

output = {
    "source": "semantic-salience-v4",
    "role": "consumer-derived-concept-view",
    "nodes": node_count,
    "edges": edge_count,
    "concepts": concepts,
    "edges_passthrough": concept_edges
}

try:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("\n✅ concept-model written:", OUTPUT_FILE)

except Exception as e:
    print("❌ failed to write concept model:", str(e))

print("🧭 content-model complete (pure consumer of semantic-salience)")
