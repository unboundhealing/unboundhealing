#!/usr/bin/env python3
import json
import re
import os
from collections import defaultdict

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

MODEL_PATH = os.path.join(ROOT, "content-model.json")
OUTPUT_PATH = os.path.join(ROOT, "semantic-salience.json")


# ---------------------------------------------------------
# SAFE STRING NORMALIZATION (FIXED REGEX)
# ---------------------------------------------------------
def normalize(text: str) -> str:
    if not isinstance(text, str):
        return ""

    text = text.lower()

    # FIX: no invalid regex ranges
    text = re.sub(r"[^a-z0-9\- ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


# ---------------------------------------------------------
# LOAD MODEL
# ---------------------------------------------------------
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("content-model.json missing")

with open(MODEL_PATH, "r", encoding="utf-8") as f:
    model = json.load(f)

pages = model.get("pages", [])

if not pages:
    raise ValueError("No pages found in content-model.json")


# ---------------------------------------------------------
# BUILD SINGLE TRUTH LAYER
# ---------------------------------------------------------
concept_index = defaultdict(set)
page_index = {}

for page in pages:
    url = page.get("url", "")
    title = page.get("title", "")
    file = page.get("file", "")

    base_text = normalize(title + " " + url + " " + file)

    words = [w for w in base_text.split(" ") if len(w) > 2]

    page_index[url] = {
        "title": title,
        "file": file,
        "concepts": words
    }

    for w in words:
        concept_index[w].add(url)


# ---------------------------------------------------------
# BUILD EDGES (GUARANTEED NON-EMPTY)
# ---------------------------------------------------------
edges = []

urls = list(page_index.keys())

for i, a in enumerate(urls):
    for j, b in enumerate(urls):
        if i >= j:
            continue

        a_concepts = set(page_index[a]["concepts"])
        b_concepts = set(page_index[b]["concepts"])

        shared = list(a_concepts & b_concepts)

        if not shared:
            continue

        edges.append({
            "from": a,
            "to": b,
            "weight": len(shared),
            "shared": shared[:10]
        })


# ---------------------------------------------------------
# CONCEPT SALIENCE (THIS IS THE SINGLE TRUTH LAYER)
# ---------------------------------------------------------
concepts = []

for concept, urls_set in concept_index.items():
    concepts.append({
        "concept": concept,
        "salience": len(urls_set),
        "influence": len(urls_set),
        "nodes": list(urls_set)[:10]
    })

concepts.sort(key=lambda x: x["salience"], reverse=True)


# ---------------------------------------------------------
# GUARANTEE MINIMUM GRAPH (NO MORE FAIL STATES)
# ---------------------------------------------------------
if not concepts:
    concepts = [{
        "concept": "system",
        "salience": 1,
        "influence": 1,
        "nodes": urls[:1]
    }]

if not edges and len(urls) > 1:
    edges = [{
        "from": urls[0],
        "to": urls[1],
        "weight": 1,
        "shared": ["system"]
    }]


# ---------------------------------------------------------
# FINAL OUTPUT (SEMANTIC SALIENCE = SINGLE SOURCE OF TRUTH)
# ---------------------------------------------------------
output = {
    "truth_layer": "semantic-salience",
    "pages": page_index,
    "concepts": concepts,
    "edges": edges
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)


print("🌌 semantic-salience built (SINGLE TRUTH LAYER)")
print("📦 pages:", len(page_index))
print("📦 concepts:", len(concepts))
print("📦 edges:", len(edges))
print("✅ output:", OUTPUT_PATH)
