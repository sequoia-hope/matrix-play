#!/usr/bin/env python3
"""p0_kat.py -- Phase P0 Known-Answer Calibration Tests across openEMS, FastHenry2, FastCap2, and libngspice."""
import json
import math
from pathlib import Path

import numpy as np

from solvers import (
    FastCapDeck,
    FastHenryDeck,
    NgSpice,
    hammerstad_microstrip_z0,
    rect_bar_loop_inductance_nh,
    run_openems_script,
)

OUT_JSON = Path(__file__).resolve().parent / "results/P0_kat.json"


def kat_openems_microstrip() -> dict:
    """Calibrate openEMS 3D FDTD on JLC04161H-7628 F.Cu over In1.Cu prepreg (w=0.38 mm, h=0.2104 mm, er=4.4)."""
    w_mm, h_mm, er, t_mm = 0.38, 0.2104, 4.4, 0.035
    z0_ref, er_eff_ref = hammerstad_microstrip_z0(w_mm, h_mm, er, t_mm=0.0)
    code = f"""
unit = 1e-3
MSL_len, MSL_w, SUB_t, EPS_R = 16.0, {w_mm}, {h_mm}, {er}
res = 0.045
f_max = 8e9

FDTD = openEMS(NrTS=24000, EndCriteria=1e-4)
FDTD.SetGaussExcite(f_max / 2, f_max / 2)
FDTD.SetBoundaryCond(["PML_8", "PML_8", "MUR", "MUR", "PEC", "MUR"])
CSX = ContinuousStructure()
FDTD.SetCSX(CSX)
mesh = CSX.GetGrid()
mesh.SetDeltaUnit(unit)

Y = 4.0
mesh.AddLine("x", [0.0, MSL_len])
mesh.SmoothMeshLines("x", 0.18)
mesh.AddLine("y", [-Y, -MSL_w/2 - res, -MSL_w/2, 0.0, MSL_w/2, MSL_w/2 + res, Y])
mesh.SmoothMeshLines("y", res, 1.35)
mesh.AddLine("z", [0.0, SUB_t, 3.0])
mesh.SmoothMeshLines("z", res, 1.35)

sub = CSX.AddMaterial("FR4_7628", epsilon=EPS_R)
sub.AddBox([0.0, -Y, 0.0], [MSL_len, Y, SUB_t], priority=1)

port = FDTD.AddMSLPort(1, CSX.AddMetal("msl"),
                       [0.0, -MSL_w/2, SUB_t], [MSL_len, MSL_w/2, 0.0],
                       "x", "z", excite=-1,
                       FeedShift=8*res, MeasPlane_Shift=MSL_len/3,
                       priority=10)

FDTD.Run(OUT, verbose=0, cleanup=True, numThreads=NUM_THREADS)
f = np.linspace(1e9, 5e9, 120)
port.CalcPort(OUT, f)
Zref = np.real(port.Z_ref)
er_fdtd = (299792458.0 * np.real(port.beta) / (2 * np.pi * f)) ** 2
save_result({{
    "Z0_fdtd_ohm": float(np.mean(Zref)),
    "Z0_fdtd_std": float(np.std(Zref)),
    "er_eff_fdtd": float(np.mean(er_fdtd)),
}})
"""
    res = run_openems_script(code)
    err_pct = float(100.0 * abs(res["Z0_fdtd_ohm"] - z0_ref) / z0_ref)
    return {
        "test": "openEMS 3D FDTD 7628 microstrip Z0 vs Hammerstad-Jensen",
        "analytic_ohm": round(float(z0_ref), 3),
        "solver_ohm": round(float(res["Z0_fdtd_ohm"]), 3),
        "er_eff_analytic": round(float(er_eff_ref), 3),
        "er_eff_solver": round(float(res["er_eff_fdtd"]), 3),
        "error_pct": round(err_pct, 2),
        "pass": bool(err_pct < 5.0),
    }


def kat_fasthenry_loop() -> dict:
    """Calibrate FastHenry2 PEEC on a 10 x 6 mm rectangular copper trace loop (w=0.20 mm, h=0.035 mm)."""
    a_mm, b_mm, w_mm, h_mm = 10.0, 6.0, 0.20, 0.035
    l_ref = rect_bar_loop_inductance_nh(a_mm, b_mm, w_mm, h_mm)

    fh = FastHenryDeck("KAT rectangular loop")
    gap = 0.10
    n0 = fh.node("p_plus", 0.0, gap / 2, 0.0)
    n1 = fh.node("c1", 0.0, b_mm / 2, 0.0)
    n2 = fh.node("c2", a_mm, b_mm / 2, 0.0)
    n3 = fh.node("c3", a_mm, -b_mm / 2, 0.0)
    n4 = fh.node("c4", 0.0, -b_mm / 2, 0.0)
    n5 = fh.node("p_minus", 0.0, -gap / 2, 0.0)
    for u, v in [(n0, n1), (n1, n2), (n2, n3), (n3, n4), (n4, n5)]:
        fh.seg(u, v, w=w_mm, h=h_mm, nwinc=3, nhinc=3)
    fh.port(n0, n5, "LOOP")
    out = fh.run(1e5, 1e7, ndec=2)
    f = float(out["freqs"][0])
    z = out["Z"][0, 0, 0]
    l_fh = float((z.imag / (2.0 * math.pi * f)) * 1e9)
    r_dc_ref = float((2.0 * (a_mm + b_mm) * 1e-3) / (5.8e7 * (w_mm * 1e-3) * (h_mm * 1e-3)) * 1e3)
    r_fh = float(z.real * 1e3)
    err_pct = float(100.0 * abs(l_fh - l_ref) / l_ref)
    return {
        "test": "FastHenry2 PEEC 10x6 mm rectangular trace loop vs Grover closed form",
        "analytic_nH": round(l_ref, 3),
        "solver_nH": round(l_fh, 3),
        "R_dc_analytic_mOhm": round(r_dc_ref, 2),
        "R_dc_solver_mOhm": round(r_fh, 2),
        "error_pct": round(err_pct, 2),
        "pass": bool(err_pct < 4.0),
    }


def kat_fastcap_microstrip() -> dict:
    """Calibrate FastCap2 BEM on a 20 mm microstrip line over wide ground vs Hammerstad capacitance per unit length."""
    w_mm, h_mm, l_mm, er = 0.38, 0.2104, 20.0, 4.4
    z0_ref, er_eff = hammerstad_microstrip_z0(w_mm, h_mm, er, t_mm=0.035)
    c_per_m_ref = math.sqrt(er_eff) / (299792458.0 * z0_ref)
    c_tot_ref_pf = c_per_m_ref * (l_mm * 1e-3) * 1e12

    fc = FastCapDeck("KAT microstrip", er_eff=er_eff)
    fc.add_box("trace", 0.0, -w_mm / 2, h_mm, l_mm, w_mm / 2, h_mm + 0.035, nx=32, ny=4, nz=1)
    fc.add_sheet_z("gnd", -2.0, -3.0, l_mm + 2.0, 3.0, 0.0, nx=36, ny=18)
    names, cmat = fc.run()
    c_mut_pf = float(-cmat[0, 1])
    err_pct = float(100.0 * abs(c_mut_pf - c_tot_ref_pf) / c_tot_ref_pf)
    return {
        "test": "FastCap2 BEM 20 mm microstrip capacitance vs Hammerstad C'",
        "analytic_pF": round(float(c_tot_ref_pf), 3),
        "solver_pF": round(c_mut_pf, 3),
        "error_pct": round(err_pct, 2),
        "pass": bool(err_pct < 8.0),
    }


def kat_ngspice_rlc() -> dict:
    """Calibrate libngspice transient RLC underdamped peak overshoot vs exact analytical e^(-pi*zeta/sqrt(1-zeta^2))."""
    l_val, c_val, r_val = 25e-9, 100e-12, 5.0
    z_char = math.sqrt(l_val / c_val)  # 15.81 Ohm
    zeta = 0.5 * r_val / z_char
    v_peak_ref = 1.0 + math.exp(-math.pi * zeta / math.sqrt(1.0 - zeta**2))

    net = f"""KAT RLC step overshoot
V1 in 0 PWL(0 0 10p 1.0 200n 1.0)
R1 in n1 {r_val}
L1 n1 out {l_val}
C1 out 0 {c_val}
.end
"""
    ng = NgSpice()
    vecs = ng.run_tran(net, "20p", "40n", ["v(out)"])
    v_peak_sim = float(np.max(vecs["v(out)"]))
    err_pct = float(100.0 * abs(v_peak_sim - v_peak_ref) / v_peak_ref)
    return {
        "test": "libngspice transient RLC step peak overshoot vs exact closed form",
        "analytic_V": round(float(v_peak_ref), 4),
        "solver_V": round(v_peak_sim, 4),
        "error_pct": round(err_pct, 3),
        "pass": bool(err_pct < 1.0),
    }


def main():
    results = []
    for fn in [kat_openems_microstrip, kat_fasthenry_loop, kat_fastcap_microstrip, kat_ngspice_rlc]:
        print(f"Running {fn.__name__}...", flush=True)
        r = fn()
        status = "PASS" if r["pass"] else "FAIL"
        print(f"[{status}] {r['test']}: err={r['error_pct']}%  ({r})", flush=True)
        results.append(r)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    summary = {"all_passed": all(r["pass"] for r in results), "tests": results}
    OUT_JSON.write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
