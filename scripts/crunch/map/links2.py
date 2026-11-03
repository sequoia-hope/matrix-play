#!/usr/bin/env python3
"""links2.py BOARD [--zone-len 4] [--other-len 0] [--dry]: F.Cu maze links between same-net cathode lands, chip zones first.

Lands over a chip's exposed pad or pad ring have no via site, so their nets must leave on F.Cu. This joins same-net lands with a small maze search on F.Cu (0.05 mm grid,
obstacles grown by half a track plus clearance plus a grid margin): first lands in those zones, up to --zone-len mm apart, then anywhere, up to --other-len mm apart.
Tracks are locked so `--strip` keeps them; unlock after routing. Writes the board in place: run on a new variant only. Reports links and land groups left per zone.
"""
import argparse, heapq, json, math, sys
import numpy as np
import pcbnew
from shapely.geometry import LineString, Point, Polygon

W, CL, GRID, MARGIN = .1, .09, .05, .04
ORG = -19.5
N = int(39/GRID)
CHIPS = [((-11.4, 3.4), 2.975), ((10.6, 3.4), 2.975), ((-1.4, -6.6), 1.975)]


def zone(x, y):
    """0 over an exposed pad, 1 over a pad ring, 2 elsewhere."""
    z = 2
    for c, h in CHIPS:
        d = max(abs(x-c[0]), abs(y-c[1]))
        if d < h:
            return 0
        if d < 3.9:
            z = 1
    return z


def cell(x, y):
    return int(round((x-ORG)/GRID)), int(round((y-ORG)/GRID))


def raster(geom, grow):
    """Cells within grow of a geometry, as (i0, j0, mask)."""
    x0, y0, x1, y1 = geom.bounds
    i0, j0 = cell(x0-grow, y0-grow); i1, j1 = cell(x1+grow, y1+grow)
    i0, j0 = max(i0, 0), max(j0, 0); i1, j1 = min(i1, N-1), min(j1, N-1)
    g = geom.buffer(grow, 4)
    from shapely import contains_xy
    xs = ORG+np.arange(i0, i1+1)*GRID; ys = ORG+np.arange(j0, j1+1)*GRID
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    return i0, j0, contains_xy(g, X, Y)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("board"); ap.add_argument("--zone-len", type=float, default=4); ap.add_argument("--other-len", type=float, default=0)
    ap.add_argument("--dry", action="store_true"); a = ap.parse_args()
    b = pcbnew.LoadBoard(a.board); um = pcbnew.ToMM; mm = pcbnew.FromMM
    GROW = W/2+CL+MARGIN
    count = np.zeros((N, N), dtype=np.int16)
    own = {}
    def add(geom, net, grow=GROW):
        i0, j0, m = raster(geom, grow)
        count[i0:i0+m.shape[0], j0:j0+m.shape[1]] += m
        own.setdefault(net, []).append((i0, j0, m))
    lands = {}
    for f in b.GetFootprints():
        ref = f.GetReference()
        for p in f.Pads():
            if not p.IsOnLayer(pcbnew.F_Cu):
                continue
            c = p.GetPosition(); cx, cy = um(c.x)-100, um(c.y)-100; net = p.GetNetname()
            if ref.startswith("D"):
                ang = math.radians(-f.GetOrientationDegrees()); s = um(p.GetSizeX())/2; ca, sa = math.cos(ang), math.sin(ang)
                g = Polygon([(cx+u*ca-v*sa, cy+u*sa+v*ca) for u, v in ((-s, -s), (s, -s), (s, s), (-s, s))])
                lands.setdefault(net, []).append((ref, p.GetNumber(), cx, cy))
            else:
                bb = p.GetBoundingBox(); g = Polygon([(um(bb.GetLeft())-100, um(bb.GetTop())-100), (um(bb.GetRight())-100, um(bb.GetTop())-100), (um(bb.GetRight())-100, um(bb.GetBottom())-100), (um(bb.GetLeft())-100, um(bb.GetBottom())-100)])
            add(g, net)
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            c = t.GetPosition(); r = max(um(t.GetWidth(pcbnew.F_Cu))/2+CL, um(t.GetDrill())/2+.2)
            add(Point(um(c.x)-100, um(c.y)-100).buffer(.001), t.GetNetname(), r+W/2+MARGIN)
        elif t.GetLayer() == pcbnew.F_Cu:
            s, e = t.GetStart(), t.GetEnd()
            add(LineString([(um(s.x)-100, um(s.y)-100), (um(e.x)-100, um(e.y)-100)]), t.GetNetname(), um(t.GetWidth())/2+CL+W/2+MARGIN)
    # Board edge.
    X, Y = np.meshgrid(ORG+np.arange(N)*GRID, ORG+np.arange(N)*GRID, indexing="ij")
    edge = np.hypot(X, Y) > 18.6
    count[edge] += 1

    par = {}
    def find(k):
        par.setdefault(k, k)
        while par[k] != k:
            par[k] = par[par[k]]; k = par[k]
        return k
    cand = []
    for net, ls in lands.items():
        if "/CS" not in net:
            continue
        for i in range(len(ls)):
            for j in range(i):
                d = math.hypot(ls[i][2]-ls[j][2], ls[i][3]-ls[j][3])
                zi, zj = zone(ls[i][2], ls[i][3]), zone(ls[j][2], ls[j][3])
                z = min(zi, zj)
                if (z < 2 and d <= a.zone_len) or d <= a.other_len:
                    cand.append((z >= 2, d, net, ls[i], ls[j]))
    cand.sort(key=lambda c: c[:2])
    SQ2 = 2**.5
    MOVES = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, SQ2), (1, -1, SQ2), (-1, 1, SQ2), (-1, -1, SQ2)]

    def maze(net, A, B, limit):
        """A* on F.Cu with this net's own copper lifted. Returns vertices in mm or None."""
        for i0, j0, m in own[net]:
            count[i0:i0+m.shape[0], j0:j0+m.shape[1]] -= m
        s, g = cell(*A), cell(*B)
        h = lambda c: math.hypot(c[0]-g[0], c[1]-g[1])
        best = {s: 0.0}; prev = {}; pq = [(h(s), s)]; found = False; maxc = limit/GRID
        while pq:
            f_, u = heapq.heappop(pq)
            if u == g:
                found = True; break
            gu = best[u]
            if f_ > maxc:
                break
            for dx, dy, w in MOVES:
                v = (u[0]+dx, u[1]+dy)
                if not (0 <= v[0] < N and 0 <= v[1] < N) or count[v] > 0:
                    continue
                ng = gu+w+(.3 if u in prev and (u[0]-prev[u][0], u[1]-prev[u][1]) != (dx, dy) else 0)
                if ng < best.get(v, 1e18):
                    best[v] = ng; prev[v] = u; heapq.heappush(pq, (ng+h(v), v))
        for i0, j0, m in own[net]:
            count[i0:i0+m.shape[0], j0:j0+m.shape[1]] += m
        if not found:
            return None
        cells = [g]
        while cells[-1] != s:
            cells.append(prev[cells[-1]])
        cells.reverse()
        pts = [cells[0]]
        for i in range(1, len(cells)-1):
            d1 = (cells[i][0]-cells[i-1][0], cells[i][1]-cells[i-1][1]); d2 = (cells[i+1][0]-cells[i][0], cells[i+1][1]-cells[i][1])
            if d1 != d2:
                pts.append(cells[i])
        pts.append(g)
        out = [(ORG+i*GRID, ORG+j*GRID) for i, j in pts]
        out[0] = A; out[-1] = B
        return out

    laid = []
    for far, d, net, p, q in cand:
        kp, kq = (net, p[0], p[1]), (net, q[0], q[1])
        if find(kp) == find(kq):
            continue
        A, B = (p[2], p[3]), (q[2], q[3])
        pth = maze(net, A, B, d*1.6+.6)
        if pth:
            laid.append((net, pth)); add(LineString(pth), net, W+CL+MARGIN)
            par[find(kp)] = find(kq)
    groups = {}
    for net, ls in lands.items():
        if "/CS" in net:
            groups[net] = {find((net, l[0], l[1])) for l in ls}
    rep = {"links": len(laid), "mm": round(sum(LineString(p).length for _, p in laid)), "groups": sum(len(v) for v in groups.values())}
    # Groups with no land where a via could go: their nets must still leave on F.Cu.
    stuck = 0; zl = [0, 0, 0]; zo = [0, 0, 0]
    for net, ls in lands.items():
        if "/CS" not in net:
            continue
        by = {}
        for l in ls:
            by.setdefault(find((net, l[0], l[1])), []).append(l)
        for k, m in by.items():
            z = [zone(l[2], l[3]) for l in m]
            if max(z) < 2:
                stuck += 1
    rep["groups_all_in_zone"] = stuck
    print(json.dumps(rep))
    if a.dry:
        return
    for net, pth in laid:
        code = b.FindNet(net).GetNetCode()
        for s, e in zip(pth, pth[1:]):
            t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(mm(s[0]+100), mm(s[1]+100))); t.SetEnd(pcbnew.VECTOR2I(mm(e[0]+100), mm(e[1]+100)))
            t.SetWidth(mm(W)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(code); t.SetLocked(True); b.Add(t)
    pcbnew.SaveBoard(a.board, b)


if __name__ == "__main__":
    main()
