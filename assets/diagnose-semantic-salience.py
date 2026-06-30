#!/usr/bin/env python3
import json
import os
import sys

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())
PATH = os.path.join(ROOT, "assets/semantic-salience.json")


# -------------------------------------------------------
# HELPERS
# -------------------------------------------------------

def fail(msg):
    print(f"❌ {msg}")
    sys.exit(1)

def warn(msg):
    print(f"⚠️ {msg}")

def ok(msg):
    print(f"✅ {msg}")


# -------------------------------------------------------
# LOAD FILE
# -------------------------------------------------------

print("🔍 Diagnosing semantic-salience...")

if not os.path.exists(PATH):
    fail("assets/semantic-salience.json missing")

try:
    with open(PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception as e:
    fail(f"JSON parse error: {e}")

if not isinstance(data, dict):
    fail("semantic-salience must be a dict at root")

ok("file loaded")


# -------------------------------------------------------
# REQUIRED STRUCTURE CHECK
# -------------------------------------------------------

required_keys = ["nodes", "edges", "page_graph"]

for k in required_keys:
    if k not in data:
        fail(f"missing required key: {k}")

nodes = data["nodes"]
edges = data["edges"]
page_graph = data["page_graph"]

if not isinstance(nodes, dict):
    fail("nodes must be dict")

if not isinstance(edges, list):
    fail("edges must be list")

if not isinstance(page_graph, dict):
    fail("page_graph must be dict")

ok("structure valid")


# -------------------------------------------------------
# NODE VALIDATION
# -------------------------------------------------------

missing_search_text = 0
missing_concepts = 0

for url, node in nodes.items():

    # search_text MUST exist
    st = node.get("search_text", None)
    if not isinstance(st, str) or not st.strip():
        fail(f"{url}: invalid or missing search_text")

    # concepts MUST exist
    concepts = node.get("concepts", None)
    if not isinstance(concepts, list):
        fail(f"{url}: concepts must be list")

    if len(concepts) == 0:
        missing_concepts += 1

    # optional but recommended sanity check
    if len(st) < 10:
        warn(f"{url}: unusually short search_text")

ok("node validation passed")


# -------------------------------------------------------
# EDGE SANITY CHECK
# -------------------------------------------------------

if edges:
    avg_edges = len(edges) / max(len(nodes), 1)
    print(f"🔗 avg edges per node: {avg_edges:.2f}")
else:
    warn("no edges found")


# -------------------------------------------------------
# PAGE GRAPH CHECK
# -------------------------------------------------------

sample_key = next(iter(page_graph.keys()), None)

if not sample_key:
    fail("page_graph is empty")

sample_val = page_graph[sample_key]

if not isinstance(sample_val, dict):
    fail("page_graph entries must be dicts")

if "concepts" not in sample_val:
    fail("page_graph entries missing 'concepts'")

ok("page_graph valid")


# -------------------------------------------------------
# FINAL SUMMARY (STRICT, NOT DEBUG)
# -------------------------------------------------------

print("\n📊 SUMMARY")
print(f"nodes: {len(nodes)}")
print(f"edges: {len(edges)}")
print(f"missing concept lists: {missing_concepts}")

if missing_concepts > 0:
    warn(f"{missing_concepts} nodes have empty concepts lists (non-fatal)")

print("\n🧭 semantic-salience diagnosis complete")

ok("semantic-salience is structurally valid")
