import os
import json
import re
from bs4 import BeautifulSoup
from collections import Counter

ROOT = os.getcwd()
OUTPUT = "semantic-model.json"

def extract_text(soup):
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return soup.get_text(" ")

def clean_words(text):
    text = text.lower()
    words = re.findall(r"[a-zA-Z]{4,}", text)
    return words

def guess_tone(text):
    calm = ["presence", "listen", "quiet", "breath", "still", "aware", "simply"]
    intense = ["urgent", "need", "must", "always", "never", "fix"]

    score = 0
    for w in calm:
        score += text.count(w)
    for w in intense:
        score -= text.count(w)

    if score > 2:
        return "contemplative"
    elif score < -2:
        return "intense"
    else:
        return "neutral"

def extract_concepts(words):
    freq = Counter(words)
    common = [w for w, c in freq.most_common(12)]
    return common

def infer_intent(title, text):
    t = (title + " " + text).lower()

    if "about" in t:
        return "identity / description"
    if "welcome" in t or "opening" in t:
        return "invitation"
    if "concept" in t:
        return "exploration"
    if "listen" in t:
        return "attention / awareness"
    return "reflection"

model = {}

for root, _, files in os.walk("."):
    for file in files:
        if not file.endswith(".html"):
            continue

        path = os.path.join(root, file)

        try:
            with open(path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
        except:
            continue

        title = soup.title.string.strip() if soup.title else ""

        text = extract_text(soup)
        words = clean_words(text)

        concepts = extract_concepts(words)
        tone = guess_tone(text)
        intent = infer_intent(title, text)

        url = path.replace("./", "")
        url = url.replace("index.html", "")
        url = url.replace(".html", "")
        url = "https://unboundhealing.org/" + url

        model[url] = {
            "title": title,
            "concepts": concepts,
            "tone": tone,
            "intent": intent
        }

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(model, f, indent=2)

print("🧠 Semantic model built (v3.3)")
