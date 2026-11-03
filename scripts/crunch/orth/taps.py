#!/usr/bin/env python3
"""taps.py DUMP.json MAP.csv SEED.json OUT.json: one in-pad via per F.Cu-connected piece of each CS net, as near its driver pin as the back side allows.
In a land it costs F.Cu nothing; the router then only has to join vias to the pin on In3 and B.Cu. Vias are unlocked, like the tracks."""
import collections, csv, json, math, re, sys
d = json.load(open(sys.argv[1])); seed = json.load(open(sys.argv[3]))
ch = collections.defaultdict(dict)
for r in csv.DictReader(open(sys.argv[2])):
    ch[(int(r["driver"]), int(r["triplet"]))][int(r["sw"])] = r["ref"]
leds = collections.defaultdict(dict)
for p in d["pads"]:
    if p["ref"].startswith("D"): leds[p["ref"]][p["num"]] = p
HOLE = .275
back = [(p["l"], p["t"], p["r"], p["b"], p["net"]) for p in d["pads"] if p["B"] and not p["pth"]]
holes = [(p["x"], p["y"], p["drill"]/2) for p in d["pads"] if p["pth"]]
u3 = d["fps"]["U3"]; l1 = d["fps"]["L1"]
vias = [(v["x"], v["y"]) for v in d["vias"]+seed.get("vias", [])]
in1 = [(s["x1"], s["y1"], s["x2"], s["y2"], s["net"]) for s in seed["segs"] if s["layer"] in ("In1.Cu", "B.Cu")]
def segd(px, py, a, b, c, e):
    vx, vy = c-a, e-b; n = vx*vx+vy*vy or 1e-9; t = max(0, min(1, ((px-a)*vx+(py-b)*vy)/n)); return math.hypot(px-a-t*vx, py-b-t*vy)
def free(x, y, net):
    if math.hypot(x, y) > 18.6: return False
    for a, b, c, e, n in back:
        if math.hypot(max(a-x, 0, x-c), max(b-y, 0, y-e)) < HOLE+.01 and n != net: return False
    if any(math.hypot(x-a, y-b) < r+.275+.01 for a, b, r in holes): return False
    m = max(abs(x-u3["x"]), abs(y-u3["y"]))
    if m < 3.1+.215 or (abs(x-l1["x"]) < 1.215 and abs(y-l1["y"]) < 1.015): return False
    if any(math.hypot(x-a, y-b) < .41 for a, b in vias): return False
    if any(n != net and segd(x, y, a, b, c, e) < HOLE+.05+.01 for a, b, c, e, n in in1): return False
    return True
opens = set(f["label"] for f in seed["fail"])
pins = {}
for p in d["pads"]:
    if p["ref"] in ("U1", "U2"): pins[p["net"]] = (p["x"], p["y"])
# Main tap of each net: chosen by DP so taps run in the same clockwise order round the driver as the pins do; then chords to pins do not cross.
CUT = {1: math.atan2(-1.5, -1.), 2: math.atan2(1.5, 1.)}
def ang(drv, x, y):
    U = d["fps"][f"U{drv}"]; return (math.atan2(y-U["y"], x-U["x"])-CUT[drv]) % (2*math.pi)
rows = {}
for k, row in ch.items():
    refs = [row[s_] for s_ in sorted(row)]
    for n in "124":
        rows[leds[refs[0]][n]["net"]] = (k[0], refs, n)
out = []; none = 0; pieces = 0; main = {}
for drv in (1, 2):
    nets = sorted((nn for nn, r_ in rows.items() if r_[0] == drv), key=lambda nn: int(nn.split("_")[-1]))
    layer = []     # per net: list of (angle, cost, ref, backpointer)
    prev = [(-1., 0., None, None, None)]
    for nn in nets:
        _, refs, n = rows[nn]; pin = pins[nn]; cand = []
        for r in refs:
            x, y = leds[r][n]["x"], leds[r][n]["y"]
            if not free(x, y, nn): continue
            th = ang(drv, x, y); L = math.hypot(x-pin[0], y-pin[1])
            b = min(((c, e) for e in prev for c in [e[1]] if e[0] <= th+.02), key=lambda z: z[0], default=None)
            if b is None: continue
            cand.append((th, b[0]+L, r, b[1], nn))
        # a net may go without an ordered tap, at a price: it then gets its nearest free site and the router's help
        carry = [(e_[0], e_[1]+40., e_[2], e_[3], *e_[4:]) for e_ in prev]
        allst = sorted(cand+carry, key=lambda z: (z[0], z[1])); prev = []; bestc = 1e18
        for e_ in allst:                      # lower angle and lower cost dominates
            if e_[1] < bestc: prev.append(e_); bestc = e_[1]
    e = min(prev, key=lambda z: z[1])
    while e and e[2]:
        main[e[4]] = e[2]; e = e[3]
print("main taps in order:", len(main), "of 78; nets with no free site", sum(1 for nn, r_ in rows.items() if not any(free(leds[q][r_[2]]["x"], leds[q][r_[2]]["y"], nn) for q in r_[1])))
for k, row in sorted(ch.items()):
    refs = [row[s_] for s_ in sorted(row)]
    for n in "124":
        net = leds[refs[0]][n]["net"]; pin = pins[net]
        ps = [[refs[0]]]
        for a_, b_ in zip(refs, refs[1:]):
            if f"{a_}>{b_} n{n}" in opens: ps.append([b_])
            else: ps[-1].append(b_)
        for piece in ps:
            pieces += 1
            c = sorted(piece, key=lambda r: math.hypot(leds[r][n]["x"]-pin[0], leds[r][n]["y"]-pin[1]))
            if main.get(net) in piece:
                c = [main[net]]+c
            for r in c:
                x, y = leds[r][n]["x"], leds[r][n]["y"]
                if free(x, y, net):
                    out.append(dict(x=x, y=y, net=net, ref=r, main=main.get(net) == r)); vias.append((x, y)); break
            else:
                none += 1
seed["vias"] = seed.get("vias", [])+out
json.dump(seed, open(sys.argv[4], "w"))
ds = [math.hypot(v["x"]-pins[v["net"]][0], v["y"]-pins[v["net"]][1]) for v in out]
print(f"pieces {pieces}, tap vias {len(out)}, no site {none}; distance to pin median {sorted(ds)[len(ds)//2]:.1f} max {max(ds):.1f}")
