#!/usr/bin/env python3
import json
import os

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

PATH = os.path.join(ROOT, "semantic-salience.json")

print("🔍 Inspecting semantic-salience.json...")

if not os.path.exists(PATH):
    print("❌ semantic-salience.json missing")
    exit(1)

with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

print("✅ truth layer loaded")

print("📦 nodes:", len(data.get("nodes", {})))
print("📦 edges:", len(data.get("edges", [])))
print("🧠 concepts:", len(data.get("salience", {})))

top = sorted(
    data.get("salience", {}).items(),
    key=lambda x: x[1]["score"],
    reverse=True
)[:10]

print("\n🔥 TOP CONCEPTS:")
for k, v in top:
    print(k, "→", round(v["score"], 5))
