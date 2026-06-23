import json
import os
from collections import defaultdict

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

GRAPH_FILE = os.path.join(ROOT, "semantic-salience.json")
OUTPUT_FILE = os.path.join(ROOT, "homepage-intelligence.json")


def load_graph():
    with open(GRAPH_FILE, "r") as f:
        return json.load(f)


def normalize_nodes(nodes_dict):
    """
    Nodes already come as dict keyed by URL.
    We just ensure consistent structure.
    """
    normalized = {}

    for url, data in nodes_dict.items():
        if not isinstance(data, dict):
            continue

        normalized[url] = {
            "path": data.get("path"),
            "url": data.get("url"),
            "concepts": data.get("concepts", []),
            "salience": data.get("salience", 0)
        }

    return normalized


def normalize_edges(edges_list):
    """
    FIX: edges are LISTS of dicts, NOT dicts.
    """
    normalized = []

    if not isinstance(edges_list, list):
        return normalized

    for edge in edges_list:
        if not isinstance(edge, dict):
            continue

        normalized.append({
            "a": edge.get("a"),
            "b": edge.get("b"),
            "weight": edge.get("weight", 1)
        })

    return normalized


def compute_homepage_intelligence(nodes, edges):
    """
    Lightweight derivative layer:
    - count concept frequency
    - identify hub nodes
    """

    concept_counts = defaultdict(int)
    node_scores = {}

    # Count concepts
    for url, node in nodes.items():
        concepts = node.get("concepts", [])
        for c in concepts:
            concept_counts[c] += 1

    # Simple salience scoring
    for url, node in nodes.items():
        score = 0

        concepts = node.get("concepts", [])
        score += len(concepts)

        # bonus if concept is widely used
        for c in concepts:
            score += concept_counts.get(c, 0) * 0.1

        node_scores[url] = round(score, 3)

    return {
        "concept_counts": dict(concept_counts),
        "node_scores": node_scores,
        "edge_count": len(edges)
    }


def main():
    graph = load_graph()

    nodes_raw = graph.get("nodes", {})
    edges_raw = graph.get("edges", [])

    nodes = normalize_nodes(nodes_raw)
    edges = normalize_edges(edges_raw)

    intelligence = compute_homepage_intelligence(nodes, edges)

    output = {
        "nodes": nodes,
        "edges": edges,
        "intelligence": intelligence
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print("🏠 homepage-intelligence built successfully")
    print(f"📦 nodes: {len(nodes)}")
    print(f"🔗 edges: {len(edges)}")


if __name__ == "__main__":
    main()
