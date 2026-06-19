import json
import os

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

INTEL_FILE = os.path.join(ROOT, "homepage-intelligence.json")
LABEL_FILE = os.path.join(ROOT, "homepage-ui-labels.json")
OUTPUT = os.path.join(ROOT, "homepage-intelligence-blocks.html")

def safe_load(path, fallback):
    if not os.path.exists(path):
        return fallback
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

intel = safe_load(INTEL_FILE, {})
labels = safe_load(LABEL_FILE, {
    "featured": "Points of attention",
    "concepts": "Fields of meaning"
})

def clean(url):
    return url.replace("https://unboundhealing.org", "").rstrip("/")

html = []

html.append("""
<!-- HOMEPAGE INTELLIGENCE BLOCKS -->
<section class="homepage-intelligence">
""")

# -------------------------
# Points of Attention
# -------------------------
html.append(f"""
<section class="points-of-attention">
  <h2>{labels["featured"]}</h2>
  <ul>
""")

for p in intel.get("featured_pages", [])[:5]:
    url = clean(p.get("url", "#"))
    label = url.strip("/") or "/"
    html.append(f'<li><a href="{url}">{label}</a></li>')

html.append("</ul></section>")

# -------------------------
# Fields of Meaning
# -------------------------
html.append(f"""
<section class="fields-of-meaning">
  <h2>{labels["concepts"]}</h2>
  <ul>
""")

for c in intel.get("concept_clusters", [])[:8]:
    html.append(f'<li>{c.get("concept","")}</li>')

html.append("</ul></section>")

html.append("</section>")

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(html))

print("✅ homepage-intelligence-blocks.html written (ROOT)")
