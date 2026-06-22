import json
import os
from collections import defaultdict

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

INPUT = os.path.join(ROOT, "semantic-words.json")
OUTPUT = os.path.join(ROOT, "word-graph.json")

# -----------------------------
# LOAD SAFE
# -----------------------------
with open(INPUT, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------------------------------------
# SCHEMA SAFETY (FIXES YOUR CRASH)
# ---------------------------------------
pages = None

if isinstance(data, dict):
    if "pages" in data:
        pages = data["pages"]
    elif "words" in data:
        pages = data["words"]
    elif "items" in data:
        pages = data["items"]

if pages is None:
    print("❌ ERROR: No valid data structure found in semantic-words.json")
    print("🔍 Keys:", list(data.keys()) if isinstance(data, dict) else type(data))
    pages = []

# -----------------------------
# GROUP WORDS → PAGES
# -----------------------------
word_to_pages = defaultdict(list)

for item in pages:
    if not isinstance(item, dict):
        continue

    word = item.get("word")
    url = item.get("url")

    if not word or not url:
        continue

    word_to_pages[word].append(url)

words = list(word_to_pages.keys())

edges = []

# -----------------------------
# BUILD RELATIONSHIPS
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

# -----------------------------
# WRITE OUTPUT
# -----------------------------
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump({
        "edges": edges
    }, f, indent=2, ensure_ascii=False)

print("🧭 Word graph built (v3.4 schema-safe)")
print(f"📦 Wrote: {OUTPUT}")
