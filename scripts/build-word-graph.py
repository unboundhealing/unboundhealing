import json
import os
from collections import defaultdict

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

INPUT = os.path.join(ROOT, "semantic-words.json")
OUTPUT = os.path.join(ROOT, "word-graph.json")

# -----------------------------
# Load semantic words
# -----------------------------
with open(INPUT, "r", encoding="utf-8") as f:
    data = json.load(f)["pages"]

# -----------------------------
# Group pages by word
# -----------------------------
word_to_pages = defaultdict(list)

for item in data:
    word_to_pages[item["word"]].append(item["url"])

words = list(word_to_pages.keys())

edges = []

# -----------------------------
# Build relationships
# -----------------------------
for i, w1 in enumerate(words):
    for w2 in words[i+1:]:

        pages1 = set(word_to_pages[w1])
        pages2 = set(word_to_pages[w2])

        # simple overlap signal (v3.3 Phase 2 baseline logic)
        overlap = len(pages1 & pages2)

        # heuristic similarity boost
        shared_prefix = 1 if w1[:3] == w2[:3] else 0

        weight = (overlap * 0.6) + (shared_prefix * 0.3)

        if weight > 0:
            edges.append({
                "from": w1,
                "to": w2,
                "weight": round(weight, 2),
                "reason": "semantic_overlap"
            })

# -----------------------------
# Write graph
# -----------------------------
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump({
        "edges": edges
    }, f, indent=2)

print("🧭 Word graph built (v3.3 Phase 2)")
print(f"📦 Wrote: {OUTPUT}")
