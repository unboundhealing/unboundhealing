#!/usr/bin/env python3

import os
import json
from collections import defaultdict

# =========================================================
# ROOT + SINGLE TRUTH SOURCE
# =========================================================

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())
SALIENCE_FILE = os.path.join(ROOT, "semantic-salience.json")


# =========================================================
# LOAD TRUTH LAYER (STRICT)
# =========================================================

def load_salience():
    if not os.path.exists(SALIENCE_FILE):
        raise FileNotFoundError("❌ semantic-salience.json missing")

    with open(SALIENCE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("❌ semantic-salience must be a dict")

    return data


salience = load_salience()


# =========================================================
# SAFE ACCESSORS (STRUCTURAL NORMALIZATION)
# =========================================================

def safe_node(node):
    return node if isinstance(node, dict) else {}


def get_pages():
    """
    semantic-salience may store pages under:
    - salience["pages"]
    - or directly as root dict of url → node
    """
    if "pages" in salience and isinstance(salience["pages"], dict):
        return salience["pages"]
    return salience


def get_concepts(node):
    node = safe_node(node)
    c = node.get("concepts", [])
    return c if isinstance(c, list) else []


def normalize_concept(c):
    """
    returns (word, weight)
    """
    if isinstance(c, dict):
        return c.get("word"), float(c.get("weight", 1.0) or 1.0)
    if isinstance(c, str):
        return c, 1.0
    return None, 0.0


# =========================================================
# CORE INDEX (CONCEPT → PAGES)
# =========================================================

_CONCEPT_INDEX = None

def build_concept_index():
    index = defaultdict(set)
    pages = get_pages()

    for url, node in pages.items():
        for c in get_concepts(node):
            word, _ = normalize_concept(c)
            if word:
                index[word].add(url)

    return {k: list(v) for k, v in index.items()}


def get_concept_index():
    global _CONCEPT_INDEX
    if _CONCEPT_INDEX is None:
        _CONCEPT_INDEX = build_concept_index()
    return _CONCEPT_INDEX


# =========================================================
# NODE WEIGHT EXTRACTION
# =========================================================

def get_concept_weights(node):
    weights = {}

    for c in get_concepts(node):
        word, weight = normalize_concept(c)
        if word:
            weights[word] = weights.get(word, 0.0) + weight

    return weights


# =========================================================
# CORE QUERY API (THE ONLY THING CONSUMERS USE)
# =========================================================

def query_salience(url=None, scope="local", limit=5):
    """
    Single unified projection function over semantic-salience.

    scope:
        - "local"  → page-level view (neighbors, local concepts)
        - "global" → full graph view (hubs, top concepts)
    """

    pages = get_pages()
    index = get_concept_index()

    # -------------------------
    # LOCAL VIEW (PAGE CONTEXT)
    # -------------------------
    if url and url in pages:
        node = safe_node(pages[url])
        weights = get_concept_weights(node)

        # related pages scoring
        scores = defaultdict(float)

        for concept, weight in weights.items():
            for other in index.get(concept, []):
                if other != url:
                    scores[other] += weight

        neighbors = sorted(
            scores.items(),
            key=lambda x: (-x[1], x[0])
        )[:limit]

        return {
            "url": url,
            "concepts": list(weights.items()),
            "neighbors": [u for u, _ in neighbors],
        }

    # -------------------------
    # GLOBAL VIEW (HOMEPAGE / SYSTEM VIEW)
    # -------------------------
    concept_totals = defaultdict(float)

    for _, node in pages.items():
        for c in get_concepts(node):
            word, weight = normalize_concept(c)
            if word:
                concept_totals[word] += weight

    top_concepts = sorted(
        concept_totals.items(),
        key=lambda x: (-x[1], x[0])
    )[:limit]

    # hub = most referenced nodes (degree proxy)
    hub_scores = defaultdict(int)

    for concept, urls in index.items():
        for u in urls:
            hub_scores[u] += 1

    top_hubs = sorted(
        hub_scores.items(),
        key=lambda x: (-x[1], x[0])
    )[:limit]

    return {
        "scope": "global",
        "top_concepts": top_concepts,
        "top_hubs": [u for u, _ in top_hubs],
    }


# =========================================================
# PUBLIC CONVENIENCE WRAPPERS (OPTIONAL)
# =========================================================

def homepage_view():
    return query_salience(scope="global")


def related_view(url):
    return query_salience(url=url, scope="local")


# =========================================================
# CLI DEBUG HOOK (OPTIONAL)
# =========================================================

if __name__ == "__main__":
    print("🧠 Semantic Salience Query Engine")
    print("=================================")

    print("\n🌐 GLOBAL VIEW")
    print(json.dumps(homepage_view(), indent=2))

    # example local debug (if any URL exists)
    pages = get_pages()
    sample = next(iter(pages.keys()), None)

    if sample:
        print("\n📍 LOCAL VIEW")
        print(sample)
        print(json.dumps(related_view(sample), indent=2))
