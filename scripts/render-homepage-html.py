import json
import os

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

INTEL_FILE = os.path.join(ROOT, "homepage-intelligence.json")
LABEL_FILE = os.path.join(ROOT, "homepage-ui-labels.json")

OUTPUT = os.path.join(ROOT, "assets", "homepage-intelligence-blocks.html")

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)


def safe_load_json(path):
    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def clean_url(url):
    if not url:
        return "#"
    return url.replace("https://unboundhealing.org", "").rstrip("/")


intel = safe_load_json(INTEL_FILE)
labels_raw = safe_load_json(LABEL_FILE)

labels = {
    "featured": labels_raw.get("featured", "Points of attention"),
    "concepts": labels_raw.get("concepts", "Fields of meaning"),
}

print("INTEL RAW:", intel)

featured = intel.get("featured_pages", []) or []
concepts = intel.get("concept_clusters", []) or []

html = []

# FEATURED
html.append(f"""
<section class="points-of-attention">
  <h2>{labels["featured"]}</h2>
  <ul>
""")

if featured:
    for page in featured[:3]:
        url = clean_url(page.get("url"))
        html.append(f'<li><a href="{url}">{url}</a></li>')
else:
    html.append("<li>No featured pages found</li>")

html.append("</ul></section>")

# CONCEPTS
html.append(f"""
<section class="fields-of-meaning">
  <h2>{labels["concepts"]}</h2>
  <ul>
""")

if concepts:
    for c in concepts[:3]:
        html.append(f'<li>{c.get("concept", "unknown")}</li>')
else:
    html.append("<li>No concepts found</li>")

html.append("</ul></section>")

final_html = "\n".join(html)

tmp_output = OUTPUT + ".tmp"

with open(tmp_output, "w", encoding="utf-8") as f:
    f.write(final_html)

os.replace(tmp_output, OUTPUT)

print("OUTPUT PATH:", OUTPUT)
print("OUTPUT SIZE:", len(final_html))
print("🏠 Homepage intelligence HTML rendered")
