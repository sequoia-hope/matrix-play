#!/usr/bin/env python3
"""silk_web.py IN.kicad_pcb OUT.kicad_pcb [--width W] [--clear C] [--no-back-strip] -- the sunflower "seed" web on F.SilkS, and no silk on the back.

The web is the Voronoi diagram of the LED centres, so each LED sits in its own seed-shaped cell, with a ring round the outside. It is clipped back from exposed front copper and holes
by the clearance, so it never prints on a pad. Tented vias are left under it: clipping round every one would chop the seeds up, and the fab prints over them. All footprint silk moves
to the Fab layers (back and front), and reference and value text goes with it, hidden. Copper, zones and nets are untouched.
"""
import argparse, math
import pcbnew
from shapely.geometry import MultiPoint, LineString, Point, box
from shapely.ops import voronoi_diagram, unary_union, linemerge
ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("out")
ap.add_argument("--width", type=float, default=.1); ap.add_argument("--clear", type=float, default=.1); ap.add_argument("--ring", type=float, default=18.75)
ap.add_argument("--no-write", action="store_true")
A = ap.parse_args()
b = pcbnew.LoadBoard(A.src); C = 100.0
mm = lambda v: v/1e6
led = [f for f in b.GetFootprints() if f.GetReference().startswith("D")]
pts = [(mm(f.GetPosition().x)-C, mm(f.GetPosition().y)-C) for f in led]
disc = Point(0, 0).buffer(A.ring, 180)
cells = voronoi_diagram(MultiPoint(pts), envelope=box(-30, -30, 30, 30))
edges = {}
for poly in cells.geoms:
    c = list(poly.exterior.coords)
    for p, q in zip(c, c[1:]):
        k = tuple(sorted((tuple(round(v, 4) for v in p), tuple(round(v, 4) for v in q))))
        edges[k] = 1
lines = [LineString(k) for k in edges]
ring = disc.exterior
# Keep out: exposed front copper and every hole.
keep = []
for f in b.GetFootprints():
    for p in f.Pads():
        at = (mm(p.GetPosition().x)-C, mm(p.GetPosition().y)-C)
        if p.IsOnLayer(pcbnew.F_Cu) or p.GetDrillSize().x > 0:
            # Pad outline as the bounding polygon the fab sees, turned with the part.
            ps = p.GetEffectivePolygon(pcbnew.F_Cu) if p.IsOnLayer(pcbnew.F_Cu) else None
            if ps is not None and ps.OutlineCount():
                o = ps.Outline(0); co = [(mm(o.CPoint(i).x)-C, mm(o.CPoint(i).y)-C) for i in range(o.PointCount())]
                from shapely.geometry import Polygon
                keep.append(Polygon(co).buffer(A.clear + A.width/2, 8))
            else:
                keep.append(Point(at).buffer(mm(p.GetDrillSize().x)/2 + A.clear + A.width/2, 16))
exposed = 0
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T and not t.IsTented(pcbnew.F_Mask):
        exposed += 1
        keep.append(Point(mm(t.GetPosition().x)-C, mm(t.GetPosition().y)-C).buffer(mm(t.GetWidth(pcbnew.F_Cu))/2 + A.clear + A.width/2, 8))
keep = unary_union(keep)
web = linemerge(unary_union([l.intersection(disc) for l in lines if l.intersects(disc)]))
kept = web.difference(keep)
ringkept = ring.difference(keep)
total = web.length; km = kept.length
print(f"web {total:.0f} mm, kept {km:.0f} mm ({100*km/total:.0f}%), ring kept {100*ringkept.length/ring.length:.0f}%, exposed vias on front {exposed}, width {A.width} clear {A.clear}")
if not A.no_write:
    # Strip all silk.
    n = 0
    for f in b.GetFootprints():
        for g in list(f.GraphicalItems()):
            if g.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
                g.SetLayer(pcbnew.B_Fab if g.GetLayer() == pcbnew.B_SilkS else pcbnew.F_Fab); n += 1
        for t in [f.Reference(), f.Value()] + [x for x in f.GetFields()]:
            if t.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
                t.SetVisible(False); t.SetLayer(pcbnew.B_Fab if t.GetLayer() == pcbnew.B_SilkS else pcbnew.F_Fab)
    print("footprint silk items moved to Fab", n)
    def seg(p, q):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.F_SilkS); s.SetWidth(int(A.width*1e6))
        s.SetStart(pcbnew.VECTOR2I(int((p[0]+C)*1e6), int((p[1]+C)*1e6))); s.SetEnd(pcbnew.VECTOR2I(int((q[0]+C)*1e6), int((q[1]+C)*1e6))); b.Add(s)
    count = 0
    for geom in (kept, ringkept):
        for l in (geom.geoms if hasattr(geom, "geoms") else [geom]):
            c = list(l.coords)
            for p, q in zip(c, c[1:]):
                if math.dist(p, q) > .005:
                    seg(p, q); count += 1
    print("segments", count)
    pcbnew.SaveBoard(A.out, b)
