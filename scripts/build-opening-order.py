#!/usr/bin/env python3

import json
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]

OPENING_INDEX = ROOT / "opening" / "index.html"
OUTPUT = ROOT / "assets" / "opening-order.json"

soup = BeautifulSoup(
    OPENING_INDEX.read_text(encoding="utf-8"),
    "html.parser"
)

main = soup.find("main")

order = []

for a in main.find_all("a", href=True):

    href = a["href"].strip()

    if not href.startswith("/opening/"):
        continue

    if href == "/opening/":
        continue

    if href not in order:
        order.append(href)

OUTPUT.write_text(
    json.dumps(order, indent=2),
    encoding="utf-8"
)

print(f"✅ Opening order built")
print(f"📦 entries: {len(order)}")
print(f"📁 output: {OUTPUT}")
