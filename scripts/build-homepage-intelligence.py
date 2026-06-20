import json
from collections import defaultdict, Counter
import os
import re

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

GRAPH_FILE = os.path.join(ROOT, "semantic-graph.json")
CLUSTERS_FILE = os.path.join(ROOT, "concept-clusters.json")
OUTPUT = os.path.join(ROOT, "homepage-intelligence.json")

# -----------------------------
# Load data
# -----------------------------
with open(GRAPH_FILE, "r", encoding="utf-8") as f:
    graph = json.load(f)["edges"]

with open(CLUSTERS_FILE, "r", encoding="utf-8") as f:
    clusters = json.load(f)

# -----------------------------
# Step 1 — STOP SYSTEM (upgraded)
# -----------------------------
HARD_STOP = {
    "that", "these", "those",
    "and", "or", "but",
    "the", "a", "an",
    "to", "of", "in", "on", "for",
    "unbound"
}

SOFT_STOP = {
    "about", "page", "post", "opening"
}

SEMANTIC_NOISE = {
    "it", "its", "they", "them",
    "here", "there",
    "thing", "things",
    "something", "anything"
}

def is_noise_concept(word: str) -> bool:
    w = word.strip().lower()

    if w in HARD_STOP:
        return True

    if w in SOFT_STOP:
        return True

    if w in SEMANTIC_NOISE:
        return True

    if len(w) < 3:
        return True

    return False

# -----------------------------
# Step 2 — Concept normalization (phrase cleanup)
# -----------------------------
def normalize_concept(word: str) -> str:
    """
    Clean concept strings into stable nodes
    """
    word = word.strip().lower()
    word = re.sub(r"-+", "-", word)   # collapse hyphens
    word = re.sub(r"\s+", " ", word)  # collapse whitespace
    return word

# -----------------------------
# Step 3 — Node importance (semantic salience)
# -----------------------------
scores = Counter()

for edge in graph:
    weight = edge.get("weight", 1)

    # basic centrality signal
    scores[edge["from"]] += weight
    scores[edge["to"]] += weight

def compute_salience(node: str, raw_score: float) -> float:
    """
    Convert raw graph weight into semantic salience (0–1)
    """

    base = raw_score

    # mild compression so hubs don't dominate
    base = base ** 0.85

    # normalization
    return min(1.0, base / 10.0)

# Build featured pages (salience-ranked nodes)
featured_pages = []

for node, score in scores.most_common(50):
    if is_noise_concept(node):
        continue

    clean = normalize_concept(node)

    featured_pages.append({
        "url": node,
        "score": compute_salience(clean, score)
    })

# sort by salience (not raw frequency anymore)
featured_pages.sort(key=lambda x: x["score"], reverse=True)

# -----------------------------
# Step 4 — Cluster scoring (salience-aware)
# -----------------------------
cluster_scores = []
clean_clusters = {}

for concept, pages in clusters.items():

    concept_clean = normalize_concept(concept)

    # filter noise concepts
    if is_noise_concept(concept_clean):
        continue

    clean_clusters[concept_clean] = pages

    # salience = size + weak semantic proxy
    size = len(pages)

    salience = min(1.0, (size * 0.1))

    cluster_scores.append({
        "concept": concept_clean,
        "salience": salience,
        "size": size
    })

# sort by salience (NOT size anymore)
cluster_scores.sort(key=lambda x: x["salience"], reverse=True)

def select_top_clusters(clusters, limit=3):
    return [
        c for c in clusters
        if c["salience"] > 0.25
    ][:limit]

top_concepts = select_top_clusters(cluster_scores, 3)

# -----------------------------
# Build output (homepage intelligence layer)
# -----------------------------
output = {
    "featured_pages": featured_pages[:3],
    "concept_clusters": top_concepts
}

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print("🏠 Homepage intelligence built (v3.4 Phase 4 — semantic salience system)")
