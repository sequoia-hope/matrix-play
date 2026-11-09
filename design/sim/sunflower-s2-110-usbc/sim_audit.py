#!/usr/bin/env python3
"""
Reproducible Phase 8 SI, PDN, Crosstalk, Control-Loop & Thermal Verification
for Sunflower s2-110-usbc (hw/sunflower/s2-110-usbc/sunflower.kicad_pcb).

Run from repository root:
    python3 design/sim/sunflower-s2-110-usbc/sim_audit.py

Outputs:
  - Printed trigger, DC-IR, PDN Z(f), SSO, crosstalk, and thermal tables (stdout)
  - design/sim/sunflower-s2-110-usbc/pdn_headroom.png
  - design/sim/sunflower-s2-110-usbc/thermal_rise.png
"""
import heapq
import math
from collections import defaultdict
from pathlib import Path
import pcbnew
from PIL import Image, ImageDraw, ImageFont

PCB_PATH = Path("hw/sunflower/s2-110-usbc/sunflower.kicad_pcb")
OUT_DIR = Path("design/sim/sunflower-s2-110-usbc")
OUT_DIR.mkdir(parents=True, exist_ok=True)

board = pcbnew.LoadBoard(str(PCB_PATH))

# Exact JLC04161H-7628 copper thicknesses from sunflower.kicad_pcb stackup:
#   Outer (F.Cu, B.Cu): t = 0.0350 mm (1.0 oz finished)
#   Inner (In1.Cu, In2.Cu): t = 0.0152 mm (0.5 oz foil = 15.2 um finished in .kicad_pcb)
# Copper resistivity: rho(T) = 17.24e-9 * (1 + 0.00393 * (T - 20)) Ohm*m
#   @ 25 C: rho = 17.58e-9 -> R_sh_outer = 0.502 mOhm/sq, R_sh_inner = 1.157 mOhm/sq
#   @ 70 C: rho = 20.63e-9 -> R_sh_outer = 0.589 mOhm/sq, R_sh_inner = 1.357 mOhm/sq
RSH_25 = {"F.Cu": 0.502, "B.Cu": 0.502, "In1.Cu": 1.157, "In2.Cu": 1.157}
RSH_70 = {"F.Cu": 0.589, "B.Cu": 0.589, "In1.Cu": 1.357, "In2.Cu": 1.357}
# 0.15 mm drill, 20 um barrel plating (checks.toml via_plating_mm = 0.020), h = 1.586 mm:
# A_barrel = pi * (0.075^2 - 0.055^2) = 0.008168 mm^2 -> R_via_70 = 20.63e-6 * 1.586 / 0.008168 = 4.01 mOhm full span
R_VIA_70 = 4.01

net_segs = defaultdict(list)  # net -> [(layer, x1, y1, x2, y2, w, L)]
net_vias = defaultdict(list)  # net -> [(x, y, drill, width)]

for t in board.GetTracks():
    net = t.GetNetname()
    if t.GetClass() == "PCB_VIA":
        p = t.GetPosition()
        net_vias[net].append((
            pcbnew.ToMM(p.x),
            pcbnew.ToMM(p.y),
            pcbnew.ToMM(t.GetDrillValue()),
            pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)),
        ))
    else:
        ln = board.GetLayerName(t.GetLayer())
        s, e = t.GetStart(), t.GetEnd()
        x1, y1 = pcbnew.ToMM(s.x), pcbnew.ToMM(s.y)
        x2, y2 = pcbnew.ToMM(e.x), pcbnew.ToMM(e.y)
        w = pcbnew.ToMM(t.GetWidth())
        L = math.hypot(x2 - x1, y2 - y1)
        net_segs[net].append((ln, x1, y1, x2, y2, w, L))


def net_stats(net: str):
    segs = net_segs[net]
    vias = net_vias[net]
    tot_len = sum(s[6] for s in segs)
    by_layer = defaultdict(float)
    r70 = 0.0
    widths = [s[5] for s in segs if s[6] > 0.02]
    for ln, x1, y1, x2, y2, w, L in segs:
        by_layer[ln] += L
        if w > 0:
            r70 += (L / w) * RSH_70.get(ln, 1.357)
    return {
        "len": tot_len,
        "vias": len(vias),
        "w_min": min(widths) if widths else 0.0,
        "w_max": max(widths) if widths else 0.0,
        "by_layer": dict(by_layer),
        "r_tracks_70_mOhm": r70,
    }


fp_map = {fp.GetReference(): fp for fp in board.GetFootprints()}


def get_pad(ref: str, num: str):
    for p in fp_map[ref].Pads():
        if p.GetNumber() == str(num):
            return p
    raise KeyError((ref, num))


def pad_contains_xy(pad, x_mm: float, y_mm: float, margin_mm: float = 0.14) -> bool:
    px, py = pcbnew.ToMM(pad.GetPosition().x), pcbnew.ToMM(pad.GetPosition().y)
    sx, sy = pcbnew.ToMM(pad.GetSize().x), pcbnew.ToMM(pad.GetSize().y)
    # Conservative rotated/unrotated bounding radius + exact rotated check (try both signs of KiCad Y-down angle)
    dx, dy = x_mm - px, y_mm - py
    for sgn in (1.0, -1.0):
        ang = sgn * math.radians(pad.GetOrientation().AsDegrees())
        lx = abs(dx * math.cos(ang) + dy * math.sin(ang))
        ly = abs(-dx * math.sin(ang) + dy * math.cos(ang))
        if lx <= sx / 2.0 + margin_mm and ly <= sy / 2.0 + margin_mm:
            return True
    return False


def pt_seg_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    l2 = dx * dx + dy * dy
    if l2 < 1e-12:
        return math.hypot(px - x1, py - y1), 0.0
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / l2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy)), t


def pad_to_pad_r70(net: str, src_ref: str, src_num: str, dst_ref: str, dst_num: str):
    def snap(x, y):
        return (round(x, 3), round(y, 3))

    adj = defaultdict(list)
    layers = ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]

    # Collect all interesting split points per layer (endpoints, vias, pad centers) so T-junctions connect!
    layer_pts = defaultdict(set)
    for ln, x1, y1, x2, y2, w, L in net_segs[net]:
        layer_pts[ln].add(snap(x1, y1))
        layer_pts[ln].add(snap(x2, y2))
    for vx, vy, dr, vw in net_vias[net]:
        for ln in layers:
            layer_pts[ln].add(snap(vx, vy))
    net_pads = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() == net:
                net_pads.append((fp, pad))
                px, py = pcbnew.ToMM(pad.GetPosition().x), pcbnew.ToMM(pad.GetPosition().y)
                pls = layers if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH else [fp.GetLayerName()]
                for ln in pls:
                    layer_pts[ln].add(snap(px, py))

    for ln, x1, y1, x2, y2, w, L in net_segs[net]:
        if L < 1e-6:
            continue
        ts = [0.0, 1.0]
        for px, py in layer_pts[ln]:
            d, t = pt_seg_dist(px, py, x1, y1, x2, y2)
            if 0.0 < t < 1.0 and d <= max(w / 2.0, 0.08) + 0.05:
                ts.append(t)
        ts = sorted(set(round(t, 5) for t in ts))
        for i in range(len(ts) - 1):
            ta, tb = ts[i], ts[i + 1]
            subL = L * (tb - ta)
            if subL < 1e-6:
                continue
            ua = (ln, snap(x1 + ta * (x2 - x1), y1 + ta * (y2 - y1)))
            ub = (ln, snap(x1 + tb * (x2 - x1), y1 + tb * (y2 - y1)))
            r = (subL / max(w, 0.09)) * RSH_70.get(ln, 1.357)
            adj[ua].append((ub, r, subL, 0))
            adj[ub].append((ua, r, subL, 0))

    # Link coincident/sub-10um-adjacent track nodes on the same layer (handles 0.5 um router float rounding)
    tnodes_by_layer = defaultdict(list)
    for nln, nxy in list(adj.keys()):
        tnodes_by_layer[nln].append(nxy)
    for ln, xy_list in tnodes_by_layer.items():
        xy_s = sorted(xy_list)
        for i in range(len(xy_s)):
            for j in range(i + 1, len(xy_s)):
                if xy_s[j][0] - xy_s[i][0] > 0.015:
                    break
                if math.hypot(xy_s[j][0] - xy_s[i][0], xy_s[j][1] - xy_s[i][1]) <= 0.015:
                    adj[(ln, xy_s[i])].append(((ln, xy_s[j]), 0.0, 0.0, 0))
                    adj[(ln, xy_s[j])].append(((ln, xy_s[i]), 0.0, 0.0, 0))

    track_nodes = list(adj.keys())
    for vx, vy, dr, vw in net_vias[net]:
        p = snap(vx, vy)
        for ln in layers:
            vn = ("VIA_" + ln, p)
            adj[vn]
            for nln, nxy in track_nodes:
                if nln == ln and math.hypot(nxy[0] - p[0], nxy[1] - p[1]) <= vw / 2 + 0.12:
                    adj[vn].append(((nln, nxy), 0.03, 0.0, 0))
                    adj[(nln, nxy)].append((vn, 0.03, 0.0, 0))
        spans = [
            ("F.Cu", "In1.Cu", 0.2104 / 1.4858, 1),
            ("In1.Cu", "In2.Cu", 1.0650 / 1.4858, 0),
            ("In2.Cu", "B.Cu", 0.2104 / 1.4858, 1),
        ]
        for la, lb, frac, vcnt in spans:
            ua, ub = ("VIA_" + la, p), ("VIA_" + lb, p)
            adj[ua].append((ub, R_VIA_70 * frac, 0.0, vcnt))
            adj[ub].append((ua, R_VIA_70 * frac, 0.0, vcnt))

    existing_nodes = list(adj.keys())
    for fp, pad in net_pads:
        px, py = pcbnew.ToMM(pad.GetPosition().x), pcbnew.ToMM(pad.GetPosition().y)
        pad_layers = layers if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH else [fp.GetLayerName()]
        phub = ("PAD", f"{fp.GetReference()}.{pad.GetNumber()}")
        adj[phub]
        for nln, nxy in existing_nodes:
            if nln == "PAD":
                continue
            base_ln = nln[4:] if nln.startswith("VIA_") else nln
            if base_ln in pad_layers and pad_contains_xy(pad, nxy[0], nxy[1], 0.14):
                adj[phub].append(((nln, nxy), 0.05, 0.0, 0))
                adj[(nln, nxy)].append((phub, 0.05, 0.0, 0))
        for ln, x1, y1, x2, y2, w, L in net_segs[net]:
            if ln in pad_layers:
                d, t = pt_seg_dist(px, py, x1, y1, x2, y2)
                cx, cy = x1 + t * (x2 - x1), y1 + t * (y2 - y1)
                if pad_contains_xy(pad, cx, cy, 0.10):
                    u_end = (ln, snap(x1, y1))
                    r_half = (L * t / max(w, 0.09)) * RSH_70.get(ln, 1.357)
                    adj[phub].append((u_end, r_half, L * t, 0))
                    adj[u_end].append((phub, r_half, L * t, 0))

    existing_with_pads = [k for k in adj.keys() if k[0] != "PAD"]
    for z in board.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != net:
            continue
        for ln in layers:
            lid = board.GetLayerID(ln)
            if not z.IsOnLayer(lid):
                continue
            ps = z.GetFilledPolysList(lid)
            for i in range(ps.OutlineCount()):
                piece_nodes = []
                for nln, nxy in existing_with_pads:
                    base_ln = nln[4:] if nln.startswith("VIA_") else nln
                    if base_ln == ln:
                        pt = pcbnew.VECTOR2I(pcbnew.FromMM(nxy[0]), pcbnew.FromMM(nxy[1]))
                        if ps.Outline(i).PointInside(pt):
                            piece_nodes.append((nln, nxy))
                if len(piece_nodes) > 1:
                    hub = (f"ZONE_{ln}_{id(z)}_{i}", (0.0, 0.0))
                    r_half = 0.4 * RSH_70.get(ln, 0.589)
                    for pn in piece_nodes:
                        adj[hub].append((pn, r_half, 0.0, 0))
                        adj[pn].append((hub, r_half, 0.0, 0))

    s_node = ("PAD", f"{src_ref}.{src_num}")
    d_node = ("PAD", f"{dst_ref}.{dst_num}")

    pq = [(0.0, 0.0, 0, s_node)]
    dist = {s_node: (0.0, 0.0, 0)}
    while pq:
        r_cur, l_cur, v_cur, u = heapq.heappop(pq)
        if u == d_node:
            return r_cur, l_cur, v_cur
        if r_cur > dist[u][0] + 1e-9:
            continue
        for v, w_r, w_l, w_v in adj[u]:
            nr, nl, nv = r_cur + w_r, l_cur + w_l, v_cur + w_v
            if v not in dist or nr < dist[v][0] - 1e-9:
                dist[v] = (nr, nl, nv)
                heapq.heappush(pq, (nr, nl, nv, v))
    return -1.0, -1.0, -1


print("=== 1. PHASE 8 SIMULATION TRIGGER & COPPER SUMMARY (JLC04161H-7628, t_in=15.2 um) ===")
key_nets = [
    "VBUS", "VBAT", "/Power/BAT_N", "VSYS", "+3V3", "+1V1", "GND",
    "/MCU/VREG_LX", "/MCU/VREG_AVDD",
    "/Power/USB_DP_C", "/Power/USB_DM_C", "USB_DP", "USB_DM", "/MCU/USB_DP_MCU", "/MCU/USB_DM_MCU",
    "/MCU/QSPI_SCLK", "/MCU/QSPI_SD0", "/MCU/QSPI_SD1", "/MCU/QSPI_SD2", "/MCU/QSPI_SD3", "/MCU/QSPI_SS",
    "Net-(R16-Pad2)",
    "Net-(U3-XIN)", "Net-(U3-XOUT)", "Net-(C24-Pad1)",
    "I2C_SDA", "I2C_SCL", "/MCU/ACC_SDA", "/MCU/ACC_SCL",
    "/MCU/LIGHT", "VBAT_SENSE",
]
for n in key_nets:
    if n in net_segs or n in net_vias:
        st = net_stats(n)
        layers_str = ", ".join(f"{k}:{v:.2f}" for k, v in sorted(st["by_layer"].items()))
        print(
            f"  {n:22s} len={st['len']:6.2f}mm vias={st['vias']:2d} "
            f"w=[{st['w_min']:.2f}..{st['w_max']:.2f}] R70_all={st['r_tracks_70_mOhm']:6.1f}mOhm ({layers_str})"
        )

sw_stats = [(n, net_stats(n)) for n in sorted(net_segs) if "/SW1_" in n or "/SW2_" in n]
cs_stats = [(n, net_stats(n)) for n in sorted(net_segs) if "/CS1_" in n or "/CS2_" in n]
sw_worst = max(sw_stats, key=lambda x: x[1]["r_tracks_70_mOhm"])
cs_worst = max(cs_stats, key=lambda x: x[1]["r_tracks_70_mOhm"])
print(f"  SW worst copper R70  : {sw_worst[0]} len={sw_worst[1]['len']:.2f}mm R70={sw_worst[1]['r_tracks_70_mOhm']:.1f}mOhm vias={sw_worst[1]['vias']}")
print(f"  CS worst copper R70  : {cs_worst[0]} len={cs_worst[1]['len']:.2f}mm R70={cs_worst[1]['r_tracks_70_mOhm']:.1f}mOhm vias={cs_worst[1]['vias']}")

print("\n=== 2. EXACT SHORTEST-PATH PAD-TO-PAD DC RESISTANCE @ 70 C ===")
paths = [
    ("VBUS: J1.A4 -> U5.13", "VBUS", "J1", "A4", "U5", "13"),
    ("VBAT: BT1.1 -> U5.2", "VBAT", "BT1", "1", "U5", "2"),
    ("BAT_N: BT1.2 -> U8.4", "/Power/BAT_N", "BT1", "2", "U8", "4"),
    ("VSYS: U5.10 -> U6.4 (3V3 LDO)", "VSYS", "U5", "10", "U6", "4"),
    ("VSYS: U5.10 -> U1.5 (PVCC)", "VSYS", "U5", "10", "U1", "5"),
    ("VSYS: U5.10 -> U2.5 (PVCC)", "VSYS", "U5", "10", "U2", "5"),
    ("+3V3: U6.1 -> U3.49 (VREG_VIN)", "+3V3", "U6", "1", "U3", "49"),
    ("+3V3: U6.1 -> U3.44 (ADC_AVDD)", "+3V3", "U6", "1", "U3", "44"),
    ("+3V3: U6.1 -> U4.8 (Flash VCC)", "+3V3", "U6", "1", "U4", "8"),
    ("+3V3: C14.1 -> U4.8 (nearest cap)", "+3V3", "C14", "1", "U4", "8"),
    ("+1V1: C18.1 -> U3.50 (VREG_FB)", "+1V1", "C18", "1", "U3", "50"),
    ("+1V1: C18.1 -> U3.23 (DVDD N)", "+1V1", "C18", "1", "U3", "23"),
    ("+1V1: C18.1 -> U3.39 (DVDD E)", "+1V1", "C18", "1", "U3", "39"),
]
path_dict = {}
for label, net, sr, sn, dr, dn in paths:
    r, l, v = pad_to_pad_r70(net, sr, sn, dr, dn)
    path_dict[label] = (r, l, v)
    print(f"  {label:34s}: R_70 = {r:6.2f} mOhm, L_track = {l:5.2f} mm, transitions = {v}")

r_bat_loop = path_dict["VBAT: BT1.1 -> U5.2"][0] + path_dict["BAT_N: BT1.2 -> U8.4"][0]
print(f"  Combined PCB battery loop (VBAT + BAT_N) @ 70 C = {r_bat_loop:.1f} mOhm (+ ~112 mOhm conn+U8+U5 FETs = {r_bat_loop+112:.1f} mOhm total)")

# 3. Board-wide Aggressor / Victim Geometric Coupling Scan
print("\n=== 3. BOARD-WIDE AGGRESSOR / VICTIM COUPLING SCAN ===")


def is_aggressor(n: str) -> bool:
    return (
        n == "/MCU/VREG_LX"
        or "/SW1_" in n or "/SW2_" in n
        or "/CS1_" in n or "/CS2_" in n
        or "/MCU/QSPI_" in n
        or "USB_" in n
    )


def is_victim(n: str) -> bool:
    return n in {
        "/MCU/LIGHT", "VBAT_SENSE", "/MCU/VREG_AVDD",
        "Net-(U1-ISET)", "Net-(U2-ISET)", "Net-(U5-ILIM)", "Net-(U5-ISET)", "Net-(U5-TS)", "Net-(U8-VDD)",
        "Net-(U3-XIN)", "Net-(U3-XOUT)", "Net-(C24-Pad1)",
        "+3V3", "+1V1", "VSYS",
        "I2C_SCL", "I2C_SDA", "/MCU/ACC_SCL", "/MCU/ACC_SDA", "/MCU/RUN",
    }


def parallel_overlap(seg_a, seg_b):
    _, ax1, ay1, ax2, ay2, aw, aL = seg_a
    _, bx1, by1, bx2, by2, bw, bL = seg_b
    if aL < 0.15 or bL < 0.15:
        return None
    ux, uy = (ax2 - ax1) / aL, (ay2 - ay1) / aL
    vx, vy = (bx2 - bx1) / bL, (by2 - by1) / bL
    cos_ang = abs(ux * vx + uy * vy)
    if cos_ang < 0.92:  # within ~23 deg of parallel
        return None
    # Project B onto A's axis
    p1 = (bx1 - ax1) * ux + (by1 - ay1) * uy
    p2 = (bx2 - ax1) * ux + (by2 - ay1) * uy
    ov_lo, ov_hi = max(0.0, min(p1, p2)), min(aL, max(p1, p2))
    ov = ov_hi - ov_lo
    if ov < 0.25:
        return None
    # Perpendicular center-to-center distance
    mid_p = 0.5 * (ov_lo + ov_hi)
    mx, my = ax1 + mid_p * ux, ay1 + mid_p * uy
    # Distance from midpoint on A to line B
    nx, ny = -vy, vx
    d_cc = abs((mx - bx1) * nx + (my - by1) * ny)
    edge_gap = max(0.0, d_cc - 0.5 * (aw + bw))
    return ov, d_cc, edge_gap


agg_segs = [(n, s) for n in net_segs if is_aggressor(n) for s in net_segs[n]]
vic_segs = [(n, s) for n in net_segs if is_victim(n) for s in net_segs[n]]

coplanar_pairs = defaultdict(lambda: [0.0, 99.0])  # (agg, vic, layer) -> [sum_ov_mm, min_edge_gap_mm]
broadside_pairs = defaultdict(lambda: [0.0, 99.0])  # (agg, vic, l_pair) -> [sum_ov_mm, min_dcc_mm]

for an, sa in agg_segs:
    for vn, sv in vic_segs:
        if an == vn:
            continue
        la, lv = sa[0], sv[0]
        if la == lv:
            res = parallel_overlap(sa, sv)
            if res and res[2] <= 0.30:
                rec = coplanar_pairs[(an, vn, la)]
                rec[0] += res[0]
                rec[1] = min(rec[1], res[2])
        elif {la, lv} in ({"F.Cu", "In1.Cu"}, {"B.Cu", "In2.Cu"}):
            res = parallel_overlap(sa, sv)
            if res and res[1] <= 0.35:
                rec = broadside_pairs[(an, vn, f"{la}<->{lv}")]
                rec[0] += res[0]
                rec[1] = min(rec[1], res[1])

# Also check In2.Cu segments directly beneath B.Cu Zone 5 (vendor /MCU/VREG_LX) + L1 body
lx_zone = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == "/MCU/VREG_LX"][0]
lx_ps = lx_zone.GetFilledPolysList(board.GetLayerID("B.Cu"))
print("  [3a] In2.Cu segments under B.Cu VREG_LX pour / L1 (h = 0.2104 mm):")
for vn, segs in sorted(net_segs.items()):
    for ln, x1, y1, x2, y2, w, L in segs:
        if ln != "In2.Cu":
            continue
        in_lx = 0
        in_l1 = 0
        for k in range(20):
            f = (k + 0.5) / 20.0
            xx, yy = x1 + f * (x2 - x1), y1 + f * (y2 - y1)
            pt = pcbnew.VECTOR2I(pcbnew.FromMM(xx), pcbnew.FromMM(yy))
            if any(lx_ps.Outline(i).PointInside(pt) for i in range(lx_ps.OutlineCount())):
                in_lx += 1
            if 99.60 <= xx <= 101.60 and 99.80 <= yy <= 101.40:
                in_l1 += 1
        if in_lx > 0 or in_l1 > 0:
            ov_lx = L * (in_lx / 20.0)
            ov_l1 = L * (in_l1 / 20.0)
            # Parallel-plate + fringing capacitance (fF): eps0*eps_r*(ov_lx*w)/h * 1.8 fringing
            c_mut_fF = 8.854 * 4.5 * (ov_lx * w) / 0.2104 * 1.8
            print(
                f"    In2.Cu {vn:16s} ({x1:.2f},{y1:.2f})->({x2:.2f},{y2:.2f}) w={w:.2f}mm "
                f"L={L:.2f}mm ov_LX_pour={ov_lx:.2f}mm ov_L1_body={ov_l1:.2f}mm C_mut~={c_mut_fF:.0f}fF"
            )

print("  [3b] Top co-planar parallel runs (edge gap <= 0.30 mm, parallel >= 0.80 mm):")
for (an, vn, ln), (ov, gap) in sorted(coplanar_pairs.items(), key=lambda x: (-x[1][0], x[1][1]))[:14]:
    if ov >= 0.80:
        print(f"    {ln:6s} {an:28s} <-> {vn:18s}: L_par={ov:5.2f} mm, min_gap={gap:5.3f} mm")

print("  [3c] Top adjacent-layer broadside runs (h = 0.2104 mm, d_cc <= 0.35 mm, parallel >= 0.50 mm):")
for (an, vn, lp), (ov, dcc) in sorted(broadside_pairs.items(), key=lambda x: (-x[1][0], x[1][1]))[:12]:
    if ov >= 0.50:
        print(f"    {lp:14s} {an:28s} <-> {vn:18s}: L_par={ov:5.2f} mm, min_dcc={dcc:5.3f} mm")

# 4. Quantitative SSO, PDN Z(f), USB skew, I2C tr, and Thermal checkpoints
print("\n=== 4. QUANTITATIVE SI / PI / THERMAL CHECKPOINTS ===")
L_u4_nH = 9.0
for mode, n_io, tr_ns in [("4-bit Quad-SPI (0xEB, fast edge)", 4, 1.5),
                          ("4-bit Quad-SPI (0xEB, 25% DRV)", 4, 2.0),
                          ("2-bit Dual-SPI (0xBB, 25% DRV)", 2, 2.0),
                          ("1-bit Fast-Read (0x0B, 25% DRV)", 1, 2.0)]:
    q_pC = n_io * 7.0 * 3.30
    dv_mV = 0.75 * L_u4_nH * (2.0 * q_pC / (tr_ns ** 2))
    print(f"  U4.8 SSO [{mode:32s}]: Q={q_pC:4.1f} pC, dV_droop ~= {dv_mV:5.0f} mV -> V_CC,min ~= {3.30 - dv_mV/1000:.2f} V (spec >= 2.70 V)")

st_dp_c, st_dp, st_dp_m = net_stats("/Power/USB_DP_C"), net_stats("USB_DP"), net_stats("/MCU/USB_DP_MCU")
st_dm_c, st_dm, st_dm_m = net_stats("/Power/USB_DM_C"), net_stats("USB_DM"), net_stats("/MCU/USB_DM_MCU")


def usb_flight_ps(stats_list):
    ps = 0.0
    for st in stats_list:
        for ln, L in st["by_layer"].items():
            ps += L * (7.09 if ln.startswith("In") else 6.06)
        ps += st["vias"] * 3.5
    return ps


t_dp_ps = usb_flight_ps([st_dp_c, st_dp, st_dp_m])
t_dm_ps = usb_flight_ps([st_dm_c, st_dm, st_dm_m])
print(f"  USB FS flight time: DP = {t_dp_ps:.1f} ps (34.55 mm, 5 vias), DM = {t_dm_ps:.1f} ps (35.87 mm, 6 vias), |dt| = {abs(t_dm_ps - t_dp_ps):.1f} ps (FS budget <= 2000 ps)")

# I2C0 1 MHz Fm+ with R21=R22=1.0 kOhm and routed 89.1 mm / 17-via bus (~40 pF total):
st_sda = net_stats("I2C_SDA")
C_i2c_pF = 15.0 + 0.10 * st_sda["len"] + 0.50 * st_sda["vias"] + 7.6  # ~40.0 pF
R_pu_ohm = 1000.0
tau_ns = R_pu_ohm * C_i2c_pF * 1e-3
tr_30_70_ns = tau_ns * math.log(0.7 / 0.3)
t_0_vil_vih_ns = tau_ns * math.log(3.30 / (3.30 - 2.40))
print(f"  I2C0 1 MHz Fm+ (R21/R22=1.0 kOhm, C_bus~={C_i2c_pF:.0f} pF): tr(30-70%)={tr_30_70_ns:.1f} ns (<=120 ns), t(0->2.4V)={t_0_vil_vih_ns:.1f} ns -> t_HIGH~={500-t_0_vil_vih_ns:.0f} ns (>=260 ns)")

for mode_lbl, tamb, rth, p_chg, v_sys, t_lim in [
    ("Wearable Battery (25 C amb, 35 K/W, 48 C skin limit)", 25.0, 35.0, 0.00, 3.90, 48.0),
    ("USB Charging CV taper (25 C amb, 35 K/W, P_chg=0.27W @4.1V, 45 C LiPo limit)", 25.0, 35.0, 0.27, 4.40, 45.0),
    ("USB Charging CC mid (25 C amb, 35 K/W, P_chg=0.36W @3.8V, 45 C LiPo limit)", 25.0, 35.0, 0.36, 4.40, 45.0),
    ("USB Charging low-bat (25 C amb, 35 K/W, P_chg=0.45W @3.5V, 45 C LiPo limit)", 25.0, 35.0, 0.45, 4.40, 45.0),
    ("Hot Ambient Battery (40 C amb, 35 K/W, 60 C LiPo discharge limit)", 40.0, 35.0, 0.00, 3.90, 60.0),
]:
    p_avail = (t_lim - tamb) / rth - 0.16 - p_chg
    p_led_255 = 0.85 * v_sys * 0.3543
    gcc_max = max(0, min(255, int(255.0 * p_avail / p_led_255)))
    t_at_128 = tamb + rth * (0.16 + p_chg + p_led_255 * (128.0 / 255.0))
    t_at_255 = tamb + rth * (0.16 + p_chg + p_led_255)
    print(f"  Thermal [{mode_lbl}]: GCC_max = {gcc_max:3d} (T@GCC128={t_at_128:.1f} C, T@GCC255={t_at_255:.1f} C)")

# 5. Generate Plot 1: Worst-Case U1 LED Current-Sink Headroom vs LiPo Cell Voltage V_cell (+ USB 4.40V marker)
W, H = 1080, 640
img1 = Image.new("RGB", (W, H), (255, 255, 255))
d1 = ImageDraw.Draw(img1)
try:
    f_t = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 19)
    f_l = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    f_b = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
except Exception:
    f_t = f_l = f_b = ImageFont.load_default()

px0, py0, px1, py1 = 95, 78, 1020, 548
d1.rectangle((px0, py0, px1, py1), outline=(40, 40, 50), width=2, fill=(250, 251, 253))


def xy1(vsrc, vcs_mv):
    # X from 3.50 V to 4.45 V; Y from -300 mV to +2100 mV so Red LED @ 4.4V stays cleanly inside plot box!
    x = px0 + (vsrc - 3.50) / 0.95 * (px1 - px0)
    y = py1 - (vcs_mv - (-300.0)) / 2400.0 * (py1 - py0)
    return (x, y)


for mv in range(-200, 2001, 200):
    _, yy = xy1(3.50, mv)
    d1.line((px0, yy, px1, yy), fill=(225, 228, 235), width=1)
    if mv % 400 == 200 or mv in (-200, 0, 400, 800, 1200, 1600, 2000):
        if mv in (-200, 0, 200, 400, 600, 800, 1200, 1600, 2000):
            d1.text((18, yy - 8), f"{mv:+d} mV", fill=(50, 50, 60), font=f_l)

for vv in [3.5, 3.6, 3.7, 3.8, 3.9, 4.0, 4.1, 4.2, 4.4]:
    xx, _ = xy1(vv, 0)
    d1.line((xx, py0, xx, py1), fill=(220, 224, 232), width=1)
    lbl = f"{vv:.1f}V" if vv < 4.3 else "4.4V (USB)"
    d1.text((xx - (34 if vv > 4.3 else 18), py1 + 10), lbl, fill=(45, 45, 55), font=f_l)

_, y300 = xy1(3.50, 300)
d1.line((px0, y300, px1, y300), fill=(210, 40, 40), width=2)
d1.text((px0 + 12, y300 - 19), "AW20198 CS Constant-Current Regulation Knee (~300 mV min V_CS)", fill=(200, 30, 30), font=f_b)

R_bat_to_vsys = r_bat_loop / 1000.0 + 0.112
R_vsys_u1 = path_dict["VSYS: U5.10 -> U1.5 (PVCC)"][0] / 1000.0
R_sw_worst = 0.43
R_cs_worst = 0.34
R_pmos = 1.04

curves = [
    ("Red LED on LiPo (VF=2.15V, GCC=107 wearable cap)", 2.15, 107 / 255.0, (215, 45, 45)),
    ("G/B LED typ on LiPo (VF=3.02V, GCC=107 wearable cap)", 3.02, 107 / 255.0, (25, 145, 75)),
    ("G/B LED typ on LiPo (VF=3.15V, GCC=216 300mA cap)", 3.15, 216 / 255.0, (30, 95, 205)),
    ("G/B LED max-bin on LiPo (VF=3.35V, GCC=216 300mA cap)", 3.35, 216 / 255.0, (145, 50, 185)),
]
for name, vf, scale_i, col in curves:
    pts = []
    i_pk = 0.01333 * scale_i
    i_sw = 15.0 * i_pk
    i_tot_bat = 0.048 + 0.3543 * scale_i
    i_u1 = 0.177 * scale_i
    for k in range(71):
        vcell = 3.50 + 0.01 * k
        vsys_u5 = vcell - i_tot_bat * R_bat_to_vsys
        vcs_mv = (vsys_u5 - i_u1 * R_vsys_u1 - i_sw * (R_pmos + R_sw_worst) - vf - i_pk * R_cs_worst) * 1000.0
        pts.append(xy1(vcell, vcs_mv))
    d1.line(pts, fill=col, width=3)
    vcs_usb_mv = (4.40 - i_u1 * R_vsys_u1 - i_sw * (R_pmos + R_sw_worst) - vf - i_pk * R_cs_worst) * 1000.0
    ux, uy = xy1(4.40, vcs_usb_mv)
    d1.ellipse((ux - 5, uy - 5, ux + 5, uy + 5), fill=col, outline=(20, 20, 25))

ly = py0 + 14
for name, _, _, col in curves:
    d1.line((px0 + 16, ly + 8, px0 + 46, ly + 8), fill=col, width=4)
    d1.text((px0 + 54, ly), name + "  [dot @ 4.4V USB]", fill=(25, 30, 40), font=f_l)
    ly += 22

d1.text((95, 18), "Sunflower s2-110-usbc — Worst-Case U1 LED Sink Headroom vs LiPo V_cell & USB 4.4 V", fill=(15, 25, 40), font=f_t)
d1.text(
    (95, 45),
    f"Includes full battery loop ({R_bat_to_vsys*1000:.0f} mOhm: PCB+BT1+U8+U5), VSYS->U1 ({R_vsys_u1*1000:.0f} mOhm), SW PMOS+trace @ 70 C (15.2 um inner Cu)",
    fill=(70, 80, 95),
    font=f_l,
)
d1.text((340, H - 32), "LiPo Cell Terminal Voltage V_cell (3.50 V .. 4.20 V)  |  USB Regulated VSYS (4.40 V)", fill=(30, 35, 45), font=f_b)
img1.save(OUT_DIR / "pdn_headroom.png")

# 6. Generate Plot 2: Steady-State Board Temperature vs AW20198 GCC (0..255)
img2 = Image.new("RGB", (W, H), (255, 255, 255))
d2 = ImageDraw.Draw(img2)
d2.rectangle((px0, py0, px1, py1), outline=(40, 40, 50), width=2, fill=(250, 251, 253))


def xy2(gcc, temp_c):
    x = px0 + (gcc / 255.0) * (px1 - px0)
    y = py1 - (temp_c - 20.0) / 85.0 * (py1 - py0)
    return (x, y)


for tc in range(20, 106, 10):
    _, yy = xy2(0, tc)
    d2.line((px0, yy, px1, yy), fill=(225, 228, 235), width=1)
    d2.text((36, yy - 8), f"{tc} °C", fill=(50, 50, 60), font=f_l)

for g in [0, 24, 64, 107, 128, 160, 192, 224, 255]:
    xx, _ = xy2(g, 20)
    d2.line((xx, py0, xx, py1), fill=(225, 228, 235), width=1)
    d2.text((xx - 12, py1 + 10), f"{g}", fill=(50, 50, 60), font=f_l)

limits = [
    (45.0, "45 °C — 403535 LiPo Max Charge Temp (U5 TS fixed via 10k R3 -> GCC<=9 CC / <=24 CV!)", (205, 110, 0), +4),
    (48.0, "48 °C — Wearable Skin-Contact Limit (cap GCC <= 107 on battery @ 25 °C amb)", (160, 95, 15), -18),
    (60.0, "60 °C — 403535 LiPo Max Discharge Temp", (215, 65, 20), -18),
    (70.0, "70 °C — SW1/SW2 (Panasonic EVQP7J01P) Max Operating Temp", (210, 25, 25), -18),
    (80.0, "80 °C — J1 (HRO TYPE-C-31-M-12) Max Operating Temp", (130, 20, 60), -18),
]
for tc, lbl, col, dy_lbl in limits:
    _, yy = xy2(0, tc)
    d2.line((px0, yy, px1, yy), fill=col, width=2)
    d2.text((px0 + 10, yy + dy_lbl), lbl, fill=col, font=f_b)

th_curves = [
    (25.0, 28.0, 0.00, 3.90, "Bare Bench PCB (no pouch) @ 25 °C Amb (R_th=28 K/W)", (90, 145, 215)),
    (25.0, 35.0, 0.00, 3.90, "Wearable Pouch Battery @ 25 °C Amb (R_th=35 K/W -> GCC<=107)", (20, 90, 195)),
    (25.0, 35.0, 0.36, 4.40, "USB CC Charge + White @ 25 °C Amb (R_th=35 K/W + 0.36W U5 -> GCC<=9)", (205, 40, 85)),
    (40.0, 35.0, 0.00, 3.90, "Hot 40 °C Ambient Battery Discharge (R_th=35 K/W -> GCC<=89)", (140, 45, 185)),
]
for tamb, rth, p_chg, vsys, name, col in th_curves:
    pts = []
    for g in range(256):
        p_heat = 0.16 + p_chg + 0.85 * (vsys * 0.3543 * (g / 255.0))
        pts.append(xy2(g, tamb + p_heat * rth))
    d2.line(pts, fill=col, width=3)

ly = py1 - 98
for _, _, _, _, name, col in th_curves:
    d2.line((px0 + 275, ly + 8, px0 + 305, ly + 8), fill=col, width=4)
    d2.text((px0 + 313, ly), name, fill=(25, 30, 40), font=f_l)
    ly += 21

d2.text((95, 18), "Sunflower s2-110-usbc — Steady-State Thermal Rise vs AW20198 Global Current (GCC)", fill=(15, 25, 40), font=f_t)
d2.text(
    (95, 45),
    "Pouch-backed R_th = 35 K/W, C_th ~= 2.6 J/K (tau_th ~= 91 s); gate charge cap on (PGOOD == 0 || CHG == 0)",
    fill=(70, 80, 95),
    font=f_l,
)
d2.text((400, H - 32), "AW20198 Global Current Control Register GCC (0..255)", fill=(30, 35, 45), font=f_b)
img2.save(OUT_DIR / "thermal_rise.png")
print("\nSaved design/sim/sunflower-s2-110-usbc/pdn_headroom.png and thermal_rise.png")
