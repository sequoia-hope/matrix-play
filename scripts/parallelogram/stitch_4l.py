#!/usr/bin/env python3
"""stitch_4l.py -- Exact 3-signal-layer (F.Cu, In2.Cu, B.Cu) 25 um octilinear PathFinder stitcher for 4L Parallelogram.

Respects all KiCad netclass clearances, hole-to-copper / hole-to-hole clearances, NPTH annular-ring
clearances, Edge.Cuts polygon, solid exposed pads (U1/U2/U3/U5), vendor B.Cu copper areas, and custom
.kicad_dru rule areas ('U3 ring vias', 'U3 ring', 'reg corner', 'L1 window').
"""
from __future__ import annotations

import collections
import heapq
import itertools
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pcbnew
import shapely
from scipy.ndimage import binary_dilation, binary_erosion, distance_transform_edt, label as nd_label
from shapely.geometry import LineString, MultiPoint, Point, Polygon
from shapely.ops import nearest_points, unary_union
from shapely.strtree import STRtree

KEEP_ALIVE = []  # prevent pcbnew SWIG GC corruption on b.Remove(item)

OX = OY = 100.0
LAY = ["F.Cu", "In2.Cu", "B.Cu"]
NLAY = len(LAY)
LIDX = {L: i for i, L in enumerate(LAY)}

TW = 0.050   # 0.10 mm track half-width (satisfies 0.10 mm SW* and CS* rules)
VR = 0.150   # 0.30 mm via copper radius (4L JLC04161H-7628)
HR = 0.075   # 0.15 mm via drill radius
HC = 0.200   # hole-to-copper / hole-to-hole clearance
CL = 0.100   # 4L signal copper-to-copper clearance
M = 0.008    # safety margin above DRC threshold

# Soft-congestion stamp radii (in mm) between negotiated 0.10 mm / 0.30-0.15 via paths
R_TT = 2 * TW + CL + M                      # 0.208 mm track-to-track center spacing
R_TV = TW + max(VR + CL, HR + HC) + M       # 0.333 mm track-center to via-center spacing
R_VV = max(2 * VR + CL, HR + HC + VR, 2 * HR + HC) + M  # 0.433 mm via-center to via-center spacing

DIRS = [
    (1, 0, 1.0),
    (-1, 0, 1.0),
    (0, 1, 1.0),
    (0, -1, 1.0),
    (1, 1, 1.41421356),
    (1, -1, 1.41421356),
    (-1, 1, 1.41421356),
    (-1, -1, 1.41421356),
]

NEVER_RIP_SUBSTR = (
    "GND", "VSYS", "+3V3", "+1V1", "VBAT", "BAT_N", "VBUS",
    "XIN", "XOUT", "C24-Pad1", "USB_D", "CC1", "CC2", "QSPI", "VREG_",
)


def can_rip_net(net: str) -> bool:
    if not net:
        return False
    return not any(k in net for k in NEVER_RIP_SUBSTR)


def net_clr(net: str) -> float:
    if any(k in net for k in ("XIN", "XOUT", "C24-Pad1", "USB_D")):
        return 0.150
    if "VREG_LX" in net:
        return 0.120
    return CL


def get_board_poly(b) -> Polygon:
    um = pcbnew.ToMM
    ps = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(ps)
    o = ps.Outline(0)
    pts = [(um(o.CPoint(i).x) - OX, um(o.CPoint(i).y) - OY) for i in range(o.PointCount())]
    poly = Polygon(pts)
    return poly if poly.is_valid else poly.buffer(0)


def make_disk_offsets(radius_mm: float, grid: float) -> tuple[np.ndarray, np.ndarray]:
    r_cells = int(math.ceil(radius_mm / grid))
    di, dj = np.meshgrid(np.arange(-r_cells, r_cells + 1), np.arange(-r_cells, r_cells + 1), indexing="ij")
    mask = np.hypot(di * grid, dj * grid) < radius_mm
    return di[mask].astype(np.int32), dj[mask].astype(np.int32)


def stamp_cells(arr: np.ndarray, cells: list[tuple[int, int]], off_i: np.ndarray, off_j: np.ndarray, delta: int):
    if not cells:
        return
    nx, ny = arr.shape
    ci = np.array([c[0] for c in cells], dtype=np.int32)[:, None] + off_i[None, :]
    cj = np.array([c[1] for c in cells], dtype=np.int32)[:, None] + off_j[None, :]
    valid = (ci >= 0) & (ci < nx) & (cj >= 0) & (cj < ny)
    lin = np.unique(ci[valid] * ny + cj[valid])
    arr.ravel()[lin] += delta


def collinear_simplify(path: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if len(path) <= 2:
        return list(path)
    out = [path[0]]
    for k in range(1, len(path) - 1):
        dx1, dy1 = path[k][0] - path[k - 1][0], path[k][1] - path[k - 1][1]
        dx2, dy2 = path[k + 1][0] - path[k][0], path[k + 1][1] - path[k][1]
        if (dx1, dy1) != (dx2, dy2):
            out.append(path[k])
    out.append(path[-1])
    return out


def snap_90_45(x0: float, y0: float, x1: float, y1: float) -> list[tuple[float, float]]:
    dx, dy = x1 - x0, y1 - y0
    if abs(dx) < 1e-6 and abs(dy) < 1e-6:
        return [(x1, y1)]
    if abs(dx) < 1e-6 or abs(dy) < 1e-6 or abs(abs(dx) - abs(dy)) < 1e-6:
        return [(x0, y0), (x1, y1)]
    if abs(dx) > abs(dy):
        xm = x0 + math.copysign(abs(dy), dx)
        return [(x0, y0), (xm, y1), (x1, y1)]
    ym = y0 + math.copysign(abs(dx), dy)
    return [(x0, y0), (x1, ym), (x1, y1)]


def pad_poly(p, lid: int, um) -> Polygon:
    ps = p.GetEffectivePolygon(lid)
    if ps.OutlineCount() > 0:
        o = ps.Outline(0)
        pts = [(um(o.CPoint(i).x) - OX, um(o.CPoint(i).y) - OY) for i in range(o.PointCount())]
        if len(pts) >= 3:
            g = Polygon(pts)
            return g if g.is_valid else g.buffer(0)
    c = p.GetPosition()
    x, y = um(c.x) - OX, um(c.y) - OY
    w, h = um(p.GetSizeX()) / 2, um(p.GetSizeY()) / 2
    t = math.radians(-p.GetOrientationDegrees())
    cs, sn = math.cos(t), math.sin(t)
    return Polygon([(x + cs * u - sn * v, y + sn * u + cs * v) for u, v in ((-w, -h), (w, -h), (w, h), (-w, h))])


def get_net_islands(b, netname: str):
    """STRtree-accelerated connected-component islands of `netname`, sorted smallest first."""
    um = pcbnew.ToMM
    ids = {b.GetLayerName(l): l for l in range(64) if b.GetLayerName(l).endswith(".Cu")}
    own_items = []
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() != netname:
                continue
            ls = [L for L in LAY if p.IsOnLayer(ids[L])]
            if not ls:
                continue
            g = pad_poly(p, ids[ls[0]], um)
            c = p.GetPosition()
            own_items.append(("pad", g, set(ls), (um(c.x) - OX, um(c.y) - OY), p))
    for t in b.GetTracks():
        if t.GetNetname() != netname:
            continue
        if isinstance(t, pcbnew.PCB_VIA):
            c = t.GetPosition()
            vx, vy = um(c.x) - OX, um(c.y) - OY
            g = Point(vx, vy).buffer(um(t.GetWidth(ids["F.Cu"])) / 2, 12)
            own_items.append(("via", g, set(LAY), (vx, vy), t))
        else:
            L = t.GetLayerName()
            if L not in LIDX:
                continue
            s, e = t.GetStart(), t.GetEnd()
            sx, sy, ex, ey = um(s.x) - OX, um(s.y) - OY, um(e.x) - OX, um(e.y) - OY
            g = LineString([(sx, sy), (ex, ey)]).buffer(um(t.GetWidth()) / 2, 6)
            own_items.append(("trk", g, {L}, ((sx + ex) / 2, (sy + ey) / 2), t))

    n = len(own_items)
    if n == 0:
        return [], []
    par = list(range(n))

    def fd(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i

    geoms = [it[1] for it in own_items]
    tree = STRtree(geoms)
    pairs = tree.query(geoms, predicate="dwithin", distance=1e-4)
    for i, j in zip(pairs[0], pairs[1]):
        if i < j and (own_items[i][2] & own_items[j][2]):
            par[fd(int(i))] = fd(int(j))

    groups = collections.defaultdict(list)
    for i, it in enumerate(own_items):
        groups[fd(i)].append(it)
    islands = list(groups.values())
    islands.sort(key=lambda g: (1 if any(it[0] == "via" for it in g) else 0, len(g)))
    return islands, own_items


def snapshot_board_tracks(b) -> list[dict]:
    snap = []
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            c = t.GetPosition()
            snap.append(dict(kind="via", x=c.x, y=c.y, w=t.GetWidth(pcbnew.F_Cu), d=t.GetDrillValue(), code=t.GetNetCode(), locked=t.IsLocked()))
        else:
            s, e = t.GetStart(), t.GetEnd()
            snap.append(dict(kind="trk", sx=s.x, sy=s.y, ex=e.x, ey=e.y, w=t.GetWidth(), layer=t.GetLayer(), code=t.GetNetCode(), locked=t.IsLocked()))
    return snap


def restore_board_tracks(b, snap: list[dict]):
    for t in list(b.GetTracks()):
        KEEP_ALIVE.append(t)
        b.Remove(t)
    for d in snap:
        if d["kind"] == "via":
            v = pcbnew.PCB_VIA(b)
            v.SetPosition(pcbnew.VECTOR2I(d["x"], d["y"]))
            v.SetWidth(d["w"])
            v.SetDrill(d["d"])
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            v.SetNetCode(d["code"])
            v.SetLocked(d["locked"])
            b.Add(v)
        else:
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(pcbnew.VECTOR2I(d["sx"], d["sy"]))
            t.SetEnd(pcbnew.VECTOR2I(d["ex"], d["ey"]))
            t.SetWidth(d["w"])
            t.SetLayer(d["layer"])
            t.SetNetCode(d["code"])
            t.SetLocked(d["locked"])
            b.Add(t)


def snapshot_net_tracks(b, netname: str) -> list[dict]:
    snap = []
    for t in b.GetTracks():
        if t.GetNetname() != netname:
            continue
        if isinstance(t, pcbnew.PCB_VIA):
            c = t.GetPosition()
            snap.append(dict(kind="via", x=c.x, y=c.y, w=t.GetWidth(pcbnew.F_Cu), d=t.GetDrillValue(), code=t.GetNetCode(), locked=t.IsLocked()))
        else:
            s, e = t.GetStart(), t.GetEnd()
            snap.append(dict(kind="trk", sx=s.x, sy=s.y, ex=e.x, ey=e.y, w=t.GetWidth(), layer=t.GetLayer(), code=t.GetNetCode(), locked=t.IsLocked()))
    return snap


def restore_net_tracks(b, netname: str, snap: list[dict]):
    for t in list(b.GetTracks()):
        if t.GetNetname() == netname:
            KEEP_ALIVE.append(t)
            b.Remove(t)
    for d in snap:
        if d["kind"] == "via":
            v = pcbnew.PCB_VIA(b)
            v.SetPosition(pcbnew.VECTOR2I(d["x"], d["y"]))
            v.SetWidth(d["w"])
            v.SetDrill(d["d"])
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            v.SetNetCode(d["code"])
            v.SetLocked(d["locked"])
            b.Add(v)
        else:
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(pcbnew.VECTOR2I(d["sx"], d["sy"]))
            t.SetEnd(pcbnew.VECTOR2I(d["ex"], d["ey"]))
            t.SetWidth(d["w"])
            t.SetLayer(d["layer"])
            t.SetNetCode(d["code"])
            t.SetLocked(d["locked"])
            b.Add(t)


def rip_local_net(b, netname: str, trk_region: Polygon, via_region: Polygon | None = None) -> int:
    um = pcbnew.ToMM
    if via_region is None:
        via_region = trk_region
    removed = 0
    for t in list(b.GetTracks()):
        if t.GetNetname() != netname:
            continue
        if isinstance(t, pcbnew.PCB_VIA):
            c = t.GetPosition()
            if Point(um(c.x) - OX, um(c.y) - OY).intersects(via_region):
                KEEP_ALIVE.append(t)
                b.Remove(t)
                removed += 1
        else:
            s, e = t.GetStart(), t.GetEnd()
            g = LineString([(um(s.x) - OX, um(s.y) - OY), (um(e.x) - OX, um(e.y) - OY)])
            if g.intersects(trk_region):
                KEEP_ALIVE.append(t)
                b.Remove(t)
                removed += 1
    return removed


def trim_net_dangling(b, netname: str) -> int:
    base_isl_cnt = len(get_net_islands(b, netname)[0])
    net_snap = snapshot_net_tracks(b, netname)
    um = pcbnew.ToMM
    ids = {b.GetLayerName(l): l for l in range(64) if b.GetLayerName(l).endswith(".Cu")}
    pad_polys = collections.defaultdict(list)
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() == netname:
                for L in LAY:
                    if p.IsOnLayer(ids[L]):
                        pad_polys[L].append(pad_poly(p, ids[L], um).buffer(0.015))
    total_peeled = 0
    while True:
        vias = [
            Point(um(t.GetPosition().x) - OX, um(t.GetPosition().y) - OY).buffer(um(t.GetWidth(ids["F.Cu"])) / 2 + 0.015)
            for t in b.GetTracks()
            if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == netname
        ]
        trks = [t for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == netname]
        if not trks:
            break
        by_lay = collections.defaultdict(list)
        for t in trks:
            L = t.GetLayerName()
            if L in LIDX:
                s, e = t.GetStart(), t.GetEnd()
                hw = um(t.GetWidth()) / 2
                by_lay[L].append((t, LineString([(um(s.x) - OX, um(s.y) - OY), (um(e.x) - OX, um(e.y) - OY)]), hw))
        peeled = 0
        for L, items in by_lay.items():
            bufs = [g.buffer(hw + 0.014) for _, g, hw in items]
            tree = STRtree(bufs)
            for idx, (t, g, _) in enumerate(items):
                c0, c1 = g.coords[0], g.coords[-1]
                if math.hypot(c1[0] - c0[0], c1[1] - c0[1]) < 1e-5:
                    KEEP_ALIVE.append(t)
                    b.Remove(t)
                    peeled += 1
                    continue
                dangling = False
                for px, py in (c0, c1):
                    pt = Point(px, py)
                    if any(pg.contains(pt) for pg in pad_polys[L]):
                        continue
                    if any(vg.contains(pt) for vg in vias):
                        continue
                    near = tree.query(pt, predicate="intersects")
                    if not any(int(j) != idx for j in near):
                        dangling = True
                        break
                if dangling:
                    KEEP_ALIVE.append(t)
                    b.Remove(t)
                    peeled += 1
        total_peeled += peeled
        if peeled == 0:
            break
    if len(get_net_islands(b, netname)[0]) > base_isl_cnt:
        restore_net_tracks(b, netname, net_snap)
        return 0
    return total_peeled


def build_static_env(
    b, board_poly: Polygon, active_nets: list[str], wx0: float, wy0: float, wx1: float, wy1: float, grid: float,
    ignore_rippable: bool = False,
):
    um = pcbnew.ToMM
    ids = {b.GetLayerName(l): l for l in range(64) if b.GetLayerName(l).endswith(".Cu")}
    edge_clr = um(b.GetDesignSettings().m_CopperEdgeClearance)
    active_set = set(active_nets)

    nx = int(round((wx1 - wx0) / grid)) + 1
    ny = int(round((wy1 - wy0) / grid)) + 1
    xs = wx0 + np.arange(nx) * grid
    ys = wy0 + np.arange(ny) * grid
    GX, GY = np.meshgrid(xs, ys, indexing="ij")
    Wbox = shapely.box(wx0 - 0.8, wy0 - 0.8, wx1 + 0.8, wy1 + 0.8)

    trk_inside = shapely.contains_xy(board_poly.buffer(-(edge_clr + TW + M)), GX, GY)
    via_inside = shapely.contains_xy(board_poly.buffer(-(max(edge_clr + VR, 0.30 + HR) + M)), GX, GY)
    base_block = [~trk_inside.copy() for _ in range(NLAY)]
    base_via_bad = ~via_inside.copy()

    f_geoms = {L: collections.defaultdict(list) for L in LAY}
    via_holes = []
    npth_holes = []

    own_geoms = {n: {L: [] for L in LAY} for n in active_nets}
    own_via_holes = {n: [] for n in active_nets}
    own_vias_xy = {n: [] for n in active_nets}

    for f in b.GetFootprints():
        for p in f.Pads():
            pnet = p.GetNetname()
            c = p.GetPosition()
            px, py = um(c.x) - OX, um(c.y) - OY
            if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH) and max(p.GetDrillSizeX(), p.GetDrillSizeY()) > 0:
                dx_d, dy_d = um(p.GetDrillSizeX()) / 2, um(p.GetDrillSizeY()) / 2
                dr = max(dx_d, dy_d)
                pt = Point(px, py)
                if pt.buffer(dr + 0.5).intersects(Wbox):
                    if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH or pnet not in active_set:
                        npth_holes.append((pt, dr))
                    else:
                        own_via_holes[pnet].append(pt.buffer(dr, 16))
            if pnet in active_set:
                for L in LAY:
                    if p.IsOnLayer(ids[L]):
                        g = pad_poly(p, ids[L], um)
                        if g.intersects(Wbox):
                            own_geoms[pnet][L].append(g)
                continue
            cl = max(CL, net_clr(pnet))
            for L in LAY:
                if p.IsOnLayer(ids[L]):
                    g = pad_poly(p, ids[L], um)
                    if g.intersects(Wbox):
                        f_geoms[L][cl].append(g)

    for t in b.GetTracks():
        tnet = t.GetNetname()
        if tnet in active_set:
            if isinstance(t, pcbnew.PCB_VIA):
                c = t.GetPosition()
                vx, vy = um(c.x) - OX, um(c.y) - OY
                pt = Point(vx, vy)
                own_vias_xy[tnet].append((vx, vy))
                if pt.buffer(0.6).intersects(Wbox):
                    g = pt.buffer(um(t.GetWidth(ids["F.Cu"])) / 2, 16)
                    for L in LAY:
                        own_geoms[tnet][L].append(g)
                    own_via_holes[tnet].append(pt.buffer(um(t.GetDrillValue()) / 2, 16))
            else:
                L = t.GetLayerName()
                if L in LIDX:
                    s, e = t.GetStart(), t.GetEnd()
                    g = LineString([(um(s.x) - OX, um(s.y) - OY), (um(e.x) - OX, um(e.y) - OY)]).buffer(um(t.GetWidth()) / 2, 8)
                    if g.intersects(Wbox):
                        own_geoms[tnet][L].append(g)
            continue

        if ignore_rippable and can_rip_net(tnet):
            continue

        cl = max(CL, net_clr(tnet))
        if isinstance(t, pcbnew.PCB_VIA):
            c = t.GetPosition()
            vx, vy = um(c.x) - OX, um(c.y) - OY
            pt = Point(vx, vy)
            if not pt.buffer(0.6).intersects(Wbox):
                continue
            g = pt.buffer(um(t.GetWidth(ids["F.Cu"])) / 2, 16)
            for L in LAY:
                f_geoms[L][cl].append(g)
            via_holes.append(pt.buffer(um(t.GetDrillValue()) / 2, 16))
        else:
            L = t.GetLayerName()
            if L not in LIDX:
                continue
            s, e = t.GetStart(), t.GetEnd()
            g = LineString([(um(s.x) - OX, um(s.y) - OY), (um(e.x) - OX, um(e.y) - OY)]).buffer(um(t.GetWidth()) / 2, 8)
            if g.intersects(Wbox):
                f_geoms[L][cl].append(g)

    for z in b.Zones():
        zname = z.GetZoneName()
        if z.GetIsRuleArea():
            o = z.Outline().COutline(0)
            g = Polygon([(um(o.CPoint(i).x) - OX, um(o.CPoint(i).y) - OY) for i in range(o.PointCount())])
            if not g.is_valid:
                g = g.buffer(0)
            if not g.buffer(0.4).intersects(Wbox):
                continue
            if "solid EP" in zname or zname.startswith("vendor ") or zname in ("U3 ring vias", "reg corner", "L1 window"):
                base_via_bad |= shapely.contains_xy(g.buffer(VR + 0.025), GX, GY)
            if "solid EP" in zname or zname.startswith("vendor ") or zname in ("U3 ring", "reg corner", "L1 window"):
                base_block[LIDX["B.Cu"]] |= shapely.contains_xy(g.buffer(TW + 0.025), GX, GY)
        else:
            znet = z.GetNetname()
            if znet in active_set or znet == "GND":
                # Note: GND In1.Cu/In2.Cu/F.Cu/B.Cu pours refill around stitched tracks automatically;
                # only fixed copper zones (like vendor B.Cu areas, handled above) block stitching!
                continue
            cl = max(CL, net_clr(znet))
            for L in LAY:
                if z.IsOnLayer(ids[L]):
                    ps = z.GetFilledPolysList(ids[L])
                    for k in range(ps.OutlineCount()):
                        o = ps.Outline(k)
                        pts = [(um(o.CPoint(i).x) - OX, um(o.CPoint(i).y) - OY) for i in range(o.PointCount())]
                        if len(pts) >= 3:
                            g = Polygon(pts).buffer(0)
                            if g.intersects(Wbox):
                                f_geoms[L][cl].append(g)

    for L in LAY:
        li = LIDX[L]
        for cl, glist in f_geoms[L].items():
            u = unary_union(glist)
            base_block[li] |= shapely.contains_xy(u.buffer(TW + cl + M), GX, GY)
            base_via_bad |= shapely.contains_xy(u.buffer(max(VR + cl, HR + HC) + M), GX, GY)

    if via_holes:
        uh = unary_union(via_holes)
        hm_trk = shapely.contains_xy(uh.buffer(TW + HC + M), GX, GY)
        for li in range(NLAY):
            base_block[li] |= hm_trk
        base_via_bad |= shapely.contains_xy(uh.buffer(max(VR + HC, HR + HC) + M), GX, GY)

    for pt, dr in npth_holes:
        hm_trk = shapely.contains_xy(pt.buffer(dr + TW + HC + M), GX, GY)
        for li in range(NLAY):
            base_block[li] |= hm_trk
        base_via_bad |= shapely.contains_xy(pt.buffer(dr + VR + HC + M), GX, GY)

    net_block = {}
    net_via_bad = {}
    other_block_contrib = {n: [np.zeros((nx, ny), dtype=bool) for _ in range(NLAY)] for n in active_nets}
    other_via_contrib = {n: np.zeros((nx, ny), dtype=bool) for n in active_nets}
    for n in active_nets:
        cl = max(CL, net_clr(n))
        for L in LAY:
            li = LIDX[L]
            if own_geoms[n][L]:
                u = unary_union(own_geoms[n][L])
                other_block_contrib[n][li] |= shapely.contains_xy(u.buffer(TW + cl + M), GX, GY)
                other_via_contrib[n] |= shapely.contains_xy(u.buffer(max(VR + cl, HR + HC) + M), GX, GY)
        if own_via_holes[n]:
            uh = unary_union(own_via_holes[n])
            hm = shapely.contains_xy(uh.buffer(TW + HC + M), GX, GY)
            for li in range(NLAY):
                other_block_contrib[n][li] |= hm
            other_via_contrib[n] |= shapely.contains_xy(uh.buffer(max(VR + HC, HR + HC) + M), GX, GY)

    for n in active_nets:
        blk = [b_arr.copy() for b_arr in base_block]
        vbad = base_via_bad.copy()
        for m in active_nets:
            if m == n:
                continue
            for li in range(NLAY):
                blk[li] |= other_block_contrib[m][li]
            vbad |= other_via_contrib[m]
        for vx, vy in own_vias_xy[n]:
            vbad |= np.hypot(GX - vx, GY - vy) < 0.365
        net_block[n] = blk
        net_via_bad[n] = vbad

    return dict(
        wx0=wx0, wy0=wy0, wx1=wx1, wy1=wy1, grid=grid, nx=nx, ny=ny, GX=GX, GY=GY,
        net_block=net_block, net_via_bad=net_via_bad,
    )


def island_masks_and_anchors(items, blk, wx0: float, wy0: float, nx: int, ny: int, GX, GY, grid: float, um):
    mask = [np.zeros((nx, ny), dtype=bool) for _ in range(NLAY)]
    anchors = {}
    for L in LAY:
        li = LIDX[L]
        geoms = [it[1] for it in items if L in it[2]]
        skel_parts = []
        for it in items:
            if L not in it[2]:
                continue
            if it[0] in ("pad", "via"):
                skel_parts.append(Point(it[3][0], it[3][1]))
            elif it[0] == "trk":
                trk = it[4]
                s, e = trk.GetStart(), trk.GetEnd()
                p0 = (um(s.x) - OX, um(s.y) - OY)
                p1 = (um(e.x) - OX, um(e.y) - OY)
                skel_parts.append(LineString([p0, p1]) if math.hypot(p1[0] - p0[0], p1[1] - p0[1]) > 1e-6 else Point(p0))
        if geoms:
            shrunk = [g.buffer(-0.032) if not g.buffer(-0.032).is_empty else g for g in geoms]
            mask[li] = shapely.contains_xy(unary_union(shrunk), GX, GY) & ~blk[li]
            if not mask[li].any():
                mask[li] = shapely.contains_xy(unary_union(geoms), GX, GY) & ~blk[li]
        for it in items:
            if L not in it[2]:
                continue
            pts = []
            if it[0] in ("pad", "via"):
                pts.append(it[3])
            elif it[0] == "trk":
                trk = it[4]
                for ep in (trk.GetStart(), trk.GetEnd()):
                    pts.append((um(ep.x) - OX, um(ep.y) - OY))
            for ax, ay in pts:
                gi0, gj0 = int(round((ax - wx0) / grid)), int(round((ay - wy0) / grid))
                candidates = [(gi0, gj0)] + [
                    (gi0 + di, gj0 + dj)
                    for di in (-1, 0, 1)
                    for dj in (-1, 0, 1)
                    if (di != 0 or dj != 0) and math.hypot((wx0 + (gi0 + di) * grid) - ax, (wy0 + (gj0 + dj) * grid) - ay) <= 0.030
                ]
                for gi, gj in candidates:
                    if 0 <= gi < nx and 0 <= gj < ny and not blk[li][gi, gj]:
                        mask[li][gi, gj] = True
                        anchors[(gi, gj, li)] = (ax, ay)
                        break
        if skel_parts and mask[li].any():
            anchors[("skel", li)] = unary_union(skel_parts)
    return mask, anchors


def resolve_state_anchor(st: tuple[int, int, int], anch: dict, wx0: float, wy0: float, grid: float) -> tuple[float, float] | None:
    if st in anch:
        return anch[st]
    sk = anch.get(("skel", st[2]))
    if sk is not None:
        np_pt = nearest_points(sk, Point(wx0 + st[0] * grid, wy0 + st[1] * grid))[0]
        return (float(np_pt.x), float(np_pt.y))
    return None


def mask_boundary_multipoint(r2d: np.ndarray, wx0: float, wy0: float, grid: float) -> MultiPoint | None:
    if not r2d.any():
        return None
    bnd = r2d & ~binary_erosion(r2d, border_value=0)
    bi, bj = np.nonzero(bnd)
    if len(bi) == 0:
        bi, bj = np.nonzero(r2d)
    if len(bi) > 1600:
        step = max(1, len(bi) // 1600)
        bi, bj = bi[::step], bj[::step]
    return MultiPoint([(float(wx0 + int(i) * grid), float(wy0 + int(j) * grid)) for i, j in zip(bi, bj)])


def analyze_3d_reach(src_mask, goal_mask, blk, vbad):
    struct8 = np.ones((3, 3), dtype=np.int8)
    lbls = []
    offset = 0
    for li in range(NLAY):
        l_arr, n_c = nd_label(~blk[li], structure=struct8)
        if n_c > 0 and offset > 0:
            nz = l_arr > 0
            l_arr[nz] += offset
        lbls.append(l_arr)
        offset += n_c
    if offset == 0:
        return False, None, None
    par = list(range(offset + 1))

    def fd(x: int) -> int:
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    vi, vj = np.nonzero(~vbad)
    if len(vi) > 0:
        cols = np.stack([lbls[li][vi, vj] for li in range(NLAY)], axis=1)
        ucols = np.unique(cols, axis=0)
        for row in ucols:
            nz = [int(c) for c in row if c > 0]
            if len(nz) >= 2:
                r0 = fd(nz[0])
                for c in nz[1:]:
                    par[fd(c)] = r0

    src_roots = set()
    for li in range(NLAY):
        for c in np.unique(lbls[li][src_mask[li]]):
            if c > 0:
                src_roots.add(fd(int(c)))
    if not src_roots:
        return False, None, None

    goal_roots = set()
    if goal_mask is not None:
        for li in range(NLAY):
            for c in np.unique(lbls[li][goal_mask[li]]):
                if c > 0:
                    rc = fd(int(c))
                    if rc in src_roots:
                        return True, None, None
                    goal_roots.add(rc)

    valid_src = np.array([False] + [fd(c) in src_roots for c in range(1, offset + 1)], dtype=bool)
    src_reach = [valid_src[lbls[li]] for li in range(NLAY)]
    if goal_roots:
        valid_goal = np.array([False] + [fd(c) in goal_roots for c in range(1, offset + 1)], dtype=bool)
        goal_reach = [valid_goal[lbls[li]] for li in range(NLAY)]
    else:
        goal_reach = None
    return False, src_reach, goal_reach


def astar_subroute(
    src_mask, src_anchors, goal_mask, goal_anchors, H_2d,
    blk, vbad, T_soft, V_soft, hist_t, hist_v, pres_fac: float, grid: float, nx: int, ny: int,
):
    pq = []
    dist = {}
    prev = {}
    prev_dir = {}
    for li in range(NLAY):
        for gi, gj in zip(*np.nonzero(src_mask[li])):
            st = (int(gi), int(gj), li)
            dist[st] = 0.0
            prev_dir[st] = None
            heapq.heappush(pq, (float(H_2d[gi, gj]), st))

    if not pq:
        return None, dist

    VIA_COST = 1.15
    LAYER_BIAS = [1.15, 1.00, 1.15]

    max_popped = 750000 if (nx * ny > 250000) else 350000
    end_state = None
    popped = 0
    while pq:
        f_score, u = heapq.heappop(pq)
        gi, gj, li = u
        g = dist.get(u, 1e18)
        if f_score - float(H_2d[gi, gj]) > g + 1e-5:
            continue
        if goal_mask[li][gi, gj]:
            end_state = u
            break
        popped += 1
        if popped > max_popped:
            break

        pdir = prev_dir[u]
        lb = LAYER_BIAS[li]
        blk_l = blk[li]
        ts_l = T_soft[li]
        ht_l = hist_t[li]

        for d_idx, (dx, dy, w_step) in enumerate(DIRS):
            ni, nj = gi + dx, gj + dy
            if not (0 <= ni < nx and 0 <= nj < ny) or blk_l[ni, nj]:
                continue
            if dx != 0 and dy != 0 and (blk_l[ni, gj] and blk_l[gi, nj]):
                continue
            occ = int(ts_l[ni, nj])
            pen = (pres_fac * occ * (1.0 + float(ht_l[ni, nj]))) if occ > 0 else (0.04 * float(ht_l[ni, nj]))
            turn = 0.008 if (pdir is not None and pdir >= 0 and pdir != d_idx) else 0.0
            ng = g + grid * w_step * lb + turn + pen
            v_st = (ni, nj, li)
            if ng < dist.get(v_st, 1e18):
                dist[v_st] = ng
                prev[v_st] = u
                prev_dir[v_st] = d_idx
                heapq.heappush(pq, (ng + float(H_2d[ni, nj]), v_st))

        if not vbad[gi, gj]:
            vocc = int(V_soft[gi, gj])
            vpen = (pres_fac * 2.5 * vocc * (1.0 + float(hist_v[gi, gj]))) if vocc > 0 else (0.12 * float(hist_v[gi, gj]))
            for nli in range(NLAY):
                if nli != li and not blk[nli][gi, gj]:
                    tocc2 = int(T_soft[nli][gi, gj])
                    tpen2 = (pres_fac * tocc2 * (1.0 + float(hist_t[nli][gi, gj]))) if tocc2 > 0 else 0.0
                    ng = g + VIA_COST + vpen + tpen2
                    v_st = (gi, gj, nli)
                    if ng < dist.get(v_st, 1e18):
                        dist[v_st] = ng
                        prev[v_st] = u
                        prev_dir[v_st] = -1
                        heapq.heappush(pq, (ng + float(H_2d[gi, gj]), v_st))

    if end_state is None:
        return None, dist

    states = [end_state]
    cur = end_state
    while cur in prev:
        cur = prev[cur]
        states.append(cur)
    states.reverse()
    return (states, src_anchors, goal_anchors), dist


def extract_route_footprint(subroutes: list):
    trk_cells = [[] for _ in range(NLAY)]
    via_cells = []
    for states, _, _ in subroutes:
        for k, (gi, gj, li) in enumerate(states):
            trk_cells[li].append((gi, gj))
            if k + 1 < len(states) and states[k + 1][2] != li:
                via_cells.append((gi, gj))
    return trk_cells, via_cells


def solve_group_pathfinder(
    b, board_poly: Polygon, active_nets: list[str], grid: float = 0.025, margin: float = 2.8, max_passes: int = 24,
    extra_pts: list[tuple[float, float]] | None = None,
):
    um = pcbnew.ToMM
    mm = pcbnew.FromMM
    ids = {b.GetLayerName(l): l for l in range(64) if b.GetLayerName(l).endswith(".Cu")}
    bx0, by0, bx1, by1 = board_poly.bounds

    net_islands = {}
    pts_x, pts_y = [], []
    if extra_pts:
        for ex, ey in extra_pts:
            pts_x.append(ex)
            pts_y.append(ey)
    long_span = False
    for n in active_nets:
        isls, _ = get_net_islands(b, n)
        if len(isls) <= 1:
            continue
        net_islands[n] = isls
        big_u = unary_union([it[1] for it in isls[-1]])
        big_vias = [it[3] for it in isls[-1] if it[0] == "via"]
        if not big_vias:
            gb0, gb1, gb2, gb3 = big_u.bounds
            pts_x.extend([gb0, gb2])
            pts_y.extend([gb1, gb3])
        for isl in isls[:-1]:
            su = unary_union([it[1] for it in isl])
            b0, b1, b2, b3 = su.bounds
            pts_x.extend([b0, b2])
            pts_y.extend([b1, b3])
            sline = shapely.shortest_line(su, big_u)
            ps, pt = sline.coords
            pts_x.extend([ps[0], pt[0]])
            pts_y.extend([ps[1], pt[1]])
            if sline.length > 9.0:
                long_span = True
                for vx, vy in big_vias:
                    pts_x.append(vx)
                    pts_y.append(vy)
            else:
                scx, scy = (b0 + b2) / 2.0, (b1 + b3) / 2.0
                near_v = sorted(big_vias, key=lambda v: math.hypot(v[0] - scx, v[1] - scy))[:4]
                for vx, vy in near_v:
                    if math.hypot(vx - scx, vy - scy) <= 9.0:
                        pts_x.append(vx)
                        pts_y.append(vy)

    if not net_islands:
        return True, "0 nets needed routing", None

    if long_span:
        wx0 = max(bx0 - 0.3, math.floor((min(pts_x) - 4.5) / grid) * grid)
        wy0 = max(by0 - 0.3, math.floor((min(pts_y) - 4.5) / grid) * grid)
        wx1 = min(bx1 + 0.3, math.ceil((max(pts_x) + 4.5) / grid) * grid)
        wy1 = min(by1 + 0.3, math.ceil((max(pts_y) + 4.5) / grid) * grid)
    else:
        wx0 = max(bx0 - 0.3, math.floor((min(pts_x) - margin) / grid) * grid)
        wy0 = max(by0 - 0.3, math.floor((min(pts_y) - margin) / grid) * grid)
        wx1 = min(bx1 + 0.3, math.ceil((max(pts_x) + margin) / grid) * grid)
        wy1 = min(by1 + 0.3, math.ceil((max(pts_y) + margin) / grid) * grid)

    env = build_static_env(b, board_poly, list(net_islands.keys()), wx0, wy0, wx1, wy1, grid)
    nx, ny, GX, GY = env["nx"], env["ny"], env["GX"], env["GY"]

    off_tt = make_disk_offsets(R_TT, grid)
    off_tv = make_disk_offsets(R_TV, grid)
    off_vv = make_disk_offsets(R_VV, grid)

    isl_data = {}
    for n, isls in net_islands.items():
        blk = env["net_block"][n]
        isl_data[n] = [island_masks_and_anchors(isl, blk, wx0, wy0, nx, ny, GX, GY, grid, um) for isl in isls]

    T_soft = [np.zeros((nx, ny), dtype=np.int16) for _ in range(NLAY)]
    V_soft = np.zeros((nx, ny), dtype=np.int16)
    hist_t = [np.zeros((nx, ny), dtype=np.float32) for _ in range(NLAY)]
    hist_v = np.zeros((nx, ny), dtype=np.float32)

    sol = {}
    last_fail_dist = None
    last_fail_reach = None

    def apply_stamp(n: str, delta: int):
        if n not in sol:
            return
        _, trk_cells, via_cells = sol[n]
        for li in range(NLAY):
            if trk_cells[li]:
                stamp_cells(T_soft[li], trk_cells[li], off_tt[0], off_tt[1], delta)
                stamp_cells(V_soft, trk_cells[li], off_tv[0], off_tv[1], delta)
        if via_cells:
            for li in range(NLAY):
                stamp_cells(T_soft[li], via_cells, off_tv[0], off_tv[1], delta)
            stamp_cells(V_soft, via_cells, off_vv[0], off_vv[1], delta)

    def net_has_conflict(n: str) -> bool:
        if n not in sol:
            return True
        apply_stamp(n, -1)
        _, trk_cells, via_cells = sol[n]
        bad = False
        for li in range(NLAY):
            for gi, gj in trk_cells[li]:
                if T_soft[li][gi, gj] > 0:
                    bad = True
                    break
            if bad:
                break
        if not bad:
            for gi, gj in via_cells:
                if V_soft[gi, gj] > 0:
                    bad = True
                    break
        apply_stamp(n, +1)
        return bad

    ordered_nets = list(net_islands.keys())

    for p_idx in range(max_passes):
        pres_fac = 0.45 * (1.42 ** p_idx)
        for n in ordered_nets:
            if p_idx > 0 and not net_has_conflict(n):
                continue
            apply_stamp(n, -1)
            sol.pop(n, None)

            blk = env["net_block"][n]
            vbad = env["net_via_bad"][n].copy()
            masks_list = isl_data[n]
            m_cnt = len(masks_list)

            cur_src_mask = [arr.copy() for arr in masks_list[0][0]]
            cur_src_anchors = dict(masks_list[0][1])
            rem_indices = set(range(1, m_cnt))
            subroutes = []
            ok_net = True

            while rem_indices:
                comb_goal = [np.zeros((nx, ny), dtype=bool) for _ in range(NLAY)]
                comb_anchors = {}
                for ridx in rem_indices:
                    gm, ga = masks_list[ridx]
                    for li in range(NLAY):
                        comb_goal[li] |= gm[li]
                    comb_anchors.update(ga)
                any_goal_2d = np.logical_or.reduce(comb_goal)
                if not any_goal_2d.any():
                    ok_net = False
                    break

                conn_3d, src_reach, goal_reach = analyze_3d_reach(cur_src_mask, comb_goal, blk, vbad)
                if not conn_3d:
                    ok_net = False
                    if n == active_nets[0]:
                        last_fail_reach = (src_reach, goal_reach)
                    break

                h_mult = (1.65 * grid) if (nx * ny > 250000) else (0.98 * grid)
                H_2d = distance_transform_edt(~any_goal_2d).astype(np.float32) * h_mult

                res, dist_map = astar_subroute(
                    cur_src_mask, cur_src_anchors, comb_goal, comb_anchors, H_2d,
                    blk, vbad, T_soft, V_soft, hist_t, hist_v, pres_fac, grid, nx, ny,
                )
                if res is None:
                    ok_net = False
                    if n == active_nets[0]:
                        last_fail_dist = dist_map
                    break
                subroutes.append(res)
                states, _, _ = res
                end_gi, end_gj, end_li = states[-1]
                hit_ridx = next((ridx for ridx in rem_indices if masks_list[ridx][0][end_li][end_gi, end_gj]), min(rem_indices))
                rem_indices.remove(hit_ridx)

                gm, ga = masks_list[hit_ridx]
                for li in range(NLAY):
                    cur_src_mask[li] |= gm[li]
                for ak, av in ga.items():
                    if isinstance(ak, tuple) and len(ak) == 2 and ak[0] == "skel" and ak in cur_src_anchors:
                        cur_src_anchors[ak] = unary_union([cur_src_anchors[ak], av])
                    else:
                        cur_src_anchors[ak] = av
                for k, (gi, gj, li) in enumerate(states):
                    cur_src_mask[li][gi, gj] = True
                    cur_src_anchors.setdefault((gi, gj, li), (round(wx0 + gi * grid, 6), round(wy0 + gj * grid, 6)))
                    if k + 1 < len(states) and states[k + 1][2] != li:
                        vx, vy = wx0 + gi * grid, wy0 + gj * grid
                        vbad |= (np.hypot(GX - vx, GY - vy) < 0.365) & ~((GX == vx) & (GY == vy))

            if not ok_net:
                if len(active_nets) == 1:
                    su = unary_union([it[1] for it in net_islands[active_nets[0]][0]])
                    if last_fail_reach is not None:
                        src_r, goal_r = last_fail_reach
                        vis_lays = {LAY[li] for li in range(NLAY) if src_r is not None and src_r[li].any()}
                        src_r2d = np.logical_or.reduce(src_r) if src_r is not None else np.zeros((nx, ny), dtype=bool)
                        src_area = float(src_r2d.sum()) * (grid * grid)
                        src_mp = mask_boundary_multipoint(src_r2d, wx0, wy0, grid)
                        goal_r2d = np.logical_or.reduce(goal_r) if goal_r is not None else np.zeros((nx, ny), dtype=bool)
                        goal_mp = mask_boundary_multipoint(goal_r2d, wx0, wy0, grid)
                        if src_area > 1.2 and src_mp is not None and goal_mp is not None:
                            fg = shapely.shortest_line(src_mp, goal_mp)
                        else:
                            fg = src_mp if src_mp is not None else su
                        return False, f"no path on {n}", (fg, vis_lays or set(LAY), src_area)
                    vis_pts = [Point(wx0 + gi * grid, wy0 + gj * grid) for (gi, gj, _) in (last_fail_dist or {}).keys()]
                    vis_lays = {LAY[li] for (_, _, li) in (last_fail_dist or {}).keys()}
                    frontier = unary_union(vis_pts).convex_hull if vis_pts else su
                    return False, f"no path on {n}", (frontier, vis_lays or set(LAY), frontier.area)
                return False, f"hard-disconnected on {n} (pass {p_idx + 1})", None

            trk_cells, via_cells = extract_route_footprint(subroutes)
            sol[n] = (subroutes, trk_cells, via_cells)
            apply_stamp(n, +1)

        if len(sol) == len(ordered_nets) and all(not net_has_conflict(n) for n in ordered_nets):
            summary = []
            for n in ordered_nets:
                netcode = b.GetNetInfo().GetNetItem(n).GetNetCode()
                subroutes, _, _ = sol[n]
                segs_added = 0
                vias_added = 0
                for states, src_anchors, goal_anchors in subroutes:
                    k = 0
                    while k < len(states):
                        li = states[k][2]
                        j = k
                        while j + 1 < len(states) and states[j + 1][2] == li:
                            j += 1
                        run = [(states[m][0], states[m][1]) for m in range(k, j + 1)]
                        simp = collinear_simplify(run)
                        pts = [(round(wx0 + a * grid, 6), round(wy0 + c * grid, 6)) for a, c in simp]
                        if k == 0:
                            anc0 = resolve_state_anchor(states[0], src_anchors, wx0, wy0, grid)
                            if anc0 is not None and math.hypot(anc0[0] - pts[0][0], anc0[1] - pts[0][1]) <= 0.12:
                                pts = snap_90_45(anc0[0], anc0[1], pts[0][0], pts[0][1]) + pts[1:]
                        if j == len(states) - 1:
                            anc1 = resolve_state_anchor(states[-1], goal_anchors, wx0, wy0, grid)
                            if anc1 is not None and math.hypot(anc1[0] - pts[-1][0], anc1[1] - pts[-1][1]) <= 0.12:
                                pts = pts[:-1] + snap_90_45(pts[-1][0], pts[-1][1], anc1[0], anc1[1])
                        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                            if math.hypot(x1 - x0, y1 - y0) < 1e-5:
                                continue
                            trk = pcbnew.PCB_TRACK(b)
                            trk.SetStart(pcbnew.VECTOR2I(mm(OX + x0), mm(OY + y0)))
                            trk.SetEnd(pcbnew.VECTOR2I(mm(OX + x1), mm(OY + y1)))
                            trk.SetWidth(mm(TW * 2))
                            trk.SetLayer(ids[LAY[li]])
                            trk.SetNetCode(netcode)
                            b.Add(trk)
                            segs_added += 1
                        if j + 1 < len(states):
                            vi, vj, _ = states[j]
                            vx, vy = round(wx0 + vi * grid, 6), round(wy0 + vj * grid, 6)
                            v = pcbnew.PCB_VIA(b)
                            v.SetPosition(pcbnew.VECTOR2I(mm(OX + vx), mm(OY + vy)))
                            v.SetWidth(mm(VR * 2))
                            v.SetDrill(mm(HR * 2))
                            v.SetLayerPair(ids["F.Cu"], ids["B.Cu"])
                            v.SetNetCode(netcode)
                            b.Add(v)
                            vias_added += 1
                        k = j + 1
                trim_net_dangling(b, n)
                summary.append(f"{n.split('/')[-1]}:{segs_added}s/{vias_added}v")
            return True, f"pass {p_idx + 1} ({', '.join(summary)})", None

        for n in ordered_nets:
            if n not in sol:
                continue
            apply_stamp(n, -1)
            _, trk_cells, via_cells = sol[n]
            for li in range(NLAY):
                for gi, gj in trk_cells[li]:
                    if T_soft[li][gi, gj] > 0:
                        hist_t[li][gi, gj] += 1.0
            for gi, gj in via_cells:
                if V_soft[gi, gj] > 0:
                    hist_v[gi, gj] += 1.5
            apply_stamp(n, +1)

        ordered_nets = ordered_nets[1:] + ordered_nets[:1]

    return False, f"PathFinder unconverged after {max_passes} passes", None


def discover_island_via_combos(
    b, board_poly: Polygon, netname: str, isl: list, forbidden: set[str] | None = None,
) -> list[tuple[list[str], Polygon, Polygon, tuple[float, float]]]:
    if any(it[0] == "via" for it in isl):
        return []
    forb = forbidden or set()
    um = pcbnew.ToMM
    ids = {b.GetLayerName(l): l for l in range(64) if b.GetLayerName(l).endswith(".Cu")}
    u0 = unary_union([it[1] for it in isl])
    b0, b1, b2, b3 = u0.bounds
    gscan = 0.05
    env_cur = build_static_env(b, board_poly, [netname], b0 - 2.2, b1 - 2.2, b2 + 2.2, b3 + 2.2, gscan, ignore_rippable=False)
    env_hard = build_static_env(b, board_poly, [netname], b0 - 2.2, b1 - 2.2, b2 + 2.2, b3 + 2.2, gscan, ignore_rippable=True)
    nx, ny, GX, GY = env_cur["nx"], env_cur["ny"], env_cur["GX"], env_cur["GY"]
    m0, _ = island_masks_and_anchors(isl, env_cur["net_block"][netname], env_cur["wx0"], env_cur["wy0"], nx, ny, GX, GY, gscan, um)

    surf_li = 0 if m0[0].any() else (2 if m0[2].any() else None)
    if surf_li is None:
        return []
    surf_L = LAY[surf_li]
    reach = m0[surf_li].copy()
    free_l = ~env_cur["net_block"][netname][surf_li]
    for _ in range(150):
        nr = (binary_dilation(reach, structure=np.ones((3, 3))) & free_l) | reach
        if np.array_equal(nr, reach):
            break
        reach = nr

    direct_via = reach & (~env_cur["net_via_bad"][netname]) & (~env_cur["net_block"][netname][1])
    if int(direct_via.sum()) >= 2:
        return []

    rpts = [Point(float(GX[i, j]), float(GY[i, j])) for i, j in zip(*np.nonzero(reach))]
    ru = unary_union(rpts) if rpts else u0

    local_rt = []
    for t in b.GetTracks():
        tn = t.GetNetname()
        if tn == netname or not can_rip_net(tn):
            continue
        if isinstance(t, pcbnew.PCB_VIA):
            c = t.GetPosition()
            g = Point(um(c.x) - OX, um(c.y) - OY)
            if g.distance(ru) < 2.2:
                local_rt.append(("via", tn, None, g, um(t.GetWidth(ids["F.Cu"])) / 2, um(t.GetDrillValue()) / 2))
        else:
            L = t.GetLayerName()
            if L in LIDX:
                s, e = t.GetStart(), t.GetEnd()
                g = LineString([(um(s.x) - OX, um(s.y) - OY), (um(e.x) - OX, um(e.y) - OY)])
                if g.distance(ru) < 2.2:
                    local_rt.append(("trk", tn, L, g, um(t.GetWidth()) / 2, 0.0))

    vlegal = (
        (~env_hard["net_via_bad"][netname])
        & (~env_hard["net_block"][netname][surf_li])
        & (~env_hard["net_block"][netname][1])
    )
    raw = []
    for i, j in zip(*np.nonzero(vlegal)):
        px, py = float(GX[i, j]), float(GY[i, j])
        pt = Point(px, py)
        d_reach = ru.distance(pt)
        if d_reach > 1.50:
            continue
        blks = set()
        hit_via_pts = []
        for kind, tn, tL, g, hw, dr in local_rt:
            cl = max(CL, net_clr(tn))
            if kind == "via":
                if pt.distance(g) < max(VR + cl, VR + HC, HR + HC, hw + cl, hw + HC) + M + 0.020:
                    blks.add(tn)
                    hit_via_pts.append(g)
            else:
                if pt.distance(g) < hw + max(VR + cl, HR + HC) + M + 0.015:
                    blks.add(tn)
        seg = shapely.shortest_line(ru, pt) if d_reach > 0.06 else pt
        if d_reach > 0.06:
            for kind, tn, tL, g, hw, dr in local_rt:
                cl = max(CL, net_clr(tn))
                if kind == "via" and seg.distance(g) < TW + max(hw + cl, dr + HC) + M + 0.015:
                    blks.add(tn)
                    hit_via_pts.append(g)
                elif kind == "trk" and tL == surf_L and seg.distance(g) < TW + hw + cl + M + 0.015:
                    blks.add(tn)
        if blks & forb:
            continue
        if 1 <= len(blks) <= 3:
            pen = len(blks) + (1.5 if any("LED_SDB" in m for m in blks) else 0.0)
            raw.append((pen, d_reach, sorted(blks), seg, (px, py), hit_via_pts))

    raw.sort(key=lambda x: (x[0], x[1]))
    out = []
    seen = set()
    for _, _, blks, seg, xy, hit_via_pts in raw:
        key = tuple(blks)
        if key in seen:
            continue
        seen.add(key)
        pt = Point(xy[0], xy[1])
        trk_reg = unary_union([pt.buffer(1.45), seg.buffer(1.35), u0.buffer(1.25)])
        via_reg = unary_union([vp.buffer(0.08) for vp in hit_via_pts]) if hit_via_pts else Point(-999.0, -999.0).buffer(0.01)
        out.append((blks, trk_reg, via_reg, xy))
        if len(out) >= 7:
            break
    return out


def stitch_net(b, board_poly: Polygon, netname: str, depth: int = 0, forbidden: set[str] | None = None) -> tuple[bool, str]:
    forb = set(forbidden or set()) | {netname}
    ok, msg, f_info = solve_group_pathfinder(b, board_poly, [netname], grid=0.025, margin=4.0, max_passes=1)
    if ok:
        return True, f"direct: {msg}"

    isls_cur, _ = get_net_islands(b, netname)
    if not isls_cur:
        return True, "empty"
    if f_info is None:
        focus_geom = unary_union([it[1] for it in isls_cur[0]])
        vis_lays = set(LAY)
        f_area = focus_geom.area
    else:
        focus_geom, vis_lays, f_area = f_info

    um = pcbnew.ToMM
    cand_scores = collections.defaultdict(lambda: 99.0)
    for t in b.GetTracks():
        tn = t.GetNetname()
        if tn in forb or not can_rip_net(tn):
            continue
        pen_sdb = 0.8 if "LED_SDB" in tn else 0.0
        if isinstance(t, pcbnew.PCB_VIA):
            c = t.GetPosition()
            d = focus_geom.distance(Point(um(c.x) - OX, um(c.y) - OY))
            if d < 0.90:
                cand_scores[tn] = min(cand_scores[tn], d + pen_sdb)
        else:
            L = t.GetLayerName()
            if L not in vis_lays:
                continue
            s, e = t.GetStart(), t.GetEnd()
            g = LineString([(um(s.x) - OX, um(s.y) - OY), (um(e.x) - OX, um(e.y) - OY)])
            d = focus_geom.distance(g)
            if d < 0.80:
                cand_scores[tn] = min(cand_scores[tn], d + pen_sdb)

    surf_cands = [n for n, _ in sorted(cand_scores.items(), key=lambda kv: kv[1])][:6]
    via_combos_0 = discover_island_via_combos(b, board_poly, netname, isls_cur[0], forbidden=forb)
    via_combos_1 = discover_island_via_combos(b, board_poly, netname, isls_cur[-1], forbidden=forb) if len(isls_cur) >= 2 else []

    indent = "    " + ("  " * depth)
    print(
        f"{indent}[d={depth} {netname}] frontier on {sorted(vis_lays)} (area={f_area:.2f}); "
        f"via0={[[x.split('/')[-1] for x in c[0]] for c in via_combos_0[:4]]}; "
        f"via1={[[x.split('/')[-1] for x in c[0]] for c in via_combos_1[:3]]}; "
        f"surf={[x.split('/')[-1] for x in surf_cands[:5]]}",
        flush=True,
    )

    default_trk_box = focus_geom.buffer(1.45)
    trials = []
    seen_trials = set()
    max_combo_sz = 2 if depth >= 1 else 3

    def add_trial(
        nbs: list[str], trk_reg: Polygon, via_reg: Polygon, extra_pts: list[tuple[float, float]], margin: float, tag: str = "std",
    ):
        clean = [x for x in sorted(set(nbs)) if x not in forb]
        key = (tuple(clean), tag)
        if not clean or len(clean) > max_combo_sz or key in seen_trials:
            return
        seen_trials.add(key)
        trials.append((clean, trk_reg, via_reg, extra_pts, margin))

    if via_combos_0 and via_combos_1:
        for b0, tr0, vr0, xy0 in via_combos_0[:3]:
            for b1, tr1, vr1, xy1 in via_combos_1[:2]:
                add_trial(b0 + b1, unary_union([tr0, tr1]), unary_union([vr0, vr1]), [xy0, xy1], 4.2)
    for blks, tr, vr, xy in via_combos_0:
        add_trial(blks, tr, vr, [xy], 4.2)
    for blks, tr, vr, xy in via_combos_0[:3]:
        if len(blks) <= 2:
            add_trial(blks, tr.buffer(0.95), vr, [xy], 4.8, tag="wide")
    for blks, tr, vr, xy in via_combos_1:
        add_trial(blks, tr, vr, [xy], 4.2)

    for nb in surf_cands[:5]:
        add_trial([nb], default_trk_box, focus_geom.buffer(0.45), [], 4.0)

    for nb_s in surf_cands[:2]:
        for blks, tr, vr, xy in via_combos_0[:4]:
            if len(blks) <= 2:
                add_trial([nb_s] + blks, unary_union([default_trk_box, tr]), vr, [xy], 4.5)

    for nb1, nb2 in itertools.combinations(surf_cands[:4], 2):
        add_trial([nb1, nb2], default_trk_box, focus_geom.buffer(0.45), [], 4.2)
    if depth == 0:
        for nb1, nb2, nb3 in itertools.combinations(surf_cands[:4], 3):
            add_trial([nb1, nb2, nb3], default_trk_box, focus_geom.buffer(0.45), [], 4.5)

    if depth >= 1:
        trials = trials[:10]

    base_board_snap = snapshot_board_tracks(b)
    pf_passes = 10 if depth >= 1 else 14

    for nbs, trk_reg, via_reg, extra_pts, margin in trials:
        for nb in nbs:
            rip_local_net(b, nb, trk_reg, via_reg)
        ok_pf, msg_pf, _ = solve_group_pathfinder(
            b, board_poly, [netname] + nbs, grid=0.025, margin=margin, max_passes=pf_passes, extra_pts=extra_pts,
        )
        if ok_pf and all(len(get_net_islands(b, x)[0]) <= 1 for x in [netname] + nbs):
            return True, f"PathFinder[{', '.join(x.split('/')[-1] for x in [netname] + nbs)}] -> {msg_pf}"
        restore_board_tracks(b, base_board_snap)
        print(f"{indent}  pf-trial {[x.split('/')[-1] for x in nbs]}: {msg_pf}", flush=True)

    if depth == 0:
        push_pool = []
        seen_push = set()
        for nbs, trk_reg, via_reg, extra_pts, margin in trials:
            pk = tuple(nbs)
            if pk not in seen_push:
                seen_push.add(pk)
                push_pool.append((nbs, trk_reg, via_reg, extra_pts, margin))
            if len(push_pool) >= 7:
                break
        for nbs, trk_reg, via_reg, extra_pts, margin in push_pool:
            for nb in nbs:
                rip_local_net(b, nb, trk_reg, via_reg)
            ok_1, msg_1, f_1 = solve_group_pathfinder(
                b, board_poly, [netname], grid=0.025, margin=margin, max_passes=1, extra_pts=extra_pts,
            )
            pushed_ok = False
            push_desc = []
            if ok_1:
                pushed_ok = True
                for nb in nbs:
                    if len(get_net_islands(b, nb)[0]) > 1:
                        ok_sub, msg_sub = stitch_net(b, board_poly, nb, depth=1, forbidden=forb | set(nbs))
                        if not ok_sub:
                            pushed_ok = False
                            break
                        push_desc.append(f"{nb.split('/')[-1]}({msg_sub})")
            elif f_1 is not None and len(f_1[1]) >= 2 and f_1[2] > f_area + 2.0:
                ok_bridge, msg_bridge = stitch_net(b, board_poly, netname, depth=1, forbidden=forb | set(nbs))
                if ok_bridge:
                    pushed_ok = True
                    push_desc.append(f"bridge({msg_bridge})")
                    for nb in nbs:
                        if len(get_net_islands(b, nb)[0]) > 1:
                            ok_sub, msg_sub = stitch_net(b, board_poly, nb, depth=1, forbidden=forb | set(nbs))
                            if not ok_sub:
                                pushed_ok = False
                                break
                            push_desc.append(f"{nb.split('/')[-1]}({msg_sub})")

            if pushed_ok and all(len(get_net_islands(b, x)[0]) <= 1 for x in [netname] + nbs):
                return True, f"Push[{netname.split('/')[-1]} -> {', '.join(push_desc)}]"
            restore_board_tracks(b, base_board_snap)
            print(f"{indent}  push-trial {[x.split('/')[-1] for x in nbs]}: failed", flush=True)

    return False, "all PathFinder/Push trials failed"


def main():
    pcb_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else pcb_path
    pro_path = pcb_path.with_suffix(".kicad_pro")
    pro_bytes = pro_path.read_bytes() if pro_path.exists() else None

    drc_json = Path("/tmp/parallelogram-stitch-in-drc.json")
    subprocess.run(["kicad-cli", "pcb", "drc", "--format", "json", "--severity-error", "-o", str(drc_json), str(pcb_path)], capture_output=True, check=True)
    d = json.loads(drc_json.read_text())
    unconn = d.get("unconnected_items", [])
    open_nets = []
    for u in unconn:
        m = re.search(r"\[([^\]]+)\]", u["items"][0]["description"])
        if m and m.group(1) not in open_nets:
            open_nets.append(m.group(1))
    print(f"Initial open nets ({len(open_nets)}): {open_nets}", flush=True)

    b = pcbnew.LoadBoard(str(pcb_path))
    board_poly = get_board_poly(b)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())

    for net in open_nets:
        ok, msg = stitch_net(b, board_poly, net)
        print(f"  {net}: {'OK' if ok else 'FAIL'} -> {msg}", flush=True)

    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(str(out_path), b)
    if pro_bytes is not None and out_path.with_suffix(".kicad_pro") == pro_path:
        pro_path.write_bytes(pro_bytes)
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
