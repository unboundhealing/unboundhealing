#!/usr/bin/env python3

import os
import re
import json
from collections import defaultdict
from urllib.parse import urljoin

# =========================================================
# CONFIG
# =========================================================

DOMAIN = "https://unboundhealing.org/"

STOPWORDS = {
    "https",
    "http",
    "www",
    "com",
    "org",
    "html",
    "indexhtml",
    "index"
}


# =========================================================
# NORMALIZATION
# =========================================================

def normalize(text: str) -> str:
    """
    Normalize path/url fragments into a stable concept space.
    """

    text = text.lower()

    text = re.sub(
        r"\.html?$",
        "",
        text
    )

    text = re.sub(
        r"[^a-z0-9/_\-\s]",
        "",
        text
    )

    return text


def extract_concepts(path: str):
    """
    Extract concepts directly from structural reality.

    IMPORTANT:

    Concepts are stored in semantic-salience
    and become part of the truth layer itself.

    Downstream systems should consume them,
    not regenerate them.
    """

    base = normalize(path)

    parts = [
        p
        for p in re.split(
            r"[/_\-\s]+",
            base
        )
        if p and p not in STOPWORDS
    ]

    seen = set()
    concepts = []

    for p in parts:
        if p not in seen:
            seen.add(p)
            concepts.append(p)

    return concepts


# =========================================================
# URL HELPERS
# =========================================================

def build_url(path: str) -> str:
    """
    Build canonical URL.
    """

    path = path.replace("\\", "/")

    if path.endswith("index.html"):
        path = path[:-10]

    elif path.endswith(".html"):
        path = path[:-5]

    return urljoin(
        DOMAIN,
        path.lstrip("/")
    )


# =========================================================
# REGISTRY
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
# GRAPH = STRUCTURE OF REALITY
# =========================================================

def build_graph(registry):
    """
    Build canonical graph structure.

    Graph answers:

    What exists?
    What is connected?
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

        for i in range(len(concepts)):
            for j in range(i + 1, len(concepts)):

                a = concepts[i]
                b = concepts[j]

                key = tuple(
                    sorted([a, b])
                )

                edge_weights[key] += 1

    edges = []

    for (a, b), weight in sorted(
        edge_weights.items()
    ):

        edges.append({
            "a": a,
            "b": b,
            "weight": weight
        })

    return nodes, edges


# =========================================================
# SALIENCE = WEIGHTING OF REALITY
# =========================================================

def build_salience(registry, edges):
    """
    Build raw weighting layer.

    IMPORTANT:

    No ranking.
    No interpretation.
    No derived scores.

    Store only raw observable properties.

    Consumers decide later how to rank,
    sort, weight, search, recommend,
    visualize, etc.
    """

    frequency = defaultdict(int)
    connectedness = defaultdict(int)

    for page in registry.values():

        for concept in page["concepts"]:
            frequency[concept] += 1

    concept_neighbors = defaultdict(set)

    for edge in edges:

        a = edge["a"]
        b = edge["b"]

        concept_neighbors[a].add(b)
        concept_neighbors[b].add(a)

    for concept, neighbors in concept_neighbors.items():
        connectedness[concept] = len(neighbors)

    salience = {}

    all_concepts = set()

    all_concepts.update(frequency.keys())
    all_concepts.update(connectedness.keys())

    for concept in sorted(all_concepts):

        salience[concept] = {
            "frequency": frequency.get(
                concept,
                0
            ),
            "connectedness": connectedness.get(
                concept,
                0
            )
        }

    return salience


# =========================================================
# PAGE GRAPH
# =========================================================

def build_page_graph(registry):
    """
    Derived navigation layer.

    This is NOT truth.

    This is a consumer-friendly view
    derived from the truth layer.
    """

    concept_map = defaultdict(set)

    for url, data in registry.items():

        for concept in data["concepts"]:
            concept_map[concept].add(url)

    page_graph = {}

    for url, data in registry.items():

        related_scores = defaultdict(int)

        for concept in data["concepts"]:

            for other_url in concept_map[concept]:

                if other_url == url:
                    continue

                related_scores[other_url] += 1

        ranked = sorted(
            related_scores.items(),
            key=lambda x: (
                -x[1],
                x[0]
            )
        )

        page_graph[url] = {
            "concepts": data["concepts"],
            "related": [
                item[0]
                for item in ranked[:10]
            ]
        }

    return page_graph


# =========================================================
# TRUTH LAYER
# =========================================================

def build_semantic_salience(registry):
    """
    Single source of truth.

    GRAPH
        structure of reality

    SALIENCE
        weighting of reality

    EVERYTHING ELSE
        consumers only
    """

    nodes, edges = build_graph(
        registry
    )

    salience = build_salience(
        registry,
        edges
    )

    page_graph = build_page_graph(
        registry
    )

    return {
        "version": "3.2",
        "philosophy": {
            "graph": "structure of reality",
            "salience": "weighting of reality",
            "consumers": "read only"
        },
        "nodes": nodes,
        "edges": edges,
        "salience": salience,
        "page_graph": page_graph
    }


# =========================================================
# FILE DISCOVERY
# =========================================================

def find_html_files(root):

    html_files = []

    for dirpath, _, filenames in os.walk(root):

        for filename in filenames:

            if not filename.endswith(".html"):
                continue

            full_path = os.path.join(
                dirpath,
                filename
            )

            rel_path = os.path.relpath(
                full_path,
                root
            )

            html_files.append(rel_path)

    return sorted(html_files)


# =========================================================
# MAIN
# =========================================================

def main():

    root = os.getcwd()

    html_files = find_html_files(root)

    print("📂 scanning root:", root)
    print("📦 html files discovered:", len(html_files))

    registry = build_registry(
        html_files
    )

    print("📦 registry entries:", len(registry))

    semantic_salience = build_semantic_salience(
        registry
    )

    output_path = os.path.join(
        root,
        "semantic-salience.json"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            semantic_salience,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(
        "🌌 semantic-salience COMPLETE (v3.2 FIRST-CLASS SALIENCE)"
    )

    print(
        "📁 output:",
        output_path
    )

    print(
        "📦 nodes:",
        len(
            semantic_salience["nodes"]
        )
    )

    print(
        "📦 edges:",
        len(
            semantic_salience["edges"]
        )
    )

    print(
        "🧠 concepts:",
        len(
            semantic_salience["salience"]
        )
    )


if __name__ == "__main__":
    main()
