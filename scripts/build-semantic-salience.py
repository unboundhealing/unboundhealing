import os
import re
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
# URL builder (FIXED)
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
# Semantic layer (safe stub)
# -----------------------------

def build_semantic_layer(registry):
    """
    Simple graph representation (no assumptions about plugin format).
    """

    nodes = {}
    edges = []

    for url, data in registry.items():
        nodes[url] = data

        concepts = data["concepts"]

        # naive co-occurrence edges
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
# Main
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

    output_path = os.path.join(root, "semantic-salience.json")

    with open(output_path, "w") as f:
        import json
        json.dump(semantic, f, indent=2)

    print("🌌 semantic-salience COMPLETE (v3.1 FIXED)")
    print("📁 output:", output_path)
    print("📦 nodes:", len(semantic["nodes"]))
    print("📦 edges:", len(semantic["edges"]))


if __name__ == "__main__":
    main()
