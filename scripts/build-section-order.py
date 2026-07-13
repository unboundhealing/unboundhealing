#!/usr/bin/env python3

import json
from pathlib import Path
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]

OUTPUT_DIR = ROOT / "assets" / "navigation"


SECTIONS = {
    "opening": {
        "index": ROOT / "opening" / "index.html",
        "prefix": "/opening/"
    },
    "concept": {
        "index": ROOT / "concept" / "index.html",
        "prefix": "/concept/"
    }
}


def build_section_order(name, config):

    index_file = config["index"]
    prefix = config["prefix"]

    soup = BeautifulSoup(
        index_file.read_text(encoding="utf-8"),
        "html.parser"
    )

    main = soup.find("main")

    order = []

    if not main:
        print(f"⚠️ no <main> found for {name}")
        return

    for a in main.find_all("a", href=True):

        href = a["href"].strip()

        if not href.startswith(prefix):
            continue

        if href == prefix:
            continue

        if href not in order:
            order.append(href)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output = OUTPUT_DIR / f"{name}.json"

    output.write_text(
        json.dumps(order, indent=2),
        encoding="utf-8"
    )

    print(f"✅ {name} order built")
    print(f"📦 entries: {len(order)}")
    print(f"📁 output: {output}")


def main():

    for name, config in SECTIONS.items():
        build_section_order(name, config)


if __name__ == "__main__":
    main()
