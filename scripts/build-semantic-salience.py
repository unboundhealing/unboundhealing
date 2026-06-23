#!/usr/bin/env python3

import os
import re
import json
from collections import defaultdict
from urllib.parse import urljoin

# =========================================================
# CONFIG — SINGLE TRUTH CONTEXT
# =========================================================

DOMAIN = "https://unboundhealing.org/"

STOPWORDS = {
    "https", "http", "www",
    "com", "org",
    "html", "indexhtml", "index"
}

# =========================================================
# CONCEPT CANONICALIZATION REGISTRY (TRUTH CORE)
# =========================================================

def canonicalize(concept: str) -> str:
    """
    Single-source concept identity resolver.

    This is NOT interpretation.
    This is identity stabilization.
    """

    concept = concept.lower().strip()

    # normalize separators into stable form
    concept = re.sub(r"[_\s]+", "-", concept)

    # collapse repeated dashes
    concept = re.sub(r"-{2,}", "-", concept)

    return concept


# =========================================================
# NORMALIZATION
# =========================================================

def normalize(text: str) -> str:
    """
    Normalize raw structural input into token-safe space.
    """

    text = text.lower()

    text = re.sub(r"\.html?$", "", text)

    text = re.sub(r"[^a-z0-9/_\-\s]", "", text)

    return text


# =========================================================
# CONCEPT EXTRACTION (STRUCTURE ONLY)
# =========================================================

def extract_concepts(path: str):
    """
    Extract concepts from structural reality:

    SOURCES:
    - URL/path structure
    - directory hierarchy
    - token segmentation
    """

    base = normalize(path)

    tokens = [
        t for t in re.split(r"[/_\-\s]+", base)
        if t and t not in STOPWORDS
    ]

    concepts = []

    # -----------------------------
    # base tokens (structure)
    # -----------------------------
    for t in tokens:
        concepts.append(canonicalize(t))

    # -----------------------------
    # phrase concepts (adjacent structure ONLY)
    # -----------------------------
    for i in range(len(tokens) - 1):
        concepts.append(
            canonicalize(f"{tokens[i]} {tokens[i+1]}")
        )

    return concepts


# =========================================================
# URL RESOLUTION
# =========================================================

def build_url(path: str) -> str:
    """
    Canonical URL builder.
    """

    path = path.replace("\\", "/")

    if path.endswith("index.html"):
        path = path[:-10]
    elif path.endswith(".html"):
        path = path[:-5]

    return urljoin(DOMAIN, path.lstrip("/"))


# =========================================================
# REGISTRY (STRUCTURAL REALITY INDEX)
# =========================================================

def build_registry(html_files):
    registry = {}

    for path in html_files:
        url = build_url(path)
        concepts = extract_concepts(path)

        registry[url] = {
            "path": path,
            "url": url,
            "concepts": concepts
        }

    return registry


# =========================================================
# GRAPH = STRUCTURE OF REALITY (PURE RELATIONS)
# =========================================================

def build_graph(registry):
    """
    Graph is ONLY structure.

    No weighting.
    No interpretation.
    No salience logic here.
    """

    nodes = {}
    edge_weights = defaultdict(int)

    for url, data in registry.items():

        nodes[url] = {
            "path": data["path"],
            "url": data["url"],
            "concepts": data["concepts"]
        }

        concepts = data["concepts"]

        # co-occurrence structure
        for i in range(len(concepts)):
            for j in range(i + 1, len(concepts)):

                a = concepts[i]
                b = concepts[j]

                key = tuple(sorted((a, b)))
                edge_weights[key] += 1

    edges = [
        {
            "a": a,
            "b": b,
            "weight": weight
        }
        for (a, b), weight in edge_weights.items()
    ]

    return nodes, edges


# =========================================================
# SALIENCE = WEIGHTING OF REALITY (CANONICALIZED)
# =========================================================

def build_salience(registry, edges):
    """
    Salience is pure measurable weighting.

    NO ranking.
    NO normalization outputs.
    ONLY raw structural signals.
    """

    frequency = defaultdict(int)
    connectivity = defaultdict(int)

    # -----------------------------
    # frequency signal
    # -----------------------------
    for page in registry.values():
        for concept in page["concepts"]:
            frequency[concept] += 1

    # -----------------------------
    # connectivity signal
    # -----------------------------
    neighbors = defaultdict(set)

    for edge in edges:
        a = edge["a"]
        b = edge["b"]

        neighbors[a].add(b)
        neighbors[b].add(a)

    for concept, neigh in neighbors.items():
        connectivity[concept] = len(neigh)

    # -----------------------------
    # SALIENCE CORE (CANONICAL KEYS)
    # -----------------------------
    salience = {}

    all_concepts = set(frequency.keys()) | set(connectivity.keys())

    for concept in all_concepts:
        c = canonicalize(concept)

        salience[c] = {
            "frequency": frequency.get(concept, 0),
            "connectivity": connectivity.get(concept, 0)
        }

    return salience


# =========================================================
# PAGE GRAPH (CONSUMER ONLY LAYER)
# =========================================================

def build_page_graph(registry):
    """
    Derived navigation layer ONLY.

    NOT truth.
    NOT structure.
    NOT salience.
    """

    concept_index = defaultdict(set)

    for url, data in registry.items():
        for c in data["concepts"]:
            concept_index[c].add(url)

    page_graph = {}

    for url, data in registry.items():

        related_scores = defaultdict(int)

        for c in data["concepts"]:
            for other in concept_index[c]:
                if other != url:
                    related_scores[other] += 1

        ranked = sorted(
            related_scores.items(),
            key=lambda x: (-x[1], x[0])
        )

        page_graph[url] = {
            "concepts": data["concepts"],
            "related": [r[0] for r in ranked[:10]]
        }

    return page_graph


# =========================================================
# TRUTH LAYER ASSEMBLY (SINGLE SOURCE OF REALITY)
# =========================================================

def build_semantic_salience(registry):

    nodes, edges = build_graph(registry)

    salience = build_salience(registry, edges)

    page_graph = build_page_graph(registry)

    return {
        "version": "4.1",
        "philosophy": {
            "graph": "structure of reality",
            "salience": "weighting of reality",
            "consumers": "read only"
        },

        # -----------------------------
        # TRUTH LAYER
        # -----------------------------
        "nodes": nodes,
        "edges": edges,
        "salience": salience,

        # -----------------------------
        # DERIVED ONLY (NON-TRUTH)
        # -----------------------------
        "page_graph": page_graph
    }


# =========================================================
# FILE DISCOVERY
# =========================================================

def find_html_files(root):
    html_files = []

    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith(".html"):
                full = os.path.join(dirpath, filename)
                rel = os.path.relpath(full, root)
                html_files.append(rel)

    return sorted(html_files)


# =========================================================
# MAIN
# =========================================================

def main():

    root = os.getcwd()

    html_files = find_html_files(root)

    print("📂 scanning root:", root)
    print("📦 html files discovered:", len(html_files))

    registry = build_registry(html_files)

    print("📦 registry entries:", len(registry))

    semantic = build_semantic_salience(registry)

    output_path = os.path.join(root, "semantic-salience.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(semantic, f, indent=2, ensure_ascii=False)

    print("🌌 semantic-salience COMPLETE (v4.1 CANONICAL TRUTH MODEL)")
    print("📁 output:", output_path)
    print("📦 nodes:", len(semantic["nodes"]))
    print("📦 edges:", len(semantic["edges"]))
    print("🧠 salience concepts:", len(semantic["salience"]))


if __name__ == "__main__":
    main()
