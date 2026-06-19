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

print("INTEL FILE PATH:", INTEL_FILE)
print("INTEL FILE EXISTS:", os.path.exists(INTEL_FILE))
print("INTEL RAW:", intel)


def clean_url(url):
    return url.replace("https://unboundhealing.org", "").rstrip("/")


html = []

# =============================
# VISIBILITY ANCHOR (FIXED)
# =============================
html.append("""
<!-- INTELLIGENCE SYSTEM ACTIVE -->
<section class="homepage-intelligence-debug">
  homepage-intelligence-status: active
</section>
""")

featured = intel.get("featured_pages", [])
concepts = intel.get("concept_clusters", [])  # IMPORTANT: matches your actual JSON

# =============================
# FEATURED
# =============================
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

    html.append("</ul></section>")

# =============================
# CONCEPTS
# =============================
if concepts:
    html.append(f"""
<section class="homepage-section fields-of-meaning">
  <h2>{labels.get("concepts")}</h2>
  <ul>
""")

    for concept in concepts[:8]:
        name = concept.get("concept", "unknown")
        html.append(f'    <li>{name}</li>')

    html.append("</ul></section>")

# =============================
# GUARANTEE OUTPUT
# =============================
if len(html) == 1:
    html.append("""
<section>
  <h2>System Notice</h2>
  <p>No featured content rendered.</p>
</section>
""")

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(html))

print("🏠 Homepage intelligence HTML rendered (ROOT output)")
