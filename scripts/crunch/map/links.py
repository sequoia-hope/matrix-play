#!/usr/bin/env python3
"""links.py BOARD [--max-len 2.2] [--lock/--no-lock] [--dry]: lay F.Cu links between same-net cathode lands of neighbouring LEDs before routing.

Every CS net's tree of lands is tried, shortest edges first, as a straight 0.1 mm track or with one bend. A link must clear foreign lands and other tracks by 0.09 mm,
and any via hole by 0.2 mm. A net's lands joined this way need one way down rather than one each, so the router has fewer through vias to find room for.
Writes the board in place: run on a new variant. Reports links laid and F.Cu groups left. Locked by default so `--strip` keeps them; unlock after routing.
"""
import argparse, json, math, re, sys
import pcbnew
from shapely.geometry import LineString, Point, Polygon
from shapely.prepared import prep
from shapely.strtree import STRtree

W = .1; CL = .09; HOLE = .275


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("board"); ap.add_argument("--max-len", type=float, default=2.2); ap.add_argument("--no-lock", action="store_true"); ap.add_argument("--dry", action="store_true")
    ap.add_argument("--max-per-net", type=int, default=99)
    a = ap.parse_args()
    b = pcbnew.LoadBoard(a.board); um = pcbnew.ToMM; mm = pcbnew.FromMM
    lands = {}; obstacles = []  # (geom, net)
    for f in b.GetFootprints():
        for p in f.Pads():
            if not p.IsOnLayer(pcbnew.F_Cu):
                continue
            poly = p.GetEffectivePolygon(pcbnew.F_Cu) if False else None
            bb = p.GetBoundingBox(); c = p.GetPosition(); ang = math.radians(-f.GetOrientationDegrees()); s = p.GetSizeX()/2e6
            ca, sa = math.cos(ang), math.sin(ang); cx, cy = um(c.x), um(c.y)
            g = Polygon([(cx+u*ca-v*sa, cy+u*sa+v*ca) for u, v in ((-s, -s), (s, -s), (s, s), (-s, s))]) if f.GetReference().startswith("D") else Polygon([(um(bb.GetLeft()), um(bb.GetTop())), (um(bb.GetRight()), um(bb.GetTop())), (um(bb.GetRight()), um(bb.GetBottom())), (um(bb.GetLeft()), um(bb.GetBottom()))])
            obstacles.append((g, p.GetNetname()))
            if f.GetReference().startswith("D"):
                lands.setdefault(p.GetNetname(), []).append((f.GetReference(), p.GetNumber(), cx, cy))
    holes = []
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            c = t.GetPosition(); holes.append((um(c.x), um(c.y), t.GetNetname(), um(t.GetWidth(pcbnew.F_Cu))/2, um(t.GetDrill())/2))
        elif t.GetLayer() == pcbnew.F_Cu:
            s, e = t.GetStart(), t.GetEnd()
            obstacles.append((LineString([(um(s.x), um(s.y)), (um(e.x), um(e.y))]).buffer(um(t.GetWidth())/2), t.GetNetname()))
    for x, y, n, r, h in holes:
        obstacles.append((Point(x, y).buffer(max(r+CL, h+.2)-CL), n))   # measured with CL added below
    # Candidate edges: every land pair under max-len in a net, shortest first; union-find keeps it a forest.
    cand = []
    for net, ls in lands.items():
        if "/CS" not in net:
            continue
        for i in range(len(ls)):
            for j in range(i):
                d = math.hypot(ls[i][2]-ls[j][2], ls[i][3]-ls[j][3])
                if d <= a.max_len:
                    cand.append((d, net, ls[i], ls[j]))
    cand.sort(key=lambda c: c[0])
    par = {}
    def find(k):
        par.setdefault(k, k)
        while par[k] != k:
            par[k] = par[par[k]]; k = par[k]
        return k
    laid = []
    bins = {}
    def bin_add(g, net):
        x0, y0, x1, y1 = g.bounds
        for i in range(int(x0//1), int(x1//1)+1):
            for j in range(int(y0//1), int(y1//1)+1):
                bins.setdefault((i, j), []).append((g, net))
    for g, n in obstacles:
        bin_add(g, n)
    def clear(line, net):
        g = line.buffer(W/2+CL-1e-4)
        x0, y0, x1, y1 = g.bounds; seen = set()
        for i in range(int(x0//1), int(x1//1)+1):
            for j in range(int(y0//1), int(y1//1)+1):
                for o, n in bins.get((i, j), ()):
                    if n != net and id(o) not in seen:
                        seen.add(id(o))
                        if g.intersects(o):
                            return False
        return True
    per = {}
    for d, net, p, q in cand:
        kp, kq = (net, p[0], p[1]), (net, q[0], q[1])
        if find(kp) == find(kq) or per.get(net, 0) >= a.max_per_net:
            continue
        A, B = (p[2], p[3]), (q[2], q[3])
        paths = [[A, B]]
        mx, my = (A[0]+B[0])/2, (A[1]+B[1])/2; ux, uy = (B[1]-A[1])/d, -(B[0]-A[0])/d
        for off in (.1, -.1, .2, -.2, .3, -.3, .45, -.45, .6, -.6):
            for fr in (.5, .3, .7):
                paths.append([A, (A[0]+(B[0]-A[0])*fr+ux*off, A[1]+(B[1]-A[1])*fr+uy*off), B])
        for pth in paths:
            line = LineString(pth)
            if clear(line, net):
                laid.append((net, pth)); bin_add(line.buffer(W/2), net)
                par[find(kp)] = find(kq); per[net] = per.get(net, 0)+1
                break
    groups = {}
    for net, ls in lands.items():
        if "/CS" in net:
            groups[net] = len({find((net, l[0], l[1])) for l in ls})
    print(json.dumps({"candidates": len(cand), "links": len(laid), "mm": round(sum(LineString(p).length for _, p in laid)), "cs_lands": sum(len(v) for k, v in lands.items() if "/CS" in k), "groups": sum(groups.values())}))
    if a.dry:
        return
    for net, pth in laid:
        code = b.FindNet(net).GetNetCode()
        for s, e in zip(pth, pth[1:]):
            t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(mm(s[0]), mm(s[1]))); t.SetEnd(pcbnew.VECTOR2I(mm(e[0]), mm(e[1])))
            t.SetWidth(mm(W)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(code); t.SetLocked(not a.no_lock); b.Add(t)
    pcbnew.SaveBoard(a.board, b)


if __name__ == "__main__":
    main()
