#!/usr/bin/env python3
"""diagnose.py PROJECT_DIR OUT_PREFIX [--board B.kicad_pcb]: what blocks each open connection on a finished route.

Uses KiCad's DRC opens on a refilled copy, then a free-space model of the finished copper at 0.025 mm:
  a 0.1 mm track centre needs 0.14 mm to other nets' copper and 0.25 mm to other nets' holes;
  a 0.25/0.15 via centre needs 0.275 mm to other nets' copper on every routing layer (hole-to-copper 0.2),
  0.275 mm to holes, and no rule area forbidding vias. Plane layers carry no tracks and don't block vias.
Each net's island joins its own copper; components on the 4 routing layers are unioned at legal via sites.

Class of a connection (first that fits):
  free-path      both ends in one component: the router left a path it could have used
  led-pad        an end on an LED pad reaches under SEAL mm2 of free space: sealed by F.Cu copper round it
  chip-fanout    an end on a chip pad likewise (U*)
  pad-other      any other pad likewise
  via-wall       both ends reach space, but the smaller region's boundary is mostly vias' keep-off
  pad-wall       ... mostly pads
  track-wall     ... mostly tracks: a wall of routed copper (the capacity-like class)
Also per connection: the cheapest path allowed through other copper (0.1 mm grid), how many mm of it are
blocked and how many foreign nets it crosses; 1-2 nets means a local shuffle, many means real shortage.
"""
import collections, json, math, re, subprocess, sys, tempfile, shutil
from pathlib import Path
import numpy as np, pcbnew
from PIL import Image, ImageDraw
from scipy import ndimage, sparse
from scipy.sparse.csgraph import dijkstra
H = 0.025; X0 = 80.0; Y0 = 80.0; N = 1600
import os
LAYERS = os.environ.get("DIAG_LAYERS", "F.Cu,In1.Cu,In3.Cu,In4.Cu,In6.Cu,B.Cu").split(","); SEAL = 0.25
PLANES = os.environ.get("DIAG_PLANES", "In2.Cu,In5.Cu").split(",")
proj = Path(sys.argv[1]); prefix = Path(sys.argv[2])
pcb = Path(sys.argv[sys.argv.index("--board") + 1]) if "--board" in sys.argv else proj / "round-pendant.kicad_pcb"
tmp = Path(tempfile.mkdtemp())
c = tmp / "x.kicad_pcb"; shutil.copy(pcb, c)
for s in (".kicad_pro", ".kicad_dru"):
    src = proj / ("round-pendant" + s)
    if src.exists(): shutil.copy(src, c.with_suffix(s))
b = pcbnew.LoadBoard(str(c)); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(str(c), b)
subprocess.run(["kicad-cli", "pcb", "drc", "--format", "json", "--severity-error", "-o", str(tmp / "d.json"), str(c)], capture_output=True)
drc = json.load(open(tmp / "d.json"))
b = pcbnew.LoadBoard(str(c))
px = lambda v: (v / 1e6 - X0) / H
pp = lambda p: (px(p.x) if hasattr(p, "x") else 0, (p.y / 1e6 - Y0) / H)
nets = {}
def nid(name): return nets.setdefault(name, len(nets) + 1)
own = {l: Image.new("I", (N, N), 0) for l in LAYERS}; kind = {l: Image.new("L", (N, N), 0) for l in LAYERS}
hole = Image.new("I", (N, N), 0)
hd = ImageDraw.Draw(hole); dr = {l: (ImageDraw.Draw(own[l]), ImageDraw.Draw(kind[l])) for l in LAYERS}
def disc(d, c, r, f):
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=f)
def stamp(l, f):
    f(dr[l][0], 0); f(dr[l][1], 1)
vias = collections.defaultdict(list)
for t in b.GetTracks():
    n = nid(t.GetNetname())
    if t.Type() == pcbnew.PCB_VIA_T:
        c0 = pp(t.GetPosition()); r = t.GetWidth(pcbnew.F_Cu) / 2e6 / H
        for l in LAYERS:
            disc(dr[l][0], c0, r, n); disc(dr[l][1], c0, r, 2)
        disc(hd, c0, t.GetDrill() / 2e6 / H, n); vias[n].append(c0)
    else:
        l = t.GetLayerName()
        if l not in dr: continue
        a, e = pp(t.GetStart()), pp(t.GetEnd()); w = t.GetWidth() / 1e6 / H
        for d, f in ((dr[l][0], n), (dr[l][1], 1)):
            d.line([a, e], fill=f, width=max(1, round(w))); disc(d, a, w / 2, f); disc(d, e, w / 2, f)
for fp in b.GetFootprints():
    for p in fp.Pads():
        n = nid(p.GetNetname() or f"nc-{fp.GetReference()}-{p.GetNumber()}")
        for l in LAYERS:
            if not p.IsOnLayer(b.GetLayerID(l)): continue
            o = p.GetEffectivePolygon(b.GetLayerID(l)).Outline(0)
            poly = [pp(o.CPoint(i)) for i in range(o.PointCount())]
            if len(poly) > 2:
                dr[l][0].polygon(poly, fill=n); dr[l][1].polygon(poly, fill=3)
        if p.GetDrillSizeX() > 0:
            disc(hd, pp(p.GetPosition()), p.GetDrillSizeX() / 2e6 / H, n)
novia = Image.new("L", (N, N), 0); notrack = {l: Image.new("L", (N, N), 0) for l in LAYERS}
for z in b.Zones():
    if z.GetIsRuleArea():
        o = z.Outline().Outline(0); poly = [pp(o.CPoint(i)) for i in range(o.PointCount())]
        if z.GetDoNotAllowVias(): ImageDraw.Draw(novia).polygon(poly, fill=1)
        if z.GetDoNotAllowTracks():
            for l in LAYERS:
                if z.IsOnLayer(b.GetLayerID(l)): ImageDraw.Draw(notrack[l]).polygon(poly, fill=1)
        continue
    for l in LAYERS:
        li = b.GetLayerID(l)
        if z.IsOnLayer(li):
            n = nid(z.GetNetname()); ps = z.GetFilledPolysList(li)
            for i in range(ps.OutlineCount()):
                o = ps.Outline(i); poly = [pp(o.CPoint(j)) for j in range(o.PointCount())]
                if len(poly) > 2:
                    dr[l][0].polygon(poly, fill=n); dr[l][1].polygon(poly, fill=4)
OWN = {l: np.array(own[l], dtype=np.int32) for l in LAYERS}; KIND = {l: np.array(kind[l]) for l in LAYERS}
HOLE = np.array(hole, dtype=np.int32); NV = np.array(novia, bool); NT = {l: np.array(notrack[l], bool) for l in LAYERS}
yy, xx = np.mgrid[0:N, 0:N]; ctr = (N - 1) / 2
inboard = np.hypot(xx - ctr, yy - ctr) * H <= 19 - 0.2 - 0.05

cache = {}
def space(net):
    n = nets[net]
    if n in cache: return cache[n]
    dh = ndimage.distance_transform_edt((HOLE == 0) | (HOLE == n)) * H
    D = {}; free = {}; vs = inboard & ~NV & (dh >= 0.275)
    for l in LAYERS:
        ob = (OWN[l] != 0) & (OWN[l] != n)
        d = ndimage.distance_transform_edt(~ob) * H; D[l] = d
        free[l] = inboard & (d >= 0.14) & (dh >= 0.25) & ~NT[l]
        vs &= d >= 0.275
    oursv = np.zeros((N, N), bool)
    for c0 in vias[n]:
        oursv[int(c0[1]), int(c0[0])] = True
    pas = {l: free[l] | (OWN[l] == n) for l in LAYERS}
    lab = {}; off = 0; pairs = []
    for l in LAYERS:
        a, k = ndimage.label(pas[l]); a[a > 0] += off; lab[l] = a; off += k
    links = vs | oursv
    ys, xs = np.nonzero(links)
    ls = [lab[l][ys, xs] for l in LAYERS]
    par = np.arange(off + 1)
    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    seen = set()
    for i in range(len(ys)):
        t = (ls[0][i], ls[1][i], ls[2][i], ls[3][i])
        if t in seen: continue
        seen.add(t)
        v = [x for x in t if x]
        for x in v[1:]:
            ra, rb = find(v[0]), find(x)
            if ra != rb: par[ra] = rb
    root = np.array([find(i) for i in range(off + 1)])
    cache.clear()
    cache[n] = dict(n=n, free=free, lab=lab, root=root, vs=vs, D=D, dh=dh, pas=pas)
    return cache[n]

def region(sp, cell, layer):
    x, y = cell
    # snap: nearest passable cell of this layer within 0.5 mm
    a = sp["lab"][layer]; R = 20
    sub = a[max(0, y - R):y + R, max(0, x - R):x + R]
    if not sub.any(): return None
    ys, xs = np.nonzero(sub); i = np.argmin((ys - min(R, y)) ** 2 + (xs - min(R, x)) ** 2)
    return sp["root"][sub[ys[i], xs[i]]]

def area(sp, r, own_net):
    tot = 0; per = {}
    for l in LAYERS:
        m = (sp["root"][sp["lab"][l]] == r) & sp["lab"][l].astype(bool) & (OWN[l] != own_net)
        per[l] = m; tot += m.sum() * H * H
    return tot, per

def blockers(sp, per):
    cnt = collections.Counter()
    for l in LAYERS:
        ring = ndimage.binary_dilation(per[l], iterations=2) & ~sp["pas"][l] & inboard
        if not ring.any(): continue
        # nearest copper kind for each blocked ring cell
        n = sp["n"]; ob = (OWN[l] != 0) & (OWN[l] != n)
        _, (iy, ix) = ndimage.distance_transform_edt(~ob, return_indices=True)
        ys, xs = np.nonzero(ring); k = KIND[l][iy[ys, xs], ix[ys, xs]]
        # a cell kept off by a hole counts as via
        k = np.where(sp["dh"][ys, xs] < 0.25, 2, k)
        for v, ct in zip(*np.unique(k, return_counts=True)):
            cnt[int(v)] += int(ct)
    return cnt

# coarse graph for the cheapest path through other copper
C = 4; M = N // C; NL = len(LAYERS)
def cross(sp, a, la, c_, lc):
    n = sp["n"]; nodes = M * M * NL; rows = []; cols = []; w = []
    idx = np.arange(M * M).reshape(M, M)
    blocked = []
    for li, l in enumerate(LAYERS):
        fr = sp["pas"][l][::C, ::C][:M, :M]; ib = inboard[::C, ::C][:M, :M]
        cost = np.where(fr, 0.001, 1.0); cost[~ib] = 1e6
        blocked.append(cost)
        for (i0, i1, c0, c1) in ((idx[:, :-1], idx[:, 1:], cost[:, :-1], cost[:, 1:]), (idx[:-1, :], idx[1:, :], cost[:-1, :], cost[1:, :])):
            rows.append(i0.ravel() + li * M * M); cols.append(i1.ravel() + li * M * M); w.append(((c0 + c1) / 2).ravel())
    vs = sp["vs"][::C, ::C][:M, :M]
    # via anywhere, at a price of 0.02 on a legal site and 3 blocked mm-cells on an illegal one
    vc = np.where(vs, 0.02, 3.0)
    for li in range(NL - 1):
        rows.append(idx.ravel() + li * M * M); cols.append(idx.ravel() + (li + 1) * M * M); w.append(vc.ravel())
    r = np.concatenate(rows); cc = np.concatenate(cols); ww = np.concatenate(w)
    g = sparse.coo_matrix((np.r_[ww, ww], (np.r_[r, cc], np.r_[cc, r])), shape=(nodes, nodes)).tocsr()
    s = la * M * M + a[1] // C * M + a[0] // C; t = lc * M * M + c_[1] // C * M + c_[0] // C
    d, pred = dijkstra(g, indices=s, return_predecessors=True, directed=False, min_only=False)
    path = []; i = t
    while i >= 0 and i != s:
        path.append(i); i = pred[i]
    foreign = set(); bl = 0; badv = 0
    for u, v in zip(path, path[1:]):
        if u % (M * M) == v % (M * M):
            y, x = np.unravel_index(u % (M * M), (M, M))
            if not vs[y, x]: badv += 1
    for i in path:
        li = i // (M * M); y, x = np.unravel_index(i % (M * M), (M, M)); l = LAYERS[li]
        if not sp["pas"][l][y * C, x * C]:
            bl += 1
            sub = OWN[l][max(0, y * C - 8):y * C + 8, max(0, x * C - 8):x * C + 8]
            foreign |= set(int(v) for v in np.unique(sub) if v and v != n)
    return round(bl * C * H, 2), len(foreign), len({i // (M * M) for i in path}), badv

EP = re.compile(r"\[(.*?)\]")
def endpoint(it):
    d = it["description"]; p = it["pos"]
    x = float(p["x"]); y = float(p["y"])
    cell = (int((x - X0) / H), int((y - Y0) / H))
    m = re.search(r"Pad (\S+)? ?\[.*?\] of (\S+)", d); ref = m.group(2) if m else None
    lm = re.search(r"on (\S+\.Cu)", d); layer = lm.group(1) if lm else None
    typ = "pad" if d.startswith("Pad") else "via" if d.startswith("Via") else "track"
    if typ == "pad" and layer is None:
        layer = "B.Cu" if ref and b.FindFootprintByReference(ref) and b.FindFootprintByReference(ref).IsFlipped() else "F.Cu"
    if layer not in LAYERS: layer = "F.Cu"
    return dict(net=EP.search(d).group(1), type=typ, ref=ref, layer=layer, cell=cell, xy=(x, y), desc=d)

planes = set()
for z in b.Zones():
    if not z.GetIsRuleArea() and any(b.GetLayerName(l) in PLANES for l in z.GetLayerSet().Seq()):
        planes.add(z.GetNetname())
rows = []
for u in sorted(drc.get("unconnected_items", []), key=lambda u: EP.search(u["items"][0]["description"]).group(1)):
    A, B = map(endpoint, u["items"][:2]); net = A["net"]; plane = net in planes
    sp = space(net); ra = region(sp, A["cell"], A["layer"]); rb = region(sp, B["cell"], B["layer"])
    aa, pa = area(sp, ra, sp["n"]) if ra else (0, {}); ab, pb = area(sp, rb, sp["n"]) if rb else (0, {})
    cls = None; info = {}
    if plane: group = "plane"
    else: group = "signal"
    if ra is not None and ra == rb: cls = "free-path"
    else:
        sealed = [(e, ar) for e, ar in ((A, aa), (B, ab)) if ar < SEAL]
        if sealed:
            e = min(sealed, key=lambda t: t[1])[0]
            if e["type"] == "pad" and (e["ref"] or "").startswith("D"): cls = "led-pad"
            elif e["type"] == "pad" and (e["ref"] or "").startswith("U"): cls = "chip-fanout"
            elif e["type"] == "pad": cls = "pad-other"
            else: cls = "stub-sealed"
        if cls is None:
            pm = pa if aa <= ab else pb
            bc = blockers(sp, pm); tot = sum(bc.values()) or 1
            info = dict(track=round(bc[1] / tot, 2), via=round(bc[2] / tot, 2), pad=round(bc[3] / tot, 2), zone=round(bc[4] / tot, 2))
            top = max(("track", "via", "pad", "zone"), key=lambda k: info[k])
            cls = {"track": "track-wall", "via": "via-wall", "pad": "pad-wall", "zone": "zone-wall"}[top]
    try:
        info["blocked_mm"], info["nets_crossed"], info["layers_used"], info["illegal_via_hops"] = cross(sp, A["cell"], LAYERS.index(A["layer"]), B["cell"], LAYERS.index(B["layer"]))
    except Exception as e:
        info["err"] = str(e)
    def sites(pm):
        return int(sum((pm[l] & sp["vs"]).sum() for l in LAYERS[:1])) if pm else 0
    def nsites(pm):
        if not pm: return 0
        m = np.zeros((N, N), bool)
        for l in LAYERS: m |= pm[l]
        return round(float((m & sp["vs"]).sum() * H * H), 3)
    rows.append(dict(via_area_a=nsites(pa), via_area_b=nsites(pb), net=net, group=group, cls=cls, a=A["desc"][:60], b=B["desc"][:60], axy=A["xy"], bxy=B["xy"], len=round(math.dist(A["xy"], B["xy"]), 2), area_a=round(aa, 2), area_b=round(ab, 2), **info))
    print(rows[-1]["cls"], net[-12:], rows[-1]["len"], round(aa, 2), round(ab, 2), info, flush=True)
# free space per layer (for picture and tile numbers)
free_all = np.zeros((len(LAYERS), N, N), bool)
ob_d = {}
for i, l in enumerate(LAYERS):
    d = ndimage.distance_transform_edt(OWN[l] == 0) * H
    dh = ndimage.distance_transform_edt(HOLE == 0) * H
    free_all[i] = inboard & (d >= 0.14) & (dh >= 0.25) & ~NT[l]
via_sites = inboard & ~NV & (dh >= 0.275)
for i, l in enumerate(LAYERS):
    via_sites &= (ndimage.distance_transform_edt(OWN[l] == 0) * H >= 0.275)
np.savez_compressed(str(prefix) + ".npz", free=free_all[:, ::2, ::2], via=via_sites[::2, ::2])
sum_ = dict(total=len(rows), signal=collections.Counter(r["cls"] for r in rows if r["group"] == "signal"), plane=collections.Counter(r["cls"] for r in rows if r["group"] == "plane"),
            free_frac={l: round(float(free_all[i][inboard].mean()), 3) for i, l in enumerate(LAYERS)}, via_site_frac=round(float(via_sites[inboard].mean()), 4))
json.dump(dict(summary=sum_, rows=rows), open(str(prefix) + ".json", "w"), indent=0)
print(json.dumps(sum_, indent=1))
