#!/usr/bin/env python3
import json
import os
import sys

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())
PATH = os.path.join(ROOT, "assets/homepage-intelligence.json")

print("🏠 Running homepage intelligence diagnostic...\n")


# -------------------------------------------------------
# 1. FILE CHECK
# -------------------------------------------------------

if not os.path.exists(PATH):
    print("❌ homepage-intelligence.json missing — HARD STOP")
    sys.exit(1)

try:
    with open(PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception as e:
    print("❌ JSON parse failure:", e)
    sys.exit(1)

print("✅ file loaded")


# -------------------------------------------------------
# 2. STRUCTURE VALIDATION
# -------------------------------------------------------

required_keys = ["homepage_intelligence", "source", "status"]

missing = [k for k in required_keys if k not in data]

if missing:
    print("❌ missing required keys:", missing)
    sys.exit(1)

hi = data.get("homepage_intelligence", {})

for k in ["arising_observations", "essential_inspirations", "node_count", "edge_count"]:
    if k not in hi:
        print(f"❌ missing homepage_intelligence key: {k}")
        sys.exit(1)

print("✅ structure valid")


# -------------------------------------------------------
# 3. OBSERVATIONS CHECK
# -------------------------------------------------------

obs = hi.get("arising_observations", [])

print(f"\n📊 observations: {len(obs)}")

if not obs:
    print("⚠️ no arising observations found")

urls = set()

for o in obs:
    url = o.get("url")
    title = o.get("title")
    score = o.get("score")

    if not url:
        print("⚠️ observation missing url:", o)
        continue

    if url in urls:
        print("⚠️ duplicate observation url:", url)

    urls.add(url)

    if title is None or title == "":
        print("⚠️ missing title for:", url)

    if not isinstance(score, (int, float)):
        print("⚠️ invalid score for:", url, score)


# -------------------------------------------------------
# 4. ESSENTIAL INSPIRATIONS CHECK
# -------------------------------------------------------

insp = hi.get("essential_inspirations", [])

print(f"\n📊 inspirations: {len(insp)}")

generic = {"concept", "page", "something", "unknown"}

for i in insp:
    concept = i.get("concept", "")
    freq = i.get("frequency", 0)

    if concept.lower() in generic:
        print(f"⚠️ generic concept detected: {concept}")

    if not isinstance(freq, int):
        print(f"⚠️ invalid frequency: {concept}")


# -------------------------------------------------------
# 5. CONSISTENCY CHECK WITH SOURCE GRAPH
# -------------------------------------------------------

nodes = hi.get("node_count", 0)
edges = hi.get("edge_count", 0)

print("\n🔗 graph consistency:")
print("nodes:", nodes)
print("edges:", edges)

# no strict enforcement — just informational

# -------------------------------------------------------
# 5. INSPIRATIONS SOURCE CHECK
# -------------------------------------------------------

print("\n🧠 TOP INSPIRATIONS\n")

salience = semantic_data.get("salience", {})

# Highest weighted concepts (current weighting)
top = sorted(
    salience.items(),
    key=lambda item: (
        item[1].get("frequency", 0)
        + item[1].get("search_signal", 0)
        + item[1].get("excerpt_signal", 0)
        + item[1].get("connectivity", 0)
    ),
    reverse=True,
)[:10]

for concept, info in top:

    evidence = info.get("evidence", {})

    print(f"\n{concept}")

    print(f"  frequency:       {info.get('frequency',0)}")
    print(f"  connectivity:   {info.get('connectivity',0)}")
    print(f"  search signal:  {info.get('search_signal',0)}")
    print(f"  excerpt signal: {info.get('excerpt_signal',0)}")

    print(
        f"  pages:          {len(evidence.get('search_pages',[]))}"
    )

# -------------------------------------------------------
# 6. FINAL SUMMARY
# -------------------------------------------------------

print("\n📊 SUMMARY")

print("observations:", len(obs))
print("inspirations:", len(insp))
print("status:", data.get("status"))

print("\n🧭 homepage diagnostic complete")
print("✔ structure valid")
print("✔ observations scanned")
print("✔ inspiration layer checked")
