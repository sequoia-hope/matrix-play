#!/usr/bin/env python3
"""pdn.py BOARD [--grid MM] [--refill]: DC drop of VSYS and +3V3 by nodal analysis of the real copper.

Rasterises the net's tracks, pads and zone fills on each layer, joins layers at vias and through-hole barrels, solves the resistor mesh, reports
each sink's drop, the worst current density as an equivalent neck, and how many vias carry the current across each layer change.
Copper: outer 35 um, inner 15.2 um (design/stackup.md). Via: 0.15 mm drill, 18 um plating assumed (JLC's stated minimum for plated holes; not measured).
Currents from design/parts/drivers.md: 494 mA scan peak per driver, shared equally between PVCC pins 15 and 25; both aligned = 988 mA. Source: U5 OUT pins 10, 11.
+3V3: 150 mA (nets.csv), 120 at U3 VREG_VIN pin 49 and IOVDD spread, source U6 pin 1.
"""
import sys, math, argparse, collections, pcbnew, numpy as np, scipy.sparse as sp, scipy.sparse.linalg as sl
from PIL import Image, ImageDraw
ap = argparse.ArgumentParser(); ap.add_argument("board"); ap.add_argument("--grid", type=float, default=.05); ap.add_argument("--refill", action="store_true"); a = ap.parse_args()
RHO = 1.72e-8; TH = {"F.Cu": 35e-6, "In1.Cu": 15.2e-6, "In2.Cu": 15.2e-6, "In3.Cu": 15.2e-6, "In4.Cu": 15.2e-6, "In5.Cu": 15.2e-6, "In6.Cu": 15.2e-6, "B.Cu": 35e-6}
b = pcbnew.LoadBoard(a.board)
if a.refill: pcbnew.ZONE_FILLER(b).Fill(b.Zones())
LAY = list(TH); um = pcbnew.ToMM; G = a.grid; N = int(40/G); X0 = 80.0
def px(x, y): return ((x-X0)/G, (y-X0)/G)
def solve(net, sources, sinks):
    img = {l: Image.new("1", (N, N)) for l in LAY}; dr = {l: ImageDraw.Draw(img[l]) for l in LAY}
    vias = []
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != net: continue
        for lid in z.GetLayerSet().Seq():
            l = b.GetLayerName(lid)
            if l not in TH or not z.HasFilledPolysForLayer(lid): continue
            ps = z.GetFilledPolysList(lid)
            for i in range(ps.OutlineCount()):
                o = ps.Outline(i); dr[l].polygon([px(um(o.CPoint(j).x), um(o.CPoint(j).y)) for j in range(o.PointCount())], fill=1)
    for t in b.GetTracks():
        if t.GetNetname() != net: continue
        if t.GetClass() == "PCB_VIA":
            c = t.GetPosition(); vias.append((um(c.x), um(c.y), um(t.GetWidth()), um(t.GetDrillValue()))); continue
        l = b.GetLayerName(t.GetLayer()); s, e = t.GetStart(), t.GetEnd(); w = um(t.GetWidth())
        dr[l].line([px(um(s.x), um(s.y)), px(um(e.x), um(e.y))], fill=1, width=max(1, round(w/G)))
        for q in (s, e):
            x, y = px(um(q.x), um(q.y)); r = w/2/G; dr[l].ellipse([x-r, y-r, x+r, y+r], fill=1)
    pads = {}
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() != net: continue
            c = p.GetPosition(); pads[f"{f.GetReference()}-{p.GetNumber()}"] = (um(c.x), um(c.y), p)
            for lid in p.GetLayerSet().Seq():
                l = b.GetLayerName(lid)
                if l in TH:
                    bb = p.GetBoundingBox(); dr[l].rectangle([px(um(bb.GetLeft()), um(bb.GetTop())), px(um(bb.GetRight()), um(bb.GetBottom()))], fill=1)
    idx = {}; arrs = {l: np.array(img[l], dtype=bool) for l in LAY}
    n = 0; I, J, V = [], [], []
    node = {l: -np.ones((N, N), dtype=np.int64) for l in LAY}
    for l in LAY:
        m = arrs[l]; k = int(m.sum()); node[l][m] = np.arange(n, n+k); n += k
        g = TH[l]/RHO      # square of copper conducts t/rho, whatever its size
        nd = node[l]
        for (d0, d1) in ((0, 1), (1, 0)):
            A = nd[:N-d0, :N-d1]; B = nd[d0:, d1:]; both = (A >= 0) & (B >= 0)
            I.append(A[both]); J.append(B[both]); V.append(np.full(both.sum(), g))
    # vias: barrel over each layer gap; the whole barrel is treated as one column from layer to layer
    plate = 18e-6
    via_links = collections.Counter()
    for x, y, w, d in vias:
        area = math.pi*(d*1e-3+plate)*plate
        cx, cy = int((y-X0)/G), int((x-X0)/G); pts = []
        for li, l in enumerate(LAY):
            if node[l][cx, cy] >= 0: pts.append((li, node[l][cx, cy]))
        for (l0, a0), (l1, b1) in zip(pts, pts[1:]):
            h = (l1-l0)*.2e-3     # about 0.2 mm a layer in a 1.0 mm board
            I.append(np.array([a0])); J.append(np.array([b1])); V.append(np.array([area/(RHO*h)]))
    I, J, V = map(np.concatenate, (I, J, V))
    L = sp.coo_matrix((np.r_[-V, -V], (np.r_[I, J], np.r_[J, I])), shape=(n, n)).tocsr()
    L = L + sp.diags(-np.asarray(L.sum(axis=1)).ravel())
    def at(name):
        x, y, p = pads[name]; c, r = int((y-X0)/G), int((x-X0)/G)
        for lid in p.GetLayerSet().Seq():
            l = b.GetLayerName(lid)
            if l in TH and node[l][c, r] >= 0: return node[l][c, r], l
        raise SystemExit(f"{name}: no copper node")
    # components: connected to the source?
    ncomp, lab = sp.csgraph.connected_components(L, directed=False)
    src = [at(s)[0] for s in sources]; root = lab[src[0]]
    res = {}
    keep = np.where(lab == root)[0]; remap = -np.ones(n, dtype=np.int64); remap[keep] = np.arange(len(keep))
    Lk = L[keep][:, keep].tocsc(); rhs = np.zeros(len(keep))
    missing = []
    for s, amps in sinks.items():
        node_id, _ = at(s)
        if lab[node_id] != root: missing.append(s); continue
        rhs[remap[node_id]] -= amps
    tot = -rhs.sum()
    for s in src: rhs[remap[s]] += tot/len(src)
    g0 = remap[src[0]]
    idxs = np.arange(len(keep)) != g0
    Lr = Lk[idxs][:, idxs]; v = np.zeros(len(keep)); v[idxs] = sl.spsolve(Lr.tocsc(), rhs[idxs])
    ref = v[[remap[s] for s in src]].mean()
    print(f"{net}: {tot:.3f} A, {len(keep)} cells, {ncomp} copper pieces, {len(vias)} vias on the net")
    if "/SW" in net:
        dr = [(ref - v[remap[at(s)[0]]])*1e3 for s in sinks if s not in missing]
        print(f"  worst LED drop {max(dr or [0]):.1f} mV, {len(missing)} of {len(sinks)} LEDs not joined, {len(vias)} vias on the line"); return
    for s, amps in sinks.items():
        if s in missing: print(f"  {s:8s} {amps*1e3:5.0f} mA  NOT JOINED to the source by tracks or fill"); continue
        print(f"  {s:8s} {amps*1e3:5.0f} mA  drop {(ref - v[remap[at(s)[0]]])*1e3:6.1f} mV")
    if net == "VSYS":
        print("  tracks under 0.3 mm: width, layer, length mm, DC current mA, from x,y to x,y")
        rows = []
        for t in b.GetTracks():
            if t.GetNetname() != net or t.GetClass() == "PCB_VIA" or um(t.GetWidth()) >= .2999: continue
            l = b.GetLayerName(t.GetLayer()); p0, p1 = t.GetStart(), t.GetEnd(); w = um(t.GetWidth()); L = um(t.GetLength())
            def nv(q):
                c, r = int((um(q.y)-X0)/G), int((um(q.x)-X0)/G); i = node[l][c, r]
                return v[remap[i]] if i >= 0 and remap[i] >= 0 else None
            a0, a1 = nv(p0), nv(p1)
            cur = abs(a0-a1)/(RHO*L*1e-3/(w*1e-3*TH[l])) if a0 is not None and a1 is not None and L > 0 else float("nan")
            rows.append((w, l, round(L, 2), round(cur*1e3, 1), round(um(p0.x)-100, 2), round(um(p0.y)-100, 2), round(um(p1.x)-100, 2), round(um(p1.y)-100, 2)))
        for r in sorted(rows, key=lambda r: -r[3] if r[3] == r[3] else 0): print("   ", r)
    # current density
    worst = (0, None)
    for l in LAY:
        nd = node[l]; t = TH[l]
        gx = np.zeros((N, N)); gy = np.zeros((N, N)); vv = np.full((N, N), np.nan); mask = nd >= 0
        ids = nd[mask]; ok = remap[ids] >= 0; vals = np.full(ids.shape, np.nan); vals[ok] = v[remap[ids[ok]]]; vv[mask] = vals
        dy = np.abs(vv[1:, :]-vv[:-1, :])/(RHO/t); dx = np.abs(vv[:, 1:]-vv[:, :-1])/(RHO/t)   # amps through one cell width
        for arr, tag in ((dx, "x"), (dy, "y")):
            if np.all(np.isnan(arr)): continue
            m = np.nanmax(arr); i = np.unravel_index(np.nanargmax(arr), arr.shape)
            if m > 0:
                # amps per mm of width -> width of this copper needed if this density held across a neck, reported as amps/mm
                apm = m/G; yy, xx = i[0]*G+X0-100, i[1]*G+X0-100
                print(f"  {l:7s} peak {apm:6.2f} A per mm of width at ({xx:.2f}, {yy:.2f})  ({apm/ (t*1e3) :6.0f} A/mm2)")
    # copper loss per layer + via currents
    vc = []
    for x, y, w, d in vias:
        cx, cy = int((y-X0)/G), int((x-X0)/G); vs = [v[remap[node[l][cx, cy]]] for l in LAY if node[l][cx, cy] >= 0 and remap[node[l][cx, cy]] >= 0]
        if len(vs) > 1:
            area = math.pi*(d*1e-3+plate)*plate
            vc.append(((max(vs)-min(vs))/(RHO*.2e-3*len(vs))*area, x-100, y-100))
    vc.sort(reverse=True)
    print("  busiest vias (A, x, y):", [(round(a_, 3), round(x, 2), round(y, 2)) for a_, x, y in vc[:5]])
if __name__ == "__main__":
    pk = .494
    sinks = {"U1-15": pk/2, "U1-25": pk/2, "U2-15": pk/2, "U2-25": pk/2}
    solve("VSYS", ["U5-10", "U5-11"], sinks)
    solve("+3V3", ["U6-1"], {"U3-49": .06, "U3-1": .01, "U3-20": .01, "U3-30": .01, "U3-38": .01, "U4-8": .025, "U9-9": .005, "U5-6": .001})
    solve("+1V1", ["L1-1"], {"U3-6": .033, "U3-23": .033, "U3-39": .034})
    solve("VBUS", ["J1-5"], {"U5-13": .5})
    drv = lambda r: next(f"{r}-{p.GetNumber()}" for f in b.GetFootprints() if f.GetReference() == r for p in f.Pads() if p.GetNetname() == "GND" and p.GetNumber() != "61")
    u8g = next(f"U8-{p.GetNumber()}" for f in b.GetFootprints() if f.GetReference() == "U8" for p in f.Pads() if p.GetNetname() == "GND")
    print("GND return source", u8g); solve("GND", [u8g], {"U1-61": .494, "U2-61": .494})
    solve("VBAT", ["BT1-1"], {"U5-2": .494, "U5-3": .494})
    solve("/Power/BAT_N", ["BT1-2"], {"U8-4": .494, "U8-5": .494})
    # SW scan lines: the driver pin to each LED anode, 494 mA shared over the line's LEDs.
    nets = {}
    for f in b.GetFootprints():
        for p in f.Pads():
            n = p.GetNetname()
            if "/SW" in n: nets.setdefault(n, []).append(f"{f.GetReference()}-{p.GetNumber()}")
    for n, ps in sorted(nets.items()):
        drv = [q for q in ps if q.startswith("U")]; leds = [q for q in ps if q.startswith("D")]
        if drv and leds: solve(n, drv[:1], {q: .494/len(leds) for q in leds})
