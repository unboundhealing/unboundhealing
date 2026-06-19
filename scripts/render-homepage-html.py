import json
import os

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

INTEL_FILE = os.path.join(ROOT, "homepage-intelligence.json")
LABEL_FILE = os.path.join(ROOT, "homepage-ui-labels.json")

OUTPUT = os.path.join(ROOT, "homepage-intelligence-blocks.html")


def safe_load_json(path, fallback=None):
    if not os.path.exists(path):
        return fallback or {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


intel = safe_load_json(INTEL_FILE, {})
labels = safe_load_json(LABEL_FILE, {
    "featured": "Points of attention",
    "concepts": "Fields of meaning"
})

# 🔍 DEBUG CHECKPOINT (add this)
print("INTEL FILE PATH:", INTEL_FILE)
print("LABEL FILE PATH:", LABEL_FILE)
print("INTEL FILE EXISTS:", os.path.exists(INTEL_FILE))
print("LABEL FILE EXISTS:", os.path.exists(LABEL_FILE))
print("INTEL RAW:", intel)

def clean_url(url):
    return url.replace("https://unboundhealing.org", "").rstrip("/")


html = []

# =====================================================
# 🧠 VISIBILITY / DEBUG ANCHOR (THIS IS THE KEY FIX)
# =====================================================
html.append("""
<!-- INTELLIGENCE SYSTEM ACTIVE -->
<section class="homepage-intelligence-debug" style="display:none">
  homepage-intelligence-status: active
</section>
""")


# -----------------------------
# DATA
# -----------------------------
featured = intel.get("featured_pages", [])
concepts = intel.get("top_concepts", [])


# -----------------------------
# FALLBACK SAFETY
# -----------------------------
if not featured and not concepts:
    html.append("""
<section class="homepage-section points-of-attention">
  <h2>Points of attention</h2>
  <ul>
    <li>Intelligence layer active (no data yet)</li>
  </ul>
</section>
""")


# -----------------------------
# POINTS OF ATTENTION
# -----------------------------
if featured:
    html.append(f"""
<section class="homepage-section points-of-attention">
  <h2>{labels.get("featured")}</h2>
  <ul>
""")

    for page in featured[:5]:
        url = clean_url(page.get("url", "#"))
        label = url.strip("/") or "/"
        html.append(f'    <li><a href="{url}">{label}</a></li>')

    html.append("""
  </ul>
</section>
""")


# -----------------------------
# FIELDS OF MEANING
# -----------------------------
if concepts:
    html.append(f"""
<section class="homepage-section fields-of-meaning">
  <h2>{labels.get("concepts")}</h2>
  <ul>
""")

    for concept in concepts[:8]:
        name = concept.get("concept", "unknown")
        html.append(f'    <li>{name}</li>')

    html.append("""
  </ul>
</section>
""")


# -----------------------------
# FINAL SAFETY NET
# -----------------------------
if not html:
    html.append("""
<section>
  <h2>System Notice</h2>
  <p>Homepage intelligence generated but no output was produced.</p>
</section>
""")


# -----------------------------
# WRITE OUTPUT
# -----------------------------
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(html))

print("🏠 Homepage intelligence HTML rendered (ROOT output)")
