#!/usr/bin/env python3

import os
import re
import json
from collections import defaultdict
from urllib.parse import urljoin
from bs4 import BeautifulSoup

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
# CANONICALIZATION (STRUCTURAL NORMALIZATION ONLY)
# =========================================================

def canonicalize_concept(text: str) -> str:
    """
    Enforces a single stable representation for concepts.

    RULE:
    - spaces, underscores, hyphens collapse into hyphen form
    - lowercase normalization
    - structural consistency only (NOT semantic interpretation)
    """

    text = text.lower().strip()

    # unify separators into hyphen
    text = re.sub(r"[\s_]+", "-", text)

    # remove invalid characters
    text = re.sub(r"[^a-z0-9\-]", "", text)

    # collapse multiple hyphens
    text = re.sub(r"-{2,}", "-", text)

    return text


# =========================================================
# NORMALIZATION (RAW STRUCTURAL CLEANING)
# =========================================================

def normalize(text: str) -> str:
    """
    Normalize raw structural input into token space.
    """

    text = text.lower()

    text = re.sub(r"\.html?$", "", text)

    text = re.sub(r"[^a-z0-9/_\-\s]", "", text)

    return text


# =========================================================
# CONCEPT EXTRACTION (STRUCTURAL REALITY + LIGHT PHRASES)
# =========================================================

def extract_concepts(path: str):
    """
    Extract concepts from structural reality.

    SOURCES:
    - URL/path structure
    - token segmentation
    - phrase adjacency

    IMPORTANT:
    Canonicalization is applied BEFORE storage.
    """

    base = normalize(path)

    tokens = [
        t for t in re.split(r"[/_\-\s]+", base)
        if t and t not in STOPWORDS
    ]

    raw_concepts = []

    # -----------------------------
    # 1. single-token concepts
    # -----------------------------
    for t in tokens:
        raw_concepts.append(t)

    # -----------------------------
    # 2. phrase concepts (2-token)
    # -----------------------------
    for i in range(len(tokens) - 1):
        raw_concepts.append(f"{tokens[i]} {tokens[i+1]}")

    # -----------------------------
    # 3. phrase concepts (3-token)
    # -----------------------------
    for i in range(len(tokens) - 2):
        raw_concepts.append(f"{tokens[i]} {tokens[i+1]} {tokens[i+2]}")

    # -----------------------------
    # CANONICALIZATION STEP
    # -----------------------------
    seen = set()
    concepts = []

    for c in raw_concepts:
        canon = canonicalize_concept(c)

        if not canon:
            continue

        if canon not in seen:
            seen.add(canon)
            concepts.append(canon)

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
# PAGE METADATA EXTRACTION
# =========================================================

def extract_page_metadata(full_path):
    """
    Extract real HTML metadata for truth-aligned rendering.
    """

    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        # -----------------------------
        # TITLE
        # -----------------------------
        title_tag = soup.find("title")
        title = title_tag.text.strip() if title_tag and title_tag.text else ""

        # -----------------------------
        # DESCRIPTION
        # -----------------------------
        desc = ""

        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            desc = meta.get("content", "").strip()

        # -----------------------------
        # WORD COUNT (light heuristic)
        # -----------------------------
        text = soup.get_text(" ", strip=True)
        word_count = len(text.split())

        return {
            "title": title,
            "description": desc,
            "word_count": word_count
        }

    except Exception as e:
        print("⚠️ metadata extraction failed:", e)
        return {
            "title": "",
            "description": "",
            "word_count": 0
        }


# =========================================================
# REGISTRY (STRUCTURAL REALITY INDEX)
# =========================================================

def build_registry(root, html_files):
    registry = {}

    for path in html_files:

        full_path = os.path.join(root, path)

        url = build_url(path)
        concepts = extract_concepts(path)

        metadata = extract_page_metadata(full_path)

        registry[url] = {
            "path": path,
            "url": url,
            "title": metadata.get("title", "").strip(),   # <-- ADD THIS (critical)
            "description": metadata.get("description", ""),
            "word_count": metadata.get("word_count", 0),
            "concepts": concepts
        }

    return registry


# =========================================================
# GRAPH = STRUCTURE OF REALITY
# =========================================================

def build_graph(registry):
    """
    GRAPH = STRUCTURE ONLY

    - nodes = existence
    - edges = co-occurrence
    """

    nodes = {}
    edge_weights = defaultdict(int)

    for url, data in registry.items():

        nodes[url] = {
            "path": data["path"],
            "url": data["url"],
            "title": data.get("title", ""),   # <-- CRITICAL
            "concepts": data["concepts"]
        }
        
        concepts = data["concepts"]

        for i in range(len(concepts)):
            for j in range(i + 1, len(concepts)):

                a = concepts[i]
                b = concepts[j]

                key = tuple(sorted((a, b)))
                edge_weights[key] += 1

    edges = [
        {"a": a, "b": b, "weight": w}
        for (a, b), w in edge_weights.items()
    ]

    return nodes, edges


# =========================================================
# SALIENCE = WEIGHTING SIGNALS ONLY (NO RANKING)
# =========================================================

def build_salience(registry, edges):
    """
    SALIENCE = observable signals only

    RULES:
    - no ranking
    - no scoring
    - no normalization
    - only measurable counts
    """

    frequency = defaultdict(int)
    connectivity = defaultdict(int)

    # frequency from registry
    for page in registry.values():
        for concept in page["concepts"]:
            frequency[concept] += 1

    # connectivity from edges
    neighbors = defaultdict(set)

    for edge in edges:
        a = edge["a"]
        b = edge["b"]
        neighbors[a].add(b)
        neighbors[b].add(a)

    for concept, neigh in neighbors.items():
        connectivity[concept] = len(neigh)

    salience = {}

    all_concepts = set(frequency) | set(connectivity)

    for c in all_concepts:
        salience[c] = {
            "frequency": frequency[c],
            "connectivity": connectivity[c]
        }

    return salience


# =========================================================
# PAGE GRAPH (CONSUMER LAYER ONLY)
# =========================================================

def build_page_graph(registry):
    """
    Derived navigation layer only.
    Not part of truth layer.
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
# TRUTH LAYER ASSEMBLY
# =========================================================

def build_semantic_salience(registry):

    nodes, edges = build_graph(registry)

    salience = build_salience(registry, edges)

    page_graph = build_page_graph(registry)

    return {
        "version": "4.2",
        "philosophy": {
            "graph": "structure of reality",
            "salience": "weighting of reality",
            "consumers": "read only"
        },

        # TRUTH LAYER
        "nodes": nodes,
        "edges": edges,
        "salience": salience,

        # DERIVED LAYER (NON-TRUTH)
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

    registry = build_registry(root, html_files)

    print("📦 registry entries:", len(registry))

    semantic = build_semantic_salience(registry)

    output_path = os.path.join(root, "semantic-salience.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(semantic, f, indent=2, ensure_ascii=False)

    print("🌌 semantic-salience COMPLETE (v4.2 CANONICAL TRUTH MODEL)")
    print("📁 output:", output_path)
    print("📦 nodes:", len(semantic["nodes"]))
    print("📦 edges:", len(semantic["edges"]))
    print("🧠 salience concepts:", len(semantic["salience"]))


if __name__ == "__main__":
    main()
