#!/usr/bin/env python3
"""config.py -- geometry, skewed LED grid progressions, and B.Cu floorplan specs for hw/parallelogram/<variant>/."""
from dataclasses import dataclass
import os
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parents[2]
OX, OY = 100.0, 100.0

# Parallelogram geometry: 25.0 mm wide x 70.0 mm tip-to-tip (62.0 mm vertical long edges, skew s = +0.32 -> +-4.0 mm).
HALF_W = 12.50       # x in [-12.50, +12.50] -> 25.00 mm wide
HALF_EDGE = 31.00    # y in [-31.00 + 0.32*x, +31.00 + 0.32*x] -> (-12.5,-35.0) to (+12.5,+35.0) = 70.00 mm tip-to-tip
SKEW = 0.32          # dy/dx = +0.32 -> skew angle = atan(0.32) = 17.7447 deg
CORNER_R = 1.00      # 1.0 mm rounded corners on all 4 parallelogram vertices

# Standard prismatic LiPo pouch cell envelope on B.Cu (e.g. 802035 / 102035: 20 x 35 mm, thickness unconstrained).
CELL_W = 20.0
CELL_H = 35.0
CELL_CENTER = (0.0, -4.0)  # Leaves South end-zone (y = +14..+30) clear for hand-soldered BT1 & J1 wire joints!


@dataclass(frozen=True)
class DriverSpec:
    idx: int          # 1..4 -> matrix{idx}.kicad_sch
    uref: str         # U1, U2, U10, U11
    rset_ref: str     # R30, R33, R50, R60
    cap_base: int     # C31..34, C41..44, C51..54, C61..64
    bulk_ref: str | None
    ad1_strap: str    # GND, VSYS, SCL, SDA
    ad0_strap: str    # GND, VSYS, SCL, SDA
    i2c_hex: str      # 0x20..0x2F
    bcu_pos: Tuple[float, float, float]  # (x_rel, y_rel, rot_deg) on B.Cu
    # Rectangular LED sub-tiles driven by this chip: list of (col0, n_cols, row0, n_rows, triplet0_1based)
    tiles: Tuple[Tuple[int, int, int, int, int], ...]


@dataclass(frozen=True)
class VariantSpec:
    name: str
    title_rev: str
    cols: int
    rows: int
    px: float
    py: float
    drivers: Tuple[DriverSpec, ...]
    summary: str
    led_type: str = "XL-1010RGB"
    io_mode: str = "pads"  # "pads" (wire pads) or "usb" (TYPE-C-31-M-22 + JST 1.25 + NW/SE wing buttons)
    usb_s: float = 0.0     # J1 tangential coordinate along South slanted bezel (mm)
    usb_ye: float = 0.0    # J1 origin inset perpendicular to South slanted bezel (mm; mouth at +5.12 mm)
    extra_side_buttons: bool = False  # Add SW5 (USER_C, West-North) & SW6 (USER_D, West-South) EVQP7J01P switches

    @property
    def n_leds(self) -> int:
        return self.cols * self.rows

    @property
    def hw_dir(self) -> Path:
        base = Path(os.environ["PARALLELOGRAM_HW_ROOT"]) if os.environ.get("PARALLELOGRAM_HW_ROOT") else (ROOT / "hw/parallelogram")
        return base / self.name


# Five progressive 4-layer density tiers on the identical 25 x 70 mm parallelogram & 4L JLCPCB promo rules:
#   p1-66:   6 x 11 =  66 RGB LEDs (1x AW20198, XL-1615RGBC-RF 1.6x1.5 mm, 3.70 x 5.20 mm =  4.3 LEDs/cm^2)
#   p2-132:  6 x 22 = 132 RGB LEDs (2x AW20198, XL-1615RGBC-RF 1.6x1.5 mm, 3.70 x 2.60 mm =  8.5 LEDs/cm^2)
#   p3-162:  9 x 18 = 162 RGB LEDs (3x AW20198, XL-1010RGB-YG  1.0x1.0 mm, 2.55 x 3.15 mm = 10.5 LEDs/cm^2)
#   p3-198:  9 x 22 = 198 RGB LEDs (3x AW20198, XL-1010RGB-YG  1.0x1.0 mm, 2.55 x 2.60 mm = 12.8 LEDs/cm^2)
#   p4-264: 12 x 22 = 264 RGB LEDs (4x AW20198, XL-1010RGB-YG  1.0x1.0 mm, 2.02 x 2.60 mm = 17.0 LEDs/cm^2)
VARIANTS = {
    "p1-66": VariantSpec(
        name="p1-66",
        title_rev="P0",
        cols=6,
        rows=11,
        px=3.70,
        py=5.20,
        drivers=(
            DriverSpec(
                1, "U1", "R30", 31, "C30", "GND", "GND", "0x20",
                (0.00, -10.40, 90.0),
                ((0, 6, 0, 11, 1),),
            ),
        ),
        summary="66 XL-1615RGBC-RF LEDs (6x11 skewed grid, 3.70x5.20 mm), 1x AW20198QNR QFN-40, 4-layer JLCPCB standard",
        led_type="XL-1615RGBC",
    ),
    "p2-132": VariantSpec(
        name="p2-132",
        title_rev="P1",
        cols=6,
        rows=22,
        px=3.70,
        py=2.60,
        drivers=(
            DriverSpec(
                1, "U1", "R30", 31, "C30", "GND", "GND", "0x20",
                (0.00, -18.50, 90.0),
                ((0, 6, 0, 11, 1),),
            ),
            DriverSpec(
                2, "U2", "R33", 41, "C40", "VSYS", "VSYS", "0x25",
                (7.40, -8.20, 90.0),
                ((0, 6, 11, 11, 1),),
            ),
        ),
        summary="132 XL-1615RGBC-RF LEDs (6x22 skewed grid, 3.70x2.60 mm), 2x AW20198QNR QFN-40, 4-layer JLCPCB standard",
        led_type="XL-1615RGBC",
    ),
    "p3-162": VariantSpec(
        name="p3-162",
        title_rev="P2",
        cols=9,
        rows=18,
        px=2.55,
        py=3.15,
        drivers=(
            DriverSpec(
                1, "U1", "R30", 31, "C30", "GND", "GND", "0x20",
                (-4.80, -16.20, 90.0),
                ((0, 6, 0, 9, 1),),
            ),
            DriverSpec(
                2, "U2", "R33", 41, "C40", "VSYS", "VSYS", "0x25",
                (-8.00, 15.20, 90.0),
                ((0, 6, 9, 9, 1),),
            ),
            DriverSpec(
                3, "U10", "R50", 51, None, "GND", "SCL", "0x22",
                (6.80, -8.50, 90.0),
                ((6, 3, 0, 9, 1), (6, 3, 9, 9, 4)),
            ),
        ),
        summary="162 RGB LEDs (9x18 skewed grid, 2.55x3.15 mm), 3x AW20198QNR QFN-40, 4-layer JLCPCB standard",
    ),
    "p3-198": VariantSpec(
        name="p3-198",
        title_rev="P3",
        cols=9,
        rows=22,
        px=2.55,
        py=2.60,
        drivers=(
            DriverSpec(
                1, "U1", "R30", 31, "C30", "GND", "GND", "0x20",
                (-4.80, -16.20, 90.0),
                ((0, 6, 0, 11, 1),),
            ),
            DriverSpec(
                2, "U2", "R33", 41, "C40", "VSYS", "VSYS", "0x25",
                (-8.00, 15.20, 90.0),
                ((0, 6, 11, 11, 1),),
            ),
            DriverSpec(
                3, "U10", "R50", 51, None, "GND", "SCL", "0x22",
                (6.80, -8.50, 90.0),
                ((6, 3, 0, 11, 1), (6, 3, 11, 11, 4)),
            ),
        ),
        summary="198 RGB LEDs (9x22 skewed grid, 2.55x2.60 mm), 3x AW20198QNR QFN-40, 4-layer JLCPCB standard",
    ),
    "p4-264": VariantSpec(
        name="p4-264",
        title_rev="P4",
        cols=12,
        rows=22,
        px=2.02,
        py=2.60,
        drivers=(
            DriverSpec(
                1, "U1", "R30", 31, "C30", "GND", "GND", "0x20",
                (-5.80, -19.50, 90.0),
                ((0, 6, 0, 11, 1),),
            ),
            DriverSpec(
                2, "U2", "R33", 41, "C40", "VSYS", "VSYS", "0x25",
                (5.80, -19.50, 90.0),
                ((6, 6, 0, 11, 1),),
            ),
            DriverSpec(
                3, "U10", "R50", 51, None, "GND", "SCL", "0x22",
                (-8.00, 15.20, 90.0),
                ((0, 6, 11, 11, 1),),
            ),
            DriverSpec(
                4, "U11", "R60", 61, None, "GND", "SDA", "0x23",
                (6.80, -6.50, 90.0),
                ((6, 6, 11, 11, 1),),
            ),
        ),
        summary="264 RGB LEDs (12x22 skewed grid, 2.02x2.60 mm), 4x AW20198QNR QFN-40, 4-layer JLCPCB standard",
    ),
    "p1-66-usb": VariantSpec(
        name="p1-66-usb",
        title_rev="P0U",
        cols=6,
        rows=11,
        px=3.70,
        py=5.20,
        drivers=(
            DriverSpec(
                1, "U1", "R30", 31, "C30", "GND", "GND", "0x20",
                (0.00, -10.40, 90.0),
                ((0, 6, 0, 11, 1),),
            ),
        ),
        summary="66 XL-1615RGBC-RF LEDs (6x11), 1x AW20198QNR, USB-C + Micro-JST 1.25 + NW/SE flat-face wing buttons, 4L",
        led_type="XL-1615RGBC",
        io_mode="usb",
        usb_s=-2.90,
        usb_ye=4.85,
    ),
    "p2-132-usb": VariantSpec(
        name="p2-132-usb",
        title_rev="P1U",
        cols=6,
        rows=22,
        px=3.70,
        py=2.60,
        drivers=(
            DriverSpec(
                1, "U1", "R30", 31, "C30", "GND", "GND", "0x20",
                (0.00, -18.50, 90.0),
                ((0, 6, 0, 11, 1),),
            ),
            DriverSpec(
                2, "U2", "R33", 41, "C40", "VSYS", "VSYS", "0x25",
                (7.40, -8.20, 90.0),
                ((0, 6, 11, 11, 1),),
            ),
        ),
        summary="132 XL-1615RGBC-RF LEDs (6x22), 2x AW20198QNR, USB-C + Micro-JST 1.25 + NW/SE flat-face wing buttons, 4L",
        led_type="XL-1615RGBC",
        io_mode="usb",
        usb_s=-2.45,
        usb_ye=3.60,
    ),
    "p2-132-usb6": VariantSpec(
        name="p2-132-usb6",
        title_rev="P1U6",
        cols=6,
        rows=22,
        px=3.70,
        py=2.60,
        drivers=(
            DriverSpec(
                1, "U1", "R30", 31, "C30", "GND", "GND", "0x20",
                (0.00, -18.50, 90.0),
                ((0, 6, 0, 11, 1),),
            ),
            DriverSpec(
                2, "U2", "R33", 41, "C40", "VSYS", "VSYS", "0x25",
                (7.40, -8.20, 90.0),
                ((0, 6, 11, 11, 1),),
            ),
        ),
        summary="132 XL-1615RGBC-RF LEDs (6x22), 2x AW20198QNR, USB-C + Micro-JST 1.25 + NW/SE wing + N/S West side buttons, 4L",
        led_type="XL-1615RGBC",
        io_mode="usb",
        usb_s=-2.45,
        usb_ye=3.60,
        extra_side_buttons=True,
    ),
    "p3-162-usb": VariantSpec(
        name="p3-162-usb",
        title_rev="P2U",
        cols=9,
        rows=18,
        px=2.55,
        py=3.15,
        drivers=(
            DriverSpec(
                1, "U1", "R30", 31, "C30", "GND", "GND", "0x20",
                (-4.80, -16.20, 90.0),
                ((0, 6, 0, 9, 1),),
            ),
            DriverSpec(
                2, "U2", "R33", 41, "C40", "VSYS", "VSYS", "0x25",
                (-9.35, 16.60, 90.0),
                ((0, 6, 9, 9, 1),),
            ),
            DriverSpec(
                3, "U10", "R50", 51, None, "GND", "SCL", "0x22",
                (6.80, -8.50, 90.0),
                ((6, 3, 0, 9, 1), (6, 3, 9, 9, 4)),
            ),
        ),
        summary="162 XL-1010RGB LEDs (9x18), 3x AW20198QNR, USB-C + Micro-JST 1.25 + NW/SE flat-face wing buttons, 4L",
        io_mode="usb",
        usb_s=-2.55,
        usb_ye=4.15,
    ),
    "p3-198-usb": VariantSpec(
        name="p3-198-usb",
        title_rev="P3U",
        cols=9,
        rows=22,
        px=2.55,
        py=2.60,
        drivers=(
            DriverSpec(
                1, "U1", "R30", 31, "C30", "GND", "GND", "0x20",
                (-4.80, -16.20, 90.0),
                ((0, 6, 0, 11, 1),),
            ),
            DriverSpec(
                2, "U2", "R33", 41, "C40", "VSYS", "VSYS", "0x25",
                (-9.35, 16.60, 90.0),
                ((0, 6, 11, 11, 1),),
            ),
            DriverSpec(
                3, "U10", "R50", 51, None, "GND", "SCL", "0x22",
                (6.80, -8.50, 90.0),
                ((6, 3, 0, 11, 1), (6, 3, 11, 11, 4)),
            ),
        ),
        summary="198 XL-1010RGB LEDs (9x22), 3x AW20198QNR, USB-C + Micro-JST 1.25 + NW/SE flat-face wing buttons, 4L",
        io_mode="usb",
        usb_s=-3.25,
        usb_ye=3.85,
    ),
    "p4-264-usb": VariantSpec(
        name="p4-264-usb",
        title_rev="P4U",
        cols=12,
        rows=22,
        px=2.02,
        py=2.60,
        drivers=(
            DriverSpec(
                1, "U1", "R30", 31, "C30", "GND", "GND", "0x20",
                (-5.80, -18.80, 90.0),
                ((0, 6, 0, 11, 1),),
            ),
            DriverSpec(
                2, "U2", "R33", 41, "C40", "VSYS", "VSYS", "0x25",
                (5.80, -18.80, 90.0),
                ((6, 6, 0, 11, 1),),
            ),
            DriverSpec(
                3, "U10", "R50", 51, None, "GND", "SCL", "0x22",
                (-9.35, 16.60, 90.0),
                ((0, 6, 11, 11, 1),),
            ),
            DriverSpec(
                4, "U11", "R60", 61, None, "GND", "SDA", "0x23",
                (6.80, -6.50, 90.0),
                ((6, 6, 11, 11, 1),),
            ),
        ),
        summary="264 XL-1010RGB LEDs (12x22), 4x AW20198QNR, USB-C + Micro-JST 1.25 + NW/SE flat-face wing buttons, 4L",
        io_mode="usb",
        usb_s=-3.35,
        usb_ye=3.70,
    ),
}


def build_led_cells(spec: VariantSpec) -> List[dict]:
    """Return ordered list of LED cell records (D1..DN) sorted by driver idx, triplet (1..6), and SW (1..11)."""
    cells = []
    d_num = 1
    for drv in spec.drivers:
        # Collect (triplet_k, sw_m, col, row) so schematic & PCB share exact deterministic D1..DN numbering.
        drv_cells = []
        for col0, n_cols, row0, n_rows, trip0 in drv.tiles:
            for dc in range(n_cols):
                col = col0 + dc
                trip_k = trip0 + dc  # 1..6
                for dr in range(n_rows):
                    row = row0 + dr
                    sw_m = dr + 1    # 1..11
                    drv_cells.append((trip_k, sw_m, col, row))
        drv_cells.sort(key=lambda t: (t[0], t[1]))
        for trip_k, sw_m, col, row in drv_cells:
            x_raw = (col - (spec.cols - 1) / 2.0) * spec.px
            x = round(round(x_raw / 0.05) * 0.05, 4)
            v = (row - (spec.rows - 1) / 2.0) * spec.py
            y = round(round((v + SKEW * x) / 0.05) * 0.05, 4)
            cells.append({
                "ref": f"D{d_num}",
                "d_num": d_num,
                "drv_idx": drv.idx,
                "uref": drv.uref,
                "triplet": trip_k,
                "sw": sw_m,
                "col": col,
                "row": row,
                "x_mm": x,
                "y_mm": y,
            })
            d_num += 1
    assert len(cells) == spec.n_leds, f"{len(cells)} != {spec.n_leds}"
    return cells
