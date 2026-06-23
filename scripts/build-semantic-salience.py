#!/usr/bin/env python3
import json
import os
import re
from collections import defaultdict

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())
REGISTRY_PATH = os.path.join(ROOT, "content-registry.json")
OUTPUT_PATH = os.path.join(ROOT, "semantic-salience.json")

def normalize(text: str) -> str:
    if not text:
        return ""

    text = text.lower().strip()
    text = re.sub(r"https?://[^/]+", "", text)
    text = re.sub(r"/+", "/", text)

    # SAFE CHARACTER FILTER (NO RANGE ERRORS)
    text = re.sub(r"[^a-z0-9/_\- ]", "", text)

    return text.strip("/")

def load_registry():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("pages", [])

def extract_concepts(path, url):
    base = f"{path} {url}"
    base = normalize(base)
    parts = [p for p in re.split(r"[/_\- ]+", base) if p]
    return list(dict.fromkeys(parts))  # unique, stable order

def main():
    pages = load_registry()

    if not pages:
        raise ValueError("Registry empty — cannot build semantic-salience")

    nodes = {}
    edges = []

    for p in pages:
        path = p.get("path", "")
        url = p.get("url", "")

        concepts = extract_concepts(path, url)

        nodes[url] = {
            "path": path,
            "url": url,
            "concepts": concepts
        }

        # build full connectivity inside node concept space
        for i in range(len(concepts)):
            for j in range(i + 1, len(concepts)):
                edges.append((concepts[i], concepts[j]))

    # collapse edges into weights
    weighted = defaultdict(int)
    for a, b in edges:
        key = tuple(sorted((a, b)))
        weighted[key] += 1

    graph_edges = [
        {"a": a, "b": b, "weight": w}
        for (a, b), w in weighted.items()
    ]

    salience = {
        "truth_layer": "semantic-salience",
        "nodes": nodes,
        "edges": graph_edges,
        "node_count": len(nodes),
        "edge_count": len(graph_edges)
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(salience, f, indent=2)

    print("🌌 semantic-salience COMPLETE (single truth layer)")
    print(f"📦 nodes: {len(nodes)}")
    print(f"📦 edges: {len(graph_edges)}")
    print(f"📁 output: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
