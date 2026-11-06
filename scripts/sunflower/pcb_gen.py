#!/usr/bin/env python3
"""pcb_gen.py -- 4-layer PCB generator for hw/sunflower/<variant>/sunflower.kicad_pcb.

One pcbnew stage per process (always restores .kicad_pro and calls os._exit(0)):
    python3 scripts/sunflower/pcb_gen.py <variant> outline
    python3 scripts/sunflower/pcb_gen.py <variant> stack
    python3 scripts/sunflower/pcb_gen.py <variant> sync
    python3 scripts/sunflower/pcb_gen.py <variant> place
    python3 scripts/sunflower/pcb_gen.py <variant> zones
    python3 scripts/sunflower/pcb_gen.py <variant> models
    python3 scripts/sunflower/pcb_gen.py <variant> post_silk
"""
import json
import math
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude/skills/pcb-design/scripts"))
sys.path.insert(0, str(ROOT / "scripts/sunflower"))

from config import (  # noqa: E402
    CELL_D,
    OX,
    OY,
    R_BOARD,
    VARIANTS,
    VariantSpec,
    build_led_cells,
)

REF_PCB = ROOT / "hw/round-pendant/d/round-pendant.kicad_pcb"
VENDOR_ZONES = ROOT / "scripts/crunch/placement/vendor_zones.json"

# Translation of the proven RP2350 + regulator + crystal + flash + charger + ESD + LDO macro from Variant D:
MACRO_DX = 0.0  # Variant D is a 38 mm disc too: the macro keeps its proven position
MACRO_DY = 0.0
MACRO_REFS = {
    "U3", "U4", "U5", "U6", "U7", "U8", "L1", "Y1",
    *(f"C{i}" for i in range(1, 25) if i not in (7, 15)),
    "R3", "R4", "R5", "R6", "R7", "R8", "R13", "R14", "R15", "R16", "R17",
}


def disc_vertices(inset: float = 0.0, n: int = 144):
    """Polygon approximating the board circle, inset radially by `inset` (relative to (OX, OY))."""
    r = R_BOARD - inset
    return [(r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def inside_disc(x: float, y: float, margin: float = 0.0) -> bool:
    return math.hypot(x, y) <= R_BOARD - margin


def stage_outline(spec: VariantSpec):
    import pcbnew

    hw = spec.hw_dir
    pcb_path = hw / "sunflower.kicad_pcb"
    pro_path = hw / "sunflower.kicad_pro"
    pro_bytes = pro_path.read_bytes()

    b = pcbnew.NewBoard(str(pcb_path))
    b.SetCopperLayerCount(4)
    tb = b.GetTitleBlock()
    tb.SetTitle(f"sunflower ({spec.name})")
    tb.SetRevision(spec.title_rev)
    tb.SetDate("2026-11-06")
    tb.SetCompany("CERN-OHL-P-2.0")
    tb.SetComment(0, spec.summary)

    mm = pcbnew.FromMM
    c = pcbnew.PCB_SHAPE(b)
    c.SetShape(pcbnew.SHAPE_T_CIRCLE)
    c.SetLayer(pcbnew.Edge_Cuts)
    c.SetWidth(mm(0.10))
    c.SetCenter(pcbnew.VECTOR2I(mm(OX), mm(OY)))
    c.SetEnd(pcbnew.VECTOR2I(mm(OX + R_BOARD), mm(OY)))
    b.Add(c)

    # 35 mm round pouch cell behind the board, on B.Fab
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_CIRCLE)
    s.SetLayer(pcbnew.B_Fab)
    s.SetWidth(mm(0.10))
    s.SetCenter(pcbnew.VECTOR2I(mm(OX), mm(OY)))
    s.SetEnd(pcbnew.VECTOR2I(mm(OX + CELL_D / 2), mm(OY)))
    b.Add(s)

    pcbnew.SaveBoard(str(pcb_path), b)
    pro_path.write_bytes(pro_bytes)
    print(f"outline saved: {pcb_path}", flush=True)
    os._exit(0)


def stage_stack(spec: VariantSpec):
    """Write JLCPCB JLC04161H-7628 1.6 mm 4-layer HASL stackup."""
    pcb_path = spec.hw_dir / "sunflower.kicad_pcb"
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
        '\t\t\t(copper_finish "HAL SnPb")',
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
    pro_path = hw / "sunflower.kicad_pro"
    pro_bytes = pro_path.read_bytes()
    update_pcb(hw / "sunflower.kicad_sch", hw / "sunflower.kicad_pcb", new_parts_at=(OX, OY))
    pro_path.write_bytes(pro_bytes)
    print(f"synced PCB from schematic: {spec.name}", flush=True)
    os._exit(0)


def stage_place(spec: VariantSpec):
    import pcbnew

    hw = spec.hw_dir
    pcb_path = hw / "sunflower.kicad_pcb"
    pro_path = hw / "sunflower.kicad_pro"
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

    placed = set()

    def at_ref(ref: str, side: str = "B", deg=None):
        """Place `ref` where Variant D (also a 38 mm disc) has it."""
        rf = ref_fps[ref]
        rp = rf.GetPosition()
        (set_bcu if side == "B" else set_fcu)(ref, um(rp.x) - OX + MACRO_DX, um(rp.y) - OY + MACRO_DY,
                                               rf.GetOrientationDegrees() if deg is None else deg)
        placed.add(ref)

    # 1. All D1..DN RGB LEDs on F.Cu on the sunflower spiral.
    cells = build_led_cells(spec)
    for c in cells:
        set_fcu(c["ref"], c["x_mm"], c["y_mm"], 0.0, hide_ref=True)
        placed.add(c["ref"])

    # 2. Q2 light sensor on F.Cu at the eye of the sunflower.
    set_fcu("Q2", 0.00, 0.00, 0.0, hide_ref=True)
    placed.add("Q2")

    # 3. The proven RP2350 + regulator + crystal + flash + charger + ESD + LDO macro at Variant D's position.
    for ref in MACRO_REFS:
        at_ref(ref)

    # 4. South rim: J1 USB pads, R1/R2 CC resistors, BT1 cell pads, Q1 VBAT sense divider -- all as in Variant D.
    for ref in ("J1", "R1", "R2", "BT1", "Q1", "R9", "R10", "R11", "R12", "C7"):
        at_ref(ref)

    # 5. Side-actuated EVQP7J01P buttons at the NE / NW rim (Variant D's angles), knobs 0.45 mm past the edge.
    def rim_button(ref: str, east: bool, phi_deg: float):
        r0 = R_BOARD - 1.70  # pad 2 corners on the curve need the 0.25 mm edge clearance
        x0 = r0 if east else -r0
        base = -90.0 if east else 90.0
        set_bcu(ref, x0, 0.0, base)
        p1 = [um(p.GetPosition().x) - OX for p in fps[ref].Pads() if p.GetNumber() == "1"][0]
        p2 = [um(p.GetPosition().x) - OX for p in fps[ref].Pads() if p.GetNumber() == "2"][0]
        if (east and p2 < p1) or ((not east) and p2 > p1):
            base = -base
        # rotate the east/west placement by phi about the board centre (CCW on screen = +orientation)
        a = math.radians(phi_deg)
        x = x0 * math.cos(a)
        y = -abs(x0) * math.sin(a)
        set_bcu(ref, x, y, base + (phi_deg if east else -phi_deg))
        placed.add(ref)

    rim_button("SW1", True, 21.0)
    rim_button("SW2", False, 21.0)
    at_ref("R18")

    # 6. U9 (LIS2DW12) with its decouplers and pull-ups, I2C pull-ups, LED_SDB R/C: Variant D's positions.
    for ref in ("U9", "C25", "C26", "C27", "R19", "R20", "R21", "R22", "R31", "C35"):
        at_ref(ref)

    # Q2's load resistor and filter cap behind it (the legaliser walks them clear of L1).
    set_bcu("R43", -1.50, -1.60, 180.0)
    set_bcu("C70", 1.50, -1.60, 180.0)
    placed.update({"R43", "C70"})

    # 7. Place AW20198QNR QFN-40 drivers + programmatically place their 5 local passives right at PVCC(5) & VCC(22)/ISET(29)!
    drv_fixed = set()
    for drv in spec.drivers:
        dx0, dy0, drot = drv.bcu_pos
        set_bcu(drv.uref, dx0, dy0, drot)
        drv_fixed.add(drv.uref)
        placed.add(drv.uref)

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
            bulk_dx = 2.10 if dx0 <= 0 else -2.10
            set_bcu(drv.bulk_ref, p5_x + bulk_dx, dy0 + pvcc_dir * 4.40, 90.0)
            drv_fixed.add(drv.bulk_ref)

        p22_x = um(p22.x) - OX
        p29_x = um(p29.x) - OX
        vcc_sgn = 1.0 if p22_x >= p29_x else -1.0
        set_bcu(c_vcc_100n, p22_x - vcc_sgn * 0.55, dy0 + vcc_dir * 3.95, 90.0)
        set_bcu(c_vcc_1u, p22_x + vcc_sgn * 0.70, dy0 + vcc_dir * 3.95, 90.0)
        set_bcu(drv.rset_ref, p29_x, dy0 + vcc_dir * 3.95, 90.0)
        drv_fixed.update({c_pvcc_1u, c_pvcc_100n, c_vcc_100n, c_vcc_1u, drv.rset_ref})
        placed.update(drv_fixed)

    # 8. Test points where Variant D has them.
    for k in range(1, 9):
        at_ref(f"TP{k}")

    missing = sorted(r for r in fps if r not in placed)
    if missing:
        raise SystemExit(f"[{spec.name}] footprints with no placement rule: {missing}")

    # 9. Legalize movable auxiliary passives/TPs against all fixed ICs/decouplers and the board circle.
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
                if not all(inside_disc(u, v, 0.35) for u in (bb[0], bb[2]) for v in (bb[1], bb[3])):
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
    pcb_path = hw / "sunflower.kicad_pcb"
    pro_path = hw / "sunflower.kicad_pro"
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
        xv = x0 + 0.30
        while xv <= x1 - 0.30 + 1e-6:
            yv = y0 + 0.30
            while yv <= y1 - 0.30 + 1e-6:
                cands.append((round(xv, 3), round(yv, 3)))
                yv += 0.15
            xv += 0.15
        cx_ep, cy_ep = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        # Prefer cross-axis points (away from 2x2 paste quadrants at +-0.95, +-0.95)
        cands.sort(key=lambda q: (min(abs(q[0] - cx_ep), abs(q[1] - cy_ep)), math.hypot(q[0] - cx_ep, q[1] - cy_ep)))
        got = []
        for qx, qy in cands:
            if len(got) >= want_n:
                break
            if fcu_clear(qx, qy) and all(math.hypot(qx - ax, qy - ay) >= 0.70 for ax, ay in got):
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

    # 3. Unbroken In1.Cu (L2) solid GND plane across the whole disc (0.30 mm edge pullback),
    #    with LX cutout under VREG_LX switch node per chips/rp2350.md §6.3.8.1!
    gnd_pts = disc_vertices(inset=0.30)
    add_zone("plane GND", IN1_CU, "GND", gnd_pts, 0, minw=0.12, clear=0.15)

    lxpads = [p for p in fps["L1"].Pads() if p.GetNetname().endswith("VREG_LX")] + [
        p for p in fps["U3"].Pads() if p.GetNetname().endswith("VREG_LX")
    ]
    lxbbs = [p.GetBoundingBox() for p in lxpads]
    lx0 = min(um(q.GetLeft()) for q in lxbbs) - OX - 0.25
    lx1 = max(um(q.GetRight()) for q in lxbbs) - OX + 0.25
    ly0 = min(um(q.GetTop()) for q in lxbbs) - OY - 0.25
    ly1 = max(um(q.GetBottom()) for q in lxbbs) - OY + 0.25
    add_area("LX cutout L2", IN1_CU, [(lx0, ly0), (lx1, ly0), (lx1, ly1), (lx0, ly1)], tracks=True, pour=True)

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
            # any pad, GND's own included: no via drilled in an SMD pad (no POFV on this 4-layer board)
            if math.hypot(max(a - xa, 0.0, xa - g), max(e - ya, 0.0, ya - h)) < 0.265:
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
    pcb_path = hw / "sunflower.kicad_pcb"
    pro_path = hw / "sunflower.kicad_pro"
    pro_bytes = pro_path.read_bytes()

    base = "${KIPRJMOD}/../../../3dmodels/"
    model_map = {
        "LED_XL-1010RGB": (base + "XL-1010RGB-YG.step", 0, 0.0),
        "LED_XL-1615RGBC": (base + "LED-ARRAY-SMD_4P-L1.6-W1.5-BR_XL-1615RGBC-RF.step", 180, 0.0),
        "SENSOR_ALS-PT19": (base + "SENSORS-SMD_L1.7-W0.8-H0.6.step", 0, 0.0),
        "AW20198_QFN-40-1EP_5x5mm_P0.4mm_EP3.4x3.4mm": (
            "${KICAD9_3DMODEL_DIR}/Package_DFN_QFN.3dshapes/TQFN-40-1EP_5x5mm_P0.4mm_EP3.5x3.5mm.step",
            0,
            0.0,
        ),
        "RP2350-QFN-60-1EP_7x7_P0.4mm_EP3.4x3.4mm_ThermalVias": (base + "QFN-60_L7.0-W7.0-P0.40-TL-EP3.4.step", 0, 0.0),
        "L_pol_2016": (base + "IND-SMD_L2.0-W1.6_AOTA-B201610S3R3-101-T.step", 180, 0.0),
        "SW_Panasonic_EVQP7J": (base + "SW-SMD_EVQP7C01P-L3.6-W3.5-H1.4-P3.6-LS4.7.step", 0, 0.0),
        "XySemi_DFN-6_1.8x1.4mm": (base + "DFNFC-6_L1.8-W1.4-H0.6-P0.50-BL_XB9901A.step", 0, 0.56),
        "Texas_X2SON-4_1x1mm_P0.65mm": (base + "X2SON-4_L1.0-W1.0-H0.4-P0.65-TL-EPSLDPRT.step", 270, 0.0),
    }

    b = pcbnew.LoadBoard(str(pcb_path))
    n = 0
    for f in b.GetFootprints():
        name = str(f.GetFPID().GetUniStringLibItemName())
        if name in model_map:
            fn, rot, zoff = model_map[name]
            ms = f.Models()
            ms.clear()
            m = pcbnew.FP_3DMODEL()
            m.m_Filename = fn
            m.m_Rotation = pcbnew.VECTOR3D(0, 0, rot)
            m.m_Show = True
            m.m_Offset = pcbnew.VECTOR3D(0, 0, zoff)
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
    pcb_path = hw / "sunflower.kicad_pcb"
    pro_path = hw / "sunflower.kicad_pro"
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

    # Obstacles on F.Cu (pads) so F.SilkS web never causes silk_over_copper!
    # Note: vias are tented on F.Mask so F.SilkS over tented vias is clean, though we also keep clear of F.Cu pads!
    fcu_obs = []
    for f in b.GetFootprints():
        if f.GetLayer() == pcbnew.F_Cu:
            if f.GetReference() == "Q2":
                bb = f.GetBoundingBox(False, False)
                fcu_obs.append((um(bb.GetLeft()) - OX - 0.35, um(bb.GetTop()) - OY - 0.35, um(bb.GetRight()) - OX + 0.35, um(bb.GetBottom()) - OY + 0.35))
            else:
                for p in f.Pads():
                    bb = p.GetBoundingBox()
                    fcu_obs.append((um(bb.GetLeft()) - OX - 0.25, um(bb.GetTop()) - OY - 0.25, um(bb.GetRight()) - OX + 0.25, um(bb.GetBottom()) - OY + 0.25))

    def pt_ok_f(x: float, y: float) -> bool:
        if not inside_disc(x, y, 0.55):
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

    # Front stays bare (brief section 9): no lattice web on the sunflower.
    seg_cnt = 0

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

    # Add clean B.SilkS connector & cell labels clear of all B.Mask openings
    bmask_obs = []
    for f in b.GetFootprints():
        if f.GetLayer() == pcbnew.B_Cu:
            for p in f.Pads():
                if p.IsOnLayer(pcbnew.B_Mask):
                    bb = p.GetBoundingBox()
                    bmask_obs.append((um(bb.GetLeft()) - OX - 0.22, um(bb.GetTop()) - OY - 0.22, um(bb.GetRight()) - OX + 0.22, um(bb.GetBottom()) - OY + 0.22))

    def add_b_label(txt: str, tx: float, ty: float, deg: float = 0.0):
        t = pcbnew.PCB_TEXT(b)
        t.SetText(txt)
        t.SetLayer(pcbnew.B_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(mm(0.85), mm(0.85)))
        t.SetTextThickness(mm(0.15))
        t.SetMirrored(True)
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
        t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
        t.SetPosition(pcbnew.VECTOR2I(mm(OX + tx), mm(OY + ty)))
        t.SetTextAngleDegrees(deg)
        bb = t.GetBoundingBox()
        bx0, by0, bx1, by1 = um(bb.GetLeft()) - OX, um(bb.GetTop()) - OY, um(bb.GetRight()) - OX, um(bb.GetBottom()) - OY
        if all(bx1 <= a or g <= bx0 or by1 <= e or h <= by0 for a, e, g, h in bmask_obs) and all(
            inside_disc(u, v, 0.45) for u in (bx0, bx1) for v in (by0, by1)
        ):
            b.Add(t)
            bmask_obs.append((bx0 - 0.25, by0 - 0.25, bx1 + 0.25, by1 + 0.25))
            return True
        return False

    def label_near(txt, cands):
        for tx, ty, deg in cands:
            if add_b_label(txt, tx, ty, deg):
                return True
        print(f"  label not placed: {txt}")
        return False

    bt = fps["BT1"].GetPosition()
    btx, bty = um(bt.x) - OX, um(bt.y) - OY
    label_near("BT1 +  - 4.2V", [(btx, bty + dy, 0.0) for dy in (2.3, -2.3, 2.8, -2.8)])
    j1 = fps["J1"].GetPosition()
    j1x, j1y = um(j1.x) - OX, um(j1.y) - OY
    label_near("USB 5V", [(j1x, j1y + dy, 0.0) for dy in (-1.9, -2.4, 1.6)])
    label_near("LIPO 35mm ROUND", [(x, y, 0.0) for x, y in ((0, -17.4), (0, 15.0), (-9, -14), (9, -14), (-11, 9))])

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
        for dist_out in (0.65, 0.85, 1.05):
            dx_b, dy_b = px0 + (vx / vlen) * dist_out, py0 + (vy / vlen) * dist_out
            bx0, by0, bx1, by1 = dx_b - 0.16, dy_b - 0.16, dx_b + 0.16, dy_b + 0.16
            if all(bx1 <= a or g <= bx0 or by1 <= e or h <= by0 for a, e, g, h in bmask_obs) and inside_disc(dx_b, dy_b, 0.45):
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
        "L1", "Y1", "SW1", "SW2", "J1", "Q1", "R30", "R33", "R50", "R60", "R43",
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
