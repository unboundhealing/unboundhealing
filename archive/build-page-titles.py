from bs4 import BeautifulSoup
import os
import json

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

titles = {}

for root, dirs, files in os.walk(ROOT):

    if ".git" in root:
        continue

    for file in files:

        if file != "index.html":
            continue

        path = os.path.join(root, file)

        try:

            with open(path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f.read(), "html.parser")

            rel = os.path.relpath(path, ROOT)

            url = "/" + os.path.dirname(rel).replace("\\", "/") + "/"

            if url == "/./":
                url = "/"

            title = None

            h1 = soup.find("h1")

            if h1:
                title = h1.get_text(" ", strip=True)

            if not title:

                meta = soup.find("meta", attrs={"property": "og:title"})

                if meta:
                    title = meta.get("content")

            if not title:

                title_tag = soup.find("title")

                if title_tag:
                    title = title_tag.get_text(strip=True)

            if title:

                titles[url] = title

        except Exception as e:
            print("Skipping:", path, e)

with open(
    os.path.join(ROOT, "page-titles.json"),
    "w",
    encoding="utf-8"
) as f:

    json.dump(titles, f, indent=2)

print(f"✅ Built {len(titles)} page titles")
