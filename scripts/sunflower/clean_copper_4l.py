#!/usr/bin/env python3
"""clean_copper_4l.py IN.kicad_pcb OUT.kicad_pcb -- fast, SWIG-safe post-route copper cleaner.

Fixes all routing & neck-fixer artifacts in pure Python geometry before mutating pcbnew:
  1. Removes zero-length segments and peels all floating/grazing leftover ripped-up stubs
     whose removal preserves 100% of physical pad/zone connectivity (each physical pad tracked
     uniquely even when multiple pads share a pin number like SW1.1 / SW2.1 / J1)
  2. Coalesces duplicate/overlapping 0-deg collinear sub-segments
  3. Snaps or bridges all off-center track-to-via joins (both endpoints and mid-segment grazes)
     to exact via centers
  4. Bridges discontinuous cap-to-cap centerline gaps and splits mid-segment T-junctions cleanly
  5. Prunes redundant signal-net loop remnants outside pads and peels exposed tails
  6. Resolves acute V-notch slivers (3..45 deg, e.g. SW3_1 on In1.Cu) via 90-deg T-reroute or
     split-vertex webbing, and bridges morphological kisses (< 0.088 mm)
  7. Merges collinear adjacent same-width track segments
"""
from __future__ import annotations

import collections
import math
import os
import sys
from pathlib import Path
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import nearest_points, unary_union
from shapely.strtree import STRtree
import pcbnew

POWER_NETS = {"GND", "VSYS", "+3V3", "+1V1", "VBUS", "VBAT", "/Power/BAT_N", "/MCU/VREG_LX"}
KEEP_ALIVE: list = []


def net_clr(n: str) -> float:
    if any(k in n for k in ("XIN", "XOUT", "C24-Pad1", "USB_D")):
        return 0.15
    if "VREG_LX" in n:
        return 0.12
    if "QSPI" in n:
        return 0.10
    return 0.10


def net_min_w(n: str) -> float:
    if n in ("VBUS", "VBAT", "/Power/BAT_N"):
        return 0.25
    if n == "VSYS":
        return 0.16
    if n == "+3V3":
        return 0.15
    if "/SW" in n:
        return 0.10
    return 0.09


def seg_poly(a: tuple[float, float], c: tuple[float, float], w: float):
    return LineString([a, c]).buffer(w / 2, 8) if math.dist(a, c) > 1e-6 else Point(a).buffer(w / 2, 8)


def snap(q: tuple[float, float]) -> tuple[float, float]:
    return (round(q[0], 4), round(q[1], 4))


def main() -> int:
    inp, out = sys.argv[1], sys.argv[2]
    b = pcbnew.LoadBoard(inp)
    um = pcbnew.ToMM
    fm = pcbnew.FromMM
    V = lambda q: pcbnew.VECTOR2I(fm(q[0]), fm(q[1]))
    P = lambda v: (um(v.x), um(v.y))

    for z in b.Zones():
        if not z.GetIsRuleArea() and z.GetZoneName() in ("plane GND", "RP2350 band"):
            z.SetMinThickness(fm(0.12))
            if z.GetZoneName() == "plane GND":
                z.SetLocalClearance(fm(0.15))
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.BuildConnectivity()
    base_open = b.GetConnectivity().GetUnconnectedCount(False)
    print(f"Loaded {inp}: initial unconnected = {base_open}")

    lay_ids = {
        b.GetLayerName(l): l
        for l in range(64)
        if b.GetLayerName(l).endswith(".Cu") and b.IsLayerEnabled(l)
    }

    # ------------------------------------------------------------------
    # 0. Extract ALL board geometry into pure Python BEFORE any Remove()
    #    IMPORTANT: Every physical pad gets a unique ID `ref.num#idx` so
    #    multi-pad pins (SW1.1, SW2.1, J1 USB-C) stay connected!
    # ------------------------------------------------------------------
    pads_by_nl = collections.defaultdict(list)
    pads_by_net = collections.defaultdict(set)
    all_pads_layer = {ln: [] for ln in lay_ids}
    holes = []

    for f in b.GetFootprints():
        ref = f.GetReference()
        for idx_p, p in enumerate(f.Pads()):
            n = p.GetNetname()
            pid = f"{ref}.{p.GetNumber()}#{idx_p}"
            pos = P(p.GetPosition())
            if n and not n.startswith("unconnected"):
                pads_by_net[n].add(pid)
            for ln, lid in lay_ids.items():
                if p.IsOnLayer(lid):
                    o = p.GetEffectivePolygon(lid).Outline(0)
                    poly = Polygon([(um(o.CPoint(i).x), um(o.CPoint(i).y)) for i in range(o.PointCount())])
                    if not poly.is_valid:
                        poly = poly.buffer(0)
                    if not poly.is_empty:
                        if n and not n.startswith("unconnected"):
                            pads_by_nl[(n, ln)].append((pos, poly, pid))
                        all_pads_layer[ln].append((poly, n))
            if p.GetDrillSizeX() > 0:
                holes.append((Point(pos).buffer(um(p.GetDrillSizeX()) / 2, 12), n))

    zone_polys_nl = collections.defaultdict(list)
    rule_areas = []
    for z in b.Zones():
        if z.GetIsRuleArea():
            zname = z.GetZoneName()
            o = z.Outline().Outline(0)
            rpoly = Polygon([(um(o.CPoint(i).x), um(o.CPoint(i).y)) for i in range(o.PointCount())])
            if not rpoly.is_valid:
                rpoly = rpoly.buffer(0)
            zlays = {ln for ln, lid in lay_ids.items() if z.IsOnLayer(lid)}
            if zname == "U3 ring":
                rule_areas.append((rpoly, zlays, {"+3V3", "+1V1", "GND"}, True))
            elif zname == "reg corner":
                rule_areas.append((rpoly, zlays, {"/MCU/VREG_LX", "+1V1", "+3V3", "GND", "/MCU/VREG_AVDD"}, True))
            elif zname == "L1 window":
                rule_areas.append((rpoly, zlays, {"/MCU/VREG_LX", "+1V1"}, True))
            elif zname.endswith("solid EP"):
                rule_areas.append((rpoly, zlays, {"GND"}, True))
            continue

        zn = z.GetNetname()
        for ln, lid in lay_ids.items():
            if z.IsOnLayer(lid):
                ps = z.GetFilledPolysList(lid)
                for k in range(ps.OutlineCount()):
                    o = ps.Outline(k)
                    pts = [(um(o.CPoint(i).x), um(o.CPoint(i).y)) for i in range(o.PointCount())]
                    if len(pts) >= 3:
                        hls = []
                        for h in range(ps.HoleCount(k)):
                            ho = ps.Hole(k, h)
                            hpts = [(um(ho.CPoint(i).x), um(ho.CPoint(i).y)) for i in range(ho.PointCount())]
                            if len(hpts) >= 3:
                                hls.append(hpts)
                        zp = Polygon(pts, hls)
                        if not zp.is_valid:
                            zp = zp.buffer(0)
                        if not zp.is_empty:
                            zone_polys_nl[(zn, ln)].append(zp)

    vias = {}
    tracks = {}
    next_id = 1
    for item in b.GetTracks():
        if isinstance(item, pcbnew.PCB_VIA):
            vid = next_id
            next_id += 1
            vp = P(item.GetPosition())
            vr = um(item.GetWidth(pcbnew.F_Cu)) / 2
            vd = um(item.GetDrill()) / 2
            vias[vid] = {
                "id": vid,
                "p": vp,
                "r": vr,
                "d": vd,
                "net": item.GetNetname(),
                "nc": item.GetNetCode(),
                "obj": item,
                "active": True,
            }
        else:
            tid = next_id
            next_id += 1
            a, c = P(item.GetStart()), P(item.GetEnd())
            w = um(item.GetWidth())
            tracks[tid] = {
                "id": tid,
                "a": a,
                "b": c,
                "w": w,
                "ln": item.GetLayerName(),
                "net": item.GetNetname(),
                "nc": item.GetNetCode(),
                "obj": item,
                "orig_a": a,
                "orig_b": c,
                "active": True,
            }

    pad_buf_cache: dict[tuple[str, str, float], list[Polygon]] = {}

    def in_pad(n: str, ln: str, pt: tuple[float, float], tol: float = 0.003) -> bool:
        key = (n, ln, tol)
        blist = pad_buf_cache.get(key)
        if blist is None:
            blist = [poly.buffer(tol) for _, poly, _ in pads_by_nl[(n, ln)]]
            pad_buf_cache[key] = blist
        gpt = Point(pt)
        return any(bp.contains(gpt) for bp in blist)

    def in_zone(n: str, ln: str, pt: tuple[float, float]) -> bool:
        gpt = Point(pt)
        return any(zp.buffer(-0.002).contains(gpt) for zp in zone_polys_nl[(n, ln)])

    def new_track(a, c, w, ln, net, nc):
        nonlocal next_id
        if math.dist(a, c) < 0.001:
            return None
        tid = next_id
        next_id += 1
        rec = {
            "id": tid,
            "a": a,
            "b": c,
            "w": w,
            "ln": ln,
            "net": net,
            "nc": nc,
            "obj": None,
            "orig_a": None,
            "orig_b": None,
            "active": True,
        }
        tracks[tid] = rec
        tracks_by_net[net].append(rec)
        return rec

    # ------------------------------------------------------------------
    # Build fast per-net physical overlap graph for Pass 1 stub peeling
    # ------------------------------------------------------------------
    removed_zero = 0
    for t in tracks.values():
        if math.dist(t["a"], t["b"]) < 0.001:
            t["active"] = False
            removed_zero += 1

    vias_by_net = collections.defaultdict(list)
    for v in vias.values():
        if v["active"]:
            vias_by_net[v["net"]].append(v)

    tracks_by_net = collections.defaultdict(list)
    for t in tracks.values():
        if t["active"]:
            tracks_by_net[t["net"]].append(t)

    net_adj = collections.defaultdict(lambda: collections.defaultdict(set))
    for n in set(list(pads_by_net.keys()) + list(tracks_by_net.keys())):
        if not n:
            continue
        for ln in lay_ids:
            items = []
            for _, poly, pid in pads_by_nl[(n, ln)]:
                items.append((("PAD", pid), poly))
            for zi, zp in enumerate(zone_polys_nl[(n, ln)]):
                items.append((("ZONE", ln, zi), zp))
            for v in vias_by_net[n]:
                items.append((("VIA", v["id"]), Point(v["p"]).buffer(v["r"], 12)))
            for t in tracks_by_net[n]:
                if t["ln"] == ln and t["active"]:
                    items.append((("TRK", t["id"]), seg_poly(t["a"], t["b"], t["w"])))
            if len(items) < 2:
                continue
            tree = STRtree([g for _, g in items])
            for i, (nk1, g1) in enumerate(items):
                for j in tree.query(g1.buffer(1e-4)):
                    if j <= i:
                        continue
                    nk2, g2 = items[j]
                    if nk1 != nk2 and g1.distance(g2) <= 1e-4:
                        # Do NOT treat a narrow (<0.09 mm) PAD<->VIA corner kiss as a sound connection,
                        # otherwise stub peeling would delete the bridge track and cause connection_width DRC errors!
                        if {nk1[0], nk2[0]} == {"PAD", "VIA"}:
                            er = unary_union([g1, g2]).buffer(-0.0445, 8)
                            if er.is_empty or (hasattr(er, "geoms") and len(er.geoms) > 1):
                                continue
                        net_adj[n][nk1].add(nk2)
                        net_adj[n][nk2].add(nk1)

    def pad_partition(n: str, skip_node=None) -> tuple:
        pads = sorted(pads_by_net[n])
        if len(pads) <= 1:
            return ()
        adj = net_adj[n]
        seen = {}
        comp_id = 0
        out = []
        for pid in pads:
            start = ("PAD", pid)
            if start in seen:
                out.append(seen[start])
                continue
            comp_id += 1
            q = collections.deque([start])
            seen[start] = comp_id
            while q:
                u = q.popleft()
                for w in adj.get(u, ()):
                    if w == skip_node or w in seen:
                        continue
                    if w[0] == "TRK" and not tracks[w[1]]["active"]:
                        continue
                    if w[0] == "VIA" and not vias[w[1]]["active"]:
                        continue
                    seen[w] = comp_id
                    q.append(w)
            out.append(seen[start])
        return tuple(out)

    base_parts = {n: pad_partition(n) for n in pads_by_net if n}

    # ------------------------------------------------------------------
    # PASS 1: Peel all degree-1 non-pad / non-via-center / non-zone stubs
    # whose removal preserves physical pad connectivity!
    # ------------------------------------------------------------------
    peeled_stubs = 0
    for _round in range(15):
        deg = collections.Counter()
        for t in tracks.values():
            if t["active"]:
                deg[(t["net"], t["ln"], snap(t["a"]))] += 1
                deg[(t["net"], t["ln"], snap(t["b"]))] += 1

        changed = 0
        for t in list(tracks.values()):
            if not t["active"]:
                continue
            n, ln = t["net"], t["ln"]
            s, e = t["a"], t["b"]
            # Never peel an intentional pad-center entry segment inside a pad
            if in_pad(n, ln, s, tol=0.005) and in_pad(n, ln, e, tol=0.005):
                continue
            bad_s = (
                deg[(n, ln, snap(s))] == 1
                and not in_pad(n, ln, s)
                and not any(math.dist(s, v["p"]) <= 0.003 for v in vias_by_net[n] if v["active"])
                and not in_zone(n, ln, s)
            )
            bad_e = (
                deg[(n, ln, snap(e))] == 1
                and not in_pad(n, ln, e)
                and not any(math.dist(e, v["p"]) <= 0.003 for v in vias_by_net[n] if v["active"])
                and not in_zone(n, ln, e)
            )
            if not (bad_s or bad_e):
                continue
            if not n or pad_partition(n, skip_node=("TRK", t["id"])) == base_parts.get(n, ()):
                t["active"] = False
                deg[(n, ln, snap(s))] -= 1
                deg[(n, ln, snap(e))] -= 1
                peeled_stubs += 1
                changed += 1
        if not changed:
            break

    # Coalesce duplicate / contained / overlapping 0-deg collinear segments
    def coalesce_collinear() -> int:
        merged = 0
        by_nl_loc = collections.defaultdict(list)
        for t in tracks.values():
            if t["active"]:
                by_nl_loc[(t["net"], t["ln"])].append(t)
        for (n, ln), segs in by_nl_loc.items():
            changed_nl = True
            while changed_nl:
                changed_nl = False
                act = [t for t in segs if t["active"]]
                for i in range(len(act)):
                    t1 = act[i]
                    if not t1["active"]:
                        continue
                    a1, b1, w1 = t1["a"], t1["b"], t1["w"]
                    l1 = math.dist(a1, b1)
                    if l1 < 0.001:
                        t1["active"] = False
                        continue
                    ux, uy = (b1[0] - a1[0]) / l1, (b1[1] - a1[1]) / l1
                    for j in range(i + 1, len(act)):
                        t2 = act[j]
                        if not t2["active"]:
                            continue
                        a2, b2, w2 = t2["a"], t2["b"], t2["w"]
                        l2 = math.dist(a2, b2)
                        if l2 < 0.001:
                            t2["active"] = False
                            continue
                        # Perpendicular distance from a2 and b2 to infinite line a1-b1
                        d_perp_a = abs((a2[0] - a1[0]) * (-uy) + (a2[1] - a1[1]) * ux)
                        d_perp_b = abs((b2[0] - a1[0]) * (-uy) + (b2[1] - a1[1]) * ux)
                        if d_perp_a > 0.0008 or d_perp_b > 0.0008:
                            continue
                        p2a = (a2[0] - a1[0]) * ux + (a2[1] - a1[1]) * uy
                        p2b = (b2[0] - a1[0]) * ux + (b2[1] - a1[1]) * uy
                        lo2, hi2 = min(p2a, p2b), max(p2a, p2b)
                        # Check 1D interval overlap strictly (> 0.002 mm overlap, not just meeting at endpoint)
                        if min(l1, hi2) - max(0.0, lo2) > 0.002:
                            if abs(w1 - w2) <= 1e-4:
                                lo = min(0.0, lo2)
                                hi = max(l1, hi2)
                                pts_map = {0.0: a1, l1: b1, p2a: a2, p2b: b2}
                                new_a = pts_map[lo]
                                new_b = pts_map[hi]
                                t1["a"], t1["b"] = new_a, new_b
                                l1 = math.dist(new_a, new_b)
                                ux, uy = (new_b[0] - new_a[0]) / l1, (new_b[1] - new_a[1]) / l1
                                a1, b1 = new_a, new_b
                                t2["active"] = False
                                merged += 1
                                changed_nl = True
                            elif w2 < w1 and lo2 >= -0.001 and hi2 <= l1 + 0.001:
                                # Narrower segment completely contained inside wider segment
                                t2["active"] = False
                                merged += 1
                                changed_nl = True
        return merged

    dup_merged_1 = coalesce_collinear()
    print(f"Pass 1: zero={removed_zero}, peeled_stubs={peeled_stubs}, dup_collinear={dup_merged_1}")

    # ------------------------------------------------------------------
    # Helper: Clearance + Edge + Rule-Area checker
    # ------------------------------------------------------------------
    edge_ps = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(edge_ps)
    e_out = edge_ps.Outline(0)
    board_poly = Polygon([(um(e_out.CPoint(i).x), um(e_out.CPoint(i).y)) for i in range(e_out.PointCount())])
    if not board_poly.is_valid:
        board_poly = board_poly.buffer(0)
    board_circle = board_poly.buffer(-0.20, 32)

    def build_clearance_checker():
        layer_items = {ln: [] for ln in lay_ids}
        hole_items = list(holes)
        for ln in lay_ids:
            for poly, n in all_pads_layer[ln]:
                layer_items[ln].append((poly, n, None))
        for v in vias.values():
            if not v["active"]:
                continue
            vg = Point(v["p"]).buffer(v["r"], 12)
            for ln in lay_ids:
                layer_items[ln].append((vg, v["net"], v["id"]))
            hole_items.append((Point(v["p"]).buffer(v["d"], 12), v["net"]))
        for t in tracks.values():
            if not t["active"]:
                continue
            layer_items[t["ln"]].append((seg_poly(t["a"], t["b"], t["w"]), t["net"], t["id"]))

        trees = {ln: STRtree([x[0] for x in layer_items[ln]]) for ln in lay_ids}
        htree = STRtree([x[0] for x in hole_items])

        def is_clear(ln: str, geom, net: str, ignore_ids: set[int] = set()) -> bool:
            if not board_circle.contains(geom):
                return False
            for rpoly, rlays, allowed, dis_trk in rule_areas:
                if dis_trk and ln in rlays and net not in allowed and geom.intersects(rpoly):
                    return False
            for idx in trees[ln].query(geom.buffer(0.20)):
                g2, n2, oid = layer_items[ln][idx]
                if n2 == net or (oid is not None and oid in ignore_ids):
                    continue
                req = max(net_clr(net), net_clr(n2)) - 1e-4
                if geom.distance(g2) < req:
                    return False
            for idx in htree.query(geom.buffer(0.21)):
                h2, n2 = hole_items[idx]
                if n2 == net:
                    continue
                if geom.distance(h2) < 0.20 - 1e-4:
                    return False
            return True

        return is_clear

    # ------------------------------------------------------------------
    # PASS 2: Heal ALL off-center via joins (both degree-1 endpoints and
    # mid-segment / elbow / pad-edge via grazes)
    # ------------------------------------------------------------------
    is_clear = build_clearance_checker()
    deg = collections.Counter()
    by_nl = collections.defaultdict(list)
    for t in tracks.values():
        if t["active"]:
            deg[(t["net"], t["ln"], snap(t["a"]))] += 1
            deg[(t["net"], t["ln"], snap(t["b"]))] += 1
            by_nl[(t["net"], t["ln"])].append(t)

    snapped_via = 0
    bridged_via = 0
    mid_via_fixed = 0

    for (n, ln), segs in list(by_nl.items()):
        for t in list(segs):
            if not t["active"]:
                continue
            w = t["w"]
            for end_key, far_key in (("a", "b"), ("b", "a")):
                pt = t[end_key]
                far = t[far_key]
                if deg[(n, ln, snap(pt))] != 1:
                    continue
                if in_pad(n, ln, pt) or in_zone(n, ln, pt):
                    continue
                if any(math.dist(pt, v["p"]) <= 0.003 for v in vias_by_net[n] if v["active"]):
                    continue
                near_v = [
                    (math.dist(pt, v["p"]), v["p"], v["r"])
                    for v in vias_by_net[n]
                    if v["active"] and math.dist(pt, v["p"]) <= v["r"] + w / 2 + 0.02
                ]
                if not near_v:
                    continue
                near_v.sort()
                _, vp, vr = near_v[0]
                far_in_pad = in_pad(n, ln, far, tol=w / 2 + 0.02)
                if not far_in_pad and math.dist(far, vp) > 0.002 and is_clear(ln, seg_poly(far, vp, w), n, {t["id"]}):
                    deg[(n, ln, snap(pt))] -= 1
                    t[end_key] = vp
                    deg[(n, ln, snap(vp))] += 1
                    snapped_via += 1
                else:
                    via_disc = Point(vp).buffer(vr + 1e-4, 16)
                    cand_ws = [w] if n in POWER_NETS or w <= 0.101 else [w, 0.10]
                    for bw in cand_ws:
                        g_br = seg_poly(pt, vp, bw)
                        if via_disc.contains(g_br) or is_clear(ln, g_br, n, {t["id"]}):
                            nt = new_track(pt, vp, bw, ln, n, t["nc"])
                            if nt:
                                by_nl[(n, ln)].append(nt)
                                deg[(n, ln, snap(pt))] += 1
                                deg[(n, ln, snap(vp))] += 1
                                bridged_via += 1
                            break

    # 2b. Mid-segment / elbow / pad-edge via grazes where via center has no vertex on (n, ln)
    is_clear = build_clearance_checker()
    by_nl = collections.defaultdict(list)
    for t in tracks.values():
        if t["active"]:
            by_nl[(t["net"], t["ln"])].append(t)

    for (n, ln), segs in list(by_nl.items()):
        for v in vias_by_net[n]:
            if not v["active"]:
                continue
            vp = v["p"]
            vr = v["r"]
            if any(math.dist(vp, t["a"]) <= 0.005 or math.dist(vp, t["b"]) <= 0.005 for t in segs if t["active"]):
                continue
            if in_pad(n, ln, vp, tol=0.005) or in_zone(n, ln, vp):
                continue
            best_hit = None
            Pvp = Point(vp)
            for t in segs:
                if not t["active"] or math.dist(t["a"], t["b"]) < 0.001:
                    continue
                ls = LineString([t["a"], t["b"]])
                d = ls.distance(Pvp)
                if d <= vr + t["w"] / 2 + 0.002:
                    proj = ls.interpolate(ls.project(Pvp))
                    q = (proj.x, proj.y)
                    if best_hit is None or d < best_hit[0]:
                        best_hit = (d, t, q)
            if best_hit is not None:
                _, t, q = best_hit
                w = t["w"]
                via_disc = Point(vp).buffer(vr + 1e-4, 16)
                cand_ws = [w] if n in POWER_NETS or w <= 0.101 else [w, 0.10]
                for bw in cand_ws:
                    g_br = seg_poly(q, vp, bw)
                    if via_disc.contains(g_br) or is_clear(ln, g_br, n, {t["id"]}):
                        a0, b0 = t["a"], t["b"]
                        if math.dist(q, a0) > 0.003 and math.dist(q, b0) > 0.003:
                            t["b"] = q
                            nt_split = new_track(q, b0, w, ln, n, t["nc"])
                            if nt_split:
                                segs.append(nt_split)
                        nt_br = new_track(q, vp, bw, ln, n, t["nc"])
                        if nt_br:
                            segs.append(nt_br)
                            mid_via_fixed += 1
                        break

    # ------------------------------------------------------------------
    # PASS 3: Bridge remaining cap-to-cap gaps and split T-junctions
    # ------------------------------------------------------------------
    is_clear = build_clearance_checker()
    deg = collections.Counter()
    by_nl = collections.defaultdict(list)
    for t in tracks.values():
        if t["active"]:
            deg[(t["net"], t["ln"], snap(t["a"]))] += 1
            deg[(t["net"], t["ln"], snap(t["b"]))] += 1
            by_nl[(t["net"], t["ln"])].append(t)

    bridged_gap = 0
    split_tjunc = 0
    paired = set()

    for (n, ln), segs in list(by_nl.items()):
        for t in list(segs):
            if not t["active"]:
                continue
            w = t["w"]
            for end_key in ("a", "b"):
                pt = t[end_key]
                spt = snap(pt)
                if (n, ln, spt) in paired or deg[(n, ln, spt)] != 1:
                    continue
                if in_pad(n, ln, pt) or in_zone(n, ln, pt):
                    continue
                if any(math.dist(pt, v["p"]) <= 0.004 for v in vias_by_net[n] if v["active"]):
                    continue

                best_end = None
                for t2 in by_nl[(n, ln)]:
                    if t2 is t or not t2["active"]:
                        continue
                    for q in (t2["a"], t2["b"]):
                        d = math.dist(pt, q)
                        if 0.001 < d <= max(w, t2["w"]) + 0.05:
                            if best_end is None or d < best_end[0]:
                                best_end = (d, q, min(w, t2["w"]))
                if best_end is not None:
                    _, q, bw = best_end
                    far = t["b"] if end_key == "a" else t["a"]
                    done_end = False
                    # First try snapping `pt -> q` directly (avoids tight-pad clearance & 0-deg backtracks!)
                    if math.dist(far, q) > 0.003 and is_clear(ln, seg_poly(far, q, w), n, {t["id"]}):
                        deg[(n, ln, spt)] -= 1
                        t[end_key] = q
                        deg[(n, ln, snap(q))] += 1
                        paired.add((n, ln, snap(q)))
                        bridged_gap += 1
                        done_end = True
                    if not done_end:
                        cand_ws = [bw] if n in POWER_NETS or bw <= 0.101 else [bw, 0.10]
                        for try_w in cand_ws:
                            if is_clear(ln, seg_poly(pt, q, try_w), n):
                                nt = new_track(pt, q, try_w, ln, n, t["nc"])
                                if nt:
                                    by_nl[(n, ln)].append(nt)
                                    deg[(n, ln, spt)] += 1
                                    deg[(n, ln, snap(q))] += 1
                                    paired.add((n, ln, spt))
                                    paired.add((n, ln, snap(q)))
                                    bridged_gap += 1
                                    done_end = True
                                    break
                    if done_end:
                        continue

                best_mid = None
                Ppt = Point(pt)
                for t2 in by_nl[(n, ln)]:
                    if t2 is t or not t2["active"] or math.dist(t2["a"], t2["b"]) < 0.001:
                        continue
                    ls = LineString([t2["a"], t2["b"]])
                    d = ls.distance(Ppt)
                    if d <= (w + t2["w"]) / 2 + 0.05:
                        proj = ls.interpolate(ls.project(Ppt))
                        q = (proj.x, proj.y)
                        if best_mid is None or d < best_mid[0]:
                            best_mid = (d, t2, q)
                if best_mid is not None:
                    _, t2, q = best_mid
                    cand_ws = [w] if n in POWER_NETS or w <= 0.101 else [w, 0.10]
                    for try_w in cand_ws:
                        if is_clear(ln, seg_poly(pt, q, try_w), n):
                            a2, b2, w2 = t2["a"], t2["b"], t2["w"]
                            if math.dist(q, a2) > 0.002 and math.dist(q, b2) > 0.002:
                                t2["b"] = q
                                nt2 = new_track(q, b2, w2, ln, n, t2["nc"])
                                if nt2:
                                    by_nl[(n, ln)].append(nt2)
                                deg[(n, ln, snap(q))] += 2
                            nt = new_track(pt, q, try_w, ln, n, t["nc"])
                            if nt:
                                by_nl[(n, ln)].append(nt)
                                deg[(n, ln, spt)] += 1
                                deg[(n, ln, snap(q))] += 1
                                paired.add((n, ln, spt))
                                split_tjunc += 1
                            break

    print(
        f"Pass 2-3: snapped_via={snapped_via}, bridged_via={bridged_via}, "
        f"mid_via_fixed={mid_via_fixed}, bridged_gap={bridged_gap}, split_tjunc={split_tjunc}"
    )

    # 3b. Weld lateral same-net track kisses (0 < centerline_dist < (w1+w2)/2) so KiCad DRC never
    # flags narrow connection_width lenses between parallel branches and Pass 4 can prune redundant loops!
    is_clear = build_clearance_checker()
    welded_kisses = 0
    for (n, ln), segs in list(by_nl.items()):
        if n == "GND":
            continue
        act = [t for t in segs if t["active"] and math.dist(t["a"], t["b"]) > 0.005]
        weld_pts = []
        for i in range(len(act)):
            t1 = act[i]
            if not t1["active"]:
                continue
            for j in range(i + 1, len(act)):
                t2 = act[j]
                if not t2["active"]:
                    continue
                if any(math.dist(p, q) <= 0.005 for p in (t1["a"], t1["b"]) for q in (t2["a"], t2["b"])):
                    continue
                ls1 = LineString([t1["a"], t1["b"]])
                ls2 = LineString([t2["a"], t2["b"]])
                d_lat = ls1.distance(ls2)
                if 0.002 < d_lat < (t1["w"] + t2["w"]) / 2.0 - 0.001:
                    bw = max(net_min_w(n), min(t1["w"], t2["w"]))
                    cand_pairs = []
                    p1, p2 = nearest_points(ls1, ls2)
                    cand_pairs.append(((p1.x, p1.y), (p2.x, p2.y)))
                    # Also bridge diverging fork ends within (w1+w2)/2 + 0.05 mm so Pass 4 collapses twin parallel stems!
                    max_fork = (t1["w"] + t2["w"]) / 2.0 + 0.05
                    for ep in (t1["a"], t1["b"]):
                        qp = ls2.interpolate(ls2.project(Point(ep)))
                        q2 = (qp.x, qp.y)
                        if 0.005 < math.dist(ep, q2) <= max_fork:
                            cand_pairs.append((ep, q2))
                    for ep in (t2["a"], t2["b"]):
                        qp = ls1.interpolate(ls1.project(Point(ep)))
                        q1 = (qp.x, qp.y)
                        if 0.005 < math.dist(q1, ep) <= max_fork:
                            cand_pairs.append((q1, ep))
                    for q1, q2 in cand_pairs:
                        if in_pad(n, ln, q1, tol=0.045) or in_pad(n, ln, q2, tol=0.045):
                            continue
                        mid = ((q1[0] + q2[0]) * 0.5, (q1[1] + q2[1]) * 0.5)
                        if any(math.dist(mid, wp) < 0.09 for wp in weld_pts):
                            continue
                        if math.dist(q1, q2) >= 0.002 and is_clear(ln, seg_poly(q1, q2, bw), n, {t1["id"], t2["id"]}):
                            # Project q1 onto current active subsegment of t1's line and q2 onto t2's line
                            for target_seg, qpt in ((t1, q1), (t2, q2)):
                                # Find active segment in `segs` containing `qpt` within 0.002 mm
                                for s in list(segs):
                                    if not s["active"]:
                                        continue
                                    sa, sb, sw = s["a"], s["b"], s["w"]
                                    if math.dist(qpt, sa) > 0.004 and math.dist(qpt, sb) > 0.004:
                                        if LineString([sa, sb]).distance(Point(qpt)) <= 0.002:
                                            s["b"] = qpt
                                            ns = new_track(qpt, sb, sw, ln, n, s["nc"])
                                            if ns:
                                                segs.append(ns)
                                            break
                            wb = new_track(q1, q2, bw, ln, n, t1["nc"])
                            if wb:
                                wb["weld"] = True
                                segs.append(wb)
                                weld_pts.append(mid)
                                welded_kisses += 1
    if welded_kisses:
        print(f"Pass 3b: welded_lateral_kisses={welded_kisses}")

    # ------------------------------------------------------------------
    # PASS 4: Prune redundant signal-net cycles OUTSIDE pads (never
    # deleting pad-entry segments!) and peel exposed multi-hop tails
    # ------------------------------------------------------------------
    pad_buf5 = {
        (n, ln): [(poly.buffer(0.005), pid) for _, poly, pid in plist]
        for (n, ln), plist in pads_by_nl.items()
    }
    pad_buf10 = {
        (n, ln): [(poly.buffer(0.010), pid) for _, poly, pid in plist]
        for (n, ln), plist in pads_by_nl.items()
    }

    via_pad_hits: dict[int, list[str]] = {}
    for n, nvias in vias_by_net.items():
        for v in nvias:
            hits = set()
            Pv = Point(v["p"])
            for ln in lay_ids:
                for pbuf, pid in pad_buf10.get((n, ln), ()):
                    if pbuf.contains(Pv):
                        hits.add(pid)
            via_pad_hits[v["id"]] = list(hits)

    pt_pad_hits: dict[tuple[str, str, tuple[float, float]], list[str]] = {}

    def pads_at_pt(n: str, ln: str, pt: tuple[float, float]) -> list[str]:
        key = (n, ln, snap(pt))
        res = pt_pad_hits.get(key)
        if res is None:
            Ppt = Point(pt)
            res = [pid for pbuf, pid in pad_buf5.get((n, ln), ()) if pbuf.contains(Ppt)]
            pt_pad_hits[key] = res
        return res

    def strict_pad_partition(n: str, skip_tid=None, skip_vid=None) -> tuple:
        pads = sorted(pads_by_net[n])
        if len(pads) <= 1:
            return ()
        parent = {}

        def find(x):
            while parent.setdefault(x, x) != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, c):
            ra, rc = find(a), find(c)
            if ra != rc:
                parent[ra] = rc

        for v in vias_by_net[n]:
            if not v["active"] or v["id"] == skip_vid:
                continue
            svp = snap(v["p"])
            vnode = ("VIA", v["id"])
            for ln in lay_ids:
                union(vnode, ("PT", ln, svp))
            for pid in via_pad_hits.get(v["id"], ()):
                union(vnode, ("PAD", pid))

        for t in tracks_by_net[n]:
            if not t["active"] or t["id"] == skip_tid:
                continue
            ln = t["ln"]
            sa, sb = snap(t["a"]), snap(t["b"])
            na, nb = ("PT", ln, sa), ("PT", ln, sb)
            union(na, nb)
            for pid in pads_at_pt(n, ln, t["a"]):
                union(na, ("PAD", pid))
            for pid in pads_at_pt(n, ln, t["b"]):
                union(nb, ("PAD", pid))

        roots = {}
        out = []
        cid = 0
        for pid in pads:
            r = find(("PAD", pid))
            if r not in roots:
                cid += 1
                roots[r] = cid
            out.append(roots[r])
        return tuple(out)

    pruned_loops = 0
    peeled_post = 0
    for n, ntracks in list(tracks_by_net.items()):
        if not n or n in POWER_NETS:
            continue
        want = strict_pad_partition(n)
        if not want or len(set(want)) != 1:
            continue
        # Sort narrower and shorter non-weld segments first so parallel twin stems go before weld bridges
        for t in sorted(ntracks, key=lambda x: (1 if x.get("weld") else 0, round(x["w"], 3), math.dist(x["a"], x["b"]))):
            if not t["active"]:
                continue
            ln = t["ln"]
            if in_pad(n, ln, t["a"], tol=0.01) or in_pad(n, ln, t["b"], tol=0.01):
                continue
            if strict_pad_partition(n, skip_tid=t["id"]) == want:
                t["active"] = False
                pruned_loops += 1

        # Immediately peel any multi-hop dead-end tails exposed on net `n`
        while True:
            deg_n = collections.Counter()
            for t in ntracks:
                if t["active"]:
                    deg_n[(t["ln"], snap(t["a"]))] += 1
                    deg_n[(t["ln"], snap(t["b"]))] += 1
            did_n = 0
            for t in ntracks:
                if not t["active"]:
                    continue
                ln = t["ln"]
                if in_pad(n, ln, t["a"], tol=0.01) and in_pad(n, ln, t["b"], tol=0.01):
                    continue
                for pt in (t["a"], t["b"]):
                    if (
                        deg_n[(ln, snap(pt))] == 1
                        and not in_pad(n, ln, pt)
                        and not any(math.dist(pt, v["p"]) <= 0.004 for v in vias_by_net[n] if v["active"])
                        and not in_zone(n, ln, pt)
                    ):
                        if strict_pad_partition(n, skip_tid=t["id"]) == want:
                            t["active"] = False
                            deg_n[(ln, snap(t["a"]))] -= 1
                            deg_n[(ln, snap(t["b"]))] -= 1
                            peeled_post += 1
                            did_n += 1
                        break
            if not did_n:
                break

    # Prune any redundant signal vias left after cycle pruning, then re-center any mid-segment via grazes!
    pruned_vias = 0
    deg_all = collections.Counter()
    for t in tracks.values():
        if t["active"]:
            deg_all[(t["net"], t["ln"], snap(t["a"]))] += 1
            deg_all[(t["net"], t["ln"], snap(t["b"]))] += 1
    for n, nvias in vias_by_net.items():
        if not n or n in POWER_NETS:
            continue
        want = strict_pad_partition(n)
        if not want or len(set(want)) != 1:
            continue
        for v in nvias:
            if not v["active"]:
                continue
            svp = snap(v["p"])
            if any(deg_all[(n, ln, svp)] == 1 and not in_pad(n, ln, v["p"]) for ln in lay_ids):
                continue
            if strict_pad_partition(n, skip_vid=v["id"]) == want:
                v["active"] = False
                pruned_vias += 1

    print(f"Pass 4: pruned_loops={pruned_loops}, peeled_post={peeled_post}, pruned_vias={pruned_vias}")

    # ------------------------------------------------------------------
    # PASS 5: Resolve genuine acute V-notch slivers (3..45 deg where legs
    # separate into a sharp wedge, e.g. SW3_1 on In1.Cu) via 90-deg T-join,
    # re-attach any mid-segment via grazes, and bridge narrow morph kisses
    # ------------------------------------------------------------------
    is_clear = build_clearance_checker()
    by_nl = collections.defaultdict(list)
    for t in tracks.values():
        if t["active"]:
            by_nl[(t["net"], t["ln"])].append(t)

    # Re-ensure every active via that grazes a same-net track on (n, ln) has a centered vertex
    for (n, ln), segs in list(by_nl.items()):
        for v in vias_by_net[n]:
            if not v["active"]:
                continue
            vp, vr = v["p"], v["r"]
            if any(math.dist(vp, t["a"]) <= 0.005 or math.dist(vp, t["b"]) <= 0.005 for t in segs if t["active"]):
                continue
            if in_pad(n, ln, vp, tol=0.005) or in_zone(n, ln, vp):
                continue
            best_hit = None
            Pvp = Point(vp)
            for t in segs:
                if not t["active"] or math.dist(t["a"], t["b"]) < 0.001:
                    continue
                ls = LineString([t["a"], t["b"]])
                d = ls.distance(Pvp)
                if d <= vr + t["w"] / 2 + 0.002:
                    proj = ls.interpolate(ls.project(Pvp))
                    q = (proj.x, proj.y)
                    if best_hit is None or d < best_hit[0]:
                        best_hit = (d, t, q)
            if best_hit is not None:
                _, t, q = best_hit
                w = t["w"]
                via_disc = Point(vp).buffer(vr + 1e-4, 16)
                cand_ws = [w] if n in POWER_NETS or w <= 0.101 else [w, 0.10]
                for bw in cand_ws:
                    g_br = seg_poly(q, vp, bw)
                    if via_disc.contains(g_br) or is_clear(ln, g_br, n, {t["id"]}):
                        a0, b0 = t["a"], t["b"]
                        if math.dist(q, a0) > 0.003 and math.dist(q, b0) > 0.003:
                            t["b"] = q
                            nt_split = new_track(q, b0, w, ln, n, t["nc"])
                            if nt_split:
                                segs.append(nt_split)
                        nt_br = new_track(q, vp, bw, ln, n, t["nc"])
                        if nt_br:
                            segs.append(nt_br)
                        break

    morph_fixed = 0
    acute_fixed = 0
    pad_joint_fixed = 0

    # 5.0 Heal narrow off-pad lens joints (track ending just outside an SMD pad on 0.025 mm grid)
    for (n, ln), plist in list(pads_by_nl.items()):
        segs = [t for t in by_nl[(n, ln)] if t["active"]]
        if not segs:
            continue
        for ppos, poly, pid in plist:
            if in_zone(n, ln, ppos):
                continue
            if any(v["active"] and v["r"] - poly.distance(Point(v["p"])) >= 0.092 for v in vias_by_net[n]):
                continue
            sound = False
            cand_ends = []
            for t in segs:
                if not t["active"]:
                    continue
                w = t["w"]
                for end_pt in (t["a"], t["b"]):
                    d = poly.distance(Point(end_pt))
                    if d <= w / 4 - 0.003:
                        sound = True
                        break
                    if d < w / 2 + 0.015:
                        cand_ends.append((d, end_pt, t))
                if sound:
                    break
            if sound or not cand_ends:
                continue
            cand_ends.sort(key=lambda x: x[0])
            er_pad = poly.buffer(-0.045, 8)
            for _, end_pt, t in cand_ends:
                if er_pad.is_empty:
                    q_in = ppos
                else:
                    qp = nearest_points(er_pad, Point(end_pt))[0]
                    q_in = (qp.x, qp.y)
                bw = max(net_min_w(n), min(t["w"], 0.10) if n not in POWER_NETS else t["w"])
                if math.dist(end_pt, q_in) >= 0.002 and is_clear(ln, seg_poly(end_pt, q_in, bw), n, {t["id"]}):
                    nt = new_track(end_pt, q_in, bw, ln, n, t["nc"])
                    if nt:
                        by_nl[(n, ln)].append(nt)
                        segs.append(nt)
                        pad_joint_fixed += 1
                    break

    for (n, ln), segs in list(by_nl.items()):
        if n in POWER_NETS:
            continue
        # 5a-pre. Split any proper interior X-crossings between same-net tracks on (n, ln) so 5a sees all 4 rays at the crossing!
        act_x = [t for t in segs if t["active"] and math.dist(t["a"], t["b"]) > 0.05]
        for ix1 in range(len(act_x)):
            t1 = act_x[ix1]
            if not t1["active"]:
                continue
            ls1 = LineString([t1["a"], t1["b"]])
            for ix2 in range(ix1 + 1, len(act_x)):
                t2 = act_x[ix2]
                if not t2["active"]:
                    continue
                ls2 = LineString([t2["a"], t2["b"]])
                if not ls1.intersects(ls2):
                    continue
                inter = ls1.intersection(ls2)
                if inter.geom_type == "Point":
                    qx = (round(inter.x, 4), round(inter.y, 4))
                    if (
                        min(math.dist(qx, t1["a"]), math.dist(qx, t1["b"])) > 0.015
                        and min(math.dist(qx, t2["a"]), math.dist(qx, t2["b"])) > 0.015
                    ):
                        b1_old, b2_old = t1["b"], t2["b"]
                        t1["b"] = qx
                        t2["b"] = qx
                        nt1 = new_track(qx, b1_old, t1["w"], ln, n, t1["nc"])
                        nt2 = new_track(qx, b2_old, t2["w"], ln, n, t2["nc"])
                        for ntx in (nt1, nt2):
                            if ntx:
                                segs.append(ntx)
                        ls1 = LineString([t1["a"], t1["b"]])
        # 5a. Acute V-notch slivers (3..45 deg)
        adj = collections.defaultdict(list)
        for t in list(segs):
            if t["active"] and math.dist(t["a"], t["b"]) > 0.02:
                adj[snap(t["a"])].append((t, t["b"]))
                adj[snap(t["b"])].append((t, t["a"]))
        for vpt, nbrs in list(adj.items()):
            if len(nbrs) < 2 or in_pad(n, ln, vpt, tol=0.02):
                continue
            for i in range(len(nbrs)):
                for j in range(i + 1, len(nbrs)):
                    t1, b1 = nbrs[i]
                    t2, b2 = nbrs[j]
                    if not t1["active"] or not t2["active"] or t1 is t2:
                        continue
                    v1 = (b1[0] - vpt[0], b1[1] - vpt[1])
                    v2 = (b2[0] - vpt[0], b2[1] - vpt[1])
                    l1, l2 = math.hypot(*v1), math.hypot(*v2)
                    if l1 <= 0.02 or l2 <= 0.02:
                        continue
                    c = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)))
                    ang = math.degrees(math.acos(c))
                    if not (2.5 <= ang < 45.0):
                        continue
                    d_sep = ((t1["w"] + t2["w"]) / 4.0) / math.sin(math.radians(ang / 2.0))
                    if min(l1, l2) <= d_sep + 0.02:
                        continue

                    if l1 <= l2:
                        t_sh, b_sh, t_lg, b_lg_far = t1, b1, t2, b2
                    else:
                        t_sh, b_sh, t_lg, b_lg_far = t2, b2, t1, b1
                    ls_lg = LineString([t_lg["a"], t_lg["b"]])
                    proj = ls_lg.interpolate(ls_lg.project(Point(b_sh)))
                    q = (proj.x, proj.y)
                    w_sh = t_sh["w"]
                    if (
                        math.dist(q, b_sh) > 0.01
                        and is_clear(ln, seg_poly(b_sh, q, w_sh), n, {t_sh["id"], t_lg["id"]})
                    ):
                        # Check whether anything else still needs `vpt`!
                        other_at_vpt = any(
                            tx["active"] and tx is not t_sh and tx is not t_lg
                            and (snap(tx["a"]) == vpt or snap(tx["b"]) == vpt)
                            for tx in by_nl[(n, ln)]
                        )
                        vpt_anchored = (
                            other_at_vpt
                            or in_pad(n, ln, vpt, tol=0.005)
                            or in_zone(n, ln, vpt)
                            or any(math.dist(vpt, v["p"]) <= 0.004 for v in vias_by_net[n] if v["active"])
                        )
                        if not vpt_anchored:
                            # Pure hairpin V-turn: trim bypassed spike `vpt -> q` cleanly!
                            t_lg["a"] = q
                            t_lg["b"] = b_lg_far
                        else:
                            a_lg, b_lg, w_lg = t_lg["a"], t_lg["b"], t_lg["w"]
                            if math.dist(q, a_lg) > 0.003 and math.dist(q, b_lg) > 0.003:
                                t_lg["b"] = q
                                nt_sp = new_track(q, b_lg, w_lg, ln, n, t_lg["nc"])
                                if nt_sp:
                                    by_nl[(n, ln)].append(nt_sp)
                        t_sh["a"] = b_sh
                        t_sh["b"] = q
                        acute_fixed += 1
                    else:
                        # Fallback: local chamfer/web across the acute V-throat 0.22 mm from vpt
                        dc = min(0.22, min(l1, l2) * 0.45)
                        q1 = (vpt[0] + (v1[0] / l1) * dc, vpt[1] + (v1[1] / l1) * dc)
                        q2 = (vpt[0] + (v2[0] / l2) * dc, vpt[1] + (v2[1] / l2) * dc)
                        bw = max(net_min_w(n), min(t1["w"], t2["w"]))
                        if math.dist(q1, q2) > 0.015 and is_clear(ln, seg_poly(q1, q2, bw), n, {t1["id"], t2["id"]}):
                            other_at_vpt = any(
                                tx["active"] and tx is not t1 and tx is not t2
                                and (snap(tx["a"]) == vpt or snap(tx["b"]) == vpt)
                                for tx in by_nl[(n, ln)]
                            )
                            vpt_anchored = (
                                other_at_vpt
                                or in_pad(n, ln, vpt, tol=0.005)
                                or in_zone(n, ln, vpt)
                                or any(math.dist(vpt, v["p"]) <= 0.004 for v in vias_by_net[n] if v["active"])
                            )
                            if not vpt_anchored:
                                t1["a"], t1["b"] = q1, b1
                                t2["a"], t2["b"] = q2, b2
                            else:
                                # Even when vpt is a via/pad, bridging q1->q2 fills the V-notch sliver;
                                # split both legs at q1/q2 and widen stub vpt->mid(q1,q2) if clear so vpt has a single trunk!
                                mid_q = ((q1[0] + q2[0]) / 2.0, (q1[1] + q2[1]) / 2.0)
                                if is_clear(ln, seg_poly(vpt, mid_q, bw), n, {t1["id"], t2["id"]}) and is_clear(
                                    ln, seg_poly(q1, q2, bw), n, {t1["id"], t2["id"]}
                                ):
                                    t1["a"], t1["b"] = q1, b1
                                    t2["a"], t2["b"] = q2, b2
                                    for sa, sb in ((vpt, mid_q), (q1, mid_q), (mid_q, q2)):
                                        ns = new_track(sa, sb, bw, ln, n, t1["nc"])
                                        if ns:
                                            by_nl[(n, ln)].append(ns)
                                    acute_fixed += 1
                                    continue
                            ns = new_track(q1, q2, bw, ln, n, t1["nc"])
                            if ns:
                                by_nl[(n, ln)].append(ns)
                                acute_fixed += 1

        # 5b. Morphological copper necks (< 0.088 mm)
        act_segs = [t for t in by_nl[(n, ln)] if t["active"]]
        if not act_segs:
            continue
        geoms = [seg_poly(t["a"], t["b"], t["w"]) for t in act_segs]
        for v in vias_by_net[n]:
            if v["active"]:
                geoms.append(Point(v["p"]).buffer(v["r"], 12))
        for _, poly, _ in pads_by_nl[(n, ln)]:
            geoms.append(poly)
        u = unary_union(geoms)
        comps = list(u.geoms) if hasattr(u, "geoms") else [u]
        nc = act_segs[0]["nc"]
        for comp in comps:
            er = comp.buffer(-0.044, 8)
            if not er.is_empty and hasattr(er, "geoms") and len(er.geoms) > 1:
                pieces = list(er.geoms)
                for i in range(len(pieces)):
                    for j in range(i + 1, len(pieces)):
                        p1, p2 = nearest_points(pieces[i], pieces[j])
                        q1, q2 = (p1.x, p1.y), (p2.x, p2.y)
                        if math.dist(q1, q2) < 0.36:
                            # Anchor each end to via center if near a via, or keep `q` if already inside a pad!
                            def snap_anchor(qx):
                                if in_pad(n, ln, qx, tol=-0.02):
                                    return qx
                                near_vs = [v["p"] for v in vias_by_net[n] if v["active"] and math.dist(qx, v["p"]) <= v["r"] + 0.02]
                                if near_vs:
                                    return min(near_vs, key=lambda z: math.dist(z, qx))
                                pts_pool = [ppos for ppos, _, _ in pads_by_nl[(n, ln)]] + [t["a"] for t in act_segs] + [t["b"] for t in act_segs]
                                return min(pts_pool, key=lambda z: math.dist(z, qx)) if pts_pool else qx

                            a_br, b_br = snap_anchor(q1), snap_anchor(q2)
                            if math.dist(a_br, b_br) > 0.005:
                                for try_w in (max(net_min_w(n), 0.10),):
                                    if is_clear(ln, seg_poly(a_br, b_br, try_w), n):
                                        nt = new_track(a_br, b_br, try_w, ln, n, nc)
                                        if nt:
                                            by_nl[(n, ln)].append(nt)
                                            act_segs.append(nt)
                                            morph_fixed += 1
                                        break

    # 5c. Heal narrow (< 0.09 mm) Via <-> Pad corner kisses across ALL non-GND nets (including POWER_NETS like VSYS/+3V3/VBAT/VBUS)
    for (n, ln), plist in list(pads_by_nl.items()):
        if n == "GND" or not vias_by_net[n]:
            continue
        nc_Obj = b.FindNet(n)
        if not nc_Obj:
            continue
        nc_p = nc_Obj.GetNetCode()
        bw_p = max(net_min_w(n), 0.10)
        for v in vias_by_net[n]:
            if not v["active"]:
                continue
            vdisc = Point(v["p"]).buffer(v["r"], 12)
            for ppos, poly, _ in plist:
                if vdisc.distance(poly) <= 1e-4:
                    u_vp = unary_union([vdisc, poly] + [seg_poly(t["a"], t["b"], t["w"]) for t in by_nl[(n, ln)] if t["active"]])
                    er_vp = u_vp.buffer(-0.0445, 8)
                    if er_vp.is_empty or (hasattr(er_vp, "geoms") and len(er_vp.geoms) > 1):
                        if math.dist(v["p"], ppos) > 0.005 and is_clear(ln, seg_poly(v["p"], ppos, bw_p), n):
                            nt = new_track(v["p"], ppos, bw_p, ln, n, nc_p)
                            if nt:
                                by_nl[(n, ln)].append(nt)
                                morph_fixed += 1

    # 5d. Weld any narrow (< 0.090 mm) lateral graze between an active Via and a same-net Track (even when loop-linked via a pad!)
    for (n, ln), segs_vt in list(by_nl.items()):
        if n == "GND" or not vias_by_net[n]:
            continue
        bw_vt = max(net_min_w(n), 0.10)
        for v in vias_by_net[n]:
            if not v["active"]:
                continue
            vp, vr = v["p"], v["r"]
            for t in list(segs_vt):
                if not t["active"] or math.dist(vp, t["a"]) < 0.01 or math.dist(vp, t["b"]) < 0.01:
                    continue
                ls_t = LineString([t["a"], t["b"]])
                ov = (vr + t["w"] * 0.5) - ls_t.distance(Point(vp))
                if 0.0005 < ov < 0.091:
                    proj_pt = ls_t.interpolate(ls_t.project(Point(vp)))
                    qp = (round(proj_pt.x, 4), round(proj_pt.y, 4))
                    if math.dist(vp, qp) > 0.005 and is_clear(ln, seg_poly(vp, qp, bw_vt), n, {t["id"]}):
                        a0, b0, w0 = t["a"], t["b"], t["w"]
                        if math.dist(qp, a0) > 0.015 and math.dist(qp, b0) > 0.015:
                            t["b"] = qp
                            nt_sp = new_track(qp, b0, w0, ln, n, t["nc"])
                            if nt_sp:
                                by_nl[(n, ln)].append(nt_sp)
                        nt_br = new_track(vp, qp, bw_vt, ln, n, t["nc"])
                        if nt_br:
                            by_nl[(n, ln)].append(nt_br)
                            morph_fixed += 1
        # Also weld any remaining Track <-> Track narrow lateral overlap (< 0.090 mm) right outside a pad edge (e.g. CS2_9 at D89.4)!
        act_tt = [t for t in by_nl[(n, ln)] if t["active"] and math.dist(t["a"], t["b"]) > 0.02]
        for i_t in range(len(act_tt)):
            t1 = act_tt[i_t]
            if not t1["active"]:
                continue
            ls1 = LineString([t1["a"], t1["b"]])
            for j_t in range(i_t + 1, len(act_tt)):
                t2 = act_tt[j_t]
                if not t2["active"] or any(math.dist(p, q) <= 0.005 for p in (t1["a"], t1["b"]) for q in (t2["a"], t2["b"])):
                    continue
                ls2 = LineString([t2["a"], t2["b"]])
                ov_tt = (t1["w"] + t2["w"]) * 0.5 - ls1.distance(ls2)
                if 0.0005 < ov_tt < 0.091:
                    p1, p2 = nearest_points(ls1, ls2)
                    q1, q2 = (round(p1.x, 4), round(p1.y, 4)), (round(p2.x, 4), round(p2.y, 4))
                    if in_pad(n, ln, q1, tol=-0.02) and in_pad(n, ln, q2, tol=-0.02):
                        continue
                    if math.dist(q1, q2) > 0.004 and is_clear(ln, seg_poly(q1, q2, bw_vt), n, {t1["id"], t2["id"]}):
                        nt_tt = new_track(q1, q2, bw_vt, ln, n, t1["nc"])
                        if nt_tt:
                            by_nl[(n, ln)].append(nt_tt)
                            morph_fixed += 1
        # Also weld any Pad <-> Track narrow lateral corner graze (< 0.090 mm, e.g. CS2_9 grazing D89.4)!
        for ppos, poly, _ in pads_by_nl[(n, ln)]:
            pad_inner = poly.buffer(-min(bw_vt * 0.45, 0.04))
            if pad_inner.is_empty:
                pad_inner = Point(ppos)
            for t in list(by_nl[(n, ln)]):
                if not t["active"] or math.dist(t["a"], t["b"]) <= 0.02:
                    continue
                if poly.buffer(-0.005).contains(Point(t["a"])) or poly.buffer(-0.005).contains(Point(t["b"])):
                    continue
                ls_t = LineString([t["a"], t["b"]])
                ov_pt = t["w"] * 0.5 - poly.distance(ls_t)
                if 0.0005 < ov_pt < 0.091:
                    pt_on_t, pt_on_pad = nearest_points(ls_t, pad_inner)
                    qt = (round(pt_on_t.x, 4), round(pt_on_t.y, 4))
                    qp = (round(pt_on_pad.x, 4), round(pt_on_pad.y, 4))
                    if math.dist(qt, qp) > 0.004 and is_clear(ln, seg_poly(qt, qp, bw_vt), n, {t["id"]}):
                        a0, b0, w0 = t["a"], t["b"], t["w"]
                        if math.dist(qt, a0) > 0.015 and math.dist(qt, b0) > 0.015:
                            t["b"] = qt
                            nt_sp = new_track(qt, b0, w0, ln, n, t["nc"])
                            if nt_sp:
                                by_nl[(n, ln)].append(nt_sp)
                        nt_pt = new_track(qt, qp, bw_vt, ln, n, t["nc"])
                        if nt_pt:
                            by_nl[(n, ln)].append(nt_pt)
                            morph_fixed += 1

    # ------------------------------------------------------------------
    # PASS 6: Coalesce collinear overlaps & merge degree-2 collinear runs
    # ------------------------------------------------------------------
    dup_merged_2 = coalesce_collinear()
    merged_collinear = 0
    active_via_pts = {(v["net"], snap(v["p"])) for v in vias.values() if v["active"]}
    for _ in range(5):
        adj = collections.defaultdict(list)
        for t in tracks.values():
            if t["active"]:
                adj[(t["net"], t["ln"], snap(t["a"]))].append((t, t["b"]))
                adj[(t["net"], t["ln"], snap(t["b"]))].append((t, t["a"]))
        did = 0
        used = set()
        for (n, ln, vpt), inc in adj.items():
            if len(inc) != 2 or (n, vpt) in active_via_pts:
                continue
            (t1, p1), (t2, p2) = inc
            if t1["id"] in used or t2["id"] in used or t1 is t2:
                continue
            if abs(t1["w"] - t2["w"]) > 1e-4 or math.dist(p1, p2) < 0.002:
                continue
            ls = LineString([p1, p2])
            if ls.distance(Point(vpt)) < 0.0005 and 0.01 < ls.project(Point(vpt), normalized=True) < 0.99:
                t1["a"] = p1
                t1["b"] = p2
                t2["active"] = False
                used.add(t1["id"])
                used.add(t2["id"])
                merged_collinear += 1
                did += 1
        if not did:
            break

    print(
        f"Pass 5-6: pad_joint_fixed={pad_joint_fixed}, acute_fixed={acute_fixed}, morph_fixed={morph_fixed}, "
        f"dup_collinear2={dup_merged_2}, merged_collinear={merged_collinear}"
    )

    # 6b. Drop any dangling via connected to copper on <= 1 layer (e.g. VREG_LX island vias or vias inside plane cutouts)
    dangling_vias_dropped = 0
    trks_by_nl_final = collections.defaultdict(list)
    for t in tracks.values():
        if t["active"]:
            trks_by_nl_final[(t["net"], t["ln"])].append(t)
    for v in vias.values():
        if not v["active"]:
            continue
        vn = v["net"]
        vp, vr = v["p"], v["r"]
        vdisc = Point(vp).buffer(vr + 0.002, 12)
        conn_layers = 0
        for ln in lay_ids:
            has_l = False
            if any(poly.intersects(vdisc) for _, poly, _ in pads_by_nl[(vn, ln)]):
                has_l = True
            elif any(zp.intersects(vdisc) for zp in zone_polys_nl[(vn, ln)]):
                has_l = True
            elif any(seg_poly(t["a"], t["b"], t["w"]).intersects(vdisc) for t in trks_by_nl_final[(vn, ln)]):
                has_l = True
            if has_l:
                conn_layers += 1
        if conn_layers <= 1:
            v["active"] = False
            dangling_vias_dropped += 1
    if dangling_vias_dropped:
        print(f"Pass 6b: dropped_1layer_dangling_vias={dangling_vias_dropped}")

    # 6c. Final peel of any tiny leftover stubs strictly inside via discs or left exposed after Pass 5-6
    final_stub_peeled = 0
    for _ in range(5):
        deg_f = collections.Counter()
        for t in tracks.values():
            if t["active"]:
                deg_f[(t["net"], t["ln"], snap(t["a"]))] += 1
                deg_f[(t["net"], t["ln"], snap(t["b"]))] += 1
        did_f = 0
        for t in tracks.values():
            if not t["active"]:
                continue
            n, ln = t["net"], t["ln"]
            if in_pad(n, ln, t["a"], tol=0.005) and in_pad(n, ln, t["b"], tol=0.005):
                continue
            # If both endpoints lie inside the same active via disc and at least one endpoint is degree-1 off-center, drop it!
            if any(
                v["active"]
                and math.dist(t["a"], v["p"]) <= v["r"] + 0.002
                and math.dist(t["b"], v["p"]) <= v["r"] + 0.002
                and (
                    (deg_f[(n, ln, snap(t["a"]))] == 1 and math.dist(t["a"], v["p"]) > 0.004)
                    or (deg_f[(n, ln, snap(t["b"]))] == 1 and math.dist(t["b"], v["p"]) > 0.004)
                )
                for v in vias_by_net[n]
            ):
                t["active"] = False
                final_stub_peeled += 1
                did_f += 1
                continue
            # Also peel any open-air degree-1 tail left behind when Pass 6b dropped a 1-layer dangling via!
            for pt in (t["a"], t["b"]):
                if (
                    deg_f[(n, ln, snap(pt))] == 1
                    and not in_pad(n, ln, pt, tol=0.02)
                    and not in_zone(n, ln, pt)
                    and not any(v["active"] and math.dist(pt, v["p"]) <= v["r"] + 0.01 for v in vias_by_net[n])
                    and not any(
                        t2["active"] and t2["id"] != t["id"] and LineString([t2["a"], t2["b"]]).distance(Point(pt)) <= (t["w"] + t2["w"]) * 0.5 + 0.01
                        for t2 in by_nl[(n, ln)]
                    )
                ):
                    t["active"] = False
                    deg_f[(n, ln, snap(t["a"]))] -= 1
                    deg_f[(n, ln, snap(t["b"]))] -= 1
                    final_stub_peeled += 1
                    did_f += 1
                    break
        if not did_f:
            break
    if final_stub_peeled:
        print(f"Pass 6c: final_via_disc_stubs_peeled={final_stub_peeled}")

    # 6d. Snap/bridge any endpoint whose degree dropped to 1 during Pass 4-6c near an active via center!
    deg_last = collections.Counter()
    for t in tracks.values():
        if t["active"]:
            deg_last[(t["net"], t["ln"], snap(t["a"]))] += 1
            deg_last[(t["net"], t["ln"], snap(t["b"]))] += 1
    late_via_snapped = 0
    for t in list(tracks.values()):
        if not t["active"]:
            continue
        n, ln, w = t["net"], t["ln"], t["w"]
        for ek, fk in (("a", "b"), ("b", "a")):
            pt, far = t[ek], t[fk]
            if deg_last[(n, ln, snap(pt))] != 1 or in_pad(n, ln, pt, tol=0.003) or in_zone(n, ln, pt):
                continue
            if any(v["active"] and math.dist(pt, v["p"]) <= 0.003 for v in vias_by_net[n]):
                continue
            near_vs = [
                (math.dist(pt, v["p"]), v["p"], v["r"])
                for v in vias_by_net[n]
                if v["active"] and math.dist(pt, v["p"]) <= v["r"] + w / 2 + 0.01
            ]
            if not near_vs:
                continue
            near_vs.sort()
            _, vp, vr = near_vs[0]
            if not in_pad(n, ln, far, tol=w / 2 + 0.02) and math.dist(far, vp) > 0.002 and is_clear(ln, seg_poly(far, vp, w), n, {t["id"]}):
                deg_last[(n, ln, snap(pt))] -= 1
                t[ek] = vp
                deg_last[(n, ln, snap(vp))] += 1
                late_via_snapped += 1
            else:
                bw_v = min(w, 0.10) if n not in POWER_NETS else w
                g_br = seg_poly(pt, vp, bw_v)
                if Point(vp).buffer(vr + 1e-4, 16).contains(g_br) or is_clear(ln, g_br, n, {t["id"]}):
                    nt_v = new_track(pt, vp, bw_v, ln, n, t["nc"])
                    if nt_v:
                        deg_last[(n, ln, snap(pt))] += 1
                        deg_last[(n, ln, snap(vp))] += 1
                        late_via_snapped += 1
    if late_via_snapped:
        print(f"Pass 6d: late_via_snapped={late_via_snapped}")

    # 6e. Collapse any post-5b acute (<45 deg) twin rays from a shared vertex into the SAME SMD pad,
    #     and snap any degree-1 endpoint sitting on the boundary of a round pad (e.g. TP1) inside the pad!
    deg_6e = collections.Counter()
    adj_6e = collections.defaultdict(list)
    for t in tracks.values():
        if t["active"]:
            deg_6e[(t["net"], t["ln"], snap(t["a"]))] += 1
            deg_6e[(t["net"], t["ln"], snap(t["b"]))] += 1
            if math.dist(t["a"], t["b"]) > 0.02:
                adj_6e[(t["net"], t["ln"], snap(t["a"]))].append((t, "a", "b"))
                adj_6e[(t["net"], t["ln"], snap(t["b"]))].append((t, "b", "a"))

    pad_edge_snapped = 0
    for t in list(tracks.values()):
        if not t["active"]:
            continue
        n, ln, w = t["net"], t["ln"], t["w"]
        for ek in ("a", "b"):
            pt = t[ek]
            if deg_6e[(n, ln, snap(pt))] != 1:
                continue
            if any(poly.buffer(-min(w * 0.45, 0.042)).contains(Point(pt)) for _, poly, _ in pads_by_nl[(n, ln)]):
                continue
            for ppos, poly, _ in pads_by_nl[(n, ln)]:
                if poly.distance(Point(pt)) <= w * 0.5 + 0.015:
                    pad_in = poly.buffer(-min(w * 0.48, 0.045))
                    cands = [ppos]
                    if not pad_in.is_empty:
                        _, pin_pt = nearest_points(Point(pt), pad_in)
                        cands.insert(0, (round(pin_pt.x, 4), round(pin_pt.y, 4)))
                    snapped_ok = False
                    for tgt in cands:
                        if math.dist(pt, tgt) > 0.003 and is_clear(ln, seg_poly(pt, tgt, w), n, {t["id"]}):
                            nt_pe = new_track(pt, tgt, w, ln, n, t["nc"])
                            if nt_pe:
                                deg_6e[(n, ln, snap(pt))] += 1
                                deg_6e[(n, ln, snap(tgt))] += 1
                                pad_edge_snapped += 1
                                snapped_ok = True
                                break
                    if snapped_ok:
                        break

    twin_pad_collapsed = 0
    for (n, ln, vpt), nbrs in list(adj_6e.items()):
        if len(nbrs) < 2 or any(poly.buffer(0.02).contains(Point(vpt)) for _, poly, _ in pads_by_nl[(n, ln)]):
            continue
        for i in range(len(nbrs)):
            t1, k1_v, k1_f = nbrs[i]
            if not t1["active"]:
                continue
            b1 = t1[k1_f]
            for j in range(i + 1, len(nbrs)):
                t2, k2_v, k2_f = nbrs[j]
                if not t2["active"] or t1 is t2:
                    continue
                b2 = t2[k2_f]
                v1 = (b1[0] - vpt[0], b1[1] - vpt[1])
                v2 = (b2[0] - vpt[0], b2[1] - vpt[1])
                l1, l2 = math.hypot(*v1), math.hypot(*v2)
                if l1 <= 0.02 or l2 <= 0.02:
                    continue
                ang = math.degrees(math.acos(max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)))))
                if 2.0 <= ang < 45.0:
                    for ppos, poly, _ in pads_by_nl[(n, ln)]:
                        pbuf = poly.buffer(0.02)
                        if pbuf.contains(Point(b1)) and pbuf.contains(Point(b2)):
                            # Route second leg from b1 -> b2 inside the pad so vpt has a single clean stem!
                            bw_c = max(net_min_w(n), min(t1["w"], t2["w"]))
                            if math.dist(b1, b2) > 0.005 and is_clear(ln, seg_poly(b1, b2, bw_c), n, {t1["id"], t2["id"]}):
                                t2[k2_v] = b1
                                twin_pad_collapsed += 1
                            break
    if pad_edge_snapped or twin_pad_collapsed:
        print(f"Pass 6e: pad_edge_snapped={pad_edge_snapped}, twin_pad_collapsed={twin_pad_collapsed}")

    # 6f. Final coalesce, late T-junction split, <2.0-deg fork resolution, and cap-gap / off-via cleanup!
    dup_final = coalesce_collinear()
    late_tjunc = 0
    collinear_fork_fixed = 0
    nub_peeled = 0
    cap_bridged = 0

    # Step 6f-1: Split any segment whose interior contains a degree-1 endpoint from Pass 5d/6e (e.g. CS1_9)
    by_nl_6f = collections.defaultdict(list)
    deg_fin = collections.Counter()
    for t in tracks.values():
        if t["active"]:
            by_nl_6f[(t["net"], t["ln"])].append(t)
            deg_fin[(t["net"], t["ln"], snap(t["a"]))] += 1
            deg_fin[(t["net"], t["ln"], snap(t["b"]))] += 1
    for (n, ln), segs in list(by_nl_6f.items()):
        pts_d1 = {
            pt
            for t in segs if t["active"]
            for pt in (snap(t["a"]), snap(t["b"]))
            if deg_fin[(n, ln, pt)] == 1
        }
        for pt in pts_d1:
            gpt = Point(pt)
            for t2 in list(segs):
                if not t2["active"]:
                    continue
                s2, e2 = snap(t2["a"]), snap(t2["b"])
                if pt == s2 or pt == e2 or math.dist(s2, e2) < 0.01:
                    continue
                ls2 = LineString([t2["a"], t2["b"]])
                if ls2.distance(gpt) <= 0.004 and 0.003 < math.dist(pt, t2["a"]) and 0.003 < math.dist(pt, t2["b"]):
                    old_b = t2["b"]
                    t2["b"] = pt
                    nt_s = new_track(pt, old_b, t2["w"], ln, n, t2["nc"])
                    if nt_s:
                        segs.append(nt_s)
                        late_tjunc += 1
                    break

    # Step 6f-2: Resolve any <2.0-deg collinear forks at a shared vertex (copper_audit COLLINEAR_DUP check)
    for _ in range(5):
        adj_cf = collections.defaultdict(list)
        v_graph = collections.defaultdict(list)
        for t in tracks.values():
            if t["active"] and t["net"] not in POWER_NETS:
                sa, sb = snap(t["a"]), snap(t["b"])
                v_graph[(t["net"], t["ln"], sa)].append((sb, t["id"]))
                v_graph[(t["net"], t["ln"], sb)].append((sa, t["id"]))
                if math.dist(sa, sb) > 0.02:
                    adj_cf[(t["net"], t["ln"], sa)].append((t, "a", "b"))
                    adj_cf[(t["net"], t["ln"], sb)].append((t, "b", "a"))
        did_cf = 0
        for (n, ln, vpt), nbrs in list(adj_cf.items()):
            if len(nbrs) < 2:
                continue
            resolved_here = False
            for i in range(len(nbrs)):
                if resolved_here:
                    break
                t1, k1_v, k1_f = nbrs[i]
                if not t1["active"]:
                    continue
                b1 = snap(t1[k1_f])
                for j in range(i + 1, len(nbrs)):
                    t2, k2_v, k2_f = nbrs[j]
                    if not t2["active"] or t1 is t2:
                        continue
                    b2 = snap(t2[k2_f])
                    v1 = (b1[0] - vpt[0], b1[1] - vpt[1])
                    v2 = (b2[0] - vpt[0], b2[1] - vpt[1])
                    l1, l2 = math.hypot(*v1), math.hypot(*v2)
                    if l1 <= 0.02 or l2 <= 0.02:
                        continue
                    ang = math.degrees(math.acos(max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)))))
                    if ang < 2.0:
                        # Order so t_short <= t_long
                        if l1 <= l2:
                            ts, ks_v, ks_f, bs, tl, kl_v, kl_f, bl = t1, k1_v, k1_f, b1, t2, k2_v, k2_f, b2
                        else:
                            ts, ks_v, ks_f, bs, tl, kl_v, kl_f, bl = t2, k2_v, k2_f, b2, t1, k1_v, k1_f, b1
                        # Check if vpt can still reach bs in v_graph without ts (cycle edge in micro-web!)
                        q_bfs = collections.deque([vpt])
                        seen_bfs = {vpt}
                        alt_path = False
                        while q_bfs:
                            cur = q_bfs.popleft()
                            if cur == bs:
                                alt_path = True
                                break
                            for nxt, eid in v_graph[(n, ln, cur)]:
                                if eid != ts["id"] and tracks[eid]["active"] and nxt not in seen_bfs:
                                    seen_bfs.add(nxt)
                                    q_bfs.append(nxt)
                        if alt_path:
                            ts["active"] = False
                            collinear_fork_fixed += 1
                            did_cf += 1
                            resolved_here = True
                            break
                        elif math.dist(bs, bl) > 0.004 and is_clear(ln, seg_poly(bs, bl, tl["w"]), n, {ts["id"], tl["id"]}):
                            tl[kl_v] = bs
                            collinear_fork_fixed += 1
                            did_cf += 1
                            resolved_here = True
                            break
                        # Or if bs is an off-center via endpoint while bl already reaches that same via center!
                        elif (
                            len(v_graph[(n, ln, bs)]) == 1
                            and not in_pad(n, ln, bs, tol=0.003)
                            and any(
                                v["active"] and math.dist(bs, v["p"]) <= v["r"] + ts["w"] / 2 + 0.005 and math.dist(bl, v["p"]) <= 0.004
                                for v in vias_by_net[n]
                            )
                        ):
                            ts["active"] = False
                            collinear_fork_fixed += 1
                            did_cf += 1
                            resolved_here = True
                            break
        if not did_cf:
            break

    dup_final += coalesce_collinear()

    # Step 6f-3: Final peel or snap/bridge of any remaining degree-1 endpoint outside pads/via-centers/zones!
    for _ in range(4):
        deg_fin = collections.Counter()
        by_nl_last = collections.defaultdict(list)
        for t in tracks.values():
            if t["active"]:
                sa, sb = snap(t["a"]), snap(t["b"])
                deg_fin[(t["net"], t["ln"], sa)] += 1
                deg_fin[(t["net"], t["ln"], sb)] += 1
                by_nl_last[(t["net"], t["ln"])].append(t)
        did_end = 0
        for t in list(tracks.values()):
            if not t["active"]:
                continue
            n, ln, w = t["net"], t["ln"], t["w"]
            for ek, fk in (("a", "b"), ("b", "a")):
                pt = snap(t[ek])
                far = snap(t[fk])
                if deg_fin[(n, ln, pt)] != 1:
                    continue
                if in_pad(n, ln, pt, tol=0.003) or in_zone(n, ln, pt):
                    continue
                if any(v["active"] and math.dist(pt, v["p"]) <= 0.003 for v in vias_by_net[n]):
                    continue
                # Case 1: Redundant stub tail attached to an interior vertex (deg[far] >= 2) touching another segment on (n, ln)
                if deg_fin[(n, ln, far)] >= 2 and math.dist(pt, far) < 0.12 and any(
                    t2["active"] and t2["id"] != t["id"] and snap(t2["a"]) != far and snap(t2["b"]) != far
                    and LineString([t2["a"], t2["b"]]).distance(Point(pt)) <= (w + t2["w"]) * 0.5 + 0.005
                    for t2 in by_nl_last[(n, ln)]
                ):
                    # Bridge far -> projection on t2 if needed, or peel t if far is already connected to t2 within 2 hops
                    t["active"] = False
                    deg_fin[(n, ln, pt)] -= 1
                    deg_fin[(n, ln, far)] -= 1
                    nub_peeled += 1
                    did_end += 1
                    break
                # Case 2: Off-center via endpoint -> bridge or snap to via center
                near_v = [
                    (math.dist(pt, v["p"]), v["p"], v["r"])
                    for v in vias_by_net[n]
                    if v["active"] and math.dist(pt, v["p"]) <= v["r"] + w / 2 + 0.006
                ]
                if near_v:
                    near_v.sort()
                    _, vp, vr = near_v[0]
                    bw_v = min(w, 0.10) if n not in POWER_NETS else w
                    if Point(vp).buffer(vr + 1e-4, 16).contains(seg_poly(pt, vp, bw_v)) or is_clear(ln, seg_poly(pt, vp, bw_v), n, {t["id"]}):
                        nt_v = new_track(pt, vp, bw_v, ln, n, t["nc"])
                        if nt_v:
                            cap_bridged += 1
                            did_end += 1
                            break
                # Case 3: Cap-to-cap gap (< w + 0.006 mm to another active endpoint on (n, ln), e.g. +1V1/+3V3/VSYS near zone edge)
                cand_pts = []
                for t2 in by_nl_last[(n, ln)]:
                    if not t2["active"] or t2["id"] == t["id"]:
                        continue
                    for q in (snap(t2["a"]), snap(t2["b"])):
                        if q != pt and q != far and 0.002 < math.dist(pt, q) < w + 0.006:
                            cand_pts.append((math.dist(pt, q), q, t2["id"]))
                if cand_pts:
                    cand_pts.sort()
                    _, qbest, tid2 = cand_pts[0]
                    if is_clear(ln, seg_poly(pt, qbest, w), n, {t["id"], tid2}):
                        nt_cg = new_track(pt, qbest, w, ln, n, t["nc"])
                        if nt_cg:
                            cap_bridged += 1
                            did_end += 1
                            break
                # Case 4: Endpoint just outside a refilled zone edge -> extend slightly into zone interior!
                for zp in zone_polys_nl[(n, ln)]:
                    z_in = zp.buffer(-0.02)
                    if not z_in.is_empty and zp.distance(Point(pt)) < w + 0.02:
                        _, p_z = nearest_points(Point(pt), z_in)
                        qz = (round(p_z.x, 4), round(p_z.y, 4))
                        if math.dist(pt, qz) > 0.003 and is_clear(ln, seg_poly(pt, qz, w), n, {t["id"]}):
                            nt_z = new_track(pt, qz, w, ln, n, t["nc"])
                            if nt_z:
                                cap_bridged += 1
                                did_end += 1
                                break
        if not did_end:
            break

    if dup_final or late_tjunc or collinear_fork_fixed or nub_peeled or cap_bridged:
        print(
            f"Pass 6f: dup_final={dup_final}, late_tjunc={late_tjunc}, "
            f"collinear_fork_fixed={collinear_fork_fixed}, nub_peeled={nub_peeled}, cap_bridged={cap_bridged}"
        )

    # ------------------------------------------------------------------
    # Apply all mutations cleanly to pcbnew.BOARD in ONE single pass!
    # ------------------------------------------------------------------
    del_tracks = 0
    mod_tracks = 0
    add_tracks = 0
    del_vias = 0

    for v in vias.values():
        if not v["active"] and v["obj"] is not None:
            KEEP_ALIVE.append(v["obj"])
            b.Remove(v["obj"])
            del_vias += 1

    for t in tracks.values():
        if not t["active"]:
            if t["obj"] is not None:
                KEEP_ALIVE.append(t["obj"])
                b.Remove(t["obj"])
                del_tracks += 1
        elif t["obj"] is not None:
            if t["a"] != t["orig_a"] or t["b"] != t["orig_b"]:
                t["obj"].SetStart(V(t["a"]))
                t["obj"].SetEnd(V(t["b"]))
                mod_tracks += 1
        else:
            nt = pcbnew.PCB_TRACK(b)
            nt.SetStart(V(t["a"]))
            nt.SetEnd(V(t["b"]))
            nt.SetWidth(fm(t["w"]))
            nt.SetLayer(lay_ids[t["ln"]])
            nt.SetNetCode(t["nc"])
            b.Add(nt)
            KEEP_ALIVE.append(nt)
            add_tracks += 1

    print(f"Applied to board: del_tracks={del_tracks}, mod_tracks={mod_tracks}, add_tracks={add_tracks}, del_vias={del_vias}")

    for z in b.Zones():
        if not z.GetIsRuleArea() and z.GetZoneName() in ("plane GND", "RP2350 band"):
            z.SetMinThickness(fm(0.12))
            if z.GetZoneName() == "plane GND":
                z.SetLocalClearance(fm(0.15))
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.BuildConnectivity()
    final_open = b.GetConnectivity().GetUnconnectedCount(False)

    pro_path = Path(out).with_suffix(".kicad_pro")
    pro_bak = pro_path.read_bytes() if pro_path.exists() else None
    pcbnew.SaveBoard(out, b)
    if pro_bak is not None:
        pro_path.write_bytes(pro_bak)

    n_final_trk = sum(1 for x in b.GetTracks() if not isinstance(x, pcbnew.PCB_VIA))
    n_final_via = sum(1 for x in b.GetTracks() if isinstance(x, pcbnew.PCB_VIA))
    print(f"Saved {out}: tracks={n_final_trk}, vias={n_final_via}, open={final_open}")
    sys.stdout.flush()
    os._exit(0 if final_open <= base_open else 1)


if __name__ == "__main__":
    main()
