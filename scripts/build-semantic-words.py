import json
import os
import re
from collections import Counter, defaultdict

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

GRAPH_FILE = os.path.join(ROOT, "semantic-graph.json")
OUTPUT_FILE = os.path.join(ROOT, "semantic-words.json")

STOP = {
    "this","that","just","about","here","like","thing","things",
    "and","or","but","the","a","an","to","of","in","on",
    "for","with","from","by","as","at","it","is","are"
}

def clean(text):
    return re.findall(r"[a-zA-Z]{3,}", text.lower())

# -----------------------------
# LOAD GRAPH
# -----------------------------
with open(GRAPH_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

edges = data.get("edges", [])

# -----------------------------
# BUILD WORD SIGNALS
# -----------------------------
freq = Counter()

for e in edges:

    # PRIMARY SIGNAL: shared concepts
    for c in e.get("shared_concepts", []):
        c = c.lower().strip()
        if c and c not in STOP:
            freq[c] += 2  # weighted stronger

    # SECONDARY SIGNAL: endpoint URLs (fallback entropy source)
    for endpoint in [e.get("from", ""), e.get("to", "")]:
        tokens = clean(endpoint)
        for t in tokens:
            if t not in STOP:
                freq[t] += 1

# -----------------------------
# ADAPTIVE THRESHOLDING
# -----------------------------
if freq:
    max_freq = max(freq.values())
    threshold = max(1, max_freq * 0.15)  # adaptive floor
else:
    threshold = 999999

filtered = {
    k: v for k, v in freq.items()
    if v >= threshold and k not in STOP
}

# -----------------------------
# GUARANTEE NON-EMPTY OUTPUT
# -----------------------------
if not filtered:
    print("⚠️ WARNING: semantic words collapsed — applying safe fallback")

    # fallback: top raw frequency words
    filtered = dict(freq.most_common(10))

# -----------------------------
# STRUCTURED OUTPUT (CRITICAL FIX)
# -----------------------------
output = {
    "words": [
        {"word": k, "weight": v}
        for k, v in sorted(filtered.items(), key=lambda x: -x[1])
    ]
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print("🧠 Semantic words built (v4.1 hardened)")
print("📦 words:", len(output["words"]))
