#!/usr/bin/env python3
import json
import os

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())
PATH = os.path.join(ROOT, "semantic-salience.json")

print("🔍 Inspecting semantic-salience.json...")

# =========================================================
# FILE SAFETY CHECK
# =========================================================

if not os.path.exists(PATH):
    print("❌ semantic-salience.json missing")
    exit(1)

with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

print("✅ truth layer loaded")


# =========================================================
# STRUCTURE OVERVIEW (OBSERVATIONAL ONLY)
# =========================================================

nodes = data.get("nodes", {}) or {}
edges = data.get("edges", []) or {}

print("📦 nodes:", len(nodes))
print("📦 edges:", len(edges))


# =========================================================
# STRICT SALIENCE CHECK (NO FALLBACKS)
# =========================================================

salience = data.get("salience", None)

if salience is None:
    print("\n🧠 salience layer: NOT PRESENT")
    print("⚠️ semantic-salience is operating in GRAPH-ONLY MODE")
    print("⚠️ NO semantic ranking or concept scoring available")

elif isinstance(salience, dict) and salience:
    print("\n🧠 salience layer: ACTIVE")
    print("🧠 concepts:", len(salience))

    top = sorted(
        salience.items(),
        key=lambda x: x[1].get("score", 0),
        reverse=True
    )[:10]

    print("\n🔥 TOP CONCEPTS:")
    for k, v in top:
        print(k, "→", round(v.get("score", 5), 5))

else:
    print("\n🧠 salience layer: EMPTY OR INVALID")
    print("⚠️ semantic-salience exists but contains no usable scoring data")


# =========================================================
# EDGE HEALTH (PURE STRUCTURAL METRICS ONLY)
# =========================================================

print("\n🔗 edge sanity check:")

if edges:
    avg = len(edges) / max(len(nodes), 1)
    print("avg edges per node ~", round(avg, 2))
else:
    print("⚠️ no edges present")


# =========================================================
# NODE CONCEPT AUDIT (STRUCTURAL ONLY — NO DERIVATION)
# =========================================================

concept_count = 0
concept_nodes = 0

for node in nodes.values():
    concepts = node.get("concepts", [])

    if isinstance(concepts, list):
        if concepts:
            concept_nodes += 1
            concept_count += len(concepts)

print("\n🧭 concept field audit (structural only):")
print("nodes with concepts:", concept_nodes)
print("total concept references:", concept_count)

if concept_nodes == 0:
    print("⚠️ WARNING: no node-level concepts found")
    print("⚠️ upstream semantic extraction may be failing")


# =========================================================
# FINAL SUMMARY
# =========================================================

print("\n📊 SUMMARY:")
print("nodes:", len(nodes))
print("edges:", len(edges))
print("salience present:", isinstance(salience, dict))

print("\n🧭 single-truth policy:")
print("✔ semantic-salience is treated as authoritative source")
print("✔ no graph-derived semantic inference performed here")

print("\n✅ inspection complete")
