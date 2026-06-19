import json
import os

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

INTEL_FILE = os.path.join(ROOT, "homepage-intelligence.json")
LABEL_FILE = os.path.join(ROOT, "homepage-ui-labels.json")

# ✅ ROOT LEVEL OUTPUT (Option B)
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

def clean_url(url):
    return url.replace("https://unboundhealing.org", "").rstrip("/")

html = []

html.append("""
<!-- HOMEPAGE INTELLIGENCE BLOCKS -->
""")

# -----------------------------
# POINTS OF ATTENTION
# -----------------------------
featured = intel.get("featured_pages", [])

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
concepts = intel.get("top_concepts", [])

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

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(html))

print("🏠 Homepage intelligence HTML rendered (ROOT output)")
