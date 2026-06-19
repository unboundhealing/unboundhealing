import json
import os

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

INTEL_FILE = os.path.join(ROOT, "homepage-intelligence.json")
LABEL_FILE = os.path.join(ROOT, "homepage-ui-labels.json")
TITLES_FILE = os.path.join(ROOT, "page-titles.json")

OUTPUT = os.path.join(ROOT, "assets", "homepage-intelligence-blocks.html")

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

def safe_load_json(path):
if not os.path.exists(path):
return {}

```
try:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
except Exception:
    return {}
```

intel = safe_load_json(INTEL_FILE)
labels_raw = safe_load_json(LABEL_FILE)
titles = safe_load_json(TITLES_FILE)

labels = {
"featured": labels_raw.get(
"featured",
"Arising observations…"
),
"concepts": labels_raw.get(
"concepts",
"Essential inspirations…"
),
}

print("INTEL RAW:", intel)

featured = intel.get("featured_pages", []) or []
concepts = intel.get("concept_clusters", []) or []

def clean_url(url):
if not url:
return "#"

```
cleaned = url.replace(
    "https://unboundhealing.org",
    ""
)

return cleaned.rstrip("/")
```

html = []

# =====================================

# FEATURED PAGES

# =====================================

html.append(f"""

<section class="points-of-attention">
  <h2>{labels["featured"]}</h2>
  <ul>
""")

if featured:

```
for page in featured[:3]:

    url = clean_url(page.get("url"))

    lookup_url = (
        url if url.endswith("/")
        else url + "/"
    )

    title = titles.get(
        lookup_url,
        url.strip("/")
           .replace("-", " ")
           .title()
    )

    html.append(
        f'<li><a href="{url}">{title}</a></li>'
    )
```

else:

```
html.append(
    "<li>Nothing appearing here just yet.</li>"
)
```

html.append("""

  </ul>
</section>
""")

# =====================================

# CONCEPT CLOUD

# =====================================

html.append(f"""

<section class="essential-inspirations">
  <h2>{labels["concepts"]}</h2>
  <p class="concept-cloud">
""")

if concepts:

```
for i, c in enumerate(concepts[:3]):

    html.append(
        c.get("concept", "unknown")
    )

    if i < len(concepts[:3]) - 1:
        html.append(" · ")
```

else:

```
html.append("listening · noticing · being")
```

html.append("""

  </p>
</section>
""")

# =====================================

# WRITE OUTPUT

# =====================================

final_html = "\n".join(html)

tmp_output = OUTPUT + ".tmp"

with open(tmp_output, "w", encoding="utf-8") as f:
f.write(final_html)

os.replace(tmp_output, OUTPUT)

print("OUTPUT PATH:", OUTPUT)
print("OUTPUT SIZE:", len(final_html))
print("FILE EXISTS:", os.path.exists(OUTPUT))

with open(OUTPUT, "r", encoding="utf-8") as f:
print(
"OUTPUT PREVIEW:",
f.read(300)
)

print("🏠 Homepage intelligence HTML rendered")
