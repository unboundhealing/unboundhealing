#!/usr/bin/env python3

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SAL_FILE = ROOT / "assets" / "semantic-salience.json"

with open(SAL_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

nodes = data["nodes"]
page_graph = data["page_graph"]

print("=" * 80)
print("PAGE GRAPH DIAGNOSTIC")
print("=" * 80)

for url in sorted(page_graph.keys()):

    node = nodes.get(url, {})

    print()
    print("=" * 80)
    print(url)

    print("\nTitle:")
    print(" ", node.get("title", ""))

    print("\nConcepts:")
    for c in node.get("concepts", []):
        print(" •", c)

    print("\nExcerpt:")
    excerpt = node.get("excerpt", "")
    if excerpt:
        print(" ", excerpt[:180])
    else:
        print("  (none)")

    print("\nRelated:")

    for i, related in enumerate(page_graph[url].get("related", []), start=1):

        related_node = nodes.get(related, {})

        print(
            f"{i:2d}. {related_node.get('title','(untitled)')}"
        )
        print(f"    {related}")

print()
print("=" * 80)
print(f"Pages: {len(page_graph)}")
