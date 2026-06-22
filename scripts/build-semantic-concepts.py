import json
import os
import re
from collections import defaultdict, Counter

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

GRAPH_FILE = os.path.join(ROOT, "semantic-graph.json")
OUTPUT_FILE = os.path.join(ROOT, "semantic-concepts.json")


STOP_CONCEPTS = {
    "this","that","these","those","just","about","here","there",
    "thing","things","like","okay","ok","really","very","still"
}

def clean(c):
    if not c:
        return None
    c = c.strip().lower()
    c = re.sub(r"[^a-z0-9\-]", "", c)
    return c if c else None


with open(GRAPH_FILE, "r", encoding="utf-8") as f:
    graph = json.load(f).get("edges", [])

concept_freq = Counter()
concept_pages = defaultdict(set)

for e in graph:
    concepts = e.get("shared_concepts", [])
    url = e.get("to")

    for c in concepts:
        c = clean(c)
        if not c or c in STOP_CONCEPTS:
            continue

        concept_freq[c] += 1
        concept_pages[c].add(url)


N = max(1, len(graph))

concepts = {}

for c, freq in concept_freq.items():
    # IDF-style weighting
    idf = max(0.2, (1.0 + (N / (1 + freq))) ** 0.35)

    concepts[c] = {
        "frequency": freq,
        "idf_weight": round(idf, 4),
        "pages": list(concept_pages[c])
    }

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(concepts, f, indent=2)

print("🌱 Semantic concepts built (v4.0 Phase 6 upgraded)")
print("📦 Concepts:", len(concepts))
