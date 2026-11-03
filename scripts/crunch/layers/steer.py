#!/usr/bin/env python3
"""steer.py BOARD OUT.json WEIGHT: layer preferences through --regions. SW nets avoid F, In1, In6, B; CS nets avoid In3, In4. Costs only, nothing forbidden."""
import sys, json, re
t = open(sys.argv[1]).read(); w = float(sys.argv[3])
nets = set(re.findall(r'\(net \d+ "([^"]+)"\)', t)) | set(re.findall(r'\(net "([^"]+)"\)', t))
sw = sorted(n for n in nets if re.search(r"/SW\d_\d+$", n)); cs = sorted(n for n in nets if "/CS" in n)
assert len(sw) == 18 and len(cs) == 78, (len(sw), len(cs))
box = [[75, 75], [125, 75], [125, 125], [75, 125]]
json.dump({"version": 1, "regions": [
    {"name": "SW off outer", "polygon": box, "layers": ["F.Cu", "In1.Cu", "In6.Cu", "B.Cu"], "rules": [{"nets": sw, "kind": "avoid", "weight": w}]},
    {"name": "CS off middle", "polygon": box, "layers": ["In3.Cu", "In4.Cu"], "rules": [{"nets": cs, "kind": "avoid", "weight": w}]}]}, open(sys.argv[2], "w"), indent=1)
print(len(sw), len(cs))
