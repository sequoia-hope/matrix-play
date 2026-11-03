#!/usr/bin/env python3
"""Shared: load a dump.py JSON, group matrix LEDs into chains. Verifies claims about the map."""
import json, math, re, sys, collections
def load(path):
    d = json.load(open(path))
    leds = collections.defaultdict(dict)
    for p in d["pads"]:
        if p["ref"].startswith("D") and p["ref"] != "D235":
            leds[p["ref"]][p["num"]] = p
    return d, leds
def parse(leds):
    """(drv, tri) -> [ref by sw]"""
    ch = collections.defaultdict(dict); info = {}
    for r, x in leds.items():
        m = re.search(r"SW(\d)_(\d+)", x["3"]["net"]); drv, sw = int(m[1]), int(m[2])
        cs = sorted(int(re.search(r"CS\d_(\d+)", x[n]["net"])[1]) for n in "124")
        tri = (cs[0]-1)//3+1
        assert cs == [3*tri-2, 3*tri-1, 3*tri], (r, cs)
        ch[(drv, tri)][sw] = r
        info[r] = dict(drv=drv, sw=sw, tri=tri, x=sum(x[n]["x"] for n in "1234")/4, y=sum(x[n]["y"] for n in "1234")/4)
    return {k: [v[s] for s in sorted(v)] for k, v in ch.items()}, info
def cross(a, b, c, d):
    def o(p, q, r): return (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
    return o(a,b,c)*o(a,b,d) < 0 and o(c,d,a)*o(c,d,b) < 0
if __name__ == "__main__":
    d, leds = load(sys.argv[1]); ch, info = parse(leds)
    print("chains", len(ch), collections.Counter(len(v) for v in ch.values()))
    U = {1: (d["fps"]["U1"]["x"], d["fps"]["U1"]["y"]), 2: (d["fps"]["U2"]["x"], d["fps"]["U2"]["y"])}
    # link lengths
    L = []; seg = []
    for k, v in ch.items():
        for a, b in zip(v, v[1:]):
            p, q = info[a], info[b]; L.append(math.hypot(p["x"]-q["x"], p["y"]-q["y"])); seg.append((k, (p["x"], p["y"]), (q["x"], q["y"])))
    L.sort(); print("CS link len min/med/max", L[0], L[len(L)//2], L[-1], "n", len(L), ">2.5mm:", sum(l > 2.5 for l in L), ">4:", sum(l > 4 for l in L))
    print("CS link crossings", sum(cross(a[1], a[2], b[1], b[2]) for i, a in enumerate(seg) for b in seg[i+1:] if a[0] != b[0]))
    # first LED distance to driver; order around driver
    for drv in (1, 2):
        ux, uy = U[drv]
        rows = []
        for (dr, t), v in sorted(ch.items()):
            if dr != drv: continue
            a = [math.atan2(info[r]["y"]-uy, info[r]["x"]-ux) for r in v]
            m = math.degrees(math.atan2(sum(map(math.sin, a)), sum(map(math.cos, a))))
            rr = [math.hypot(info[r]["x"]-ux, info[r]["y"]-uy) for r in v]
            spread = max((math.degrees(x)-m+180) % 360-180 for x in a)-min((math.degrees(x)-m+180) % 360-180 for x in a)
            rows.append((round(m), t, round(rr[0], 1), round(rr[-1], 1), round(spread), all(x < y for x, y in zip(rr, rr[1:]))))
        rows.sort(); print("drv", drv, "(angle,tri,r1,r9,spread,monotone)"); [print("  ", r) for r in rows]
    # SW chords
    for drv in (1, 2):
        sw = collections.defaultdict(list)
        for r, i in info.items():
            if i["drv"] == drv: sw[i["sw"]].append(r)
        print("drv", drv, "SW counts", {k: len(v) for k, v in sw.items()})
    # anode-rear test with current turn
    def diag(r):
        x = leds[r]; return x["2"]["x"]-x["3"]["x"], x["2"]["y"]-x["3"]["y"]
    tot = collections.Counter()
    for k, v in ch.items():
        for sgn in (1, -1):
            good = 0
            for i, r in enumerate(v):
                a, b = v[max(i-1, 0)], v[min(i+1, len(v)-1)]
                tx, ty = sgn*(info[b]["x"]-info[a]["x"]), sgn*(info[b]["y"]-info[a]["y"])
                dx, dy = diag(r); good += (dx*tx+dy*ty) > 0
            tot[sgn] += good
    print("LEDs with anode at rear as built, chain direction sw1->9:", tot[1], "of 234; sw9->1:", tot[-1])
