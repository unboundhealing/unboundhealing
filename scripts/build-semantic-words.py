import json
import os
import re
from collections import defaultdict

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

INPUT_INDEX = os.path.join(ROOT, "search-index.json")
OUTPUT = os.path.join(ROOT, "semantic-words.json")

# -----------------------------
# Load search index
# -----------------------------
with open(INPUT_INDEX, "r", encoding="utf-8") as f:
    index = json.load(f)

results = []

# -----------------------------
# Helper: extract clean word
# -----------------------------
def extract_word(title, url):
    """
    Priority:
    1. URL slug
    2. title dominant noun
    3. fallback: first meaningful token
    """

    # URL-based signal
    slug = url.rstrip("/").split("/")[-1]
    if slug:
        return slug.lower()

    # Title-based fallback
    if title:
        clean = re.sub(r"[^a-zA-Z\s]", "", title).strip().lower()
        words = clean.split()
        if words:
            return words[0]

    return "unknown"

# -----------------------------
# Build semantic words
# -----------------------------
for url, data in index.items():

    title = data.get("title", "")
    url_lower = url.lower()

    word = extract_word(title, url)

    signals = []

    if word in url_lower:
        signals.append("url_match")

    if word in title.lower():
        signals.append("title_match")

    confidence = 0.5 + (0.2 * len(signals))

    results.append({
        "url": url,
        "word": word,
        "confidence": round(min(confidence, 0.95), 2),
        "signals": signals
    })

# -----------------------------
# Write output
# -----------------------------
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump({
        "pages": results
    }, f, indent=2)

print("🧠 Semantic words built (v3.3 Phase 1)")
print(f"📦 Wrote: {OUTPUT}")
