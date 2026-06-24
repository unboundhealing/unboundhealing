#!/usr/bin/env python3

import os
import json
from collections import defaultdict

# =========================================================
# PATHS
# =========================================================

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

SAL_FILE = os.path.join(ROOT, "semantic-salience.json")
OUTPUT_FILE = os.path.join(ROOT, "homepage-intelligence.json")


# =========================================================
# LOADER (TRUTH LAYER ONLY)
# =========================================================

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# =========================================================
# SAFE ACCESSORS (NO REINTERPRETATION OF TRUTH)
# =========================================================

def get_nodes(data):
    """
    Nodes are authoritative from semantic-salience.

    Expected format:
        { url: { path, url, concepts } }
    """
    nodes = data.get("nodes", {})

    if not isinstance(nodes, dict):
        return {}

    return nodes


def get_edges(data):
    """
    Edges are authoritative from semantic-salience.

    Expected format:
        [{a, b, weight}]
    """
    edges = data.get("edges", [])

    if not isinstance(edges, list):
        return []

    cleaned = []

    for e in edges:
        if not isinstance(e, dict):
            continue

        a = e.get("a")
        b = e.get("b")

        if a is None or b is None:
            continue

        cleaned.append({
            "a": str(a),
            "b": str(b),
            "weight": float(e.get("weight", 1))
        })

    return cleaned


# =========================================================
# PURE DERIVATION (NO NEW SEMANTIC LAYERS)
# =========================================================

def build_homepage_intelligence(nodes, edges):
    """
    Consumer projection of semantic-salience.

    IMPORTANT PRINCIPLE:
    - This does NOT interpret meaning
    - This does NOT redefine structure
    - This only aggregates already-existing truth signals
    """

    concept_frequency = defaultdict(int)
    node_degree = defaultdict(float)

    # -------------------------------------------------
    # derive concept frequency from truth-layer nodes
    # -------------------------------------------------
    for node in nodes.values():
        concepts = node.get("concepts", [])

        if not isinstance(concepts, list):
            continue

        for c in concepts:
            concept_frequency[c] += 1

    # -------------------------------------------------
    # derive node connectivity from truth-layer edges
    # -------------------------------------------------
    for e in edges:
        a = e["a"]
        b = e["b"]
        w = e["weight"]

        node_degree[a] += w
        node_degree[b] += w

    # -------------------------------------------------
    # top concepts (frequency-based only)
    # -------------------------------------------------
    top_concepts = sorted(
        concept_frequency.items(),
        key=lambda x: (-x[1], x[0])
    )[:10]

    # -------------------------------------------------
    # top hubs (connectivity-based only)
    # -------------------------------------------------
    top_hubs = sorted(
        node_degree.items(),
        key=lambda x: (-x[1], x[0])
    )[:10]

    return {
        "top_concepts": [
            {"concept": c, "frequency": f}
            for c, f in top_concepts
        ],
        "top_hubs": [
            {"node": n, "score": s}
            for n, s in top_hubs
        ],
        "node_count": len(nodes),
        "edge_count": len(edges)
    }


# =========================================================
# MAIN PIPELINE (PURE READ MODEL)
# =========================================================

def main():

    data = load_json(SAL_FILE)

    print()
    print("INTELLIGENCE INPUT KEYS:")
    print(data.keys())

    print()
    print("PAGE_GRAPH COUNT:")
    print(len(data.get("page_graph", {})))

    nodes = get_nodes(data)
    edges = get_edges(data)

    homepage = build_homepage_intelligence(nodes, edges)

    output = {
        "homepage_intelligence": homepage,

        # explicit contract boundary
        "source": "semantic-salience",
        "consumer_model": "read-only-projection",
        "status": "ok"
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("🏠 homepage-intelligence built successfully (v4.0 PURE CONSUMER)")
    print(f"📦 nodes: {len(nodes)}")
    print(f"🔗 edges: {len(edges)}")


if __name__ == "__main__":
    main()
