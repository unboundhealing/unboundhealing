import json
import os
import re
from collections import Counter

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

GRAPH_FILE = os.path.join(ROOT, "semantic-graph.json")
OUTPUT_FILE = os.path.join(ROOT, "semantic-words.json")

STOP = {
    "this","that","just","about","here","like","thing","things",
    "and","or","but","the","a","an","to","of","in","on",
    "for","with","from","by","as","at","it","is","are"
}

def clean(endpoint):
    return re.findall(r"[a-zA-Z]{3,}", endpoint.lower())


with open(GRAPH_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

edges = data.get("edges", [])

freq = Counter()

for e in edges:

    for c in e.get("shared_concepts", []):
        c = c.lower().strip()
        if c and c not in STOP:
            freq[c] += 2

    for endpoint in [e.get("from", ""), e.get("to", "")]:
        for t in clean(endpoint):
            if t not in STOP:
                freq[t] += 1

# IMPORTANT FIX: no aggressive threshold collapse
filtered = dict(freq.most_common(200))

if not filtered:
    filtered = dict(freq.most_common(10))

output = {
    "words": [
        {"word": k, "weight": v}
        for k, v in sorted(filtered.items(), key=lambda x: -x[1])
    ]
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print("🧠 semantic words built")
print("📦 words:", len(output["words"]))
