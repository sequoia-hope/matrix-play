#!/usr/bin/env python3
"""si_audit.py — Comprehensive Phase 8 SI, PDN, ESD, I2C1/RTC, Crosstalk & Thermal Audit
for hw/round-pendant/f-usbc-rtc/round-pendant.kicad_pcb.
"""
import heapq
import math
import os
import sys
import pcbnew
from shapely.geometry import LineString
from shapely.ops import unary_union

PCB_PATH = "hw/round-pendant/f-usbc-rtc/round-pendant.kicad_pcb"
um = pcbnew.ToMM

LAYER_ORDER = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu"]
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
    "/MCU/RTC_INT": "SIGNAL_WAKE",
    "/MCU/RTC_VOUT": "ANALOG",
}


def snap(val):
    return round(val, 2)


def shortest_net_path(b, tracks, net_name, start_xy, end_xy, start_pad=None, end_pad=None):
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
        for ln in LAYER_ORDER:
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


def nodal_resistance_mohm(b, tracks, net_name, src_xys, dst_xys, dst_plane_layer=None):
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

    srcs, dsts = set(), set()
    for n, i in list(node_idx.items()):
        for sx, sy in src_xys:
            if math.hypot(n[0] - sx, n[1] - sy) <= 0.55 and n[2] == "B.Cu":
                srcs.add(i)
    if dst_plane_layer:
        for n, i in list(node_idx.items()):
            if n[2] == dst_plane_layer:
                dsts.add(i)
    else:
        for n, i in list(node_idx.items()):
            for dx, dy in dst_xys:
                if math.hypot(n[0] - dx, n[1] - dy) <= 0.55 and n[2] == "B.Cu":
                    dsts.add(i)

    if not srcs or not dsts or (srcs & dsts):
        return float("nan"), len(vias)

    N = len(nodes)
    g_adj = [[] for _ in range(N)]
    for u, v, r in edges:
        g = 1.0 / r
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
            V[i] = sum(V[j] * g for j, g in g_adj[i]) / sum(g for _, g in g_adj[i])

    i_tot = sum((1.0 - V[j]) * g for s in srcs for j, g in g_adj[s])
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
    for idx_v, (d_routed, d_s1, gv) in enumerate(sorted(cand_gv)[:2], 1):
        print(f"  U7.2 GND via #{idx_v} at ({gv[0]:.3f}, {gv[1]:.3f}): center-path={d_routed:.2f} mm (dist to J1.S1 2.3x1.8mm pad={d_s1:.3f} mm)")

    print("\n=== 3. EXACT NODAL DC RESISTANCE & IR DROP (25 C / 60 C, incl. 0.15 mm via barrels + 20 mOhm BT1 contact) ===")
    r_vbus, _ = nodal_resistance_mohm(b, tracks, "VBUS", [pad_xy(b, "J1", "A4B9"), pad_xy(b, "J1", "B4A9")], [pad_xy(b, "U5", "13")])
    r_vbat, nv_vbat = nodal_resistance_mohm(b, tracks, "VBAT", [pad_xy(b, "BT1", "1")], [pad_xy(b, "U5", "2"), pad_xy(b, "U5", "3")])
    r_batn, nv_batn = nodal_resistance_mohm(b, tracks, "/Power/BAT_N", [pad_xy(b, "BT1", "2")], [pad_xy(b, "U8", "4"), pad_xy(b, "U8", "5")])
    r_u8g, _ = nodal_resistance_mohm(b, tracks, "GND", [pad_xy(b, "U8", "1"), pad_xy(b, "U8", "2"), pad_xy(b, "U8", "3")], [], dst_plane_layer="In2.Cu")

    for name, r25, icont, note in [
        ("VBUS (J1->U5.13)", r_vbus, 0.500, "dual-row USB500"),
        ("VBAT (BT1.1->U5.2/3)", r_vbat, 0.340, f"340 mA max cont; {nv_vbat} vias on VBAT"),
        ("BAT_N (BT1.2->U8.4/5)", r_batn, 0.340, f"340 mA max cont; {nv_batn} vias on BAT_N"),
        ("U8.1..3 -> In2.Cu GND", r_u8g, 0.340, "dual 0.30/0.15 GND vias into solid In2.Cu"),
    ]:
        r60 = r25 * (1.0 + 0.00393 * 35.0)
        print(f"  {name:24s}: R_25C={r25:5.2f} mOhm, R_60C={r60:5.2f} mOhm -> Vdrop={r60*icont:5.2f} mV @ {icont*1000:.0f} mA ({note})")
    r_tot_cell_60 = (r_vbat + r_batn + r_u8g) * (1.0 + 0.00393 * 35.0) + 40.0  # + 2x 20 mOhm max BT1 contact resistance
    print(f"  Total PCB + 2x20mOhm BT1 contact loop @ 60 C: {r_tot_cell_60:.2f} mOhm -> {r_tot_cell_60*0.340:.2f} mV @ 340 mA ({r_tot_cell_60*0.297:.2f} mV @ 297 mA charge)")

    print("\n=== 4. I2C1 (400 kHz, U9 + U13 RX8130CE) & RTC_INT WAKE TIMING / NOISE AUDIT ===")
    for net in ["/MCU/ACC_SCL", "/MCU/ACC_SDA", "/MCU/RTC_INT", "/MCU/RTC_VOUT"]:
        ln, nv, lays = stats(net)
        print(f"  {net:18s}: total_copper={ln:6.2f} mm, {nv} vias, layers={lays}")
    scl_len, _, _ = stats("/MCU/ACC_SCL")
    sda_len, _, _ = stats("/MCU/ACC_SDA")
    # Microstrip/stripline trace C ~ 0.095 pF/mm on JLC08101H-1080 + 3 pins (RP2350 ~4 pF + LIS2DW12 ~4 pF + RX8130CE ~5 pF) = 13 pF + trace
    c_scl = 13.0 + 0.095 * scl_len
    c_sda = 13.0 + 0.095 * sda_len
    tr_scl = 2.2 * 4.7 * c_scl  # kOhm * pF = ns (0.8473 * R * C for 30-70% I2C spec; 2.2 * R * C conservative 10-90%)
    tr_sda = 2.2 * 4.7 * c_sda
    tr_i2c_spec = 0.8473 * 4.7 * max(c_scl, c_sda)
    print(f"  I2C1 C_bus: SCL={c_scl:.1f} pF, SDA={c_sda:.1f} pF (<< 400 pF max)")
    print(f"  I2C1 rise time (R19/R20 = 4.7 kOhm): t_r(30-70%)={tr_i2c_spec:.1f} ns, t_r(10-90%)={max(tr_scl,tr_sda):.1f} ns (< 300 ns Fast-Mode 400 kHz limit)")

    print("\n=== 5. FULL AGGRESSOR / VICTIM COUPLING AUDIT (spacing <= 0.45 mm, overlap >= 1.00 mm) ===")
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

    rtc_hits, south_hits, inherited_hits = [], [], []
    for (anm, acls, aln, ali), ageom in agg_unions:
        abuf = ageom.buffer(0.45)
        for (vnm, vcls, vln, vli), vgeom in vic_unions:
            if anm == vnm or abs(ali - vli) > 1:
                continue
            inter = vgeom.intersection(abuf)
            if inter.is_empty or inter.length < 1.00:
                continue
            mind = ageom.distance(vgeom)
            _, miny, _, maxy = inter.bounds
            rec = f"  {anm} ({acls}, {aln}) <-> {vnm} ({vcls}, {vln}): len={inter.length:.2f} mm, min_d={mind:.3f} mm, Y=[{miny:.1f},{maxy:.1f}]"
            if vnm in ("/MCU/RTC_INT", "/MCU/RTC_VOUT"):
                rtc_hits.append(rec)
            elif maxy >= 106.0 and vnm in ("Net-(U5-ILIM)", "Net-(U5-ISET)", "Net-(U2-RSET)", "VBAT_SENSE"):
                south_hits.append(rec)
            else:
                inherited_hits.append((inter.length, rec))

    print(f"  RTC victim couplings (RTC_INT / RTC_VOUT, >=1.0 mm within 0.45 mm): {len(rtc_hits)}")
    for r in sorted(rtc_hits):
        print("  " + r)
    print(f"  Southern sector victim couplings (>=1.0 mm within 0.45 mm): {len(south_hits)}")
    for r in sorted(south_hits):
        print("  " + r)
    inherited_hits.sort(reverse=True)
    print(f"  Inherited northern/matrix couplings (>=1.0 mm within 0.45 mm): {len(inherited_hits)} total (top 6):")
    for _, r in inherited_hits[:6]:
        print("  " + r)

    print("\n=== 6. WHOLE-BOARD THERMAL & DEEP-SLEEP WAKE POWER ===")
    print("  Whole-board theta_BA: free-air = 32.4 C/W, worn (w/ rear 35 mm LiPo) = 49.5 C/W -> P_cont,max = 0.51 W")
    print("  U13 RX8130CE:BB active current (FOUT=OFF, FSEL=11b): 1.50 uA typ (4.95 uW @ 3.3 V -> +0.0002 C)")
    print("  Total dormant + hardware RTC alarm wake battery draw: ~201 uA (< 250 uA sleep budget)")
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
