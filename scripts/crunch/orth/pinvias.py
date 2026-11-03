#!/usr/bin/env python3
"""pinvias.py DUMP.json OUT.json: reserve one via and a short B.Cu stub for every CS and SW pin of U1 and U2 before anything else is seeded.
8a and 8b showed prefanout failing on 50-57 pins against 9 unseeded: seeded F.Cu and In1 copper took the through-via sites round the drivers. Sites are checked on every layer against pads, vias and holes."""
import json, math, sys
d = json.load(open(sys.argv[1])); HOLE = .275
def boxd(x, y, p): return math.hypot(max(p["l"]-x, 0, x-p["r"]), max(p["t"]-y, 0, y-p["b"]))
led = [p for p in d["pads"] if p["F"] and not p["pth"]]; back = [p for p in d["pads"] if p["B"] and not p["pth"]]; pth = [p for p in d["pads"] if p["pth"]]
def rectd(x, y, p):
    a = math.radians(p["rot"]); c, s = math.cos(a), math.sin(a); dx, dy = x-p["x"], y-p["y"]
    return math.hypot(max(abs(c*dx-s*dy)-p["w"]/2, 0), max(abs(s*dx+c*dy)-p["h"]/2, 0))
placed = [(v["x"], v["y"], v["net"]) for v in d["vias"]]; stubs = []
def segd(px, py, s):
    vx, vy = s[2]-s[0], s[3]-s[1]; n = vx*vx+vy*vy or 1e-9; t = max(0, min(1, ((px-s[0])*vx+(py-s[1])*vy)/n)); return math.hypot(px-s[0]-t*vx, py-s[1]-t*vy)
def site_ok(x, y, net):
    if any(math.hypot(x-a, y-b) < .41 for a, b, n in placed if n != net): return False
    if any(rectd(x, y, p) < HOLE+.005 for p in led if p["net"] != net): return False
    if any(boxd(x, y, p) < HOLE+.005 for p in back if p["net"] != net): return False
    if any(math.hypot(x-p["x"], y-p["y"]) < p["drill"]/2+HOLE+.01 for p in pth): return False
    return all(segd(x, y, s) >= HOLE+.05+.005 for s in stubs if s[4] != net)
def seg_ok(a, b, net):
    n = int(math.hypot(a[0]-b[0], a[1]-b[1])/.02)+1
    for i in range(n+1):
        x, y = a[0]+(b[0]-a[0])*i/n, a[1]+(b[1]-a[1])*i/n
        if any(boxd(x, y, p) < .145 for p in back if p["net"] != net): return False
        if any(math.hypot(x-q[0], y-q[1]) < HOLE+.055 for q in placed if q[2] != net): return False
        if any(segd(x, y, s) < .195 for s in stubs if s[4] != net): return False
    return True
segs = []; vias = []; miss = []
pins = [p for p in d["pads"] if p["ref"] in ("U1", "U2") and ("/CS" in p["net"] or "/SW" in p["net"])]
for p in sorted(pins, key=lambda p: (p["ref"], int(p["num"]))):
    U = d["fps"][p["ref"]]; dx, dy = p["x"]-U["x"], p["y"]-U["y"]
    out = (1 if dx > 0 else -1, 0) if abs(dx) > abs(dy) else (0, 1 if dy > 0 else -1); lat = (-out[1], out[0])
    best = None
    for L in (.75, 1.1, 1.45, 1.8, 2.15, 2.5, 2.85):
        for o in (0, .15, -.15, .3, -.3, .45, -.45, .6, -.6):
            knee = (p["x"]+out[0]*.65, p["y"]+out[1]*.65)
            e = (p["x"]+out[0]*L+lat[0]*o, p["y"]+out[1]*L+lat[1]*o)
            if site_ok(e[0], e[1], p["net"]) and seg_ok((p["x"], p["y"]), knee, p["net"]) and seg_ok(knee, e, p["net"]):
                best = (knee, e); break
        if best: break
    if not best:
        miss.append(p["net"].split("/")[-1]); continue
    knee, e = best
    for a, b in (((p["x"], p["y"]), knee), (knee, e)):
        if math.hypot(a[0]-b[0], a[1]-b[1]) > 1e-3:
            segs.append(dict(x1=a[0], y1=a[1], x2=b[0], y2=b[1], layer="B.Cu", net=p["net"], w=.1)); stubs.append((a[0], a[1], b[0], b[1], p["net"]))
    vias.append(dict(x=e[0], y=e[1], net=p["net"], ref=p["ref"], pin=True)); placed.append((e[0], e[1], p["net"]))
json.dump(dict(segs=segs, vias=vias, fail=[]), open(sys.argv[2], "w"))
print("pin vias", len(vias), "of", len(pins), "missed", miss)
