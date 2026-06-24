import json
import os
from collections import defaultdict

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

INPUT = os.path.join(ROOT, "semantic-words.json")
OUTPUT = os.path.join(ROOT, "word-graph.json")

with open(INPUT, "r", encoding="utf-8") as f:
    data = json.load(f)

# -----------------------------
# NORMALIZE INPUT SAFELY
# -----------------------------
if isinstance(data, dict):
    if "pages" in data:
        items = data["pages"]
    elif "words" in data:
        items = data["words"]
    else:
        # fallback: try flatten
        items = []
        for k, v in data.items():
            if isinstance(v, list):
                items.extend(v)
else:
    items = data if isinstance(data, list) else []

if not items:
    print("❌ ERROR: No valid data structure found in semantic-words.json")
    print("🔍 Keys:", list(data.keys()) if isinstance(data, dict) else "NOT DICT")
    raise SystemExit(1)

# -----------------------------
# Group pages by word
# -----------------------------
word_to_pages = defaultdict(list)

for item in items:
    if not isinstance(item, dict):
        continue
    word = item.get("word")
    url = item.get("url")

    if word and url:
        word_to_pages[word].append(url)

words = list(word_to_pages.keys())

edges = []

# -----------------------------
# Build relationships
# -----------------------------
for i, w1 in enumerate(words):
    for w2 in words[i+1:]:

        pages1 = set(word_to_pages[w1])
        pages2 = set(word_to_pages[w2])

        overlap = len(pages1 & pages2)
        shared_prefix = 1 if w1[:3] == w2[:3] else 0

        weight = (overlap * 0.6) + (shared_prefix * 0.3)

        if weight > 0:
            edges.append({
                "from": w1,
                "to": w2,
                "weight": round(weight, 2),
                "reason": "semantic_overlap"
            })

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump({
        "edges": edges
    }, f, indent=2)

print("🧭 Word graph built (safe v3.4)")
print(f"📦 Wrote: {OUTPUT}")
