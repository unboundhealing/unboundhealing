#!/usr/bin/env python3
import os
from collections import defaultdict

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

print("🧭 Dependency diagnostic starting...\n")


# -------------------------------------------------------
# 1. SCAN FILES (READ ONLY)
# -------------------------------------------------------

def scan_scripts(root):
    scripts = []

    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if f.endswith(".py") or f.endswith(".sh"):
                path = os.path.join(dirpath, f)
                rel = os.path.relpath(path, root)
                scripts.append(rel)

    return sorted(scripts)


files = scan_scripts(ROOT)


# -------------------------------------------------------
# 2. CLASSIFY DEPENDENCIES (READ ONLY ANALYSIS)
# -------------------------------------------------------

classification = {
    "UNKNOWN": [],
    "CORE_CONSUMER": [],
    "ORPHAN_CANDIDATE": [],
    "LEGACY_BRIDGE": []
}


for f in files:

    if "generate-site" in f or "build-search-index" in f:
        classification["CORE_CONSUMER"].append(f)

    elif "diagnose" in f:
        classification["CORE_CONSUMER"].append(f)

    elif "inspect" in f:
        classification["LEGACY_BRIDGE"].append(f)

    else:
        classification["UNKNOWN"].append(f)


# -------------------------------------------------------
# 3. REPORT
# -------------------------------------------------------

print("🧭 DEPENDENCY DIAGNOSTIC REPORT")
print("=" * 40)

for k, v in classification.items():
    print(f"\n{k}: {len(v)}")
    for item in v:
        print(" -", item)


# -------------------------------------------------------
# 4. HEALTH SUMMARY
# -------------------------------------------------------

print("\n📊 SUMMARY")

total = len(files)
print("total scripts:", total)

core = len(classification["CORE_CONSUMER"])
unknown = len(classification["UNKNOWN"])

print("core systems:", core)
print("unknown:", unknown)

if unknown > 0:
    print("\n⚠️ Review recommended: unknown scripts exist")

print("\n✅ dependency diagnostic complete")
