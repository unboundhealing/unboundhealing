#!/usr/bin/env python3

import json
import os
from pathlib import Path
from urllib.parse import urlparse


# =========================================================
# PATHS
# =========================================================

ROOT = Path(os.environ.get("GITHUB_WORKSPACE", os.getcwd()))
SAL_FILE = ROOT / "semantic-salience.json"


# =========================================================
# LOAD TRUTH LAYER
# =========================================================

def load():
    with open(SAL_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# =========================================================
# URL NORMALIZATION (MATCHES build-related-content)
# =========================================================

def normalize_url(url: str) -> str:
    if not isinstance(url, str):
        return ""

    url = url.strip()

    if not url.startswith("http"):
        return ""

    # ensure trailing slash consistency
    if not url.endswith("/"):
        url += "/"

    return url


# =========================================================
# SAFE LOOKUP HELPERS
# =========================================================

def safe_get_nodes(data):
    return data.get("nodes", {})


def safe_get_page_graph(data):
    return data.get("page_graph", {})


# =========================================================
# DEBUG REPORTING
# =========================================================

def debug_page(url, node, page_graph, nodes):
    print("\n" + "=" * 80)
    print("PAGE:", url)

    if not node:
        print("❌ NODE MISSING IN page_graph")
        return

    related = node.get("related", [])

    print("RELATED (raw):", len(related))

    if not related:
        print("⚠️ NO RELATED LINKS FOUND AT SOURCE LEVEL")
        return

    resolved = []
    missing = []
    malformed = []

    for r in related:
        nr = normalize_url(r)

        if not nr:
            malformed.append(r)
            continue

        target_node = nodes.get(nr)

        if not target_node:
            missing.append(nr)
        else:
            resolved.append(nr)

    print("✔ resolved:", len(resolved))
    print("❌ missing:", len(missing))
    print("⚠️ malformed:", len(malformed))

    if missing:
        print("\n--- MISSING NODE MATCHES ---")
        for m in missing[:10]:
            print("  -", m)

    if malformed:
        print("\n--- MALFORMED URLS ---")
        for m in malformed[:10]:
            print("  -", m)


# =========================================================
# MAIN ANALYSIS
# =========================================================

def main():

    print("\n🧠 LOADING semantic-salience.json...")
    data = load()

    nodes = safe_get_nodes(data)
    page_graph = safe_get_page_graph(data)

    print("📦 nodes:", len(nodes))
    print("📦 page_graph:", len(page_graph))

    if not page_graph:
        print("❌ page_graph is empty — upstream build failure likely")
        return

    # -----------------------------------------------------
    # CROSS-CHECK: page_graph vs nodes
    # -----------------------------------------------------

    print("\n🔍 RUNNING RELATED CONTENT RESOLUTION CHECK...")

    total_missing_pages = 0

    for url, node in page_graph.items():

        norm_url = normalize_url(url)

        if norm_url not in nodes:
            print("\n⚠️ PAGE EXISTS IN page_graph BUT NOT IN nodes:")
            print("  ", norm_url)
            total_missing_pages += 1
            continue

        debug_page(norm_url, node, page_graph, nodes)

    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("pages in page_graph:", len(page_graph))
    print("nodes available:", len(nodes))
    print("page_graph missing node matches:", total_missing_pages)

    print("\n🧭 INTERPRETATION GUIDE:")

    if total_missing_pages > 0:
        print("❌ ROOT ISSUE: URL mismatch between page_graph and nodes")
        print("   → build-related-content.py is not matching canonical URLs correctly")

    else:
        print("✔ page_graph ↔ nodes alignment OK")

    print("\nDONE\n")


if __name__ == "__main__":
    main()
