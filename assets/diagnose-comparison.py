#!/usr/bin/env python3

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAL_FILE = ROOT / "assets" / "semantic-salience.json"


# -------------------------------------------------------
# LOAD DATA
# -------------------------------------------------------

with open(SAL_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

nodes = data["nodes"]
page_graph = data["page_graph"]


# -------------------------------------------------------
# LOAD PAGE
# -------------------------------------------------------

def print_divider():
    print("\n" + "=" * 80 + "\n")


def compare(url):
    node = nodes.get(url, {})

    print_divider()
    print("PAGE DIAGNOSTIC")
    print(url)

    print("\nTITLE:")
    print(" ", node.get("title", ""))

    print("\nCONCEPTS:")
    for c in node.get("concepts", []):
        print(" •", c)

    print("\nEXCERPT:")
    print(" ", node.get("excerpt", "")[:200])

    print("\nWORD COUNT:")
    print(" ", node.get("word_count", 0))

    related = page_graph.get(url, {}).get("related", [])

    print("\nTOP RELATIONSHIPS:\n")

    for i, other in enumerate(related[:10], 1):

        other_node = nodes.get(other, {})

        print(f"{i}. {other_node.get('title', '(untitled)')}")
        print(f"   {other}")

        # ---------------------------------------------------
        # FULL SIGNAL BREAKDOWN
        # ---------------------------------------------------

        print("\n   SIGNAL BREAKDOWN:")

        a = node
        b = other_node

        # concept overlap
        ca = set(a.get("concepts", []))
        cb = set(b.get("concepts", []))
        concept_overlap = len(ca & cb)

        print(f"   concept_overlap: {concept_overlap}")

        # search text similarity
        sa = set(a.get("search_text", "").split())
        sb = set(b.get("search_text", "").split())
        search_overlap = len(sa & sb)

        print(f"   search_similarity: {search_overlap}")

        # excerpt similarity
        ea = set(a.get("excerpt", "").split())
        eb = set(b.get("excerpt", "").split())
        excerpt_overlap = len(ea & eb)

        print(f"   excerpt_similarity: {excerpt_overlap}")

        # word count similarity (normalized)
        wa = a.get("word_count", 0)
        wb = b.get("word_count", 0)

        if max(wa, wb) > 0:
            word_similarity = 1 - abs(wa - wb) / max(wa, wb)
        else:
            word_similarity = 0

        print(f"   word_similarity: {word_similarity:.2f}")

        # quick interpretation layer
        total_signal = concept_overlap + search_overlap + excerpt_overlap

        if total_signal == 0:
            print("   ⚠️ weak match (likely structural coincidence)")
        elif concept_overlap > 0:
            print("   ✔ semantic alignment (shared concepts)")
        elif search_overlap > 0:
            print("   ◐ lexical alignment (text-based match)")

        print()


# -------------------------------------------------------
# MAIN ENTRY
# -------------------------------------------------------

if __name__ == "__main__":

    print("\nDIAGNOSTIC COMPARISON TOOL")

    # pick first page for now (we can extend later)
    first_url = list(nodes.keys())[0]

    compare(first_url)
