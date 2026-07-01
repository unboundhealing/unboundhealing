#!/usr/bin/env python3
import json
import os
from pathlib import Path

ROOT = Path(os.environ.get("GITHUB_WORKSPACE", os.getcwd()))

SAL = ROOT / "assets/semantic-salience.json"
TAGS = ROOT / "assets/tags.json"
HOMEPAGE = ROOT / "assets/homepage-intelligence.json"

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
    tags = load(TAGS)
    home = load(HOMEPAGE)

    if not sal:
        print("❌ semantic-salience missing — abort")
        return

    sal_nodes = sal.get("nodes", {})
    sal_urls = set(sal_nodes.keys())

    tag_urls = set(tags.keys()) if tags else set()
    home_urls = set()

    if home and isinstance(home.get("homepage_intelligence"), dict):
        for item in home["homepage_intelligence"].get("arising_observations", []):
            home_urls.add(item.get("url", ""))

    # -----------------------------------------------------
    # 1. NODE PARITY CHECK
    # -----------------------------------------------------

    print("🔗 node parity check...")

    missing_in_tags = sal_urls - tag_urls
    missing_in_sal = tag_urls - sal_urls
    missing_in_home = sal_urls - home_urls if home_urls else set()

    print(f"nodes in salience: {len(sal_urls)}")
    print(f"nodes in tags: {len(tag_urls)}")
    print(f"nodes in homepage: {len(home_urls)}")

    if missing_in_tags:
        print("\n⚠️ missing in tags:", len(missing_in_tags))
        for u in list(missing_in_tags)[:5]:
            print("  -", u)

    if missing_in_home:
        print("\n⚠️ missing in homepage intelligence:", len(missing_in_home))
        for u in list(missing_in_home)[:5]:
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
        t = set(tags.get(url, []))

        if concepts and not t:
            drift += 1
        elif t and not concepts:
            drift += 1
        elif concepts and t:
            if len(concepts & t) == 0:
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
    print("tag nodes:", len(tag_urls))
    print("homepage nodes:", len(home_urls))
    print("missing tag coverage:", len(missing_in_tags))
    print("missing homepage coverage:", len(missing_in_home))
    print("field gaps:", sum(missing_fields.values()))
    print("concept/tag drift:", drift)

    print("\n🧭 interpretation:")
    print("- salience is truth layer")
    print("- tags + homepage + search index are projections")
    print("- drift indicates semantic inconsistency")

    print("\n✅ site integrity diagnostic complete")


if __name__ == "__main__":
    main()
