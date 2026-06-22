import json
import sys

INPUT = "content-model.json"

try:
    with open(INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception as e:
    print("❌ JSON parse error:", e)
    sys.exit(1)

if not isinstance(data, dict):
    print("❌ Invalid structure: not a dict")
    sys.exit(1)

print("🔑 TOP-LEVEL KEYS:", list(data.keys()))

if len(data.keys()) == 0:
    print("❌ EMPTY MODEL DETECTED - STOPPING BUILD")
    sys.exit(1)

for k in ["pages", "nodes", "content"]:
    if k in data:
        val = data[k]
        size = len(val) if isinstance(val, list) else "non-list"
        print(f"✅ Found key: {k} (count={size})")
