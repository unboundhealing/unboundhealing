#!/usr/bin/env python3
import json
import os
from pathlib import Path

ROOT = Path(os.environ.get("GITHUB_WORKSPACE", os.getcwd()))
FILE = ROOT / "assets/tags.json"

# -----------------------------
# LOAD
# -----------------------------

def load():
    if not FILE.exists():
        print("❌ tags.json missing")
        return None
    try:
        return json.loads(FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print("❌ failed to load tags.json:", e)
        return None


# -----------------------------
# HELPERS
# -----------------------------

def safe_list(x):
    return x if isinstance(x, list) else []


# -----------------------------
# MAIN DIAGNOSTIC
# -----------------------------

def main():
    print("🧪 Running tags diagnostic...")

    data = load()
    if not data:
        print("❌ aborting")
        return

    total = len(data)
    missing_tags = 0
    missing_concepts = 0
    empty_nodes = 0

    mismatch_nodes = 0
    heavy_nodes = 0

    print(f"📦 nodes: {total}")

    for url, tags in data.items():

        tags = safe_list(tags)

        if not tags:
            empty_nodes += 1

        # heuristics
        if len(tags) == 0:
            missing_tags += 1

        if len(tags) > 6:
            heavy_nodes += 1

        # NOTE: we cannot directly compare concepts here
        # unless semantic-salience is loaded — so we only infer structure

        # flag structural weirdness
        if any("-" in t and len(t.split("-")) > 3 for t in tags):
            print("⚠️ deep compound tag detected:", url)

    # -----------------------------
    # SUMMARY
    # -----------------------------

    print("\n📊 TAGS DIAGNOSTIC SUMMARY")
    print("==========================")
    print("nodes:", total)
    print("empty tag lists:", empty_nodes)
    print("missing tags:", missing_tags)
    print("heavy tag nodes (>6):", heavy_nodes)

    print("\n🧭 interpretation:")
    print("- tags are derived from concepts (expected)")
    print("- this tool checks structural health only")
    print("- semantic correctness lives in semantic-salience layer")

    print("\n✅ diagnosis complete")


if __name__ == "__main__":
    main()
