import json
import os
import re
from collections import Counter

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

GRAPH_FILE = os.path.join(ROOT, "semantic-graph.json")
OUTPUT_FILE = os.path.join(ROOT, "semantic-words.json")

STOP = {
    "this","that","just","about","here","like","thing","things",
    "and","or","but","the","a","an","to","of","in","on"
}

def tokenize(text):
    return re.findall(r"[a-zA-Z]{3,}", text.lower())


with open(GRAPH_FILE, "r", encoding="utf-8") as f:
    edges = json.load(f).get("edges", [])

freq = Counter()

for e in edges:
    for c in e.get("shared_concepts", []):
        if c not in STOP:
            freq[c] += 1

# prune low-signal words
filtered = {
    k: v for k, v in freq.items()
    if v >= 2 and k not in STOP
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(filtered, f, indent=2)

print("🧠 Semantic words built (v4.0 filtered)")
print("📦 words:", len(filtered))
