#!/usr/bin/env python3
"""board.py -- build stages for round-pendant. One stage per process (pcbnew: one board per process).

    python3 scripts/board.py stack     six copper layers and the stackup, once, on the outline board
    python3 scripts/board.py rules     .kicad_pro classes and rules, .kicad_dru (after any step that saves the board)
    python3 scripts/board.py sync      Update PCB from Schematic (kicad_write.update_pcb)

Every number comes from design/nets.csv, design/stackup.md or design/brief.md.
"""
import csv, json, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".claude/skills/pcb-design/scripts"))
import os
VARIANT = os.environ.get("PENDANT_VARIANT", "a")
HW = ROOT / f"hw/round-pendant/{VARIANT}"
PCB = HW / "round-pendant.kicad_pcb"; PRO = HW / "round-pendant.kicad_pro"; SCH = HW / "round-pendant.kicad_sch"; DRU = HW / "round-pendant.kicad_dru"

# name: track, clearance, via dia, via drill. Via 0.25/0.15 is JLC's standard minimum; see stackup.md.
CLASSES = {"Default": (.1, .09, .25, .15), "SIGNAL": (.1, .09, .25, .15), "POWER": (.2, .09, .3, .15), "SW_SCAN": (.1, .09, .25, .15), "ANALOG": (.1, .09, .25, .15),
           "CLOCK": (.15, .15, .25, .15), "SE_HS": (.1, .1, .25, .15), "SWITCH": (.4, .12, .3, .15), "DIFF_HS": (.15, .15, .25, .15)}
STACK = [("F.SilkS", "Top Silk Screen", None), ("F.Paste", "Top Solder Paste", None), ("F.Mask", "Top Solder Mask", .01),
         ("F.Cu", "copper", .035), ("d1", "prepreg", .0994), ("In1.Cu", "copper", .0152), ("d2", "core", .2708), ("In2.Cu", "copper", .0152),
         ("d3", "prepreg", .1088), ("In3.Cu", "copper", .0152), ("d4", "core", .2708), ("In4.Cu", "copper", .0152), ("d5", "prepreg", .0994),
         ("B.Cu", "copper", .035), ("B.Mask", "Bottom Solder Mask", .01), ("B.Paste", "Bottom Solder Paste", None), ("B.SilkS", "Bottom Silk Screen", None)]


def rules():
    src = Path.home() / "Software/boardroom/examples/easy2350/hw/easy2350/a/easy2350.kicad_pro"
    d = json.loads(src.read_text())
    d["meta"]["filename"] = PRO.name
    d["sheets"] = []; d["boards"] = []
    ds = d["board"]["design_settings"]
    ds["rules"].update(min_clearance=.09, min_copper_edge_clearance=.2, min_hole_clearance=.2, min_hole_to_hole=.2, min_resolved_spokes=1,
                       min_through_hole_diameter=.1, min_track_width=.09, min_via_annular_width=.05, min_via_diameter=.2)
    ds["via_dimensions"] = [{"diameter": 0, "drill": 0}, {"diameter": .25, "drill": .15}, {"diameter": .3, "drill": .15}]
    ds["track_widths"] = [0, .1, .15, .2, .3, .4]
    ds["rule_severities"].update(silk_overlap="error", silk_over_copper="error", track_dangling="error", via_dangling="warning",
                                 net_conflict="error", duplicate_footprints="error", extra_footprint="error", missing_footprint="error",
                                 lib_footprint_issues="warning", lib_footprint_mismatch="ignore")
    tmpl = d["net_settings"]["classes"][0]
    d["net_settings"]["classes"] = []
    for n, (w, c, vd, vh) in CLASSES.items():
        k = dict(tmpl, name=n, track_width=w, clearance=c, via_diameter=vd, via_drill=vh, microvia_diameter=.2, microvia_drill=.1,
                 diff_pair_width=.15, diff_pair_gap=.15, priority=2147483647 if n == "Default" else len(d["net_settings"]["classes"]))
        d["net_settings"]["classes"].append(k)
    pats = []
    for r in csv.DictReader(open(ROOT / "design/nets.csv")):
        pats.append({"netclass": r["class"], "pattern": r["net"]})
    d["net_settings"]["netclass_patterns"] = pats
    PRO.write_text(json.dumps(d, indent=2))
    rows = list(csv.DictReader(open(ROOT / "design/nets.csv")))
    out = ["(version 1)", "", "# Derived from design/nets.csv and design/brief.md. Each rule cites its source.", ""]
    for net, w, why in (("VBUS", .25, "0.5 A, nets.csv; IPC-2221 outer 1 oz, 10 C rise"), ("VSYS", .3, "0.34 A avg, 1 A scan peak, nets.csv"),
                        ("VBAT", .3, "0.34 A avg, 1 A scan peak, nets.csv"), ("/Power/BAT_N", .3, "same as VBAT, cell minus"),
                        ("+3V3", .2, "150 mA max, intent.md")):
        out += [f"# {why}", f'(rule "{net} current width"', f'  (condition "A.NetName == \'{net}\'")', f"  (constraint track_width (min {w}mm)))", ""]
    # SW scan lines: 494 mA peak for 32 us, 55 mA average (nets.csv). 0.1 mm on 0.5 oz inner carries the average with room. Class SW_SCAN sets the width; POWER at 0.2 mm halved inner-layer capacity (trial 7).
    for r in rows:
        if r["class"] == "SW_SCAN":
            out += [f'(rule "{r["net"]} width"', f'  (condition "A.NetName == \'{r["net"]}\'")', "  (constraint track_width (min 0.1mm)))", ""]
    for r in rows:
        if r["length_limit"]:
            out += [f'(rule "{r["net"]} length"', f'  (condition "A.NetName == \'{r["net"]}\'")', f'  (constraint length (max {r["length_limit"]}mm)))']
        if "no vias" in r["reason"]:
            out += [f'(rule "{r["net"]} no vias"', f'  (condition "A.NetName == \'{r["net"]}\'")', "  (constraint via_count (max 0)))"]
    DRU.write_text("\n".join(out) + "\n")
    print("rules written")


def stack():
    """Copper layers and stackup, written directly: pcbnew can't set the stackup headless. Run once, on the outline board."""
    t = PCB.read_text()
    stack = ['\t\t(stackup']
    for n, kind, th in STACK:
        if n.startswith("d"):
            num = int(n[1:])
            stack.append(f'\t\t\t(layer "dielectric {num}" (type "{kind}") (thickness {th}) (material "FR4") (epsilon_r 4.1) (loss_tangent 0.02))')
        elif th is None:
            stack.append(f'\t\t\t(layer "{n}" (type "{kind}"))')
        elif kind == "copper":
            stack.append(f'\t\t\t(layer "{n}" (type "copper") (thickness {th}))')
        else:
            stack.append(f'\t\t\t(layer "{n}" (type "{kind}") (thickness {th}))')
    stack += ['\t\t\t(copper_finish "ENIG")', '\t\t\t(dielectric_constraints no)', '\t\t)']
    t = re.sub(r'\t\t\(stackup.*?\n\t\t\)\n', '', t, flags=re.S)
    t = t.replace('(setup\n', '(setup\n' + "\n".join(stack) + "\n", 1)
    t = re.sub(r'\(general\n\t\t\(thickness [\d.]+\)', '(general\n\t\t(thickness 1.0)', t)
    PCB.write_text(t)
    print("stack written")


def sync():
    from kicad_write import update_pcb
    update_pcb(SCH, PCB, new_parts_at=(100.0, 100.0))


OX, OY = 100.0, 100.0
BY = {}


def place():
    """All parts. LEDs from matrix_map.csv, top. Everything else bottom, x and y in mm from the board centre, seen from the top."""
    import math, pcbnew
    b = pcbnew.LoadBoard(str(PCB))
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    mm = pcbnew.FromMM

    def put_b(ref, x, y, rot=0.0):
        f = fps[ref]
        if f.GetLayer() == pcbnew.F_Cu:
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        f.SetPosition(pcbnew.VECTOR2I(mm(OX + x), mm(OY + y)))
        f.SetOrientationDegrees(180 - rot)  # the mirror image in x of the part at rotation rot

    def snap(x, y):
        """Middle of four anode vias: vias at x = 0.6, y = 1.4 mod 2, so a small part centres at x = 1.6, y = 0.4 mod 2."""
        return (round((x - 1.6) / 2) * 2 + 1.6, round((y - 0.4) / 2) * 2 + 0.4)

    def put_s(ref, x, y, rot=0.0):
        put_b(ref, *snap(x, y), rot)

    for r in csv.DictReader(open(ROOT / "design/study/matrix_map.csv")):
        f = fps[r["ref"]]
        f.SetPosition(pcbnew.VECTOR2I(mm(OX + float(r["x_mm"])), mm(OY + float(r["y_mm"]))))
        f.SetOrientationDegrees(0)
        f.Reference().SetVisible(False); f.Value().SetVisible(False)

    # Chip centres on the anode via grid: via = (odd - 0.4, odd + 0.4).
    U1 = (-11.4, 3.4); U2 = (10.6, 3.4); U3 = (-1.4, -6.6)
    put_b("U1", *U1, 180); put_b("U2", *U2, 0); put_b("U3", *U3, 180)

    # Driver parts, chip frame: (cx, cy) with pin 1 corner at (-, -). CS pins face the board centre, control pins the rim.
    # U1: board = centre + (cx, -cy). U2: board = centre + (-cx, cy).
    def drv(n, ref, cx, cy, rot=0):
        if n == 1:
            put_b(ref, U1[0] + cx, U1[1] - cy, rot)
        else:
            put_b(ref, U2[0] - cx, U2[1] + cy, rot)
    # Pins 16-24 (SW) on the frame's +y edge stay clear of parts: they carry the matrix fan-in.
    for n, cn, rn in ((1, 30, 30), (2, 40, 33)):
        drv(n, f"C{cn+2}", -5.1, 3)        # 100 nF, PVCC 15
        drv(n, f"C{cn+1}", -5.1, 5)        # 1 uF, PVCC 15
        drv(n, f"C{cn}", -0.2 if n == 1 else -3.2, 8.2 if n == 1 else 6.8, 0 if n == 1 else 90)   # 22 uF bulk
        drv(n, f"C{cn+4}", 1.4, 5.6, 90)   # 100 nF, PVCC 25
        drv(n, f"C{cn+3}", 3.4, 5.6, 90)   # 1 uF, PVCC 25
        drv(n, f"C{cn+5}", -5.1, 1)        # 1 uF, AVCC 14
        drv(n, f"C{cn+6}", -1.1, 6.6)      # 100 nF, AVCC 14
        drv(n, f"R{rn+2}", -5.1, -1)       # ISET
        drv(n, f"R{rn}", -5.1, -3)         # INTB pull-up
        drv(n, f"R{rn+1}", -4.1, -5.1, 90)  # SDB pull-down
        drv(n, f"C{cn+7}", -1, -5.5, 90)   # SDB cap

    # RP2350: rotated 180 and flipped, so chip frame (cx, cy) -> board centre + (cx, -cy). Regulator block per chips/rp2350.md.
    def mcu(ref, cx, cy, rot=0):
        put_b(ref, U3[0] + cx, U3[1] - cy, rot)
    mcu("L1", 2.0, -7.2, 180); mcu("C18", 2.0, -5.55, 180); mcu("C16", 2.0, -4.6, 180)
    mcu("C17", 4.7, -5.05, 90); mcu("R13", 4.7, -6.9, 90)
    mcu("R14", -1.1, -6.2, 90); mcu("R15", -0.1, -6.2, 90); mcu("C13", -2.1, -6.2, 270)
    mcu("C8", -5.5, -3); mcu("C20", -5.5, -1); mcu("C9", -5.5, 1)
    mcu("C10", -3, 5.5, 90); mcu("C19", 1, 5.5, 90); mcu("C11", 3, 5.5, 90)
    mcu("C12", 5.5, 1); mcu("C21", 5.5, -1); mcu("C14", 5.5, -3)
    # Crystal to the north, on XIN and XOUT.
    mcu("Y1", -1.3, 8.2); mcu("R17", -1, 5.5, 90); mcu("C23", 1.6, 8.2, 90); mcu("C24", -4.2, 8.2, 90)
    # Flash south of U3, on the QSPI pins.
    put_b("U4", -2.8, 5.4, 90); put_b("C22", -6.4, 2.4, 90)
    # I2C pull-ups by the MCU's GPIO4, 5 side; accelerometer north-west.
    put_s("R21", -9.4, -11.6); put_s("R22", -7.4, -11.6)
    put_b("U9", 8.6, -10.6, 0); put_s("C25", 7.0, -6.6); put_s("C26", 9.0, -6.6); put_s("C27", 11.0, -8.6)
    put_s("R19", 5.6, -11.6); put_s("R20", 3.6, -11.6)
    # Buttons on their rim sites.
    st = json.loads((ROOT / "design/study/sites.json").read_text())
    for ref, deg in st["buttons_deg"].items():
        a = math.radians(deg); r = st["button_radius"]
        put_b(ref, r*math.cos(a), r*math.sin(a), deg - 90)
    put_s("R18", 12.6, -11.6); put_s("R16", -11.6, -11.6)
    # USB-C, ESD and CC at the south edge.
    j = st["j1"]; put_b("J1", j[0], j[1], 0)
    put_b("U7", 2.3, 9.4); put_b("R1", -5.0, 9.9); put_b("R2", -3.0, 9.9)
    # Charger and power path.
    put_b("U5", 3.4, 6.0, 180)
    put_b("C1", 5.0, 10.0); put_b("R3", 0.8, 6.9, 90); put_b("R4", -0.8, 9.4); put_b("R5", 5.0, 8.95)
    put_b("C2", 4.7, 3.0, 0); put_b("C5", 1.5, 3.0, 0)
    put_s("R6", 11.6, -13.6); put_s("R7", 9.6, -13.6)
    # LDO and VBAT switch, south-west.
    put_b("U6", -6.0, 0.4); put_s("C3", -6.4, -1.6); put_b("C4", -4.6, 0.4, 90)
    put_b("Q1", -8.2, 12.4); put_b("R9", -12.4, 11.6); put_s("R10", -10.4, 12.4); put_b("R11", -8.9, 14.4); put_b("R12", -10.9, 14.4); put_b("C7", -7.0, 14.4)
    # Cell and protection, south-east.
    put_b("BT1", 9.8, 12.9, 0); put_b("U8", 6.1, 12.6, 0); put_b("C6", 7.2, 10.6); put_b("R8", 6.1, 14.6)
    # Test pads where nothing needs to pass.
    for ref, x, y in (("TP1", 7.6, -5.6), ("TP2", -12.4, -9.6), ("TP3", 9.6, -5.6), ("TP4", 5.4, -1.6), ("TP5", -10.4, -13.6), ("TP8", -8.4, -13.6), ("TP6", 3.6, -15.6), ("TP7", 5.6, -15.6)):
        put_b(ref, x, y)
    pcbnew.SaveBoard(str(PCB), b)
    print("placed")


def anodes():
    """One locked via per LED anode: in pad 3 if it clears everything on the bottom, else on a short stub in one of the 5 open directions.
    Rule areas: U3's 1V1 ring and L1 stay clear (chips/rp2350.md, brief.md section 10)."""
    import pcbnew, math
    b = pcbnew.LoadBoard(str(PCB))
    mm = pcbnew.FromMM; um = pcbnew.ToMM
    VIA_R, CL = .125, .09
    HOLE = max(VIA_R + CL, .075 + .2)   # JLC hole to copper 0.2 mm, stackup.md
    obst = []
    for f in b.GetFootprints():
        for p in f.Pads():
            if not f.GetReference().startswith("D") and (p.IsOnLayer(pcbnew.B_Cu) or p.GetAttribute() in (pcbnew.PAD_ATTRIB_NPTH, pcbnew.PAD_ATTRIB_PTH)):
                bb = p.GetBoundingBox()
                obst.append((um(bb.GetLeft()), um(bb.GetTop()), um(bb.GetRight()), um(bb.GetBottom()), f.GetReference(), p.GetNumber()))
    top = [(p.GetPosition(), f.GetReference(), p.GetBoundingBox()) for f in b.GetFootprints() if f.GetReference().startswith("D") for p in f.Pads()]
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    U3 = fps["U3"].GetPosition(); ux, uy = um(U3.x), um(U3.y)
    L = fps["L1"].GetBoundingBox(False, False) if False else None
    l1 = fps["L1"].GetPosition(); lx, ly = um(l1.x), um(l1.y)
    def free(x, y, own=None):
        for _, ref, bb in top:
            if ref != own:
                dx = max(um(bb.GetLeft()) - x, 0, x - um(bb.GetRight())); dy = max(um(bb.GetTop()) - y, 0, y - um(bb.GetBottom()))
                if dx*dx + dy*dy < HOLE**2:
                    return False
        for a, c, e, g, ref, n in obst:
            dx = max(a - x, 0, x - e); dy = max(c - y, 0, y - g)
            if dx*dx + dy*dy < HOLE**2:
                return False
        m = max(abs(x-ux), abs(y-uy))
        if 1.7 - VIA_R - CL < m < 2.2 + VIA_R + CL:
            return False                                 # 1V1 ring
        if abs(x-lx) < 1.0 + VIA_R + CL and abs(y-ly) < .8 + VIA_R + CL:
            return False                                 # under L1
        if 100 + 1.2 < x < 100 + 3.0 and 100 - 2.9 < y < 100 + 1.5:
            return False                                 # the LX corridor from pin 48 to L1
        return True
    gnd = None
    trials = [(0, 0, 0), *[(a, c, .5) for a, c in ((-1, 0), (0, 1), (-1, 1), (-1, -1), (1, 1))], *[(a, c, .8) for a, c in ((-1, 0), (0, 1), (-1, 1), (-1, -1), (1, 1))]]
    stat = {}; blocked = []; placed = []
    for f in b.GetFootprints():
        if not f.GetReference().startswith("D"):
            continue
        done = False
        for rot in (0, 90, 180, 270):
            f.SetOrientationDegrees(rot)
            pad = next(p for p in f.Pads() if p.GetNumber() == "3")
            c = pad.GetPosition(); x0, y0 = um(c.x), um(c.y)
            net = pad.GetNetCode()
            a = math.radians(rot); ca, sa = round(math.cos(a)), round(math.sin(a))
            for k, (tx, ty, S) in enumerate(trials):
                dx, dy = tx*ca + ty*sa, -tx*sa + ty*ca       # open directions turn with the part
                x, y = x0 + dx*S, y0 + dy*S
                if free(x, y, f.GetReference()) and not any((x-p_)**2 + (y-e)**2 < 0.36**2 for p_, e in placed):
                    small = max(abs(x-ux), abs(y-uy)) < 2.95    # keeps the 3V3 band whole: JLC 0.10/0.20 mm, board <= 1 mm, ENIG
                    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); v.SetWidth(mm(.2 if small else .25)); v.SetDrill(mm(.1 if small else .15))
                    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(net); v.SetLocked(True); b.Add(v)
                    if k:
                        t = pcbnew.PCB_TRACK(b); t.SetStart(c); t.SetEnd(pcbnew.VECTOR2I(mm(x), mm(y))); t.SetWidth(mm(.12)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(net); t.SetLocked(True); b.Add(t)
                    placed.append((x, y)); stat[(rot, k)] = stat.get((rot, k), 0) + 1
                    done = True
                    break
            if done:
                break
        if not done:
            f.SetOrientationDegrees(0)
            pad = next(p for p in f.Pads() if p.GetNumber() == "3"); c = pad.GetPosition()
            blocked.append((f.GetReference(), round(um(c.x)-100, 2), round(um(c.y)-100, 2)))
    # Thermal vias at LED channel crossings under each exposed pad; a through via reaches the LED side.
    gnd = b.FindNet("GND").GetNetCode()
    th = {}
    for ref, half in (("U1", 2.7), ("U2", 2.7), ("U3", 1.7), ("U5", .85)):
        f = fps[ref]; p0 = f.GetPosition(); cx, cy = um(p0.x), um(p0.y)
        rects = [p.GetBoundingBox() for p in f.Pads() if p.GetNumber() in ("61", "17") and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD]
        n = 0
        # LEDs sit at odd mm, so their channels cross at even x, even y.
        for i in range(-3, 4):
            for j in range(-3, 4):
                x, y = 2*round(cx/2 - OX/2)+OX + 2*i, 2*round(cy/2 - OY/2)+OY + 2*j
                if any(um(r.GetLeft()) + .09 <= x <= um(r.GetRight()) - .09 and um(r.GetTop()) + .09 <= y <= um(r.GetBottom()) - .09 for r in rects) \
                        and not any((x-a)**2 + (y-e)**2 < 0.36**2 for a, e in placed):
                    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); v.SetWidth(mm(.25)); v.SetDrill(mm(.15))
                    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(gnd); v.SetLocked(True); b.Add(v); n += 1
        th[ref] = n
    print("thermal vias", th)
    pcbnew.SaveBoard(str(PCB), b)
    print("anode vias, (rotation, trial): count", stat, "blocked", blocked)


# ---------------------------------------------------------------- variant b: sunflower, USB wire pads, EVQP7C01P

LED_PAD_HALF = .225


def place_b():
    """Parts as in variant a, except LEDs on the sunflower (design/study/b), USB pads for J1, EVQP7C01P buttons."""
    import math, pcbnew
    place()
    b = pcbnew.LoadBoard(str(PCB)); mm = pcbnew.FromMM
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    for r in csv.DictReader(open(ROOT / os.environ.get("PENDANT_MAP", "design/study/b/matrix_map.csv"))):
        f = fps[r["ref"]]
        f.SetPosition(pcbnew.VECTOR2I(mm(OX + float(r["x_mm"])), mm(OY + float(r["y_mm"]))))
        f.SetOrientationDegrees(-float(r["angle_deg"]))
    for ref, (deg, rc) in json.loads((ROOT / "design/study/b/buttons.json").read_text()).items():
        a = math.radians(deg); f = fps[ref]
        f.SetPosition(pcbnew.VECTOR2I(mm(OX + rc*math.cos(a)), mm(OY + rc*math.sin(a))))
        f.SetOrientationDegrees(180 - (deg - 90))
    f = fps["J1"]
    f.SetPosition(pcbnew.VECTOR2I(mm(OX), mm(OY + 16.5))); f.SetOrientationDegrees(0)
    pcbnew.SaveBoard(str(PCB), b)
    for ref in ("SW1", "SW2", "J1"):
        print(ref, [(p.GetNumber() or "hole", p.GetNetname().split("/")[-1], round(pcbnew.ToMM(p.GetPosition().x)-OX, 2), round(pcbnew.ToMM(p.GetPosition().y)-OY, 2)) for p in fps[ref].Pads()])
    print("placed b")


def place_c():
    """Variant b's placement plus the centre LED and its resistors beside U3's GPIO23-25 pins (design/study/center-plus2)."""
    import pcbnew
    place_b()
    b = pcbnew.LoadBoard(str(PCB)); mm = pcbnew.FromMM
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    f = fps["D235"]; f.SetPosition(pcbnew.VECTOR2I(mm(OX + .05), mm(OY - .65))); f.SetOrientationDegrees(-80)
    for ref, x, y in (("R40", 3.8, -10.6), ("R41", 3.8, -9.6), ("R42", 3.8, -8.6)):
        f = fps[ref]
        if f.GetLayer() == pcbnew.F_Cu:
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        f.SetPosition(pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))); f.SetOrientationDegrees(0)
    pcbnew.SaveBoard(str(PCB), b); print("placed c")


def seg_dist(px, py, ax, ay, bx, by):
    import math
    vx, vy = bx-ax, by-ay; n = vx*vx+vy*vy
    t = 0 if n == 0 else max(0, min(1, ((px-ax)*vx+(py-ay)*vy)/n))
    return math.hypot(px-ax-t*vx, py-ay-t*vy)


def anodes_b():
    """One locked via per LED anode, in the pad if the back side allows, else on a short stub. Any of the 4 turns of an LED puts its anode on a
    different corner without moving a land, so all four are tried. Exposed pads are then cut round foreign vias, and thermal vias go where they fit."""
    import pcbnew, math
    b = pcbnew.LoadBoard(str(PCB)); mm = pcbnew.FromMM; um = pcbnew.ToMM
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    VIA_R, CL, STUB = .125, .09, .06
    HOLE = max(VIA_R + CL, .075 + .2)
    EP = {"U1": "61", "U2": "61", "U3": "61", "U5": "17"}
    obst = []; holes = []
    for f in b.GetFootprints():
        ref = f.GetReference()
        for p in f.Pads():
            if ref.startswith("D"):
                continue
            if p.GetAttribute() in (pcbnew.PAD_ATTRIB_NPTH, pcbnew.PAD_ATTRIB_PTH):
                c = p.GetPosition(); holes.append((um(c.x), um(c.y), um(p.GetDrillSizeX())/2))
            elif p.IsOnLayer(pcbnew.B_Cu) and not (ref in EP and p.GetNumber() == EP[ref]):
                bb = p.GetBoundingBox(); obst.append((um(bb.GetLeft()), um(bb.GetTop()), um(bb.GetRight()), um(bb.GetBottom())))
    # All LED pads: fixed squares whichever way an LED is turned.
    leds = {f.GetReference(): f for f in b.GetFootprints() if f.GetReference().startswith("D")}
    tops = []
    for ref, f in leds.items():
        a = math.radians(-f.GetOrientationDegrees()); c0 = f.GetPosition()
        for p in f.Pads():
            c = p.GetPosition(); tops.append((um(c.x), um(c.y), math.cos(a), math.sin(a), ref))
    def top_dist(x, y, skip=None):
        best = 9.0
        for px, py, c, s_, ref in tops:
            if abs(px-x) > 1 or abs(py-y) > 1 or (skip and (abs(px-skip[0]) < 1e-3 and abs(py-skip[1]) < 1e-3)):
                continue
            dx, dy = x-px, y-py
            u, v = abs(c*dx+s_*dy)-LED_PAD_HALF, abs(-s_*dx+c*dy)-LED_PAD_HALF
            best = min(best, math.hypot(max(u, 0), max(v, 0)))
        return best
    U3 = fps["U3"].GetPosition(); ux, uy = um(U3.x), um(U3.y)
    l1 = fps["L1"].GetPosition(); lx, ly = um(l1.x), um(l1.y)
    def back_free(x, y):
        if math.hypot(x-OX, y-OY) > 18.6:
            return False
        for a, c, e, g in obst:
            dx = max(a-x, 0, x-e); dy = max(c-y, 0, y-g)
            if dx*dx + dy*dy < HOLE**2:
                return False
        for hx, hy, hr in holes:
            if math.hypot(x-hx, y-hy) < hr + .075 + .2:
                return False
        m = max(abs(x-ux), abs(y-uy))
        if 1.7 - VIA_R - CL < m < 2.2 + VIA_R + CL:
            return False
        if abs(x-lx) < 1.0 + VIA_R + CL and abs(y-ly) < .8 + VIA_R + CL:
            return False
        if OX + 1.2 < x < OX + 3.0 and OY - 2.9 < y < OY + 1.5:
            return False
        return True
    # Fan-out rings and the U3-to-flash corridor: pins need these on the back, so an LED via goes elsewhere when a stub can reach (trial 5).
    CH = [(um(fps[r].GetPosition().x), um(fps[r].GetPosition().y)) for r in ("U1", "U2", "U3")]
    def fan_free(x, y):
        if any(3.0 < max(abs(x-a), abs(y-c)) < 5.3 for a, c in CH):
            return False
        return not (OX - 5.2 < x < OX + 1.8 and OY - 3.3 < y < OY + 3.0)
    placed = []; stubs = []
    def clear(x, y):
        return all(math.hypot(x-a, y-c) >= .40 for a, c in placed) and all(seg_dist(x, y, *t) >= HOLE+STUB for t in stubs)
    def stub_ok(x0, y0, x, y):
        n = max(2, int(math.hypot(x-x0, y-y0)/.04))
        for i in range(1, n+1):
            px, py = x0+(x-x0)*i/n, y0+(y-y0)*i/n
            if top_dist(px, py, skip=(x0, y0)) < STUB+CL:
                return False
        for a, c in placed:
            if seg_dist(a, c, x0, y0, x, y) < HOLE+STUB:
                return False
        return all(min(seg_dist(t[0], t[1], x0, y0, x, y), seg_dist(t[2], t[3], x0, y0, x, y)) >= 2*STUB+CL for t in stubs)
    rings = [(r, 2*math.pi*k/24) for r in (.35, .45, .55, .65, .75, .85, .95, 1.1, 1.25, 1.4, 1.6) for k in range(24)]
    stat = {"in pad": 0, "stub": 0}; blocked = []; lens = []
    PREF = {}; PREF_STUB = float(os.environ.get("PREF_STUB", ".5"))
    for r_ in csv.DictReader(open(ROOT / os.environ.get("PENDANT_MAP", "design/study/b/matrix_map.csv"))):
        if r_.get("turn") not in (None, ""):
            PREF[r_["ref"]] = int(r_["turn"])
    turns = {}
    if os.environ.get("PROBE_OUT"):
        # Static via fit per site and turn, with no other LED's via placed yet: {"x,y": [[r clear of fan-out or null, r anywhere or null] x 4]}.
        STUB = .06; probe = {}
        for ref in sorted(leds, key=lambda r: int(r[1:])):
            f = leds[ref]; base = f.GetOrientationDegrees(); res = []
            for k in range(4):
                f.SetOrientationDegrees(base + 90*k)
                pad = next(p for p in f.Pads() if p.GetNumber() == "3"); c = pad.GetPosition(); x0, y0 = um(c.x), um(c.y); two = []
                for tier in (True, False):
                    got = None
                    if (not tier or fan_free(x0, y0)) and back_free(x0, y0):
                        got = 0.0
                    else:
                        for r, a in rings:
                            x, y = x0+r*math.cos(a), y0+r*math.sin(a)
                            if (not tier or fan_free(x, y)) and back_free(x, y) and top_dist(x, y) >= HOLE and stub_ok(x0, y0, x, y):
                                got = r; break
                    two.append(got)
                res.append(two)
            f.SetOrientationDegrees(base); p0 = f.GetPosition()
            probe[f"{um(p0.x)-OX:.3f},{um(p0.y)-OY:.3f}"] = res
        Path(os.environ["PROBE_OUT"]).write_text(json.dumps(probe)); print("probe written"); return
    FIRST = set(os.environ.get("ANODE_FIRST", "").split(","))    # LEDs that lost their spot to an earlier via take their pick first
    for ref in sorted(leds, key=lambda r: (r not in FIRST, int(r[1:]))):
        f = leds[ref]; base = f.GetOrientationDegrees(); best = None
        STUB = .1 if ref == "D235" else .06    # its anode is +3V3, a POWER net; last in the order, so earlier stubs keep .06
        # c-map: a map's `turn` column is tried alone first and kept if its anode via fits within PREF_STUB; else the plain search over all four.
        pk = PREF.get(ref)
        if pk is not None:
            for tier in (True,):
                f.SetOrientationDegrees(base + 90*pk)
                pad = next(p for p in f.Pads() if p.GetNumber() == "3"); c = pad.GetPosition(); x0, y0 = um(c.x), um(c.y)
                if (not tier or fan_free(x0, y0)) and back_free(x0, y0) and clear(x0, y0):
                    best = (0.0, pk, x0, y0, x0, y0); break
                for r, a in rings:
                    if r > PREF_STUB:
                        break
                    x, y = x0+r*math.cos(a), y0+r*math.sin(a)
                    if (not tier or fan_free(x, y)) and back_free(x, y) and clear(x, y) and top_dist(x, y) >= HOLE and stub_ok(x0, y0, x, y):
                        best = (r, pk, x0, y0, x, y); break
                if best:
                    break
            stat["turn kept" if best else "turn changed"] = stat.get("turn kept" if best else "turn changed", 0) + 1
        for tier in (True, False):
            if best:
                break
            for k in ([pk, (pk+1) % 4, (pk+3) % 4, (pk+2) % 4] if pk is not None else range(4)):   # nearest the wanted turn first
                f.SetOrientationDegrees(base + 90*k)
                pad = next(p for p in f.Pads() if p.GetNumber() == "3"); c = pad.GetPosition(); x0, y0 = um(c.x), um(c.y)
                if (not tier or fan_free(x0, y0)) and back_free(x0, y0) and clear(x0, y0):
                    best = (0.0, k, x0, y0, x0, y0); break
                for r, a in rings:
                    if best and r >= best[0]:
                        break
                    x, y = x0+r*math.cos(a), y0+r*math.sin(a)
                    if (not tier or fan_free(x, y)) and back_free(x, y) and clear(x, y) and top_dist(x, y) >= HOLE and stub_ok(x0, y0, x, y):
                        best = (r, k, x0, y0, x, y); break
            if best:
                break
        if best and not fan_free(best[4], best[5]):
            stat["in fan-out"] = stat.get("in fan-out", 0) + 1
        if not best:
            f.SetOrientationDegrees(base); blocked.append(ref); continue
        r, k, x0, y0, x, y = best
        f.SetOrientationDegrees(base + 90*k); turns[ref] = k
        pad = next(p for p in f.Pads() if p.GetNumber() == "3"); net = pad.GetNetCode()
        small = max(abs(x-ux), abs(y-uy)) < 2.95
        v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); v.SetWidth(mm(.2 if small else .25)); v.SetDrill(mm(.1 if small else .15))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(net); v.SetLocked(True); b.Add(v)
        placed.append((x, y))
        if r:
            t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(mm(x0), mm(y0))); t.SetEnd(pcbnew.VECTOR2I(mm(x), mm(y))); t.SetWidth(mm(2*STUB)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(net); t.SetLocked(True); b.Add(t)
            stubs.append((x0, y0, x, y)); stat["stub"] += 1; lens.append(r)
        else:
            stat["in pad"] += 1
    print("anode vias", stat, "longest stub", max(lens or [0]), "blocked", blocked)
    (HW / "turns.json").write_text(json.dumps(turns))
    # A via in every cathode pad the back side allows: gets the matrix off the crowded LED side and onto the inner layers (trial 3, decisions.md).
    # Exposed pads count as obstacles here, so they aren't cut further, and U3's band stays whole.
    eps = []
    for ref, num in EP.items():
        for p in fps[ref].Pads():
            if p.GetNumber() == num and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                bb = p.GetBoundingBox(); eps.append((um(bb.GetLeft()), um(bb.GetTop()), um(bb.GetRight()), um(bb.GetBottom())))
    n_c = n_skip = 0
    for ref in sorted(leds, key=lambda r: int(r[1:])) if os.environ.get("CATHODE_VIAS") else ():
        for p in leds[ref].Pads():
            if p.GetNumber() == "3":
                continue
            c = p.GetPosition(); x, y = um(c.x), um(c.y)
            in_ep = any(math.hypot(max(a-x, 0, x-e), max(g-y, 0, y-h)) < HOLE for a, g, e, h in eps)
            if in_ep or max(abs(x-ux), abs(y-uy)) < 3.6 or not back_free(x, y) or not clear(x, y):
                n_skip += 1; continue
            v = pcbnew.PCB_VIA(b); v.SetPosition(c); v.SetWidth(mm(.25)); v.SetDrill(mm(.15))
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(p.GetNetCode()); v.SetLocked(True); b.Add(v)
            placed.append((x, y)); n_c += 1
    print("cathode vias", n_c, "left to the router", n_skip)
    # c-map: a cathode's land over a driver's exposed pad has no via site and must leave on F.Cu. EP_VIAS="U1,U2" gives each net one via through the pad, in a hole of its own,
    # for each cluster of its lands there (lands within EP_LINK mm), at the land nearest the cluster's middle that the via rules allow. The tile step below cuts the holes.
    ep_via = {}
    for chip in [c for c in os.environ.get("EP_VIAS", "").split(",") if c]:
        link = float(os.environ.get("EP_LINK", "2.6"))
        bb = [p.GetBoundingBox() for p in fps[chip].Pads() if p.GetNumber() == EP[chip] and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD]
        ax, ex = min(um(q.GetLeft()) for q in bb), max(um(q.GetRight()) for q in bb); ay, ey = min(um(q.GetTop()) for q in bb), max(um(q.GetBottom()) for q in bb)
        bynet = {}
        for ref, f in leds.items():
            for p in f.Pads():
                c = p.GetPosition(); x, y = um(c.x), um(c.y)
                if p.GetNumber() != "3" and ax < x < ex and ay < y < ey:
                    bynet.setdefault(p.GetNetname(), []).append((x, y, p.GetNetCode()))
        for net, ls in bynet.items():
            left = list(ls)
            while left:
                cl = [left.pop()]
                grew = True
                while grew:
                    grew = False
                    for q in list(left):
                        if any(math.dist(q[:2], m[:2]) <= link for m in cl):
                            cl.append(q); left.remove(q); grew = True
                mx, my = sum(q[0] for q in cl)/len(cl), sum(q[1] for q in cl)/len(cl)
                for x, y, code in sorted(cl, key=lambda q: math.hypot(q[0]-mx, q[1]-my)):
                    if back_free(x, y) and clear(x, y):
                        v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); v.SetWidth(mm(.25)); v.SetDrill(mm(.15))
                        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(code); v.SetLocked(True); b.Add(v)
                        placed.append((x, y)); ep_via[chip] = ep_via.get(chip, 0)+1
                        break
                else:
                    ep_via[chip+" no spot"] = ep_via.get(chip+" no spot", 0)+1
    print("cathode vias through exposed pads", ep_via)
    # Exposed pads as tiles round foreign vias; thermal vias where a through via misses the LED side's pads.
    gnd = b.FindNet("GND").GetNetCode(); th = {}
    COUNT = {"U1": 16, "U2": 16, "U3": 9, "U5": 4}
    for ref, num in EP.items():
        f = fps[ref]
        old = [p for p in f.Pads() if p.GetNumber() == num and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD]
        boxes = [p.GetBoundingBox() for p in old]
        x0, x1 = min(um(q.GetLeft()) for q in boxes), max(um(q.GetRight()) for q in boxes)
        y0, y1 = min(um(q.GetTop()) for q in boxes), max(um(q.GetBottom()) for q in boxes)
        net = old[0].GetNetCode()
        for p in list(f.Pads()):
            if p.GetNumber() == num and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD or (p.GetNumber() == "" and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD):
                f.Remove(p)
        inside = [(a, c) for a, c in placed if x0-.3 < a < x1+.3 and y0-.3 < c < y1+.3]
        CELL = .15; nx = round((x1-x0)/CELL); ny = round((y1-y0)/CELL); dx = (x1-x0)/nx; dy = (y1-y0)/ny
        def ok(i, j):
            ax, cx = x0+i*dx, y0+j*dy
            for a, c in inside:
                if math.hypot(max(ax-a, 0, a-ax-dx), max(cx-c, 0, c-cy_(j))) < .075+.2+.025:
                    return False
            return True
        cy_ = lambda j: y0+(j+1)*dy
        cols = []
        for i in range(nx):
            spans = []; j = 0
            while j < ny:
                if ok(i, j):
                    s_ = j
                    while j < ny and ok(i, j):
                        j += 1
                    spans.append((s_, j))
                else:
                    j += 1
            cols.append(tuple(spans))
        i = 0; n_t = 0
        while i < nx:
            e = i
            while e+1 < nx and cols[e+1] == cols[i]:
                e += 1
            for a, c in cols[i]:
                pd = pcbnew.PAD(f); pd.SetShape(pcbnew.PAD_SHAPE_RECT); pd.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
                ls = pcbnew.LSET(); ls.AddLayer(pcbnew.B_Cu); ls.AddLayer(pcbnew.B_Mask); pd.SetLayerSet(ls)
                pd.SetSize(pcbnew.VECTOR2I(mm((e-i+1)*dx+.02), mm((c-a)*dy+.02)))
                pd.SetNumber(num); f.Add(pd)
                pd.SetPosition(pcbnew.VECTOR2I(mm(x0+(i+e+1)*dx/2), mm(y0+(a+c)*dy/2)))
                pd.SetOrientationDegrees(0)
                pd.SetNetCode(net); n_t += 1
            i = e+1
        cands = []
        X = x0+.15
        while X < x1-.1:
            Y = y0+.15
            while Y < y1-.1:
                cands.append((X, Y)); Y += .1
            X += .1
        cx, cy = (x0+x1)/2, (y0+y1)/2
        cands.sort(key=lambda q: math.hypot(q[0]-cx, q[1]-cy))
        got = []
        for q in cands:
            if len(got) >= COUNT[ref]:
                break
            if top_dist(*q) >= HOLE and all(math.hypot(q[0]-a, q[1]-c) >= .40 for a, c in placed) and all(seg_dist(q[0], q[1], *t) >= HOLE+STUB for t in stubs) \
                    and all(math.hypot(q[0]-a, q[1]-c) >= .75 for a, c in got):
                got.append(q)
        for q in got:
            v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(mm(q[0]), mm(q[1]))); v.SetWidth(mm(.25)); v.SetDrill(mm(.15)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(gnd); v.SetLocked(True); b.Add(v)
            placed.append(q)
        th[ref] = dict(tiles=n_t, foreign_vias=len(inside), thermal=len(got))
    print(th)
    pcbnew.SaveBoard(str(PCB), b)


def zones_b():
    """Planes for routing: GND on In2, VSYS and +3V3 on In4, the RP2350 1V1 ring and 3V3 band on B.Cu (chips/rp2350.md), no In2 copper under LX."""
    import pcbnew, math
    b = pcbnew.LoadBoard(str(PCB)); mm = pcbnew.FromMM
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    def poly(pts):
        p = pcbnew.SHAPE_POLY_SET(); p.NewOutline()
        for x, y in pts:
            p.Append(mm(OX+x), mm(OY+y))
        return p
    def add(name, layer, net, pts, prio, connect=pcbnew.ZONE_CONNECTION_FULL, minw=.1, clear=None):
        z = pcbnew.ZONE(b); z.SetZoneName(name); z.SetLayer(layer); z.SetNet(b.FindNet(net)); z.SetAssignedPriority(prio)
        z.SetPadConnection(connect); z.SetMinThickness(mm(minw)); z.SetThermalReliefGap(mm(.2)); z.SetThermalReliefSpokeWidth(mm(.2))
        if clear: z.SetLocalClearance(mm(clear))
        pl = poly(pts); pl.thisown = False; z.SetOutline(pl); b.Add(z); return z
    circle = [(18.8*math.cos(2*math.pi*k/96), 18.8*math.sin(2*math.pi*k/96)) for k in range(96)]
    add("plane GND", pcbnew.In2_Cu, "GND", circle, 0)
    add("plane VSYS", pcbnew.In4_Cu, "VSYS", circle, 0)
    # 3V3 island: the MCU, flash, LDO and accelerometer. Drivers stay on VSYS either side.
    # Boundaries pass between pads, from the pad list: U6 OUT and C4 in, its IN and C3 out; C14 and U5's EN1 in, C2 and U5's OUT out; TP1 out.
    r = 18.8; yl, yr = -5.5, -6.0
    a0, a1 = math.atan2(yl, -math.sqrt(r*r-yl*yl)), math.atan2(yr, math.sqrt(r*r-yr*yr))
    arc = [(r*math.cos(a0+(a1-a0)*k/32), r*math.sin(a0+(a1-a0)*k/32)) for k in range(33)]
    island = [(-5.3, 9.0), (-5.3, -2.6), (-7.2, -2.6), (-7.2, yl)] + arc + [(4.75, yr), (4.75, 9.0)]
    add("plane 3V3", pcbnew.In4_Cu, "+3V3", island, 1)
    u = fps["U3"].GetPosition(); ux, uy = pcbnew.ToMM(u.x)-OX, pcbnew.ToMM(u.y)-OY
    sq = lambda h: [(ux-h, uy-h), (ux+h, uy-h), (ux+h, uy+h), (ux-h, uy+h)]
    add("RP2350 band", pcbnew.B_Cu, "+3V3", sq(2.8), 1)
    add("RP2350 ring", pcbnew.B_Cu, "+1V1", sq(2.2), 3, connect=pcbnew.ZONE_CONNECTION_THERMAL, minw=.2)
    # EP keeps its own copper: ring zone stays out by giving the pad priority through clearance (GND pad is a foreign pad).
    # No In2 copper under the switch node.
    lxpads = [p for p in fps["L1"].Pads() if p.GetNetname().endswith("VREG_LX")] + [p for p in fps["U3"].Pads() if p.GetNetname().endswith("VREG_LX")]
    bbs = [p.GetBoundingBox() for p in lxpads]
    x0 = min(pcbnew.ToMM(q.GetLeft()) for q in bbs)-OX-.3; x1 = max(pcbnew.ToMM(q.GetRight()) for q in bbs)-OX+.3
    y0 = min(pcbnew.ToMM(q.GetTop()) for q in bbs)-OY-.3; y1 = max(pcbnew.ToMM(q.GetBottom()) for q in bbs)-OY+.3
    k = pcbnew.ZONE(b); k.SetIsRuleArea(True); k.SetZoneName("LX no plane"); k.SetLayer(pcbnew.In2_Cu)
    k.SetDoNotAllowCopperPour(True); k.SetDoNotAllowTracks(False); k.SetDoNotAllowVias(False); k.SetDoNotAllowPads(False); k.SetDoNotAllowFootprints(False)
    pl = poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]); pl.thisown = False; k.SetOutline(pl); b.Add(k)
    print("LX cut", round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2))
    # Inside each pad ring, no tracks on the back: the router wrapped long nets under the chips and walled in pins (trial 5, chips/rp2350.md).
    for ref, h in (("U1", 2.9), ("U2", 2.9), ("U3", 2.9)):
        u_ = fps[ref].GetPosition(); ax, ay = pcbnew.ToMM(u_.x)-OX, pcbnew.ToMM(u_.y)-OY
        k = pcbnew.ZONE(b); k.SetIsRuleArea(True); k.SetZoneName(f"{ref} no tracks inside pads"); k.SetLayer(pcbnew.B_Cu)
        k.SetDoNotAllowCopperPour(False); k.SetDoNotAllowTracks(True); k.SetDoNotAllowVias(False); k.SetDoNotAllowPads(False); k.SetDoNotAllowFootprints(False)
        pl = poly([(ax-h, ay-h), (ax+h, ay-h), (ax+h, ay+h), (ax-h, ay+h)]); pl.thisown = False; k.SetOutline(pl); b.Add(k)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(str(PCB), b)
    print("zones", [(z.GetZoneName()) for z in b.Zones()])


if __name__ == "__main__":
    {"rules": rules, "stack": stack, "sync": sync, "place": place, "anodes": anodes, "place_b": place_b, "place_c": place_c, "anodes_b": anodes_b, "zones_b": zones_b}[sys.argv[1]]()
