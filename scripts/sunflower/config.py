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
import dataclasses
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
    # Layout options (2026-11-06 USB-C study): an LED at the very centre, a USB-C receptacle on B.Cu in place of the
    # wire pads, and the light sensor at the rim (x, y, rot on F.Cu) instead of the centre.
    centre_led: bool = False
    usb_c: bool = False
    als_pos: Tuple[float, float, float] | None = None
    vbat_en_gpio: int = 14  # RP2350 GPIO switching the VBAT divider (s2-110-usbc: GPIO28, pin 42, routes beside VBAT_SENSE)
    # Bring-up pads (2026-11-07, s2-110-usbc): test points for UART1, I2C0, VBUS and a spare ADC GPIO (TP_GPIOS),
    # and board ID straps. ID_GPIOS are read with internal pull-ups; the ones in id_tied are tied to GND (bit = 0),
    # the rest left open (bit = 1). Boards without straps read all ones.
    test_pads: bool = False
    id_tied: Tuple[int, ...] = ()
    # LED field: "vogel" (sunflower spiral, n LEDs) or "penrose" (Penrose P3 rhomb vertices at the pattern explorer's
    # dense pitch, cropped to R_OUT; n is then the vertex count left after the keepouts, see penrose_points).
    layout: str = "vogel"
    # One LED driven straight from RP2350 GPIOs (pn-dense-1d): the GPIOs on its (R, G, B) cathodes, each through a
    # series resistor, anode on +3V3 (design/parts/direct-led.md). It sits at the board centre; the matrix keeps n LEDs.
    direct_led: Tuple[int, ...] = ()

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


def _v(name, rev, n, wedges, summary, **kw):
    drivers = (DRV_W,) if len(wedges) == 1 else (DRV_W, DRV_E)
    return VariantSpec(name=name, title_rev=rev, n=n, drivers=drivers, summary=summary, wedges=wedges, **kw)


# Four 4-layer density tiers on the identical 38 mm disc (annulus area ~911 mm^2):
VARIANTS = {
    "s1-66": _v("s1-66", "S1", 66, (6,), "66 XL-1615RGBC-RF LEDs in a 38 mm sunflower, 1x AW20198QNR, 4-layer JLCPCB"),
    "s2-88": _v("s2-88", "S2", 88, (4, 4), "88 XL-1615RGBC-RF LEDs in a 38 mm sunflower, 2x AW20198QNR, 4-layer JLCPCB"),
    "s2-110": _v("s2-110", "S3", 110, (5, 5), "110 XL-1615RGBC-RF LEDs in a 38 mm sunflower, 2x AW20198QNR, 4-layer JLCPCB"),
    "s2-132": _v("s2-132", "S4", 132, (6, 6), "132 XL-1615RGBC-RF LEDs in a 38 mm sunflower, 2x AW20198QNR, 4-layer JLCPCB"),
}
# Routes that allow vias in SMD pads (order with POFV) are kept beside the no-via-in-pad routes, as their own folders.
for _k in ("s1-66", "s2-88"):
    _s = VARIANTS[_k]
    VARIANTS[_k + "-pofv"] = _v(_k + "-pofv", _s.title_rev, _s.n, _s.wedges, _s.summary + " (vias in pads, POFV)")
# USB-C study: s2-110 with a USB-C receptacle at the south rim, an LED at the centre and the light sensor at the top rim.
VARIANTS["s2-110-usbc"] = _v("s2-110-usbc", "S3C", 110, (5, 5),
                             "110 XL-1615RGBC-RF LEDs in a 38 mm sunflower with a centre LED, USB-C on the back, light sensor at the rim, 2x AW20198QNR, 4-layer JLCPCB",
                             centre_led=True, usb_c=True, als_pos=(0.0, -18.20, 0.0), vbat_en_gpio=28,
                             test_pads=True, id_tied=(19,))

# Board ID straps: GPIO19..21 (RP2350A pins 31-33, east side, next to the exposed GND pad). Read with pull-ups,
# ID = GPIO19 | GPIO20 << 1 | GPIO21 << 2; a tied pin reads 0. 0b111 = no straps (every board before s2-110-usbc).
ID_GPIOS = (19, 20, 21)
# Test-pad GPIOs on boards with test_pads: UART1 on GPIO24 (TX) and GPIO25 (RX), and GPIO29, the only free ADC input.
TP_GPIOS = {24: "UART_TX", 25: "UART_RX", 29: "GPIO29_TP"}
# Where pcb_gen puts the bring-up pads and the ID net tie on B.Cu (x, y from the board centre).
TEST_PAD_POS = {"TP5": (3.0, -17.0), "TP11": (8.5, 15.4), "TP12": (10.25, 14.15),
                "TP13": (6.5, 16.25), "TP14": (10.5, -4.6), "TP15": (10.9, -6.9), "TP16": (10.75, -9.75),
                "NT1": (3.75, -10.0)}

# USB-C receptacle (HRO TYPE-C-31-M-12, LCSC C165948) on B.Cu at the south rim, mouth out, its front 0.3 mm past the
# rim. The north rim was tried first (next to the battery socket) but its courtyard lands on U3 at every angle there.
USB_FP = "round_pendant:USB_C_Receptacle_HRO_TYPE-C-31-M-12"
USB_LIB_SRC = "/usr/share/kicad/footprints/Connector_USB.pretty"
USB_POS = (0.0, 15.60, 180.0)  # 180: flipping to B.Cu mirrors the footprint front-to-back, and the mouth must face out
# Its shell legs and pegs go through the board: (x, y) relative to the footprint, and a keepout radius for front LED
# centres (hole half-length + 0.3 mm + half the LED's courtyard).
USB_HOLES = [(-4.32, -3.13, 2.35), (4.32, -3.13, 2.35), (-4.32, 1.05, 2.15), (4.32, 1.05, 2.15),
             (-2.89, -2.60, 1.75), (2.89, -2.60, 1.75)]
# Light sensor at the top rim on F.Cu (pads 0.27 mm inside the edge), and the keepout it needs from LED centres.
ALS_TOP = (0.0, -18.20, 0.0)
ALS_KEEPOUT = 2.50


def front_keepouts(spec) -> List[Tuple[float, float, float]]:
    """Discs (x, y, r) that front LED centres must stay out of for this variant."""
    k = []
    if spec.usb_c:
        ux, uy, _ = USB_POS  # flip (mirror y) then 180 deg maps (hx, hy) to (-hx, hy); the holes are symmetric in x
        k += [(ux + hx, uy + hy, r) for hx, hy, r in USB_HOLES]
    if spec.als_pos:
        k.append((spec.als_pos[0], spec.als_pos[1], ALS_KEEPOUT))
    return k


# Battery connector: Molex PicoBlade 1.25 mm 2-pin right-angle SMD, 53261-0271 (LCSC C177225). The "JST 1.25" plug on most
# small LiPo cells is this friction-fit PicoBlade style, not latching JST GH. On B.Cu with its mouth (mounting-tab side)
# facing the board centre at the north-west rim; (x, y, orientation) relative to the board centre, the same on every tier.
BAT_FP = "round_pendant:Molex_PicoBlade_53261-0271_1x02-1MP_P1.25mm_Horizontal"  # copied from KiCad's Connector_Molex by lib_gen.py
BAT_LIB_SRC = "/usr/share/kicad/footprints/Connector_Molex.pretty"
BAT_LCSC, BAT_MPN, BAT_MFR, BAT_VALUE = "C177225", "53261-0271", "Molex", "PicoBlade 2P"
BAT_POS = (-11.40, -10.20, 250.0)  # jst_site.py: NW rim, plug entering from the board-centre side (user's choice); the 9.4 mm-wide socket can't face the rim there


def sunflower_points(n: int, centre: bool = False, keepouts=()) -> List[Tuple[float, float]]:
    """Vogel spiral. centre=True puts LED 0 at (0, 0) and starts the spiral from the middle (no R_IN hole);
    keepouts are discs (x, y, r) that LED centres are pushed out of (through-holes, rim parts on F.Cu)."""
    raw = []
    if centre:
        for k in range(n):
            r = R_OUT * math.sqrt(k / (n - 1))
            th = k * GOLDEN
            raw.append([r * math.cos(th), r * math.sin(th)])
    else:
        q2 = (R_IN / R_OUT) ** 2
        a = n * q2 / (1.0 - q2)
        for k in range(n):
            r = R_OUT * math.sqrt((k + a) / (n - 1 + a))
            th = k * GOLDEN
            raw.append([r * math.cos(th), r * math.sin(th)])
    r_in = 0.0 if centre else R_IN
    # Relax: XL-1615's courtyard is 2.0 x 1.9 mm at 0 deg, so a dense spiral's diagonal neighbours can overlap.
    # Push overlapping pairs apart along the axis of least overlap; a no-op where the spiral is already clear.
    cw, ch = CRT_W + 0.06, CRT_H + 0.06
    for _ in range(600):
        moved = False
        for i in range(n):
            if centre and i == 0:
                continue
            for kx, ky, kr in keepouts:
                dx, dy = raw[i][0] - kx, raw[i][1] - ky
                d = math.hypot(dx, dy)
                if d < kr:
                    moved = True
                    if d < 1e-6:
                        dx, dy, d = 0.0, -1.0, 1.0
                    raw[i][0] = kx + dx / d * (kr + 0.01)
                    raw[i][1] = ky + dy / d * (kr + 0.01)
        for i in range(n):
            for j in range(i + 1, n):
                dx = raw[j][0] - raw[i][0]
                dy = raw[j][1] - raw[i][1]
                ox, oy = cw - abs(dx), ch - abs(dy)
                if ox > 0 and oy > 0:
                    moved = True
                    # LED 0 stays put at the centre when centre=True: its neighbour takes the whole move
                    wi, wj = (0.0, 1.0) if (centre and i == 0) else (0.5, 0.5)
                    if ox < oy:
                        s = (ox + 0.01) * (1 if dx >= 0 else -1)
                        raw[i][0] -= s * wi
                        raw[j][0] += s * wj
                    else:
                        s = (oy + 0.01) * (1 if dy >= 0 else -1)
                        raw[i][1] -= s * wi
                        raw[j][1] += s * wj
        for p in raw:
            r = math.hypot(*p)
            if r > R_OUT:
                p[0] *= R_OUT / r
                p[1] *= R_OUT / r
            elif r < r_in:
                p[0] *= r_in / max(r, 1e-6)
                p[1] *= r_in / max(r, 1e-6)
        if not moved:
            break
    pts = [(round(round(x / 0.05) * 0.05, 4), round(round(y / 0.05) * 0.05, 4)) for x, y in raw]
    for i in range(n):
        for j in range(i + 1, n):
            if abs(pts[i][0] - pts[j][0]) < CRT_W and abs(pts[i][1] - pts[j][1]) < CRT_H:
                raise SystemExit(f"sunflower {n}: LED courtyards {i} and {j} still overlap after relaxation")
    for i, (x, y) in enumerate(pts):
        for kx, ky, kr in keepouts:
            if math.hypot(x - kx, y - ky) < kr - 0.04:
                raise SystemExit(f"sunflower {n}: LED {i} at ({x}, {y}) inside keepout ({kx}, {ky}, r={kr})")
    return pts


# Penrose P3 field (2026-11-07, pn-dense): the pattern explorer's "Penrose tiling (P3 rhombs)" view at dense density with
# LEDs at rhomb vertices (design/study/pattern-explorer/index.html, penroseTris / genPenrose). The same Robinson-triangle
# deflation of a ten-triangle sun, scaled so the closest two vertices are exactly the explorer's dense pitch for
# XL-1615 (hypot(1.6 + 0.25, 1.5 + 0.25) = 2.547 mm), centre vertex at the board centre, cropped to R_OUT. Vertices
# inside a keepout are dropped, not pushed, so the tiling stays exact. At this orientation the closest pairs lie at
# 18/54/90/126/162 deg and no two XL-1615 courtyards (2.0 x 1.9 mm at 0 deg) overlap.
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PENROSE_PITCH = math.hypot(1.6 + 0.25, 1.5 + 0.25)
PENROSE_LEVEL = 4      # deflations; level 4 at this pitch covers r = 22 mm (rhomb edge 4.12 mm)
PENROSE_SNAP = 0.025   # ultraroute's cell; moves a vertex at most 0.018 mm


def penrose_triangles(level: int):
    """Robinson triangles (kind, A, B, C) of the deflated sun, unit circumradius (kind 0 = thin/half-kite, 1 = thick)."""
    tris = []
    for i in range(10):
        B = (math.cos((2 * i - 1) * math.pi / 10), math.sin((2 * i - 1) * math.pi / 10))
        C = (math.cos((2 * i + 1) * math.pi / 10), math.sin((2 * i + 1) * math.pi / 10))
        if i % 2 == 0:
            B, C = C, B
        tris.append((0, (0.0, 0.0), B, C))

    def lerp(a, b, t):
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

    for _ in range(level):
        res = []
        for c, A, B, C in tris:
            if c == 0:
                P = lerp(A, B, 1 / PHI)
                res += [(0, C, P, B), (1, P, C, A)]
            else:
                Q, R = lerp(B, A, 1 / PHI), lerp(B, C, 1 / PHI)
                res += [(1, R, C, A), (1, Q, R, B), (0, R, Q, A)]
        tris = res
    return tris


def penrose_scale(level: int = PENROSE_LEVEL) -> float:
    """mm per unit so the closest two vertices are PENROSE_PITCH apart."""
    v = list({(round(p[0], 9), round(p[1], 9)): p for t in penrose_triangles(level) for p in t[1:]}.values())
    d = min(math.dist(a, b) for i, a in enumerate(v) for b in v[i + 1:])
    return PENROSE_PITCH / d


def penrose_edges(level: int = PENROSE_LEVEL) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
    """Rhomb edges in board mm (CA and AB of each Robinson triangle; BC is the rhomb's diagonal), for silk guides."""
    s = penrose_scale(level)
    e = set()
    for _, A, B, C in penrose_triangles(level):
        for p, q in ((C, A), (A, B)):
            p, q = (round(p[0] * s, 4), round(p[1] * s, 4)), (round(q[0] * s, 4), round(q[1] * s, 4))
            e.add(tuple(sorted((p, q))))
    return sorted(e)


def penrose_points(keepouts=(), r_max: float = R_OUT, report: bool = False) -> List[Tuple[float, float]]:
    s = penrose_scale()
    v = {(round(p[0], 9), round(p[1], 9)): p for t in penrose_triangles(PENROSE_LEVEL) for p in t[1:]}
    pts, dropped = [], []
    for x, y in sorted(v.values(), key=lambda p: (round(math.hypot(*p), 9), math.atan2(p[1], p[0]))):
        x, y = x * s, y * s
        if math.hypot(x, y) > r_max + 1e-6:
            continue
        if any(math.hypot(x - kx, y - ky) < kr for kx, ky, kr in keepouts):
            dropped.append((round(x, 3), round(y, 3)))
            continue
        pts.append((round(round(x / PENROSE_SNAP) * PENROSE_SNAP, 4), round(round(y / PENROSE_SNAP) * PENROSE_SNAP, 4)))
    if report:
        print(f"penrose: level {PENROSE_LEVEL}, scale {s:.4f} mm/unit, rhomb edge {s * PHI ** -PENROSE_LEVEL:.3f} mm, "
              f"{len(pts)} LEDs within r {r_max} mm, {len(dropped)} dropped in keepouts: {dropped}")
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            if abs(pts[i][0] - pts[j][0]) < CRT_W and abs(pts[i][1] - pts[j][1]) < CRT_H:
                raise SystemExit(f"penrose: LED courtyards {i} {pts[i]} and {j} {pts[j]} overlap")
    return pts


def spec_points(spec) -> List[Tuple[float, float]]:
    if spec.layout == "penrose":
        pts = penrose_points(front_keepouts(spec))
        if spec.direct_led:
            pts = [p for p in pts if p != (0.0, 0.0)]  # the centre vertex is the direct LED, not a matrix cell
        assert len(pts) == spec.n, (len(pts), spec.n)
        return pts
    return sunflower_points(spec.n, centre=spec.centre_led, keepouts=front_keepouts(spec))


# Dense Penrose study: s2-110-usbc's board (USB-C on the back, centre LED, rim light sensor, test pads, PicoBlade socket,
# 2x AW20198) with the LED field taken from the pattern explorer's dense Penrose P3 vertices. ID strap GPIO20 (ID = 5).
VARIANTS["pn-dense"] = _v("pn-dense", "PN", 0, (4, 4),
                          "Dense Penrose P3 tiling of XL-1615RGBC-RF LEDs (rhomb vertices, 2.547 mm closest pair) in a 38 mm disc, USB-C on the back, light sensor at the rim, 2x AW20198QNR, 4-layer JLCPCB",
                          centre_led=True, usb_c=True, als_pos=(0.0, -18.20, 0.0), vbat_en_gpio=28,
                          test_pads=True, id_tied=(20,), layout="penrose")
VARIANTS["pn-dense"] = dataclasses.replace(
    VARIANTS["pn-dense"], n=len(penrose_points(front_keepouts(VARIANTS["pn-dense"]))))
VARIANTS["pn-dense"] = dataclasses.replace(
    VARIANTS["pn-dense"], summary=VARIANTS["pn-dense"].summary.replace("Dense", f"{VARIANTS['pn-dense'].n}-LED dense", 1))


# One driver: pn-dense with U2 removed and the centre LED driven directly by GPIO7/8/9 (R, G, B), so the matrix is 66 LEDs
# in 6 wedges of 11 on U1. Board ID strap GPIO21 (ID = 3).
VARIANTS["pn-dense-1d"] = _v("pn-dense-1d", "PN1", 66, (6,),
                             "67-LED dense Penrose P3 tiling of XL-1615RGBC-RF LEDs (rhomb vertices, 2.547 mm closest pair) in a 38 mm disc: 66 on 1x AW20198QNR, the centre LED on RP2350 GPIO7/8/9; USB-C on the back, light sensor at the rim, 4-layer JLCPCB",
                             centre_led=True, usb_c=True, als_pos=(0.0, -18.20, 0.0), vbat_en_gpio=28,
                             test_pads=True, id_tied=(21,), layout="penrose", direct_led=(7, 8, 9))
assert len(spec_points(VARIANTS["pn-dense-1d"])) == 66
# Direct LED parts: the LED takes the next D number after the matrix; R/G/B series resistors (direct-led.md).
DIRECT_R = (("R80", "150R"), ("R81", "510R"), ("R82", "510R"))


def _nn(spec):
    pts = spec_points(spec)
    return [min(math.hypot(x - u, y - v) for j, (u, v) in enumerate(pts) if j != i) for i, (x, y) in enumerate(pts)]


def nn_min(spec) -> float:
    return min(_nn(spec))


def nn_mean(spec) -> float:
    d = _nn(spec)
    return sum(d) / len(d)


def build_led_cells(spec: VariantSpec) -> List[dict]:
    """Ordered LED records D1..DN by (driver, triplet, SW), each with its sunflower position."""
    pts = spec_points(spec)
    n_w = sum(spec.wedges)
    assert spec.n <= 11 * n_w, (spec.n, spec.wedges)
    # Angle measured clockwise on screen from due south (y down), so the first half of the sort is the west half.
    def ang(p):
        return (math.atan2(-p[0], p[1])) % (2 * math.pi)  # south=0, west=pi/2, north=pi, east=3pi/2
    order = sorted(range(spec.n), key=lambda i: ang(pts[i]))
    # Wedges of 11 when n fills them (the Vogel tiers); otherwise n is spread as evenly as it goes (sizes differ by at
    # most one, each <= 11), so a wedge's unused SW lines are simply left unconnected at its driver.
    sizes = [spec.n // n_w + (1 if w < spec.n % n_w else 0) for w in range(n_w)]
    starts = [sum(sizes[:w]) for w in range(n_w)]
    wedges = [order[a: a + k] for a, k in zip(starts, sizes)]
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
