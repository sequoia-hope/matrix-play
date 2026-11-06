#!/usr/bin/env python3
"""config.py -- geometry, ultra-dense 20x20 mm square LED array specs, and floorplan for hw/dense-square/<variant>/."""
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parents[2]
OX, OY = 100.0, 100.0

# Rectangular board geometry: 25.0 mm wide x 50.0 mm tall, R = 1.50 mm rounded corners.
HALF_W = 12.50       # x in [-12.50, +12.50] -> 25.00 mm wide
HALF_H = 25.00       # y in [-25.00, +25.00] -> 50.00 mm tall
CORNER_R = 1.50      # 1.50 mm rounded corners

# North 20.0 x 20.0 mm square LED array window (symmetric 2.50 mm bezel to West, North, East edges):
#   x in [-10.00, +10.00], y in [-22.50, -2.50], centered at (0.00, -12.50).
# All ICs, drivers, passives, and connectors sit in the South electronics bay (y in [-2.00, +25.00]),
# leaving all 8 copper layers under the 20 x 20 mm LED array 100% clear for LED escape & matrix routing!
ARRAY_CX = 0.00
ARRAY_CY = -12.50
ARRAY_W = 20.00
ARRAY_H = 20.00
SOUTH_BAY_Y_MIN = -2.00  # Strict north ceiling for all non-LED / non-Q2 footprints


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
    fcu_pos: Tuple[float, float, float]  # (x_rel, y_rel, rot_deg) on F.Cu South bay
    # Rectangular LED sub-tiles driven by this chip:
    # list of (col0, n_cols, row0, n_rows, triplet0_1based, sw0_1based)
    tiles: Tuple[Tuple[int, int, int, int, int, int], ...]


@dataclass(frozen=True)
class VariantSpec:
    name: str
    title_rev: str
    cols: int
    rows: int
    pitch: float
    drivers: Tuple[DriverSpec, ...]
    summary: str

    @property
    def n_leds(self) -> int:
        return self.cols * self.rows

    @property
    def hw_dir(self) -> Path:
        return ROOT / "hw/dense-square" / self.name


VARIANTS = {
    # Provable off-pad maximum density inside 20.0 x 20.0 mm:
    # 16 x 16 = 256 MHPA0808RGBDT (0.80 x 0.80 mm) at 1.27 mm (50 mil) pitch -> 19.95 x 19.95 mm copper span (64.0 LEDs/cm^2)
    "s16-256": VariantSpec(
        name="s16-256",
        title_rev="S16",
        cols=16,
        rows=16,
        pitch=1.27,
        drivers=(
            # Each AW20198QNR drives a pure 4-col x 16-row = 64-LED vertical slice directly north of its lane!
            # Fold-back rows 11..15 keep triplet 5 contiguous in local cols 0..1 and triplet 6 contiguous in local cols 2..3.
            DriverSpec(
                1, "U1", "R30", 31, "C30", "GND", "GND", "0x20",
                (-8.90, 2.40, 0.0),
                ((0, 4, 0, 11, 1, 1), (0, 1, 11, 5, 5, 1), (1, 1, 11, 5, 5, 6), (2, 1, 11, 5, 6, 1), (3, 1, 11, 5, 6, 6)),
            ),
            DriverSpec(
                2, "U2", "R33", 41, "C40", "VSYS", "VSYS", "0x25",
                (-8.90, 11.60, 0.0),
                ((4, 4, 0, 11, 1, 1), (4, 1, 11, 5, 5, 1), (5, 1, 11, 5, 5, 6), (6, 1, 11, 5, 6, 1), (7, 1, 11, 5, 6, 6)),
            ),
            DriverSpec(
                3, "U10", "R50", 51, None, "GND", "SCL", "0x22",
                (8.90, 11.60, 0.0),
                ((8, 4, 0, 11, 1, 1), (8, 1, 11, 5, 5, 1), (9, 1, 11, 5, 5, 6), (10, 1, 11, 5, 6, 1), (11, 1, 11, 5, 6, 6)),
            ),
            DriverSpec(
                4, "U11", "R60", 61, None, "GND", "SDA", "0x23",
                (8.90, 2.40, 0.0),
                ((12, 4, 0, 11, 1, 1), (12, 1, 11, 5, 5, 1), (13, 1, 11, 5, 5, 6), (14, 1, 11, 5, 6, 1), (15, 1, 11, 5, 6, 6)),
            ),
        ),
        summary="256 MHPA0808RGBDT 0808 LEDs (16x16 square in 20x20 mm, 1.27 mm pitch, 64 LEDs/cm^2), 4x AW20198QNR, 8-layer ENIG",
    ),
    # Fallback tier if needed: 15 x 15 = 225 MHPA0808RGBDT at 1.36 mm pitch -> 19.94 x 19.94 mm copper span (56.25 LEDs/cm^2)
    "s15-225": VariantSpec(
        name="s15-225",
        title_rev="S15",
        cols=15,
        rows=15,
        pitch=1.36,
        drivers=(
            DriverSpec(
                1, "U1", "R30", 31, "C30", "GND", "GND", "0x20",
                (-8.90, 2.40, 0.0),
                ((0, 4, 0, 11, 1, 1), (0, 1, 11, 4, 5, 1), (1, 1, 11, 4, 5, 5), (2, 1, 11, 4, 6, 1), (3, 1, 11, 4, 6, 5)),
            ),
            DriverSpec(
                2, "U2", "R33", 41, "C40", "VSYS", "VSYS", "0x25",
                (-8.90, 11.60, 0.0),
                ((4, 4, 0, 11, 1, 1), (4, 1, 11, 4, 5, 1), (5, 1, 11, 4, 5, 5), (6, 1, 11, 4, 6, 1), (7, 1, 11, 4, 6, 5)),
            ),
            DriverSpec(
                3, "U10", "R50", 51, None, "GND", "SCL", "0x22",
                (8.90, 11.60, 0.0),
                ((8, 4, 0, 11, 1, 1), (8, 1, 11, 4, 5, 1), (9, 1, 11, 4, 5, 5), (10, 1, 11, 4, 6, 1), (11, 1, 11, 4, 6, 5)),
            ),
            DriverSpec(
                4, "U11", "R60", 61, None, "GND", "SDA", "0x23",
                (8.90, 2.40, 0.0),
                ((12, 3, 0, 11, 1, 1), (12, 3, 11, 4, 4, 1)),
            ),
        ),
        summary="225 MHPA0808RGBDT 0808 LEDs (15x15 square in 20x20 mm, 1.36 mm pitch, 56.3 LEDs/cm^2), 4x AW20198QNR, 8-layer ENIG",
    ),
    # 14 x 14 = 196 MHPA0808RGBDT at 1.46 mm pitch -> 19.88 x 19.88 mm copper span (49.0 LEDs/cm^2)
    "s14-196": VariantSpec(
        name="s14-196",
        title_rev="S14",
        cols=14,
        rows=14,
        pitch=1.46,
        drivers=(
            DriverSpec(
                1, "U1", "R30", 31, "C30", "GND", "GND", "0x20",
                (-7.20, 2.00, 0.0),
                ((0, 4, 0, 11, 1, 1), (0, 2, 11, 3, 5, 1), (2, 2, 11, 3, 5, 4)),
            ),
            DriverSpec(
                2, "U2", "R33", 41, "C40", "VSYS", "VSYS", "0x25",
                (-7.20, 9.60, 0.0),
                ((4, 4, 0, 11, 1, 1), (4, 2, 11, 3, 5, 1), (6, 2, 11, 3, 5, 4)),
            ),
            DriverSpec(
                3, "U10", "R50", 51, None, "GND", "SCL", "0x22",
                (7.20, 9.60, 0.0),
                ((8, 3, 0, 11, 1, 1), (8, 3, 11, 3, 4, 1)),
            ),
            DriverSpec(
                4, "U11", "R60", 61, None, "GND", "SDA", "0x23",
                (7.20, 2.00, 0.0),
                ((11, 3, 0, 11, 1, 1), (11, 3, 11, 3, 4, 1)),
            ),
        ),
        summary="196 MHPA0808RGBDT 0808 LEDs (14x14 square in 20x20 mm, 1.46 mm pitch, 49 LEDs/cm^2), 4x AW20198QNR, 8-layer ENIG",
    ),
}


def build_led_cells(spec: VariantSpec) -> List[dict]:
    """Return ordered list of all cols*rows LED cells D1..DN in row-major order inside the 20x20 mm North window."""
    tile_map = {}
    for drv in spec.drivers:
        used_keys = set()
        for c0, nc, r0, nr, trip0, sw0 in drv.tiles:
            for dr in range(nr):
                for dc in range(nc):
                    col = c0 + dc
                    row = r0 + dr
                    trip = trip0 + dc
                    sw = sw0 + dr
                    assert 1 <= trip <= 6, f"{spec.name} {drv.uref}: triplet {trip} out of 1..6"
                    assert 1 <= sw <= 11, f"{spec.name} {drv.uref}: sw {sw} out of 1..11"
                    assert (trip, sw) not in used_keys, f"{spec.name} {drv.uref}: duplicate (trip={trip}, sw={sw})"
                    used_keys.add((trip, sw))
                    assert (col, row) not in tile_map, f"Duplicate tile assignment at ({col}, {row})"
                    tile_map[(col, row)] = (drv.idx, drv.uref, trip, sw)

    cells = []
    d_num = 1
    for row in range(spec.rows):
        for col in range(spec.cols):
            assert (col, row) in tile_map, f"Missing driver assignment at ({col}, {row}) in {spec.name}"
            drv_idx, uref, trip, sw = tile_map[(col, row)]
            x_rel = round(ARRAY_CX + (col - (spec.cols - 1) / 2.0) * spec.pitch, 4)
            y_rel = round(ARRAY_CY + (row - (spec.rows - 1) / 2.0) * spec.pitch, 4)
            # Verify every LED's 0.90 x 0.90 mm reflow land pattern fits strictly inside the 20.0 x 20.0 mm window!
            assert abs(x_rel - ARRAY_CX) + 0.45 <= ARRAY_W / 2.0 + 1e-6, f"LED X out of 20mm window: {x_rel}"
            assert abs(y_rel - ARRAY_CY) + 0.45 <= ARRAY_H / 2.0 + 1e-6, f"LED Y out of 20mm window: {y_rel}"
            cells.append({
                "ref": f"D{d_num}",
                "d_num": d_num,
                "col": col,
                "row": row,
                "x_mm": x_rel,
                "y_mm": y_rel,
                "drv_idx": drv_idx,
                "uref": uref,
                "triplet": trip,
                "sw": sw,
            })
            d_num += 1
    assert len(cells) == spec.n_leds
    return cells


if __name__ == "__main__":
    for vname, sp in VARIANTS.items():
        cs = build_led_cells(sp)
        xs = [c["x_mm"] for c in cs]
        ys = [c["y_mm"] for c in cs]
        span_cu_x = (max(xs) - min(xs)) + 0.90
        span_cu_y = (max(ys) - min(ys)) + 0.90
        print(f"{vname}: {len(cs)} LEDs ({sp.cols}x{sp.rows} @ {sp.pitch} mm), cu_span={span_cu_x:.2f}x{span_cu_y:.2f} mm, X=[{min(xs):.3f}..{max(xs):.3f}], Y=[{min(ys):.3f}..{max(ys):.3f}]")
