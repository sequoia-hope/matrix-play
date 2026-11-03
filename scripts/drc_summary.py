#!/usr/bin/env python3
import json, collections, sys, re
d = json.load(open(sys.argv[1])); skip = set(sys.argv[2:])
print(collections.Counter(v["type"] for v in d["violations"]).most_common(14), "unconnected", len(d.get("unconnected_items", [])))
seen = collections.Counter()
for v in d["violations"]:
    if v["type"] in skip: continue
    k = v["type"]; seen[k] += 1
    if seen[k] <= 10:
        print(k, [re.sub(r"\[.*?\]|Footprint |of ", "", i["description"])[:48] for i in v["items"]], [round(i["pos"]["x"]*1000-100,1) if False else (round(i["pos"]["x"]-100,2), round(i["pos"]["y"]-100,2)) for i in v["items"]][:1])
