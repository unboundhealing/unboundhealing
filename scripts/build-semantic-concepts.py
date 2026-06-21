import json
import os
import re
from bs4 import BeautifulSoup
from collections import Counter

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

OUTPUT = os.path.join(
    ROOT,
    "semantic-concepts.json"
)

# -----------------------------
# Locate pages
# -----------------------------

def find_html_files():

    html_files = []

    for root, _, files in os.walk(ROOT):

        for f in files:

            if f.endswith(".html"):
                html_files.append(
                    os.path.join(root, f)
                )

    return html_files


# -----------------------------
# Helpers
# -----------------------------

STOP = {
    "the","a","an",
    "and","or","but",
    "to","of","in","on","for",
    "with","from","into",
    "that","this","these","those",
    "is","are","was","were",
    "be","been","being"
}


def clean_text(text):

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\s-]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# -----------------------------
# Extract concepts
# -----------------------------

pages = []

for file in find_html_files():

    try:

        with open(
            file,
            "r",
            encoding="utf-8"
        ) as f:

            soup = BeautifulSoup(
                f,
                "html.parser"
            )

        text = clean_text(
            soup.get_text(" ")
        )

        words = text.split()

        concepts = Counter()

        # two-word phrases

        for i in range(len(words) - 1):

            a = words[i]
            b = words[i + 1]

            if (
                a in STOP or
                b in STOP
            ):
                continue

            phrase = f"{a} {b}"

            concepts[phrase] += 1

        rel = (
            file.replace(ROOT, "")
                .replace("index.html", "")
        )

        rel = rel.lstrip("/")

        url = (
            "https://unboundhealing.org/"
            + rel
        )

        pages.append({
            "url": url,
            "concepts": [
                c
                for c, n
                in concepts.items()
                if n >= 2
            ]
        })

    except Exception:
        pass


# -----------------------------
# Save
# -----------------------------

with open(
    OUTPUT,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        {"pages": pages},
        f,
        indent=2,
        ensure_ascii=False
    )

print("🌱 Semantic concepts built")
print("📦 Wrote:", OUTPUT)
