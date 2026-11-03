#!/usr/bin/env python3
"""nudge.py BOARD IN.json OUT.json [REACH]: slide each free back-side part a little, or turn it, so its pads block as few LED pads as possible from taking a via in the pad.
A pad's via needs 0.275 mm to a foreign copper pad (0.2 hole clearance plus the 0.15 drill's radius). Keeps every courtyard clear, keeps decouplers within limits, and leaves the reference block, connectors and drivers alone.
Writes IN.json plus a "move" entry per part. Deterministic."""
import json, math, sys, pcbnew
board, inp, outp = sys.argv[1:4]; REACH = float(sys.argv[4]) if len(sys.argv) > 4 else .7
mm = pcbnew.ToMM; b = pcbnew.LoadBoard(board); fps = {f.GetReference(): f for f in b.GetFootprints()}
FIX = {"Y1", "U1", "U2", "U3", "L1", "C16", "C18", "C17", "R13", "J1", "BT1", "SW1", "SW2", "R14", "R15", "C13"}
TIGHT = {"C8": .4, "C9": .4, "C10": .4, "C11": .4, "C12": .4, "C14": .4, "C19": .4, "C20": .4, "C21": .4, "Y1": .4, "C23": .4, "C24": .4, "R17": .4}
NOTURN = {"U4", "U5", "U7", "U8", "U9", "U6", "Q1", "Y1"}
RAD = .275
leds = []
for r, f in fps.items():
    if r[0] == "D":
        for p in f.Pads():
            c = p.GetPosition(); leds.append((mm(c.x)-100, mm(c.y)-100, p.GetNumber() == "3"))
def cell(x, y): return (int(x//1), int(y//1))
grid = {}
for x, y, an in leds:
    grid.setdefault(cell(x, y), []).append((x, y, an))
def shape(f):
    """Pads and courtyard relative to the part's position, per turn, by turning the real footprint."""
    res = {}; o0 = f.GetOrientationDegrees(); c = f.GetPosition()
    for t in (0, 90, 180, 270):
        f.SetOrientationDegrees(o0+t)
        ps = []
        for p in f.Pads():
            q = p.GetBoundingBox(); ps.append((mm(q.GetLeft()-c.x), mm(q.GetTop()-c.y), mm(q.GetRight()-c.x), mm(q.GetBottom()-c.y)))
        cy = f.GetCourtyard(pcbnew.B_CrtYd)
        q = cy.BBox() if cy.OutlineCount() else f.GetBoundingBox(False)
        res[t] = (ps, (mm(q.GetLeft()-c.x), mm(q.GetTop()-c.y), mm(q.GetRight()-c.x), mm(q.GetBottom()-c.y)), (o0+t) % 360)
    f.SetOrientationDegrees(o0)
    return res
pos = {r: (mm(f.GetPosition().x)-100, mm(f.GetPosition().y)-100) for r, f in fps.items() if r[0] != "D"}
shapes = {r: shape(fps[r]) for r in pos}
turn = {r: 0 for r in pos}
def blocked(ps, x, y):
    n = 0; seen = set()
    for a, c, e, g in ps:
        A, C, E, G = a+x-RAD, c+y-RAD, e+x+RAD, g+y+RAD
        for gx in range(int(A//1), int(E//1)+1):
            for gy in range(int(C//1), int(G//1)+1):
                for lx, ly, an in grid.get((gx, gy), ()):
                    if (lx, ly) in seen: continue
                    if math.hypot(max(a+x-lx, 0, lx-e-x), max(c+y-ly, 0, ly-g-y)) < RAD:
                        seen.add((lx, ly)); n += 1.5 if an else 1
    return n
def box(r, x=None, y=None, t=None):
    x = pos[r][0] if x is None else x; y = pos[r][1] if y is None else y; t = turn[r] if t is None else t
    a, c, e, g = shapes[r][t][1]
    return (a+x, c+y, e+x, g+y)
M = .02
def free(r, bb):
    if max(math.hypot(u, v) for u in (bb[0], bb[2]) for v in (bb[1], bb[3])) > 18.7: return False
    for q in pos:
        if q == r: continue
        o = box(q)
        if not (bb[2]+M <= o[0] or o[2]+M <= bb[0] or bb[3]+M <= o[1] or o[3]+M <= bb[1]): return False
    return True
parts = [r for r in pos if r not in FIX]
start = {r: pos[r] for r in pos}
tot0 = sum(blocked(shapes[r][0][0], *pos[r]) for r in pos)
for sweep in range(3):
    ch = 0
    for r in sorted(parts, key=lambda q: -blocked(shapes[q][0][0], *pos[q])):
        reach = TIGHT.get(r, REACH)
        best = (blocked(shapes[r][turn[r]][0], *pos[r]), 0, pos[r], turn[r])
        sx, sy = start[r]
        for t in ((0,) if r in NOTURN or r.startswith("TP") else (0, 90, 180, 270)):
            k = int(reach/.05)
            for i in range(-k, k+1):
                for j in range(-k, k+1):
                    x, y = sx+i*.05, sy+j*.05
                    d = math.hypot(i*.05, j*.05)
                    if d > reach or not free(r, box(r, x, y, t)): continue
                    s = blocked(shapes[r][t][0], x, y)
                    if (s, d+(.01 if t else 0)) < (best[0], best[1]):
                        best = (s, d+(.01 if t else 0), (x, y), t)
        if best[2] != pos[r] or best[3] != turn[r]:
            pos[r], turn[r] = best[2], best[3]; ch += 1
    print("sweep", sweep, "changed", ch, "blocked now", sum(blocked(shapes[r][turn[r]][0], *pos[r]) for r in pos))
    if not ch: break
o = json.loads(open(inp).read()); mv = o.setdefault("move", {}); o.pop("legalize", None); o.pop("clusters", None) if False else None
far = 0
for r in parts:
    if pos[r] != start[r] or turn[r]:
        mv[r] = [round(pos[r][0], 3), round(pos[r][1], 3), shapes[r][turn[r]][2]]
        far = max(far, math.dist(pos[r], start[r]))
print("weighted blocked", tot0, "->", sum(blocked(shapes[r][turn[r]][0], *pos[r]) for r in pos), "moved", len(mv), "furthest", round(far, 2))
json.dump(o, open(outp, "w"), indent=1)
