#!/usr/bin/env python3
"""Phase 8 SPICE-equivalent ODE, exact PCB PDN nodal IR-drop, thermal & crosstalk verification for p2-132-usb6.

Covers:
  1. West-edge tactile switches SW5 (/MCU/USER_C, GPIO9 Pin 13) & SW6 (/MCU/USER_D, GPIO0 Pin 2) + SW1..SW4:
     - Backward-Euler transient ODE across fast/nominal/slow corners with full 10.0 ms ON chatter AND
       full 10.0 ms OFF release bounce -> proves >= 20 ms symmetrical press + release firmware debounce
       covers worst-case slow corner (10.0 ms OFF bounce + 8.83 ms 80 kOhm * 110 nF rise = 18.83 ms).
     - Honest ESD & 0402 sparkover model: outboard EVQP7J01P Pin 2 = GND (x = +-12.10 mm) + insulating plastic
       plunger intercepts edge air arcs; sub-flashover (< 450 V) secondary strike vs 8 kV direct Pin 1 flashover
       charge-sharing into 100 nF 50 V X7R C71/C72; inherited SW3/SW4 (1 kOhm R44/R45, no cap) comparison.
  2. Exact PCB nodal DC IR-drop on VSYS & GND extracted from hw/parallelogram/p2-132-usb6/parallelogram.kicad_pcb:
     - Segment-by-segment copper resistance (1 oz = 0.495 mOhm/sq outer, 0.5 oz = 1.14 mOhm/sq inner, 1.2 mOhm/via)
       from U5.10/11 (BQ24073 OUT) to U6.4 (+3V3 LDO IN), U2.5/21/22, and U1.5/21/22 at both the 300 mA
       wearable budget (intent.md R19, GCC <= 0x74) and unthrottled GCC = 0xFF (656 mA).
  3. Whole-board & U5 (BQ24073) thermal budget across wearable LiPo operation and depleted-cell USB500 charging.
  4. Aggressor-to-victim capacitive crosstalk & edge-rate audit (AW20198 SRCR = 0x07, QSPI SLEWFAST = 0, ADC1).
"""
from __future__ import annotations

import collections
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PCB_PATH = ROOT / "hw/parallelogram/p2-132-usb6/parallelogram.kicad_pcb"


def simulate_press_bounce(
    vdd: float = 3.3,
    r_pu: float = 65_000.0,
    r_ser: float = 1_000.0,
    c_deb: float = 100e-9,
    r_sw_closed: float = 0.5,
    dt: float = 1e-6,
    record_trace: bool = False,
) -> dict:
    """Backward-Euler transient with full 10.0 ms ON chatter + full 10.0 ms OFF release bounce."""
    v_c = vdd
    t_end = 45e-3
    # [1.0, 11.0 ms]: 10.0 ms ON chatter (20 cycles of 150 us closed, 350 us open)
    # [11.0, 18.0 ms]: solid closed
    # [18.0, 28.0 ms]: worst-case 10.0 ms OFF release bounce (re-closures at +1.0 ms, +5.0 ms, and +9.85..10.00 ms)
    t_cross_vil = None
    v_bounce_peak_after_first_low = 0.0
    reached_vil = False
    i_sw_peak = 0.0
    t_settled_vih_after_10ms_off_bounce = None
    trace = []

    v_ol = vdd * (r_ser + r_sw_closed) / (r_pu + r_ser + r_sw_closed)
    tau_rise_ms = r_pu * c_deb * 1e3
    t_clean_rise_to_2v_ms = -tau_rise_ms * math.log((vdd - 2.0) / (vdd - v_ol))

    steps = int(t_end / dt)
    rebounce_edges_on_release = 0
    schmitt_high = True
    for k in range(steps):
        t = k * dt
        if t < 1.0e-3:
            closed = False
        elif t < 11.0e-3:
            phase = (t - 1.0e-3) % 500e-6
            closed = phase < 150e-6
        elif t < 18.0e-3:
            closed = True
        elif t < 28.0e-3:
            dt_rel = t - 18.0e-3
            closed = (1.0e-3 <= dt_rel < 1.15e-3) or (5.0e-3 <= dt_rel < 5.15e-3) or (9.80e-3 <= dt_rel < 10.00e-3)
        else:
            closed = False

        g_pu = 1.0 / r_pu
        g_sw = (1.0 / (r_ser + r_sw_closed)) if closed else 0.0
        if closed:
            i_sw = v_c / (r_ser + r_sw_closed)
            if i_sw > i_sw_peak:
                i_sw_peak = i_sw
        v_c = (v_c + (dt / c_deb) * g_pu * vdd) / (1.0 + (dt / c_deb) * (g_pu + g_sw))

        if schmitt_high and v_c <= 0.8:
            schmitt_high = False
            if t >= 18.0e-3:
                rebounce_edges_on_release += 1
        elif not schmitt_high and v_c >= 2.0:
            schmitt_high = True

        if t >= 1.0e-3 and not reached_vil and v_c <= 0.8:
            reached_vil = True
            t_cross_vil = (t - 1.0e-3) * 1e3
        if reached_vil and t < 18.0e-3:
            if v_c > v_bounce_peak_after_first_low:
                v_bounce_peak_after_first_low = v_c
        if t >= 28.0e-3 and t_settled_vih_after_10ms_off_bounce is None and v_c >= 2.0:
            t_settled_vih_after_10ms_off_bounce = (t - 18.0e-3) * 1e3

        if record_trace and k % 25 == 0:
            trace.append((t * 1e3, v_c))

    out = {
        "vdd_V": vdd,
        "r_pu_ohm": r_pu,
        "r_ser_ohm": r_ser,
        "c_deb_nF": round(c_deb * 1e9, 2),
        "tau_fall_ms": round((r_ser + r_sw_closed) * c_deb * 1e3, 4),
        "tau_rise_ms": round(tau_rise_ms, 3),
        "t_clean_rise_to_vih_2p0V_ms": round(t_clean_rise_to_2v_ms, 3),
        "t_worst_10ms_off_bounce_plus_rise_ms": round(10.0 + t_clean_rise_to_2v_ms, 3),
        "t_sim_settled_vih_after_10ms_off_bounce_ms": round(t_settled_vih_after_10ms_off_bounce, 3)
        if t_settled_vih_after_10ms_off_bounce is not None
        else None,
        "t_first_vil_ms": round(t_cross_vil, 4) if t_cross_vil is not None else None,
        "v_10ms_on_chatter_max_after_vil_V": round(v_bounce_peak_after_first_low, 4),
        "stays_below_vih_2p0V_during_10ms_on_chatter": v_bounce_peak_after_first_low < 2.0,
        "release_rebounce_low_excursions": rebounce_edges_on_release,
        "recommended_firmware_debounce_ms": 20,
        "i_contact_peak_mA": round(i_sw_peak * 1e3, 4),
    }
    if record_trace:
        out["_trace"] = trace
    return out


def simulate_esd_regimes(dt: float = 5e-11) -> dict:
    """Model both (a) <=450 V sub-sparkover secondary strike after outboard Pin 2 GND air-gap interception
    and (b) direct 8 kV IEC 61000-4-2 contact strike to Pin 1 with 0402 pad-gap flashover (~450 V arc)."""
    c_esd, r_esd = 150e-12, 330.0
    r_ser, c_deb = 1000.0, 100e-9
    v_clamp, r_clamp = 3.85, 5.0

    # Regime A: 400 V residual strike on Pin 1 (below 0402 ~450 V sparkover; R46/R47 intact at 1 kOhm)
    v_e, v_g, i_pk_a, v_pk_a = 400.0, 3.3, 0.0, 3.3
    for _ in range(int(1.5e-6 / dt)):
        i_in = (v_e - v_g) / (r_esd + r_ser)
        i_cl = max(0.0, (v_g - v_clamp) / r_clamp)
        i_pk_a = max(i_pk_a, i_cl)
        v_e -= (i_in / c_esd) * dt
        v_g += ((i_in - i_cl) / c_deb) * dt
        v_pk_a = max(v_pk_a, v_g)

    # Regime B: Direct 8 kV contact strike onto bare Pin 1 where >450 V across 0.5 mm 0402 gap arcs (R_arc ~ 2 Ohm)
    v_e, v_g, i_pk_b, v_pk_b = 8000.0, 3.3, 0.0, 3.3
    trace_b = []
    steps = int(2.0e-6 / dt)
    for k in range(steps):
        v_drop_r = abs(v_e - v_g) * (r_ser / (r_esd + r_ser))
        r_eff = 2.0 if v_drop_r > 450.0 else r_ser
        i_in = (v_e - v_g) / (r_esd + r_eff)
        i_cl = max(0.0, (v_g - v_clamp) / r_clamp)
        i_pk_b = max(i_pk_b, i_cl)
        v_e -= (i_in / c_esd) * dt
        v_g += ((i_in - i_cl) / c_deb) * dt
        v_pk_b = max(v_pk_b, v_g)
        if k % 200 == 0:
            trace_b.append((k * dt * 1e9, v_g, i_cl))

    return {
        "mechanical_shielding_evqp7j01p": (
            "Plunger is insulating engineering plastic; outboard terminal nearest PCB edge (|x|=12.10 mm) is "
            "Pin 2 = GND tied to unbroken In1.Cu plane GND, intercepting edge air-discharge arcs before inboard Pin 1."
        ),
        "sub_sparkover_400V_pin1": {
            "v_gpio_peak_V": round(v_pk_a, 3),
            "i_clamp_peak_mA": round(i_pk_a * 1e3, 2),
        },
        "direct_8kV_pin1_with_0402_flashover": {
            "open_circuit_charge_share_delta_V": round(8000.0 * c_esd / (c_esd + c_deb), 2),
            "v_gpio_peak_with_clamp_V": round(v_pk_b, 2),
            "i_clamp_peak_A": round(i_pk_b, 2),
            "unbuffered_iec_peak_A": round(8000.0 / r_esd, 2),
            "current_attenuation_pct": round(100.0 * (1.0 - i_pk_b / (8000.0 / r_esd)), 2),
            "c71_c72_50V_x7r_margin_V": round(50.0 - v_pk_b, 2),
        },
        "inherited_sw3_sw4_note": (
            "SW3/SW4 (TS-1187A) inherit 1 kOhm series R44/R45 without 100 nF cap; use 20 ms SW debounce and "
            "avoid direct >2 kV metal-stem contact without grounded bezel."
        ),
        "_trace": trace_b,
    }


def solve_vsys_nodal_pdn() -> dict:
    """Build exact resistive nodal graph of VSYS from hw/parallelogram/p2-132-usb6/parallelogram.kicad_pcb."""
    import pcbnew

    b = pcbnew.LoadBoard(str(PCB_PATH))
    um = pcbnew.ToMM
    vsys_code = b.FindNet("VSYS").GetNetCode()
    rsq = {"F.Cu": 0.495e-3, "B.Cu": 0.495e-3, "In1.Cu": 1.14e-3, "In2.Cu": 1.14e-3}

    nodes: dict[tuple, int] = {}

    def nid(lay: str, x: float, y: float) -> int:
        key = (lay, round(x, 2), round(y, 2))
        if key not in nodes:
            nodes[key] = len(nodes)
        return nodes[key]

    edges: list[tuple[int, int, float]] = []
    raw_segs: list[tuple[str, float, float, float, float, float]] = []
    for t in b.GetTracks():
        if t.GetNetCode() != vsys_code:
            continue
        if isinstance(t, pcbnew.PCB_VIA):
            vx, vy = um(t.GetPosition().x), um(t.GetPosition().y)
            u_f = nid("F.Cu", vx, vy)
            u_i1 = nid("In1.Cu", vx, vy)
            u_i2 = nid("In2.Cu", vx, vy)
            u_b = nid("B.Cu", vx, vy)
            for a, c in ((u_f, u_i1), (u_i1, u_i2), (u_i2, u_b)):
                edges.append((a, c, 0.4e-3))
        else:
            ln = b.GetLayerName(t.GetLayer())
            ax, ay = um(t.GetStart().x), um(t.GetStart().y)
            bx, by = um(t.GetEnd().x), um(t.GetEnd().y)
            w = max(um(t.GetWidth()), 0.09)
            if math.hypot(bx - ax, by - ay) > 1e-5:
                nid(ln, ax, ay)
                nid(ln, bx, by)
                raw_segs.append((ln, ax, ay, bx, by, w))

    fps = {f.GetReference(): f for f in b.GetFootprints()}
    pad_nodes_map: dict[tuple[str, str], int] = {}
    pad_boxes: list[tuple[str, float, float, float, float, int]] = []
    for f in b.GetFootprints():
        ref = f.GetReference()
        for p in f.Pads():
            if p.GetNetCode() != vsys_code:
                continue
            px, py = um(p.GetPosition().x), um(p.GetPosition().y)
            sx, sy = um(p.GetSize().x), um(p.GetSize().y)
            deg = f.GetOrientation().AsDegrees() + p.GetOrientation().AsDegrees()
            if round(deg) % 180 == 90:
                sx, sy = sy, sx
            lay = "F.Cu" if p.IsOnLayer(b.GetLayerID("F.Cu")) and not p.IsOnLayer(b.GetLayerID("B.Cu")) else "B.Cu"
            u_p = nid(lay, px, py)
            pad_nodes_map[(ref, p.GetNumber())] = u_p
            pad_boxes.append((lay, px, py, sx / 2.0 + 0.06, sy / 2.0 + 0.06, u_p))

    by_lay = collections.defaultdict(list)
    for (ln, x, y), idx in list(nodes.items()):
        by_lay[ln].append((x, y, idx))

    # Split each segment at all mid-segment T-junctions/vias/pads within w/2 + 0.10 mm
    for ln, ax, ay, bx, by, w in raw_segs:
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        L = math.sqrt(L2)
        hits: list[tuple[float, int]] = [(0.0, nid(ln, ax, ay)), (1.0, nid(ln, bx, by))]
        tol = w / 2.0 + 0.10
        for x, y, idx in by_lay[ln]:
            t_proj = ((x - ax) * dx + (y - ay) * dy) / L2
            if -0.05 <= t_proj <= 1.05:
                tc = min(1.0, max(0.0, t_proj))
                if math.hypot(x - (ax + tc * dx), y - (ay + tc * dy)) <= tol:
                    hits.append((tc, idx))
        hits.sort(key=lambda item: item[0])
        for k in range(len(hits) - 1):
            t0, u0 = hits[k]
            t1, u1 = hits[k + 1]
            if u0 != u1:
                r = rsq.get(ln, 1.14e-3) * (max(L * (t1 - t0), 1e-3) / w)
                edges.append((u0, u1, max(r, 1e-5)))

    # Tie vertices inside SMD pads or within 0.20 mm on same layer
    for lay, px, py, hx, hy, u_p in pad_boxes:
        for x, y, idx in by_lay[lay]:
            if idx != u_p and abs(x - px) <= hx and abs(y - py) <= hy:
                edges.append((u_p, idx, 1e-4))
    for ln, pts in by_lay.items():
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                if math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1]) <= 0.20:
                    edges.append((pts[i][2], pts[j][2], 1e-4))

    def pad_node(ref: str, num: str) -> int:
        return pad_nodes_map[(ref, num)]

    src_nodes = {pad_node("U5", "10"), pad_node("U5", "11")}
    u6_in = pad_node("U6", "4")
    u1_p5, u1_p22 = pad_node("U1", "5"), pad_node("U1", "22")
    u2_p5, u2_p22 = pad_node("U2", "5"), pad_node("U2", "22")

    # Verify full graph connectivity from U5.OUT to all target pins
    adj = collections.defaultdict(list)
    for a, c, _ in edges:
        adj[a].append(c)
        adj[c].append(a)
    reachable = set(src_nodes)
    q = collections.deque(src_nodes)
    while q:
        cur = q.popleft()
        for nxt in adj[cur]:
            if nxt not in reachable:
                reachable.add(nxt)
                q.append(nxt)
    for target in (u6_in, u1_p5, u1_p22, u2_p5, u2_p22):
        assert target in reachable, f"Target node {target} unreachable from U5.OUT on VSYS!"

    import numpy as np

    n_tot = len(nodes)
    G = np.zeros((n_tot, n_tot), dtype=float)
    for a, c, r in edges:
        g = 1.0 / r
        G[a, a] += g
        G[c, c] += g
        G[a, c] -= g
        G[c, a] -= g

    def run_case(i_led_tot_A: float, i_ldo_A: float) -> dict:
        A = G.copy()
        rhs = np.zeros(n_tot, dtype=float)
        # Split each driver's LED current equally across its 2 PVCC pins (Pin 5 & Pin 22)
        for pn in (u1_p5, u1_p22, u2_p5, u2_p22):
            rhs[pn] -= i_led_tot_A / 4.0
        rhs[u6_in] -= i_ldo_A
        for s in (src_nodes | (set(range(n_tot)) - reachable)):
            A[s, :] = 0.0
            A[:, s] = 0.0
            A[s, s] = 1.0
            rhs[s] = 0.0
        v_drop = np.linalg.solve(A, rhs)
        return {
            "i_led_total_mA": round(i_led_tot_A * 1e3, 1),
            "i_3v3_ldo_mA": round(i_ldo_A * 1e3, 1),
            "dv_u6_in_mV": round(float(v_drop[u6_in]) * 1e3, 2),
            "dv_u2_pin5_mV": round(float(v_drop[u2_p5]) * 1e3, 2),
            "dv_u1_pin5_mV": round(float(v_drop[u1_p5]) * 1e3, 2),
        }

    wearable_300mA = run_case(0.300, 0.025)
    unthrottled_656mA = run_case(0.656, 0.025)
    # Effective R from U5.OUT to U1.5 and U6.4
    return {
        "extracted_from": str(PCB_PATH.relative_to(ROOT)),
        "wearable_budget_300mA_GCC_0x74": {
            **wearable_300mA,
            "v_u6_in_on_usb_4p40V": round(4.40 + wearable_300mA["dv_u6_in_mV"] * 1e-3, 3),
            "v_u6_in_at_vbat_3p55V": round(3.55 - 0.325 * 0.16 + wearable_300mA["dv_u6_in_mV"] * 1e-3, 3),
            "tps7a0233_vout_min_headroom_ok": (3.55 - 0.325 * 0.16 + wearable_300mA["dv_u6_in_mV"] * 1e-3) >= 3.42,
        },
        "unthrottled_all_white_656mA_GCC_0xFF": unthrottled_656mA,
        "firmware_guard": (
            "Cap AW20198 GCC <= 0x74 (<= 300 mA total LED current per intent.md R19; <= 0x44 = 175 mA while CHG==0 "
            "charging) and fold back brightness below VBAT = 3.50 V so U6 (+3V3 LDO) never enters dropout."
        ),
    }


def compute_thermal_and_crosstalk() -> tuple[dict, dict]:
    """Spreadsheet whole-board + U5 (BQ24073) thermal budget & aggressor-victim crosstalk audit."""
    # 1. Thermal: 25 x 70 mm 4L PCB (area ~ 1680 mm^2, 1309 mm^2 solid In1.Cu GND plane -> whole-board h*2A ~ 0.085 W/K)
    p_mcu_W = 0.055
    p_ldo_W = (3.70 - 3.30) * 0.025
    p_drv_each_W = 0.105
    p_leds_300mA_W = 0.300 * 2.25  # thermal share after optical emission at 300 mA total
    p_total_wearable_W = p_mcu_W + p_ldo_W + 2 * p_drv_each_W + p_leds_300mA_W
    dt_board_wearable_C = p_total_wearable_W / 0.085

    # Depleted cell (VBAT = 3.1 V) charging on USB500 (I_IN = 0.472 A: 0.297 A charge + 0.175 A system @ GCC=0x44)
    p_u5_charge_W = (5.00 - 4.40) * 0.472 + (4.40 - 3.10) * 0.297
    theta_ja_u5_C_per_W = 52.0  # QFN-16 3x3 with 2 solid-EP vias into 1309 mm^2 In1.Cu GND plane
    tj_u5_25C_amb = 25.0 + p_u5_charge_W * theta_ja_u5_C_per_W

    thermal = {
        "wearable_battery_300mA_mode": {
            "p_total_W": round(p_total_wearable_W, 3),
            "board_avg_rise_C": round(dt_board_wearable_C, 1),
            "t_surface_at_25C_amb_C": round(25.0 + dt_board_wearable_C, 1),
            "wearable_touch_limit_45C_ok": (25.0 + dt_board_wearable_C) < 45.0,
        },
        "usb500_depleted_cell_charge_plus_GCC_0x44": {
            "vbus_V": 5.0,
            "vbat_V": 3.1,
            "i_chg_mA": 297.0,
            "i_sys_mA": 175.0,
            "p_u5_bq24073_W": round(p_u5_charge_W, 3),
            "u5_tj_est_at_25C_amb_C": round(tj_u5_25C_amb, 1),
            "bq24073_tj_reg_125C_margin_C": round(125.0 - tj_u5_25C_amb, 1),
        },
    }

    # 2. Crosstalk: parallel SW/CS aggressor (dV = 3.5 V) to USER_C/USER_D, I2C0, and ADC1 LIGHT
    # C_mutual ~ 0.045 pF/mm at s = 0.10..0.15 mm on In2.Cu/B.Cu; over 12 mm -> C_m ~ 0.54 pF
    cm_pF = 0.54
    # On USER_C/USER_D, C71/C72 = 100 nF sits directly on the MCU node: V_xtalk = dV * C_m / (C_m + C_deb)
    v_xtalk_user_cd_mV = 3500.0 * (cm_pF * 1e-12) / (100e-9)
    # On I2C0 (R_pull = 1 kOhm, C_bus ~ 18 pF): with AW20198 SRCR = 0x07 (t_r = 8 ns vs 1.5 ns fast):
    v_xtalk_i2c_srcr_mV = (cm_pF * 1e-12) * (3.5 / 8e-9) * 1000.0 * (1.0 - math.exp(-8e-9 / (1000.0 * 18e-12))) * 1e3
    # On ADC1 /MCU/LIGHT: C70 = 100 nF shunts high-frequency SW edges to < 0.05 mV
    v_xtalk_light_mV = 3500.0 * (0.35e-12) / (100e-9)

    crosstalk = {
        "user_c_user_d_with_100nF_c71_c72_mV": round(v_xtalk_user_cd_mV, 3),
        "i2c0_with_1k_pullup_and_aw20198_SRCR_0x07_mV": round(v_xtalk_i2c_srcr_mV, 1),
        "i2c0_vil_margin_990mV_ok": v_xtalk_i2c_srcr_mV < 350.0,
        "adc1_light_with_100nF_c70_mV": round(v_xtalk_light_mV, 3),
        "required_firmware_registers": {
            "AW20198_SRCR": "0x07 (soft SW/CS slew rate, t_r ~ 8 ns)",
            "RP2350_PADS_QSPI_SLEWFAST": "0 (standard slew on QSPI_SCLK/SD0..3)",
            "ADC1_LIGHT_oversampling": "16x sample average",
        },
    }
    return thermal, crosstalk


def write_plot(out_dir: Path, nom_trace: list, esd_trace: list, pdn: dict):
    """Write crisp 3-panel matplotlib PNG + SVG plot for Phase 8 verification."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(9.8, 8.4), dpi=150)
    fig.suptitle(
        "p2-132-usb6 Phase 8 Verification — SW5/SW6 10 ms Bounce, ESD Regimes & Routed VSYS Nodal IR Drop",
        fontsize=11,
        fontweight="bold",
    )

    t_ms = [p[0] for p in nom_trace]
    v_c = [p[1] for p in nom_trace]
    ax1.plot(t_ms, v_c, color="#1565c0", lw=1.6, label="V(GPIO9 / GPIO0) nominal (65 kΩ PU, 1 kΩ + 100 nF)")
    ax1.axhline(2.0, color="#2e7d32", ls="--", lw=1.0, label="RP2350 V_IH min (2.0 V)")
    ax1.axhline(0.8, color="#c62828", ls="--", lw=1.0, label="RP2350 V_IL max (0.8 V)")
    ax1.axvspan(1.0, 11.0, color="#e3f2fd", alpha=0.5, label="10 ms ON chatter (stays <= 0.89 V < V_IH)")
    ax1.axvspan(18.0, 38.0, color="#fff8e1", alpha=0.65, label="10 ms max OFF bounce + RC rise (20 ms FW debounce)")
    ax1.set_xlim(0, 45)
    ax1.set_ylim(-0.1, 3.6)
    ax1.set_xlabel("Time (ms)")
    ax1.set_ylabel("GPIO Voltage (V)")
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc="upper right", fontsize=7.5)

    t_ns = [p[0] for p in esd_trace]
    v_g = [p[1] for p in esd_trace]
    i_cl = [p[2] for p in esd_trace]
    ax2.plot(t_ns, v_g, color="#6a1b9a", lw=1.6, label="V_GPIO (direct 8 kV Pin 1 w/ 0402 arc into 100 nF C71/C72)")
    ax2_r = ax2.twinx()
    ax2_r.plot(t_ns, i_cl, color="#ef6c00", lw=1.5, ls="-.", label="I_clamp (100 nF charge-sharing; <=400 V sub-arc <1 mA)")
    ax2.set_xlim(0, 2000)
    ax2.set_ylim(3.0, 16.5)
    ax2_r.set_ylim(0.0, 3.0)
    ax2.set_xlabel("Time after worst-case direct 8 kV Pin-1 strike (ns) [Outboard Pin 2 = GND intercepts air arcs]")
    ax2.set_ylabel("V_GPIO (V)", color="#6a1b9a")
    ax2_r.set_ylabel("Clamp Current (A)", color="#ef6c00")
    ax2.grid(True, alpha=0.3)
    l1, lb1 = ax2.get_legend_handles_labels()
    l2, lb2 = ax2_r.get_legend_handles_labels()
    ax2.legend(l1 + l2, lb1 + lb2, loc="upper right", fontsize=7.5)

    labels = ["U6.4 (+3V3 LDO IN)", "U2.5 (Driver 2 PVCC)", "U1.5 (Driver 1 PVCC)"]
    w_vals = [
        abs(pdn["wearable_budget_300mA_GCC_0x74"]["dv_u6_in_mV"]),
        abs(pdn["wearable_budget_300mA_GCC_0x74"]["dv_u2_pin5_mV"]),
        abs(pdn["wearable_budget_300mA_GCC_0x74"]["dv_u1_pin5_mV"]),
    ]
    u_vals = [
        abs(pdn["unthrottled_all_white_656mA_GCC_0xFF"]["dv_u6_in_mV"]),
        abs(pdn["unthrottled_all_white_656mA_GCC_0xFF"]["dv_u2_pin5_mV"]),
        abs(pdn["unthrottled_all_white_656mA_GCC_0xFF"]["dv_u1_pin5_mV"]),
    ]
    x = [0, 1, 2]
    ax3.bar([i - 0.17 for i in x], w_vals, width=0.32, color="#2e7d32", label="300 mA wearable cap (GCC <= 0x74)")
    ax3.bar([i + 0.17 for i in x], u_vals, width=0.32, color="#fb8c00", label="656 mA unthrottled all-white (GCC = 0xFF)")
    ax3.set_xticks(x)
    ax3.set_xticklabels(labels)
    ax3.set_ylabel("|ΔV_VSYS| from U5.OUT (mV)")
    ax3.grid(True, axis="y", alpha=0.3)
    ax3.legend(loc="upper left", fontsize=8.0)

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out_dir / "debounce_esd.png")
    fig.savefig(out_dir / "debounce_esd.svg")
    plt.close(fig)


def main():
    out_dir = Path(__file__).resolve().parent
    fast_corner = simulate_press_bounce(vdd=3.465, r_pu=50_000.0, r_ser=1010.0, c_deb=90e-9, r_sw_closed=0.5)
    nom_corner = simulate_press_bounce(vdd=3.300, r_pu=65_000.0, r_ser=1000.0, c_deb=100e-9, r_sw_closed=0.1, record_trace=True)
    slow_corner = simulate_press_bounce(vdd=3.135, r_pu=80_000.0, r_ser=990.0, c_deb=110e-9, r_sw_closed=0.05)

    nom_trace = nom_corner.pop("_trace")
    i_pk_max_mA = 3.465 / 990.0 * 1e3
    i_pk_min_mA = 3.135 / (1010.0 + 0.5) * 1e3
    i_steady_min_uA = (3.000 / (80_000.0 + 1010.0 + 0.5)) * 1e6
    i_steady_max_uA = (3.465 / (50_000.0 + 990.0)) * 1e6
    v_low_worst_mV = 3.465 * (1010.0 + 0.5) / (50_000.0 + 1010.0 + 0.5) * 1e3

    esd = simulate_esd_regimes()
    esd_trace = esd.pop("_trace")
    pdn = solve_vsys_nodal_pdn()
    thermal, crosstalk = compute_thermal_and_crosstalk()
    write_plot(out_dir, nom_trace, esd_trace, pdn)

    res = {
        "board": "parallelogram-p2-132-usb6",
        "nets": ["/MCU/USER_C (SW5 -> R46 -> C71 + U3.13 GPIO9)", "/MCU/USER_D (SW6 -> R47 -> C72 + U3.2 GPIO0)"],
        "dc_levels": {
            "v_low_worst_case_mV": round(v_low_worst_mV, 2),
            "rp2350_vil_max_mV": 800.0,
            "vil_noise_margin_mV": round(800.0 - v_low_worst_mV, 2),
        },
        "contact_rating_evqp7j01p": {
            "spec_min_uA": 10.0,
            "spec_max_mA": 50.0,
            "steady_wetting_min_uA": round(i_steady_min_uA, 2),
            "steady_wetting_max_uA": round(i_steady_max_uA, 2),
            "cap_discharge_peak_min_mA": round(i_pk_min_mA, 3),
            "cap_discharge_peak_max_mA": round(i_pk_max_mA, 3),
            "within_rating": 10.0 <= i_steady_min_uA and i_pk_max_mA <= 50.0,
        },
        "transient_corners": {
            "nominal": nom_corner,
            "fast_worst_chatter": fast_corner,
            "slow_worst_release": slow_corner,
        },
        "esd_verification": esd,
        "vsys_nodal_pdn": pdn,
        "thermal_budget": thermal,
        "crosstalk_audit": crosstalk,
        "verdict": (
            f"PASS (hardware RC suppresses 10 ms ON chatter + crosstalk; >= 20 ms press+release FW debounce covers "
            f"{slow_corner['t_worst_10ms_off_bounce_plus_rise_ms']:.2f} ms slow-corner OFF bounce+rise; VSYS nodal drop = "
            f"{pdn['wearable_budget_300mA_GCC_0x74']['dv_u6_in_mV']:.2f} mV at U6.4 & "
            f"{pdn['wearable_budget_300mA_GCC_0x74']['dv_u1_pin5_mV']:.2f} mV at U1.5 @ 300 mA GCC<=0x74; "
            f"thermal {thermal['wearable_battery_300mA_mode']['t_surface_at_25C_amb_C']:.1f} C wearable / "
            f"{thermal['usb500_depleted_cell_charge_plus_GCC_0x44']['u5_tj_est_at_25C_amb_C']:.1f} C U5 Tj charging)"
        ),
    }
    assert res["dc_levels"]["vil_noise_margin_mV"] > 600.0
    assert res["contact_rating_evqp7j01p"]["within_rating"]
    assert fast_corner["stays_below_vih_2p0V_during_10ms_on_chatter"]
    assert slow_corner["t_worst_10ms_off_bounce_plus_rise_ms"] < 20.0
    assert pdn["wearable_budget_300mA_GCC_0x74"]["tps7a0233_vout_min_headroom_ok"]
    (out_dir / "results.json").write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
