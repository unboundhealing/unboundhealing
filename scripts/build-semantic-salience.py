import os
import re
import json
from urllib.parse import urljoin

# -----------------------------
# Config
# -----------------------------

DOMAIN = "https://unboundhealing.org/"

STOPWORDS = {
    "https", "http", "www", "com", "org",
    "indexhtml", "html", "index"
}

# -----------------------------
# Normalization
# -----------------------------

def normalize(text: str) -> str:
    """
    Normalize path/url fragments into clean token base.
    """
    text = text.lower()

    # strip file extensions early
    text = re.sub(r"\.html?$", "", text)

    # remove junk tokens but KEEP separators intact for splitting
    text = re.sub(r"[^a-z0-9/_\- ]", "", text)

    return text


def extract_concepts(path: str, url: str):
    """
    Extract semantic concepts from a file path + URL.
    """
    base = normalize(path)

    parts = [
        p for p in re.split(r"[/_\- ]+", base)
        if p and p not in STOPWORDS
    ]

    # dedupe while preserving order
    seen = set()
    concepts = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            concepts.append(p)

    return concepts


# -----------------------------
# URL builder
# -----------------------------

def build_url(path: str) -> str:
    """
    Safely construct canonical URL.
    Prevents https:/// bugs.
    """
    return urljoin(DOMAIN, path.lstrip("/"))


# -----------------------------
# Registry builder
# -----------------------------

def build_registry(html_files):
    registry = {}

    for path in html_files:
        url = build_url(path)
        concepts = extract_concepts(path, url)

        registry[url] = {
            "path": path,
            "url": url,
            "concepts": concepts
        }

    return registry


# -----------------------------
# Semantic layer (concept graph)
# -----------------------------

def build_semantic_layer(registry):
    """
    Simple graph representation of concept co-occurrence.
    """

    nodes = {}
    edges = []

    for url, data in registry.items():
        nodes[url] = data

        concepts = data["concepts"]

        for i in range(len(concepts)):
            for j in range(i + 1, len(concepts)):
                edges.append({
                    "a": concepts[i],
                    "b": concepts[j],
                    "weight": 1
                })

    return {
        "nodes": nodes,
        "edges": edges
    }


# -----------------------------
# PAGE GRAPH (UI DERIVATION LAYER)
# -----------------------------

def build_page_graph(registry, semantic):
    """
    Builds page-level adjacency graph based on shared concepts.
    This is the UI-facing layer used by plugins like related_content.
    """

    page_graph = {}

    # -----------------------------
    # INIT STRUCTURE
    # -----------------------------
    for url, data in registry.items():
        page_graph[url] = {
            "concepts": data["concepts"],
            "related": []
        }

    # -----------------------------
    # concept → urls reverse index
    # -----------------------------
    concept_map = {}

    for url, data in registry.items():
        for c in data["concepts"]:
            concept_map.setdefault(c, []).append(url)

    # -----------------------------
    # build related pages
    # -----------------------------
    for url, data in registry.items():
        related = set()

        for c in data["concepts"]:
            for other in concept_map.get(c, []):
                if other != url:
                    related.add(other)

        page_graph[url]["related"] = list(related)[:5]

    # attach once (important: single source of truth)
    semantic["page_graph"] = page_graph

    return semantic


# -----------------------------
# MAIN PIPELINE
# -----------------------------

def main():
    root = os.getcwd()

    html_files = []

    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if f.endswith(".html"):
                rel_path = os.path.join(dirpath, f).replace(root + "/", "")
                html_files.append(rel_path)

    print("📂 scanning root:", root)
    print("📦 html files discovered:", len(html_files))

    registry = build_registry(html_files)

    print("📦 registry entries:", len(registry))

    semantic = build_semantic_layer(registry)

    # IMPORTANT: derive UI layer AFTER semantic graph
    semantic = build_page_graph(registry, semantic)

    output_path = os.path.join(root, "semantic-salience.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(semantic, f, indent=2)

    print("🌌 semantic-salience COMPLETE (v3.1 FIXED + PAGE GRAPH)")
    print("📁 output:", output_path)
    print("📦 nodes:", len(semantic["nodes"]))
    print("📦 edges:", len(semantic["edges"]))


if __name__ == "__main__":
    main()
