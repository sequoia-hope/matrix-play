#!/usr/bin/env python3
"""fanb.py DUMP.json MAP.csv SEED_WITH_TAPS.json OUT.json: lay each CS net's way from its tap via to its driver pin on B.Cu: one layer, no second via.
Row order matches pin order round the driver, so these should nest. Fails go to the router."""
import collections, csv, json, math, re, sys, time, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seed import Layer, ob_pad, ob_circle, ob_seg, raster, astar, pull, ij, xy, W, CL, EPS, H
d = json.load(open(sys.argv[1])); seed = json.load(open(sys.argv[3]))
B = Layer()
for p in d["pads"]:
    if p["pth"]:
        B.add(ob_circle(p["x"], p["y"], p["drill"]/2+.2+W/2+EPS, p["net"] or "*"))
    elif p["B"]:
        B.add(ob_pad((p["l"]+p["r"])/2, (p["t"]+p["b"])/2, (p["r"]-p["l"])/2, (p["b"]-p["t"])/2, 0, p["net"], W/2+CL+EPS))   # bounding box: custom and rotated pads stay clear
for v in d["vias"]+seed.get("vias", []):
    dd = v.get("d", .25); dr = v.get("drill", .15)
    B.add(ob_circle(v["x"], v["y"], max(dd/2+CL, dr/2+.2)+W/2+EPS, v["net"]))
for t in d["tracks"]:
    if t["layer"] == "B.Cu": B.add(ob_seg(t["x1"], t["y1"], t["x2"], t["y2"], t["w"]/2+CL+W/2+EPS, t["net"]))
for z in d["zones"]:
    if "B.Cu" in z["layers"]:
        cx, cy = (z["l"]+z["r"])/2, (z["t"]+z["b"])/2
        hw, hh = (z["r"]-z["l"])/2, (z["b"]-z["t"])/2
        if z["rule"]:
            B.add(ob_pad(cx, cy, hw, hh, 0, "*", W/2+EPS))      # no tracks inside the pad ring
        else:
            B.add(ob_pad(cx, cy, hw, hh, 0, z["net"] or "*", W/2+CL+EPS))
pins = {}
for p in d["pads"]:
    if p["ref"] in ("U1", "U2"): pins[p["net"]] = (p["x"], p["y"], p["ref"])
tap = collections.defaultdict(list)
for v in seed.get("vias", []):
    if v.get("main"): tap[v["net"]].append((v["x"], v["y"]))
ords = collections.defaultdict(list)
for r in csv.DictReader(open(sys.argv[2])):
    ords[(int(r["driver"]), int(r["triplet"]))]
def csi(n): return int(n.split("_")[-1])
def order(drv):
    """Clockwise from CS1 for the triplets that arrive from one side, anticlockwise from CS39 for the rest: each track then lies outside those laid before it."""
    nets = [n for n in tap if f"CS{drv}_" in n]
    return sorted((n for n in nets if csi(n) <= 21), key=csi)+sorted((n for n in nets if csi(n) > 21), key=lambda n: -csi(n))
# Each pin's radial stub first, so nothing wraps across a pin on its way to another.
stub_end = {}
for p in d["pads"]:
    if p["ref"] in ("U1", "U2") and "CS" in p["net"]:
        U = d["fps"][p["ref"]]; dx, dy = p["x"]-U["x"], p["y"]-U["y"]
        v = (1 if dx > 0 else -1, 0) if abs(dx) > abs(dy) else (0, 1 if dy > 0 else -1)
        for L in (1.0, .8, .6, .4):
            e = (p["x"]+v[0]*L, p["y"]+v[1]*L)
            m, i0, j0 = raster(B, p["net"], min(p["x"], e[0])-.05, min(p["y"], e[1])-.05, max(p["x"], e[0])+.05, max(p["y"], e[1])+.05)
            n = int(L/(H/2))
            if all(not m[ij(p["x"]+v[0]*L*t/n, p["y"]+v[1]*L*t/n)[0]-i0, ij(p["x"]+v[0]*L*t/n, p["y"]+v[1]*L*t/n)[1]-j0] for t in range(n+1)):
                stub_end[p["net"]] = e; B.add(ob_seg(p["x"], p["y"], e[0], e[1], W+CL+EPS, p["net"])); break
print("pin stubs", len(stub_end), "of 78")
segs = []; fail = []; t0 = time.time(); okc = collections.Counter()
for drv in (1, 2):
    for net in order(drv):
        px0, py0, _ = pins[net]; px, py = stub_end.get(net, (px0, py0)); x, y = min(tap[net], key=lambda q: math.hypot(q[0]-px, q[1]-py))
        pad = 3.5
        m, i0, j0 = raster(B, net, min(x, px)-pad, min(y, py)-pad, max(x, px)+pad, max(y, py)+pad)
        s = (ij(x, y)[0]-i0, ij(x, y)[1]-j0); g = (ij(px, py)[0]-i0, ij(px, py)[1]-j0)
        if m[g] or m[s]:
            fail.append(dict(net=net, why="end blocked")); continue
        p = astar(m, s, g)
        if p is None:
            fail.append(dict(net=net, why="no path")); continue
        p = pull(m, p); pts = [(x, y)]+[xy(a+i0, c+j0) for a, c in p[1:-1]]+[(px, py), (px0, py0)]
        for a, b in zip(pts, pts[1:]):
            if math.hypot(a[0]-b[0], a[1]-b[1]) < 1e-3: continue
            B.add(ob_seg(a[0], a[1], b[0], b[1], W+CL+EPS, net)); segs.append(dict(x1=a[0], y1=a[1], x2=b[0], y2=b[1], layer="B.Cu", net=net, w=W))
        okc[drv] += 1
print("B.Cu fan-in laid", dict(okc), "failed", len(fail), collections.Counter(f["why"] for f in fail), "nets with no tap", sum(1 for k in range(1, 3) for i in range(1, 40) if not any(f"CS{k}_{i}" == n.split("/")[-1] for n in tap)), round(time.time()-t0), "s")
seed["segs"] += segs; seed["fanfail"] = fail
json.dump(seed, open(sys.argv[4], "w"))
if os.environ.get("FANDBG"):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    from seed import R0
    x0, y0, x1, y1 = -19, -2, -3, 11
    m, i0, j0 = raster(B, "none", x0, y0, x1, y1)
    plt.figure(figsize=(16, 13)); plt.imshow(m.T, extent=[x0, x1, y1, y0], cmap="Greys", origin="upper", alpha=.6)
    for n, v in tap.items():
        if "CS1_" in n:
            for q in v: plt.plot(q[0], q[1], "r.", ms=4)
    plt.tight_layout(); plt.savefig(os.environ["FANDBG"], dpi=60)
