#!/usr/bin/env python3
"""trunk.py BOARD NET LAYER FROM TO WIDTHS: lay a locked trunk for NET on LAYER between two pads: vias beside/in each end pad, a stub on the pad's layer if the via isn't in the pad, then an A* track on LAYER.

FROM and TO are REF-PAD[+PAD...]:NVIAS. Obstacles come from every pad, via and track of other nets, with the rules' clearances. Widths are tried widest first. A labelled pre-route, not router copper. Saves over BOARD.
"""
import sys, math, heapq, pcbnew
board, net, layer, a_spec, b_spec, widths = sys.argv[1:7]
b = pcbnew.LoadBoard(board); um = pcbnew.ToMM; mm = pcbnew.FromMM
lid = {b.GetLayerName(l): l for l in range(64) if b.GetLayerName(l).endswith(".Cu")}; L = lid[layer]
CL, HOLE, VD, DR, OX = .09, .2, .3, .15, 100.0
fps = {f.GetReference(): f for f in b.GetFootprints()}
def box(p):
    q = p.GetBoundingBox(); return um(q.GetLeft()), um(q.GetTop()), um(q.GetRight()), um(q.GetBottom())
def dbox(x, y, r): return math.hypot(max(r[0]-x, 0, x-r[2]), max(r[1]-y, 0, y-r[3]))
pads = []
for f in b.GetFootprints():
    for p in f.Pads():
        pads.append((box(p), p.GetNetname(), {b.GetLayerName(l) for l in p.GetLayerSet().Seq() if b.GetLayerName(l).endswith(".Cu")}, p.GetDrillSizeX() > 0))
vias = [(um(t.GetPosition().x), um(t.GetPosition().y), um(t.GetWidth(pcbnew.F_Cu))/2, um(t.GetDrillValue())/2, t.GetNetname()) for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
stubs = [(um(t.GetStart().x), um(t.GetStart().y), um(t.GetEnd().x), um(t.GetEnd().y), um(t.GetWidth())/2, t.GetNetname(), b.GetLayerName(t.GetLayer())) for t in b.GetTracks() if t.GetClass() != "PCB_VIA"]
def seg(px, py, x0, y0, x1, y1):
    vx, vy = x1-x0, y1-y0; n = vx*vx+vy*vy; t = 0 if n == 0 else max(0, min(1, ((px-x0)*vx+(py-y0)*vy)/n)); return math.hypot(px-x0-t*vx, py-y0-t*vy)
new_vias = []
def via_ok(x, y):
    for r, n, ls, hole in pads:
        if n == net: continue
        d = dbox(x, y, r)
        if ls and d < max(VD/2 + CL, DR/2 + HOLE): return False
    for vx, vy, vr, vh, n in vias + new_vias:
        d = math.hypot(x-vx, y-vy)
        if d < DR + vh + HOLE or (n != net and d < VD/2 + vr + CL): return False
    for x0, y0, x1, y1, r, n, l in stubs:
        if n != net and seg(x, y, x0, y0, x1, y1) < VD/2 + r + CL: return False
    return math.hypot(x-OX, y-OX) < 18.6
STUBW = .2
def stub_ok(p, x, y):
    c = p.GetPosition(); cx, cy = um(c.x), um(c.y)
    n = max(2, int(math.hypot(x-cx, y-cy)/.02))
    for i in range(n+1):
        qx, qy = cx+(x-cx)*i/n, cy+(y-cy)*i/n
        for r, nn, ls, hole in pads:
            if nn != net and "B.Cu" in ls and dbox(qx, qy, r) < STUBW/2 + CL: return False
        for vx, vy, vr, vh, nn in vias + new_vias:
            if nn != net and math.hypot(qx-vx, qy-vy) < max(STUBW/2 + vr + CL, STUBW/2 + vh + HOLE): return False
        for x0, y0, x1, y1, r, nn, l in stubs:
            if nn != net and l == "B.Cu" and seg(qx, qy, x0, y0, x1, y1) < STUBW/2 + r + CL: return False
    return True
def place(spec):
    """Vias in the first pad if they fit, else as near it as can be, with a stub. Returns the via points and any stubs."""
    ref, count = spec.split(":"); r, nums = ref.split("-", 1); nums = nums.split("+"); out = []; st = []
    for num in nums:
        p = next(q for q in fps[r].Pads() if q.GetNumber() == num); bx = box(p); cx, cy = (bx[0]+bx[2])/2, (bx[1]+bx[3])/2; c = []
        for dx in range(-40, 41):
            for dy in range(-40, 41):
                x, y = cx+dx*.05, cy+dy*.05; c.append((dbox(x, y, bx), math.hypot(x-cx, y-cy), x, y))
        c.sort(); got = 0
        for d, _, x, y in c:
            if got >= max(1, int(count)//len(nums)): break
            if via_ok(x, y) and (d == 0 or stub_ok(p, x, y)):
                new_vias.append((x, y, VD/2, DR/2, net)); out.append((x, y)); got += 1
                if d > 0: st.append((p, x, y))
        assert got, f"no via site at {r}-{num}"
    return out, st
def blocked_fn(w):
    G = {}
    def blocked(x, y):
        k = (round(x/.05), round(y/.05))
        if k in G: return G[k]
        h = w/2; res = False
        if math.hypot(x-OX, y-OX) > 18.8 - h - .2: res = True
        for r, n, ls, hole in pads:
            if n != net and layer in ls and dbox(x, y, r) < h + CL: res = True; break
        if not res:
            for vx, vy, vr, vh, n in vias + new_vias:
                if n != net and math.hypot(x-vx, y-vy) < max(h + vr + CL, h + vh + HOLE): res = True; break
        if not res:
            for x0, y0, x1, y1, r, n, l in stubs:
                if n != net and l == layer and seg(x, y, x0, y0, x1, y1) < h + r + CL: res = True; break
        G[k] = res; return res
    return blocked
def astar(s, t, w):
    blocked = blocked_fn(w); st = (round(s[0]/.05), round(s[1]/.05)); go = (round(t[0]/.05), round(t[1]/.05))
    h = lambda n: math.hypot(n[0]-go[0], n[1]-go[1])
    pq = [(h(st), 0, st, None)]; seen = {}
    while pq:
        f, g, n, par = heapq.heappop(pq)
        if n in seen: continue
        seen[n] = par
        if n == go:
            path = [n]
            while seen[path[-1]] is not None: path.append(seen[path[-1]])
            return [(a*.05, c*.05) for a, c in reversed(path)], g*.05
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            m = (n[0]+dx, n[1]+dy)
            if m in seen or (blocked(m[0]*.05, m[1]*.05) and m != go): continue
            heapq.heappush(pq, (g+math.hypot(dx, dy)+h(m), g+math.hypot(dx, dy), m, n))
    return None, None
A, sa = place(a_spec); B, sb = place(b_spec)  # pad-to-via stubs are 0.2 mm, so a stub's current is limited by its short length
print("vias", [(round(x-OX, 2), round(y-OX, 2)) for x, y in A], [(round(x-OX, 2), round(y-OX, 2)) for x, y in B], "stubs", len(sa), len(sb))
path = None
for w in map(float, widths.split(",")):
    path, n = astar(A[0], B[0], w)
    if path: print("width", w, "length", round(n, 2)); break
    print("no way at", w)
assert path, "no trunk path"
def simplify(p):
    o = [p[0]]
    for i in range(1, len(p)-1):
        if (p[i][0]-o[-1][0])*(p[i+1][1]-p[i][1]) != (p[i][1]-o[-1][1])*(p[i+1][0]-p[i][0]) or abs((p[i][0]-p[i-1][0])*(p[i+1][1]-p[i][1])-(p[i][1]-p[i-1][1])*(p[i+1][0]-p[i][0])) > 1e-9: o.append(p[i])
    return o + [p[-1]]
nc = b.FindNet(net).GetNetCode()
def track(x0, y0, x1, y1, w, l):
    t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(mm(x0), mm(y0))); t.SetEnd(pcbnew.VECTOR2I(mm(x1), mm(y1))); t.SetWidth(mm(w)); t.SetLayer(l); t.SetNetCode(nc); t.SetLocked(True); b.Add(t)
pts = [A[0]] + simplify(path)[1:-1] + [B[0]]
for p, q in zip(pts, pts[1:]): track(*p, *q, w, L)
for vs in (A, B):
    for p, q in zip(vs, vs[1:]): track(*p, *q, min(w, .3), L)
for x, y in A+B:
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); v.SetWidth(mm(VD)); v.SetDrill(mm(DR)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(nc); v.SetLocked(True); b.Add(v)
for p, x, y in sa + sb:
    c = p.GetPosition(); track(um(c.x), um(c.y), x, y, STUBW, pcbnew.B_Cu)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(board, b)
