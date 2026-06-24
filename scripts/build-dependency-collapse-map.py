import os
import re
import json
from collections import defaultdict

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

OUTPUT_FILE = os.path.join(ROOT, "dependency-collapse-map.json")

# =========================================================
# CONFIGURATION SIGNALS (YOUR SYSTEM'S TRUTH RULES)
# =========================================================

TRUTH_LAYER = "semantic-salience.json"

LEGACY_GRAPH_FILES = {
    "content-graph.json",
    "semantic-graph.json",
    "content-model.json",
    "semantic-context.json",
    "semantic-words.json",
    "word-graph.json"
}

DERIVATIVE_OUTPUTS = {
    "search-index.json",
    "sitemap.xml",
    "tags.json",
    "feed.xml",
    "homepage-intelligence.json"
}

CORE_KEYWORDS = [
    "semantic-salience",
    "build-semantic-salience"
]

# =========================================================
# FILE DISCOVERY
# =========================================================

def find_scripts():
    scripts = []

    for root, _, files in os.walk(ROOT):
        for f in files:
            if f.endswith(".py") or f.endswith(".sh"):
                scripts.append(os.path.join(root, f))

    return scripts


# =========================================================
# SAFE READ
# =========================================================

def safe_read(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


# =========================================================
# ANALYSIS
# =========================================================

def analyze_script(path):
    content = safe_read(path)

    reads = set()
    writes = set()

    is_truth_layer = False

    # detect salience authority usage
    if any(k in content for k in CORE_KEYWORDS):
        is_truth_layer = True

    # detect file reads/writes
    for f in LEGACY_GRAPH_FILES.union(DERIVATIVE_OUTPUTS).union({TRUTH_LAYER}):
        if f in content:
            if "open(" in content or "read" in content or "cat" in content:
                reads.add(f)
            if "write" in content or "dump" in content or ">" in content:
                writes.add(f)

    # structural heuristics
    name = os.path.basename(path)

    return {
        "script": name,
        "path": path.replace(ROOT, "."),
        "reads": sorted(reads),
        "writes": sorted(writes),
        "is_truth_layer_aware": is_truth_layer
    }


# =========================================================
# CLASSIFICATION ENGINE
# =========================================================

def classify(node):
    reads = set(node["reads"])
    writes = set(node["writes"])

    # CORE: builds or directly depends on semantic salience
    if node["is_truth_layer_aware"]:
        return "CORE"

    if TRUTH_LAYER in reads:
        return "DERIVATIVE"

    # OBSOLETE: writes legacy graphs that are no longer authoritative
    if writes & LEGACY_GRAPH_FILES:
        return "OBSOLETE_CANDIDATE"

    # DERIVATIVE: consumes outputs but doesn't define truth
    if reads & DERIVATIVE_OUTPUTS:
        return "DERIVATIVE"

    return "UNKNOWN"


# =========================================================
# GRAPH BUILDER
# =========================================================

def build_map():
    scripts = find_scripts()

    nodes = []
    edges = []

    for s in scripts:
        node = analyze_script(s)
        node["classification"] = classify(node)

        nodes.append(node)

        # edges: simple dependency inference
        for r in node["reads"]:
            edges.append({
                "from": node["script"],
                "to": r,
                "type": "reads"
            })

        for w in node["writes"]:
            edges.append({
                "from": node["script"],
                "to": w,
                "type": "writes"
            })

    return {
        "nodes": nodes,
        "edges": edges
    }


# =========================================================
# SUMMARY REPORT
# =========================================================

def print_summary(data):
    counts = defaultdict(int)

    for n in data["nodes"]:
        counts[n["classification"]] += 1

    print("\n🧭 DEPENDENCY COLLAPSE MAP")
    print("=" * 40)

    for k, v in counts.items():
        print(f"{k}: {v}")

    print("\n🔥 POTENTIAL OBSOLETE CANDIDATES:")
    for n in data["nodes"]:
        if n["classification"] == "OBSOLETE_CANDIDATE":
            print(" -", n["script"])

    print("\n⚠️ UNKNOWN (needs manual review):")
    for n in data["nodes"]:
        if n["classification"] == "UNKNOWN":
            print(" -", n["script"])


# =========================================================
# MAIN
# =========================================================

def main():
    data = build_map()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print_summary(data)

    print("\n📦 map written:", OUTPUT_FILE)
    print("✅ dependency collapse analysis complete")


if __name__ == "__main__":
    main()
