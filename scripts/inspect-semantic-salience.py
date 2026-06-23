#!/usr/bin/env python3
import json
import os
from collections import defaultdict

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())
PATH = os.path.join(ROOT, "semantic-salience.json")

print("🔍 Inspecting semantic-salience.json...")

if not os.path.exists(PATH):
    print("❌ semantic-salience.json missing")
    exit(1)

with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

print("✅ truth layer loaded")


# =========================================================
# BASIC STRUCTURE REPORT
# =========================================================

nodes = data.get("nodes", {}) or {}
edges = data.get("edges", []) or []

print("📦 nodes:", len(nodes))
print("📦 edges:", len(edges))


# =========================================================
# SAFE CONCEPT EXTRACTION (NO ASSUMPTIONS)
# =========================================================

salience = data.get("salience", None)

# ---------------------------------------------------------
# CASE 1: legacy / older pipeline still present
# ---------------------------------------------------------
if isinstance(salience, dict) and salience:
    print("🧠 salience layer detected (legacy mode)")

    print("🧠 concepts:", len(salience))

    top = sorted(
        salience.items(),
        key=lambda x: x[1].get("score", 0),
        reverse=True
    )[:10]

    print("\n🔥 TOP CONCEPTS:")
    for k, v in top:
        print(k, "→", round(v.get("score", 0), 5))


# ---------------------------------------------------------
# CASE 2: v3 system (nodes + edges only)
# ---------------------------------------------------------
else:
    print("🧠 salience layer not found → deriving from graph")

    # derive concept frequencies from nodes
    concept_frequency = defaultdict(int)

    for node_url, node_data in nodes.items():
        concepts = node_data.get("concepts", [])

        if isinstance(concepts, list):
            for c in concepts:
                concept_frequency[c] += 1

    print("🧠 derived concepts:", len(concept_frequency))

    if concept_frequency:
        top = sorted(
            concept_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        print("\n🔥 TOP CONCEPTS (derived):")
        for k, v in top:
            print(k, "→", v)
    else:
        print("\n🔥 TOP CONCEPTS: (none found)")
        print("⚠️ Suggestion: upstream concept extraction is not populating nodes.concepts")


# =========================================================
# EDGE HEALTH CHECK
# =========================================================

print("\n🔗 edge sanity check:")

if edges:
    print("avg edges per node ~", round(len(edges) / max(len(nodes), 1), 2))
else:
    print("⚠️ no edges present")


# =========================================================
# FINAL SUMMARY
# =========================================================

print("\n📊 SUMMARY:")
print("nodes:", len(nodes))
print("edges:", len(edges))
print("salience present:", isinstance(salience, dict))

print("\n✅ inspection complete")
