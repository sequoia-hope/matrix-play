#!/usr/bin/env python3
"""back_silk.py -- Tidy back-side silkscreen reference designators and chip pin-1 marks.

Usage:
    python3 scripts/crunch/silk/back_silk.py BOARD.kicad_pcb OUT.kicad_pcb [--stats JSON]

Rules enforced:
- Leaves copper, zones, vias, component positions/orientations, Edge.Cuts, nets,
  and all front-side silk (F.SilkS and front footprints) completely untouched.
- Uses JLCPCB's smallest supported silkscreen text: 0.80 mm height, 0.10 mm stroke
  (requires JLCPCB "High-precision Printing Silkscreen" / DLP option).
- Places all 24 major back-side reference designators first (U*, SW*, L*, Y*, Q*, J*,
  BT*, TP*), then as many passive designators (C*, R*) as fit cleanly without crowding.
- Keeps >= 0.16 mm clear of all back solder-mask openings (exposed pads), >= 0.20 mm
  clear of all drill holes and board Edge.Cuts, and >= 0.22 mm between text items
  (>= 0.46 mm end-to-end along the reading axis so adjacent labels never read as one),
  plus a soft crowding-repulsion term so labels spread out cleanly and cramped passives
  are omitted rather than crowded.
- Preserves useful chip outlines and ensures every back-side polarized IC/part
  (U*, Q*, L*, 4-pin Y*) has a genuine visual pin-1 mark (dot/triangle/asymmetric L)
  >= 0.16 mm clear of exposed pads.
- Uses only two back-side text rotations (0 deg horizontal left-to-right and -90 deg
  vertical bottom-to-top when viewing the back side), mirrored for B.SilkS.
- Avoids tented vias wherever a clean spot exists, falling back to tented vias only
  when required and reporting exact counts.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pcbnew
from scipy.optimize import LinearConstraint, milp
from scipy.sparse import csc_matrix
from shapely.affinity import translate
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

TEXT_H_MM = 0.80
TEXT_W_MM = 0.80
TEXT_STROKE_MM = 0.10

PAD_CLEAR_MM = 0.16           # JLC min is 0.15 mm
HOLE_CLEAR_MM = 0.20          # Keep clear of NPTH/PTH drills
EDGE_CLEAR_MM = 0.21          # Inside Edge.Cuts centerline (0.16 mm inside inner stroke)
SILK_GRAPHIC_CLEAR_MM = 0.17  # KiCad min_silk_clearance is 0.15 mm
LABEL_CLEAR_MM = 0.22         # Hard minimum stroke-to-stroke gap between labels (DRC is 0.15 mm)
CROWD_DIST_MM = 0.52          # Soft repulsion radius so labels don't crowd each other
READING_GAP_MM = 0.46         # Hard end-to-end gap along reading axis so words never fuse
VIA_PAD_MARGIN_MM = 0.02      # Margin around tented via copper ring

MAJOR_PREFIXES = ("U", "SW", "L", "Y", "Q", "J", "BT", "TP")
PIN1_PREFIXES = ("U", "Q", "L", "Y")

mm = pcbnew.ToMM


def from_mm(v: float) -> int:
    return pcbnew.FromMM(float(v))


def ref_prefix(ref: str) -> str:
    m = re.match(r"[A-Za-z_#]+", ref)
    return m.group(0) if m else ""


def ref_sort_key(ref: str) -> tuple[str, int, str]:
    p = ref_prefix(ref)
    digits = "".join(c for c in ref if c.isdigit())
    return (p, int(digits) if digits else 0, ref)


def poly_from_ps(ps: "pcbnew.SHAPE_POLY_SET") -> Polygon:
    polys = []
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        pts = [(mm(o.CPoint(j).x), mm(o.CPoint(j).y)) for j in range(o.PointCount())]
        if len(pts) >= 3:
            p = Polygon(pts)
            if not p.is_valid:
                p = p.buffer(0)
            if not p.is_empty:
                polys.append(p)
    if not polys:
        return Polygon()
    u = unary_union(polys)
    return u if not u.is_empty else Polygon()


def shape_to_poly(shape, layer: int) -> Polygon:
    ps = pcbnew.SHAPE_POLY_SET()
    shape.TransformShapeToPolygon(ps, layer, 0, from_mm(0.005), pcbnew.ERROR_INSIDE)
    return poly_from_ps(ps)


def get_board_safe_region(board: "pcbnew.BOARD") -> Polygon:
    circles = []
    segs = []
    for d in board.GetDrawings():
        if d.GetLayer() != pcbnew.Edge_Cuts:
            continue
        if hasattr(d, "GetShapeStr") and d.GetShapeStr() == "Circle":
            cx, cy = mm(d.GetCenter().x), mm(d.GetCenter().y)
            r = mm(d.GetRadius())
            circles.append(Point(cx, cy).buffer(r - EDGE_CLEAR_MM, 256))
        else:
            segs.append(shape_to_poly(d, pcbnew.Edge_Cuts))
    if circles:
        return unary_union(circles)
    hull = unary_union(segs).convex_hull
    return hull.buffer(-EDGE_CLEAR_MM)


def collect_obstacles(board: "pcbnew.BOARD"):
    """Collect mask openings, holes, tented vias, and physical bodies of back footprints."""
    mask_raw = []
    hole_raw = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.IsOnLayer(pcbnew.B_Mask):
                mp = poly_from_ps(p.GetEffectivePolygon(pcbnew.B_Mask))
                if not mp.is_empty:
                    mask_raw.append(mp)
            if p.GetDrillSize().x > 0:
                r = max(mm(p.GetDrillSize().x), mm(p.GetDrillSize().y)) / 2.0
                hole_raw.append(Point(mm(p.GetPosition().x), mm(p.GetPosition().y)).buffer(r, 24))

    mask_buffered = [m.buffer(PAD_CLEAR_MM, 8) for m in mask_raw] + [
        h.buffer(HOLE_CLEAR_MM, 12) for h in hole_raw
    ]
    mask_union = unary_union(mask_raw + hole_raw) if (mask_raw or hole_raw) else Polygon()

    via_rings = []
    via_drills = []
    for t in board.GetTracks():
        if t.Type() != pcbnew.PCB_VIA_T:
            continue
        vx, vy = mm(t.GetPosition().x), mm(t.GetPosition().y)
        vr = mm(t.GetWidth(pcbnew.B_Cu)) / 2.0
        dr = mm(t.GetDrillValue()) / 2.0
        if not t.IsTented(pcbnew.B_Mask):
            mask_buffered.append(Point(vx, vy).buffer(vr + PAD_CLEAR_MM, 12))
            mask_union = unary_union([mask_union, Point(vx, vy).buffer(vr, 12)])
        else:
            via_rings.append(Point(vx, vy).buffer(vr + VIA_PAD_MARGIN_MM, 8))
            via_drills.append(Point(vx, vy).buffer(dr, 8))

    back_fps = [
        fp for fp in board.GetFootprints()
        if fp.IsFlipped() and fp.GetReference() and not fp.GetReference().startswith("#")
    ]

    bodies = {}
    courtyards = {}
    for fp in back_fps:
        ref = fp.GetReference()
        fp.BuildCourtyardCaches()
        cy = poly_from_ps(fp.GetCourtyard(pcbnew.B_CrtYd))
        courtyards[ref] = cy

        parts = []
        for p in fp.Pads():
            if p.IsOnLayer(pcbnew.B_Cu) or p.IsOnLayer(pcbnew.B_Mask):
                lyr = pcbnew.B_Cu if p.IsOnLayer(pcbnew.B_Cu) else pcbnew.B_Mask
                mp = poly_from_ps(p.GetEffectivePolygon(lyr))
                if not mp.is_empty:
                    parts.append(mp)
            elif p.GetDrillSize().x > 0:
                r = mm(p.GetDrillSize().x) / 2.0
                parts.append(Point(mm(p.GetPosition().x), mm(p.GetPosition().y)).buffer(r, 12))
        for g in fp.GraphicalItems():
            if g.GetLayer() == pcbnew.B_Fab and g.GetClass() != "PCB_TEXT":
                gp = shape_to_poly(g, pcbnew.B_Fab)
                if not gp.is_empty:
                    parts.append(gp)
        if parts:
            bodies[ref] = unary_union(parts).convex_hull
        elif not cy.is_empty:
            bodies[ref] = cy
        else:
            bb = fp.GetBoundingBox(False, False)
            bodies[ref] = Polygon([
                (mm(bb.GetLeft()), mm(bb.GetTop())),
                (mm(bb.GetRight()), mm(bb.GetTop())),
                (mm(bb.GetRight()), mm(bb.GetBottom())),
                (mm(bb.GetLeft()), mm(bb.GetBottom())),
            ])

    return back_fps, mask_union, mask_buffered, via_rings, via_drills, bodies, courtyards


def clean_footprint_silk_and_pin1(
    board: "pcbnew.BOARD",
    back_fps: list,
    mask_union: Polygon,
    safe_region: Polygon,
    via_rings: list[Polygon],
    bodies: dict[str, Polygon],
):
    """Tidy back-side footprint graphic silk and ensure every chip has an unambiguous pin-1 mark."""
    for d in list(board.GetDrawings()):
        if d.GetLayer() == pcbnew.B_SilkS:
            board.RemoveNative(d)

    removed_graphics = 0
    kept_shapes: list[tuple[str, object, Polygon, str]] = []

    for fp in back_fps:
        ref = fp.GetReference()
        pfx = ref_prefix(ref)
        for fld in [fp.Value()] + list(fp.GetFields()):
            if fld.GetName().lower() == "reference":
                continue
            if fld.GetLayer() == pcbnew.B_SilkS:
                fld.SetVisible(False)

        for g in list(fp.GraphicalItems()):
            if g.GetLayer() != pcbnew.B_SilkS or g.GetClass() == "PCB_FIELD":
                continue
            if g.GetClass() == "PCB_TEXT":
                if "${" not in g.GetText():
                    fp.RemoveNative(g)
                    removed_graphics += 1
                else:
                    g.SetVisible(False)
                continue

            if pfx in ("C", "R", "TP"):
                fp.RemoveNative(g)
                removed_graphics += 1
                continue

            gp = shape_to_poly(g, pcbnew.B_SilkS)
            if gp.is_empty:
                fp.RemoveNative(g)
                removed_graphics += 1
                continue

            if gp.distance(mask_union) < (PAD_CLEAR_MM - 0.005) or not safe_region.contains(gp):
                fp.RemoveNative(g)
                removed_graphics += 1
                continue

            s_type = g.GetShapeStr()
            bb = gp.bounds
            span = max(bb[2] - bb[0], bb[3] - bb[1])
            bd = bodies[ref].bounds
            pkg_span = max(bd[2] - bd[0], bd[3] - bd[1])
            if pfx == "U" and pkg_span < 1.8 and s_type == "Line":
                fp.RemoveNative(g)
                removed_graphics += 1
                continue
            if pfx == "U" and span > 5.0 and s_type == "Line":
                fp.RemoveNative(g)
                removed_graphics += 1
                continue

            kept_shapes.append((ref, g, gp, s_type))

    final_kept: list[tuple[str, Polygon, str]] = []
    for ref_i, g_i, gp_i, st_i in kept_shapes:
        if any(ref_i != ref_j and gp_i.distance(gp_j) < 0.155 for ref_j, gp_j, _ in final_kept):
             board_fp = next(fp for fp in back_fps if fp.GetReference() == ref_i)
             board_fp.RemoveNative(g_i)
             removed_graphics += 1
        else:
            final_kept.append((ref_i, gp_i, st_i))

    via_tree = STRtree(via_rings) if via_rings else None
    all_body_keepouts = [b.buffer(0.02, 4) for b in bodies.values()]
    body_ko_tree = STRtree(all_body_keepouts) if all_body_keepouts else None
    pin1_added = []
    pin1_verified = []

    for fp in sorted(back_fps, key=lambda f: ref_sort_key(f.GetReference())):
        ref = fp.GetReference()
        pfx = ref_prefix(ref)
        if pfx not in PIN1_PREFIXES:
            continue
        pads = list(fp.Pads())
        p1_pads = [p for p in pads if p.GetNumber() == "1"]
        other_pads = [p for p in pads if p.GetNumber() not in ("1", "")]
        if not p1_pads or not other_pads:
            continue

        fpx, fpy = mm(fp.GetPosition().x), mm(fp.GetPosition().y)
        p1_pads.sort(key=lambda p: -math.hypot(mm(p.GetPosition().x) - fpx, mm(p.GetPosition().y) - fpy))
        p1 = p1_pads[0]
        p1x, p1y = mm(p1.GetPosition().x), mm(p1.GetPosition().y)
        p1_bb = p1.GetBoundingBox()
        p1_half = max(mm(p1_bb.GetWidth()), mm(p1_bb.GetHeight())) / 2.0
        other_pts = [
            (mm(q.GetPosition().x), mm(q.GetPosition().y))
            for q in other_pads
            if math.hypot(mm(q.GetPosition().x) - p1x, mm(q.GetPosition().y) - p1y) > 0.05
            and math.hypot(mm(q.GetPosition().x) - fpx, mm(q.GetPosition().y) - fpy) > 0.05
        ]
        if not other_pts:
            continue

        # Only count an existing shape as a genuine visual pin-1 indicator if it is a Circle/Polygon,
        # OR a 2-line perpendicular corner L-bracket (e.g. Y1) whose combined centroid sits at pad 1.
        owner_shapes = [(gp, st) for r_o, gp, st in final_kept if r_o == ref]
        has_mark = False
        for gp, st in owner_shapes:
            if st not in ("Circle", "Polygon"):
                continue
            cx, cy = gp.centroid.x, gp.centroid.y
            d1 = math.hypot(cx - p1x, cy - p1y)
            if d1 <= p1_half + 1.15 and all(d1 + 0.02 < math.hypot(cx - ox, cy - oy) for ox, oy in other_pts):
                has_mark = True
                break

        if not has_mark and len(owner_shapes) == 2 and all(st == "Line" for _, st in owner_shapes):
            u_lines = unary_union([gp for gp, _ in owner_shapes])
            ucx, ucy = u_lines.centroid.x, u_lines.centroid.y
            d1 = math.hypot(ucx - p1x, ucy - p1y)
            if d1 <= p1_half + 0.60 and all(d1 + 0.30 < math.hypot(ucx - ox, ucy - oy) for ox, oy in other_pts):
                has_mark = True

        if has_mark:
            pin1_verified.append(ref)
            continue

        # Outward cardinal direction from package center through pad 1
        vx_out, vy_out = p1x - fpx, p1y - fpy
        if abs(vx_out) >= abs(vy_out):
            out_ang = 0.0 if vx_out >= 0 else math.pi
        else:
            out_ang = math.pi / 2.0 if vy_out >= 0 else -math.pi / 2.0

        # Solid 0.26 mm diameter filled silk dot (width 0.13 mm, radius 0.065 mm -> outer radius 0.13 mm)
        dot_r = 0.13
        best_dot = None
        for r_dist in np.linspace(0.24, 1.05, 34):
            for d_ang in np.linspace(-math.pi * 0.85, math.pi * 0.85, 69):
                ang = out_ang + float(d_ang)
                dx = float(round(p1x + float(r_dist) * math.cos(ang), 3))
                dy = float(round(p1y + float(r_dist) * math.sin(ang), 3))
                d1 = math.hypot(dx - p1x, dy - p1y)
                if d1 > p1_half + 1.10:
                    continue
                min_other = min(math.hypot(dx - ox, dy - oy) for ox, oy in other_pts)
                if d1 + 0.12 >= min_other:
                    continue
                dot_poly = Point(dx, dy).buffer(dot_r, 24)
                if not safe_region.contains(dot_poly):
                    continue
                if dot_poly.distance(mask_union) < PAD_CLEAR_MM:
                    continue
                if body_ko_tree is not None and any(
                    all_body_keepouts[k].intersects(dot_poly) for k in body_ko_tree.query(dot_poly)
                ):
                    continue
                if any(dot_poly.distance(gp) < SILK_GRAPHIC_CLEAR_MM for _, gp, _ in final_kept):
                    continue
                nvias = (
                    sum(1 for k in via_tree.query(dot_poly) if via_rings[k].intersects(dot_poly))
                    if via_tree is not None
                    else 0
                )
                score = (nvias * 8.0) + d1 + 0.55 * abs(float(d_ang)) - 0.12 * min(min_other - d1, 0.5)
                if best_dot is None or score < best_dot[0]:
                    best_dot = (score, dx, dy, dot_poly, nvias)

        if best_dot is not None:
            _, dx, dy, dot_poly, nvias = best_dot
            s = pcbnew.PCB_SHAPE(board)
            s.SetShape(pcbnew.SHAPE_T_CIRCLE)
            s.SetLayer(pcbnew.B_SilkS)
            s.SetFilled(True)
            s.SetWidth(from_mm(0.13))
            s.SetCenter(pcbnew.VECTOR2I(from_mm(dx), from_mm(dy)))
            s.SetEnd(pcbnew.VECTOR2I(from_mm(dx + 0.065), from_mm(dy)))
            board.Add(s)
            final_kept.append((ref, dot_poly, "Circle"))
            pin1_added.append((ref, dx, dy, nvias))
            pin1_verified.append(ref)

    return removed_graphics, [gp for _, gp, _ in final_kept], pin1_verified, pin1_added


def build_text_templates(board: "pcbnew.BOARD", refs: list[str]):
    """Render exact KiCad stroke polygons for each ref at 0 deg and -90 deg, normalized to ink bbox center."""
    probe = pcbnew.PCB_TEXT(board)
    probe.SetLayer(pcbnew.B_SilkS)
    probe.SetMirrored(True)
    probe.SetKeepUpright(False)
    probe.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    probe.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    probe.SetTextSize(pcbnew.VECTOR2I(from_mm(TEXT_W_MM), from_mm(TEXT_H_MM)))
    probe.SetTextThickness(from_mm(TEXT_STROKE_MM))

    templates = {}
    for ref in refs:
        for rot in (0.0, -90.0):
            probe.SetText(ref)
            probe.SetPosition(pcbnew.VECTOR2I(from_mm(100.0), from_mm(100.0)))
            probe.SetTextAngleDegrees(rot)
            ps = pcbnew.SHAPE_POLY_SET()
            probe.TransformTextToPolySet(ps, 0, from_mm(0.005), pcbnew.ERROR_INSIDE)
            p = poly_from_ps(ps)
            bx0, by0, bx1, by1 = p.bounds
            icx, icy = (bx0 + bx1) / 2.0, (by0 + by1) / 2.0
            norm_poly = translate(p, -icx, -icy)
            anchor_dx, anchor_dy = 100.0 - icx, 100.0 - icy
            templates[(ref, rot)] = (norm_poly, anchor_dx, anchor_dy, bx1 - bx0, by1 - by0)
    return templates


def generate_candidates(
    back_fps: list,
    templates: dict,
    safe_region: Polygon,
    mask_buffered: list[Polygon],
    silk_graphics: list[Polygon],
    via_rings: list[Polygon],
    via_drills: list[Polygon],
    bodies: dict[str, Polygon],
    courtyards: dict[str, Polygon],
):
    """Generate clean, human-aligned candidate placements for every back-side component."""
    mask_tree = STRtree(mask_buffered) if mask_buffered else None
    silk_buf = [g.buffer(SILK_GRAPHIC_CLEAR_MM, 6) for g in silk_graphics]
    silk_tree = STRtree(silk_buf) if silk_buf else None
    via_ring_tree = STRtree(via_rings) if via_rings else None
    via_drill_tree = STRtree(via_drills) if via_drills else None
    via_drills_buf = [vd.buffer(0.035, 8) for vd in via_drills]
    via_drill_buf_tree = STRtree(via_drills_buf) if via_drills_buf else None

    body_refs = list(bodies.keys())
    body_list = [bodies[r] for r in body_refs]
    body_keepout = [b.buffer(0.055, 4) for b in body_list]
    body_tree = STRtree(body_list)
    body_ko_tree = STRtree(body_keepout)

    cy_refs = [r for r in body_refs if not courtyards[r].is_empty]
    cy_list = [courtyards[r] for r in cy_refs]
    cy_tree = STRtree(cy_list) if cy_list else None

    candidates_by_ref: dict[str, list[dict]] = {}

    for fp in sorted(back_fps, key=lambda f: ref_sort_key(f.GetReference())):
        ref = fp.GetReference()
        is_major = ref.startswith(MAJOR_PREFIXES)
        bd = bodies[ref]
        minx, miny, maxx, maxy = bd.bounds
        cx, cy = (minx + maxx) / 2.0, (miny + maxy) / 2.0
        bw, bh = maxx - minx, maxy - miny

        gaps = (
            [0.06, 0.10, 0.14, 0.18, 0.23, 0.29, 0.36, 0.45, 0.56, 0.70, 0.86, 1.05, 1.25]
            if is_major
            else [0.10, 0.14, 0.18, 0.23, 0.29, 0.36, 0.45, 0.55]
        )
        lat_step = 0.06 if is_major else 0.08
        max_edge_dist = 1.38 if is_major else 0.62
        assoc_center_margin = 0.03 if is_major else 0.14
        assoc_edge_margin = 0.01 if is_major else 0.06

        raw_trials = []
        for rot in (0.0, -90.0):
            tpl, adx, ady, tw, th = templates[(ref, rot)]
            # Keep lateral overhang modest so labels sit beside the part rather than hanging off a far corner
            x_half = max(0.0, (bw - tw) / 2.0) + (0.48 if is_major else 0.36)
            n_x = max(1, int(round(x_half / lat_step)))
            lat_xs = sorted({0.0} | {round(k * lat_step, 3) for k in range(-n_x, n_x + 1)})

            y_half = max(0.0, (bh - th) / 2.0) + (0.48 if is_major else 0.36)
            n_y = max(1, int(round(y_half / lat_step)))
            lat_ys = sorted({0.0} | {round(k * lat_step, 3) for k in range(-n_y, n_y + 1)})

            for g in gaps:
                for dx in lat_xs:
                    raw_trials.append((rot, "N", g, abs(dx), round(cx + dx, 3), round(miny - g - th / 2.0, 3)))
                    raw_trials.append((rot, "S", g, abs(dx), round(cx + dx, 3), round(maxy + g + th / 2.0, 3)))
                for dy in lat_ys:
                    raw_trials.append((rot, "W", g, abs(dy), round(minx - g - tw / 2.0, 3), round(cy + dy, 3)))
                    raw_trials.append((rot, "E", g, abs(dy), round(maxx + g + tw / 2.0, 3), round(cy + dy, 3)))

        seen_xy = set()
        valid = []
        for rot, side, g_nom, lat_off, x, y in raw_trials:
            key = (rot, round(x * 20), round(y * 20))
            if key in seen_xy:
                continue
            seen_xy.add(key)

            tpl, adx, ady, tw, th = templates[(ref, rot)]
            tp = translate(tpl, x, y)

            if not safe_region.contains(tp):
                continue
            if mask_tree is not None and any(mask_buffered[k].intersects(tp) for k in mask_tree.query(tp)):
                continue
            if silk_tree is not None and any(silk_buf[k].intersects(tp) for k in silk_tree.query(tp)):
                continue
            if any(body_keepout[k].intersects(tp) for k in body_ko_tree.query(tp)):
                continue

            d_own = bd.distance(tp)
            if d_own > max_edge_dist:
                continue

            c_pt = Point(x, y)
            dc_own = bd.distance(c_pt)
            near_b = body_tree.query(tp.buffer(3.0))
            dc_other = min((body_list[k].distance(c_pt) for k in near_b if body_refs[k] != ref), default=99.0)
            de_other = min((body_list[k].distance(tp) for k in near_b if body_refs[k] != ref), default=99.0)
            if dc_other < dc_own + assoc_center_margin:
                continue
            if de_other < d_own + assoc_edge_margin:
                continue

            cy_overlaps = 0
            cy_assoc_ok = True
            if cy_tree is not None:
                cy_overlaps = sum(1 for k in cy_tree.query(tp) if cy_list[k].intersects(tp))
                own_cy = courtyards[ref]
                if not own_cy.is_empty:
                    d_cy_own = own_cy.distance(c_pt)
                    near_c = cy_tree.query(tp.buffer(3.0))
                    d_cy_other = min((cy_list[k].distance(c_pt) for k in near_c if cy_refs[k] != ref), default=99.0)
                    if d_cy_other + 0.05 < d_cy_own:
                        cy_assoc_ok = False

            if not is_major and not cy_assoc_ok:
                continue

            n_via_rings = (
                sum(1 for k in via_ring_tree.query(tp) if via_rings[k].intersects(tp))
                if via_ring_tree is not None
                else 0
            )
            n_via_drills = (
                sum(1 for k in via_drill_tree.query(tp) if via_drills[k].intersects(tp))
                if via_drill_tree is not None
                else 0
            )
            n_via_drills_buf = (
                sum(1 for k in via_drill_buf_tree.query(tp) if via_drills_buf[k].intersects(tp))
                if via_drill_buf_tree is not None
                else 0
            )

            # Never let a passive cross a tented via drill (even buffered) or span 2+ tented via rings
            if not is_major and (n_via_rings > 1 or n_via_drills_buf > 0):
                continue

            base = 100000.0 if is_major else 135.0
            # Strongly prefer 0 vias, and strictly avoid via drill holes wherever any drill-free spot exists
            via_pen = (
                (n_via_rings * 4500.0 + n_via_drills_buf * 6000.0 + n_via_drills * 25000.0)
                if is_major
                else (n_via_rings * 82.0)
            )
            cy_pen = (
                (cy_overlaps * 800.0 + (0.0 if cy_assoc_ok else 1200.0))
                if is_major
                else (cy_overlaps * 16.0)
            )

            # Strong cardinal centering preference (especially on wide parts like BT1, J1, U*)
            overhang = max(0.0, lat_off - max(0.0, ((bw - tw) if side in ("N", "S") else (bh - th)) / 2.0))
            center_bonus = 24.0 if lat_off < 0.02 else max(0.0, 14.0 - 22.0 * lat_off)
            overhang_pen = 35.0 * overhang
            dist_pen = 22.0 * abs(d_own - 0.20)
            sep_bonus = min(dc_other - dc_own, 1.2) * 14.0 + min(de_other - d_own, 0.8) * 10.0
            rot_bonus = 5.0 if rot == 0.0 else 0.0

            score = base - via_pen - cy_pen + center_bonus - overhang_pen - dist_pen + sep_bonus + rot_bonus
            if not is_major and score < 30.0:
                continue

            valid.append({
                "ref": ref,
                "is_major": is_major,
                "rot": rot,
                "side": side,
                "x": x,
                "y": y,
                "adx": adx,
                "ady": ady,
                "tw": tw,
                "th": th,
                "poly": tp,
                "bounds": tp.bounds,
                "d_own": d_own,
                "n_vias": n_via_rings,
                "n_drills": n_via_drills,
                "cy_overlaps": cy_overlaps,
                "lat_off": lat_off,
                "score": score,
            })

        valid.sort(key=lambda c: -c["score"])
        kept_cands = []
        buckets: dict[tuple, list] = {}
        for c in valid:
            bkey = (c["rot"], c["side"], c["n_vias"] == 0)
            lst = buckets.setdefault(bkey, [])
            if len(lst) < 6 and all(math.hypot(c["x"] - o["x"], c["y"] - o["y"]) >= 0.11 for o in lst):
                lst.append(c)
                kept_cands.append(c)
        kept_cands.sort(key=lambda c: -c["score"])
        candidates_by_ref[ref] = kept_cands[:36]

    return candidates_by_ref


def solve_global_placement(candidates_by_ref: dict[str, list[dict]], bodies: dict[str, Polygon]):
    """Solve exact global placement + alignment bonuses + anti-crowding repulsion via HiGHS MILP."""
    all_cands = []
    comp_groups = []
    for ref in sorted(candidates_by_ref.keys(), key=ref_sort_key):
        cands = candidates_by_ref[ref]
        if not cands:
            continue
        idxs = list(range(len(all_cands), len(all_cands) + len(cands)))
        all_cands.extend(cands)
        comp_groups.append((ref, idxs))

    n_cand = len(all_cands)
    if n_cand == 0:
        return []

    buf_polys = [c["poly"].buffer(CROWD_DIST_MM / 2.0 + 0.05, 6) for c in all_cands]
    cand_tree = STRtree(buf_polys)

    conflict_pairs = set()
    crowd_pairs: list[tuple[int, int, float]] = []

    for i, ci in enumerate(all_cands):
        bx0, by0, bx1, by1 = ci["bounds"]
        q_box = Point((bx0 + bx1) / 2.0, (by0 + by1) / 2.0).buffer(
            max(bx1 - bx0, by1 - by0) / 2.0 + max(READING_GAP_MM, CROWD_DIST_MM) + 0.15, 4
        )
        for j in cand_tree.query(q_box):
            if j <= i:
                continue
            cj = all_cands[j]
            if ci["ref"] == cj["ref"]:
                continue

            dist = ci["poly"].distance(cj["poly"])
            if dist < LABEL_CLEAR_MM:
                conflict_pairs.add((i, j))
                continue

            ox0, oy0, ox1, oy1 = cj["bounds"]
            fused = False
            if ci["rot"] == 0.0 and cj["rot"] == 0.0:
                if (min(by1, oy1) - max(by0, oy0)) > -0.18 and max(ox0 - bx1, bx0 - ox1) < READING_GAP_MM:
                    fused = True
            elif ci["rot"] == -90.0 and cj["rot"] == -90.0:
                if (min(bx1, ox1) - max(bx0, ox0)) > -0.18 and max(oy0 - by1, by0 - oy1) < READING_GAP_MM:
                    fused = True
            if fused:
                conflict_pairs.add((i, j))
                continue

            # Soft crowding repulsion for close labels in [LABEL_CLEAR_MM, CROWD_DIST_MM)
            if dist < CROWD_DIST_MM:
                pen = 38.0 * (CROWD_DIST_MM - dist) / (CROWD_DIST_MM - LABEL_CLEAR_MM)
                if pen >= 3.0:
                    crowd_pairs.append((i, j, pen))

    # Row/column alignment bonus for neat neighboring part groups
    align_bonuses = []
    ref_to_idxs = dict(comp_groups)
    refs_list = [r for r, _ in comp_groups]
    part_centers = {
        r: ((bodies[r].bounds[0] + bodies[r].bounds[2]) / 2.0, (bodies[r].bounds[1] + bodies[r].bounds[3]) / 2.0)
        for r in refs_list
    }
    for a_idx in range(len(refs_list)):
        ra = refs_list[a_idx]
        xa, ya = part_centers[ra]
        for b_idx in range(a_idx + 1, len(refs_list)):
            rb = refs_list[b_idx]
            xb, yb = part_centers[rb]
            same_row = abs(ya - yb) <= 0.15 and 0.8 <= abs(xa - xb) <= 3.0
            same_col = abs(xa - xb) <= 0.15 and 0.8 <= abs(ya - yb) <= 3.0
            if not (same_row or same_col):
                continue
            buckets_a: dict[tuple, list[int]] = {}
            buckets_b: dict[tuple, list[int]] = {}
            for i in ref_to_idxs[ra]:
                c = all_cands[i]
                line_coord = round(c["y"] * 10) if same_row else round(c["x"] * 10)
                buckets_a.setdefault((c["rot"], c["side"], line_coord), []).append(i)
            for j in ref_to_idxs[rb]:
                c = all_cands[j]
                line_coord = round(c["y"] * 10) if same_row else round(c["x"] * 10)
                buckets_b.setdefault((c["rot"], c["side"], line_coord), []).append(j)
            for key in set(buckets_a.keys()) & set(buckets_b.keys()):
                ia = buckets_a[key]
                jb = buckets_b[key]
                if any((min(i, j), max(i, j)) not in conflict_pairs for i in ia for j in jb):
                    align_bonuses.append((ia, jb, 20.0))

    n_bonus = len(align_bonuses)
    n_crowd = len(crowd_pairs)
    n_vars = n_cand + n_bonus + n_crowd

    c_obj = np.zeros(n_vars, dtype=float)
    for i, cand in enumerate(all_cands):
        c_obj[i] = -cand["score"]
    for k, (_, _, bval) in enumerate(align_bonuses):
        c_obj[n_cand + k] = -bval
    for m, (_, _, pen) in enumerate(crowd_pairs):
        c_obj[n_cand + n_bonus + m] = +pen  # Minimize +pen * w_m <=> subtract pen when both active

    rows = []
    cols = []
    vals = []
    ubs = []
    row_idx = 0

    for _, idxs in comp_groups:
        for i in idxs:
            rows.append(row_idx)
            cols.append(i)
            vals.append(1.0)
        ubs.append(1.0)
        row_idx += 1

    for i, j in sorted(conflict_pairs):
        rows.extend([row_idx, row_idx])
        cols.extend([i, j])
        vals.extend([1.0, 1.0])
        ubs.append(1.0)
        row_idx += 1

    for k, (ia, jb, _) in enumerate(align_bonuses):
        z_col = n_cand + k
        rows.append(row_idx)
        cols.append(z_col)
        vals.append(1.0)
        for i in ia:
            rows.append(row_idx)
            cols.append(i)
            vals.append(-1.0)
        ubs.append(0.0)
        row_idx += 1

        rows.append(row_idx)
        cols.append(z_col)
        vals.append(1.0)
        for j in jb:
            rows.append(row_idx)
            cols.append(j)
            vals.append(-1.0)
        ubs.append(0.0)
        row_idx += 1

    # Crowding variables w_m >= x_i + x_j - 1  <=>  x_i + x_j - w_m <= 1, with w_m >= 0 continuous
    for m, (i, j, _) in enumerate(crowd_pairs):
        w_col = n_cand + n_bonus + m
        rows.extend([row_idx, row_idx, row_idx])
        cols.extend([i, j, w_col])
        vals.extend([1.0, 1.0, -1.0])
        ubs.append(1.0)
        row_idx += 1

    mat = csc_matrix((vals, (rows, cols)), shape=(row_idx, n_vars))
    lbs = np.full(row_idx, -np.inf)
    constraints = LinearConstraint(mat, lbs, np.array(ubs, dtype=float))

    integrality = np.zeros(n_vars, dtype=int)
    integrality[: n_cand + n_bonus] = 1  # Candidate & bonus vars binary; crowd slack w_m continuous >= 0!

    res = milp(
        c=c_obj,
        integrality=integrality,
        constraints=constraints,
        options={"time_limit": 6.0, "mip_rel_gap": 2e-3},
    )
    if not res.success and res.x is None:
        raise RuntimeError(f"MILP solver failed: {res.message}")

    chosen = [all_cands[i] for i in range(n_cand) if res.x[i] > 0.5]
    return chosen


def apply_placements(board: "pcbnew.BOARD", back_fps: list, chosen: list[dict]):
    chosen_map = {c["ref"]: c for c in chosen}
    kept_refs = []
    dropped_refs = []

    for fp in sorted(back_fps, key=lambda f: ref_sort_key(f.GetReference())):
        ref = fp.GetReference()
        rf = fp.Reference()
        if ref in chosen_map:
            c = chosen_map[ref]
            rf.SetLayer(pcbnew.B_SilkS)
            rf.SetVisible(True)
            rf.SetMirrored(True)
            rf.SetKeepUpright(False)
            rf.SetItalic(False)
            rf.SetBold(False)
            rf.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
            rf.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
            rf.SetTextSize(pcbnew.VECTOR2I(from_mm(TEXT_W_MM), from_mm(TEXT_H_MM)))
            rf.SetTextThickness(from_mm(TEXT_STROKE_MM))
            ax = c["x"] + c["adx"]
            ay = c["y"] + c["ady"]
            rf.SetPosition(pcbnew.VECTOR2I(from_mm(ax), from_mm(ay)))
            rf.SetTextAngleDegrees(c["rot"])
            kept_refs.append(ref)
        else:
            rf.SetLayer(pcbnew.B_SilkS)
            rf.SetVisible(False)
            dropped_refs.append(ref)

    return kept_refs, dropped_refs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", type=Path, help="Input .kicad_pcb file")
    ap.add_argument("out", type=Path, help="Output .kicad_pcb file")
    ap.add_argument("--stats", type=Path, help="Optional JSON path to write detailed summary statistics")
    args = ap.parse_args()

    board = pcbnew.LoadBoard(str(args.src))
    safe_region = get_board_safe_region(board)
    back_fps, mask_union, mask_buffered, via_rings, via_drills, bodies, courtyards = collect_obstacles(board)

    removed_graphics, silk_graphics, pin1_verified, pin1_added = clean_footprint_silk_and_pin1(
        board, back_fps, mask_union, safe_region, via_rings, bodies
    )

    all_refs = [fp.GetReference() for fp in back_fps]
    templates = build_text_templates(board, all_refs)
    candidates_by_ref = generate_candidates(
        back_fps, templates, safe_region, mask_buffered, silk_graphics,
        via_rings, via_drills, bodies, courtyards
    )

    chosen = solve_global_placement(candidates_by_ref, bodies)
    kept_refs, dropped_refs = apply_placements(board, back_fps, chosen)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(args.out), board)

    majors_all = sorted([r for r in all_refs if r.startswith(MAJOR_PREFIXES)], key=ref_sort_key)
    passives_all = sorted([r for r in all_refs if not r.startswith(MAJOR_PREFIXES)], key=ref_sort_key)
    majors_kept = [r for r in majors_all if r in set(kept_refs)]
    majors_dropped = [r for r in majors_all if r not in set(kept_refs)]
    passives_kept = [r for r in passives_all if r in set(kept_refs)]
    passives_dropped = [r for r in passives_all if r not in set(kept_refs)]

    via_overlaps = [
        (c["ref"], c["n_vias"], c["n_drills"])
        for c in sorted(chosen, key=lambda x: ref_sort_key(x["ref"]))
        if c["n_vias"] > 0
    ]
    rot_counts = {}
    for c in chosen:
        rot_counts[str(c["rot"])] = rot_counts.get(str(c["rot"]), 0) + 1

    via_tree = STRtree(via_rings) if via_rings else None
    graphic_via_shapes = 0
    if via_tree is not None:
        for gp in silk_graphics:
            if any(via_rings[k].intersects(gp) for k in via_tree.query(gp)):
                graphic_via_shapes += 1

    stats = {
        "text_height_mm": TEXT_H_MM,
        "text_width_mm": TEXT_W_MM,
        "text_stroke_mm": TEXT_STROKE_MM,
        "back_parts_total": len(all_refs),
        "majors_total": len(majors_all),
        "majors_kept": len(majors_kept),
        "majors_kept_list": majors_kept,
        "majors_dropped_list": majors_dropped,
        "passives_total": len(passives_all),
        "passives_kept": len(passives_kept),
        "passives_dropped": len(passives_dropped),
        "passives_kept_list": passives_kept,
        "passives_dropped_list": passives_dropped,
        "total_kept": len(kept_refs),
        "total_dropped": len(dropped_refs),
        "designators_over_tented_vias_count": len(via_overlaps),
        "designators_over_tented_vias": [
            {"ref": r, "via_rings": nv, "via_drills": nd} for r, nv, nd in via_overlaps
        ],
        "graphic_shapes_kept": len(silk_graphics),
        "graphic_shapes_removed": removed_graphics,
        "graphic_shapes_over_tented_vias": graphic_via_shapes,
        "pin1_verified": pin1_verified,
        "pin1_dots_added": [
            {"ref": r, "x": x, "y": y, "tented_vias": nv} for r, x, y, nv in pin1_added
        ],
        "rotation_counts": rot_counts,
    }

    if args.stats:
        args.stats.parent.mkdir(parents=True, exist_ok=True)
        args.stats.write_text(json.dumps(stats, indent=2) + "\n")

    print(
        f"back_silk: {len(majors_kept)}/{len(majors_all)} majors kept, "
        f"{len(passives_kept)}/{len(passives_all)} passives kept "
        f"({len(kept_refs)}/{len(all_refs)} total, {len(dropped_refs)} dropped); "
        f"{len(via_overlaps)} designators over tented vias; "
        f"pin-1 verified on {len(pin1_verified)} parts ({len(pin1_added)} dots added)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
