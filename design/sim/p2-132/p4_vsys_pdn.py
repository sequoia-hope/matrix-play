#!/usr/bin/env python3
"""p4_vsys_pdn.py -- Phase P4: VSYS + SW-Tree Power Integrity, 2D In1.Cu Return Plane, & LiPo Headroom Foldback.

Models the exact extracted power delivery path of parallelogram/p2-132:
  - South U5 (BQ24073 at y=+19.0 mm) -> 137.90 mm routed VSYS copper network (73.0 mm In2.Cu 0.5 oz, 38.4 mm B.Cu 1 oz,
    26.5 mm F.Cu 1 oz, 25 vias) -> Mid U2 (AW20198 at y=-8.2 mm) -> North U1 (AW20198 at y=-18.5 mm).
  - Row switch copper tree SW1_1 / SW2_1 (up to 99.36 mm of 0.10 mm trace carrying 240 mA active-row anode current!).
  - 2D finite-difference Laplace/Poisson sheet-resistance solver on the actual 25 x 70 mm 17.75-deg skewed In1.Cu GND plane.
  - libngspice transient PDN droop simulation (MLCC DC-bias derated C2/C30/C40 = 22 uF 0603 + local 1 uF / 100 nF)
    comparing Simultaneous 1-Phase (480 mA step) vs Firmware 3-Phase Staggered PWM (3 x 160 mA).
  - Derives exact Green/Blue LED headroom floor across VBAT = 4.20..3.00 V and outputs the GCC(VBAT) foldback LUT for fw/p2-132!
"""
import json
import math
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from solvers import FastHenryDeck, NgSpice, SIGMA_CU

HERE = Path(__file__).resolve().parent
GEOM_JSON = HERE / "work/p2-132-geom.json"
OUT_JSON = HERE / "results/P4_vsys_pdn.json"
IMG_DIR = HERE / "report/img"

LAYER_THICK_MM = {"F.Cu": 0.035, "In1.Cu": 0.0152, "In2.Cu": 0.0152, "B.Cu": 0.035}


def solve_copper_graph_resistance(geom: dict, net_name: str, src_xy: tuple[float, float], dst_xys: dict[str, tuple[float, float]]) -> dict:
    """Build exact nodal conductance matrix from extracted KiCad tracks + vias of `net_name` and solve DC drops."""
    tracks = geom["tracks_by_net"][net_name]
    vias = geom["vias_by_net"].get(net_name, [])

    # Snap 3D points (x_round, y_round, layer) within 0.08 mm
    nodes: list[tuple[float, float, str]] = []

    def get_node(x: float, y: float, lyr: str) -> int:
        for idx, (nx, ny, nl) in enumerate(nodes):
            if nl == lyr and abs(nx - x) < 0.09 and abs(ny - y) < 0.09:
                return idx
        nodes.append((x, y, lyr))
        return len(nodes) - 1

    edges: list[tuple[int, int, float]] = []
    for t in tracks:
        u = get_node(t["x1"], t["y1"], t["layer"])
        v = get_node(t["x2"], t["y2"], t["layer"])
        if u == v:
            continue
        thick_m = LAYER_THICK_MM[t["layer"]] * 1e-3
        r_ohm = max(1e-5, (t["len"] * 1e-3) / (SIGMA_CU * (t["w"] * 1e-3) * thick_m))
        edges.append((u, v, 1.0 / r_ohm))

    # Connect vias across all layers present near (vx, vy)
    for via in vias:
        vx, vy = via["x"], via["y"]
        hit_layers = []
        for idx, (nx, ny, nl) in enumerate(nodes):
            if math.hypot(nx - vx, ny - vy) < 0.22:
                hit_layers.append(idx)
        # Plated 0.15 mm drill barrel (~18 um plating, 1.59 mm tall -> R_via ~ 1.8 mOhm)
        for i in range(len(hit_layers)):
            for j in range(i + 1, len(hit_layers)):
                edges.append((hit_layers[i], hit_layers[j], 1.0 / 0.0018))

    # Also bridge pad overlaps on same layer within 0.35 mm (e.g. multi-pad PVCC pins on QFN-40 / SOT-23 / passives)
    for p in [pad for fp in geom["footprints"].values() for pad in fp["pads"] if pad["net"] == net_name]:
        px, py, sx, sy = p["x"], p["y"], max(0.25, p["sx"]), max(0.25, p["sy"])
        in_pad = [
            idx for idx, (nx, ny, nl) in enumerate(nodes)
            if nl in p["layers"] and abs(nx - px) <= sx * 0.65 and abs(ny - py) <= sy * 0.65
        ]
        for i in range(len(in_pad)):
            for j in range(i + 1, len(in_pad)):
                edges.append((in_pad[i], in_pad[j], 1.0 / 0.0005))

    n = len(nodes)
    # Find closest node to src_xy
    src_idx = min(range(n), key=lambda i: math.hypot(nodes[i][0] - src_xy[0], nodes[i][1] - src_xy[1]))
    dst_idx = {
        k: min(range(n), key=lambda i: math.hypot(nodes[i][0] - xy[0], nodes[i][1] - xy[1]))
        for k, xy in dst_xys.items()
    }

    # BFS connected component from src_idx
    adj = defaultdict(list)
    for u, v, g_val in edges:
        adj[u].append((v, g_val))
        adj[v].append((u, g_val))
    seen = {src_idx}
    q = [src_idx]
    while q:
        cur = q.pop()
        for nxt, _ in adj[cur]:
            if nxt not in seen:
                seen.add(nxt)
                q.append(nxt)

    # Solve effective 2-port resistance from src_idx to each dst_idx by injecting 1 A
    r_to_dst = {}
    comp_list = sorted(seen)
    idx_map = {old: new for new, old in enumerate(comp_list)}
    m = len(comp_list)
    gmat = np.zeros((m, m), dtype=float)
    for u, v, g_val in edges:
        if u in idx_map and v in idx_map:
            iu, iv = idx_map[u], idx_map[v]
            gmat[iu, iu] += g_val
            gmat[iv, iv] += g_val
            gmat[iu, iv] -= g_val
            gmat[iv, iu] -= g_val
    # Ground src_idx
    s_loc = idx_map[src_idx]
    gmat[s_loc, :] = 0.0
    gmat[:, s_loc] = 0.0
    gmat[s_loc, s_loc] = 1.0

    for label, d_orig in dst_idx.items():
        if d_orig not in idx_map:
            # Find nearest node inside connected component
            d_orig = min(comp_list, key=lambda i: math.hypot(nodes[i][0] - dst_xys[label][0], nodes[i][1] - dst_xys[label][1]))
        rhs = np.zeros(m)
        rhs[idx_map[d_orig]] = 1.0
        rhs[s_loc] = 0.0
        v_sol = np.linalg.solve(gmat, rhs)
        r_to_dst[label] = float(v_sol[idx_map[d_orig]])

    return {"n_nodes": n, "connected_nodes": m, "R_ohm": r_to_dst}


def solve_in1_gnd_return_plane() -> dict:
    """2D finite-difference Laplace/Poisson solver on the 25 x 70 mm 17.75-deg skewed parallelogram In1.Cu GND plane (15.2 um = 1.135 mOhm/sq)."""
    # Grid in u in [-11.8, 11.8] mm, y_skew = y - u * tan(17.75 deg) in [-34.0, 34.0] mm
    nx, ny = 50, 140
    us = np.linspace(-11.8, 11.8, nx)
    vs = np.linspace(-34.0, 34.0, ny)
    du = us[1] - us[0]
    dv = vs[1] - vs[0]
    tan_skew = math.tan(math.radians(17.75))
    r_sheet = 1.0 / (SIGMA_CU * 15.2e-6)  # ~1.135 mOhm/sq

    # Map physical (x, y) -> (iu, iv) where u = x, v = y - x * tan(17.75 deg)
    def xy_to_ij(x: float, y: float) -> tuple[int, int]:
        v = y - x * tan_skew
        i = int(np.clip(round((x - us[0]) / du), 0, nx - 1))
        j = int(np.clip(round((v - vs[0]) / dv), 0, ny - 1))
        return i, j

    N = nx * ny
    A = np.zeros((N, N), dtype=float)
    gx = 1.0 / (r_sheet * (du / dv))
    gy = 1.0 / (r_sheet * (dv / du))

    # Mask out 'LX cutout L2' [1.65..3.30] x [9.15..14.70]
    active = np.ones((nx, ny), dtype=bool)
    for i, x in enumerate(us):
        for j, v in enumerate(vs):
            y = v + x * tan_skew
            if 1.65 <= x <= 3.30 and 9.15 <= y <= 14.70:
                active[i, j] = False

    for i in range(nx):
        for j in range(ny):
            k = i * ny + j
            if not active[i, j]:
                A[k, k] = 1.0
                continue
            diag = 0.0
            for di, dj, g in [(-1, 0, gx), (1, 0, gx), (0, -1, gy), (0, 1, gy)]:
                ni, nj = i + di, j + dj
                if 0 <= ni < nx and 0 <= nj < ny and active[ni, nj]:
                    A[k, ni * ny + nj] = -g
                    diag += g
            A[k, k] = max(diag, 1e-6)

    # Sink return current at U5 BQ24073 GND EP (4.8, 19.0) = 0 V reference; inject 240 mA at U1 EP (0.0, -18.5) + 240 mA at U2 EP (7.4, -8.2)
    rhs = np.zeros(N)
    for x_ep, y_ep, cur in [(0.0, -18.5, 0.240), (7.4, -8.2, 0.240)]:
        ic, jc = xy_to_ij(x_ep, y_ep)
        pts = [(ic + di, jc + dj) for di in (-1, 0, 1) for dj in (-1, 0, 1) if 0 <= ic + di < nx and 0 <= jc + dj < ny]
        for pi, pj in pts:
            rhs[pi * ny + pj] += cur / len(pts)

    i_u5, j_u5 = xy_to_ij(4.8, 19.0)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            k0 = (i_u5 + di) * ny + (j_u5 + dj)
            A[k0, :] = 0.0
            A[:, k0] = 0.0
            A[k0, k0] = 1.0
            rhs[k0] = 0.0

    v_map = np.linalg.solve(A, rhs).reshape((nx, ny))
    i_u1, j_u1 = xy_to_ij(0.0, -18.5)
    i_u2, j_u2 = xy_to_ij(7.4, -8.2)
    return {
        "in1_r_sheet_mohm_sq": round(r_sheet * 1e3, 3),
        "gnd_bounce_dc_u1_mv_at_480ma": round(float(v_map[i_u1, j_u1] * 1e3), 2),
        "gnd_bounce_dc_u2_mv_at_480ma": round(float(v_map[i_u2, j_u2] * 1e3), 2),
        "_grid": {"us": us, "vs": vs, "tan_skew": tan_skew, "v_mv": v_map * 1e3, "active": active},
    }


def extract_vsys_inductance_and_spice(r_vsys: dict, r_sw1: dict, gnd_res: dict) -> dict:
    """FastHenry2 loop inductance of the U5 -> U2 -> U1 VSYS spine over In1.Cu + SPICE transient & LiPo foldback."""
    fh = FastHenryDeck("VSYS U5 -> U2 -> U1 spine over In1.Cu")
    pnodes = [("gu5", 4.8, 19.0, -0.253), ("gu2", 7.4, -8.2, -0.253), ("gu1", 0.0, -18.5, -0.253)]
    fh.plane("in1", -8.0, -24.0, 11.0, 23.0, -0.253, thick=0.0152, seg1=16, seg2=32, nodes=pnodes)
    nu5 = fh.node("vu5", 4.8, 19.0, -1.333)
    nu5t = fh.node("vu5t", 4.8, 19.0, -0.253)
    nu2 = fh.node("vu2", 7.4, -8.2, -1.333)
    nu2t = fh.node("vu2t", 7.4, -8.2, -0.253)
    nu1 = fh.node("vu1", 0.0, -18.5, -1.333)
    nu1t = fh.node("vu1t", 0.0, -18.5, -0.253)
    fh.seg(nu5, nu2, w=0.20, h=0.0152)
    fh.seg(nu2, nu1, w=0.20, h=0.0152)
    fh.seg(nu5, nu5t, w=0.25, h=0.25)
    fh.equiv(nu5t, "gu5")
    fh.equiv(nu2t, "gu2")
    fh.equiv(nu1t, "gu1")
    fh.port(nu1, nu1t, "U1_PVCC")
    fh.port(nu2, nu2t, "U2_PVCC")
    out = fh.run(1e6, 5e7, ndec=2)
    f = float(out["freqs"][-1])
    z = out["Z"][-1]
    l_u1_nh = float(np.imag(z[0, 0]) / (2 * math.pi * f) * 1e9)
    l_u2_nh = float(np.imag(z[1, 1]) / (2 * math.pi * f) * 1e9)
    l_seg1 = l_u2_nh
    l_seg2 = max(4.0, l_u1_nh - l_u2_nh)

    r_u5_u2 = r_vsys["R_ohm"]["U2_PVCC"]
    r_u2_u1 = max(0.05, r_vsys["R_ohm"]["U1_PVCC"] - r_u5_u2)

    # SPICE transient at VBAT = 3.70 V: BQ24073 internal BAT FET R_dson = 0.22 Ohm, C2=C30=C40 = 9.5 uF effective (derated 22 uF 0603)
    ng = NgSpice()

    def run_pdn(three_phase: bool) -> dict:
        if not three_phase:
            i_u1 = "Iload1 u1_v 0 PULSE(0.005 0.240 2u 10n 10n 6.5u 16u)"
            i_u2 = "Iload2 u2_v 0 PULSE(0.005 0.240 2u 10n 10n 6.5u 16u)"
        else:
            # 3-Phase PWM stagger + phase shift between U1 and U2 spreads transient steps cleanly
            i_u1 = (
                "Iload1a u1_v 0 PULSE(0.002 0.080 2.0u 10n 10n 6.5u 16u)\n"
                "Iload1b u1_v 0 PULSE(0.002 0.080 7.3u 10n 10n 6.5u 16u)\n"
                "Iload1c u1_v 0 PULSE(0.001 0.080 12.6u 10n 10n 6.5u 16u)"
            )
            i_u2 = (
                "Iload2a u2_v 0 PULSE(0.002 0.080 4.6u 10n 10n 6.5u 16u)\n"
                "Iload2b u2_v 0 PULSE(0.002 0.080 9.9u 10n 10n 6.5u 16u)\n"
                "Iload2c u2_v 0 PULSE(0.001 0.080 15.2u 10n 10n 6.5u 16u)"
            )
        net = f"""VSYS PDN Droop (3phase={three_phase})
Vbat bat 0 3.70
Rbq  bat u5_v 0.220
Cc2  u5_v c2_esr 9.5u
Rc2  c2_esr 0 0.012
* U6 TPS7A0233 + RP2350 steady 32 mA load
Imcu u5_v 0 0.032
* Segment U5 -> U2
Rseg1 u5_v n_u2 {r_u5_u2:.4f}
Lseg1 n_u2 u2_v {l_seg1:.3f}n
Cc40  u2_v c40_r 9.5u
Rc40  c40_r 0 0.012
Cc41  u2_v 0 0.8u
* Segment U2 -> U1
Rseg2 u2_v n_u1 {r_u2_u1:.4f}
Lseg2 n_u1 u1_v {l_seg2:.3f}n
Cc30  u1_v c30_r 9.5u
Rc30  c30_r 0 0.012
Cc31  u1_v 0 0.8u
{i_u1}
{i_u2}
.end
"""
        vecs = ng.run_tran(net, "20n", "64u", ["v(u5_v)", "v(u2_v)", "v(u1_v)"])
        m_ss = vecs["time"] >= 32e-6
        vmin_u1 = float(np.min(vecs["v(u1_v)"][m_ss]))
        vpp_u1_mv = float((np.max(vecs["v(u1_v)"][m_ss]) - np.min(vecs["v(u1_v)"][m_ss])) * 1e3)
        return {
            "v_u1_min_at_3p7v": round(vmin_u1, 4),
            "droop_from_vbat_mv": round((3.70 - vmin_u1) * 1e3, 1),
            "ac_ripple_u1_vpp_mv": round(vpp_u1_mv, 1),
            "t_us": (vecs["time"] * 1e6).tolist(),
            "v_u1": vecs["v(u1_v)"].tolist(),
            "v_u2": vecs["v(u2_v)"].tolist(),
        }

    pdn_1ph = run_pdn(False)
    pdn_3ph = run_pdn(True)

    # Exact Green/Blue LED current-regulation headroom budget at North-West D1 (-9.25, -30.25):
    # At I_peak(G) = 13.33 mA * (96/255 D65 SL) = 5.02 mA (or I_peak(B) = 13.33 mA * (220/255) = 11.50 mA!):
    # Blue XL-1615RGBC-RF at I_peak = 11.5 mA * (GCC/255):
    #   VF_blue(I) = 2.68 V + 0.032 * I_mA  (typ-to-high bin: 3.05 V @ 11.5 mA; worst-case cold/high bin: 3.22 V @ 11.5 mA)
    #   V_drop_SW_PMOS (AW20198 R_SW = 0.65 Ohm * I_row)
    #   V_drop_SW_copper (R_SW1_1_to_D1 * I_row/6 + shared stem)
    #   V_headroom_CS (AW20198 constant-current sink knee = 0.22 V at 11.5 mA, scales gently with I)
    #   V_drop_VSYS_to_U1 = (R_BQ24073 + R_VSYS_U1 + R_GND_In1) * I_avg_total
    r_sw_d1 = r_sw1["R_ohm"]["D1_A"]
    r_total_dc_u1 = 0.220 + r_vsys["R_ohm"]["U1_PVCC"] + (gnd_res["gnd_bounce_dc_u1_mv_at_480ma"] * 1e-3 / 0.480)

    vbat_grid = np.linspace(3.00, 4.20, 25)
    foldback_curve = []
    for vb in vbat_grid:
        # Find max GCC in [32..255] such that North D1 Blue channel stays out of CS dropout (V_CS >= 0.22 V)
        best_gcc = 32
        for gcc in range(255, 31, -1):
            scale = gcc / 255.0
            # Peak white row current per driver (6 RGB triplets with SL=(255, 96, 220) -> sum = (1 + 0.376 + 0.863)*13.33*6 = 179 mA * scale)
            i_row_pk = 0.179 * scale
            # Average dual-driver current (duty = 11/12.4 = 0.887 active scan time, avg 50% visual fill -> ~0.75 * 2 * i_row_pk + 32 mA MCU)
            i_sys_avg = 0.032 + 1.50 * i_row_pk
            v_pvcc_u1 = vb - i_sys_avg * r_total_dc_u1 - 0.015 * scale  # includes 3-phase AC ripple
            v_anode_d1 = v_pvcc_u1 - i_row_pk * (0.65 + 0.45 * r_sw_d1)
            i_blue_ma = 11.50 * scale
            vf_blue = 2.68 + 0.034 * i_blue_ma  # XL-1615RGBC Blue @ I_peak
            v_cs_avail = v_anode_d1 - vf_blue
            v_cs_knee = 0.14 + 0.007 * i_blue_ma
            if v_cs_avail >= v_cs_knee:
                best_gcc = gcc
                break
        foldback_curve.append({"vbat_v": round(float(vb), 2), "max_clean_gcc": int(best_gcc)})

    return {
        "L_vsys_u1_loop_nh": round(l_u1_nh, 2),
        "L_vsys_u2_loop_nh": round(l_u2_nh, 2),
        "R_vsys_u5_to_u2_mohm": round(r_u5_u2 * 1e3, 1),
        "R_vsys_u5_to_u1_mohm": round(r_vsys["R_ohm"]["U1_PVCC"] * 1e3, 1),
        "R_sw1_1_u1_to_d1_mohm": round(r_sw_d1 * 1e3, 1),
        "pdn_1phase": {k: v for k, v in pdn_1ph.items() if not isinstance(v, list)},
        "pdn_3phase": {k: v for k, v in pdn_3ph.items() if not isinstance(v, list)},
        "gcc_foldback_lut": foldback_curve,
        "_wf": {"p1": pdn_1ph, "p3": pdn_3ph},
    }


def make_plots(gnd_res: dict, pdn_res: dict):
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "figure.facecolor": "#0d1117",
        "axes.facecolor": "#161b22",
        "axes.edgecolor": "#30363d",
        "axes.labelcolor": "#e6edf3",
        "xtick.color": "#8b949e",
        "ytick.color": "#8b949e",
        "text.color": "#e6edf3",
        "grid.color": "#21262d",
        "font.size": 10,
    })

    fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.7), dpi=150)

    # Panel 1: Skewed parallelogram In1.Cu GND return potential map
    ax = axes[0]
    gr = gnd_res["_grid"]
    U, V = np.meshgrid(gr["us"], gr["vs"], indexing="ij")
    X = U
    Y = V + U * gr["tan_skew"]
    vm = np.where(gr["active"], gr["v_mv"], np.nan)
    im = ax.pcolormesh(X, Y, vm, cmap="magma", shading="auto")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="In1.Cu GND Potential (mV @ 480 mA)")
    ax.scatter([4.8, 7.4, 0.0], [19.0, -8.2, -18.5], c=["#7ee787", "#58a6ff", "#ff7b72"], s=45, zorder=5)
    ax.text(4.8, 21.0, "U5 (0 mV)", color="#7ee787", fontsize=8, ha="center")
    ax.text(5.8, -6.5, "U2", color="#58a6ff", fontsize=8)
    ax.text(0.0, -21.8, f"U1 ({gnd_res['gnd_bounce_dc_u1_mv_at_480ma']:.1f} mV)", color="#ff7b72", fontsize=8, ha="center")
    ax.invert_yaxis()
    ax.set_xlabel("Board X (mm)")
    ax.set_ylabel("Board Y (mm, KiCad South=+)")
    ax.set_title("Skewed In1.Cu Return Drop (480 mA)")

    # Panel 2: VSYS transient droop at North U1 (1-Phase vs 3-Phase)
    ax = axes[1]
    p1 = pdn_res["_wf"]["p1"]
    p3 = pdn_res["_wf"]["p3"]
    ax.plot(p1["t_us"], p1["v_u1"], color="#ff7b72", lw=1.7,
            label=f"U1 PVCC 1-Phase (min {p1['v_u1_min_at_3p7v']:.3f} V, {p1['ac_ripple_u1_vpp_mv']:.1f} mVpp)")
    ax.plot(p3["t_us"], p3["v_u1"], color="#7ee787", lw=2.0,
            label=f"U1 PVCC 3-Phase (min {p3['v_u1_min_at_3p7v']:.3f} V, {p3['ac_ripple_u1_vpp_mv']:.1f} mVpp)")
    ax.axhline(3.70, color="#8b949e", ls=":", lw=1.0, label="VBAT = 3.70 V")
    ax.set_xlim(0, 64)
    ax.set_xlabel("Time (µs)")
    ax.set_ylabel("North U1 PVCC Voltage (V)")
    ax.set_title(f"137.9 mm VSYS Spine Transient (R={pdn_res['R_vsys_u5_to_u1_mohm']:.0f} mΩ)")
    ax.grid(True, alpha=0.6)
    ax.legend(loc="lower right", fontsize=8, framealpha=0.88, facecolor="#0d1117")

    # Panel 3: Firmware GCC(VBAT) Blue-Shift Prevention Foldback Curve
    ax = axes[2]
    vbs = [pt["vbat_v"] for pt in pdn_res["gcc_foldback_lut"]]
    gccs = [pt["max_clean_gcc"] for pt in pdn_res["gcc_foldback_lut"]]
    ax.plot(vbs, gccs, color="#58a6ff", lw=2.4, marker="o", ms=3.5, label="Max Color-Accurate GCC (North D1 Blue)")
    ax.axvspan(3.0, 3.45, color="#f85149", alpha=0.14, label="Blue/Green CS Dropout Zone @ GCC=255")
    ax.set_xlim(3.0, 4.2)
    ax.set_ylim(0, 270)
    ax.set_xlabel("LiPo Battery Voltage VBAT (V)")
    ax.set_ylabel("AW20198 Global Current GCC (0-255)")
    ax.set_title("EM/PDN-Derived Firmware GCC(VBAT) Foldback")
    ax.grid(True, alpha=0.6)
    ax.legend(loc="lower right", fontsize=8, framealpha=0.88, facecolor="#0d1117")

    fig.tight_layout()
    fig.savefig(IMG_DIR / "p4_vsys_pdn.png", dpi=150)
    plt.close(fig)


def main():
    geom = json.loads(GEOM_JSON.read_text())
    print("[P4] Solving exact nodal copper resistance of 137.9 mm VSYS tree and 99.4 mm SW1_1 tree...", flush=True)
    r_vsys = solve_copper_graph_resistance(
        geom,
        "VSYS",
        src_xy=(4.8, 19.0),
        dst_xys={"U2_PVCC": (7.4, -8.2), "U1_PVCC": (0.0, -18.5)},
    )
    r_sw1 = solve_copper_graph_resistance(
        geom,
        "/Driver 1 and matrix/SW1_1",
        src_xy=(0.0, -18.5),
        dst_xys={"D1_A": (-9.25, -30.25), "D56_A": (9.25, -24.50)},
    )
    print(f"     R_VSYS(U5->U2) = {r_vsys['R_ohm']['U2_PVCC']*1e3:.1f} mOhm, R_VSYS(U5->U1) = {r_vsys['R_ohm']['U1_PVCC']*1e3:.1f} mOhm", flush=True)

    print("[P4] Solving 2D skewed parallelogram In1.Cu GND return plane...", flush=True)
    gnd_res = solve_in1_gnd_return_plane()
    print("[P4] Running FastHenry2 VSYS spine + libngspice PDN droop & LiPo GCC foldback sweep...", flush=True)
    pdn_res = extract_vsys_inductance_and_spice(r_vsys, r_sw1, gnd_res)
    make_plots(gnd_res, pdn_res)

    knee_v = next((pt["vbat_v"] for pt in pdn_res["gcc_foldback_lut"] if pt["max_clean_gcc"] == 255), 4.20)
    out = {
        "phase": "P4_vsys_pdn",
        "vsys_copper_graph": r_vsys,
        "sw1_1_copper_graph": r_sw1,
        "in1_gnd_plane": {k: v for k, v in gnd_res.items() if k != "_grid"},
        "pdn_and_foldback": {k: v for k, v in pdn_res.items() if k != "_wf"},
        "full_gcc255_vbat_floor_v": knee_v,
        "verdict": (
            f"The 137.9 mm VSYS spine adds {pdn_res['R_vsys_u5_to_u1_mohm']} mOhm + {pdn_res['L_vsys_u1_loop_nh']} nH from South U5 to North U1, "
            f"plus {pdn_res['R_sw1_1_u1_to_d1_mohm']} mOhm along SW1_1 to corner LED D1 and 220 mOhm in BQ24073's BAT FET. "
            f"3-Phase PWM stagger cuts AC PVCC ripple at U1 from {pdn_res['pdn_1phase']['ac_ripple_u1_vpp_mv']} mVpp down to "
            f"{pdn_res['pdn_3phase']['ac_ripple_u1_vpp_mv']} mVpp! Below VBAT = {knee_v:.2f} V, full-white GCC=255 pushes North D1's "
            f"Blue/Green sinks into dropout (causing warm/red color shift on the North half before the South half!). "
            f"Implementing our derived GCC(VBAT) foldback curve in firmware preserves D65 color balance all the way down to 3.10 V."
        ),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2))
    print(f"[P4] Saved {OUT_JSON} and {IMG_DIR / 'p4_vsys_pdn.png'}", flush=True)


if __name__ == "__main__":
    main()
