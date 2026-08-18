#!/usr/bin/env python3
import json
import os
from pathlib import Path

ROOT = Path(os.environ.get("GITHUB_WORKSPACE", os.getcwd()))

SAL = ROOT / "assets/semantic-salience.json"
VOCAB = ROOT / "assets/vocabulary.json"

# ---------------------------------------------------------
# LOAD HELPERS
# ---------------------------------------------------------

def load(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"❌ failed to load {path}: {e}")
        return None


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():
    print("🧭 Running site integrity diagnostic...\n")

    sal = load(SAL)
    vocabulary = load(VOCAB)

    if not sal:
        print("❌ semantic-salience missing — abort")
        return

    sal_nodes = sal.get("nodes", {})
    sal_urls = set(sal_nodes.keys())

    vocab_urls = set(vocabulary.keys()) if vocabulary else set()

    # -----------------------------------------------------
    # 1. NODE PARITY CHECK
    # -----------------------------------------------------

    print("🔗 node parity check...")

    missing_in_vocab = sal_urls - vocab_urls
    missing_in_sal = vocab_urls - sal_urls

    print(f"nodes in salience: {len(sal_urls)}")
    print(f"nodes in vocabulary: {len(vocab_urls)}")

    if missing_in_vocab:
        print("\n⚠️ missing in vocabulary:", len(missing_in_vocab))
        for u in list(missing_in_vocab)[:5]:
            print("  -", u)

    # -----------------------------------------------------
    # 2. FIELD COMPLETENESS CHECK
    # -----------------------------------------------------

    print("\n📦 field completeness...")

    missing_fields = {
        "title": 0,
        "description": 0,
        "excerpt": 0,
        "search_text": 0,
        "concepts": 0
    }

    for url, node in sal_nodes.items():
        for f in missing_fields:
            if not node.get(f):
                missing_fields[f] += 1

    for k, v in missing_fields.items():
        print(f"{k}: {v} missing")

    # -----------------------------------------------------
    # 3. TAG ↔ CONCEPT DRIFT
    # -----------------------------------------------------

    print("\n🧠 tag vs concept alignment...")

    drift = 0

    for url, node in sal_nodes.items():

        # -------------------------------------------------
        # STRUCTURAL VALIDATION (early visibility)
        # -------------------------------------------------

        if not node.get("concepts"):
            print("⚠️ empty concepts:", url)

        # -------------------------------------------------
        # ALIGNMENT LOGIC
        # -------------------------------------------------      
        
        concepts = set(node.get("concepts", []))
        entry = vocabulary.get(url, {}) if vocabulary else {}

        tags = set(entry.get("tags", []))
        aliases = set(entry.get("aliases", []))

        v = tags | aliases

        if concepts and not v:
            drift += 1
        elif v and not concepts:
            drift += 1
        elif concepts and v:
            if len(concepts & v) == 0:
                drift += 1

    print("drifted nodes:", drift)

    # -----------------------------------------------------
    # 4. SEARCH TEXT HEALTH
    # -----------------------------------------------------

    print("\n🔎 search_text coverage...")

    empty_search = 0

    for url, node in sal_nodes.items():
        st = node.get("search_text", "")
        if not isinstance(st, str) or not st.strip():
            empty_search += 1

    print("empty search_text:", empty_search)

    # -----------------------------------------------------
    # 5. SUMMARY
    # -----------------------------------------------------

    print("\n📊 FINAL SUMMARY")
    print("================")
    print("salience nodes:", len(sal_urls))
    print("vocabulary nodes:", len(vocab_urls))
    print("missing vocabulary coverage:", len(missing_in_vocab))
    print("missing homepage coverage:", len(missing_in_home))
    print("field gaps:", sum(missing_fields.values()))
    print("concept/tag drift:", drift)

    print("\n🧭 interpretation:")
    print("- salience is truth layer")
    print("- vocabulary + search index are projections")
    print("- drift indicates semantic inconsistency")

    print("\n✅ site integrity diagnostic complete")


if __name__ == "__main__":
    main()
