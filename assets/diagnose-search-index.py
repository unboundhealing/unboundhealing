import json

with open("assets/search-index.json", "r", encoding="utf-8") as f:
    data = json.load(f)

sample = next(iter(data.values()))

print("SAMPLE ENTRY:")
for k, v in sample.items():
    print(k, "=>", type(v), ":", str(v)[:60])
