#!/usr/bin/env python3
import os
import re
import json
from collections import defaultdict

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

OUTPUT_FILE = os.path.join(ROOT, "dependency-collapse-map.json")

# ---------------------------------------------------------
# FILE DISCOVERY
# ---------------------------------------------------------

def find_files():
    targets = []

    for root, _, files in os.walk(ROOT):
        # skip noise
        if any(skip in root for skip in [".git", "node_modules", "__pycache__"]):
            continue

        for f in files:
            if f.endswith((".py", ".sh")):
                targets.append(os.path.join(root, f))

    return targets


# ---------------------------------------------------------
# CLASSIFIERS
# ---------------------------------------------------------

TRUTH_LAYER = "semantic-salience.json"

LEGACY_LAYERS = {
    "semantic-graph.json",
    "semantic-words.json",
    "word-graph.json",
    "concept-clusters.json",
    "semantic-concepts.json"
}

DERIVATIVE_MARKERS = {
    "content-model.json",
    "content-graph.json",
    "content-registry.json"
}

def classify(text):

    reads_salience = TRUTH_LAYER in text
    reads_legacy = any(x in text for x in LEGACY_LAYERS)
    reads_derivative = any(x in text for x in DERIVATIVE_MARKERS)

    writes_outputs = bool(re.search(r"\.json|\.xml|\.md", text))

    # -----------------------------------------------------
    # CORE CONSUMER
    # -----------------------------------------------------
    if reads_salience and not reads_legacy:
        return "CORE_CONSUMER"

    # -----------------------------------------------------
    # LEGACY BRIDGE
    # -----------------------------------------------------
    if reads_legacy:
        return "LEGACY_BRIDGE"

    # -----------------------------------------------------
    # DERIVATIVE LAYER
    # -----------------------------------------------------
    if reads_derivative:
        return "DERIVATIVE_LAYER"

    # -----------------------------------------------------
    # ORPHAN CANDIDATE
    # -----------------------------------------------------
    if writes_outputs:
        return "ORPHAN_CANDIDATE"

    return "UNKNOWN"


# ---------------------------------------------------------
# ANALYSIS
# ---------------------------------------------------------

def analyze_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return None

    rel = path.replace(ROOT, "")

    return {
        "file": rel,
        "classification": classify(content),
        "reads_salience": TRUTH_LAYER in content,
        "reads_legacy_graph": any(x in content for x in LEGACY_LAYERS),
        "writes_output": bool(re.search(r"(>|\boutput\b|\.json|\.xml)", content)),
    }


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    files = find_files()

    results = []
    buckets = defaultdict(list)

    for f in files:
        res = analyze_file(f)
        if not res:
            continue

        results.append(res)
        buckets[res["classification"]].append(res["file"])

    # -----------------------------------------------------
    # REPORT
    # -----------------------------------------------------

    print("\n🧭 DEPENDENCY COLLAPSE MAP (v2)")
    print("=" * 50)

    for k, v in buckets.items():
        print(f"\n{str(k)}: {len(v)}")
        for f in sorted(v):
            print(" -", f)

    print("\n📦 writing map →", OUTPUT_FILE)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "summary": {k: len(v) for k, v in buckets.items()},
            "buckets": buckets,
            "files": results
        }, f, indent=2)


if __name__ == "__main__":
    main()
