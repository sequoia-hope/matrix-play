#!/usr/bin/env python3
"""config.py -- 38 mm round sunflower (Vogel spiral) LED layouts and B.Cu driver specs for hw/sunflower/<variant>/.

Forked from scripts/parallelogram/config.py: same AW20198QNR drivers, XL-1615RGBC-RF LEDs, 4-layer JLC rules.
The LED field is a Vogel spiral, r_n = R_OUT * sqrt((n + a) / (N + a)), theta_n = n * golden angle, with `a`
chosen so the innermost LED sits at R_IN: the centre is left for the Q2 light sensor and density is uniform
over the annulus R_IN..R_OUT.

Matrix map (any LED may take any (CS triplet, SW) cell, so this is a free assignment): LEDs sorted by angle
are cut into N/11 wedges of 11. Each wedge is one CS triplet (R, G, B cathodes run radially, like the
parallelogram's columns); within a wedge the SW index is the LED's radius rank 1..11, so SW_m joins the m-th
ring across all of a driver's wedges (circumferential, like the parallelogram's rows). Driver 1 takes the
western wedges, driver 2 the eastern.
"""
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parents[2]
OX, OY = 100.0, 100.0

DIAMETER = 38.0
R_BOARD = DIAMETER / 2.0
R_OUT = 17.20        # outermost LED centre: XL-1615 pad corner ~0.9 mm from centre -> ~0.9 mm to the rim
R_IN = 2.40          # innermost LED centre: leaves the centre for Q2 (ALS, 1.7 x 0.8 mm) on F.Cu
GOLDEN = math.pi * (3.0 - math.sqrt(5.0))  # 137.508 deg

# Round pouch cell behind the board (403535, 35 mm round, by the user's choice for round-pendant); wired to BT1.
CELL_D = 35.0

# XL-1615RGBC-RF courtyard (lib footprint), LEDs at 0 deg
CRT_W, CRT_H = 2.0, 1.9


@dataclass(frozen=True)
class DriverSpec:
    idx: int          # 1..2 -> matrix{idx}.kicad_sch
    uref: str
    rset_ref: str
    cap_base: int
    bulk_ref: str | None
    ad1_strap: str
    ad0_strap: str
    i2c_hex: str
    bcu_pos: Tuple[float, float, float]  # (x_rel, y_rel, rot_deg) on B.Cu
    tiles: Tuple = ()                    # unused (parallelogram tiling); kept for sch_gen compatibility


@dataclass(frozen=True)
class VariantSpec:
    name: str
    title_rev: str
    n: int
    drivers: Tuple[DriverSpec, ...]
    summary: str
    led_type: str = "XL-1615RGBC"
    # wedges per driver (each wedge = one CS triplet of 11 LEDs)
    wedges: Tuple[int, ...] = (6,)

    @property
    def n_leds(self) -> int:
        return self.n

    @property
    def hw_dir(self) -> Path:
        return ROOT / "hw/sunflower" / self.name

    # Legacy fields some forked tools print
    @property
    def px(self) -> float:
        return round(nn_mean(self), 3)

    @property
    def py(self) -> float:
        return round(nn_min(self), 3)


DRV_W = DriverSpec(1, "U1", "R30", 31, "C30", "GND", "GND", "0x20", (-12.60, 3.00, 90.0))
DRV_E = DriverSpec(2, "U2", "R33", 41, "C40", "VSYS", "VSYS", "0x25", (12.60, 3.00, 90.0))


def _v(name, rev, n, wedges, summary):
    drivers = (DRV_W,) if len(wedges) == 1 else (DRV_W, DRV_E)
    return VariantSpec(name=name, title_rev=rev, n=n, drivers=drivers, summary=summary, wedges=wedges)


# Four 4-layer density tiers on the identical 38 mm disc (annulus area ~911 mm^2):
VARIANTS = {
    "s1-66": _v("s1-66", "S1", 66, (6,), "66 XL-1615RGBC-RF LEDs in a 38 mm sunflower, 1x AW20198QNR, 4-layer JLCPCB"),
    "s2-88": _v("s2-88", "S2", 88, (4, 4), "88 XL-1615RGBC-RF LEDs in a 38 mm sunflower, 2x AW20198QNR, 4-layer JLCPCB"),
    "s2-110": _v("s2-110", "S3", 110, (5, 5), "110 XL-1615RGBC-RF LEDs in a 38 mm sunflower, 2x AW20198QNR, 4-layer JLCPCB"),
    "s2-132": _v("s2-132", "S4", 132, (6, 6), "132 XL-1615RGBC-RF LEDs in a 38 mm sunflower, 2x AW20198QNR, 4-layer JLCPCB"),
}


def sunflower_points(n: int) -> List[Tuple[float, float]]:
    q2 = (R_IN / R_OUT) ** 2
    a = n * q2 / (1.0 - q2)
    raw = []
    for k in range(n):
        r = R_OUT * math.sqrt((k + a) / (n - 1 + a))
        th = k * GOLDEN
        raw.append([r * math.cos(th), r * math.sin(th)])
    # Relax: XL-1615's courtyard is 2.0 x 1.9 mm at 0 deg, so a dense spiral's diagonal neighbours can overlap.
    # Push overlapping pairs apart along the axis of least overlap; a no-op where the spiral is already clear.
    cw, ch = CRT_W + 0.06, CRT_H + 0.06
    for _ in range(400):
        moved = False
        for i in range(n):
            for j in range(i + 1, n):
                dx = raw[j][0] - raw[i][0]
                dy = raw[j][1] - raw[i][1]
                ox, oy = cw - abs(dx), ch - abs(dy)
                if ox > 0 and oy > 0:
                    moved = True
                    if ox < oy:
                        s = (ox / 2 + 0.005) * (1 if dx >= 0 else -1)
                        raw[i][0] -= s
                        raw[j][0] += s
                    else:
                        s = (oy / 2 + 0.005) * (1 if dy >= 0 else -1)
                        raw[i][1] -= s
                        raw[j][1] += s
        for p in raw:
            r = math.hypot(*p)
            if r > R_OUT:
                p[0] *= R_OUT / r
                p[1] *= R_OUT / r
            elif r < R_IN:
                p[0] *= R_IN / max(r, 1e-6)
                p[1] *= R_IN / max(r, 1e-6)
        if not moved:
            break
    pts = [(round(round(x / 0.05) * 0.05, 4), round(round(y / 0.05) * 0.05, 4)) for x, y in raw]
    for i in range(n):
        for j in range(i + 1, n):
            if abs(pts[i][0] - pts[j][0]) < CRT_W and abs(pts[i][1] - pts[j][1]) < CRT_H:
                raise SystemExit(f"sunflower {n}: LED courtyards {i} and {j} still overlap after relaxation")
    return pts


def _nn(spec):
    pts = sunflower_points(spec.n)
    return [min(math.hypot(x - u, y - v) for j, (u, v) in enumerate(pts) if j != i) for i, (x, y) in enumerate(pts)]


def nn_min(spec) -> float:
    return min(_nn(spec))


def nn_mean(spec) -> float:
    d = _nn(spec)
    return sum(d) / len(d)


def build_led_cells(spec: VariantSpec) -> List[dict]:
    """Ordered LED records D1..DN by (driver, triplet, SW), each with its sunflower position."""
    pts = sunflower_points(spec.n)
    assert spec.n == 11 * sum(spec.wedges), (spec.n, spec.wedges)
    # Angle measured clockwise on screen from due south (y down), so the first half of the sort is the west half.
    def ang(p):
        return (math.atan2(-p[0], p[1])) % (2 * math.pi)  # south=0, west=pi/2, north=pi, east=3pi/2
    order = sorted(range(spec.n), key=lambda i: ang(pts[i]))
    wedges = [order[11 * w: 11 * w + 11] for w in range(spec.n // 11)]
    recs = []
    w = 0
    for drv, n_w in zip(spec.drivers, spec.wedges):
        for t in range(n_w):
            members = sorted(wedges[w], key=lambda i: math.hypot(*pts[i]))
            for m, i in enumerate(members):
                recs.append((drv, t + 1, m + 1, i))
            w += 1
    recs.sort(key=lambda r: (r[0].idx, r[1], r[2]))
    cells = []
    for d_num, (drv, trip, sw, i) in enumerate(recs, start=1):
        x, y = pts[i]
        cells.append({
            "ref": f"D{d_num}", "d_num": d_num, "drv_idx": drv.idx, "uref": drv.uref,
            "triplet": trip, "sw": sw, "col": trip - 1, "row": sw - 1, "x_mm": x, "y_mm": y,
        })
    assert len(cells) == spec.n
    return cells


if __name__ == "__main__":
    for k, s in VARIANTS.items():
        print(f"{k}: n={s.n} nn_min={nn_min(s):.2f} nn_mean={nn_mean(s):.2f} mm^2/LED={math.pi*(R_OUT**2-R_IN**2)/s.n:.1f}")
