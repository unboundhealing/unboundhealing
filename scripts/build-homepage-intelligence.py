import os
import json

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

SAL_FILE = os.path.join(ROOT, "semantic-salience.json")
OUTPUT_FILE = os.path.join(ROOT, "homepage-intelligence.json")


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def safe_nodes(raw_nodes):
    """
    Nodes are expected as dict:
    {
        url: {path, url, concepts: []}
    }
    """
    if isinstance(raw_nodes, dict):
        return raw_nodes
    if isinstance(raw_nodes, list):
        # fallback: convert list form to dict
        out = {}
        for item in raw_nodes:
            if isinstance(item, dict) and "url" in item:
                out[item["url"]] = item
        return out
    return {}


def safe_edges(raw_edges):
    """
    Edges MUST be list of dicts:
    [{a, b, weight}]
    """
    if not isinstance(raw_edges, list):
        return []

    cleaned = []
    for e in raw_edges:
        if not isinstance(e, dict):
            continue

        a = e.get("a")
        b = e.get("b")

        if not a or not b:
            continue

        cleaned.append({
            "a": str(a),
            "b": str(b),
            "weight": e.get("weight", 1)
        })

    return cleaned


def build_homepage_intelligence(nodes, edges):
    """
    Derives homepage-level intelligence:
    - top concepts
    - hub nodes
    - entry suggestions
    """

    concept_counts = {}
    hubs = {}

    for url, node in nodes.items():
        concepts = node.get("concepts", []) or []
        for c in concepts:
            concept_counts[c] = concept_counts.get(c, 0) + 1

        hubs[url] = 0

    for e in edges:
        a = e["a"]
        b = e["b"]
        w = e["weight"]

        if a in hubs:
            hubs[a] += w
        if b in hubs:
            hubs[b] += w

    top_concepts = sorted(
        concept_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]

    top_hubs = sorted(
        hubs.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]

    return {
        "top_concepts": top_concepts,
        "top_hubs": top_hubs,
        "node_count": len(nodes),
        "edge_count": len(edges)
    }


def main():
    data = load_json(SAL_FILE)

    raw_nodes = data.get("nodes", {})
    raw_edges = data.get("edges", [])

    nodes = safe_nodes(raw_nodes)
    edges = safe_edges(raw_edges)

    homepage = build_homepage_intelligence(nodes, edges)

    output = {
        "homepage_intelligence": homepage,
        "source": "semantic-salience-v3",
        "status": "ok"
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print("🏠 homepage-intelligence built successfully")
    print(f"📦 nodes: {len(nodes)}")
    print(f"🔗 edges: {len(edges)}")


if __name__ == "__main__":
    main()
