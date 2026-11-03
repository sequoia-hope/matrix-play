#!/usr/bin/env python3
"""seed.py DUMP.json MAP.csv OUT.json [--no-in1] [--no-f]: generate the structured matrix copper on real geometry.

F.Cu: along each chain (one triplet), three tracks LED to LED, pad 2's going through the next LED's crosshair by the arm beside its anode, pads 1 and 4 round the outside.
In1: along each SW column, row to row, one track between anode vias, kept inside the corridor between the two rows by virtual walls.
Grid A* at 0.02 mm with every obstacle inflated by its real clearance; DRC-checked afterwards by KiCad, not here. Connections that fail are listed and left for the router."""
import argparse, collections, csv, heapq, json, math, re, sys, time
import numpy as np
from scipy import ndimage
H = .02; R0 = 19.2; N = int(2*R0/H)+1
W = .1; CL = .09; EPS = .016
def ij(x, y): return int(round((x+R0)/H)), int(round((y+R0)/H))
def xy(i, j): return i*H-R0, j*H-R0

class Layer:
    """Obstacles by spatial bin; a window's blocked mask is rastered per net, excluding that net's own copper."""
    def __init__(self):
        self.bins = collections.defaultdict(list); self.segs = []
    def add(self, ob):
        x0, y0, x1, y1 = ob["bb"]
        for bx in range(int((x0+R0)//2), int((x1+R0)//2)+1):
            for by in range(int((y0+R0)//2), int((y1+R0)//2)+1):
                self.bins[(bx, by)].append(ob)
    def remove(self, ob):
        x0, y0, x1, y1 = ob["bb"]
        for bx in range(int((x0+R0)//2), int((x1+R0)//2)+1):
            for by in range(int((y0+R0)//2), int((y1+R0)//2)+1):
                self.bins[(bx, by)].remove(ob)
    def query(self, x0, y0, x1, y1):
        seen = {}
        for bx in range(int((x0+R0)//2), int((x1+R0)//2)+1):
            for by in range(int((y0+R0)//2), int((y1+R0)//2)+1):
                for ob in self.bins.get((bx, by), ()):
                    seen[id(ob)] = ob
        return seen.values()

def ob_pad(x, y, hw, hh, deg, net, infl):
    r = math.hypot(hw, hh)+infl
    return dict(k="rect", x=x, y=y, hw=hw, hh=hh, a=math.radians(deg), net=net, infl=infl, bb=(x-r, y-r, x+r, y+r))
def ob_circle(x, y, r, net):
    return dict(k="circ", x=x, y=y, r=r, net=net, bb=(x-r, y-r, x+r, y+r))
def ob_seg(x1, y1, x2, y2, r, net):
    return dict(k="seg", x1=x1, y1=y1, x2=x2, y2=y2, r=r, net=net, bb=(min(x1, x2)-r, min(y1, y2)-r, max(x1, x2)+r, max(y1, y2)+r))

def raster(layer, net, x0, y0, x1, y1, walls=(), allow=None, skip=None):
    """skip(ob) True: that obstacle is left out (the caller prices it instead)."""
    i0, j0 = ij(x0, y0); i1, j1 = ij(x1, y1)
    i0 = max(i0, 0); j0 = max(j0, 0); i1 = min(i1, N-1); j1 = min(j1, N-1)
    X = np.arange(i0, i1+1)*H-R0; Y = np.arange(j0, j1+1)*H-R0
    XX, YY = np.meshgrid(X, Y, indexing="ij")
    m = XX*XX+YY*YY > (19-.2-.05-EPS)**2
    if allow is not None:
        m |= ~allow[i0:i1+1, j0:j1+1]
    for ob in layer.query(x0, y0, x1, y1):
        if ob["net"] == net or (skip and skip(ob)):
            continue
        b = ob["bb"]
        a0 = max(0, int((b[0]-X[0])/H)-1); a1 = min(len(X), int((b[2]-X[0])/H)+3); c0 = max(0, int((b[1]-Y[0])/H)-1); c1 = min(len(Y), int((b[3]-Y[0])/H)+3)
        if a0 >= a1 or c0 >= c1:
            continue
        xx = XX[a0:a1, c0:c1]; yy = YY[a0:a1, c0:c1]
        if ob["k"] == "circ":
            s = (xx-ob["x"])**2+(yy-ob["y"])**2 < ob["r"]**2
        elif ob["k"] == "rect":
            c, sn = math.cos(ob["a"]), math.sin(ob["a"])
            u = np.abs(c*(xx-ob["x"])+sn*(yy-ob["y"]))-ob["hw"]; v = np.abs(-sn*(xx-ob["x"])+c*(yy-ob["y"]))-ob["hh"]
            s = np.maximum(u, 0)**2+np.maximum(v, 0)**2 < ob["infl"]**2
        else:
            vx, vy = ob["x2"]-ob["x1"], ob["y2"]-ob["y1"]; n = vx*vx+vy*vy or 1e-9
            t = np.clip(((xx-ob["x1"])*vx+(yy-ob["y1"])*vy)/n, 0, 1)
            s = (xx-ob["x1"]-t*vx)**2+(yy-ob["y1"]-t*vy)**2 < ob["r"]**2
        m[a0:a1, c0:c1] |= s
    for (ax, ay, bx, by) in walls:      # virtual walls, one cell thick
        n = int(max(abs(bx-ax), abs(by-ay))/(H/2))+1
        for q in range(n+1):
            px, py = ax+(bx-ax)*q/n, ay+(by-ay)*q/n; a, c = ij(px, py)
            for da, dc in ((0, 0), (1, 0), (0, 1), (1, 1)):
                if i0 <= a+da <= i1 and j0 <= c+dc <= j1:
                    m[a+da-i0, c+dc-j0] = True
    return m, i0, j0

NB = [(1, 0, 1.), (-1, 0, 1.), (0, 1, 1.), (0, -1, 1.), (1, 1, 1.4142), (1, -1, 1.4142), (-1, 1, 1.4142), (-1, -1, 1.4142)]
def astar(m, s, g, cost=None):
    nx, ny = m.shape
    idx = lambda a, c: a*ny+c
    best = {idx(*s): 0.}; prev = {}; hq = [(0., s[0], s[1])]; gi, gj = g
    bl = m.tobytes(); 
    while hq:
        f, a, c = heapq.heappop(hq)
        if (a, c) == g:
            p = [(a, c)]
            while idx(*p[-1]) in prev: p.append(prev[idx(*p[-1])])
            return p[::-1]
        d0 = best[idx(a, c)]
        for da, dc, w in NB:
            e, h = a+da, c+dc
            if not (0 <= e < nx and 0 <= h < ny) or bl[e*ny+h]:
                continue
            nd = d0+w*(1. if cost is None else cost[e, h])
            k = e*ny+h
            if nd < best.get(k, 1e18):
                best[k] = nd; prev[k] = (a, c)
                dx, dy = abs(e-gi), abs(h-gj)
                heapq.heappush(hq, (nd+max(dx, dy)+.4142*min(dx, dy), e, h))
    return None

def los(m, p, q):
    (a, c), (e, h) = p, q
    n = max(abs(e-a), abs(h-c))*2 or 1
    for t in range(n+1):
        if m[int(round(a+(e-a)*t/n)), int(round(c+(h-c)*t/n))]:
            return False
    return True
def pull(m, path):
    out = [path[0]]; i = 0
    while i < len(path)-1:
        j = len(path)-1
        while j > i+1 and not los(m, path[i], path[j]):
            j -= 1
        out.append(path[j]); i = j
    return out

class Seeder:
    def __init__(self, dump, mapcsv):
        self.d = json.load(open(dump))
        self.F = Layer(); self.I = Layer(); self.done = []; self.fail = []; self.linkseg = collections.defaultdict(list); self.open = []
        self.leds = collections.defaultdict(dict)
        for p in self.d["pads"]:
            if p["ref"].startswith("D"):
                self.leds[p["ref"]][p["num"]] = p
            if p["pth"]:
                r = p["drill"]/2+.2+W/2+EPS
                self.F.add(ob_circle(p["x"], p["y"], r, p["net"] or "*")); self.I.add(ob_circle(p["x"], p["y"], r, p["net"] or "*"))
            elif p["F"]:
                if abs(p["w"]-p["h"]) < 1e-6 or True:
                    self.F.add(ob_pad(p["x"], p["y"], p["w"]/2, p["h"]/2, -p["rot"], p["net"], W/2+CL+EPS))
        for v in self.d["vias"]:
            R = max(v["d"]/2+CL, v["drill"]/2+.2)+W/2+EPS
            self.F.add(ob_circle(v["x"], v["y"], R, v["net"])); self.I.add(ob_circle(v["x"], v["y"], R, v["net"]))
        for t in self.d["tracks"]:
            if t["layer"] == "F.Cu":
                self.F.add(ob_seg(t["x1"], t["y1"], t["x2"], t["y2"], t["w"]/2+CL+W/2+EPS, t["net"]))
            if t["layer"] == "In1.Cu":
                self.I.add(ob_seg(t["x1"], t["y1"], t["x2"], t["y2"], t["w"]/2+CL+W/2+EPS, t["net"]))
        self.ch = collections.defaultdict(dict)
        for r in csv.DictReader(open(mapcsv)):
            self.ch[(int(r["driver"]), int(r["triplet"]))][int(r["sw"])] = r["ref"]
    def centre(self, ref):
        x = self.leds[ref]; return sum(x[n]["x"] for n in "1234")/4, sum(x[n]["y"] for n in "1234")/4
    def lay(self, layer, lname, net, pts, link=None):
        for (a, b) in zip(pts, pts[1:]):
            if math.hypot(a[0]-b[0], a[1]-b[1]) < 1e-3:
                continue
            ob = ob_seg(a[0], a[1], b[0], b[1], W+CL+EPS, net); ob["link"] = link; layer.add(ob)
            g = dict(x1=a[0], y1=a[1], x2=b[0], y2=b[1], layer=lname, net=net, w=W, ob=ob); self.done.append(g)
            if link is not None:
                self.linkseg[link].append(g)
    def rip(self, link):
        layer = self.F
        for g in self.linkseg.pop(link, []):
            (self.F if g["layer"] == "F.Cu" else self.I).remove(g["ob"]); self.done.remove(g)
    def route(self, layer, lname, net, A, B, tail=(), walls=(), pad=1.6, label="", cost_fn=None, allow=None, link=None):
        """A, B are (x, y); tail: extra fixed points after B (B's own approach, already known clear)."""
        x0, x1 = min(A[0], B[0])-pad, max(A[0], B[0])+pad; y0, y1 = min(A[1], B[1])-pad, max(A[1], B[1])+pad
        m, i0, j0 = raster(layer, net, x0, y0, x1, y1, walls, allow)
        s = (ij(*A)[0]-i0, ij(*A)[1]-j0); g = (ij(*B)[0]-i0, ij(*B)[1]-j0)
        if not (0 <= g[0] < m.shape[0] and 0 <= g[1] < m.shape[1]):
            self.fail.append(dict(net=net, label=label, why="window")); return False
        if m[g] and allow is None:
            self.fail.append(dict(net=net, label=label, why="end blocked", a=A, b=B)); return False
        m[s] = False; m[g] = False
        cost = cost_fn(m) if cost_fn else None
        p = astar(m, s, g, cost)
        if p is None:
            self.fail.append(dict(net=net, label=label, why="no path", a=A, b=B)); return False
        p = pull(m, p)
        pts = [A]+[xy(a+i0, c+j0) for a, c in p[1:-1]]+[B]+list(tail)
        self.lay(layer, lname, net, pts, link); return True
    def frame(self, ref):
        x = self.leds[ref]; c = self.centre(ref)
        ex = ((x["2"]["x"]-x["1"]["x"])/.8, (x["2"]["y"]-x["1"]["y"])/.8)   # local +x
        ey = ((x["3"]["x"]-x["1"]["x"])/.8, (x["3"]["y"]-x["1"]["y"])/.8)   # local +y
        return c, ex, ey
    def refs(self, key):
        v = self.ch[key]; return [v[s] for s in sorted(v)]
    def clear(self, layer, net, pts):
        for p, q in zip(pts, pts[1:]):
            x0, x1 = min(p[0], q[0])-.05, max(p[0], q[0])+.05; y0, y1 = min(p[1], q[1])-.05, max(p[1], q[1])+.05
            m, i0, j0 = raster(layer, net, x0, y0, x1, y1)
            n = int(math.hypot(p[0]-q[0], p[1]-q[1])/(H/2))+1
            for t in range(n+1):
                a, c = ij(p[0]+(q[0]-p[0])*t/n, p[1]+(q[1]-p[1])*t/n)
                if m[a-i0, c-j0]:
                    return False
        return True
    def arm(self, a, b, net=None):
        """Where pad 2's track enters LED b coming from LED a: the arm beside the anode facing a, or the other if a stub is in the way. Returns entry point, centre, pad 2; None if neither is free."""
        B = self.leds[b]; cb, ex, ey = self.frame(b); ca = self.centre(a); t = (cb[0]-ca[0], cb[1]-ca[1])
        dm = -(ex[0]*t[0]+ex[1]*t[1]); dp = ey[0]*t[0]+ey[1]*t[1]
        arms = [(-ex[0], -ex[1]), (ey[0], ey[1])]
        if dm < dp: arms.reverse()
        p2 = (B["2"]["x"], B["2"]["y"])
        for d in arms:
            e = (cb[0]+.62*d[0], cb[1]+.62*d[1])
            if net is None or self.clear(self.F, net, [e, cb, p2]):
                return e, cb, p2
        return None
    def reserve_tails(self, keys):
        """Pad 2's way through every LED but a chain's first is fixed, so lay it first: nothing else may use that crosshair."""
        self.entry = {}; self.tails = {}; lost = 0
        for k in keys:
            r = self.refs(k); net = self.leds[r[0]]["2"]["net"]
            for a, b in zip(r, r[1:]):
                got = self.arm(a, b, net)
                if got is None:
                    lost += 1; self.entry[b] = (self.leds[b]["2"]["x"], self.leds[b]["2"]["y"]); continue
                self.entry[b] = got[0]; n0 = len(self.done); self.lay(self.F, "F.Cu", net, list(got)); self.tails[b] = self.done[n0:]
        print("LEDs with no free crosshair arm:", lost)
    def territories(self, keys):
        """Share the free space between chains: each cell belongs to the nearest chain, drawn through its lands. A chain's tracks stay on its own ground unless that fails."""
        lab = np.zeros((N, N), dtype=np.int32); self.keyid = {k: i+1 for i, k in enumerate(keys)}
        for k in keys:
            r = self.refs(k); pts = []
            for ref in r:
                x = self.leds[ref]
                for n in "1234":
                    a, c = ij(x[n]["x"], x[n]["y"]); lab[a-6:a+7, c-6:c+7] = self.keyid[k]
            for p, q in zip(r, r[1:]):
                A, B = self.centre(p), self.centre(q); n = int(math.hypot(A[0]-B[0], A[1]-B[1])/H)+1
                for t in range(n+1):
                    a, c = ij(A[0]+(B[0]-A[0])*t/n, A[1]+(B[1]-A[1])*t/n); lab[a, c] = self.keyid[k]
        idx = ndimage.distance_transform_edt(lab == 0, return_distances=False, return_indices=True)
        self.lab = lab[idx[0], idx[1]]
    def centring(self, m):
        dist = ndimage.distance_transform_edt(~m)*H
        return 1+.05/(.05+dist)
    def link_targets(self, a, b):
        A, B = self.leds[a], self.leds[b]
        return {n: (A[n]["net"], (A[n]["x"], A[n]["y"]), self.entry[b] if n == "2" else (B[n]["x"], B[n]["y"])) for n in "124"}
    def chain_f(self, key):
        """Each link: pad 2's track first, then the flanks; other orders if that traps one. Failures stay in self.open."""
        refs = self.refs(key); allow = self.lab == self.keyid[key] if hasattr(self, "lab") else None; ok = 0
        for a, b in zip(refs, refs[1:]):
            tg = self.link_targets(a, b); best = None
            for order in ("214", "124", "421", "142", "412", "241"):
                got = []
                for n in order:
                    net, st, en = tg[n]
                    r = self.route(self.F, "F.Cu", net, st, en, label="", cost_fn=self.centring if n == "2" else None, allow=allow, link=(a, b, n), pad=1.8)
                    if not r:
                        self.fail.pop()
                        r = self.route(self.F, "F.Cu", net, st, en, label="", cost_fn=self.centring if n == "2" else None, link=(a, b, n), pad=2.2)
                        if not r: self.fail.pop()
                    if r: got.append(n)
                if len(got) == 3:
                    best = got; break
                if best is None or len(got) > len(best): best = got; bestorder = order
                for n in got: self.rip((a, b, n))
            else:
                # lay the best partial again
                got = []
                for n in bestorder:
                    net, st, en = tg[n]
                    r = self.route(self.F, "F.Cu", net, st, en, label="", cost_fn=self.centring if n == "2" else None, allow=allow, link=(a, b, n), pad=1.8)
                    if not r:
                        self.fail.pop(); r = self.route(self.F, "F.Cu", net, st, en, label="", cost_fn=self.centring if n == "2" else None, link=(a, b, n), pad=2.2)
                        if not r: self.fail.pop()
                    if r: got.append(n)
                best = got
            ok += len(best)
            for n in "124":
                if n not in best:
                    self.open.append((a, b, n))
        return ok
    def ripup(self, rounds=6):
        """Rounds over the open links: route over other chains' flank tracks at a price, rip what the way crosses, reroute that."""
        tries = collections.Counter()
        for rnd in range(rounds):
            q = list(self.open); self.open = []; n0 = len(q)
            chain = lambda ref: next(k for k, v in self.ch.items() if ref in v.values())
            while q:
                l = q.pop(0); a, b, n = l; tg = self.link_targets(a, b); net, st, en = tg[n]
                if self.route(self.F, "F.Cu", net, st, en, label="", link=l, pad=2.2):
                    continue
                self.fail.pop(); tries[l] += 1
                if tries[l] > 3:
                    self.open.append(l); continue
                ck = chain(a); pad = 2.2
                soft = lambda ob: ob.get("link") is not None and chain(ob["link"][0]) != ck
                x0, x1 = min(st[0], en[0])-pad, max(st[0], en[0])+pad; y0, y1 = min(st[1], en[1])-pad, max(st[1], en[1])+pad
                m, i0, j0 = raster(self.F, net, x0, y0, x1, y1, skip=soft)
                hard_soft, _, _ = raster(self.F, net, x0, y0, x1, y1)
                s_ = (ij(*st)[0]-i0, ij(*st)[1]-j0); g_ = (ij(*en)[0]-i0, ij(*en)[1]-j0)
                if m[g_]:
                    self.open.append(l); continue
                m[s_] = False
                cost = 1+25.*(hard_soft & ~m)
                p = astar(m, s_, g_, cost)
                if p is None:
                    self.open.append(l); continue
                pts = [xy(a_+i0, c_+j0) for a_, c_ in p]
                hit = set()
                for ob in self.F.query(x0, y0, x1, y1):
                    if not soft(ob) or ob["net"] == net: continue
                    for px, py in pts[::2]:
                        vx, vy = ob["x2"]-ob["x1"], ob["y2"]-ob["y1"]; nn = vx*vx+vy*vy or 1e-9
                        t = max(0, min(1, ((px-ob["x1"])*vx+(py-ob["y1"])*vy)/nn))
                        if (px-ob["x1"]-t*vx)**2+(py-ob["y1"]-t*vy)**2 < ob["r"]**2:
                            hit.add(ob["link"]); break
                if len(hit) > 4 or any(tries[h] > 3 for h in hit):
                    self.open.append(l); continue
                for h in hit:
                    self.rip(h); tries[h] += 1
                if self.route(self.F, "F.Cu", net, st, en, label="", link=l, pad=2.2):
                    q.extend(hit)
                else:
                    self.fail.pop(); self.open.append(l); q.extend(hit)
            print(f"rip-up round {rnd}: open {n0} -> {len(self.open)}", flush=True)
            if not self.open: break
    def anode(self, ref):
        x = self.leds[ref]["3"]; 
        v = min((q for q in self.d["vias"] if q["net"] == x["net"]), key=lambda q: math.hypot(q["x"]-x["x"], q["y"]-x["y"]))
        return v["x"], v["y"]
    def columns(self, drv):
        tris = sorted(t for d, t in self.ch if d == drv); ok = n = 0
        for t, u in zip(tris, tris[1:]):
            ra, rb = self.ch[(drv, t)], self.ch[(drv, u)]
            for k in sorted(ra):
                A, B = self.anode(ra[k]), self.anode(rb[k]); net = self.leds[ra[k]]["3"]["net"]
                walls = []
                for row in (ra, rb):
                    pts = [self.anode(row[s]) for s in sorted(row)]
                    # the wall stops short of this column's own via
                    for s, (p, q) in zip(sorted(row), zip(pts, pts[1:])):
                        walls.append((p[0], p[1], q[0], q[1]))
                n += 1
                good = self.route(self.I, "In1.Cu", net, A, B, walls=walls, pad=1.5, label=f"SW{drv}_{k} t{t}-{u}")
                if not good:
                    self.fail.pop()
                    good = self.route(self.I, "In1.Cu", net, A, B, pad=2.5, label=f"SW{drv}_{k} t{t}-{u} nowall")
                ok += good
        return ok, n

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("dump"); ap.add_argument("map"); ap.add_argument("out"); ap.add_argument("--only", default=""); ap.add_argument("--no-in1", action="store_true"); ap.add_argument("--no-f", action="store_true"); ap.add_argument("--base", help="earlier seed JSON: its tracks and vias are kept and are obstacles")
    a = ap.parse_args()
    S = Seeder(a.dump, a.map); t0 = time.time(); tot = 0; base = None
    if a.base:
        base = json.load(open(a.base))
        for v in base.get("vias", []):
            R = max(.125+CL, .075+.2)+W/2+EPS; S.F.add(ob_circle(v["x"], v["y"], R, v["net"])); S.I.add(ob_circle(v["x"], v["y"], R, v["net"]))
        for g in base["segs"]:
            ob = ob_seg(g["x1"], g["y1"], g["x2"], g["y2"], g["w"]/2+CL+W/2+EPS, g["net"])
            if g["layer"] == "F.Cu": S.F.add(ob)
            if g["layer"] == "In1.Cu": S.I.add(ob)
    keys = sorted(S.ch)
    if a.only:
        keys = [tuple(map(int, s.split(":"))) for s in a.only.split(",")]
    if not a.no_f:
        S.reserve_tails(keys); S.territories(keys)
        for k in keys:
            ok = S.chain_f(k); tot += ok
        print("F.Cu: laid", tot, "of", 24*len(keys), "open", len(S.open), flush=True)
        S.ripup()
        for a_, b_, n_ in S.open:
            net, st, en = S.link_targets(a_, b_)[n_]; S.fail.append(dict(net=net, label=f"{a_}>{b_} n{n_}", why="open", a=st, b=en))
            if n_ == "2" and b_ in S.tails:
                for g in S.tails.pop(b_):
                    S.F.remove(g["ob"]); S.done.remove(g)
    fF = len(S.fail)
    if not a.no_in1:
        for drv in (1, 2):
            print("SW columns", drv, S.columns(drv), round(time.time()-t0, 1), flush=True)
        print("In1 failed", len(S.fail)-fF)
    for x in S.fail: print("fail", x["label"], x["why"])
    for s_ in S.done: s_.pop("ob")
    res = dict(segs=S.done, fail=S.fail)
    if base:
        res = dict(base, segs=base["segs"]+S.done, fail=base["fail"]+S.fail)
    json.dump(res, open(a.out, "w"))
    print("segments", len(res["segs"]))
