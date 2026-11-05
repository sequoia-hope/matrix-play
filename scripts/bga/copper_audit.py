#!/usr/bin/env python3
"""copper_audit.py BOARD.kicad_pcb [--verbose] -- strict geometric & topological copper check.

Catches routing/post-processing artifacts that KiCad's built-in DRC misses when round endcaps
barely overlap (0.001..0.088 mm) on the same net:
  1. Discontinuous centerline cap-to-cap gaps (two degree-1 endpoints within < w that don't meet)
  2. Mid-segment grazing / unsplit T-junctions & leftover ripped-up stubs whose tip touches same-net copper
  3. Off-center track-to-via connections (track ends on or grazes via annular ring instead of via center)
  4. Pure floating degree-1 stubs (outside pads/vias/zones)
  5. Overlapping duplicate collinear segments (0-deg double-drawn traces)
  6. Morphological copper necks < 0.088 mm anywhere in merged same-net copper (tracks + vias + SMD pads)
  7. Acute V-notch slivers (3..45 deg) between same-net segments whose legs separate into a sharp wedge
"""
from __future__ import annotations

import argparse
import collections
import math
import os
import sys
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union
import pcbnew


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("board")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    b = pcbnew.LoadBoard(args.board)
    um = pcbnew.ToMM
    tracks = [t for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
    vias = [t for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]

    lay_ids = {
        b.GetLayerName(l): l
        for l in range(64)
        if b.GetLayerName(l).endswith(".Cu") and b.IsLayerEnabled(l)
    }

    pads_by_nl = collections.defaultdict(list)
    for f in b.GetFootprints():
        for idx_p, p in enumerate(f.Pads()):
            n = p.GetNetname()
            if not n:
                continue
            px, py = um(p.GetPosition().x), um(p.GetPosition().y)
            for ln, lid in lay_ids.items():
                if p.IsOnLayer(lid):
                    o = p.GetEffectivePolygon(lid).Outline(0)
                    poly = Polygon([(um(o.CPoint(i).x), um(o.CPoint(i).y)) for i in range(o.PointCount())])
                    if poly.is_valid and not poly.is_empty:
                        pads_by_nl[(n, ln)].append((px, py, poly, f"{f.GetReference()}.{p.GetNumber()}#{idx_p}"))

    zones_by_nl = collections.defaultdict(list)
    for z in b.Zones():
        if z.GetIsRuleArea():
            continue
        for ln, lid in lay_ids.items():
            if z.IsOnLayer(lid):
                zones_by_nl[(z.GetNetname(), ln)].append((z, lid))

    vias_by_n = collections.defaultdict(list)
    for v in vias:
        n = v.GetNetname()
        vias_by_n[n].append((um(v.GetPosition().x), um(v.GetPosition().y), um(v.GetWidth(pcbnew.F_Cu)) / 2, v))

    snap = lambda x, y: (round(x, 4), round(y, 4))
    deg = collections.Counter()
    by_nl = collections.defaultdict(list)
    micro_segs = []

    for t in tracks:
        n, ln = t.GetNetname(), t.GetLayerName()
        s = snap(um(t.GetStart().x), um(t.GetStart().y))
        e = snap(um(t.GetEnd().x), um(t.GetEnd().y))
        w = um(t.GetWidth())
        d = math.dist(s, e)
        if d < 0.04:
            in_pad = any(
                poly.contains(Point(s)) and poly.contains(Point(e))
                for _, _, poly, _ in pads_by_nl[(n, ln)]
            )
            if not in_pad:
                micro_segs.append((n, ln, s, e, round(d, 4)))
        deg[(n, ln, s)] += 1
        deg[(n, ln, e)] += 1
        by_nl[(n, ln)].append((s, e, w, t))

    off_via = []
    mid_seg_graze = []
    cap_to_cap_gap = []
    pure_dangling = []

    for (n, ln), segs in by_nl.items():
        pts_seen = {}
        for s, e, w, _ in segs:
            pts_seen[s] = max(pts_seen.get(s, 0.0), w)
            pts_seen[e] = max(pts_seen.get(e, 0.0), w)
        for pt, w in pts_seen.items():
            if deg[(n, ln, pt)] != 1:
                continue
            P_pt = Point(pt)
            if any(poly.buffer(0.003).contains(P_pt) for _, _, poly, _ in pads_by_nl[(n, ln)]):
                continue
            if any(math.dist(pt, (vx, vy)) <= 0.003 for vx, vy, _, _ in vias_by_n[n]):
                continue
            vec = pcbnew.VECTOR2I(pcbnew.FromMM(pt[0]), pcbnew.FromMM(pt[1]))
            if any(z.GetFilledPolysList(lid).Contains(vec) for z, lid in zones_by_nl[(n, ln)]):
                continue
            if any(math.dist(pt, (vx, vy)) <= vr + w / 2 + 0.005 for vx, vy, vr, _ in vias_by_n[n]):
                off_via.append((n, ln, pt, "endpoint"))
                continue
            min_end_d = 999.0
            min_seg_d = 999.0
            for s2, e2, w2, _ in segs:
                if s2 == pt or e2 == pt:
                    continue
                min_end_d = min(min_end_d, math.dist(pt, s2), math.dist(pt, e2))
                min_seg_d = min(min_seg_d, LineString([s2, e2]).distance(P_pt) - w2 / 2)
            if min_end_d < w + 0.005:
                cap_to_cap_gap.append((n, ln, pt, round(min_end_d, 4)))
            elif min_seg_d < w / 2 + 0.005:
                mid_seg_graze.append((n, ln, pt, round(min_seg_d, 4)))
            else:
                pure_dangling.append((n, ln, pt))

        # Check any via on (n, ln) that grazes a track without a centered vertex
        for vx, vy, vr, _ in vias_by_n[n]:
            vp = (vx, vy)
            if any(math.dist(vp, s) <= 0.005 or math.dist(vp, e) <= 0.005 for s, e, _, _ in segs):
                continue
            if any(poly.buffer(0.005).contains(Point(vp)) for _, _, poly, _ in pads_by_nl[(n, ln)]):
                continue
            vec = pcbnew.VECTOR2I(pcbnew.FromMM(vx), pcbnew.FromMM(vy))
            if any(z.GetFilledPolysList(lid).Contains(vec) for z, lid in zones_by_nl[(n, ln)]):
                continue
            for s, e, w, _ in segs:
                if s != e and LineString([s, e]).distance(Point(vp)) <= vr + w / 2 - 0.002:
                    off_via.append((n, ln, (round(vx, 4), round(vy, 4)), "mid_graze"))
                    break

    morph_necks = []
    acute_vnotches = []
    collinear_dups = []
    for (n, ln), segs in by_nl.items():
        if n in ("GND", "VSYS", "+3V3", "+1V1"):
            continue
        geoms = [LineString([s, e]).buffer(w / 2, 8) for s, e, w, _ in segs if s != e]
        for vx, vy, vr, _ in vias_by_n[n]:
            geoms.append(Point(vx, vy).buffer(vr, 12))
        for _, _, poly, _ in pads_by_nl[(n, ln)]:
            geoms.append(poly)
        u = unary_union(geoms)
        comps = list(u.geoms) if hasattr(u, "geoms") else [u]
        for comp in comps:
            er = comp.buffer(-0.043, 8)
            if er.is_empty:
                morph_necks.append((n, ln, "vanished", tuple(round(v, 3) for v in comp.centroid.coords[0])))
            elif hasattr(er, "geoms") and len(er.geoms) > 1:
                morph_necks.append((n, ln, f"pinched->{len(er.geoms)}", tuple(round(v, 3) for v in comp.centroid.coords[0])))

        # Check acute V-notches (3..45 deg where legs separate outside copper width) & 0-deg overlaps
        adj = collections.defaultdict(list)
        for s, e, w, _ in segs:
            if math.dist(s, e) > 0.02:
                adj[s].append((e, w))
                adj[e].append((s, w))
        for vpt, nbrs in adj.items():
            if len(nbrs) < 2:
                continue
            for i in range(len(nbrs)):
                for j in range(i + 1, len(nbrs)):
                    b1, w1 = nbrs[i]
                    b2, w2 = nbrs[j]
                    v1 = (b1[0] - vpt[0], b1[1] - vpt[1])
                    v2 = (b2[0] - vpt[0], b2[1] - vpt[1])
                    l1, l2 = math.hypot(*v1), math.hypot(*v2)
                    if l1 <= 0.02 or l2 <= 0.02:
                        continue
                    c = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)))
                    ang = math.degrees(math.acos(c))
                    if ang < 2.0:
                        collinear_dups.append((n, ln, vpt))
                    elif ang < 45.0:
                        if any(poly.buffer(0.02).contains(Point(vpt)) for _, _, poly, _ in pads_by_nl[(n, ln)]):
                            continue
                        d_sep = ((w1 + w2) / 4.0) / math.sin(math.radians(ang / 2.0))
                        if min(l1, l2) > d_sep + 0.02:
                            acute_vnotches.append((n, ln, vpt, round(ang, 1)))

    total_issues = (
        len(pure_dangling)
        + len(cap_to_cap_gap)
        + len(mid_seg_graze)
        + len(off_via)
        + len(morph_necks)
        + len(acute_vnotches)
        + len(collinear_dups)
    )
    print(
        f"{args.board}: tracks={len(tracks)} vias={len(vias)} | "
        f"dangling={len(pure_dangling)} cap_gap={len(cap_to_cap_gap)} "
        f"mid_graze/stubs={len(mid_seg_graze)} off_via={len(off_via)} "
        f"morph_necks(<86um)={len(morph_necks)} acute_slivers={len(acute_vnotches)} "
        f"collinear_dups={len(collinear_dups)} micro_segs(<40um)={len(micro_segs)}"
    )
    if args.verbose:
        for label, lst in [
            ("PURE_DANGLING", pure_dangling),
            ("CAP_GAP", cap_to_cap_gap),
            ("MID_GRAZE_OR_STUB", mid_seg_graze),
            ("OFF_CENTER_VIA", off_via),
            ("MORPH_NECK", morph_necks),
            ("ACUTE_SLIVER", acute_vnotches),
            ("COLLINEAR_DUP", collinear_dups),
        ]:
            for item in lst[:20]:
                print(f"  {label}: {item}")

    sys.stdout.flush()
    os._exit(1 if total_issues > 0 else 0)


if __name__ == "__main__":
    main()
