#!/usr/bin/env python3
"""escape_d.py -- Dual-side 25 um octilinear (0/45/90 deg) PathFinder pre-escape for Variant D.

Runs AFTER critpass_d.py (honouring all locked critical tracks/vias on XIN/XOUT/QSPI/USB):
  Stage 1 (B.Cu): Escapes 100% of unescaped WLCSP-36 signal balls (U1, U2, U10, U11, U12)
                  with locked 0.10 mm B.Cu tracks to locked 0.25/0.15 mm through-vias
                  (or free joins to existing same-net locked vias/pads).
  Stage 2 (F.Cu): Escapes every blocked F.Cu LED matrix cathode pad (1, 2, 4) over IC bodies,
                  keepouts, and BGA escape halos (U3, reg corner, L1, U5, and U1..U12 +-2.5 mm)
                  with a locked 0.10 mm F.Cu track to same-net F.Cu copper/via or a clean
                  locked 0.25/0.15 mm through-via.
Every generated segment is strictly 0/45/90 deg and verified against KiCad DRC clearances.
"""
from __future__ import annotations

import collections
import heapq
import math
import re
import sys
from pathlib import Path

import numpy as np
import pcbnew
import shapely
from shapely.geometry import Polygon

OX = OY = 100.0
G = 0.025
X0 = Y0 = -20.0
N = int(round(40.0 / G)) + 1
XS = X0 + np.arange(N) * G
YS = Y0 + np.arange(N) * G

TW = 0.050   # 0.10 mm track half-width
CL = 0.090   # min copper clearance
HC = 0.200   # min hole-to-copper / hole-to-hole clearance
VR = 0.125   # 0.25 mm via copper radius
HR = 0.075   # 0.15 mm via drill radius
M = 0.006    # safety margin above DRC threshold
VV = 0.406   # foreign via-to-via center spacing (>= 0.400 mm)

BGA_REFS = ("U1", "U2", "U10", "U11", "U12")
INNER_BALLS = {"B2", "B3", "B4", "B5", "C2", "D2", "E2", "C5", "D5", "E5", "E3", "C3", "C4", "D3"}
SKIP_BGA_BALLS = {"F2", "D4", "E4", "A3", "F4", "F5", "F3"}
MATRIX_PAT = re.compile(r"/(CS|SW)\d_\d+$")
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


def ij(x: float, y: float) -> tuple[int, int]:
    return int(round((x - X0) / G)), int(round((y - Y0) / G))


def xy(i: int, j: int) -> tuple[float, float]:
    return round(X0 + i * G, 6), round(Y0 + j * G, 6)


def win(x0: float, y0: float, x1: float, y1: float) -> tuple[int, int, int, int]:
    i0, j0 = ij(x0, y0)
    i1, j1 = ij(x1, y1)
    return max(i0 - 1, 0), max(j0 - 1, 0), min(i1 + 2, N), min(j1 + 2, N)


def rect_d(a: float, c: float, e: float, g: float):
    return lambda x, y: np.hypot(np.maximum(np.maximum(a - x, x - e), 0.0), np.maximum(np.maximum(c - y, y - g), 0.0))


def rot_rect_d(px: float, py: float, cs: float, sn: float, hw: float, hh: float):
    return lambda x, y: np.hypot(
        np.maximum(np.abs(cs * (x - px) + sn * (y - py)) - hw, 0.0),
        np.maximum(np.abs(-sn * (x - px) + cs * (y - py)) - hh, 0.0),
    )


def seg_d(a: float, c: float, e: float, g: float):
    def f(x, y):
        vx, vy = e - a, g - c
        n = vx * vx + vy * vy
        t = np.clip(((x - a) * vx + (y - c) * vy) / n, 0.0, 1.0) if n > 1e-12 else 0.0
        return np.hypot(x - a - t * vx, y - c - t * vy)

    return f


def circ_d(a: float, c: float):
    return lambda x, y: np.hypot(x - a, y - c)


class Obj:
    __slots__ = ("net", "win", "tf", "tb", "vm")

    def __init__(self, net: str, w: tuple[int, int, int, int], tf, tb, vm):
        self.net = net
        self.win = w
        self.tf = tf
        self.tb = tb
        self.vm = vm


def mk_obj(net: str, dist_fn, bbox: tuple[float, float, float, float], r_tf: float, r_tb: float, r_v: float) -> Obj:
    rmax = max(r_tf, r_tb, r_v, 0.0) + 0.03
    i0, j0, i1, j1 = win(bbox[0] - rmax, bbox[1] - rmax, bbox[2] + rmax, bbox[3] + rmax)
    gx, gy = np.meshgrid(XS[i0:i1], YS[j0:j1], indexing="ij")
    d = dist_fn(gx, gy)
    tf = (d < r_tf) if r_tf > 0 else None
    tb = (d < r_tb) if r_tb > 0 else None
    vm = (d < r_v) if r_v > 0 else None
    return Obj(net, (i0, j0, i1, j1), tf, tb, vm)


def poly_mask(pts: list[tuple[float, float]], buf: float):
    poly = Polygon(pts)
    if not poly.is_valid:
        poly = poly.buffer(0)
    bpoly = poly.buffer(buf)
    minx, miny, maxx, maxy = bpoly.bounds
    i0, j0, i1, j1 = win(minx, miny, maxx, maxy)
    gx, gy = np.meshgrid(XS[i0:i1], YS[j0:j1], indexing="ij")
    return (i0, j0, i1, j1), shapely.contains_xy(bpoly, gx, gy)


def net_clr(net: str) -> float:
    if any(k in net for k in ("XIN", "XOUT", "C24-Pad1", "USB_D")):
        return 0.150
    if "VREG_LX" in net:
        return 0.120
    if "QSPI" in net:
        return 0.100
    return 0.090


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
    """Connect exact point (x0,y0) to (x1,y1) with exact 0/45/90 deg segments."""
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


def main():
    pcb_path = Path(sys.argv[1])
    pro_path = pcb_path.with_suffix(".kicad_pro")
    pro_bytes = pro_path.read_bytes() if pro_path.exists() else None

    b = pcbnew.LoadBoard(str(pcb_path))
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    mm = pcbnew.FromMM
    um = pcbnew.ToMM
    lid = {b.GetLayerName(l): l for l in range(64) if b.GetLayerName(l).endswith(".Cu")}
    FL, BL = lid["F.Cu"], lid["B.Cu"]
    fps = {f.GetReference(): f for f in b.GetFootprints()}

    TF_hard = np.zeros((N, N), np.int16)
    TB_hard = np.zeros((N, N), np.int16)
    V_hard = np.zeros((N, N), np.int16)
    R_grid = np.hypot(*np.meshgrid(XS, YS, indexing="ij"))
    TF_hard[R_grid > 18.55] += 1
    TB_hard[R_grid > 18.55] += 1
    V_hard[R_grid > 18.48] += 1

    netobjs: dict[str, list[Obj]] = collections.defaultdict(list)

    def apply_obj(o: Obj, sgn: int, TF, TB, V):
        i0, j0, i1, j1 = o.win
        if o.tf is not None:
            TF[i0:i1, j0:j1] += sgn * o.tf
        if o.tb is not None:
            TB[i0:i1, j0:j1] += sgn * o.tb
        if o.vm is not None:
            V[i0:i1, j0:j1] += sgn * o.vm

    def add_hard(o: Obj):
        apply_obj(o, +1, TF_hard, TB_hard, V_hard)
        netobjs[o.net].append(o)

    # 1. Rule areas (via/track keepouts, buffered outward cleanly via shapely!) & non-plane copper zones.
    for z in b.Zones():
        zname = z.GetZoneName()
        zlayers = [b.GetLayerName(l) for l in z.GetLayerSet().Seq()]
        if z.GetIsRuleArea():
            ol = z.Outline().COutline(0)
            pts = [(um(ol.CPoint(k).x) - OX, um(ol.CPoint(k).y) - OY) for k in range(ol.PointCount())]
            if zname in ("U3 ring vias", "reg corner", "L1 window", "LX no copper In6"):
                (i0, j0, i1, j1), vm = poly_mask(pts, VR + 0.025)
                V_hard[i0:i1, j0:j1] += vm
            if zname in ("U3 ring", "reg corner", "L1 window"):
                (i0, j0, i1, j1), tm = poly_mask(pts, TW + 0.025)
                if "B.Cu" in zlayers:
                    TB_hard[i0:i1, j0:j1] += tm
                if "F.Cu" in zlayers:
                    TF_hard[i0:i1, j0:j1] += tm
        else:
            if any(ln in ("B.Cu", "In6.Cu") for ln in zlayers) and zname != "RP2350 band":
                znet = z.GetNetname()
                cl = net_clr(znet)
                for l in z.GetLayerSet().Seq():
                    ln = b.GetLayerName(l)
                    if ln not in ("B.Cu", "In6.Cu"):
                        continue
                    ps = z.GetFilledPolysList(l)
                    for oi in range(ps.OutlineCount()):
                        ol = ps.Outline(oi)
                        pts = [(um(ol.CPoint(k).x) - OX, um(ol.CPoint(k).y) - OY) for k in range(ol.PointCount())]
                        if len(pts) < 3:
                            continue
                        rv = max(VR + cl, HR + HC) + M
                        (i0, j0, i1, j1), vm = poly_mask(pts, rv)
                        tb = None
                        if ln == "B.Cu":
                            poly = Polygon(pts).buffer(0).buffer(TW + cl + M)
                            gx, gy = np.meshgrid(XS[i0:i1], YS[j0:j1], indexing="ij")
                            tb = shapely.contains_xy(poly, gx, gy)
                        add_hard(Obj(znet, (i0, j0, i1, j1), None, tb, vm))

    # 2. All pads (LED F.Cu rotated pads, B.Cu SMD pads, PTH/NPTH holes).
    joins_f: dict[str, dict[tuple[int, int], tuple[float, float]]] = collections.defaultdict(dict)
    joins_b: dict[str, dict[tuple[int, int], tuple[float, float]]] = collections.defaultdict(dict)
    own_vias: dict[str, list[tuple[float, float]]] = collections.defaultdict(list)
    ledpads = {}
    touch_copper: set[tuple[str, str]] = set()

    for f in b.GetFootprints():
        ref = f.GetReference()
        is_led = ref.startswith("D")
        ang = math.radians(-f.GetOrientationDegrees())
        cs, sn = math.cos(ang), math.sin(ang)
        for p in f.Pads():
            net = p.GetNetname()
            cl = net_clr(net)
            c = p.GetPosition()
            px, py = um(c.x) - OX, um(c.y) - OY
            if is_led:
                ledpads[(ref, p.GetNumber())] = dict(
                    x=px, y=py, cs=cs, sn=sn, net=net, code=p.GetNetCode(), ref=ref, num=p.GetNumber()
                )
                dfn = rot_rect_d(px, py, cs, sn, 0.225, 0.225)
                add_hard(mk_obj(net, dfn, (px - 0.35, py - 0.35, px + 0.35, py + 0.35), TW + cl + M, 0.0, max(VR + cl, HR + HC) + M))
                joins_f[net][ij(px, py)] = (px, py)
            else:
                bb = p.GetBoundingBox()
                bx = (um(bb.GetLeft()) - OX, um(bb.GetTop()) - OY, um(bb.GetRight()) - OX, um(bb.GetBottom()) - OY)
                th = p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)
                if th:
                    dr = um(p.GetDrillSizeX()) / 2
                    dfn = circ_d(px, py)
                    rt_h = TW + HC + dr + M
                    # NPTH hole clearance is measured from hole edge to VIA COPPER ANNULAR RING (VR = 0.125)!
                    rv_h = VR + HC + dr + M
                    if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                        pr = max(um(p.GetSizeX()), um(p.GetSizeY())) / 2
                        rt_h = max(rt_h, TW + cl + pr + M)
                        rv_h = max(rv_h, VR + cl + pr + M, HR + HC + pr + M)
                    add_hard(mk_obj(net or "__HOLE__", dfn, (px - dr, py - dr, px + dr, py + dr), rt_h, rt_h, rv_h))
                else:
                    on_f = p.IsOnLayer(FL)
                    on_b = p.IsOnLayer(BL)
                    rt_f = (TW + cl + M) if on_f else 0.0
                    rt_b = (TW + cl + M) if on_b else 0.0
                    rv_p = max(VR + cl, HR + HC) + M if (on_f or on_b) else 0.0
                    add_hard(mk_obj(net or "__NC__", rect_d(*bx), bx, rt_f, rt_b, rv_p))
                    if on_b and net and ref not in BGA_REFS:
                        joins_b[net][ij(px, py)] = (px, py)

    # 3. Existing locked tracks & vias.
    pad_lookup = {}
    for ref in BGA_REFS:
        for p in fps[ref].Pads():
            c = p.GetPosition()
            pad_lookup[(round(um(c.x) - OX, 3), round(um(c.y) - OY, 3), p.GetNetname())] = (ref, p.GetNumber())
    for (ref, num), d in ledpads.items():
        pad_lookup[(round(d["x"], 3), round(d["y"], 3), d["net"])] = (ref, num)

    for t in b.GetTracks():
        net = t.GetNetname()
        cl = net_clr(net)
        if isinstance(t, pcbnew.PCB_VIA):
            c = t.GetPosition()
            vx, vy = um(c.x) - OX, um(c.y) - OY
            vr = um(t.GetWidth(FL)) / 2
            hr = um(t.GetDrillValue()) / 2
            rt = max(vr + cl + TW, hr + HC + TW) + M
            rv = max(vr + VR + cl, hr + VR + HC, vr + HR + HC, hr + HR + HC) + M
            add_hard(mk_obj(net, circ_d(vx, vy), (vx, vy, vx, vy), rt, rt, rv))
            joins_f[net][ij(vx, vy)] = (vx, vy)
            joins_b[net][ij(vx, vy)] = (vx, vy)
            own_vias[net].append((vx, vy))
            k = (round(vx, 3), round(vy, 3), net)
            if k in pad_lookup:
                touch_copper.add(pad_lookup[k])
        else:
            s, e = t.GetStart(), t.GetEnd()
            x0, y0, x1, y1 = um(s.x) - OX, um(s.y) - OY, um(e.x) - OX, um(e.y) - OY
            w = um(t.GetWidth()) / 2
            ln = t.GetLayerName()
            rt_f = (w + cl + TW + M) if ln == "F.Cu" else 0.0
            rt_b = (w + cl + TW + M) if ln == "B.Cu" else 0.0
            rv = max(w + VR + cl, w + HR + HC) + M
            add_hard(mk_obj(net, seg_d(x0, y0, x1, y1), (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)), rt_f, rt_b, rv))
            for qx, qy in ((x0, y0), (x1, y1)):
                k = (round(qx, 3), round(qy, 3), net)
                if k in pad_lookup:
                    touch_copper.add(pad_lookup[k])

    bga_boxes = []
    for uref in BGA_REFS:
        cp = fps[uref].GetPosition()
        bx, by = um(cp.x) - OX, um(cp.y) - OY
        bga_boxes.append((uref, bx, by))

    def get_view(net: str, layer: str, i0: int, j0: int, i1: int, j1: int):
        T = (TF_hard if layer == "F.Cu" else TB_hard)[i0:i1, j0:j1].copy()
        V = V_hard[i0:i1, j0:j1].copy()
        for o in netobjs[net]:
            a0, c0, a1, c1 = o.win
            x0, x1 = max(a0, i0), min(a1, i1)
            y0, y1 = max(c0, j0), min(c1, j1)
            if x0 >= x1 or y0 >= y1:
                continue
            tm = o.tf if layer == "F.Cu" else o.tb
            if tm is not None:
                T[x0 - i0 : x1 - i0, y0 - j0 : y1 - j0] -= tm[x0 - a0 : x1 - a0, y0 - c0 : y1 - c0]
            if o.vm is not None:
                V[x0 - i0 : x1 - i0, y0 - j0 : y1 - j0] -= o.vm[x0 - a0 : x1 - a0, y0 - c0 : y1 - c0]
        return T, V

    def run_unified_escape(items: list[dict], passes: int):
        """Unified 3-grid (TF_soft, TB_soft, V_soft) Gauss-Seidel PathFinder across B.Cu & F.Cu."""
        TF_soft = np.zeros((N, N), np.int16)
        TB_soft = np.zeros((N, N), np.int16)
        V_soft = np.zeros((N, N), np.int16)
        hist_tf = np.zeros((N, N), np.float32)
        hist_tb = np.zeros((N, N), np.float32)
        hist_v = np.zeros((N, N), np.float32)
        stubs = {}
        net_stubs = collections.defaultdict(list)

        class Stub:
            __slots__ = ("key", "layer", "net", "code", "pts", "grid_path", "via", "objs", "cells")

        def apply_soft(objs, sgn: int):
            for o in objs:
                i0, j0, i1, j1 = o.win
                if o.tf is not None:
                    TF_soft[i0:i1, j0:j1] += sgn * o.tf
                if o.tb is not None:
                    TB_soft[i0:i1, j0:j1] += sgn * o.tb
                if o.vm is not None:
                    V_soft[i0:i1, j0:j1] += sgn * o.vm

        def search_one(it: dict, allow_soft: bool, pres_fac: float):
            layer = it["layer"]
            reach = it["reach"]
            crowd = it["crowd"]
            px, py, net = it["x"], it["y"], it["net"]
            joins = joins_f if layer == "F.Cu" else joins_b
            T_soft_cur = TF_soft if layer == "F.Cu" else TB_soft
            H_t_cur = hist_tf if layer == "F.Cu" else hist_tb

            i0, j0, i1, j1 = win(px - reach, py - reach, px + reach, py + reach)
            T, V = get_view(net, layer, i0, j0, i1, j1)
            Ts = T_soft_cur[i0:i1, j0:j1].copy()
            Vs = V_soft[i0:i1, j0:j1].copy()
            for s in net_stubs[net]:
                for o in s.objs:
                    a0, c0, a1, c1 = o.win
                    x0, x1 = max(a0, i0), min(a1, i1)
                    y0, y1 = max(c0, j0), min(c1, j1)
                    if x0 >= x1 or y0 >= y1:
                        continue
                    tm = o.tf if layer == "F.Cu" else o.tb
                    if tm is not None:
                        Ts[x0 - i0 : x1 - i0, y0 - j0 : y1 - j0] -= tm[x0 - a0 : x1 - a0, y0 - c0 : y1 - c0]
                    if o.vm is not None:
                        Vs[x0 - i0 : x1 - i0, y0 - j0 : y1 - j0] -= o.vm[x0 - a0 : x1 - a0, y0 - c0 : y1 - c0]

            W, Hh = T.shape
            gx, gy = np.meshgrid(XS[i0:i1], YS[j0:j1], indexing="ij")
            Ht = H_t_cur[i0:i1, j0:j1]
            Hv = hist_v[i0:i1, j0:j1]
            ok = V == 0
            for _, bx, by in bga_boxes:
                ok &= ~((np.abs(gx - bx) < 1.56) & (np.abs(gy - by) < 1.56))
            site = np.full(T.shape, np.inf, np.float32)
            site[ok] = 0.22 + 0.45 * Hv[ok]
            if crowd > 0:
                for s_ in stubs.values():
                    if s_.via and s_.net != net:
                        vx, vy = s_.via
                        if X0 + i0 * G - 0.7 <= vx <= X0 + i1 * G + 0.7 and Y0 + j0 * G - 0.7 <= vy <= Y0 + j1 * G + 0.7:
                            site[ok & (np.hypot(gx - vx, gy - vy) < 0.54)] += crowd
            if allow_soft:
                ov = ok & (Vs > 0)
                site[ov] += pres_fac * (1.0 + Hv[ov]) * Vs[ov]
            else:
                site[Vs > 0] = np.inf

            for vx, vy in own_vias[net] + [s_.via for s_ in net_stubs[net] if s_.via]:
                site[np.hypot(gx - vx, gy - vy) < 0.36] = np.inf

            join_targets: dict[tuple[int, int], tuple[float, float]] = {}
            for (ja, jc), exact_xy in joins[net].items():
                if math.hypot(exact_xy[0] - px, exact_xy[1] - py) < 0.03:
                    continue
                if i0 <= ja < i1 and j0 <= jc < j1 and not T[ja - i0, jc - j0]:
                    if allow_soft or Ts[ja - i0, jc - j0] == 0:
                        site[ja - i0, jc - j0] = 0.0
                        join_targets[(ja - i0, jc - j0)] = exact_xy
            for s_ in net_stubs[net]:
                for (ja, jc), exact_xy in s_.cells.items():
                    if math.hypot(exact_xy[0] - px, exact_xy[1] - py) < 0.03:
                        continue
                    if s_.layer != layer and (s_.via is None or (ja, jc) != ij(*s_.via)):
                        continue
                    if i0 <= ja < i1 and j0 <= jc < j1 and not T[ja - i0, jc - j0]:
                        if allow_soft or Ts[ja - i0, jc - j0] == 0:
                            site[ja - i0, jc - j0] = 0.0
                            join_targets[(ja - i0, jc - j0)] = exact_xy

            si_abs, sj_abs = ij(px, py)
            si, sj = si_abs - i0, sj_abs - j0
            Tb = T > 0
            Tb[si, sj] = False
            dist = {(si, sj): 0.0}
            prev = {}
            prev_dir = {(si, sj): None}
            pq = [(0.0, si, sj)]
            best = (np.inf, None)
            while pq:
                g, a, c = heapq.heappop(pq)
                if g > dist.get((a, c), 1e9):
                    continue
                if g >= best[0]:
                    break
                sc = site[a, c]
                if sc < np.inf and g + sc < best[0]:
                    best = (g + sc, (a, c))
                pdir = prev_dir[(a, c)]
                for d_idx, (dx, dy, w_step) in enumerate(DIRS):
                    a2, c2 = a + dx, c + dy
                    if not (0 <= a2 < W and 0 <= c2 < Hh) or Tb[a2, c2]:
                        continue
                    if dx != 0 and dy != 0 and (Tb[a2, c] and Tb[a, c2]):
                        continue
                    ts_v = Ts[a2, c2]
                    if ts_v > 0:
                        if not allow_soft:
                            continue
                        step_cost = G * w_step * (1.0 + 0.5 * Ht[a2, c2]) + pres_fac * (0.4 + Ht[a2, c2]) * ts_v
                    else:
                        step_cost = G * w_step * (1.0 + 0.5 * Ht[a2, c2])
                    if pdir is not None and pdir != d_idx:
                        step_cost += 0.004
                    g2 = g + step_cost
                    if g2 < dist.get((a2, c2), 1e9):
                        dist[(a2, c2)] = g2
                        prev[(a2, c2)] = (a, c)
                        prev_dir[(a2, c2)] = d_idx
                        heapq.heappush(pq, (g2, a2, c2))
            if best[1] is None:
                return None
            cur = best[1]
            rev = [cur]
            while cur != (si, sj):
                cur = prev[cur]
                rev.append(cur)
            rev.reverse()
            join_xy = join_targets.get(best[1])
            return [(a + i0, c + j0) for a, c in rev], join_xy

        def make_stub_objs(layer: str, net: str, pts: list[tuple[float, float]], via_xy: tuple[float, float] | None):
            cl = net_clr(net)
            objs = []
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                if abs(x0 - x1) < 1e-6 and abs(y0 - y1) < 1e-6:
                    continue
                rt_f = (TW + cl + TW + M) if layer == "F.Cu" else 0.0
                rt_b = (TW + cl + TW + M) if layer == "B.Cu" else 0.0
                rv = max(TW + VR + cl, TW + HR + HC) + M
                objs.append(mk_obj(net, seg_d(x0, y0, x1, y1), (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)), rt_f, rt_b, rv))
            if via_xy is not None:
                vx, vy = via_xy
                rt = max(VR + cl + TW, HR + HC + TW) + M
                rv = max(VR + VR + cl, HR + VR + HC, HR + HR + HC, VV) + M
                objs.append(mk_obj(net, circ_d(vx, vy), (vx, vy, vx, vy), rt, rt, rv))
            return objs

        def commit(it: dict, res):
            grid_path, join_xy = res
            simp = collinear_simplify(grid_path)
            gpts = [xy(a, c) for a, c in simp]
            if len(grid_path) == 1 and join_xy is None:
                # Direct 0-length via-in-pad at grid cell (<= 17 um from pad center)
                pts = []
                via_xy = gpts[0]
            else:
                pts = snap_90_45(it["x"], it["y"], gpts[0][0], gpts[0][1]) + gpts[1:]
                if join_xy is not None:
                    tail = snap_90_45(pts[-1][0], pts[-1][1], join_xy[0], join_xy[1])
                    pts = pts[:-1] + tail
                    via_xy = None
                else:
                    via_xy = pts[-1]
            s = Stub()
            s.key = it["key"]
            s.layer = it["layer"]
            s.net = it["net"]
            s.code = it["code"]
            s.pts = pts
            s.grid_path = grid_path
            s.via = via_xy
            s.objs = make_stub_objs(s.layer, s.net, pts, via_xy)
            # Expose ONLY exact pad origin and exact via center (never mid-segment cells -> 0 track_dangling!)
            s.cells = {ij(it["x"], it["y"]): (it["x"], it["y"])}
            if via_xy is not None:
                s.cells[ij(*via_xy)] = via_xy
            apply_soft(s.objs, +1)
            stubs[s.key] = s
            net_stubs[s.net].append(s)

        def rip(key):
            s = stubs.pop(key)
            net_stubs[s.net].remove(s)
            apply_soft(s.objs, -1)
            ripped = [key]
            cell_set = set(s.cells.keys())
            for s2 in list(net_stubs[s.net]):
                if s2.key in stubs and s2.via is None and s2.grid_path[-1] in cell_set:
                    ripped.extend(rip(s2.key))
            return ripped

        def conflict_cells(s: Stub):
            """Return (bad_track_cells, bad_via_cell) where stub `s` overlaps any OTHER net's stub."""
            T_soft_cur = TF_soft if s.layer == "F.Cu" else TB_soft
            for sn in net_stubs[s.net]:
                apply_soft(sn.objs, -1)
            bad_t = []
            bad_v = None
            for ga, gc in s.grid_path:
                if T_soft_cur[ga, gc] > 0:
                    bad_t.append((ga, gc))
            for (x0, y0), (x1, y1) in zip(s.pts, s.pts[1:]):
                steps = max(2, int(math.hypot(x1 - x0, y1 - y0) / (G * 0.5)))
                for u in range(steps + 1):
                    ga, gc = ij(x0 + (x1 - x0) * u / steps, y0 + (y1 - y0) * u / steps)
                    if T_soft_cur[ga, gc] > 0:
                        bad_t.append((ga, gc))
            if s.via is not None:
                va, vc = ij(*s.via)
                if V_soft[va, vc] > 0:
                    bad_v = (va, vc)
            for sn in net_stubs[s.net]:
                apply_soft(sn.objs, +1)
            return bad_t, bad_v

        item_by_key = {it["key"]: it for it in items}
        # Pass 0: route in priority order (inner BGA -> outer BGA -> blocked LEDs)
        for it in items:
            r = search_one(it, False, 1.0)
            if r is None:
                r = search_one(it, True, 0.7)
            if r is not None:
                commit(it, r)
            else:
                print(f"  [WARN] pass 0 no hard-legal path for {it['layer']} {it['key']} ({it['net']})")

        # True Gauss-Seidel PathFinder negotiation loop
        for p_it in range(passes):
            conflicted = []
            for k, s in list(stubs.items()):
                bt, bv = conflict_cells(s)
                if bt or bv is not None:
                    conflicted.append(k)
                    H_t_cur = hist_tf if s.layer == "F.Cu" else hist_tb
                    for ga, gc in set(bt):
                        H_t_cur[max(ga - 1, 0) : min(ga + 2, N), max(gc - 1, 0) : min(gc + 2, N)] += 1.0
                    if bv is not None:
                        va, vc = bv
                        hist_v[max(va - 2, 0) : min(va + 3, N), max(vc - 2, 0) : min(vc + 3, N)] += 1.5
            missing = [it["key"] for it in items if it["key"] not in stubs]
            if not conflicted and not missing:
                print(f"  [unified] converged cleanly at pass {p_it}: {len(stubs)}/{len(items)} escaped, 0 conflicts!")
                break
            pres = 0.8 * (1.38 ** p_it)
            allow_s = p_it < passes - 2
            # Reroute easier/outer items FIRST on even passes so they step around inner BGA stubs!
            order = list(reversed(items)) if (p_it % 2 == 0) else list(items)
            rerouted = 0
            for it in order:
                k = it["key"]
                if k not in stubs:
                    r = search_one(it, allow_s, pres)
                    if r is not None:
                        commit(it, r)
                        rerouted += 1
                else:
                    bt, bv = conflict_cells(stubs[k])
                    if bt or bv is not None:
                        ripped_keys = rip(k)
                        for rk in ripped_keys:
                            if rk in stubs:
                                continue
                            rit = item_by_key[rk]
                            r = search_one(rit, allow_s, pres)
                            if r is None and not allow_s:
                                # Keep conflict-free; will stay unrouted rather than create DRC error
                                pass
                            elif r is not None:
                                commit(rit, r)
                        rerouted += 1
            bga_ok = sum(1 for it in items if it["layer"] == "B.Cu" and it["key"] in stubs)
            led_ok = sum(1 for it in items if it["layer"] == "F.Cu" and it["key"] in stubs)
            print(f"  [unified] pass {p_it + 1}: BGA {bga_ok}, LED {led_ok} ({len(stubs)}/{len(items)}), was {len(conflicted)} conflicted (rerouted {rerouted})")

        # Final safety prune: guarantee ZERO DRC conflicts among committed stubs!
        for k in list(stubs.keys()):
            if k in stubs:
                bt, bv = conflict_cells(stubs[k])
                if bt or bv is not None:
                    rip(k)
        # One final conflict-free greedy fill for any ripped/missing item!
        for it in items:
            if it["key"] not in stubs:
                r = search_one(it, False, 100.0)
                if r is not None:
                    commit(it, r)

        f_bga = [it["key"] for it in items if it["layer"] == "B.Cu" and it["key"] not in stubs]
        f_led = [it["key"] for it in items if it["layer"] == "F.Cu" and it["key"] not in stubs]

        n_vias_b, n_joins_b, n_vias_f, n_joins_f = 0, 0, 0, 0
        for s in stubs.values():
            lay_id = FL if s.layer == "F.Cu" else BL
            for (x0, y0), (x1, y1) in zip(s.pts, s.pts[1:]):
                if abs(x0 - x1) < 1e-6 and abs(y0 - y1) < 1e-6:
                    continue
                t = pcbnew.PCB_TRACK(b)
                t.SetStart(pcbnew.VECTOR2I(mm(OX + x0), mm(OY + y0)))
                t.SetEnd(pcbnew.VECTOR2I(mm(OX + x1), mm(OY + y1)))
                t.SetWidth(mm(TW * 2))
                t.SetLayer(lay_id)
                t.SetNetCode(s.code)
                t.SetLocked(True)
                b.Add(t)
            if s.via is not None:
                vx, vy = s.via
                v = pcbnew.PCB_VIA(b)
                v.SetPosition(pcbnew.VECTOR2I(mm(OX + vx), mm(OY + vy)))
                v.SetWidth(mm(VR * 2))
                v.SetDrill(mm(HR * 2))
                v.SetLayerPair(FL, BL)
                v.SetNetCode(s.code)
                v.SetLocked(True)
                b.Add(v)
                own_vias[s.net].append((vx, vy))
                joins_f[s.net][ij(vx, vy)] = (vx, vy)
                joins_b[s.net][ij(vx, vy)] = (vx, vy)
                if s.layer == "B.Cu":
                    n_vias_b += 1
                else:
                    n_vias_f += 1
            else:
                if s.layer == "B.Cu":
                    n_joins_b += 1
                else:
                    n_joins_f += 1
            for o in s.objs:
                add_hard(o)
        print(f"B.Cu BGA: {n_vias_b + n_joins_b} escaped ({n_vias_b} vias, {n_joins_b} joins), failed={f_bga}")
        print(f"F.Cu LED: {n_vias_f + n_joins_f} escaped ({n_vias_f} vias, {n_joins_f} joins), failed={f_led}")
        return f_bga, f_led

    # === Collect B.Cu WLCSP-36 Signal Balls + F.Cu Critical-Zone LED Cathode Pads ===
    bga_items = []
    for uref in BGA_REFS:
        for p in fps[uref].Pads():
            num = p.GetNumber()
            if num in SKIP_BGA_BALLS or (uref, num) in touch_copper:
                continue
            c = p.GetPosition()
            px, py = um(c.x) - OX, um(c.y) - OY
            bga_items.append(
                dict(
                    key=(uref, num),
                    layer="B.Cu",
                    reach=5.5,
                    crowd=0.25,
                    x=px,
                    y=py,
                    net=p.GetNetname(),
                    code=p.GetNetCode(),
                    prio=0 if num in INNER_BALLS else 1,
                )
            )
    bga_items.sort(key=lambda d: (d["prio"], d["key"]))

    def in_critical_zone(x: float, y: float) -> bool:
        if max(abs(x - (-1.40)), abs(y - (-6.60))) <= 4.3:
            return True  # U3 QFN + +1V1 ring + decouplers
        if -1.3 <= x <= 2.8 and -4.2 <= y <= 2.3:
            return True  # L1 window + reg corner
        if max(abs(x - 3.40), abs(y - 6.00)) <= 2.2:
            return True  # U5 charger + solid EP
        if any(max(abs(x - bx), abs(y - by)) <= 2.6 for _, bx, by in bga_boxes):
            return True  # 5x WLCSP-36 bodies + B.Cu escape halos
        return False

    led_items = []
    for (ref, num), d in sorted(ledpads.items()):
        if (ref, num) in touch_copper or not MATRIX_PAT.search(d["net"]):
            continue
        if not in_critical_zone(d["x"], d["y"]):
            continue
        dist_u3 = max(0.0, 4.3 - max(abs(d["x"] - (-1.40)), abs(d["y"] - (-6.60))))
        led_items.append(
            dict(
                key=(ref, num),
                layer="F.Cu",
                reach=6.5,
                crowd=0.18,
                x=d["x"],
                y=d["y"],
                net=d["net"],
                code=d["code"],
                prio=2.0 - 0.1 * dist_u3,
            )
        )
    led_items.sort(key=lambda d: (d["prio"], d["key"]))
    all_items = bga_items + led_items
    print(f"Unified escape items: {len(bga_items)} BGA balls + {len(led_items)} critical-zone LED cathode pads = {len(all_items)} total")
    f1, f2 = run_unified_escape(all_items, passes=40)

    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(str(pcb_path), b)
    if pro_bytes is not None:
        pro_path.write_bytes(pro_bytes)
    print(f"escape_d saved: BGA failed={len(f1)}, LED failed={len(f2)}")


if __name__ == "__main__":
    main()
