#!/usr/bin/env python3
"""pcb_gen.py -- 4-layer PCB generator for hw/parallelogram/<variant>/parallelogram.kicad_pcb.

One pcbnew stage per process (always restores .kicad_pro and calls os._exit(0)):
    python3 scripts/parallelogram/pcb_gen.py <variant> outline
    python3 scripts/parallelogram/pcb_gen.py <variant> stack
    python3 scripts/parallelogram/pcb_gen.py <variant> sync
    python3 scripts/parallelogram/pcb_gen.py <variant> place
    python3 scripts/parallelogram/pcb_gen.py <variant> zones
    python3 scripts/parallelogram/pcb_gen.py <variant> models
    python3 scripts/parallelogram/pcb_gen.py <variant> post_silk
"""
import json
import math
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude/skills/pcb-design/scripts"))
sys.path.insert(0, str(ROOT / "scripts/parallelogram"))

from config import (  # noqa: E402
    CELL_CENTER,
    CELL_H,
    CELL_W,
    CORNER_R,
    HALF_EDGE,
    HALF_W,
    OX,
    OY,
    SKEW,
    VARIANTS,
    VariantSpec,
    build_led_cells,
)

REF_PCB = ROOT / "hw/round-pendant/d/round-pendant.kicad_pcb"
VENDOR_ZONES = ROOT / "scripts/crunch/placement/vendor_zones.json"
SKEW_DEG = math.degrees(math.atan(SKEW))  # 17.7447 deg

# Translation of the proven RP2350 + regulator + crystal + flash + charger + ESD + LDO macro from Variant D:
MACRO_DX = 1.40
MACRO_DY = 13.00
MACRO_REFS = {
    "U3", "U4", "U5", "U6", "U7", "U8", "L1", "Y1",
    *(f"C{i}" for i in range(1, 25) if i not in (7, 15)),
    "R3", "R4", "R5", "R6", "R7", "R8", "R13", "R14", "R15", "R16", "R17",
}


def poly_vertices(inset: float = 0.0):
    """Return the 4 parallelogram vertices [(x,y) relative to (OX,OY)] inset perpendicular to every edge by `inset`."""
    # West edge: x = -HALF_W + inset
    # East edge: x = +HALF_W - inset
    # Top slanted edge: y - SKEW*x = -HALF_EDGE + inset * hypot(1, SKEW)
    # Bot slanted edge: y - SKEW*x = +HALF_EDGE - inset * hypot(1, SKEW)
    sec = math.hypot(1.0, SKEW)
    xw = -HALF_W + inset
    xe = HALF_W - inset
    c_top = -HALF_EDGE + inset * sec
    c_bot = HALF_EDGE - inset * sec
    return [
        (xw, c_top + SKEW * xw),  # NW acute
        (xe, c_top + SKEW * xe),  # NE obtuse
        (xe, c_bot + SKEW * xe),  # SE acute
        (xw, c_bot + SKEW * xw),  # SW obtuse
    ]


def inside_parallelogram(x: float, y: float, margin: float = 0.0) -> bool:
    sec = math.hypot(1.0, SKEW)
    if abs(x) > HALF_W - margin:
        return False
    v = y - SKEW * x
    if abs(v) > HALF_EDGE - margin * sec:
        return False
    return True


def stage_outline(spec: VariantSpec):
    import pcbnew

    hw = spec.hw_dir
    pcb_path = hw / "parallelogram.kicad_pcb"
    pro_path = hw / "parallelogram.kicad_pro"
    pro_bytes = pro_path.read_bytes()

    b = pcbnew.NewBoard(str(pcb_path))
    b.SetCopperLayerCount(4)
    tb = b.GetTitleBlock()
    tb.SetTitle(spec.name if spec.extra_side_buttons else f"parallelogram ({spec.name})")
    tb.SetRevision(spec.title_rev)
    tb.SetDate("2026-11-05")
    tb.SetCompany("CERN-OHL-P-2.0")
    tb.SetComment(0, spec.summary)

    mm = pcbnew.FromMM
    verts = poly_vertices(0.0)
    r = CORNER_R
    n = len(verts)
    fillets = []
    for k in range(n):
        v_prev = verts[(k - 1) % n]
        vk = verts[k]
        v_next = verts[(k + 1) % n]
        uin_x, uin_y = v_prev[0] - vk[0], v_prev[1] - vk[1]
        lin = math.hypot(uin_x, uin_y)
        uin_x, uin_y = uin_x / lin, uin_y / lin

        uout_x, uout_y = v_next[0] - vk[0], v_next[1] - vk[1]
        lout = math.hypot(uout_x, uout_y)
        uout_x, uout_y = uout_x / lout, uout_y / lout

        cos_th = max(-1.0, min(1.0, uin_x * uout_x + uin_y * uout_y))
        theta = math.acos(cos_th)
        d = r / math.tan(theta / 2.0)
        p1 = (vk[0] + d * uin_x, vk[1] + d * uin_y)
        p2 = (vk[0] + d * uout_x, vk[1] + d * uout_y)

        bx, by = uin_x + uout_x, uin_y + uout_y
        bl = math.hypot(bx, by)
        bx, by = bx / bl, by / bl
        dc = r / math.sin(theta / 2.0)
        cx, cy = vk[0] + dc * bx, vk[1] + dc * by
        pm = (cx - r * bx, cy - r * by)
        fillets.append((p1, pm, p2))

    # Add 4 straight Edge.Cuts segments + 4 tangent fillet arcs
    for k in range(n):
        _, _, p_start = fillets[k]
        p_end, _, _ = fillets[(k + 1) % n]
        seg = pcbnew.PCB_SHAPE(b)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(mm(0.10))
        seg.SetStart(pcbnew.VECTOR2I(mm(OX + p_start[0]), mm(OY + p_start[1])))
        seg.SetEnd(pcbnew.VECTOR2I(mm(OX + p_end[0]), mm(OY + p_end[1])))
        b.Add(seg)

        p1, pm, p2 = fillets[k]
        arc = pcbnew.PCB_SHAPE(b)
        arc.SetShape(pcbnew.SHAPE_T_ARC)
        arc.SetLayer(pcbnew.Edge_Cuts)
        arc.SetWidth(mm(0.10))
        arc.SetArcGeometry(
            pcbnew.VECTOR2I(mm(OX + p1[0]), mm(OY + p1[1])),
            pcbnew.VECTOR2I(mm(OX + pm[0]), mm(OY + pm[1])),
            pcbnew.VECTOR2I(mm(OX + p2[0]), mm(OY + p2[1])),
        )
        b.Add(arc)

    # Draw 20 x 35 mm prismatic pouch cell outline on B.Fab
    cx0, cy0 = CELL_CENTER
    cell_pts = [
        (cx0 - CELL_W / 2, cy0 - CELL_H / 2),
        (cx0 + CELL_W / 2, cy0 - CELL_H / 2),
        (cx0 + CELL_W / 2, cy0 + CELL_H / 2),
        (cx0 - CELL_W / 2, cy0 + CELL_H / 2),
        (cx0 - CELL_W / 2, cy0 - CELL_H / 2),
    ]
    for a, c in zip(cell_pts, cell_pts[1:]):
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.B_Fab)
        s.SetWidth(mm(0.10))
        s.SetStart(pcbnew.VECTOR2I(mm(OX + a[0]), mm(OY + a[1])))
        s.SetEnd(pcbnew.VECTOR2I(mm(OX + c[0]), mm(OY + c[1])))
        b.Add(s)

    pcbnew.SaveBoard(str(pcb_path), b)
    pro_path.write_bytes(pro_bytes)
    print(f"outline saved: {pcb_path}", flush=True)
    os._exit(0)


def stage_stack(spec: VariantSpec):
    """Write JLCPCB JLC04161H-7628 1.6 mm 4-layer HASL stackup."""
    pcb_path = spec.hw_dir / "parallelogram.kicad_pcb"
    t = pcb_path.read_text()

    def lay(n, k, th=None):
        return f'\t\t\t(layer "{n}" (type "{k}")' + (f" (thickness {th})" if th else "") + ")"

    s = [
        "\t\t(stackup",
        lay("F.SilkS", "Top Silk Screen"),
        lay("F.Paste", "Top Solder Paste"),
        lay("F.Mask", "Top Solder Mask", 0.01),
        lay("F.Cu", "copper", 0.035),
        '\t\t\t(layer "dielectric 1" (type "prepreg") (thickness 0.2104) (material "FR4") (epsilon_r 4.4) (loss_tangent 0.02))',
        lay("In1.Cu", "copper", 0.0152),
        '\t\t\t(layer "dielectric 2" (type "core") (thickness 1.065) (material "FR4") (epsilon_r 4.6) (loss_tangent 0.02))',
        lay("In2.Cu", "copper", 0.0152),
        '\t\t\t(layer "dielectric 3" (type "prepreg") (thickness 0.2104) (material "FR4") (epsilon_r 4.4) (loss_tangent 0.02))',
        lay("B.Cu", "copper", 0.035),
        lay("B.Mask", "Bottom Solder Mask", 0.01),
        lay("B.Paste", "Bottom Solder Paste"),
        lay("B.SilkS", "Bottom Silk Screen"),
        '\t\t\t(copper_finish "ENIG")' if spec.extra_side_buttons else '\t\t\t(copper_finish "HAL SnPb")',
        "\t\t\t(dielectric_constraints no)",
        "\t\t)",
    ]
    if "\t\t(stackup" in t:
        t, n = re.subn(r"\t\t\(stackup.*?\n\t\t\)\n", lambda _: "\n".join(s) + "\n", t, count=1, flags=re.S)
        assert n == 1
    else:
        t = t.replace("(setup\n", "(setup\n" + "\n".join(s) + "\n", 1)
    t = re.sub(r"\(general\n\t\t\(thickness [\d.]+\)", "(general\n\t\t(thickness 1.5862)", t)
    pcb_path.write_text(t)
    print(f"4-layer JLC04161H-7628 stack written: {pcb_path}")


def stage_sync(spec: VariantSpec):
    from kicad_write import update_pcb

    hw = spec.hw_dir
    pro_path = hw / "parallelogram.kicad_pro"
    pro_bytes = pro_path.read_bytes()
    update_pcb(hw / "parallelogram.kicad_sch", hw / "parallelogram.kicad_pcb", new_parts_at=(OX, OY))
    if spec.extra_side_buttons:
        pcb_txt = (hw / "parallelogram.kicad_pcb").read_text()
        pcb_txt = pcb_txt.replace("unconnected-(U3-GPIO28/ADC2-Pad42)", "unconnected-(U3-GPIO28{slash}ADC2-Pad42)")
        pcb_txt = pcb_txt.replace("unconnected-(U3-GPIO29/ADC3-Pad43)", "unconnected-(U3-GPIO29{slash}ADC3-Pad43)")
        (hw / "parallelogram.kicad_pcb").write_text(pcb_txt)
    pro_path.write_bytes(pro_bytes)
    print(f"synced PCB from schematic: {spec.name}", flush=True)
    os._exit(0)


def stage_place(spec: VariantSpec):
    import pcbnew

    hw = spec.hw_dir
    pcb_path = hw / "parallelogram.kicad_pcb"
    pro_path = hw / "parallelogram.kicad_pro"
    pro_bytes = pro_path.read_bytes()

    b = pcbnew.LoadBoard(str(pcb_path))
    ref_b = pcbnew.LoadBoard(str(REF_PCB))
    mm = pcbnew.FromMM
    um = pcbnew.ToMM
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    ref_fps = {f.GetReference(): f for f in ref_b.GetFootprints()}

    def set_fcu(ref: str, x: float, y: float, deg: float, hide_ref: bool = False):
        f = fps[ref]
        if f.GetLayer() != pcbnew.F_Cu:
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        f.SetPosition(pcbnew.VECTOR2I(mm(OX + x), mm(OY + y)))
        f.SetOrientationDegrees(float(deg))
        if hide_ref:
            f.Reference().SetVisible(False)
        f.Value().SetVisible(False)

    def set_bcu(ref: str, x: float, y: float, deg: float):
        f = fps[ref]
        if f.GetLayer() == pcbnew.F_Cu:
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        f.SetPosition(pcbnew.VECTOR2I(mm(OX + x), mm(OY + y)))
        f.SetOrientationDegrees(float(deg))
        f.Value().SetVisible(False)

    # 1. Place all D1..DN RGB LEDs on F.Cu in the skewed parallelogram lattice.
    cells = build_led_cells(spec)
    for c in cells:
        set_fcu(c["ref"], c["x_mm"], c["y_mm"], 0.0, hide_ref=True)

    # 2. Place Q2 (XYC-PT19C-L1 / ALS-PT19) on F.Cu tangent to the slanted top bezel (y = -31.0 + 0.32*x).
    set_fcu("Q2", 0.00, -29.90, -SKEW_DEG, hide_ref=False)
    fps["Q2"].Reference().SetVisible(False)  # Clean front aesthetic; pin-1 dot + optional tidy label added in post_silk

    # 3. Copy the proven RP2350 + regulator + crystal + flash + charger + ESD + LDO macro translated by (MACRO_DX, MACRO_DY).
    for ref in MACRO_REFS:
        rf = ref_fps[ref]
        rp = rf.GetPosition()
        set_bcu(ref, (um(rp.x) - OX) + MACRO_DX, (um(rp.y) - OY) + MACRO_DY, rf.GetOrientationDegrees())

    # 4. South end-zone & wing I/O (pads mode vs board-mounted USB-C + Micro-JST 1.25 + NW/SE flat-face buttons).
    if spec.io_mode == "usb":
        sec = math.hypot(1.0, SKEW)
        ut = (1.0 / sec, SKEW / sec)
        un = (-SKEW / sec, 1.0 / sec)  # outward South-West normal to South slanted bezel (y - SKEW*x = +HALF_EDGE)

        # Keep RP2350A + L1 + Y1 + U6 core macro identical; adjust South sub-macros around USB-C J1 & Micro-JST BT1:
        if spec.usb_ye > 4.5:
            set_bcu("U4", -5.60, 17.20, 180.0)
            set_bcu("C22", -1.60, 15.00, -90.0)
        else:
            set_bcu("U4", -3.65, 17.60, 90.0)
            set_bcu("C22", -0.30, 15.10, -90.0)
        set_bcu("C4", -3.20, 13.05, -90.0)

        set_bcu("U5", 3.02, 18.55, 0.0)
        set_bcu("C5", 0.02, 18.85, 90.0)
        set_bcu("C2", 3.60, 15.50, 180.0)
        if spec.usb_ye > 4.5:
            set_bcu("U7", -10.30, 21.80, 180.0)
            set_bcu("C1", -0.05, 16.50, 180.0)
            set_bcu("R5", 1.80, 15.45, 90.0)
        elif spec.extra_side_buttons:
            set_bcu("C1", 2.65, 23.65, 180.0)
            set_bcu("U7", 2.20, 21.95, 180.0)
            set_bcu("R5", 5.70, 16.95, -90.0)
        else:
            set_bcu("C1", 4.55, 21.75, -90.0)
            set_bcu("U7", 2.20, 21.95, 180.0)
            set_bcu("R5", 4.55, 23.40, 180.0)
        set_bcu("R3", 1.25, 15.45, 180.0)
        set_bcu("R4", 0.02, 21.25, 90.0)

        # J1 (TYPE-C-31-M-22 16P full-SMT USB-C) aligned to South slanted bezel:
        jx = spec.usb_s * ut[0] - spec.usb_ye * un[0]
        jy = HALF_EDGE + spec.usb_s * ut[1] - spec.usb_ye * un[1]
        best_j1_deg = None
        for deg in (SKEW_DEG, -SKEW_DEG, 180.0 + SKEW_DEG, 180.0 - SKEW_DEG):
            set_bcu("J1", jx, jy, deg)
            pa = next(p for p in fps["J1"].Pads() if p.GetNumber() == "A1B12").GetPosition()
            pb = next(p for p in fps["J1"].Pads() if p.GetNumber() == "B1A12").GetPosition()
            s1_n = max((um(p.GetPosition().x) - OX) * un[0] + (um(p.GetPosition().y) - OY) * un[1] for p in fps["J1"].Pads() if p.GetNumber() == "S1")
            sig_n = (um(pa.x) - OX) * un[0] + (um(pa.y) - OY) * un[1]
            dx_j = um(pb.x) - um(pa.x)
            slope_j = (um(pb.y) - um(pa.y)) / dx_j if abs(dx_j) > 1e-6 else 999.0
            if s1_n > sig_n + 2.0 and abs(slope_j - SKEW) < 0.02:
                best_j1_deg = deg
                break
        assert best_j1_deg is not None, f"[{spec.name}] failed to orient J1 along South slanted bezel"
        set_bcu("J1", jx, jy, best_j1_deg)

        # Verify both Ø0.65 mm NPTH locating peg holes clear every F.Cu pad by >= 0.25 mm!
        from shapely.geometry import Point, Polygon

        fcu_pad_polys = [
            Polygon([
                (um(bb.GetLeft()) - OX, um(bb.GetTop()) - OY),
                (um(bb.GetRight()) - OX, um(bb.GetTop()) - OY),
                (um(bb.GetRight()) - OX, um(bb.GetBottom()) - OY),
                (um(bb.GetLeft()) - OX, um(bb.GetBottom()) - OY),
            ])
            for f in b.GetFootprints()
            if f.GetLayer() == pcbnew.F_Cu
            for p in f.Pads()
            for bb in [p.GetBoundingBox()]
        ]
        for hp in fps["J1"].Pads():
            if hp.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                hx, hy = um(hp.GetPosition().x) - OX, um(hp.GetPosition().y) - OY
                hpoly = Point(hx, hy).buffer(0.325, 32)
                min_gap = min(hpoly.distance(pp) for pp in fcu_pad_polys)
                assert min_gap >= 0.25, f"[{spec.name}] J1 NPTH hole ({hx:.2f},{hy:.2f}) too close to F.Cu pad: {min_gap:.3f} mm"

        pa5 = next(p for p in fps["J1"].Pads() if p.GetNumber() == "A5").GetPosition()
        pb5 = next(p for p in fps["J1"].Pads() if p.GetNumber() == "B5").GetPosition()
        set_bcu("R1", (um(pa5.x) - OX) - 1.65 * un[0], (um(pa5.y) - OY) - 1.65 * un[1], 90.0)
        set_bcu("R2", (um(pb5.x) - OX) - 1.65 * un[0], (um(pb5.y) - OY) - 1.65 * un[1], 90.0)

        if spec.extra_side_buttons:
            # BT1 rotated 90 deg CCW to 0.0 deg on B.Cu: mating mouth faces straight North (-Y) toward board center / LiPo
            # with >5.4 mm unobstructed runway; SW4 aligned parallel to South slanted bezel (180 - SKEW_DEG) in SE wing.
            set_bcu("BT1", 7.97, 23.00, 0.0)
            bt_p1_y = um(next(p for p in fps["BT1"].Pads() if p.GetNumber() == "1").GetPosition().y) - OY
            if bt_p1_y < 23.00:
                set_bcu("BT1", 7.97, 23.00, 180.0)
            set_bcu("SW3", -9.15, -28.65, 90.0)
            set_bcu("SW4", 8.15, 30.55, 180.0 - SKEW_DEG)
            set_bcu("R44", -7.20, -24.10, 180.0)
            set_bcu("R45", 10.70, 27.10, -90.0)
        else:
            # BT1 (Micro-JST 1.25 / MX1.25 right-angle SMT) at East-South outside 20x35 mm LiPo, mating mouth facing West (-X):
            set_bcu("BT1", 8.40, 20.05, 90.0)
            bt_p1_x = um(next(p for p in fps["BT1"].Pads() if p.GetNumber() == "1").GetPosition().x) - OX
            if bt_p1_x < 8.40:
                set_bcu("BT1", 8.40, 20.05, -90.0)

            # Two flat-face back push buttons (XKB TS-1187A-B-A-B) in NW & SE acute wings, 100% outside 20x35 mm LiPo:
            set_bcu("SW3", -9.15, -28.65, 90.0)
            set_bcu("SW4", 9.15, 28.65, 90.0)
            set_bcu("R44", -7.20, -24.10, 180.0)
            set_bcu("R45", 5.20, 26.80, 90.0)

        # U8 (XB9901A protection) + R8 + C6 and Q1 + R9..R12 + C7 (VBAT_SENSE) in spacious East corridor above BT1:
        set_bcu("U8", 10.00, 12.60, 180.0)
        set_bcu("C6", 10.60, 10.65, 180.0)
        set_bcu("R8", 10.00, 14.15, 180.0)
        set_bcu("Q1", 9.20, 7.60, 180.0)
        set_bcu("R9", 11.10, 7.20, 90.0)
        set_bcu("R10", 7.30, 7.20, 90.0)
        set_bcu("R11", 9.20, 9.40, 180.0)
        set_bcu("R12", 7.30, 9.20, 90.0)
        set_bcu("C7", 8.00, 10.80, 180.0)
    else:
        set_bcu("J1", 0.00, 29.10, SKEW_DEG)  # Flipped on B.Cu: +SKEW_DEG aligns along dy/dx = +0.32!
        # Verify J1 pad slope matches +0.32; if negated, flip sign!
        j1_p1 = next(p for p in fps["J1"].Pads() if p.GetNumber() == "1").GetPosition()
        j1_p6 = next(p for p in fps["J1"].Pads() if p.GetNumber() == "6").GetPosition()
        slope_j1 = (um(j1_p6.y) - um(j1_p1.y)) / (um(j1_p6.x) - um(j1_p1.x))
        if abs(slope_j1 - SKEW) > 0.05:
            set_bcu("J1", 0.00, 29.10, -SKEW_DEG)

        # R1, R2 (5.1k CC1/CC2) right above J1.1/J1.2
        j1_p1 = next(p for p in fps["J1"].Pads() if p.GetNumber() == "1").GetPosition()
        j1_p2 = next(p for p in fps["J1"].Pads() if p.GetNumber() == "2").GetPosition()
        set_bcu("R1", um(j1_p1.x) - OX, um(j1_p1.y) - OY - 2.20, 90.0)
        set_bcu("R2", um(j1_p2.x) - OX, um(j1_p2.y) - OY - 2.20, 90.0)

        # BT1 in the spacious South-East acute triangle (y_bot(+6.0) = +32.92 mm!), cleanly below R8 (bottom 28.12).
        set_bcu("BT1", 8.60, 29.85, 180.0)

        # Q1 + R9..R12 + C7 (VBAT_SENSE) compactly grouped in South-West with zero net crossings around Q1.
        set_bcu("Q1", -5.20, 25.40, 180.0)
        set_bcu("R9", -3.30, 24.80, 180.0)
        set_bcu("R10", -7.20, 24.80, 180.0)
        set_bcu("R11", -5.20, 27.10, 180.0)
        set_bcu("R12", -7.20, 26.40, 180.0)
        set_bcu("C7", -3.30, 26.40, 180.0)

    # 5. Side-actuated peg-less EVQP7J01P buttons on East & West vertical edges (+-12.50 mm), knobs protruding 0.45 mm.
    set_bcu("SW1", 10.85, 1.50, -90.0)
    sw1_p1 = [um(p.GetPosition().x) - OX for p in fps["SW1"].Pads() if p.GetNumber() == "1"][0]
    sw1_p2 = [um(p.GetPosition().x) - OX for p in fps["SW1"].Pads() if p.GetNumber() == "2"][0]
    if sw1_p2 < sw1_p1:
        set_bcu("SW1", 10.85, 1.50, 90.0)
    set_bcu("R18", 8.20, 1.50, 90.0)

    set_bcu("SW2", -10.85, -3.50, 90.0)
    sw2_p1 = [um(p.GetPosition().x) - OX for p in fps["SW2"].Pads() if p.GetNumber() == "1"][0]
    sw2_p2 = [um(p.GetPosition().x) - OX for p in fps["SW2"].Pads() if p.GetNumber() == "2"][0]
    if sw2_p2 > sw2_p1:
        set_bcu("SW2", -10.85, -3.50, -90.0)

    if spec.extra_side_buttons:
        for sref, sy in (("SW5", -22.00), ("SW6", 22.80)):
            set_bcu(sref, -10.85, sy, 90.0)
            sw_p1 = [um(p.GetPosition().x) - OX for p in fps[sref].Pads() if p.GetNumber() == "1"][0]
            sw_p2 = [um(p.GetPosition().x) - OX for p in fps[sref].Pads() if p.GetNumber() == "2"][0]
            if sw_p2 > sw_p1:
                set_bcu(sref, -10.85, sy, -90.0)
        set_bcu("C71", -7.40, -22.20, 180.0)
        set_bcu("R46", -7.40, -21.00, 180.0)
        set_bcu("C72", -7.40, 19.80, 180.0)
        set_bcu("R47", -7.40, 21.00, 180.0)

    # 6. U9 (LIS2DW12) + decouplers/pull-ups West of U3 (near U3 West GPIO2/3/10 & +3V3).
    set_bcu("U9", -8.80, 5.20, 180.0)
    p9 = next(p for p in fps["U9"].Pads() if p.GetNumber() == "9").GetPosition()
    dy_u9 = -2.45 if (um(p9.y) - OY) < 5.20 else 2.45
    set_bcu("C25", -10.20, 5.20 + dy_u9, 90.0)
    set_bcu("C26", -8.80, 5.20 + dy_u9, 90.0)
    set_bcu("C27", -7.40, 5.20 + dy_u9, 90.0)
    set_bcu("R19", -9.70, 5.20 - dy_u9, 90.0)
    set_bcu("R20", -8.10, 5.20 - dy_u9, 90.0)

    # I2C0 pull-ups (R21, R22) & LED_SDB (R31, C35) just NW of U3 (near U3 pads 7, 8, 9!).
    set_bcu("R21", -5.20, 2.20, 180.0)
    set_bcu("R22", -5.20, 1.00, 180.0)
    set_bcu("R31", -7.40, 1.00, 180.0)
    set_bcu("C35", -7.40, 2.20, 180.0)

    # R43 (22k) & C70 (100n) on B.Cu directly behind top-bezel Q2 (0.0, -29.9).
    set_bcu("R43", -1.50, -28.20, 180.0)
    set_bcu("C70", 1.50, -28.20, 180.0)

    # 7. Place AW20198QNR QFN-40 drivers + programmatically place their 5 local passives right at PVCC(5) & VCC(22)/ISET(29)!
    drv_fixed = set()
    for drv in spec.drivers:
        dx0, dy0, drot = drv.bcu_pos
        # Place SW driver clear of C22 & U4; on 6-col p2-132 x=-7.40 centers U2's 3.4 mm EP cleanly between cols -9.25 and -5.55!
        if spec.io_mode != "usb" and dy0 > 10.0 and dx0 < 0:
            dx0, dy0 = (-7.40 if spec.cols == 6 else -8.00), 19.25
        set_bcu(drv.uref, dx0, dy0, drot)
        drv_fixed.add(drv.uref)

        uf = fps[drv.uref]
        p5 = next(p for p in uf.Pads() if p.GetNumber() == "5").GetPosition()    # PVCC
        p22 = next(p for p in uf.Pads() if p.GetNumber() == "22").GetPosition()  # VCC
        p29 = next(p for p in uf.Pads() if p.GetNumber() == "29").GetPosition()  # ISET

        p5_y = um(p5.y) - OY
        p22_y = um(p22.y) - OY
        pvcc_dir = -1.0 if p5_y < dy0 else 1.0
        vcc_dir = -1.0 if p22_y < dy0 else 1.0

        # 100n closest to PVCC(5), 1u right behind it, optional 22u 0603 bulk beside them
        c_pvcc_1u = f"C{drv.cap_base}"
        c_pvcc_100n = f"C{drv.cap_base + 1}"
        c_vcc_100n = f"C{drv.cap_base + 2}"
        c_vcc_1u = f"C{drv.cap_base + 3}"

        p5_x = um(p5.x) - OX
        set_bcu(c_pvcc_100n, p5_x - 0.65, dy0 + pvcc_dir * 3.95, 90.0)
        set_bcu(c_pvcc_1u, p5_x + 0.65, dy0 + pvcc_dir * 3.95, 90.0)
        if drv.bulk_ref:
            bulk_dx = -2.00 if (spec.io_mode == "usb" and dy0 > 10.0 and dx0 < 0) else (2.10 if dx0 <= 0 else -2.10)
            set_bcu(drv.bulk_ref, p5_x + bulk_dx, dy0 + pvcc_dir * 4.40, 90.0)
            drv_fixed.add(drv.bulk_ref)

        p22_x = um(p22.x) - OX
        p29_x = um(p29.x) - OX
        vcc_sgn = 1.0 if p22_x >= p29_x else -1.0
        set_bcu(c_vcc_100n, p22_x - vcc_sgn * 0.55, dy0 + vcc_dir * 3.95, 90.0)
        set_bcu(c_vcc_1u, p22_x + vcc_sgn * 0.70, dy0 + vcc_dir * 3.95, 90.0)
        set_bcu(drv.rset_ref, p29_x, dy0 + vcc_dir * 3.95, 90.0)
        drv_fixed.update({c_pvcc_1u, c_pvcc_100n, c_vcc_100n, c_vcc_1u, drv.rset_ref})

    # 8. Place Test Points in clean open pockets near their nets.
    if spec.io_mode == "usb":
        tp_targets = [
            ("TP1", 6.25, 14.30),    # VSYS near C2/U5
            ("TP2", -6.90, 11.75),   # +3V3 near C4/U6
            ("TP3", 6.50, 12.10),    # VBAT near U8/C5
            ("TP4", -5.20, 13.80),   # +1V1 near L1/U6 (keeps East driver throat open!)
            ("TP5", -5.50, -1.50),   # RUN
            ("TP8", -5.50, -3.55),   # GND adjacent to RUN for easy boot/reset jumper!
            ("TP6", 4.20, -1.20),    # SWCLK
            ("TP7", 4.20, -2.55),    # SWDIO
        ]
    else:
        tp_targets = [
            ("TP1", 7.80, 15.80),    # VSYS near C2/U5
            ("TP2", -5.20, 11.40),   # +3V3 near C4/U6
            ("TP3", 3.50, 15.80),    # VBAT near C5/U5
            ("TP4", 5.80, 12.20),    # +1V1 near L1/C18
            ("TP5", -5.50, -1.50),   # RUN
            ("TP8", -5.50, -3.00),   # GND adjacent to RUN for easy boot/reset jumper!
            ("TP6", 4.20, -1.50),    # SWCLK
            ("TP7", 4.20, -3.00),    # SWDIO
        ]
    for tref, tx, ty in tp_targets:
        set_bcu(tref, tx, ty, 180.0)

    # 9. Legalize movable auxiliary passives/TPs against all fixed ICs/decouplers and the parallelogram outline.
    if spec.io_mode == "usb":
        from shapely.affinity import translate
        from shapely.geometry import Polygon
        from shapely.ops import unary_union
        from shapely.prepared import prep

        def bcu_poly(f):
            cy = f.GetCourtyard(pcbnew.B_CrtYd)
            if cy.OutlineCount():
                polys = []
                for k in range(cy.OutlineCount()):
                    o = cy.Outline(k)
                    pts = [(um(o.CPoint(i).x) - OX, um(o.CPoint(i).y) - OY) for i in range(o.PointCount())]
                    if len(pts) >= 3:
                        polys.append(Polygon(pts).buffer(0))
                if polys:
                    return unary_union(polys)
            q = f.GetBoundingBox(False, False)
            return Polygon([
                (um(q.GetLeft()) - OX, um(q.GetTop()) - OY),
                (um(q.GetRight()) - OX, um(q.GetTop()) - OY),
                (um(q.GetRight()) - OX, um(q.GetBottom()) - OY),
                (um(q.GetLeft()) - OX, um(q.GetBottom()) - OY),
            ])

        movable = [
            "R1", "R2", "R3", "R4", "R5", "R8",
            "Q1", "R9", "R10", "R11", "R12", "C7",
            "R18", "R19", "R20", "R21", "R22", "R31", "C35", "R43", "C70", "R44", "R45",
            "TP1", "TP2", "TP3", "TP4", "TP5", "TP6", "TP7", "TP8",
        ]
        if spec.extra_side_buttons:
            movable.extend(["R46", "C71", "R47", "C72"])
        fixed_polys = {
            r: bcu_poly(f)
            for r, f in fps.items()
            if f.GetLayer() == pcbnew.B_Cu and r not in movable
        }
        p_board = prep(Polygon(poly_vertices(0.32)))
        obs_union = unary_union([p.buffer(0.06, 4) for p in fixed_polys.values()])
        for r in movable:
            f = fps[r]
            p0 = bcu_poly(f)
            x0, y0 = um(f.GetPosition().x) - OX, um(f.GetPosition().y) - OY
            p_obs = prep(obs_union)
            best = None
            for ring in range(0, 90):
                rad = ring * 0.10
                steps = max(1, 12 * ring)
                for k in range(steps):
                    a = 2.0 * math.pi * k / steps
                    dx, dy = rad * math.cos(a), rad * math.sin(a)
                    cand = translate(p0, xoff=dx, yoff=dy)
                    if p_board.contains(cand) and not p_obs.intersects(cand):
                        best = (dx, dy, cand, rad)
                        break
                if best:
                    break
            if not best:
                raise SystemExit(f"[{spec.name}] legalize failed for {r} around ({x0:.2f}, {y0:.2f})")
            dx, dy, cand, rad = best
            if rad > 0:
                f.SetPosition(pcbnew.VECTOR2I(mm(OX + x0 + dx), mm(OY + y0 + dy)))
                print(f"  legalized {r}: +{rad:.2f} mm -> ({x0 + dx:.2f}, {y0 + dy:.2f})")
            fixed_polys[r] = cand
            obs_union = obs_union.union(cand.buffer(0.06, 4))

        # Verify 0 B.Cu courtyard polygon overlaps across all non-core-macro pairs
        core_macro = MACRO_REFS - {"U4", "C22", "C4", "U5", "C5", "C2", "C1", "U7", "U8", "C6", "R8", "R3", "R4", "R5"}
        bcu_names = sorted(fixed_polys.keys())
        for i, r1 in enumerate(bcu_names):
            a = fixed_polys[r1]
            for r2 in bcu_names[i + 1 :]:
                if r1 in core_macro and r2 in core_macro:
                    continue
                c = fixed_polys[r2]
                if a.intersects(c) and a.intersection(c).area > 1e-4:
                    raise SystemExit(f"[{spec.name}] B.Cu courtyard overlap: {r1} {a.bounds} vs {r2} {c.bounds}")
    else:
        def cbox_bcu(f):
            cy = f.GetCourtyard(pcbnew.B_CrtYd)
            q = cy.BBox() if cy.OutlineCount() else f.GetBoundingBox(False, False)
            return [um(q.GetLeft()) - OX, um(q.GetTop()) - OY, um(q.GetRight()) - OX, um(q.GetBottom()) - OY]

        movable = [
            "R1", "R2", "Q1", "R9", "R10", "R11", "R12", "C7",
            "R18", "R19", "R20", "R21", "R22", "R31", "C35", "R43", "C70",
            "TP1", "TP2", "TP3", "TP4", "TP5", "TP6", "TP7", "TP8",
        ]
        fixed_boxes = {
            r: cbox_bcu(f)
            for r, f in fps.items()
            if f.GetLayer() == pcbnew.B_Cu and r not in movable
        }
        margin = 0.06
        for r in movable:
            f = fps[r]
            q = cbox_bcu(f)
            x0, y0 = um(f.GetPosition().x) - OX, um(f.GetPosition().y) - OY
            best = None
            for ring in range(0, 160):
                rad = ring * 0.10
                steps = max(1, 16 * ring)
                for k in range(steps):
                    a = 2.0 * math.pi * k / steps
                    dx, dy = rad * math.cos(a), rad * math.sin(a)
                    bb = [q[0] + dx, q[1] + dy, q[2] + dx, q[3] + dy]
                    if not all(inside_parallelogram(u, v, 0.35) for u in (bb[0], bb[2]) for v in (bb[1], bb[3])):
                        continue
                    if all(
                        bb[2] + margin <= c[0] or c[2] + margin <= bb[0] or bb[3] + margin <= c[1] or c[3] + margin <= bb[1]
                        for c in fixed_boxes.values()
                    ):
                        best = (dx, dy, bb, rad)
                        break
                if best:
                    break
            if not best:
                raise SystemExit(f"[{spec.name}] legalize failed for {r} around ({x0:.2f}, {y0:.2f})")
            dx, dy, bb, rad = best
            if rad > 0:
                f.SetPosition(pcbnew.VECTOR2I(mm(OX + x0 + dx), mm(OY + y0 + dy)))
                print(f"  legalized {r}: +{rad:.2f} mm -> ({x0 + dx:.2f}, {y0 + dy:.2f})")
            fixed_boxes[r] = bb

        # Verify 0 B.Cu courtyard overlaps across all non-macro pairs
        bcu_names = sorted(fixed_boxes.keys())
        for i, r1 in enumerate(bcu_names):
            a = fixed_boxes[r1]
            for r2 in bcu_names[i + 1 :]:
                if r1 in MACRO_REFS and r2 in MACRO_REFS:
                    continue
                c = fixed_boxes[r2]
                if not (a[2] <= c[0] + 0.02 or c[2] <= a[0] + 0.02 or a[3] <= c[1] + 0.02 or c[3] <= a[1] + 0.02):
                    raise SystemExit(f"[{spec.name}] B.Cu courtyard overlap: {r1} {a} vs {r2} {c}")

    # Hide noisy B.Cu silkscreen designators prior to post_silk tidy pass
    for f in b.GetFootprints():
        if f.GetLayer() == pcbnew.B_Cu:
            f.Reference().SetVisible(False)

    pcbnew.SaveBoard(str(pcb_path), b)
    pro_path.write_bytes(pro_bytes)
    print(f"placed {len(fps)} footprints on {spec.name} (0 courtyard overlaps)", flush=True)
    os._exit(0)


def stage_zones(spec: VariantSpec):
    """Add In1.Cu unbroken GND plane, RP2350 4-layer reference zones, solid EP GND thermal vias, and keepout rule areas."""
    import pcbnew

    hw = spec.hw_dir
    pcb_path = hw / "parallelogram.kicad_pcb"
    pro_path = hw / "parallelogram.kicad_pro"
    pro_bytes = pro_path.read_bytes()

    b = pcbnew.LoadBoard(str(pcb_path))
    mm = pcbnew.FromMM
    um = pcbnew.ToMM
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    lid = {b.GetLayerName(l): l for l in range(64) if b.GetLayerName(l).endswith(".Cu")}
    F_CU, IN1_CU, IN2_CU, B_CU = lid["F.Cu"], lid["In1.Cu"], lid["In2.Cu"], lid["B.Cu"]

    # 1. Ensure U5 pad 17 is solid B.Cu copper without paste-split fragments
    u5 = fps["U5"]
    old17 = [p for p in u5.Pads() if p.GetNumber() == "17" and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD]
    if len(old17) > 1:
        boxes = [p.GetBoundingBox() for p in old17]
        x0, x1 = min(um(q.GetLeft()) for q in boxes), max(um(q.GetRight()) for q in boxes)
        y0, y1 = min(um(q.GetTop()) for q in boxes), max(um(q.GetBottom()) for q in boxes)
        net17 = old17[0].GetNetCode()
        keep_alive = []
        for p in list(u5.Pads()):
            if p.GetNumber() == "17" and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                u5.Remove(p)
                keep_alive.append(p)
        pd = pcbnew.PAD(u5)
        pd.SetShape(pcbnew.PAD_SHAPE_RECT)
        pd.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        ls = pcbnew.LSET()
        ls.AddLayer(B_CU)
        ls.AddLayer(pcbnew.B_Mask)
        pd.SetLayerSet(ls)
        pd.SetSize(pcbnew.VECTOR2I(mm(x1 - x0), mm(y1 - y0)))
        pd.SetNumber("17")
        u5.Add(pd)
        pd.SetPosition(pcbnew.VECTOR2I(mm((x0 + x1) / 2), mm((y0 + y1) / 2)))
        pd.SetOrientationDegrees(0)
        pd.SetNetCode(net17)

    # Collect all F.Cu SMD pad boxes so GND thermal vias inside solid B.Cu EPs never touch F.Cu LED pads!
    fcu_pads = [
        (um(q.GetLeft()), um(q.GetTop()), um(q.GetRight()), um(q.GetBottom()), p.GetNetname())
        for f in b.GetFootprints()
        if f.GetLayer() == pcbnew.F_Cu
        for p in f.Pads()
        for q in [p.GetBoundingBox()]
    ]

    def fcu_clear(xa: float, ya: float, req_r: float = 0.275) -> bool:
        # 0.30 mm via radius (0.15) + 0.125 mm clearance = 0.275 mm to any non-GND F.Cu pad
        for a, e, g, h, n in fcu_pads:
            if n != "GND":
                if math.hypot(max(a - xa, 0.0, xa - g), max(e - ya, 0.0, ya - h)) < req_r:
                    return False
        return True

    def poly_rel(pts):
        p = pcbnew.SHAPE_POLY_SET()
        p.NewOutline()
        for px, py in pts:
            p.Append(mm(OX + px), mm(OY + py))
        p.thisown = False
        return p

    def add_zone(name, layer, net, pts, prio, connect=pcbnew.ZONE_CONNECTION_FULL, minw=0.10, clear=0.10):
        z = pcbnew.ZONE(b)
        z.SetZoneName(name)
        z.SetLayer(layer)
        z.SetNet(b.FindNet(net))
        z.SetAssignedPriority(prio)
        z.SetPadConnection(connect)
        z.SetMinThickness(mm(minw))
        z.SetThermalReliefGap(mm(0.20))
        z.SetThermalReliefSpokeWidth(mm(0.20))
        z.SetLocalClearance(mm(clear))
        z.SetOutline(poly_rel(pts))
        b.Add(z)
        return z

    def add_area(name, layer, pts, tracks=False, pour=False, vias=False):
        k = pcbnew.ZONE(b)
        k.SetIsRuleArea(True)
        k.SetZoneName(name)
        k.SetLayer(layer)
        k.SetDoNotAllowCopperPour(pour)
        k.SetDoNotAllowTracks(tracks)
        k.SetDoNotAllowVias(vias)
        k.SetDoNotAllowPads(False)
        k.SetDoNotAllowFootprints(False)
        k.SetOutline(poly_rel(pts))
        b.Add(k)
        return k

    # 2. Place collision-checked 0.20/0.45 mm GND thermal vias inside U3.61, U5.17, and all AW20198.41 solid EPs,
    #    plus B.Cu named rule areas forbidding any foreign via or B.Cu track inside any solid EP!
    gnd_code = b.FindNet("GND").GetNetCode()
    placed_vias = []
    ep_specs = [("U3", "61", 5), ("U5", "17", 2)] + [(drv.uref, "41", 5) for drv in spec.drivers]
    th_summary = {}
    for sref, pad_num, want_n in ep_specs:
        ep_pad = next(p for p in fps[sref].Pads() if p.GetNumber() == pad_num and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD)
        bb = ep_pad.GetBoundingBox()
        x0, y0, x1, y1 = um(bb.GetLeft()), um(bb.GetTop()), um(bb.GetRight()), um(bb.GetBottom())
        # Named rule area on B.Cu (+0.05 mm around EP) enforced by .kicad_dru
        rx0, ry0, rx1, ry1 = x0 - OX - 0.05, y0 - OY - 0.05, x1 - OX + 0.05, y1 - OY + 0.05
        add_area(f"{sref} solid EP", B_CU, [(rx0, ry0), (rx1, ry0), (rx1, ry1), (rx0, ry1)])

        # Candidate thermal via positions inside EP (at least 0.28 mm inside EP edge so 0.45 mm pad stays inside EP)
        cands = []
        if spec.extra_side_buttons:
            bpaste_id = b.GetLayerID("B.Paste")
            pboxes_ep = [
                (um(pb.GetLeft()), um(pb.GetTop()), um(pb.GetRight()), um(pb.GetBottom()))
                for p in fps[sref].Pads()
                if p.IsOnLayer(bpaste_id) and not p.IsOnLayer(B_CU)
                for pb in [p.GetBoundingBox()]
            ]
            if sref == "U5":
                cands = [((x0 + x1) / 2.0, (y0 + y1) / 2.0 - 0.45), ((x0 + x1) / 2.0, (y0 + y1) / 2.0 + 0.45)]
            else:
                xv = x0 + 0.25
                while xv <= x1 - 0.25 + 1e-6:
                    yv = y0 + 0.25
                    while yv <= y1 - 0.25 + 1e-6:
                        if not any(px0 - 0.075 < xv < px1 + 0.075 and py0 - 0.075 < yv < py1 + 0.075 for px0, py0, px1, py1 in pboxes_ep):
                            cands.append((round(xv, 3), round(yv, 3)))
                        yv += 0.05
                    xv += 0.05
        else:
            xv = x0 + 0.30
            while xv <= x1 - 0.30 + 1e-6:
                yv = y0 + 0.30
                while yv <= y1 - 0.30 + 1e-6:
                    cands.append((round(xv, 3), round(yv, 3)))
                    yv += 0.15
                xv += 0.15
        cx_ep, cy_ep = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        # Prefer cross-axis points (away from 2x2 paste quadrants at +-0.95, +-0.95)
        if not (spec.extra_side_buttons and sref == "U5"):
            cands.sort(key=lambda q: (min(abs(q[0] - cx_ep), abs(q[1] - cy_ep)), math.hypot(q[0] - cx_ep, q[1] - cy_ep)))
        min_sep = 0.65 if spec.extra_side_buttons else 0.70
        got = []
        for qx, qy in cands:
            if len(got) >= want_n:
                break
            if fcu_clear(qx, qy) and all(math.hypot(qx - ax, qy - ay) >= min_sep for ax, ay in got):
                v = pcbnew.PCB_VIA(b)
                v.SetPosition(pcbnew.VECTOR2I(mm(qx), mm(qy)))
                v.SetWidth(mm(0.30))
                v.SetDrill(mm(0.15))
                v.SetLayerPair(F_CU, B_CU)
                v.SetNetCode(gnd_code)
                v.SetLocked(True)
                b.Add(v)
                got.append((qx, qy))
                placed_vias.append((qx, qy))
        th_summary[sref] = len(got)
    print(f"[{spec.name}] solid EP GND thermal vias: {th_summary}")

    # 3. Unbroken In1.Cu (L2) solid GND plane across the entire parallelogram (0.30 mm edge pullback),
    #    with LX cutout under VREG_LX switch node per chips/rp2350.md §6.3.8.1!
    gnd_pts = poly_vertices(inset=0.30)
    add_zone("plane GND", IN1_CU, "GND", gnd_pts, 0, minw=0.22 if spec.extra_side_buttons else 0.18, clear=0.15)

    # (the LX cutout itself is added after the vendor zones below: it follows the VREG_LX copper)

    # 4. RP2350 4-layer unbroken B.Cu power rings + vendor regulator zones (chips/rp2350.md):
    #    - "RP2350 ring" (+1V1, sq(2.32), prio 3): 1 unbroken ring inside U3 moat (1.80..2.32 mm)
    #    - "RP2350 band" (+3V3, sq(3.12), prio 1): 1 unbroken ring joining all IOVDD pads (2.42..2.90+ mm)
    u3_pos = fps["U3"].GetPosition()
    ux_rel, uy_rel = um(u3_pos.x) - OX, um(u3_pos.y) - OY
    sq = lambda h: [(ux_rel - h, uy_rel - h), (ux_rel + h, uy_rel - h), (ux_rel + h, uy_rel + h), (ux_rel - h, uy_rel + h)]
    add_zone("RP2350 band", B_CU, "+3V3", sq(3.12), 1, minw=0.10, clear=0.10)
    add_zone("RP2350 ring", B_CU, "+1V1", sq(2.32), 3, connect=pcbnew.ZONE_CONNECTION_FULL, minw=0.20, clear=0.10)

    # Place 2 collision-free +1V1 vias inside "RP2350 ring" (at r ~ 2.06 mm) so ultraroute connects DVDD & COUT on In2.Cu!
    v11_code = b.FindNet("+1V1").GetNetCode()
    ring_vias = 0
    for rx, ry in ((0.45, 2.06), (-0.45, -2.06), (-2.06, -0.45), (2.06, 0.45), (0.0, 2.06), (0.0, -2.06)):
        xa, ya = OX + ux_rel + rx, OY + uy_rel + ry
        if fcu_clear(xa, ya) and all(math.hypot(xa - ax, ya - ay) >= 0.60 for ax, ay in placed_vias):
            v = pcbnew.PCB_VIA(b)
            v.SetPosition(pcbnew.VECTOR2I(mm(xa), mm(ya)))
            v.SetWidth(mm(0.30))
            v.SetDrill(mm(0.15))
            v.SetLayerPair(F_CU, B_CU)
            v.SetNetCode(v11_code)
            v.SetLocked(True)
            b.Add(v)
            placed_vias.append((xa, ya))
            ring_vias += 1
            if ring_vias >= 3:
                break
    print(f"[{spec.name}] RP2350 +1V1 ring vias placed: {ring_vias}")

    # Named rule areas around U3 & regulator corner
    add_area("U3 ring", B_CU, sq(2.85))
    if spec.extra_side_buttons:
        add_area(
            "U3 band",
            B_CU,
            [
                (ux_rel - 2.94, uy_rel - 2.94),
                (ux_rel + 2.94, uy_rel - 2.94),
                (ux_rel + 2.94, uy_rel + 2.94),
                (ux_rel - 2.94, uy_rel + 2.94),
                (ux_rel - 2.94, uy_rel),
                (ux_rel - 2.35, uy_rel),
                (ux_rel - 2.35, uy_rel + 2.35),
                (ux_rel + 2.35, uy_rel + 2.35),
                (ux_rel + 2.35, uy_rel - 2.35),
                (ux_rel - 2.35, uy_rel - 2.35),
                (ux_rel - 2.35, uy_rel - 0.002),
                (ux_rel - 2.94, uy_rel - 0.002),
            ],
        )
    add_area(
        "U3 ring vias",
        B_CU,
        [
            (ux_rel - 2.32, uy_rel - 2.32),
            (ux_rel + 2.32, uy_rel - 2.32),
            (ux_rel + 2.32, uy_rel + 2.32),
            (ux_rel - 2.32, uy_rel + 2.32),
            (ux_rel - 2.32, uy_rel),
            (ux_rel - 1.75, uy_rel),
            (ux_rel - 1.75, uy_rel + 1.75),
            (ux_rel + 1.75, uy_rel + 1.75),
            (ux_rel + 1.75, uy_rel - 1.75),
            (ux_rel - 1.75, uy_rel - 1.75),
            (ux_rel - 1.75, uy_rel - 0.002),
            (ux_rel - 2.32, uy_rel - 0.002),
        ],
    )
    add_area("reg corner", B_CU, [(ux_rel + 1.05, uy_rel + 3.0), (ux_rel + 3.65, uy_rel + 3.0), (ux_rel + 3.65, uy_rel + 8.35), (ux_rel + 1.05, uy_rel + 8.35)])
    l1_cy = fps["L1"].GetCourtyard(B_CU).BBox()
    add_area(
        "L1 window",
        B_CU,
        [
            (um(l1_cy.GetLeft()) - OX, um(l1_cy.GetTop()) - OY),
            (um(l1_cy.GetRight()) - OX, um(l1_cy.GetTop()) - OY),
            (um(l1_cy.GetRight()) - OX, um(l1_cy.GetBottom()) - OY),
            (um(l1_cy.GetLeft()) - OX, um(l1_cy.GetBottom()) - OY),
        ],
    )

    # IOVDD pin-to-decap links + FB Kelvin-sense link as locked B.Cu tracks (replaces thin strip zones
    # that foreign vias/tracks could split into islands; unlocked in post_silk per LESSONS.md).
    v33_code = b.FindNet("+3V3").GetNetCode()
    for pin, cap in (("1", "C8"), ("11", "C9"), ("20", "C10"), ("30", "C11"), ("38", "C12"), ("44", "C14"), ("54", "C13")):
        a = next(p for p in fps["U3"].Pads() if p.GetNumber() == pin).GetPosition()
        c_ = next(p for p in fps[cap].Pads() if p.GetNetname() == "+3V3").GetPosition()
        ax, ay, cx_, cy_ = um(a.x), um(a.y), um(c_.x), um(c_.y)
        ux_a, uy_a = OX + ux_rel, OY + uy_rel
        if abs(ax - ux_a) > abs(ay - uy_a):
            ox_, oy_ = ux_a + (1 if ax > ux_a else -1) * 4.15, ay
        else:
            ox_, oy_ = ax, uy_a + (1 if ay > uy_a else -1) * 4.15
        for (p0x, p0y), (p1x, p1y) in (((ax, ay), (ox_, oy_)), ((ox_, oy_), (cx_, cy_))):
            if math.hypot(p1x - p0x, p1y - p0y) > 1e-4:
                tr = pcbnew.PCB_TRACK(b)
                tr.SetStart(pcbnew.VECTOR2I(mm(p0x), mm(p0y)))
                tr.SetEnd(pcbnew.VECTOR2I(mm(p1x), mm(p1y)))
                tr.SetWidth(mm(0.20))
                tr.SetLayer(B_CU)
                tr.SetNetCode(v33_code)
                tr.SetLocked(True)
                b.Add(tr)

    # FB Kelvin sense: U3 pin 50 (+1V1) straight down, jog left clear of pin 51 escape into vendor +1V1 COUT pour
    p50_pos = next(p for p in fps["U3"].Pads() if p.GetNumber() == "50").GetPosition()
    ux_a, uy_a = OX + ux_rel, OY + uy_rel
    fb_segs = [
        ((um(p50_pos.x), um(p50_pos.y)), (ux_a + 1.20, uy_a + 3.90), 0.20),
        ((ux_a + 1.20, uy_a + 3.90), (ux_a + 1.04, uy_a + 4.06), 0.12),
        ((ux_a + 1.04, uy_a + 4.06), (ux_a + 1.04, uy_a + 5.20), 0.12),
    ]
    for (p0x, p0y), (p1x, p1y), w_fb in fb_segs:
        tr = pcbnew.PCB_TRACK(b)
        tr.SetStart(pcbnew.VECTOR2I(mm(p0x), mm(p0y)))
        tr.SetEnd(pcbnew.VECTOR2I(mm(p1x), mm(p1y)))
        tr.SetWidth(mm(w_fb))
        tr.SetLayer(B_CU)
        tr.SetNetCode(v11_code)
        tr.SetLocked(True)
        b.Add(tr)

    # Vendor regulator zones (PGND prio 4, VREG_LX prio 5, +1V1 COUT prio 6, +3V3 CIN prio 7),
    # trimmed clear of any foreign B.Cu pads (e.g. R14.2) and protected by B.Cu rule areas against foreign intrusions!
    from shapely.geometry import Point, Polygon
    from shapely.ops import unary_union

    bcu_pad_polys = []
    for f in b.GetFootprints():
        if f.GetLayer() == pcbnew.B_Cu:
            for p in f.Pads():
                if p.IsOnLayer(B_CU):
                    o_p = p.GetEffectivePolygon(B_CU).Outline(0)
                    poly_p = Polygon([(um(o_p.CPoint(i).x) - OX, um(o_p.CPoint(i).y) - OY) for i in range(o_p.PointCount())])
                    if poly_p.is_valid and not poly_p.is_empty:
                        bcu_pad_polys.append((p.GetNetname(), poly_p))

    vzones = json.loads(VENDOR_ZONES.read_text())
    for q in vzones:
        if q["prio"] <= 3:
            continue
        net = {"/VREG_LX": "/MCU/VREG_LX"}.get(q["net"], q["net"])
        raw_poly = Polygon([(ux_rel + x, uy_rel - y) for x, y in q["pts"]]).buffer(0)
        for pnet, ppoly in bcu_pad_polys:
            if pnet != net:
                raw_poly = raw_poly.difference(ppoly.buffer(0.18, 8))
        if hasattr(raw_poly, "geoms"):
            raw_poly = max(raw_poly.geoms, key=lambda g: g.area)
        z_pts = [(round(x, 4), round(y, 4)) for x, y in list(raw_poly.exterior.coords)[:-1]]
        add_zone(f"vendor {net}", B_CU, net, z_pts, q["prio"], minw=0.10, clear=0.12)
        add_area(f"vendor {net} area", B_CU, z_pts)
        if net.endswith("VREG_LX"):
            lx_zone_poly = raw_poly

    # In1.Cu GND cutout under the LX node (chips/rp2350.md §6.3.8.1): the VREG_LX zone plus the LX pads
    # of U3 and L1, grown 0.25 mm. Not their bounding box, which also cleared plane under pins 46/47.
    lx_polys = [lx_zone_poly] + [ppoly for pnet, ppoly in bcu_pad_polys if pnet.endswith("VREG_LX")]
    lx_cut = unary_union([g.buffer(0) for g in lx_polys]).buffer(0.25, join_style=2, mitre_limit=1.5).simplify(0.01)
    if hasattr(lx_cut, "geoms"):
        lx_cut = max(lx_cut.geoms, key=lambda g: g.area)
    add_area("LX cutout L2", IN1_CU, [(round(x, 4), round(y, 4)) for x, y in list(lx_cut.exterior.coords)[:-1]],
             tracks=True, pour=True)
    if spec.extra_side_buttons:
        add_area("LX cutout L3", IN2_CU, [(round(x, 4), round(y, 4)) for x, y in list(lx_cut.exterior.coords)[:-1]],
                 tracks=True, pour=True)

    # Fill zones first so we place single-point PGND vias squarely inside the actual filled vendor GND pour!

    b.BuildConnectivity()
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())

    vgnd_polys = []
    for z in b.Zones():
        if z.GetZoneName() == "vendor GND":
            ps = z.GetFilledPolysList(B_CU)
            for k in range(ps.OutlineCount()):
                o = ps.Outline(k)
                pts = [(um(o.CPoint(i).x), um(o.CPoint(i).y)) for i in range(o.PointCount())]
                if len(pts) >= 3:
                    vgnd_polys.append(Polygon(pts).buffer(0))
    vgnd_core = unary_union(vgnd_polys).buffer(-0.12) if vgnd_polys else Polygon()

    bcu_pads = [
        (um(q.GetLeft()), um(q.GetTop()), um(q.GetRight()), um(q.GetBottom()), p.GetNetname())
        for f in b.GetFootprints()
        if f.GetLayer() == pcbnew.B_Cu
        for p in f.Pads()
        for q in [p.GetBoundingBox()]
    ]

    def pgnd_free(xa, ya):
        if not fcu_clear(xa, ya):
            return False
        for a, e, g, h, n in bcu_pads:
            if n != "GND" and math.hypot(max(a - xa, 0.0, xa - g), max(e - ya, 0.0, ya - h)) < 0.265:
                return False
        return all(math.hypot(xa - ax, ya - ay) >= 0.60 for ax, ay in placed_vias)

    pg_placed = 0
    if not vgnd_core.is_empty:
        bx0, by0, bx1, by1 = vgnd_core.bounds
        xv = bx0
        while xv <= bx1 + 1e-6 and pg_placed < 2:
            yv = by0
            while yv <= by1 + 1e-6 and pg_placed < 2:
                if vgnd_core.contains(Point(xv, yv)) and pgnd_free(xv, yv):
                    v = pcbnew.PCB_VIA(b)
                    v.SetPosition(pcbnew.VECTOR2I(mm(round(xv, 3)), mm(round(yv, 3))))
                    v.SetWidth(mm(0.30))
                    v.SetDrill(mm(0.15))
                    v.SetLayerPair(F_CU, B_CU)
                    v.SetNetCode(gnd_code)
                    v.SetLocked(True)
                    b.Add(v)
                    placed_vias.append((round(xv, 3), round(yv, 3)))
                    pg_placed += 1
                yv += 0.05
            xv += 0.05
    print(f"[{spec.name}] PGND vias placed: {pg_placed}")

    b.BuildConnectivity()
    filler.Fill(b.Zones())
    for z in b.Zones():
        if not z.GetIsRuleArea():
            for l in z.GetLayerSet().Seq():
                ps = z.GetFilledPolysList(l)
                if z.GetZoneName() in ("plane GND", "RP2350 band", "RP2350 ring"):
                    print(f"  zone {z.GetZoneName():<14} ({b.GetLayerName(l)}): pieces={ps.OutlineCount()}, area={ps.Area()/1e12:.1f} mm^2")

    pcbnew.SaveBoard(str(pcb_path), b)
    pro_path.write_bytes(pro_bytes)
    print(f"zones saved: {pcb_path}", flush=True)
    os._exit(0)


def stage_models(spec: VariantSpec):
    """Attach 3D STEP models to all custom footprints for pcbview."""
    import pcbnew

    hw = spec.hw_dir
    pcb_path = hw / "parallelogram.kicad_pcb"
    pro_path = hw / "parallelogram.kicad_pro"
    pro_bytes = pro_path.read_bytes()

    base = "${KIPRJMOD}/../../../3dmodels/"
    model_map = {
        "LED_XL-1010RGB": (base + "XL-1010RGB-YG.step", 0, (0.0, 0.0, 0.0)),
        "LED_XL-1615RGBC": (base + "LED-ARRAY-SMD_4P-L1.6-W1.5-BR_XL-1615RGBC-RF.step", 180, (0.0, 0.0, 0.0)),
        "SENSOR_ALS-PT19": (base + "SENSORS-SMD_L1.7-W0.8-H0.6.step", 0, (0.0, 0.0, 0.0)),
        "AW20198_QFN-40-1EP_5x5mm_P0.4mm_EP3.4x3.4mm": (
            "${KICAD9_3DMODEL_DIR}/Package_DFN_QFN.3dshapes/TQFN-40-1EP_5x5mm_P0.4mm_EP3.5x3.5mm.step",
            0,
            (0.0, 0.0, 0.0),
        ),
        "RP2350-QFN-60-1EP_7x7_P0.4mm_EP3.4x3.4mm_ThermalVias": (base + "QFN-60_L7.0-W7.0-P0.40-TL-EP3.4.step", 0, (0.0, 0.0, 0.0)),
        "L_pol_2016": (base + "IND-SMD_L2.0-W1.6_AOTA-B201610S3R3-101-T.step", 0 if spec.extra_side_buttons else 180, (0.0, 0.0, 0.0)),
        "SW_Panasonic_EVQP7J": (base + "SW-SMD_EVQP7C01P-L3.6-W3.5-H1.4-P3.6-LS4.7.step", 0, (0.0, 0.0, 0.0)),
        "XySemi_DFN-6_1.8x1.4mm": (base + "DFNFC-6_L1.8-W1.4-H0.6-P0.50-BL_XB9901A.step", 0, (0.0, 0.0, 0.56)),
        "Texas_X2SON-4_1x1mm_P0.65mm": (base + "X2SON-4_L1.0-W1.0-H0.4-P0.65-TL-EPSLDPRT.step", 270, (0.0, 0.0, 0.0)),
        "USB_C_Receptacle_Hroparts_TYPE-C-31-M-22": (base + "USB-C-SMD_TYPE-C-31-M-22.step", 0, (0.0, -1.06, 1.63)),
        "Molex_PicoBlade_53261-0271_1x02-1MP_P1.25mm_Horizontal": (
            "${KICAD9_3DMODEL_DIR}/Connector_Molex.3dshapes/Molex_PicoBlade_53261-0271_1x02-1MP_P1.25mm_Horizontal.step",
            0,
            (0.0, 0.0, 0.0),
        ),
        "SW_Push_1P1T_XKB_TS-1187A": (base + "SW-SMD_4P-L5.1-W5.1-P3.70-LS6.5-TL_H1.5.step", 0, (0.0, 0.0, 0.0)),
    }

    b = pcbnew.LoadBoard(str(pcb_path))
    n = 0
    for f in b.GetFootprints():
        name = str(f.GetFPID().GetUniStringLibItemName())
        if name in model_map:
            fn, rot, xyz_off = model_map[name]
            ms = f.Models()
            ms.clear()
            m = pcbnew.FP_3DMODEL()
            m.m_Filename = fn
            m.m_Rotation = pcbnew.VECTOR3D(0, 0, rot)
            m.m_Show = True
            m.m_Offset = pcbnew.VECTOR3D(*xyz_off)
            ms.push_back(m)
            n += 1

    pcbnew.SaveBoard(str(pcb_path), b)
    pro_path.write_bytes(pro_bytes)
    print(f"[{spec.name}] 3D models set on {n} footprints", flush=True)
    os._exit(0)


def stage_post_silk(spec: VariantSpec):
    """Add skewed lattice front silkscreen web (clipped clear of LEDs, Q2, and exposed vias) + connector polarity labels."""
    import pcbnew

    hw = spec.hw_dir
    pcb_path = hw / "parallelogram.kicad_pcb"
    pro_path = hw / "parallelogram.kicad_pro"
    pro_bytes = pro_path.read_bytes()

    b = pcbnew.LoadBoard(str(pcb_path))
    mm = pcbnew.FromMM
    um = pcbnew.ToMM
    fps = {f.GetReference(): f for f in b.GetFootprints()}

    # Clear any old graphic silkscreen segments on F.SilkS / B.SilkS and strip footprint silk strokes that could touch vias
    keep_alive = []
    for d in list(b.GetDrawings()):
        if d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            b.Remove(d)
            keep_alive.append(d)
    for f in b.GetFootprints():
        f.Reference().SetVisible(False)
        f.Value().SetVisible(False)
        for gi in list(f.GraphicalItems()):
            if gi.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
                f.Remove(gi)
                keep_alive.append(gi)

    # Obstacles on F.Cu (pads & any F.Mask / NPTH openings) so F.SilkS web never causes silk_over_copper!
    # Note: vias are tented on F.Mask so F.SilkS over tented vias is clean, though we also keep clear of F.Cu pads!
    fcu_obs = []
    for f in b.GetFootprints():
        if f.GetLayer() == pcbnew.F_Cu and f.GetReference() == "Q2":
            bb = f.GetBoundingBox(False, False)
            fcu_obs.append((um(bb.GetLeft()) - OX - 0.35, um(bb.GetTop()) - OY - 0.35, um(bb.GetRight()) - OX + 0.35, um(bb.GetBottom()) - OY + 0.35))
        else:
            for p in f.Pads():
                if f.GetLayer() == pcbnew.F_Cu or p.IsOnLayer(pcbnew.F_Mask):
                    bb = p.GetBoundingBox()
                    fcu_obs.append((um(bb.GetLeft()) - OX - 0.25, um(bb.GetTop()) - OY - 0.25, um(bb.GetRight()) - OX + 0.25, um(bb.GetBottom()) - OY + 0.25))

    def pt_ok_f(x: float, y: float) -> bool:
        if not inside_parallelogram(x, y, 0.55):
            return False
        for a, e, g, h in fcu_obs:
            if a <= x <= g and e <= y <= h:
                return False
        return True

    def add_clipped_line(x0, y0, x1, y1, layer, width=0.15):
        dist = math.hypot(x1 - x0, y1 - y0)
        steps = max(4, int(dist / 0.08))
        cur_start = None
        added = 0
        for k in range(steps + 1):
            t = k / steps
            px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            ok = pt_ok_f(px, py)
            if ok and cur_start is None:
                cur_start = (px, py)
            elif not ok and cur_start is not None:
                prev = (x0 + (x1 - x0) * ((k - 1) / steps), y0 + (y1 - y0) * ((k - 1) / steps))
                if math.hypot(prev[0] - cur_start[0], prev[1] - cur_start[1]) >= 0.35:
                    s = pcbnew.PCB_SHAPE(b)
                    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
                    s.SetLayer(layer)
                    s.SetWidth(mm(width))
                    s.SetStart(pcbnew.VECTOR2I(mm(OX + cur_start[0]), mm(OY + cur_start[1])))
                    s.SetEnd(pcbnew.VECTOR2I(mm(OX + prev[0]), mm(OY + prev[1])))
                    b.Add(s)
                    added += 1
                cur_start = None
        if cur_start is not None and math.hypot(x1 - cur_start[0], y1 - cur_start[1]) >= 0.35:
            s = pcbnew.PCB_SHAPE(b)
            s.SetShape(pcbnew.SHAPE_T_SEGMENT)
            s.SetLayer(layer)
            s.SetWidth(mm(width))
            s.SetStart(pcbnew.VECTOR2I(mm(OX + cur_start[0]), mm(OY + cur_start[1])))
            s.SetEnd(pcbnew.VECTOR2I(mm(OX + x1), mm(OY + y1)))
            b.Add(s)
            added += 1
        return added

    # Draw artistic skewed diamond/parallelogram lattice web on F.SilkS along LED cell midpoints!
    seg_cnt = 0
    for ic in range(spec.cols + 1):
        xg = (ic - spec.cols / 2.0) * spec.px
        v_top = (-spec.rows / 2.0) * spec.py
        v_bot = (spec.rows / 2.0) * spec.py
        seg_cnt += add_clipped_line(xg, v_top + SKEW * xg, xg, v_bot + SKEW * xg, pcbnew.F_SilkS, 0.15)
    for ir in range(spec.rows + 1):
        vg = (ir - spec.rows / 2.0) * spec.py
        x_l = (-spec.cols / 2.0) * spec.px
        x_r = (spec.cols / 2.0) * spec.px
        seg_cnt += add_clipped_line(x_l, vg + SKEW * x_l, x_r, vg + SKEW * x_r, pcbnew.F_SilkS, 0.15)

    # Add Q2 collector pin-1 dot on F.SilkS
    q2_p1 = next(p for p in fps["Q2"].Pads() if p.GetNumber() == "1").GetPosition()
    q2_dot = pcbnew.PCB_SHAPE(b)
    q2_dot.SetShape(pcbnew.SHAPE_T_CIRCLE)
    q2_dot.SetFilled(True)
    q2_dot.SetLayer(pcbnew.F_SilkS)
    q2_dot.SetWidth(mm(0.05))
    dx_q, dy_q = um(q2_p1.x) - OX - 0.72, um(q2_p1.y) - OY - 0.22
    q2_dot.SetCenter(pcbnew.VECTOR2I(mm(OX + dx_q), mm(OY + dy_q)))
    q2_dot.SetEnd(pcbnew.VECTOR2I(mm(OX + dx_q + 0.15), mm(OY + dy_q)))
    b.Add(q2_dot)

    # Add clean B.SilkS connector & cell labels clear of all B.Mask openings (and outside USB/JST/button housings)
    bmask_obs = []
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.IsOnLayer(pcbnew.B_Mask):
                bb = p.GetBoundingBox()
                bmask_obs.append((um(bb.GetLeft()) - OX - 0.22, um(bb.GetTop()) - OY - 0.22, um(bb.GetRight()) - OX + 0.22, um(bb.GetBottom()) - OY + 0.22))
    if spec.io_mode == "usb":
        for body_ref in ("J1", "BT1", "SW3", "SW4") + (("SW5", "SW6") if spec.extra_side_buttons else ()):
            if body_ref in fps:
                bb = fps[body_ref].GetBoundingBox(False, False)
                bmask_obs.append((um(bb.GetLeft()) - OX - 0.10, um(bb.GetTop()) - OY - 0.10, um(bb.GetRight()) - OX + 0.10, um(bb.GetBottom()) - OY + 0.10))

    if spec.extra_side_buttons:
        from shapely.affinity import translate
        from shapely.geometry import Point, Polygon, box
        from shapely.ops import unary_union
        from shapely.prepared import prep

        b.GetTitleBlock().SetTitle(spec.name)
        board_inner = Polygon(poly_vertices(inset=0.25)).buffer(0)
        obs_geoms = []
        for f in b.GetFootprints():
            for p in f.Pads():
                if p.IsOnLayer(pcbnew.B_Mask):
                    o_p = p.GetEffectivePolygon(pcbnew.B_Mask)
                    if o_p.OutlineCount():
                        ol = o_p.Outline(0)
                        pts_p = [(um(ol.CPoint(i).x) - OX, um(ol.CPoint(i).y) - OY) for i in range(ol.PointCount())]
                        if len(pts_p) >= 3:
                            obs_geoms.append(Polygon(pts_p).buffer(0.155, 8))
                if p.HasHole():
                    hx, hy = um(p.GetPosition().x) - OX, um(p.GetPosition().y) - OY
                    obs_geoms.append(Point(hx, hy).buffer(um(p.GetDrillSizeX()) / 2.0 + 0.18, 16))
        for tr in b.GetTracks():
            if tr.Type() == pcbnew.PCB_VIA_T:
                vx, vy = um(tr.GetPosition().x) - OX, um(tr.GetPosition().y) - OY
                obs_geoms.append(Point(vx, vy).buffer(um(tr.GetWidth(pcbnew.F_Cu)) / 2.0 + 0.125, 12))

        # Build solid 3D package body hulls AND courtyards FIRST so BOTH Pin-1 dots and text stay visible outside all bodies!
        body_geoms = []
        court_polys = {}
        bcu_courts = {}
        for rf, fp_ in fps.items():
            if fp_.IsFlipped():
                fp_.BuildCourtyardCaches()
                cy_ = fp_.GetCourtyard(pcbnew.B_CrtYd)
                if cy_.OutlineCount():
                    bcu_courts[rf] = cy_
                    ol_c = cy_.Outline(0)
                    cpts = [(um(ol_c.CPoint(i).x) - OX, um(ol_c.CPoint(i).y) - OY) for i in range(ol_c.PointCount())]
                    if len(cpts) >= 3:
                        court_polys[rf] = Polygon(cpts).buffer(0)
                if rf in ("J1", "SW4", "BT1") and rf in court_polys:
                    body_geoms.append(court_polys[rf].buffer(-0.04))
                elif not rf.startswith("TP"):
                    fab_bbs = [gi.GetBoundingBox() for gi in fp_.GraphicalItems() if gi.GetLayer() == pcbnew.B_Fab]
                    if fab_bbs:
                        bx0 = max(-12.40, min(um(bb.GetLeft()) - OX for bb in fab_bbs))
                        by0 = min(um(bb.GetTop()) - OY for bb in fab_bbs)
                        bx1 = min(12.40, max(um(bb.GetRight()) - OX for bb in fab_bbs))
                        by1 = max(um(bb.GetBottom()) - OY for bb in fab_bbs)
                        pad_m = 0.16 if rf.startswith(("U", "SW", "BT", "L", "Y", "Q")) else 0.08
                        body_geoms.append(box(bx0 - pad_m, by0 - pad_m, bx1 + pad_m, by1 + pad_m))

        b_free_body = board_inner.difference(unary_union(obs_geoms + body_geoms))
        pfree_body = prep(b_free_body)
        b_free_nocrt = b_free_body.difference(unary_union(list(court_polys.values()))) if court_polys else b_free_body
        pfree_nocrt = prep(b_free_nocrt)
        tp_court_union = unary_union([g.buffer(0.15) for k, g in court_polys.items() if k.startswith("TP")]) if court_polys else Polygon()
        placed_silk_geoms: list[tuple[str, Polygon]] = []

        def poly_set_to_shapely(ps):
            geoms = []
            for k in range(ps.OutlineCount()):
                ol = ps.Outline(k)
                ext = [(um(ol.CPoint(i).x) - OX, um(ol.CPoint(i).y) - OY) for i in range(ol.PointCount())]
                if len(ext) >= 3:
                    holes = []
                    for h in range(ps.HoleCount(k)):
                        hl = ps.Hole(k, h)
                        hpts = [(um(hl.CPoint(i).x) - OX, um(hl.CPoint(i).y) - OY) for i in range(hl.PointCount())]
                        if len(hpts) >= 3:
                            holes.append(hpts)
                    g = Polygon(ext, holes)
                    if not g.is_valid:
                        g = g.buffer(0)
                    if not g.is_empty:
                        geoms.append(g)
            return unary_union(geoms) if geoms else Polygon()

        # 1. Place B.Cu IC/inductor/crystal Pin-1 dots OUTSIDE 3D bodies and clear of all mask/via obstacles!
        ic_refs = ["U3", "U1", "U2", "U10", "U11", "U4", "U5", "U6", "U7", "U8", "U9", "Q1", "L1", "Y1"]
        p1_dots = 0
        for r in ic_refs:
            if r not in fps:
                continue
            pads_dict = {p.GetNumber(): p for p in fps[r].Pads()}
            p1 = pads_dict.get("1") or pads_dict.get("A1")
            if p1 is None:
                continue
            px0, py0 = um(p1.GetPosition().x) - OX, um(p1.GetPosition().y) - OY
            p1_half = max(um(p1.GetBoundingBox().GetWidth()), um(p1.GetBoundingBox().GetHeight())) / 2.0
            fcx, fcy = um(fps[r].GetPosition().x) - OX, um(fps[r].GetPosition().y) - OY
            other_pads = [
                (um(op.GetPosition().x) - OX, um(op.GetPosition().y) - OY)
                for num, op in pads_dict.items()
                if num not in ("1", "A1") and op.GetPosition() != p1.GetPosition()
            ]
            ux_out = (px0 - fcx) / (math.hypot(px0 - fcx, py0 - fcy) or 1.0)
            uy_out = (py0 - fcy) / (math.hypot(px0 - fcx, py0 - fcy) or 1.0)
            placed_dot = False
            max_reach = p1_half + (1.18 if r.startswith(("U", "Q")) else 1.55)
            for dot_r in (0.14, 0.11, 0.085):
                dot_cands = []
                for ix_d in range(-28, 29):
                    for iy_d in range(-28, 29):
                        ddx, ddy = ix_d * 0.05, iy_d * 0.05
                        dist_c = math.hypot(ddx, ddy)
                        if 0.30 <= dist_c <= max_reach:
                            out_proj = (ddx * ux_out + ddy * uy_out) / dist_c
                            dot_cands.append((dist_c - 0.38 * out_proj, px0 + ddx, py0 + ddy))
                dot_cands.sort(key=lambda item: item[0])
                for _, dx_b, dy_b in dot_cands:
                    d1 = math.hypot(dx_b - px0, dy_b - py0)
                    if any(math.hypot(dx_b - ox, dy_b - oy) <= d1 + 0.008 for ox, oy in other_pads):
                        continue
                    dg = Point(dx_b, dy_b).buffer(dot_r + 0.025, 16)
                    if pfree_body.contains(dg) and all(dg.distance(pg) >= 0.16 for _, pg in placed_silk_geoms):
                        dot = pcbnew.PCB_SHAPE(b)
                        dot.SetShape(pcbnew.SHAPE_T_CIRCLE)
                        dot.SetFilled(True)
                        dot.SetLayer(pcbnew.B_SilkS)
                        dot.SetWidth(mm(0.05))
                        dot.SetCenter(pcbnew.VECTOR2I(mm(OX + dx_b), mm(OY + dy_b)))
                        dot.SetEnd(pcbnew.VECTOR2I(mm(OX + dx_b + dot_r), mm(OY + dy_b)))
                        b.Add(dot)
                        placed_silk_geoms.append((f"dot:{r}", dg))
                        p1_dots += 1
                        placed_dot = True
                        break
                if placed_dot:
                    break

        def make_text_template(txt: str, deg: float, sz: float = 0.80):
            t0 = pcbnew.PCB_TEXT(b)
            t0.SetText(txt)
            t0.SetLayer(pcbnew.B_SilkS)
            t0.SetTextSize(pcbnew.VECTOR2I(mm(sz), mm(sz)))
            t0.SetTextThickness(mm(0.15))
            t0.SetMirrored(True)
            t0.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
            t0.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
            t0.SetPosition(pcbnew.VECTOR2I(mm(OX), mm(OY)))
            t0.SetTextAngleDegrees(deg)
            ps0 = pcbnew.SHAPE_POLY_SET()
            t0.TransformTextToPolySet(ps0, 0, mm(0.006), pcbnew.ERROR_INSIDE)
            return t0, poly_set_to_shapely(ps0)

        major_refs = [
            "SW5", "SW6", "SW1", "SW2", "SW3", "SW4", "J1", "BT1",
            "U3", "U1", "U2", "U4", "U5", "U6", "U7", "U8", "U9",
            "Y1", "L1", "Q1",
        ]
        major_courts = {r: bcu_courts[r] for r in major_refs if r in bcu_courts}

        def place_radial_usb6(
            txt: str,
            tx0: float,
            ty0: float,
            rad: float,
            degs=(0.0, 90.0),
            sz: float = 0.80,
            must_nearest_ref: str | None = None,
            must_nearest_major: str | None = None,
            prefer_nocrt: bool = True,
            extra_pred=None,
            min_gap: float = 0.20,
            tag: str = "lbl",
        ):
            free_spaces = [pfree_nocrt, pfree_body] if prefer_nocrt else [pfree_body]
            for pf in free_spaces:
                for deg in degs:
                    t0, g0 = make_text_template(txt, deg, sz)
                    if g0.is_empty:
                        continue
                    cands = []
                    for ix in range(-121, 122, 2):
                        xc = ix / 10.0
                        if abs(xc - tx0) > rad:
                            continue
                        for iy in range(-346, 347, 2):
                            yc = iy / 10.0
                            dc = math.hypot(xc - tx0, yc - ty0)
                            if dc <= rad:
                                cands.append((dc, xc, yc))
                    cands.sort()
                    for _, xc, yc in cands:
                        if extra_pred is not None and not extra_pred(xc, yc):
                            continue
                        pt_c = pcbnew.VECTOR2I(mm(OX + xc), mm(OY + yc))
                        if must_nearest_ref and must_nearest_ref in bcu_courts:
                            if min(bcu_courts, key=lambda k: bcu_courts[k].SquaredDistance(pt_c)) != must_nearest_ref:
                                continue
                        if must_nearest_major and must_nearest_major in major_courts:
                            if min(major_courts, key=lambda k: major_courts[k].SquaredDistance(pt_c)) != must_nearest_major:
                                continue
                            if major_courts[must_nearest_major].SquaredDistance(pt_c) > (3.2 * 1e6) ** 2:
                                continue
                        g = translate(g0, xc, yc)
                        if pf.contains(g) and all(
                            g.distance(pg) >= (1.10 if (tag == "id" and ptag == "btn") or (tag == "btn" and ptag == "id") else min_gap)
                            for ptag, pg in placed_silk_geoms
                        ):
                            t0.SetPosition(pcbnew.VECTOR2I(mm(OX + xc), mm(OY + yc)))
                            b.Add(t0)
                            placed_silk_geoms.append((tag, g))
                            return True
            return False

        # 2. Connector polarity & function/rating labels (strictly 0° / 90° only!)
        bt_p1 = next(p for p in fps["BT1"].Pads() if p.GetNumber() == "1").GetPosition()
        bt_p2 = next(p for p in fps["BT1"].Pads() if p.GetNumber() == "2").GetPosition()
        p1x, p1y = um(bt_p1.x) - OX, um(bt_p1.y) - OY  # VBAT (+) West rear pad at (+7.345, +25.400)
        p2x, p2y = um(bt_p2.x) - OX, um(bt_p2.y) - OY  # BAT_N (-) East rear pad at (+8.595, +25.400)
        place_radial_usb6(
            "+", p1x - 1.05, p1y + 0.15, 2.5, (0.0,), 0.85,
            prefer_nocrt=False,
            extra_pred=lambda xc, yc: xc <= p1x - 0.15 and math.hypot(xc - p1x, yc - p1y) + 0.30 < math.hypot(xc - p2x, yc - p2y),
            tag="conn",
        )
        place_radial_usb6(
            "-", p2x + 1.05, p2y - 0.15, 2.5, (0.0,), 0.85,
            prefer_nocrt=False,
            extra_pred=lambda xc, yc: xc >= p2x + 0.15 and math.hypot(xc - p2x, yc - p2y) + 0.30 < math.hypot(xc - p1x, yc - p1y),
            tag="conn",
        )
        if not place_radial_usb6("BATT 3.7V", 10.60, 18.20, 6.0, (90.0, 0.0), 0.80, must_nearest_ref="BT1", tag="conn"):
            place_radial_usb6("BATT", 10.60, 18.20, 6.0, (90.0, 0.0), 0.80, must_nearest_ref="BT1", tag="conn")

        bt1_crt = court_polys.get("BT1", Polygon()).buffer(0.20)
        if not place_radial_usb6(
            "USB 5V", -1.24, 26.82, 11.5, (0.0, 90.0), 0.80,
            must_nearest_ref="J1", extra_pred=lambda xc, yc: not bt1_crt.contains(Point(xc, yc)), tag="conn",
        ):
            if not place_radial_usb6(
                "5V", -1.24, 26.82, 11.5, (0.0, 90.0), 0.80,
                must_nearest_ref="J1", extra_pred=lambda xc, yc: not bt1_crt.contains(Point(xc, yc)), tag="conn",
            ):
                place_radial_usb6(
                    "5V", -1.24, 26.82, 11.5, (0.0, 90.0), 0.80,
                    must_nearest_ref="J1", prefer_nocrt=False,
                    extra_pred=lambda xc, yc: not bt1_crt.contains(Point(xc, yc)), tag="conn",
                )

        # 3. All 6 button function labels (clear of TP courtyards!)
        place_radial_usb6("USER_C", -11.30, -17.60, 6.5, (90.0, 0.0), 0.80, extra_pred=lambda xc, yc: yc <= -15.2, tag="btn")
        place_radial_usb6("USER_D", -11.30, 18.20, 6.5, (90.0, 0.0), 0.80, extra_pred=lambda xc, yc: yc >= 15.5, tag="btn")
        place_radial_usb6("PWR", 10.90, 4.90, 5.5, (0.0, 90.0), 0.80, tag="btn")
        place_radial_usb6(
            "BOOT", -11.20, -7.20, 6.0, (90.0, 0.0), 0.80,
            extra_pred=lambda xc, yc: not tp_court_union.contains(Point(xc, yc)), tag="btn",
        )
        place_radial_usb6("USER_A", -5.00, -29.60, 6.5, (0.0, 90.0), 0.80, tag="btn")
        if not place_radial_usb6(
            "USER_B", 7.30, 27.50, 5.5, (0.0, 90.0), 0.80,
            prefer_nocrt=False, extra_pred=lambda xc, yc: yc >= 26.40, tag="btn",
        ):
            place_radial_usb6(
                "USR_B", 7.30, 27.50, 5.5, (0.0, 90.0), 0.80,
                prefer_nocrt=False, extra_pred=lambda xc, yc: yc >= 26.40, tag="btn",
            )

        # 4. Contiguous 3-line repository URL block + required board identity (placed BEFORE optional TP/minor labels!)
        def place_contiguous_url_usb6() -> bool:
            u1, u2, u3 = "github.com/", "sequoia-hope/", "round-pendant"
            def make_url_tpl(txt: str, deg: float):
                t = pcbnew.PCB_TEXT(b)
                t.SetText(txt)
                t.SetLayer(pcbnew.B_SilkS)
                t.SetTextSize(pcbnew.VECTOR2I(mm(0.68), mm(0.80)))
                t.SetTextThickness(mm(0.15))
                t.SetMirrored(True)
                t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
                t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
                t.SetPosition(pcbnew.VECTOR2I(mm(OX), mm(OY)))
                t.SetTextAngleDegrees(deg)
                ps0 = pcbnew.SHAPE_POLY_SET()
                t.TransformTextToPolySet(ps0, 0, mm(0.006), pcbnew.ERROR_INSIDE)
                return t, poly_set_to_shapely(ps0)

            t1, g1_0 = make_url_tpl(u1, 90.0)
            t2, g2_0 = make_url_tpl(u2, 90.0)
            t3, g3_0 = make_url_tpl(u3, 90.0)
            v1, v2, v3 = [], [], []
            for ix in range(-115, 116, 2):
                for iy in range(-280, 281, 5):
                    xc, yc = round(ix / 10.0, 2), round(iy / 10.0, 2)
                    for g0, out in ((g1_0, v1), (g2_0, v2), (g3_0, v3)):
                        g = translate(g0, xc, yc)
                        if pfree_body.contains(g) and all(
                            g.distance(pg) >= (1.40 if ptag == "btn" else 0.18) for ptag, pg in placed_silk_geoms
                        ):
                            out.append((xc, yc, g))
            best = None
            for x1, y1, g1 in v1:
                for x2, y2, g2 in v2:
                    if not ((0.95 <= x1 - x2 <= 4.00 and abs(y2 - y1) <= 7.50) or (abs(x1 - x2) <= 0.25 and 7.50 <= y2 - y1 <= 11.50)):
                        continue
                    if g1.distance(g2) < 0.22:
                        continue
                    for x3, y3, g3 in v3:
                        if not ((0.95 <= x2 - x3 <= 4.00 and abs(y3 - y2) <= 7.50) or (abs(x2 - x3) <= 0.25 and 8.00 <= y3 - y2 <= 12.00)):
                            continue
                        score = abs(x1 - x2) + abs(x2 - x3) + 0.35 * (abs(y2 - y1) + abs(y3 - y2)) - 0.1 * x1
                        if best is not None and score >= best[0]:
                            continue
                        if g2.distance(g3) >= 0.22 and g1.distance(g3) >= 0.22:
                            best = (score, x1, y1, g1, x2, y2, g2, x3, y3, g3)
            if best is not None:
                _, x1, y1, g1, x2, y2, g2, x3, y3, g3 = best
                t1.SetPosition(pcbnew.VECTOR2I(mm(OX + x1), mm(OY + y1)))
                t2.SetPosition(pcbnew.VECTOR2I(mm(OX + x2), mm(OY + y2)))
                t3.SetPosition(pcbnew.VECTOR2I(mm(OX + x3), mm(OY + y3)))
                b.Add(t1)
                b.Add(t2)
                b.Add(t3)
                placed_silk_geoms.extend([("id", g1), ("id", g2), ("id", g3)])
                return True
            return False

        place_contiguous_url_usb6()

        for id_txt, ix0, iy0, idegs in (
            (spec.name, -8.7, -12.0, (90.0, 0.0)),
            (f"rev {spec.title_rev}", 11.7, -11.5, (90.0, 0.0)),
            ("2026-11", -11.5, 6.8, (90.0, 0.0)),
            ("CERN-OHL-P", 11.7, -4.0, (90.0, 0.0)),
        ):
            place_radial_usb6(id_txt, ix0, iy0, 28.0, idegs, 0.80, prefer_nocrt=False, min_gap=0.20, tag="id")

        # 5. Bare SMD test point net labels FIRST (TP1..TP8 -> all 8/8 labeled on B.SilkS per silkscreen-and-art.md!)
        tp_net_labels = {
            "TP1": "VSYS", "TP2": "3V3", "TP3": "VBAT", "TP4": "1V1",
            "TP5": "RUN", "TP6": "CLK", "TP7": "DIO", "TP8": "GND",
        }
        tp_courts_only = {k: bcu_courts[k] for k in tp_net_labels if k in bcu_courts}
        tp_labeled = 0
        for tpr, tplbl in tp_net_labels.items():
            if tpr in fps:
                tpx = um(fps[tpr].GetPosition().x) - OX
                tpy = um(fps[tpr].GetPosition().y) - OY
                def tp_pred(xc: float, yc: float, _tpr: str = tpr) -> bool:
                    if not tp_courts_only or _tpr not in tp_courts_only:
                        return True
                    pt_t = pcbnew.VECTOR2I(mm(OX + xc), mm(OY + yc))
                    return min(tp_courts_only, key=lambda k: tp_courts_only[k].SquaredDistance(pt_t)) == _tpr
                tp_placed_ok = False
                tp_alts = ("VBAT", "BAT", "VB") if tpr == "TP3" else ("VSYS", "VS") if tpr == "TP1" else (tplbl,)
                for tp_str in tp_alts:
                    if place_radial_usb6(tp_str, tpx, tpy, 4.0, (0.0, 90.0), 0.80, prefer_nocrt=False, extra_pred=tp_pred, tag="tp"):
                        tp_labeled += 1
                        tp_placed_ok = True
                        break

        # 6. Selective major B.Cu designators via native fp.Reference() (so silk_check.py audits [under-part] & [association]!)
        def poly_overlaps_court(ps_txt, ps_crt) -> bool:
            if not ps_txt.OutlineCount() or not ps_crt.OutlineCount():
                return False
            if not ps_txt.BBox().Intersects(ps_crt.BBox()):
                return False
            tmp_ps = pcbnew.SHAPE_POLY_SET(ps_txt)
            tmp_ps.BooleanIntersection(ps_crt)
            return tmp_ps.OutlineCount() > 0

        des_placed = 0
        for r in major_refs:
            if r not in fps or r not in bcu_courts:
                continue
            fp_r = fps[r]
            field = fp_r.Reference()
            field.SetLayer(pcbnew.B_SilkS)
            field.SetTextSize(pcbnew.VECTOR2I(mm(0.80), mm(0.80)))
            field.SetTextThickness(mm(0.15))
            field.SetMirrored(True)
            if hasattr(field, "SetKeepUpright"):
                field.SetKeepUpright(False)
            field.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
            field.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
            fcx = um(fp_r.GetPosition().x) - OX
            fcy = um(fp_r.GetPosition().y) - OY
            mine_crt = bcu_courts[r]
            placed_ref = False
            # Try candidate angles yielding draw rotation 0° or 90° mod 180
            valid_f_degs = []
            seen_draw_mod = set()
            for cand_deg in (0.0, 90.0, 180.0, 270.0, -fp_r.GetOrientationDegrees(), 90.0 - fp_r.GetOrientationDegrees()):
                field.SetTextAngleDegrees(cand_deg)
                dmod = round(field.GetDrawRotation().AsDegrees()) % 180
                if dmod in (0, 90) and dmod not in seen_draw_mod:
                    seen_draw_mod.add(dmod)
                    valid_f_degs.append(cand_deg)
            cands_r = []
            for ix in range(-121, 122, 2):
                xc = ix / 10.0
                if abs(xc - fcx) > 5.2:
                    continue
                for iy in range(-346, 347, 2):
                    yc = iy / 10.0
                    dc = math.hypot(xc - fcx, yc - fcy)
                    if dc <= 5.2:
                        cands_r.append((dc, xc, yc))
            cands_r.sort()
            for cand_deg in valid_f_degs:
                field.SetTextAngleDegrees(cand_deg)
                for _, xc, yc in cands_r:
                    field.SetPosition(pcbnew.VECTOR2I(mm(OX + xc), mm(OY + yc)))
                    center_v = pcbnew.VECTOR2I(field.GetBoundingBox().GetCenter())
                    d_own = mine_crt.SquaredDistance(center_v) ** 0.5
                    if d_own > 1.85 * 1e6:
                        continue
                    # Strict silk_check.py [association] check against ALL 98 B.Cu courtyards (0.03 mm < silk_check's 0.05 mm)
                    if any(c_ps.SquaredDistance(center_v) ** 0.5 + 0.03 * 1e6 < d_own for r2, c_ps in bcu_courts.items() if r2 != r):
                        continue
                    ps_f = pcbnew.SHAPE_POLY_SET()
                    field.TransformTextToPolySet(ps_f, 0, mm(0.006), pcbnew.ERROR_INSIDE)
                    if any(poly_overlaps_court(ps_f, c_ps) for c_ps in bcu_courts.values()):
                        continue
                    g_f = poly_set_to_shapely(ps_f)
                    if not g_f.is_empty and pfree_nocrt.contains(g_f) and all(g_f.distance(pg) >= 0.20 for _, pg in placed_silk_geoms):
                        field.SetVisible(True)
                        placed_silk_geoms.append(("des", g_f))
                        des_placed += 1
                        placed_ref = True
                        break
                if placed_ref:
                    break
            if not placed_ref:
                field.SetVisible(False)

        place_radial_usb6("LIPO <=18x35", -1.5, -26.5, 28.0, (0.0, 90.0), 0.80, min_gap=0.22, tag="id")

        # 7. Clean, 100%-complete, 0-collision F.Fab (133/133 top parts) & B.Fab (98/98 bottom parts) assembly designators!
        # Update existing footprint F.Fab/B.Fab PCB_TEXT items in-place (KiCad 9 SaveBoard does not persist SetVisible(False)
        # on graphical FP_TEXT items), and add board-level PCB_TEXT only for custom footprints that lack one.
        for d in list(b.GetDrawings()):
            if d.GetLayer() in (pcbnew.F_Fab, pcbnew.B_Fab):
                b.Remove(d)
                keep_alive.append(d)

        def get_fp_fab_texts(fp_, lyr):
            return [gi for gi in fp_.GraphicalItems() if isinstance(gi, pcbnew.PCB_TEXT) and gi.GetLayer() == lyr]

        board_fab_inner = Polygon(poly_vertices(inset=0.18)).buffer(0)
        ffab_boxes: list[Polygon] = []
        ffab_placed = 0
        for rf in sorted(fps, key=lambda k: (0 if k == "Q2" else 1, int(k[1:]) if k[1:].isdigit() else 0, k)):
            fp_ = fps[rf]
            if fp_.IsFlipped():
                continue
            fcx, fcy = um(fp_.GetPosition().x) - OX, um(fp_.GetPosition().y) - OY
            sz_f = 0.44 if rf == "Q2" else 0.30
            th_f = 0.07 if rf == "Q2" else 0.05
            existing_f = get_fp_fab_texts(fp_, pcbnew.F_Fab)
            tf = existing_f[0] if existing_f else pcbnew.PCB_TEXT(b)
            for extra_gi in existing_f[1:]:
                fp_.Remove(extra_gi)
                keep_alive.append(extra_gi)
            if not existing_f:
                tf.SetText(rf)
                tf.SetLayer(pcbnew.F_Fab)
            tf.SetTextSize(pcbnew.VECTOR2I(mm(sz_f), mm(sz_f)))
            tf.SetTextThickness(mm(th_f))
            tf.SetMirrored(False)
            tf.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
            tf.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
            tf.SetTextAngleDegrees(0.0)
            tf.SetPosition(pcbnew.VECTOR2I(mm(OX + fcx), mm(OY + fcy)))
            bb_t = tf.GetBoundingBox()
            gb = box(um(bb_t.GetLeft()) - OX, um(bb_t.GetTop()) - OY, um(bb_t.GetRight()) - OX, um(bb_t.GetBottom()) - OY)
            if not existing_f:
                b.Add(tf)
            ffab_boxes.append(gb)
            ffab_placed += 1

        bfab_boxes: list[Polygon] = []
        bfab_placed = 0
        # Order tight/small parts first so every 0402/TP claims its exact package center, then larger ICs/switches
        def bfab_order(rf: str):
            if rf.startswith("TP"):
                return (0, rf)
            if rf.startswith(("R", "C")):
                return (1, rf)
            if rf in ("U6", "U7", "U8", "Q1", "L1"):
                return (2, rf)
            return (3, rf)

        for rf in sorted((k for k, v in fps.items() if v.IsFlipped()), key=bfab_order):
            fp_ = fps[rf]
            fcx, fcy = um(fp_.GetPosition().x) - OX, um(fp_.GetPosition().y) - OY
            if rf in ("U1", "U2", "U3", "U4", "U5", "J1", "BT1", "SW1", "SW2", "SW3", "SW4", "SW5", "SW6", "Y1"):
                sz_b, th_b = 0.62, 0.095
            elif rf in ("U8", "U9", "Q1", "L1", "C5", "C30", "C35"):
                sz_b, th_b = 0.42, 0.065
            else:
                sz_b, th_b = 0.31, 0.050
            ori_mod = round(fp_.GetOrientationDegrees()) % 180
            degs_b = (90.0, 0.0) if (rf.startswith(("R", "C")) and ori_mod == 90) else (0.0, 90.0)
            existing_b = get_fp_fab_texts(fp_, pcbnew.B_Fab)
            for extra_gi in existing_b[1:]:
                fp_.Remove(extra_gi)
                keep_alive.append(extra_gi)
            best_tb = None
            offsets_b = [(0.0, 0.0)]
            for r_step in (0.20, 0.40, 0.65, 0.90, 1.20, 1.55, 1.95):
                for ang_i in range(16):
                    ang = ang_i * math.pi / 8.0
                    offsets_b.append((round(r_step * math.cos(ang), 2), round(r_step * math.sin(ang), 2)))
            for deg_b in degs_b:
                for ox_b, oy_b in offsets_b:
                    tb = existing_b[0] if existing_b else pcbnew.PCB_TEXT(b)
                    if not existing_b:
                        tb.SetText(rf)
                        tb.SetLayer(pcbnew.B_Fab)
                    tb.SetTextSize(pcbnew.VECTOR2I(mm(sz_b), mm(sz_b)))
                    tb.SetTextThickness(mm(th_b))
                    tb.SetMirrored(True)
                    tb.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
                    tb.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
                    tb.SetTextAngleDegrees(deg_b)
                    tb.SetPosition(pcbnew.VECTOR2I(mm(OX + fcx + ox_b), mm(OY + fcy + oy_b)))
                    bb_t = tb.GetBoundingBox()
                    gb = box(um(bb_t.GetLeft()) - OX, um(bb_t.GetTop()) - OY, um(bb_t.GetRight()) - OX, um(bb_t.GetBottom()) - OY)
                    if board_fab_inner.contains(gb) and all(gb.distance(prev_g) >= 0.06 for prev_g in bfab_boxes):
                        best_tb = (tb, gb, ox_b, oy_b)
                        break
                if best_tb is not None:
                    break
            assert best_tb is not None, f"Failed to place collision-free B.Fab label for {rf}"
            tb_win, gb_win, ox_w, oy_w = best_tb
            if not existing_b:
                b.Add(tb_win)
            bfab_boxes.append(gb_win)
            bfab_placed += 1
            if math.hypot(ox_w, oy_w) > 0.55:
                ldr = pcbnew.PCB_SHAPE(b)
                ldr.SetShape(pcbnew.SHAPE_T_SEGMENT)
                ldr.SetLayer(pcbnew.B_Fab)
                ldr.SetWidth(mm(0.045))
                ldr.SetStart(pcbnew.VECTOR2I(mm(OX + fcx), mm(OY + fcy)))
                ldr.SetEnd(pcbnew.VECTOR2I(mm(OX + fcx + ox_w * 0.72), mm(OY + fcy + oy_w * 0.72)))
                b.Add(ldr)

        # Unlock all copper tracks/vias (0 locked copper), lock non-copper keepouts, outline, front web & mechanical parts
        for tr in b.GetTracks():
            tr.SetLocked(False)
        for z in b.Zones():
            if z.GetIsRuleArea():
                z.SetLocked(True)
        for d in b.GetDrawings():
            if d.GetLayerName() in ("Edge.Cuts", "F.SilkS"):
                d.SetLocked(True)
        for fname, fp in fps.items():
            if fname in ("J1", "BT1", "SW1", "SW2", "SW3", "SW4", "SW5", "SW6", "Q2") or fname.startswith("D"):
                fp.SetLocked(True)
        pcbnew.SaveBoard(str(pcb_path), b)
        pcb_txt = pcb_path.read_text()
        if '(copper_finish "HAL SnPb")' in pcb_txt:
            pcb_path.write_text(pcb_txt.replace('(copper_finish "HAL SnPb")', '(copper_finish "ENIG")'))
        pro_path.write_bytes(pro_bytes)
        print(
            f"[{spec.name}] post_silk saved ({seg_cnt} front web segments, {des_placed}/{len(major_refs)} back designators, "
            f"{tp_labeled}/8 TP labels, {p1_dots}/12 pin1 dots, 0 locked copper)",
            flush=True,
        )
        os._exit(0)

    def add_b_label(txt: str, tx: float, ty: float, deg: float = 0.0, size_mm: float = 0.85, thick_mm: float = 0.15):
        t = pcbnew.PCB_TEXT(b)
        t.SetText(txt)
        t.SetLayer(pcbnew.B_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(mm(size_mm), mm(size_mm)))
        t.SetTextThickness(mm(thick_mm))
        t.SetMirrored(True)
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
        t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
        t.SetPosition(pcbnew.VECTOR2I(mm(OX + tx), mm(OY + ty)))
        t.SetTextAngleDegrees(deg)
        bb = t.GetBoundingBox()
        bx0, by0, bx1, by1 = um(bb.GetLeft()) - OX, um(bb.GetTop()) - OY, um(bb.GetRight()) - OX, um(bb.GetBottom()) - OY
        if spec.extra_side_buttons:
            ps = pcbnew.SHAPE_POLY_SET()
            t.TransformTextToPolySet(ps, 0, mm(0.005), pcbnew.ERROR_INSIDE)
            if any(ps.Collide( pcbnew.VECTOR2I(vp), vr ) for vp, vr in via_list + hole_list):
                return False
        if all(bx1 <= a or g <= bx0 or by1 <= e or h <= by0 for a, e, g, h in bmask_obs) and all(
            inside_parallelogram(u, v, 0.45) for u in (bx0, bx1) for v in (by0, by1)
        ):
            b.Add(t)
            bmask_obs.append((bx0 - 0.25, by0 - 0.25, bx1 + 0.25, by1 + 0.25))
            return True
        return False

    if spec.io_mode == "usb":
        bt_p1 = next(p for p in fps["BT1"].Pads() if p.GetNumber() == "1").GetPosition()
        bt_p2 = next(p for p in fps["BT1"].Pads() if p.GetNumber() == "2").GetPosition()
        p1x, p1y = um(bt_p1.x) - OX, um(bt_p1.y) - OY
        p2x, p2y = um(bt_p2.x) - OX, um(bt_p2.y) - OY
        for dx_pol in (1.05, 1.20, 0.0):
            dy_p1 = 0.0 if dx_pol > 0 else (1.05 if p1y > p2y else -1.05)
            if add_b_label("+", p1x + dx_pol, p1y + dy_p1, 0.0):
                break
        for dx_pol in (1.05, 1.20, 0.0):
            dy_p2 = 0.0 if dx_pol > 0 else (-1.05 if p1y > p2y else 1.05)
            if add_b_label("-", p2x + dx_pol, p2y + dy_p2, 0.0):
                break
        add_b_label("JST 1.25", 8.40, 14.35, 0.0)
        if spec.extra_side_buttons:
            # Place J1 label so nearest courtyard is J1 within 6.0 mm (passes silk_check connector-label)
            bcu_courts = {}
            for rf, fp_ in fps.items():
                if fp_.IsFlipped():
                    fp_.BuildCourtyardCaches()
                    cy_ = fp_.GetCourtyard(pcbnew.B_CrtYd)
                    if cy_.OutlineCount():
                        bcu_courts[rf] = cy_
            for jx_c, jy_c, jd_c in (
                (-5.60, 23.00, 0.0), (5.80, 24.40, 0.0), (-5.20, 22.40, SKEW_DEG),
                (4.80, 24.80, SKEW_DEG), (-3.80, 22.80, SKEW_DEG), (-1.20, 22.10, SKEW_DEG),
            ):
                pt_c = pcbnew.VECTOR2I(mm(OX + jx_c), mm(OY + jy_c))
                nearest_rf = min(bcu_courts, key=lambda k: bcu_courts[k].SquaredDistance(pt_c))
                if nearest_rf == "J1" and add_b_label("USB-C 5V", jx_c, jy_c, jd_c):
                    break
            for ux, uy, udeg in ((-9.20, -18.55, 0.0), (-8.60, -18.80, 0.0), (-5.40, -21.60, 0.0), (-9.60, -18.20, 90.0)):
                if add_b_label("USER_C", ux, uy, udeg):
                    break
            for dx_, dy_, ddeg in ((-8.60, 18.65, 0.0), (-9.20, 18.90, 0.0), (-5.40, 20.40, 0.0), (-9.60, 18.50, 90.0)):
                if add_b_label("USER_D", dx_, dy_, ddeg):
                    break
            for lx, ly in ((0.00, -24.50), (-1.50, -25.20), (0.00, -10.80), (-2.50, -10.50)):
                if add_b_label("LIPO 20x35mm", lx, ly, 0.0):
                    break
            # Board identity (name, rev, date, license) in open via-free B.SilkS strips
            for id_txt in (f"parallelogram ({spec.name})", f"rev {spec.title_rev} 2026-11 CERN-OHL-P-2.0"):
                placed_id = False
                for iy in (-12.50, -11.20, -9.80, -8.40, -7.00, -13.80, -15.20, -25.80, -26.80, 26.80, 28.00):
                    for ix in (-2.50, -1.50, 0.00, -3.50, 1.50):
                        if add_b_label(id_txt, ix, iy, 0.0, 0.80, 0.15):
                            placed_id = True
                            break
                    if placed_id:
                        break
        else:
            add_b_label("USB-C", -1.20, 22.10, SKEW_DEG)
            add_b_label("LIPO 20x35mm", 0.00, -24.50, 0.0)
    else:
        add_b_label("BT1 +  - 4.2V", 8.20, 31.30, 0.0)
        add_b_label("USB 5V", 0.00, 30.55, SKEW_DEG)
        add_b_label("LIPO 20x35mm", 0.00, -24.50, 0.0)

    # Add IC pin-1 dots and visible B.SilkS designators adjacent to major B.Cu parts (clear of B.Mask & edge)
    ic_refs = ["U3", "U1", "U2", "U10", "U11", "U4", "U5", "U6", "U7", "U8", "U9", "Q1"]
    p1_dots = 0
    for r in ic_refs:
        if r not in fps:
            continue
        p1 = next((p for p in fps[r].Pads() if p.GetNumber() in ("1", "A1")), None)
        if p1 is None:
            continue
        px0, py0 = um(p1.GetPosition().x) - OX, um(p1.GetPosition().y) - OY
        fcx, fcy = um(fps[r].GetPosition().x) - OX, um(fps[r].GetPosition().y) - OY
        vx, vy = px0 - fcx, py0 - fcy
        vlen = math.hypot(vx, vy) or 1.0
        if spec.extra_side_buttons:
            other_pads = [
                (um(op.GetPosition().x) - OX, um(op.GetPosition().y) - OY)
                for op in fps[r].Pads()
                if op.GetNumber() not in ("1", "A1")
            ]
            base_ang = math.atan2(vy, vx)
            dot_cands = []
            for dist_out in (0.55, 0.70, 0.85, 1.00, 1.12):
                for da_deg in (0, -25, 25, -50, 50, -75, 75, -100, 100, -130, 130, 180):
                    ang = base_ang + math.radians(da_deg)
                    dot_cands.append((px0 + dist_out * math.cos(ang), py0 + dist_out * math.sin(ang)))
            for dx_b, dy_b in dot_cands:
                d1 = math.hypot(dx_b - px0, dy_b - py0)
                if d1 > 1.18 or any(math.hypot(dx_b - ox, dy_b - oy) <= d1 + 0.02 for ox, oy in other_pads):
                    continue
                bx0, by0, bx1, by1 = dx_b - 0.16, dy_b - 0.16, dx_b + 0.16, dy_b + 0.16
                if all(bx1 <= a or g <= bx0 or by1 <= e or h <= by0 for a, e, g, h in bmask_obs) and inside_parallelogram(dx_b, dy_b, 0.40):
                    dot = pcbnew.PCB_SHAPE(b)
                    dot.SetShape(pcbnew.SHAPE_T_CIRCLE)
                    dot.SetFilled(True)
                    dot.SetLayer(pcbnew.B_SilkS)
                    dot.SetWidth(mm(0.05))
                    dot.SetCenter(pcbnew.VECTOR2I(mm(OX + dx_b), mm(OY + dy_b)))
                    dot.SetEnd(pcbnew.VECTOR2I(mm(OX + dx_b + 0.13), mm(OY + dy_b)))
                    b.Add(dot)
                    bmask_obs.append((bx0 - 0.18, by0 - 0.18, bx1 + 0.18, by1 + 0.18))
                    p1_dots += 1
                    break
        else:
            for dist_out in (0.65, 0.85, 1.05):
                dx_b, dy_b = px0 + (vx / vlen) * dist_out, py0 + (vy / vlen) * dist_out
                bx0, by0, bx1, by1 = dx_b - 0.16, dy_b - 0.16, dx_b + 0.16, dy_b + 0.16
                if all(bx1 <= a or g <= bx0 or by1 <= e or h <= by0 for a, e, g, h in bmask_obs) and inside_parallelogram(dx_b, dy_b, 0.45):
                    dot = pcbnew.PCB_SHAPE(b)
                    dot.SetShape(pcbnew.SHAPE_T_CIRCLE)
                    dot.SetFilled(True)
                    dot.SetLayer(pcbnew.B_SilkS)
                    dot.SetWidth(mm(0.05))
                    dot.SetCenter(pcbnew.VECTOR2I(mm(OX + dx_b), mm(OY + dy_b)))
                    dot.SetEnd(pcbnew.VECTOR2I(mm(OX + dx_b + 0.13), mm(OY + dy_b)))
                    b.Add(dot)
                    bmask_obs.append((bx0 - 0.18, by0 - 0.18, bx1 + 0.18, by1 + 0.18))
                    p1_dots += 1
                    break

    major_refs = [
        "U3", "U1", "U2", "U10", "U11", "U4", "U5", "U6", "U7", "U8", "U9",
        "L1", "Y1", "SW1", "SW2", "SW3", "SW4",
        *(("SW5", "SW6") if spec.extra_side_buttons else ()),
        "BT1", "J1", "Q1", "R30", "R33", "R50", "R60", "R43",
    ]
    des_placed = 0
    for r in major_refs:
        if r not in fps:
            continue
        f = fps[r]
        pboxes = [p.GetBoundingBox() for p in f.Pads()]
        if not pboxes:
            continue
        fx0 = min(um(bb.GetLeft()) - OX for bb in pboxes)
        fy0 = min(um(bb.GetTop()) - OY for bb in pboxes)
        fx1 = max(um(bb.GetRight()) - OX for bb in pboxes)
        fy1 = max(um(bb.GetBottom()) - OY for bb in pboxes)
        fcx, fcy = (fx0 + fx1) / 2.0, (fy0 + fy1) / 2.0
        hw_f, hh_f = (fx1 - fx0) / 2.0, (fy1 - fy0) / 2.0
        cands = []
        for extra in (0.75, 1.15, 1.55):
            cands.extend([
                (fcx, fy0 - extra, 0.0),
                (fcx, fy1 + extra, 0.0),
                (fx0 - extra - 0.35, fcy, 0.0),
                (fx1 + extra + 0.35, fcy, 0.0),
                (fx0 - extra, fcy, 90.0),
                (fx1 + extra, fcy, 90.0),
            ])
        for tx, ty, deg in cands:
            if add_b_label(r, tx, ty, deg):
                des_placed += 1
                break

    # Unlock all routed copper so finished board has 0 locked copper per LESSONS.md
    for tr in b.GetTracks():
        tr.SetLocked(False)

    pcbnew.SaveBoard(str(pcb_path), b)
    pro_path.write_bytes(pro_bytes)
    print(f"[{spec.name}] post_silk saved ({seg_cnt} front web segments, {des_placed} back designators, {p1_dots} pin1 dots, 0 locked copper)", flush=True)
    os._exit(0)


if __name__ == "__main__":
    spec_arg = VARIANTS[sys.argv[1]]
    stage_arg = sys.argv[2]
    {
        "outline": stage_outline,
        "stack": stage_stack,
        "sync": stage_sync,
        "place": stage_place,
        "zones": stage_zones,
        "models": stage_models,
        "post_silk": stage_post_silk,
    }[stage_arg](spec_arg)
