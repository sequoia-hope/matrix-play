#!/usr/bin/env python3
"""solvers.py -- Wrappers for openEMS (FDTD), FastHenry2 (PEEC), FastCap2 (BEM), and libngspice."""
import ctypes
import json
import math
import os
import re
import subprocess
import tempfile
import threading
from pathlib import Path

import numpy as np

OPENEMS_PY = Path("/home/sequoia/micromamba/envs/openems/bin/python")
FASTHENRY_BIN = Path("/home/sequoia/opt/FastHenry2/bin/fasthenry")
FASTCAP_BIN = Path("/home/sequoia/opt/FastCap2/bin/fastcap")
NGSPICE_SO = "/usr/lib/x86_64-linux-gnu/libngspice.so.0"

SIGMA_CU = 5.8e7         # S/m annealed copper
SIGMA_PLATED = 4.7e7     # S/m ED foil / plated barrel
EPS0 = 8.8541878128e-12
MU0 = 4e-7 * math.pi


# ---------------------------------------------------------------------------
# Closed-form reference formulas (for P0 Known-Answer Calibration)
# ---------------------------------------------------------------------------
def hammerstad_microstrip_z0(w_mm: float, h_mm: float, er: float, t_mm: float = 0.0) -> tuple[float, float]:
    """Hammerstad & Jensen (1980) microstrip Z0 (Ohm) and effective permittivity eps_eff."""
    u = w_mm / h_mm
    if t_mm > 0:
        th = t_mm / h_mm
        du1 = (th / math.pi) * math.log(1.0 + (4.0 * math.e) / (th * (1.0 / math.tanh(math.sqrt(6.517 * u))) ** 2))
        du_r = 0.5 * du1 * (1.0 + 1.0 / math.cosh(math.sqrt(er - 1.0)))
        u = u + du_r
    a = 1.0 + (1.0 / 49.0) * math.log((u**4 + (u / 52.0) ** 2) / (u**4 + 0.432)) + (1.0 / 18.7) * math.log(1.0 + (u / 18.1) ** 3)
    b = 0.564 * ((er - 0.9) / (er + 3.0)) ** 0.053
    er_eff = 0.5 * (er + 1.0) + 0.5 * (er - 1.0) * (1.0 + 10.0 / u) ** (-a * b)
    f_u = 6.0 + (2.0 * math.pi - 6.0) * math.exp(-((30.666 / u) ** 0.7528))
    z0_air = 60.0 * math.log(f_u / u + math.sqrt(1.0 + (2.0 / u) ** 2))
    return z0_air / math.sqrt(er_eff), er_eff


def rect_bar_loop_inductance_nh(a_mm: float, b_mm: float, w_mm: float, h_mm: float) -> float:
    """Exact Grover low-frequency inductance (nH) of an a x b rectangular loop of rectangular cross-section w x h."""
    a = a_mm * 1e-3
    b = b_mm * 1e-3
    gmd = 0.2235 * (w_mm + h_mm) * 1e-3
    d = math.hypot(a, b)
    term_a = a * math.log(2.0 * a / gmd) - a * math.log((a + d) / b)
    term_b = b * math.log(2.0 * b / gmd) - b * math.log((b + d) / a)
    l_h = (MU0 / math.pi) * (term_a + term_b + 2.0 * d - 2.0 * (a + b))
    return float(l_h * 1e9)


# ---------------------------------------------------------------------------
# FastHenry2 runner
# ---------------------------------------------------------------------------
class FastHenryDeck:
    def __init__(self, title: str, sigma: float = SIGMA_CU):
        self.title = title
        self.sigma = sigma
        self.lines = [
            f"* {title}",
            ".units mm",
            f".default sigma={sigma / 1000.0:.6e}",
        ]
        self._id = 0
        self.ports = []

    def node(self, name: str, x: float, y: float, z: float) -> str:
        nm = name if name[0] in "Nn" else f"N_{name}"
        self.lines.append(f"{nm} x={x:.5f} y={y:.5f} z={z:.5f}")
        return nm

    def seg(self, n1: str, n2: str, w: float, h: float, nwinc: int = 3, nhinc: int = 3, sigma: float | None = None) -> str:
        self._id += 1
        en = f"E{self._id}"
        u1 = n1 if n1[0] in "Nn" else f"N_{n1}"
        u2 = n2 if n2[0] in "Nn" else f"N_{n2}"
        s_str = f" sigma={sigma / 1000.0:.6e}" if sigma else ""
        self.lines.append(f"{en} {u1} {u2} w={w:.5f} h={h:.5f} nwinc={nwinc} nhinc={nhinc}{s_str}")
        return en

    def plane(
        self,
        name: str,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        z: float,
        thick: float,
        seg1: int,
        seg2: int,
        nodes: list[tuple[str, float, float, float]] = (),
        holes: list[tuple[str, float, float, float, float]] = (),
        sigma: float | None = None,
    ) -> str:
        gn = name if name[0] in "Gg" else f"G_{name}"
        s_str = f" sigma={sigma / 1000.0:.6e}" if sigma else f" sigma={self.sigma / 1000.0:.6e}"
        hdr = (
            f"{gn} x1={x0:.4f} y1={y0:.4f} z1={z:.4f} "
            f"x2={x1:.4f} y2={y0:.4f} z2={z:.4f} "
            f"x3={x1:.4f} y3={y1:.4f} z3={z:.4f} "
            f"thick={thick:.5f} seg1={seg1} seg2={seg2}{s_str}"
        )
        parts = [hdr]
        for nd, nx, ny, nz in nodes:
            nm = nd if nd[0] in "Nn" else f"N_{nd}"
            parts.append(f"+ {nm} ({nx:.4f},{ny:.4f},{nz:.4f})")
        for kind, hx0, hy0, hx1, hy1 in holes:
            if kind == "rect":
                parts.append(f"+ hole rect ({hx0:.4f},{hy0:.4f},{z:.4f},{hx1:.4f},{hy1:.4f},{z:.4f})")
        self.lines.extend(parts)
        return gn

    def equiv(self, *nodes: str):
        nms = [n if n[0] in "Nn" else f"N_{n}" for n in nodes]
        self.lines.append(".equiv " + " ".join(nms))

    def port(self, n_plus: str, n_minus: str, pname: str = "P1"):
        p1 = n_plus if n_plus[0] in "Nn" else f"N_{n_plus}"
        p2 = n_minus if n_minus[0] in "Nn" else f"N_{n_minus}"
        self.lines.append(f".external {p1} {p2} {pname}")
        self.ports.append(pname)

    def run(self, fmin: float, fmax: float, ndec: int = 4) -> dict:
        deck_txt = "\n".join(self.lines + [f".freq fmin={fmin:.6e} fmax={fmax:.6e} ndec={ndec}", ".end", ""])
        with tempfile.TemporaryDirectory(prefix="fh_") as td:
            td_p = Path(td)
            inp = td_p / "deck.inp"
            inp.write_text(deck_txt)
            proc = subprocess.run(
                [str(FASTHENRY_BIN), "deck.inp"],
                cwd=td_p,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if proc.returncode != 0:
                raise RuntimeError(f"FastHenry failed ({proc.returncode}):\n{proc.stdout}\n{proc.stderr}")
            zc = (td_p / "Zc.mat").read_text()
        return parse_zc_mat(zc)


def parse_zc_mat(text: str) -> dict:
    """Parse FastHenry Zc.mat into {freqs: [...], Z: np.ndarray(nf, np, np)}."""
    freqs = []
    mats = []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    i = 0
    while i < len(lines):
        m = re.match(r"Impedance matrix for frequency\s*=\s*([0-9.eE+-]+)\s*(\d+)\s*x\s*(\d+)", lines[i])
        if m:
            f = float(m.group(1))
            nr, nc = int(m.group(2)), int(m.group(3))
            mat = np.zeros((nr, nc), dtype=np.complex128)
            for r in range(nr):
                i += 1
                toks = lines[i].replace("j", "").split()
                for c in range(nc):
                    re_v = float(toks[2 * c])
                    im_v = float(toks[2 * c + 1])
                    mat[r, c] = re_v + 1j * im_v
            freqs.append(f)
            mats.append(mat)
        i += 1
    return {"freqs": np.array(freqs), "Z": np.array(mats)}


# ---------------------------------------------------------------------------
# FastCap2 runner
# ---------------------------------------------------------------------------
class FastCapDeck:
    """Electrostatic panel model in mm (converted to m for FastCap MKS; result scaled by er_eff in fF / pF)."""

    def __init__(self, title: str, er_eff: float = 1.0):
        self.title = title
        self.er_eff = er_eff
        self.conds: dict[str, list[list[tuple[float, float, float]]]] = {}

    def add_box(self, cond: str, x0: float, y0: float, z0: float, x1: float, y1: float, z1: float, nx: int = 4, ny: int = 4, nz: int = 1):
        """Add all 6 faces of a rectangular prism [x0..x1] x [y0..y1] x [z0..z1] (mm), subdivided."""
        panels = self.conds.setdefault(cond, [])
        xs = np.linspace(min(x0, x1), max(x0, x1), nx + 1)
        ys = np.linspace(min(y0, y1), max(y0, y1), ny + 1)
        zs = np.linspace(min(z0, z1), max(z0, z1), nz + 1)
        # Top & bottom faces
        for i in range(nx):
            for j in range(ny):
                panels.append([(xs[i], ys[j], zs[-1]), (xs[i + 1], ys[j], zs[-1]), (xs[i + 1], ys[j + 1], zs[-1]), (xs[i], ys[j + 1], zs[-1])])
                panels.append([(xs[i], ys[j], zs[0]), (xs[i], ys[j + 1], zs[0]), (xs[i + 1], ys[j + 1], zs[0]), (xs[i + 1], ys[j], zs[0])])
        # Side faces
        if abs(z1 - z0) > 1e-4:
            for i in range(nx):
                for k in range(nz):
                    panels.append([(xs[i], ys[0], zs[k]), (xs[i + 1], ys[0], zs[k]), (xs[i + 1], ys[0], zs[k + 1]), (xs[i], ys[0], zs[k + 1])])
                    panels.append([(xs[i], ys[-1], zs[k]), (xs[i], ys[-1], zs[k + 1]), (xs[i + 1], ys[-1], zs[k + 1]), (xs[i + 1], ys[-1], zs[k])])
            for j in range(ny):
                for k in range(nz):
                    panels.append([(xs[0], ys[j], zs[k]), (xs[0], ys[j], zs[k + 1]), (xs[0], ys[j + 1], zs[k + 1]), (xs[0], ys[j + 1], zs[k])])
                    panels.append([(xs[-1], ys[j], zs[k]), (xs[-1], ys[j + 1], zs[k]), (xs[-1], ys[j + 1], zs[k + 1]), (xs[-1], ys[j], zs[k + 1])])

    def add_sheet_z(self, cond: str, x0: float, y0: float, x1: float, y1: float, z: float, nx: int = 12, ny: int = 12):
        panels = self.conds.setdefault(cond, [])
        xs = np.linspace(min(x0, x1), max(x0, x1), nx + 1)
        ys = np.linspace(min(y0, y1), max(y0, y1), ny + 1)
        for i in range(nx):
            for j in range(ny):
                panels.append([(xs[i], ys[j], z), (xs[i + 1], ys[j], z), (xs[i + 1], ys[j + 1], z), (xs[i], ys[j + 1], z)])

    def run(self) -> tuple[list[str], np.ndarray]:
        """Returns (names, C_pF_maxwell) scaled by er_eff."""
        names = list(self.conds.keys())
        lines = [f"0 {self.title}"]
        for idx, nm in enumerate(names, start=1):
            for q in self.conds[nm]:
                pts = " ".join(f"{p[0] * 1e-3:.7e} {p[1] * 1e-3:.7e} {p[2] * 1e-3:.7e}" for p in q)
                lines.append(f"Q {idx} {pts}")
        with tempfile.TemporaryDirectory(prefix="fc_") as td:
            td_p = Path(td)
            qui = td_p / "model.qui"
            qui.write_text("\n".join(lines) + "\n")
            proc = subprocess.run(
                [str(FASTCAP_BIN), "-o2", "model.qui"],
                cwd=td_p,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if proc.returncode != 0:
                raise RuntimeError(f"FastCap failed ({proc.returncode}):\n{proc.stdout}\n{proc.stderr}")
            out = proc.stdout
        # Parse CAPACITANCE MATRIX, every unit is picofarads (or attofarads / femtofarads -- check header!)
        scale_pf = 1.0
        m_u = re.search(r"CAPACITANCE MATRIX,\s*(\w+)", out)
        if m_u:
            unit_w = m_u.group(1).lower()
            if "atto" in unit_w:
                scale_pf = 1e-6
            elif "femto" in unit_w:
                scale_pf = 1e-3
            elif "pico" in unit_w:
                scale_pf = 1.0
            elif "nano" in unit_w:
                scale_pf = 1e3
        n = len(names)
        cmat = np.zeros((n, n), dtype=float)
        in_mat = False
        rows_read = 0
        for ln in out.splitlines():
            if "CAPACITANCE MATRIX" in ln:
                in_mat = True
                continue
            if in_mat:
                toks = ln.split()
                if len(toks) >= n + 2 and toks[1].isdigit():
                    r = int(toks[1]) - 1
                    vals = [float(x) for x in toks[-n:]]
                    cmat[r, :] = vals
                    rows_read += 1
                    if rows_read == n:
                        break
        if rows_read != n:
            raise RuntimeError(f"Failed to parse FastCap matrix ({rows_read}/{n}):\n{out[-1500:]}")
        return names, cmat * scale_pf * self.er_eff


# ---------------------------------------------------------------------------
# openEMS subprocess helper (runs inside micromamba openems env)
# ---------------------------------------------------------------------------
def run_openems_script(script_code: str, env_extra: dict[str, str] | None = None, timeout: int = 600) -> dict:
    with tempfile.TemporaryDirectory(prefix="oems_") as td:
        td_p = Path(td)
        out_dir = td_p / "sim_out"
        out_dir.mkdir()
        res_json = td_p / "result.json"
        wrapper = f"""import json, math, os, sys
import numpy as np
from CSXCAD import ContinuousStructure
from openEMS import openEMS

OUT = {str(out_dir)!r}
RESULT_JSON = {str(res_json)!r}
NUM_THREADS = int(os.environ.get("RESERVED_CORES", "4"))

def save_result(obj):
    with open(RESULT_JSON, "w") as fp:
        json.dump(obj, fp, indent=2)

{script_code}
"""
        scr_p = td_p / "run_sim.py"
        scr_p.write_text(wrapper)
        env = os.environ.copy()
        env.setdefault("OMP_NUM_THREADS", env.get("RESERVED_CORES", "4"))
        if env_extra:
            env.update(env_extra)
        proc = subprocess.run(
            [str(OPENEMS_PY), str(scr_p)],
            cwd=td_p,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.returncode != 0 or not res_json.exists():
            raise RuntimeError(
                f"openEMS failed (rc={proc.returncode}):\nSTDOUT:\n{proc.stdout[-2000:]}\nSTDERR:\n{proc.stderr[-2000:]}"
            )
        return json.loads(res_json.read_text())


# ---------------------------------------------------------------------------
# libngspice ctypes wrapper
# ---------------------------------------------------------------------------
class _NgComplex(ctypes.Structure):
    _fields_ = [("cx_real", ctypes.c_double), ("cx_imag", ctypes.c_double)]


class _VectorInfo(ctypes.Structure):
    _fields_ = [
        ("v_name", ctypes.c_char_p),
        ("v_type", ctypes.c_int),
        ("v_flags", ctypes.c_short),
        ("v_realdata", ctypes.POINTER(ctypes.c_double)),
        ("v_compdata", ctypes.POINTER(_NgComplex)),
        ("v_length", ctypes.c_int),
    ]


_SendChar = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
_SendStat = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
_CtrlExit = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_bool, ctypes.c_bool, ctypes.c_int, ctypes.c_void_p)


class NgSpice:
    _inst = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._inst is None:
                obj = super().__new__(cls)
                obj._init_lib()
                cls._inst = obj
            return cls._inst

    def _init_lib(self):
        self.log: list[str] = []
        self.err: str | None = None
        L = ctypes.CDLL(NGSPICE_SO)
        self.lib = L
        L.ngSpice_Init.restype = ctypes.c_int
        L.ngSpice_Circ.argtypes = [ctypes.POINTER(ctypes.c_char_p)]
        L.ngSpice_Circ.restype = ctypes.c_int
        L.ngSpice_Command.argtypes = [ctypes.c_char_p]
        L.ngSpice_Command.restype = ctypes.c_int
        L.ngGet_Vec_Info.argtypes = [ctypes.c_char_p]
        L.ngGet_Vec_Info.restype = ctypes.POINTER(_VectorInfo)
        L.ngSpice_CurPlot.restype = ctypes.c_char_p
        L.ngSpice_AllVecs.argtypes = [ctypes.c_char_p]
        L.ngSpice_AllVecs.restype = ctypes.POINTER(ctypes.c_char_p)

        def on_char(msg, _i, _u):
            s = msg.decode(errors="replace")
            self.log.append(s)
            if s.startswith("stderr Error") or "Error:" in s:
                self.err = s
            return 0

        def on_stat(_m, _i, _u):
            return 0

        def on_exit(status, _im, _q, _i, _u):
            self.err = f"ngspice exit({status})"
            return 0

        self._cbs = (_SendChar(on_char), _SendStat(on_stat), _CtrlExit(on_exit))
        rc = L.ngSpice_Init(self._cbs[0], self._cbs[1], self._cbs[2], None, None, None, None)
        if rc != 0:
            raise RuntimeError(f"ngSpice_Init failed: {rc}")

    def run_tran(self, netlist: str, tstep: str, tstop: str, vec_names: list[str], uic: bool = False) -> dict[str, np.ndarray]:
        self.err = None
        self.log.clear()
        self.lib.ngSpice_Command(b"destroy all")
        self.err = None
        lines = [ln for ln in netlist.strip().splitlines()]
        arr = (ctypes.c_char_p * (len(lines) + 1))()
        for i, ln in enumerate(lines):
            arr[i] = ln.encode()
        arr[len(lines)] = None
        rc = self.lib.ngSpice_Circ(arr)
        if rc != 0 or self.err:
            raise RuntimeError(f"ngSpice_Circ error: {self.err}\n" + "\n".join(self.log[-25:]))
        cmd = f"tran {tstep} {tstop}" + (" uic" if uic else "")
        self.lib.ngSpice_Command(cmd.encode())
        if self.err:
            raise RuntimeError(f"ngSpice tran error: {self.err}\n" + "\n".join(self.log[-25:]))
        out = {}
        for nm in ["time", *vec_names]:
            vi = self.lib.ngGet_Vec_Info(nm.encode())
            if not vi:
                raise RuntimeError(f"Missing ngspice vector {nm!r}")
            v = vi.contents
            out[nm] = np.ctypeslib.as_array(v.v_realdata, shape=(v.v_length,)).copy()
        return out
