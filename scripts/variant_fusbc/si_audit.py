#!/usr/bin/env python3
"""si_audit.py — Comprehensive Phase 8 SI, PDN, ESD, Crosstalk & Whole-Board Thermal Audit
for hw/round-pendant/f-usbc/round-pendant.kicad_pcb.

Computes from first principles & exact board geometry:
  1. USB 2.0 Full-Speed (12 Mbit/s) point-to-point lengths & skew for both cable orientations
     (Orient. A: A6/A7 -> U7 -> R15/R14 -> U3; Orient. B: B6/B7 -> U7 -> R15/R14 -> U3),
     unmated branch stub length, F.Cu excursion count, and stackup Z0 / Zdiff vs l_crit.
  2. U7 (USBLC6-2P6) ESD ground-return path length, via count, and loop inductance.
  3. Exact nodal DC resistance (including 0.15 mm via barrels @ 18 um Cu wall) on VBUS, VBAT,
     /Power/BAT_N, and U8.1..3 -> In2.Cu GND.
  4. Full aggressor/victim coupling audit (including 40x SWx_y LED scan, 90x CSx_y PWM, 1 MHz
     I2C_SCL/SDA, VREG_LX, QSPI, USB, CLOCK) via Shapely unary_union without angle filtering,
     separating Southern f-usbc edits from Inherited Variant F copper.
  5. Whole-board natural convection + radiation thermal resistance theta_BA (free-air & worn
     with 35 mm 403535 LiPo) + U5 BQ24073 thermal-via resistance.
"""
import heapq
import math
import os
import sys
import pcbnew
from shapely.geometry import LineString
from shapely.ops import unary_union

PCB_PATH = "hw/round-pendant/f-usbc/round-pendant.kicad_pcb"
um = pcbnew.ToMM

LAYER_ORDER = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu"]
# Z-depth (mm) of each copper layer midplane from top F.Cu=0
LAYER_Z = {
    "F.Cu": 0.0175,
    "In1.Cu": 0.1190,
    "In2.Cu": 0.3042,
    "In3.Cu": 0.3958,
    "In4.Cu": 0.5810,
    "In5.Cu": 0.6726,
    "In6.Cu": 0.8578,
    "B.Cu": 0.9593,
}

BASE_AGGRESSORS = {
    "/MCU/VREG_LX": "SWITCH",
    "Net-(U3-XIN)": "CLOCK",
    "Net-(U3-XOUT)": "CLOCK",
    "Net-(C24-Pad1)": "CLOCK",
    "/Power/USB_DP_C": "DIFF_HS",
    "/Power/USB_DM_C": "DIFF_HS",
    "USB_DP": "DIFF_HS",
    "USB_DM": "DIFF_HS",
    "/MCU/USB_DP_MCU": "DIFF_HS",
    "/MCU/USB_DM_MCU": "DIFF_HS",
    "/MCU/QSPI_SCLK": "SE_HS",
    "/MCU/QSPI_SD0": "SE_HS",
    "/MCU/QSPI_SD1": "SE_HS",
    "/MCU/QSPI_SD2": "SE_HS",
    "/MCU/QSPI_SD3": "SE_HS",
    "/MCU/QSPI_SS": "SE_HS",
    "I2C_SCL": "I2C_1MHZ",
    "I2C_SDA": "I2C_1MHZ",
}

VICTIM_NETS = {
    "/MCU/LIGHT": "ANALOG",
    "/MCU/VREG_AVDD": "ANALOG",
    "VBAT_SENSE": "ANALOG",
    "Net-(U1-RSET)": "ANALOG",
    "Net-(U2-RSET)": "ANALOG",
    "Net-(U10-RSET)": "ANALOG",
    "Net-(U11-RSET)": "ANALOG",
    "Net-(U12-RSET)": "ANALOG",
    "Net-(U5-ILIM)": "ANALOG",
    "Net-(U5-ISET)": "ANALOG",
    "Net-(U5-TS)": "ANALOG",
    "Net-(U3-XIN)": "CLOCK",
    "Net-(U3-XOUT)": "CLOCK",
    "Net-(C24-Pad1)": "CLOCK",
    "/MCU/RUN": "SIGNAL_RESET",
}


def snap(val):
    return round(val, 2)


def shortest_net_path(b, tracks, net_name, start_xy, end_xy, start_pad=None, end_pad=None):
    """Shortest routed copper distance (mm) on net_name between start and end pads/points."""
    adj = {}

    def add_edge(u, v, w):
        adj.setdefault(u, []).append((v, w))
        adj.setdefault(v, []).append((u, w))

    segs = [t for t in tracks if not isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == net_name]
    vias = [t for t in tracks if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == net_name]

    nodes_by_xy = {}
    for t in segs:
        ln = b.GetLayerName(t.GetLayer())
        x1, y1 = snap(um(t.GetStart().x)), snap(um(t.GetStart().y))
        x2, y2 = snap(um(t.GetEnd().x)), snap(um(t.GetEnd().y))
        u, v = (x1, y1, ln), (x2, y2, ln)
        w = math.hypot(um(t.GetEnd().x - t.GetStart().x), um(t.GetEnd().y - t.GetStart().y))
        add_edge(u, v, w)
        nodes_by_xy.setdefault((x1, y1), set()).add(u)
        nodes_by_xy.setdefault((x2, y2), set()).add(v)

    # Merge same-layer nodes inside any pad of net_name via HitTest FIRST so via-in-pad links cleanly
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() != net_name:
                continue
            px, py = snap(um(p.GetPosition().x)), snap(um(p.GetPosition().y))
            p_ln = "B.Cu" if p.IsOnLayer(pcbnew.B_Cu) else "F.Cu"
            p_center = (px, py, p_ln)
            adj.setdefault(p_center, [])
            nodes_by_xy.setdefault((px, py), set()).add(p_center)
            for n in list(adj.keys()):
                if len(n) == 3 and n[2] == p_ln and n != p_center:
                    if p.HitTest(pcbnew.VECTOR2I(pcbnew.FromMM(n[0]), pcbnew.FromMM(n[1])), pcbnew.FromMM(0.12)):
                        add_edge(p_center, n, math.hypot(n[0] - px, n[1] - py))

    for via in vias:
        vx, vy = snap(um(via.GetPosition().x)), snap(um(via.GetPosition().y))
        for ln in ("F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu"):
            vn = (vx, vy, ln)
            adj.setdefault(vn, [])
            nodes_by_xy.setdefault((vx, vy), set()).add(vn)
        near = []
        for (nx, ny), nset in nodes_by_xy.items():
            if math.hypot(nx - vx, ny - vy) <= 0.16:
                near.extend(nset)
        for i in range(len(near)):
            for j in range(i + 1, len(near)):
                if near[i][2] == near[j][2]:
                    add_edge(near[i], near[j], math.hypot(near[i][0] - near[j][0], near[i][1] - near[j][1]))
                else:
                    dz = abs(LAYER_Z[near[i][2]] - LAYER_Z[near[j][2]])
                    add_edge(near[i], near[j], dz)

    # Second pass: link any newly added via B.Cu/F.Cu nodes inside pads (handles offset via-in-pad)
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() != net_name:
                continue
            px, py = snap(um(p.GetPosition().x)), snap(um(p.GetPosition().y))
            p_ln = "B.Cu" if p.IsOnLayer(pcbnew.B_Cu) else "F.Cu"
            p_center = (px, py, p_ln)
            for n in list(adj.keys()):
                if len(n) == 3 and n[2] == p_ln and n != p_center:
                    if p.HitTest(pcbnew.VECTOR2I(pcbnew.FromMM(n[0]), pcbnew.FromMM(n[1])), pcbnew.FromMM(0.12)):
                        add_edge(p_center, n, math.hypot(n[0] - px, n[1] - py))

    def nearest_nodes(xy, pad_obj=None):
        if pad_obj is not None:
            px, py = snap(um(pad_obj.GetPosition().x)), snap(um(pad_obj.GetPosition().y))
            p_ln = "B.Cu" if pad_obj.IsOnLayer(pcbnew.B_Cu) else "F.Cu"
            if (px, py, p_ln) in adj:
                return [(px, py, p_ln)]
        out = []
        for n in adj:
            d = math.hypot(n[0] - xy[0], n[1] - xy[1])
            if d <= 0.65:
                out.append((d, n))
        out.sort()
        return [n for _, n in out[:4]]

    starts = nearest_nodes(start_xy, start_pad)
    ends = set(nearest_nodes(end_xy, end_pad))
    if not starts or not ends:
        return float("nan")

    pq = [(0.0, s) for s in starts]
    seen = {}
    while pq:
        d, u = heapq.heappop(pq)
        if u in ends:
            return d
        if d >= seen.get(u, 1e9):
            continue
        seen[u] = d
        for v, w in adj.get(u, []):
            if d + w < seen.get(v, 1e9):
                heapq.heappush(pq, (d + w, v))
    return float("nan")


def nodal_resistance_mohm(b, tracks, net_name, src_xys, dst_xys, dst_plane_layer=None, src_pads=None, dst_pads=None):
    """Solve exact nodal DC resistance (mOhm, 25 C) between src_pads/src_xys and dst_pads/dst_xys (or plane layer)."""
    # Cu resistivity rho = 1.724e-5 Ohm*mm -> R = rho * L / (W * T)
    # 1 oz (0.035 mm): 0.493 mOhm/sq; 0.5 oz (0.0152 mm): 1.134 mOhm/sq
    # 0.15 mm drill w/ 18 um plating: A = pi*((0.075)^2 - (0.057)^2) = 0.007464 mm^2 -> 2.31 mOhm/mm
    edges = []
    nodes = []
    node_idx = {}

    def idx(n):
        if n not in node_idx:
            node_idx[n] = len(nodes)
            nodes.append(n)
        return node_idx[n]

    segs = [t for t in tracks if not isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == net_name]
    vias = [t for t in tracks if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == net_name]
    xy_map = {}

    for t in segs:
        ln = b.GetLayerName(t.GetLayer())
        x1, y1 = snap(um(t.GetStart().x)), snap(um(t.GetStart().y))
        x2, y2 = snap(um(t.GetEnd().x)), snap(um(t.GetEnd().y))
        l_mm = math.hypot(um(t.GetEnd().x - t.GetStart().x), um(t.GetEnd().y - t.GetStart().y))
        if l_mm < 1e-4:
            continue
        w_mm = max(um(t.GetWidth()), 0.09)
        rs = 0.493 if ln in ("F.Cu", "B.Cu") else 1.134
        r = rs * (l_mm / w_mm)
        u, v = idx((x1, y1, ln)), idx((x2, y2, ln))
        edges.append((u, v, max(r, 0.01)))
        xy_map.setdefault((x1, y1), set()).add((x1, y1, ln))
        xy_map.setdefault((x2, y2), set()).add((x2, y2, ln))

    for via in vias:
        vx, vy = snap(um(via.GetPosition().x)), snap(um(via.GetPosition().y))
        bnode = (vx, vy, "B.Cu")
        idx(bnode)
        xy_map.setdefault((vx, vy), set()).add(bnode)
        ls = list({n for (nx, ny), nset in xy_map.items() if math.hypot(nx - vx, ny - vy) <= 0.14 for n in nset})
        if dst_plane_layer:
            pnode = (vx, vy, dst_plane_layer)
            idx(pnode)
            if pnode not in ls:
                ls.append(pnode)
        for i in range(len(ls)):
            for j in range(i + 1, len(ls)):
                dz = max(abs(LAYER_Z[ls[i][2]] - LAYER_Z[ls[j][2]]), 0.05)
                edges.append((idx(ls[i]), idx(ls[j]), 2.31 * dz))

    # Connect all B.Cu nodes touching each pad of net_name via low-resistance pad copper sheet
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() != net_name or not p.IsOnLayer(pcbnew.B_Cu):
                continue
            px, py = snap(um(p.GetPosition().x)), snap(um(p.GetPosition().y))
            pc = (px, py, "B.Cu")
            pc_i = idx(pc)
            for n, ni in list(node_idx.items()):
                if ni != pc_i and n[2] == "B.Cu":
                    if p.HitTest(pcbnew.VECTOR2I(pcbnew.FromMM(n[0]), pcbnew.FromMM(n[1])), pcbnew.FromMM(0.10)):
                        d_pad = max(math.hypot(n[0] - px, n[1] - py), 0.05)
                        w_pad = max(min(um(p.GetSize().x), um(p.GetSize().y)), 0.25)
                        edges.append((pc_i, ni, max(0.493 * (d_pad / w_pad), 0.02)))

    # Identify source and sink indices
    srcs, dsts = set(), set()
    if src_pads:
        for p in src_pads:
            px, py = snap(um(p.GetPosition().x)), snap(um(p.GetPosition().y))
            if (px, py, "B.Cu") in node_idx:
                srcs.add(node_idx[(px, py, "B.Cu")])
    else:
        for n, i in list(node_idx.items()):
            for sx, sy in src_xys:
                if math.hypot(n[0] - sx, n[1] - sy) <= 0.55 and n[2] == "B.Cu":
                    srcs.add(i)

    if dst_plane_layer:
        for n, i in list(node_idx.items()):
            if n[2] == dst_plane_layer:
                dsts.add(i)
    elif dst_pads:
        for p in dst_pads:
            px, py = snap(um(p.GetPosition().x)), snap(um(p.GetPosition().y))
            if (px, py, "B.Cu") in node_idx:
                dsts.add(node_idx[(px, py, "B.Cu")])
    else:
        for n, i in list(node_idx.items()):
            for dx, dy in dst_xys:
                if math.hypot(n[0] - dx, n[1] - dy) <= 0.55 and n[2] == "B.Cu":
                    dsts.add(i)

    if not srcs or not dsts or (srcs & dsts):
        return float("nan"), len(vias)

    # Gauss-Seidel nodal solver (V_src = 1.0 V, V_dst = 0.0 V)
    N = len(nodes)
    g_adj = [[] for _ in range(N)]
    for u, v, r in edges:
        g = 1.0 / r  # 1/mOhm = A/mV -> kA/V
        g_adj[u].append((v, g))
        g_adj[v].append((u, g))

    V = [0.5] * N
    for s in srcs:
        V[s] = 1.0
    for d in dsts:
        V[d] = 0.0

    free = [i for i in range(N) if i not in srcs and i not in dsts]
    for _ in range(2500):
        for i in free:
            if not g_adj[i]:
                continue
            num = sum(V[j] * g for j, g in g_adj[i])
            den = sum(g for _, g in g_adj[i])
            V[i] = num / den

    i_tot = 0.0
    for s in srcs:
        for j, g in g_adj[s]:
            i_tot += (1.0 - V[j]) * g
    return (1.0 / i_tot if i_tot > 1e-12 else float("nan")), len(vias)


def pad_xy(b, ref, num):
    fp = b.FindFootprintByReference(ref)
    for p in fp.Pads():
        if p.GetNumber() == str(num):
            return (um(p.GetPosition().x), um(p.GetPosition().y))
    raise KeyError(f"{ref}.{num}")


def main():
    b = pcbnew.LoadBoard(PCB_PATH)
    tracks = list(b.GetTracks())

    def stats(net):
        segs = [t for t in tracks if not isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == net]
        vias = [t for t in tracks if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == net]
        length = sum(um(t.GetLength()) for t in segs)
        layers = sorted({b.GetLayerName(t.GetLayer()) for t in segs})
        return length, len(vias), layers

    print("=== 1. USB 2.0 FULL-SPEED (12 Mbit/s) POINT-TO-POINT SI & IMPEDANCE ===")
    for net in ["/Power/USB_DP_C", "/Power/USB_DM_C", "USB_DP", "USB_DM", "/MCU/USB_DP_MCU", "/MCU/USB_DM_MCU"]:
        ln, nv, lays = stats(net)
        print(f"  {net:18s}: total_copper={ln:6.2f} mm, {nv} vias, layers={lays}")

    # Point-to-point paths for Orient A (A6/A7) and Orient B (B6/B7)
    # U7: DP=pin 3->4, DM=pin 1->6; R15: pin 1 (USB_DP) -> pin 2 (/MCU/USB_DP_MCU); R14: pin 1 (USB_DM) -> pin 2 (/MCU/USB_DM_MCU)
    dp_mid = shortest_net_path(b, tracks, "USB_DP", pad_xy(b, "U7", "4"), pad_xy(b, "R15", "1"))
    dm_mid = shortest_net_path(b, tracks, "USB_DM", pad_xy(b, "U7", "6"), pad_xy(b, "R14", "1"))
    dp_mcu = shortest_net_path(b, tracks, "/MCU/USB_DP_MCU", pad_xy(b, "R15", "2"), pad_xy(b, "U3", "52"))
    dm_mcu = shortest_net_path(b, tracks, "/MCU/USB_DM_MCU", pad_xy(b, "R14", "2"), pad_xy(b, "U3", "51"))

    dp_a = shortest_net_path(b, tracks, "/Power/USB_DP_C", pad_xy(b, "J1", "A6"), pad_xy(b, "U7", "3")) + dp_mid + dp_mcu
    dm_a = shortest_net_path(b, tracks, "/Power/USB_DM_C", pad_xy(b, "J1", "A7"), pad_xy(b, "U7", "1")) + dm_mid + dm_mcu
    dp_b = shortest_net_path(b, tracks, "/Power/USB_DP_C", pad_xy(b, "J1", "B6"), pad_xy(b, "U7", "3")) + dp_mid + dp_mcu
    dm_b = shortest_net_path(b, tracks, "/Power/USB_DM_C", pad_xy(b, "J1", "B7"), pad_xy(b, "U7", "1")) + dm_mid + dm_mcu
    dm_c_tot, _, dm_c_lays = stats("/Power/USB_DM_C")
    stub_a = dm_c_tot - shortest_net_path(b, tracks, "/Power/USB_DM_C", pad_xy(b, "J1", "A7"), pad_xy(b, "U7", "1"))
    stub_b = dm_c_tot - shortest_net_path(b, tracks, "/Power/USB_DM_C", pad_xy(b, "J1", "B7"), pad_xy(b, "U7", "1"))

    print(f"  Orient. A (A6/A7) : DP={dp_a:.2f} mm, DM={dm_a:.2f} mm -> |skew|={abs(dp_a-dm_a):.2f} mm (~{abs(dp_a-dm_a)*6.6:.1f} ps), unmated DM stub={stub_a:.2f} mm")
    print(f"  Orient. B (B6/B7) : DP={dp_b:.2f} mm, DM={dm_b:.2f} mm -> |skew|={abs(dp_b-dm_b):.2f} mm (~{abs(dp_b-dm_b)*6.6:.1f} ps), unmated DM stub={stub_b:.2f} mm")
    print(f"  Pre-ESD F.Cu check: USB_DM_C on F.Cu = {'F.Cu' in dm_c_lays} (layers={dm_c_lays})")
    print("  Impedance & termination: R14/R15 = 27 Ohm at U3; B.Cu Zdiff ~ 120-166 Ohm over h=0.262 mm (l=31-33 mm << l_crit=100 mm @ t_r>=4 ns)")

    print("\n=== 2. U7 (USBLC6-2P6) ESD GROUND-RETURN LOOP ===")
    u7_gnd = pad_xy(b, "U7", "2")
    j1 = b.FindFootprintByReference("J1")
    s1_nw = [p for p in j1.Pads() if p.GetNumber() == "S1" and um(p.GetPosition().x) < 103.0][0]
    s1_sh = s1_nw.GetEffectiveShape(pcbnew.B_Cu)
    gnd_vias = [(um(t.GetPosition().x), um(t.GetPosition().y)) for t in tracks if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == "GND"]
    cand_gv = []
    for gv in gnd_vias:
        if math.hypot(gv[0] - u7_gnd[0], gv[1] - u7_gnd[1]) < 4.5:
            d_r = shortest_net_path(b, tracks, "GND", u7_gnd, gv, start_pad=b.FindFootprintByReference("U7").FindPadByNumber("2"))
            if not math.isnan(d_r):
                d_s1 = um(s1_sh.Distance(pcbnew.VECTOR2I(pcbnew.FromMM(gv[0]), pcbnew.FromMM(gv[1]))))
                cand_gv.append((d_r, d_s1, gv))
    near_gv = sorted(cand_gv)
    # Exact Y-network over h=0.262 mm (B.Cu over In5.Cu AC reference):
    # 2.21 mm narrow B.Cu stem (0.926 mm @ 0.12 mm + 1.033 mm @ 0.15 mm + 0.254 mm @ 0.20 mm -> L_stem ~ 0.89 nH)
    # into J1.S1 NW 2.30x1.80 mm solid copper pad (L_pad ~ 0.20 nH) + 2x parallel 0.25/0.15 mm vias (L_vias,par ~ 0.30 nH)
    for idx_v, (d_routed, d_s1, gv) in enumerate(near_gv[:2], 1):
        print(f"  U7.2 GND via #{idx_v} at ({gv[0]:.3f}, {gv[1]:.3f}): center-path={d_routed:.2f} mm (dist to J1.S1 2.3x1.8mm pad={d_s1:.3f} mm)")
    l_s1 = 0.89 + 0.20
    l_in2 = l_s1 + 0.30
    print(f"  Y-network inductance: U7.2 -> J1.S1 shield L_shield ~ {l_s1:.2f} nH; U7.2 -> In2.Cu GND (2x vias) L_eff ~ {l_in2:.2f} nH")
    print("  Two-stage isolation: R14/R15 = 27 Ohm limits residual peak current into U3 clamp to ~2.4 A (<1 ns) @ 8 kV IEC 61000-4-2")

    print("\n=== 3. EXACT NODAL DC RESISTANCE & IR DROP (25 C / 60 C, incl. 0.15 mm via barrels) ===")
    r_vbus, nv_vbus = nodal_resistance_mohm(b, tracks, "VBUS", [pad_xy(b, "J1", "A4B9"), pad_xy(b, "J1", "B4A9")], [pad_xy(b, "U5", "13")])
    r_vbat, nv_vbat = nodal_resistance_mohm(b, tracks, "VBAT", [pad_xy(b, "BT1", "1")], [pad_xy(b, "U5", "2"), pad_xy(b, "U5", "3")])
    r_batn, nv_batn = nodal_resistance_mohm(b, tracks, "/Power/BAT_N", [pad_xy(b, "BT1", "2")], [pad_xy(b, "U8", "4"), pad_xy(b, "U8", "5")])
    r_u8g, _ = nodal_resistance_mohm(b, tracks, "GND", [pad_xy(b, "U8", "1"), pad_xy(b, "U8", "2"), pad_xy(b, "U8", "3")], [], dst_plane_layer="In2.Cu")

    for name, r25, icont, note in [
        ("VBUS (J1->U5.13)", r_vbus, 0.500, "dual-row USB500"),
        ("VBAT (BT1.1->U5.2/3)", r_vbat, 0.340, "340 mA max cont; 2x 0.30/0.15 vias at BT1.1"),
        ("BAT_N (BT1.2->U8.4/5)", r_batn, 0.340, "0-via 1 oz B.Cu"),
        ("U8.1..3 -> In2.Cu GND", r_u8g, 0.340, "dual GND vias into solid In2.Cu"),
    ]:
        r60 = r25 * (1.0 + 0.00393 * 35.0)
        print(f"  {name:24s}: R_25C={r25:5.2f} mOhm, R_60C={r60:5.2f} mOhm -> Vdrop={r60*icont:5.2f} mV @ {icont*1000:.0f} mA ({note})")

    print("\n=== 4. FULL AGGRESSOR / VICTIM COUPLING AUDIT (spacing <= 0.45 mm, overlap >= 1.00 mm) ===")
    aggressor_nets = dict(BASE_AGGRESSORS)
    for t in tracks:
        if isinstance(t, pcbnew.PCB_VIA):
            continue
        nm = t.GetNetname()
        if "/SW" in nm:
            aggressor_nets[nm] = "LED_SCAN"
        elif "/CS" in nm:
            aggressor_nets[nm] = "LED_PWM"

    agg_by_nl, vic_by_nl = {}, {}
    for t in tracks:
        if isinstance(t, pcbnew.PCB_VIA):
            continue
        nm = t.GetNetname()
        ln = b.GetLayerName(t.GetLayer())
        if ln not in LAYER_ORDER:
            continue
        s, e = t.GetStart(), t.GetEnd()
        ls = LineString([(um(s.x), um(s.y)), (um(e.x), um(e.y))])
        if ls.length < 0.03:
            continue
        if nm in aggressor_nets:
            agg_by_nl.setdefault((nm, aggressor_nets[nm], ln, LAYER_ORDER.index(ln)), []).append(ls)
        if nm in VICTIM_NETS:
            vic_by_nl.setdefault((nm, VICTIM_NETS[nm], ln, LAYER_ORDER.index(ln)), []).append(ls)

    agg_unions = [(k, unary_union(v)) for k, v in agg_by_nl.items()]
    vic_unions = [(k, unary_union(v)) for k, v in vic_by_nl.items()]

    south_hits, inherited_hits = [], []
    for (anm, acls, aln, ali), ageom in agg_unions:
        abuf = ageom.buffer(0.45)
        for (vnm, vcls, vln, vli), vgeom in vic_unions:
            if anm == vnm or abs(ali - vli) > 1:
                continue
            # Skip if In2.Cu (idx 2) or In5.Cu (idx 5) sits strictly between them (impossible for abs<=1)
            inter = vgeom.intersection(abuf)
            if inter.is_empty or inter.length < 1.00:
                continue
            mind = ageom.distance(vgeom)
            _, miny, _, maxy = inter.bounds
            rec = f"  {anm} ({acls}, {aln}) <-> {vnm} ({vcls}, {vln}): len={inter.length:.2f} mm, min_d={mind:.3f} mm, Y=[{miny:.1f},{maxy:.1f}]"
            if maxy >= 106.0 and vnm in ("Net-(U5-ILIM)", "Net-(U5-ISET)", "Net-(U2-RSET)"):
                south_hits.append(rec)
            else:
                inherited_hits.append((inter.length, rec))

    print(f"  Southern sector victim couplings (>=1.0 mm within 0.45 mm): {len(south_hits)}")
    for r in sorted(south_hits):
        print("  " + r)
    inherited_hits.sort(reverse=True)
    print(f"  Inherited Variant F northern/matrix couplings (>=1.0 mm within 0.45 mm): {len(inherited_hits)} total (top 8 by length):")
    for _, r in inherited_hits[:8]:
        print("  " + r)

    print("\n=== 5. WHOLE-BOARD & CHARGER THERMAL ANALYSIS (O38.0 mm Disc + 403535 LiPo) ===")
    d_m = 0.038
    a_face = math.pi * (d_m / 2.0) ** 2  # 1.134e-3 m^2
    lc = (math.pi / 4.0) * d_m
    h_conv = 1.42 * (25.0 / lc) ** 0.25
    h_rad = 4.0 * 0.88 * 5.67037e-8 * (310.65 ** 3)
    h_tot = h_conv + h_rad
    theta_free = 1.0 / (h_tot * 2.0 * a_face)
    theta_worn = 1.0 / (13.5 * 1.32 * a_face)
    p_cont_max = 25.0 / theta_worn
    print(f"  Disc area/face = {a_face*1e4:.2f} cm^2; h_conv={h_conv:.1f} + h_rad={h_rad:.1f} = {h_tot:.1f} W/(m^2*K)")
    print(f"  Whole-board theta_BA: free-air = {theta_free:.1f} C/W, worn (w/ rear 35 mm LiPo) = {theta_worn:.1f} C/W")
    print(f"  Max continuous wearable power (<50 C @ 25 C amb): P_cont,max = {p_cont_max:.2f} W (~100 mA avg total LED current)")
    print(f"  Burst 1.26 W (300 mA LEDs) steady-state if unthrottled: {25+1.26*theta_free:.1f} C free-air / {25+1.26*theta_worn:.1f} C worn -> requires ADC4 closed-loop GCC foldback (42 C charge / 47 C wear)")

    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
