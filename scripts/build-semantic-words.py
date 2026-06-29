import json
import os
import re
from collections import Counter

# =========================================================
# ROOT / INPUT (TRUTH LAYER ANCHORED)
# =========================================================

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

# IMPORTANT: now anchored directly to semantic-salience
INPUT_FILE = os.path.join(ROOT, "assets/semantic-salience.json")
OUTPUT_FILE = os.path.join(ROOT, "assets/semantic-words.json")

# =========================================================
# STOPWORDS (LEXICAL NOISE FILTER)
# =========================================================

STOP = {
    "this","that","just","about","here","like","thing","things",
    "and","or","but","the","a","an","to","of","in","on",
    "for","with","from","by","as","at","it","is","are"
}

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


data = safe_load(INPUT_FILE)

if not data:
    print("❌ semantic-salience missing — cannot build semantic-words")
    exit(1)

concepts = data.get("concepts", [])

if not concepts:
    print("⚠️ no concepts found in semantic-salience — using fallback")
    concepts = [{"concept": "system", "frequency": 1}]

# =========================================================
# WORD EXTRACTION (PRIMARY SIGNAL: SALIENCE CONCEPTS)
# =========================================================

freq = Counter()

for c in concepts:
    concept = c.get("concept", "")
    weight = c.get("frequency", 1)

    if not concept:
        continue

    concept = concept.lower().strip()

    if concept in STOP:
        continue

    if len(concept) < 2:
        continue

    freq[concept] += int(weight)

# =========================================================
# OPTIONAL SECONDARY SIGNAL (DERIVED STRUCTURE ONLY)
# =========================================================
# We DO NOT treat this as truth — only enrichment signal

edges = data.get("edges", [])

def tokenize_path(text):
    return re.findall(r"[a-zA-Z]{3,}", text.lower())

for e in edges:
    for endpoint in [e.get("from", ""), e.get("to", "")]:
        for t in tokenize_path(endpoint):
            if t not in STOP:
                freq[t] += 1

# =========================================================
# OUTPUT LIMIT (CONTROLLED SURFACE AREA)
# =========================================================

TOP_N = 200

filtered = dict(freq.most_common(TOP_N))

# fallback safety
if not filtered:
    filtered = dict(freq.most_common(10))

# =========================================================
# OUTPUT STRUCTURE (STABLE CONTRACT)
# =========================================================

output = {
    "source": "semantic-salience",
    "mode": "derivative-projection",
    "words": [
        {"word": k, "weight": v}
        for k, v in sorted(filtered.items(), key=lambda x: -x[1])
    ]
}

# =========================================================
# WRITE
# =========================================================

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

# =========================================================
# DEBUG / TRACEABILITY
# =========================================================

print("\n🧠 semantic-words rebuilt (SALIENT SOURCE MODE)")
print("📦 concepts:", len(concepts))
print("📦 words:", len(output["words"]))
print("🔗 edges scanned:", len(edges))

print("\n🧭 TOP WORDS:")
for w in output["words"][:15]:
    print(w["word"], w["weight"])

print("\n✅ semantic-words = PURE DERIVATIVE OF semantic-salience")
