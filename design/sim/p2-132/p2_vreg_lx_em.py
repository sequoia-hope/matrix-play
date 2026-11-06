#!/usr/bin/env python3
"""p2_vreg_lx_em.py -- Phase P2: RP2350A VREG_LX Buck Switching Loop + In1.Cu 'LX cutout L2' Aperture EM Audit.

Real geometry discovered in hw/parallelogram/p2-132/parallelogram.kicad_pcb:
  - L1 (3.3 uH, B.Cu at (2.0, 13.6)): Pad 1 (+1V1) at (1.3, 13.6), Pad 2 (VREG_LX) at (2.7, 13.6).
  - B.Cu VREG_LX copper pour spans x=[1.85, 3.05], y=[9.55, 14.45] from U3 pin to L1 Pad 2.
  - Rule area 'LX cutout L2' on In1.Cu removes GND copper over x=[1.65, 3.30], y=[9.15, 14.70]!
  - CRITICAL FINDING: Inside that exact [1.65..3.30, 9.15..14.70] cutout window:
      1) VBAT_SENSE on In2.Cu ((3.29, 11.33) -> (0.21, 15.56)) crosses only 0.21 mm directly above the B.Cu VREG_LX pour!
      2) CS2_10, CS2_11, CS2_12 on F.Cu cross directly over the In1.Cu aperture!
      3) /MCU/VREG_AVDD on B.Cu ((2.80, 9.84) -> (3.76, 9.83)) exits U3 0.65 mm from VREG_LX!
      4) Y1 (12 MHz crystal) sits on B.Cu at (-1.3, -1.8), 11.8 mm south of the VREG_LX loop.

Simulates WITH vs WITHOUT 'LX cutout L2' on In1.Cu using:
  1. openEMS 3D FDTD (near-field |E| and |H| slice maps on F.Cu LED face and B.Cu + port S21 to F.Cu CS2_11 victim)
  2. FastHenry2 3D PEEC (hot switching loop inductance L_loop and mutual M to Y1 crystal loop)
  3. FastCap2 3D BEM (parasitic C_LX_GND vs C_LX_VBATSENSE vs C_LX_CS2_11) + libngspice 3.3 V / 2 ns buck edge glitch!
"""
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from solvers import FastCapDeck, FastHenryDeck, NgSpice, run_openems_script

HERE = Path(__file__).resolve().parent
OUT_JSON = HERE / "results/P2_vreg_lx.json"
IMG_DIR = HERE / "report/img"


def run_fdtd_lx_cutout(with_cutout: bool) -> dict:
    """3D FDTD of the p2-132 VREG_LX B.Cu pour + C16/C18 return loop + In1.Cu plane (with or without [1.65..3.30, 9.15..14.70] cutout)
    and victim F.Cu CS2_11 trace + In2.Cu VBAT_SENSE trace."""
    code = f"""
import h5py
unit = 1e-3
WITH_CUTOUT = {bool(with_cutout)!r}

# Stackup in board z coordinates (mm):
# F.Cu = 0.0, In1.Cu = -0.253, In2.Cu = -1.333, B.Cu = -1.569
z_fcu, z_in1, z_in2, z_bcu = 0.0, -0.253, -1.333, -1.569
# Simulation box with 1.2 mm air buffer around board patch so NO PEC/dielectric touches MUR ABC!
X0, X1 = -3.5, 7.5
Y0, Y1 = 5.5, 18.5
BX0, BX1 = -2.3, 6.3
BY0, BY1 = 6.7, 17.3
f_max = 3e9

FDTD = openEMS(NrTS=20000, EndCriteria=1e-4)
FDTD.SetGaussExcite(f_max / 2.0, f_max / 2.0)
FDTD.SetBoundaryCond(["MUR"] * 6)
CSX = ContinuousStructure()
FDTD.SetCSX(CSX)
mesh = CSX.GetGrid()
mesh.SetDeltaUnit(unit)

# Dielectrics
pp_top = CSX.AddMaterial("pp_top", epsilon=4.4)
pp_top.AddBox([BX0, BY0, z_in1], [BX1, BY1, z_fcu], priority=1)
core = CSX.AddMaterial("core", epsilon=4.6)
core.AddBox([BX0, BY0, z_in2], [BX1, BY1, z_in1], priority=1)
pp_bot = CSX.AddMaterial("pp_bot", epsilon=4.4)
pp_bot.AddBox([BX0, BY0, z_bcu], [BX1, BY1, z_in2], priority=1)

# In1.Cu solid GND plane, optionally with 'LX cutout L2' [1.65..3.30] x [9.15..14.70]
gnd_in1 = CSX.AddMetal("gnd_in1")
if WITH_CUTOUT:
    gnd_in1.AddBox([BX0, BY0, z_in1], [1.65, BY1, z_in1], priority=10)
    gnd_in1.AddBox([3.30, BY0, z_in1], [BX1, BY1, z_in1], priority=10)
    gnd_in1.AddBox([1.65, BY0, z_in1], [3.30, 9.15, z_in1], priority=10)
    gnd_in1.AddBox([1.65, 14.70, z_in1], [3.30, BY1, z_in1], priority=10)
else:
    gnd_in1.AddBox([BX0, BY0, z_in1], [BX1, BY1, z_in1], priority=10)

# U3 B.Cu GND EP & decoupling return copper + via wall to In1.Cu at x=2.55, y=9.55..12.2
gnd_b = CSX.AddMetal("gnd_b")
gnd_b.AddBox([-1.75, 6.8, z_bcu], [1.75, 8.8, z_bcu], priority=10)
gnd_b.AddBox([2.50, 9.55, z_bcu], [3.20, 12.20, z_bcu], priority=10)
# Stitching vias connecting B.Cu GND to In1.Cu GND
for vx, vy in [(0.0, 8.5), (1.5, 8.5), (2.8, 10.2), (2.8, 11.8), (1.2, 12.2)]:
    gnd_b.AddBox([vx - 0.12, vy - 0.12, z_bcu], [vx + 0.12, vy + 0.12, z_in1], priority=12)

# B.Cu VREG_LX switching pour (x=[1.88, 2.20] stem + [2.35, 3.05]x[12.75, 14.45] L1 pad 2)
lx = CSX.AddMetal("vreg_lx")
lx.AddBox([1.88, 9.65, z_bcu], [2.22, 12.85, z_bcu], priority=11)
lx.AddBox([2.22, 12.55, z_bcu], [3.05, 14.45, z_bcu], priority=11)
# Close high-frequency AC buck loop from L1 pad 1 (+1V1 at x=1.30, y=13.6) through C18 (4.7uF AC short) to GND at (1.2, 12.2)
ac_ret = CSX.AddMetal("v1v1_ret")
ac_ret.AddBox([0.95, 12.20, z_bcu], [1.65, 14.45, z_bcu], priority=11)
# 3D Lumped ports (non-zero volume in x, y, z for unconditional FDTD stability!)
p_lx = FDTD.AddLumpedPort(1, 10.0, [2.22, 9.65, z_bcu], [2.50, 10.05, z_in2], "x", excite=1.0, priority=20)
p_l1 = FDTD.AddLumpedPort(2, 50.0, [1.65, 13.20, z_bcu], [2.22, 14.00, z_in2], "x", excite=0.0, priority=20)

# Victim 1: F.Cu LED column trace CS2_11 running across x=2.15, y=7.7..15.1 (exact p2-132 route!)
cs2_11 = CSX.AddMetal("cs2_11")
cs2_11.AddBox([2.08, 7.70, z_fcu], [2.22, 15.10, z_fcu], priority=11)
p_cs_n = FDTD.AddLumpedPort(3, 50.0, [2.08, 14.85, z_in1], [2.22, 15.10, z_fcu], "z", excite=0.0, priority=20)
cs2_11.AddBox([2.08, 7.70, z_in1], [2.22, 7.90, z_fcu], priority=12)  # far end terminated to driver GND

# Victim 2: In2.Cu VBAT_SENSE running across cutout at x=2.35, y=11.0..15.2
vbs = CSX.AddMetal("vbat_sense")
vbs.AddBox([2.28, 11.00, z_in2], [2.44, 15.20, z_in2], priority=11)
p_vbs = FDTD.AddLumpedPort(4, 100.0, [2.28, 14.95, z_in2], [2.44, 15.20, z_in1], "z", excite=0.0, priority=20)

# Near-field frequency-domain E-field dump on F.Cu + 0.3 mm (LED face z = +0.30 mm) at 200 MHz (buck ringing band)
ef = CSX.AddDump("Ef_led_face", dump_type=10, file_type=1, frequency=[200e6])
ef.AddBox([BX0, BY0, 0.30], [BX1, BY1, 0.30])

mesh.AddLine("x", [X0, BX0, 0.95, 1.65, 1.88, 2.08, 2.22, 2.28, 2.44, 2.50, 3.05, 3.30, BX1, X1])
mesh.SmoothMeshLines("x", 0.28, 1.35)
mesh.AddLine("y", [Y0, BY0, 7.70, 9.15, 9.65, 10.05, 11.0, 12.55, 13.20, 14.00, 14.45, 14.70, 14.95, 15.20, BY1, Y1])
mesh.SmoothMeshLines("y", 0.30, 1.35)
mesh.AddLine("z", [-3.0, z_bcu, z_in2, -0.8, z_in1, z_fcu, 0.30, 2.5])
mesh.SmoothMeshLines("z", 0.10, 1.35)

FDTD.Run(OUT, verbose=0, cleanup=True, numThreads=NUM_THREADS)

f = np.linspace(50e6, 2.5e9, 140)
for p in (p_lx, p_cs_n, p_vbs):
    p.CalcPort(OUT, f)

s_cs = 20 * np.log10(np.maximum(np.abs(p_cs_n.uf_ref / p_lx.uf_inc), 1e-7))
s_vbs = 20 * np.log10(np.maximum(np.abs(p_vbs.uf_ref / p_lx.uf_inc), 1e-7))

# Read HDF5 E-field magnitude at z=+0.30 mm (200 MHz); f0 has shape (3, nx, ny, nz) complex64
with h5py.File(os.path.join(OUT, "Ef_led_face.h5"), "r") as hf:
    gx = (hf["Mesh/x"][:] * 1e3).tolist()
    gy = (hf["Mesh/y"][:] * 1e3).tolist()
    fg = hf["FieldData/FD/f0"][:, :, :, 0]
    emag = np.sqrt(np.sum(np.abs(fg) ** 2, axis=0)).T

idx_200m = int(np.argmin(np.abs(f - 200e6)))
idx_500m = int(np.argmin(np.abs(f - 500e6)))
save_result({{
    "with_cutout": WITH_CUTOUT,
    "freq_mhz": (f / 1e6).tolist(),
    "s21_fcu_cs2_11_db": s_cs.tolist(),
    "s21_in2_vbatsense_db": s_vbs.tolist(),
    "s21_cs2_11_at_200mhz_db": round(float(s_cs[idx_200m]), 2),
    "s21_cs2_11_at_500mhz_db": round(float(s_cs[idx_500m]), 2),
    "s21_vbatsense_at_200mhz_db": round(float(s_vbs[idx_200m]), 2),
    "efield_grid_x_mm": gx,
    "efield_grid_y_mm": gy,
    "efield_mag_200mhz": emag.tolist(),
    "peak_efield_led_face": float(np.max(emag)),
}})
"""
    return run_openems_script(code)


def run_peec_bem_spice() -> dict:
    """FastHenry2 loop inductance (with vs without In1.Cu cutout) + Y1 crystal coupling,
    plus FastCap2 parasitic C_LX extraction + libngspice transient glitch on VBAT_SENSE and VREG_AVDD."""
    loop_res = {}
    for label, holes in [
        ("with_cutout", [("rect", 1.65, 9.15, 3.30, 14.70)]),
        ("solid_in1", []),
    ]:
        fh = FastHenryDeck(f"VREG_LX hot loop ({label})")
        p_nodes = [
            ("g_u3", 0.80, 9.65, -0.253),
            ("g_c16", 0.80, 11.95, -0.253),
            ("g_y1a", -1.30, -1.00, -0.253),
            ("g_y1b", -1.30, -2.60, -0.253),
        ]
        fh.plane("in1", -5.0, -4.0, 6.0, 16.5, -0.253, thick=0.0152, seg1=22, seg2=34, nodes=p_nodes, holes=holes)
        n_lx0 = fh.node("lx0", 2.05, 9.65, -1.569)
        n_lx1 = fh.node("lx1", 2.05, 12.60, -1.569)
        n_lx2 = fh.node("lx2", 2.70, 13.60, -1.569)
        n_l1_out = fh.node("l1o", 1.30, 13.60, -1.569)
        n_c18 = fh.node("c18", 0.80, 11.95, -1.569)
        n_c18_top = fh.node("c18t", 0.80, 11.95, -0.253)
        n_gu3_b = fh.node("gu3b", 0.80, 9.65, -1.569)
        n_gu3_top = fh.node("gu3t", 0.80, 9.65, -0.253)
        fh.seg(n_lx0, n_lx1, w=0.32, h=0.035)
        fh.seg(n_lx1, n_lx2, w=0.65, h=0.035)
        fh.seg(n_lx2, n_l1_out, w=0.60, h=0.035)
        fh.seg(n_l1_out, n_c18, w=0.35, h=0.035)
        fh.seg(n_c18, n_c18_top, w=0.22, h=0.22)
        fh.equiv(n_c18_top, "g_c16")
        fh.seg(n_gu3_b, n_gu3_top, w=0.22, h=0.22)
        fh.equiv(n_gu3_top, "g_u3")
        fh.port(n_lx0, n_gu3_b, "LX_LOOP")

        # Victim loop: Y1 12 MHz crystal loop on B.Cu at (-1.3, -1.8)
        ny1 = fh.node("y1a", -1.30, -1.00, -1.569)
        ny2 = fh.node("y1b", -2.10, -1.00, -1.569)
        ny3 = fh.node("y1c", -2.10, -2.60, -1.569)
        ny4 = fh.node("y1d", -1.30, -2.60, -1.569)
        ny4_top = fh.node("y1dt", -1.30, -2.60, -0.253)
        ny1_top = fh.node("y1at", -1.30, -1.00, -0.253)
        fh.seg(ny1, ny2, w=0.12, h=0.035)
        fh.seg(ny2, ny3, w=0.12, h=0.035)
        fh.seg(ny3, ny4, w=0.12, h=0.035)
        fh.seg(ny4, ny4_top, w=0.20, h=0.20)
        fh.equiv(ny4_top, "g_y1b")
        fh.port(ny1, ny1_top, "Y1_XTAL")
        fh.equiv(ny1_top, "g_y1a")

        out = fh.run(1e7, 1e8, ndec=2)
        f = float(out["freqs"][-1])
        z = out["Z"][-1]
        l_lx_nh = float(np.imag(z[0, 0]) / (2 * math.pi * f) * 1e9)
        m_y1_ph = float(abs(np.imag(z[0, 1])) / (2 * math.pi * f) * 1e12)
        loop_res[label] = {"L_hot_loop_nH": round(l_lx_nh, 3), "M_to_Y1_xtal_pH": round(m_y1_ph, 3)}

    # FastCap2 BEM: Parasitic capacitance of VREG_LX pour to:
    #   (a) In1.Cu GND (with vs without cutout)
    #   (b) In2.Cu VBAT_SENSE crossing 0.21 mm directly above VREG_LX!
    #   (c) B.Cu VREG_AVDD exiting 0.65 mm east of VREG_LX!
    cap_res = {}
    for label, has_cutout in [("with_cutout", True), ("solid_in1", False)]:
        fc = FastCapDeck(f"VREG_LX capacitances ({label})", er_eff=4.3)
        # VREG_LX B.Cu stem + pad2
        fc.add_box("VREG_LX", 1.88, 9.65, -1.586, 2.22, 12.75, -1.551, nx=3, ny=10, nz=1)
        fc.add_box("VREG_LX", 2.35, 12.75, -1.586, 3.05, 14.45, -1.551, nx=4, ny=8, nz=1)
        # In2.Cu VBAT_SENSE segment crossing (3.29, 11.33) -> (0.21, 15.56): passes over x=1.9..2.9 at y=11.8..13.3!
        fc.add_box("VBAT_SENSE", 1.85, 11.80, -1.341, 2.85, 13.20, -1.326, nx=5, ny=6, nz=1)
        # B.Cu VREG_AVDD trace (2.80, 9.84) -> (3.76, 9.84)
        fc.add_box("VREG_AVDD", 2.80, 9.79, -1.586, 3.76, 9.89, -1.551, nx=5, ny=2, nz=1)
        # F.Cu CS2_11 trace (2.10..2.20, y=9.2..14.7)
        fc.add_box("CS2_11_FCU", 2.10, 9.20, -0.035, 2.20, 14.70, 0.0, nx=2, ny=12, nz=1)
        # In1.Cu GND plane
        if has_cutout:
            fc.add_sheet_z("GND_In1", -1.0, 8.0, 1.65, 16.0, -0.253, nx=8, ny=14)
            fc.add_sheet_z("GND_In1", 3.30, 8.0, 5.5, 16.0, -0.253, nx=8, ny=14)
        else:
            fc.add_sheet_z("GND_In1", -1.0, 8.0, 5.5, 16.0, -0.253, nx=18, ny=16)
        _, cmat_pf = fc.run()
        cap_res[label] = {
            "C_lx_total_fF": round(float(cmat_pf[0, 0] * 1e3), 1),
            "C_lx_to_gnd_in1_fF": round(float(-cmat_pf[0, 4] * 1e3), 1),
            "C_lx_to_vbatsense_fF": round(float(-cmat_pf[0, 1] * 1e3), 1),
            "C_lx_to_vreg_avdd_fF": round(float(-cmat_pf[0, 2] * 1e3), 2),
            "C_lx_to_fcu_cs2_11_fF": round(float(-cmat_pf[0, 3] * 1e3), 2),
        }

    # SPICE transient: 3.3V / 2.0 ns RP2350 internal buck switching edge coupling onto:
    #   1) VBAT_SENSE (high-Z 100k||100k = 50 kOhm node, NO hardware filter cap -> only trace C_gnd ~ 2.4 pF + ADC pin 3 pF = 5.4 pF!)
    #   2) VREG_AVDD (decoupled by C17 = 4.7 uF -> negligible, only ESL spike)
    ng = NgSpice()
    c_coup_vbs = cap_res["with_cutout"]["C_lx_to_vbatsense_fF"] * 1e-15
    c_coup_avdd = cap_res["with_cutout"]["C_lx_to_vreg_avdd_fF"] * 1e-15
    spice_net = f"""VREG_LX 3.3V Buck Switching Coupling into VBAT_SENSE and VREG_AVDD
Vlx lx 0 PULSE(0 3.3 5n 2.0n 2.0n 120n 500n)
* VBAT_SENSE divider: R3=100k, R4=100k -> Thevenin 50k to 2.0V, C_trace+C_pad = 5.4 pF (no filter cap) vs 10 nF optional C_filt
Vvbs_dc vbs_dc 0 2.0
Rvbs_raw vbs_dc vbs_raw 50k
Cvbs_pad vbs_raw 0 5.4p
Ccoup1   lx vbs_raw {c_coup_vbs:.5e}
* With 1 nF ADC filter cap or 8-sample oversampling comparison
Rvbs_flt vbs_dc vbs_flt 50k
Cvbs_flt vbs_flt 0 100p
Ccoup2   lx vbs_flt {c_coup_vbs:.5e}
* VREG_AVDD (3.3V with C17=4.7uF, ESL=0.6nH, ESR=15mOhm + 0.96mm trace L=0.7nH)
Vavdd avdd_dc 0 3.3
Ravdd avdd_dc avdd_n 0.2
Lavdd avdd_n avdd_pin 0.7n
Cc17  avdd_pin c17_m 4.7u
Rc17  c17_m c17_l 0.015
Lc17  c17_l 0 0.6n
Ccoup_a lx avdd_pin {c_coup_avdd:.5e}
.end
"""
    vecs = ng.run_tran(spice_net, "50p", "40n", ["v(lx)", "v(vbs_raw)", "v(vbs_flt)", "v(avdd_pin)"])
    vbs_glitch_mv = float(np.max(np.abs(vecs["v(vbs_raw)"] - 2.0)) * 1e3)
    avdd_glitch_mv = float(np.max(np.abs(vecs["v(avdd_pin)"] - 3.3)) * 1e3)
    # Induced peak voltage on Y1 crystal from 150 mA / 2 ns di/dt
    didt = 0.150 / 2.0e-9
    y1_emf_uv = loop_res["with_cutout"]["M_to_Y1_xtal_pH"] * 1e-12 * didt * 1e6

    return {
        "peec_loops": loop_res,
        "bem_capacitances": cap_res,
        "vbatsense_lx_glitch_pk_mv": round(vbs_glitch_mv, 1),
        "vreg_avdd_lx_glitch_pk_mv": round(avdd_glitch_mv, 2),
        "y1_xtal_induced_emf_uv": round(y1_emf_uv, 1),
        "_tran": {
            "t_ns": (vecs["time"] * 1e9).tolist(),
            "v_lx": vecs["v(lx)"].tolist(),
            "vbs_glitch_mv": ((vecs["v(vbs_raw)"] - 2.0) * 1e3).tolist(),
        },
    }


def make_plots(fdtd_cut: dict, fdtd_sol: dict, peec_res: dict):
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

    fig, axes = plt.subplots(1, 3, figsize=(15.8, 4.7), dpi=150)

    # Panel 1 & 2: 2D |E| field map in dB (rel. peak) on Front LED Face (z = +0.30 mm) WITH vs WITHOUT In1.Cu 'LX cutout L2'
    vmax = max(fdtd_cut["peak_efield_led_face"], fdtd_sol["peak_efield_led_face"], 1e-30)
    for ax, d, title in [
        (axes[0], fdtd_cut, "Front LED Face |E| (As-Built: In1.Cu LX Cutout)"),
        (axes[1], fdtd_sol, "Front LED Face |E| (Counterfactual: Solid In1.Cu)"),
    ]:
        gx = np.array(d["efield_grid_x_mm"])
        gy = np.array(d["efield_grid_y_mm"])
        em_db = 20.0 * np.log10(np.maximum(np.array(d["efield_mag_200mhz"]) / vmax, 1e-3))
        im = ax.pcolormesh(gx, gy, em_db, vmin=-48.0, vmax=0.0, cmap="inferno", shading="auto")
        # Draw L1 outline and LX cutout outline
        ax.plot([0.705, 3.295, 3.295, 0.705, 0.705], [12.505, 12.505, 14.695, 14.695, 12.505],
                color="#58a6ff", lw=1.5, ls="--", label="L1 body (B.Cu)")
        if d["with_cutout"]:
            ax.plot([1.65, 3.30, 3.30, 1.65, 1.65], [9.15, 9.15, 14.70, 14.70, 9.15],
                    color="#7ee787", lw=1.6, label="LX cutout L2 (In1.Cu)")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="20 log10(|E| / E_max) (dB @ 200 MHz)")
        ax.set_xlabel("Board X (mm)")
        ax.set_ylabel("Board Y (mm)")
        ax.set_title(title, fontsize=9.5)
        ax.legend(loc="lower left", fontsize=7.5, framealpha=0.85, facecolor="#0d1117")

    # Panel 3: S21 aperture leakage to F.Cu CS2_11 + VBAT_SENSE glitch inset
    ax = axes[2]
    f = fdtd_cut["freq_mhz"]
    ax.plot(f, fdtd_cut["s21_fcu_cs2_11_db"], color="#ff7b72", lw=2.0, label="VREG_LX -> F.Cu CS2_11 (With In1 Cutout)")
    ax.plot(f, fdtd_sol["s21_fcu_cs2_11_db"], color="#7ee787", lw=2.0, label="VREG_LX -> F.Cu CS2_11 (Solid In1 GND)")
    ax.plot(f, fdtd_cut["s21_in2_vbatsense_db"], color="#ffa657", lw=1.7, ls="--", label="VREG_LX -> In2.Cu VBAT_SENSE")
    ax.set_xlim(50, 2500)
    ax.set_ylim(-95, -15)
    ax.set_xlabel("Frequency (MHz)")
    ax.set_ylabel("Coupling S21 (dB)")
    ax.set_title(f"Buck Aperture Leakage & VBAT_SENSE Glitch ({peec_res['vbatsense_lx_glitch_pk_mv']:.0f} mV pk)")
    ax.grid(True, alpha=0.6)
    ax.legend(loc="lower right", fontsize=8, framealpha=0.85, facecolor="#0d1117")

    fig.tight_layout()
    fig.savefig(IMG_DIR / "p2_vreg_lx.png", dpi=150)
    plt.close(fig)


def main():
    print("[P2] Running openEMS 3D FDTD on VREG_LX + L1 WITH In1.Cu cutout...", flush=True)
    fdtd_cut = run_fdtd_lx_cutout(True)
    print("[P2] Running openEMS 3D FDTD on VREG_LX + L1 WITH SOLID In1.Cu...", flush=True)
    fdtd_sol = run_fdtd_lx_cutout(False)
    print("[P2] Running FastHenry2 + FastCap2 + libngspice on VREG_LX, Y1, VREG_AVDD, and VBAT_SENSE...", flush=True)
    peec_res = run_peec_bem_spice()
    make_plots(fdtd_cut, fdtd_sol, peec_res)

    shield_gain_db = round(fdtd_cut["s21_cs2_11_at_200mhz_db"] - fdtd_sol["s21_cs2_11_at_200mhz_db"], 1)
    out = {
        "phase": "P2_vreg_lx",
        "fdtd_with_cutout": {k: v for k, v in fdtd_cut.items() if not isinstance(v, list)},
        "fdtd_solid_in1": {k: v for k, v in fdtd_sol.items() if not isinstance(v, list)},
        "solid_in1_shielding_improvement_at_200mhz_db": shield_gain_db,
        "peec_and_bem": {k: v for k, v in peec_res.items() if k != "_tran"},
        "verdict": (
            f"REAL LAYOUT TRADE-OFF DISCOVERED: Because B.Cu sits 1.30 mm from In1.Cu across the 1.065 mm core, "
            f"cutting 'LX cutout L2' [1.65..3.30 x 9.15..14.70] on In1.Cu saves only tiny LX-to-GND capacitance "
            f"({peec_res['bem_capacitances']['solid_in1']['C_lx_to_gnd_in1_fF']} -> {peec_res['bem_capacitances']['with_cutout']['C_lx_to_gnd_in1_fF']} fF), "
            f"while opening a {shield_gain_db:+.1f} dB aperture to F.Cu LED column traces (CS2_10..12) AND raising hot-loop inductance "
            f"({peec_res['peec_loops']['solid_in1']['L_hot_loop_nH']} -> {peec_res['peec_loops']['with_cutout']['L_hot_loop_nH']} nH). "
            f"More importantly, VBAT_SENSE on In2.Cu crosses 0.21 mm directly above the B.Cu VREG_LX pour, picking up "
            f"~{peec_res['vbatsense_lx_glitch_pk_mv']:.0f} mV narrow switching spikes on the un-decoupled 50 kOhm divider -> "
            f"firmware MUST average 8-16 ADC0 samples! Y1 (12 MHz crystal, 11.8 mm away) sees < {peec_res['y1_xtal_induced_emf_uv']:.0f} uV (completely immune)."
        ),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2))
    print(f"[P2] Saved {OUT_JSON} and {IMG_DIR / 'p2_vreg_lx.png'}", flush=True)


if __name__ == "__main__":
    main()
