#!/usr/bin/env python3
"""space.py BOARD OUT.npz: free-space model of a finished board for one new net, at 0.025 mm (rules as diagnose.py).
Prints for each of ADC pins 41-43 the free component reached, its area per layer, and legal via area near each survey site.
Saves free[layer], via, label maps to OUT.npz for reuse."""
import collections, json, math, os, sys
import numpy as np, pcbnew
from PIL import Image, ImageDraw
from scipy import ndimage
H = .025; X0 = 80.; Y0 = 80.; N = 1600
LAYERS = "F.Cu,In1.Cu,In3.Cu,In4.Cu,In6.Cu,B.Cu".split(",")
b = pcbnew.LoadBoard(sys.argv[1]); 
if "--fill" in sys.argv: pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pp = lambda p: ((p.x / 1e6 - X0) / H, (p.y / 1e6 - Y0) / H)
cu = {l: Image.new("L", (N, N), 0) for l in LAYERS}; dr = {l: ImageDraw.Draw(cu[l]) for l in LAYERS}
hole = Image.new("L", (N, N), 0); hd = ImageDraw.Draw(hole)
def disc(d, c, r): d.ellipse([c[0]-r, c[1]-r, c[0]+r, c[1]+r], fill=1)
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        c = pp(t.GetPosition()); r = t.GetWidth(pcbnew.F_Cu) / 2e6 / H
        for l in LAYERS: disc(dr[l], c, r)
        disc(hd, c, t.GetDrill() / 2e6 / H)
    elif t.GetLayerName() in dr:
        a, e = pp(t.GetStart()), pp(t.GetEnd()); w = t.GetWidth() / 1e6 / H; d = dr[t.GetLayerName()]
        d.line([a, e], fill=1, width=max(1, round(w))); disc(d, a, w/2); disc(d, e, w/2)
for f in b.GetFootprints():
    for p in f.Pads():
        for l in LAYERS:
            if p.IsOnLayer(b.GetLayerID(l)):
                o = p.GetEffectivePolygon(b.GetLayerID(l)).Outline(0); dr[l].polygon([pp(o.CPoint(i)) for i in range(o.PointCount())], fill=1)
        if p.GetDrillSizeX() > 0: disc(hd, pp(p.GetPosition()), p.GetDrillSizeX() / 2e6 / H)
nt = {l: Image.new("L", (N, N), 0) for l in LAYERS}; nv = Image.new("L", (N, N), 0)
for z in b.Zones():
    o = z.Outline().Outline(0); poly = [pp(o.CPoint(i)) for i in range(o.PointCount())]
    if z.GetIsRuleArea():
        if z.GetDoNotAllowVias(): ImageDraw.Draw(nv).polygon(poly, fill=1)
        for l in LAYERS:
            if z.GetDoNotAllowTracks() and z.IsOnLayer(b.GetLayerID(l)): ImageDraw.Draw(nt[l]).polygon(poly, fill=1)
        continue
    for l in LAYERS:
        li = b.GetLayerID(l)
        if z.IsOnLayer(li):
            ps = z.GetFilledPolysList(li)
            for i in range(ps.OutlineCount()):
                o = ps.Outline(i); q = [pp(o.CPoint(j)) for j in range(o.PointCount())]
                if len(q) > 2: dr[l].polygon(q, fill=1)
yy, xx = np.mgrid[0:N, 0:N]; ctr = (N-1)/2 ; rad = np.hypot(xx-ctr, yy-ctr)*H
dh = ndimage.distance_transform_edt(np.array(hole) == 0) * H
free = {}; via = (rad <= 19-.4) & (np.array(nv) == 0) & (dh >= .275)
D = {}
for l in LAYERS:
    D[l] = ndimage.distance_transform_edt(np.array(cu[l]) == 0) * H
    free[l] = (rad <= 19-.25) & (D[l] >= .14) & (dh >= .25) & (np.array(nt[l]) == 0)
    via &= D[l] >= .275
# U3 rule: no new vias within +-2.3 of U3
U = b.FindFootprintByReference("U3").GetPosition(); ux, uy = U.x/1e6-X0, U.y/1e6-Y0
via[int((uy-2.3)/H):int((uy+2.3)/H)+1, int((ux-2.3)/H):int((ux+2.3)/H)+1] = False
lab = {}; off = 0
for l in LAYERS:
    a, k = ndimage.label(free[l]); a[a > 0] += off; lab[l] = a; off += k
par = list(range(off+1))
def find(i):
    while par[i] != i: par[i] = par[par[i]]; i = par[i]
    return i
ys, xs = np.nonzero(via); seen = set()
for t in {tuple(lab[l][y, x] for l in LAYERS) for y, x in zip(ys, xs)}:
    v = [x for x in t if x]
    for x in v[1:]:
        ra, rb = find(v[0]), find(x)
        if ra != rb: par[ra] = rb
root = np.array([find(i) for i in range(off+1)])
big = collections.Counter(root[np.concatenate([lab[l].ravel() for l in LAYERS])].tolist()); big.pop(0, None)
print("largest free component mm2", [round(v*H*H, 1) for _, v in big.most_common(5)], "legal via area mm2", round(via.sum()*H*H, 1))
main = big.most_common(1)[0][0]
for num in ("41", "42", "43"):
    p = [q for q in b.FindFootprintByReference("U3").Pads() if q.GetNumber() == num][0]
    x, y = pp(p.GetPosition()); ox = int(x + .4/H); y = int(y)
    d = []
    for k in range(0, 80):  # march outwards on B.Cu from the pad
        c = (y, int(x) + k)
        if free["B.Cu"][c]: d.append(k*H); break
    r = lab["B.Cu"][c] if d else 0
    print("pin", num, "first free B.Cu cell outward", d, "in main component", bool(r) and root[r] == main, "comp area", round(sum((root[lab[l]] == root[r]).sum() for l in LAYERS)*H*H, 2) if r else 0)
np.savez_compressed(sys.argv[2], via=via, **{l: free[l] for l in LAYERS})
