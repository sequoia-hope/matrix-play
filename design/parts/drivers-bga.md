# U1, U2, U10, U11, U12: Lumissil IS31FL3745-CLS4-TR (Variant D — BGA)

Datasheet: `datasheets/is31fl3745.pdf` (Rev. 0A, 2018-06-04). Read: all 21 pages; Figure 1, Figure 2, pin configuration (p. 3), and WLCSP-36 package outline (p. 20) verified at 300 DPI.
Supplier: `C2678907 IS31FL3745-CLS4-TR (ISSI, WLCSP-36(2.9x2.9)): extended, JLC stock 0, lifecycle normal, checked 2026-11-04` (user-approved pre-order / global sourcing from DigiKey/Mouser, same path as `L1` `C42411119`).
Footprint: `round_pendant:WLCSP-36_2.9x2.9mm_P0.5mm`, verified against mechanical drawing p. 20 (6×6 array, 0.500 mm pitch, 0.250 mm ball diameter, 2.895 × 2.895 mm ±0.025 mm package body, 0.1975 mm outer ball centre to die edge, 0.400 mm height, **no exposed pad**). NSMD circular copper lands 0.20 mm dia (80% of 0.25 mm collapsible ball per IPC-7351B), +0.045 mm solder mask margin (0.29 mm mask opening, 0.21 mm mask web between balls), pin A1 top-left per p. 3 Top View.

## Why Variant D replaces U1/U2 QFN-60 with 5× WLCSP-36
Variant C's two `IS31FL3741A-QFLS4-TR` QFN-60 drivers (`7 × 7 mm` body = `98 mm²` total, `5.4 × 5.4 mm` solid exposed ground pad = `58.3 mm²`) blocked through-via LED escapes when solid exposed pads were enforced (`decisions.md` 2026-11-04; `c-solid-z6..z17` stalled at 37–58 open signals). Five `IS31FL3745-CLS4-TR` WLCSP-36 packages occupy `5 × 8.38 mm² = 41.9 mm²` total with **zero exposed ground pads**, provide `5 × 48 = 240` Common-Anode RGB matrix cells (covering all 235 LEDs including `D235` at 47 RGB LEDs per driver), halve scan-line peak current, and sit locally at the centroids of five 47-LED sectors.

## Absolute max vs our worst case
| Parameter | Abs max (p. 5) | Our worst case | Margin |
|---|---|---|---|
| Supply voltage `PVCC`, `VDD` (`VCC`) | −0.3 V to +6.0 V | `VSYS` = 4.5 V max (`BQ24073` `VO(REG)` max) | 1.5 V margin |
| Voltage at any input pin | −0.3 V to `VCC` + 0.3 V | `+3V3` fed from `VSYS` (≤ `VSYS`); `ADDR1/2` strapped to `GND`, `SDA`, `SCL`, or `VSYS` (= `VCC`) | OK by construction |
| Operating supply voltage | 2.7 V to 5.5 V | 3.0 V to 4.5 V (`VSYS`); firmware blanks below 3.3 V | OK |
| Junction temperature `TJMAX` / `TA` | 150 °C abs / −40 to +125 °C op | ~80 °C board max at 300 mA total (`decisions.md`) | > 45 °C margin |

## Required external parts (Figure 1 p. 1, Figure 2 p. 2, Layout p. 18)
| Datasheet | Variant D implementation |
|---|---|
| `PVCC` (ball `A3`): 1 µF + 0.1 µF to `GND` | `1 µF` (`C52923`) + `100 nF` (`C1525`) 0402 per IC (`C31/32, C41/42, C51/52, C61/62, C71/72`), plus two `22 µF` 10 V 0603 bulk caps (`C30`, `C40`, `C86295`) on `VSYS` |
| `VDD` (ball `F5`): 1 µF + 0.1 µF to `GND` | `1 µF` (`C52923`) + `100 nF` (`C1525`) 0402 per IC (`C33/34, C43/44, C53/54, C63/64, C73/74`) next to `F5`/`F4` |
| `RSET` (ball `F3`): resistor to `GND` (10 kΩ example) | `30.0 kΩ` 1% 0402 (`C25776`) per IC (`R30, R33, R50, R60, R70`) right next to `F3`/`F4` |
| `SDA` (`D3`), `SCL` (`E3`): 1 kΩ pull-ups at 1 MHz (p. 7) | Shared `R21`, `R22` = `1 kΩ` (`C11702`) to `+3V3` on `I2C0` |
| `SDB` (`E5`): 100 kΩ pull-down to `GND` (Fig. 1 & Fig. 2) | Shared `LED_SDB` (`GPIO6`) with `R31 = 100 kΩ` (`C25741`) + `C35 = 100 nF` (`C1525`) to `GND` |
| `ADDR2` (`E4`), `ADDR1` (`D4`) (Table 1, p. 7) | `U1`: `GND/GND` (`0x20`); `U2`: `GND/SDA` (`0x22`); `U10`: `SCL/SCL` (`0x25`); `U11`: `SCL/SDA` (`0x26`); `U12`: `VSYS/VSYS` (`0x2F`) |
| `SYNC` (`F2`) (Table 14, p. 15) | Unconnected (`NC`): default `SYNC = 00` disables clock I/O with internal ~30 kΩ pull-low |
| 20 Ω / 51 Ω series CS resistors (Fig. 1 at 5 V) | Omitted (`decisions.md` 2026-11-02): `VSYS` ≤ 4.4–4.5 V and per-IC dissipation is ~0.10 W at the 300 mA limit |
| `GND` (ball `F4`) | Connected directly to `In2.Cu` `GND` plane and local decoupling/`RSET` ground return |

## Calculations
- **Peak & average LED current (p. 11, Eq. 1–3):**
  - Configure `PG2 00h` `SWS = 0011` (`SW1~SW8`, 1/8 scan); non-overlap blanking `tNOL = 1 µs`, `tSCAN = 40 µs` → `Duty = 40 / ((40 + 1) × 8) = 1 / 8.2` (p. 11, Eq. 2). (Note: POR default `SWS = 0000` is 1/11 duty; firmware writes `SWS = 0011` during init.)
  - `IOUT(PEAK) = (343 V / RSET) × (GCC / 256) × (SL / 256)` (p. 11, Eq. 3).
  - With `RSET = 30.0 kΩ` (`C25776`) and `GCC = SL = 255`:
    `IOUT(PEAK) = (343 / 30e3) × (255/256)² = 11.34 mA` per active `CS` channel (`≤ 34 mA` max).
  - Full-scale average current per die: `ILED = 11.34 mA / 8.2 = 1.38 mA` (matching Variant C's ~1.25–1.5 mA range; setting `GCC = 231` gives exact `1.25 mA`).
- **Matrix partitioning (`235 = 5 × 47` RGB LEDs):**
  - Each `IS31FL3745` provides `8 SW × 18 CS = 144 dots = 48` Common-Anode RGB cells (`R = CS(3k)`, `G = CS(3k-1)`, `B = CS(3k-2)` for `k = 1..6`, matching Fig. 1 p. 1).
  - Each of the 5 drivers (`U1, U2, U10, U11, U12`) drives **47 RGB LEDs** (`SW1..SW7` × 6 RGB + `SW8` × 5 RGB = 47 RGB; cell `SW8 / triplet 6` is unpopulated on each chip). All 235 LEDs (`D1..D235`, including the centre LED `D235`) are matrix-driven with uniform constant-current scaling, freeing `GPIO23–25` and removing `R40–R42`.
- **Scan-line (`SWx`) current & headroom:**
  - Peak current per `SWx` pin = `18 × 11.34 mA = 204.2 mA` (`2.4×` lower than Variant C's `494 mA`!), continuous average `204.2 / 8.2 = 24.9 mA`.
  - Switch headroom `VHR(SW)` (p. 5): `200 mV` typ at `306 mA` → `~133 mV` typ at `204 mA`.
  - Sink headroom `VHR(CS)` (p. 5): `300 mV` typ at `34 mA` (conservative `300 mV` at `11.34 mA`).
  - Minimum `VSYS` for full-scale blue (`VF = 2.8 V` typ) = `2.8 + 0.13 + 0.30 = 3.23 V` typ (`420 mV` more headroom than Variant C!).
- **Quiescent & shutdown current (p. 5):**
  - Active quiescent (`SDB = H`, all LEDs off): `5 × 2 mA = 10 mA` typ.
  - Hardware shutdown (`LED_SDB = 0 V` via `R31 = 100 kΩ` in sleep): `5 × 1 µA = 5 µA` typ (within the 85 µA sleep budget; Variant C budgeted 1–2 µA).
- **Thermal dissipation:**
  - At the 300 mA firmware board limit (`60 mA` per driver across 5 drivers, `VSYS = 4.2 V`, mean `VF = 2.53 V`): `P_IC ≈ (4.2 − 2.53) × 0.060 = 0.10 W` per IC. At `θJA = 47.49 °C/W` (p. 5, 4-layer JEDEC; 8-layer board with `In2.Cu` GND + `In5.Cu` VSYS planes conducts through all 36 balls), local junction-to-board rise is `< 8 °C`. Whole-board dissipation remains `~1.26 W` (`decisions.md` 2026-11-03).
- **I²C bus timing at 1 MHz (p. 6–7):**
  - 5 WLCSP inputs × ~5 pF + ~60 mm trace ≈ `45 pF` bus capacitance; with `R21 = R22 = 1 kΩ`, `tR ≈ 0.847 × 1 kΩ × 45 pF = 38 ns < 120 ns` Fm+ limit.
  - Frame update: `5 × 144 = 720` PWM bytes (`705` active + 15 padding for contiguous burst) at 1 MHz ≈ `6.6 ms` (`> 140 fps` max).

## Fine print / gotchas
- **`LGC` logic threshold (p. 5, p. 13 Table 9):** Powers up `LGC = 0` (`VIH = 1.4 V`, `VIL = 0.4 V`). As on `IS31FL3741A`, firmware should set `LGC = 1` (`VIH = 2.4 V`, `VIL = 0.6 V`) on init for maximum `VIL` margin over `RP2350` `VOL`, and use 12 mA drive strength on `GPIO4/GPIO5`.
- **`SWS` scan limit (p. 13 Table 9):** Powers up `SWS = 0000` (`1/11` duty, inherited from the 11-SW silicon family). Firmware sets `SWS = 0011` (`SW1~SW8`, `1/8` duty) so no time is wasted scanning non-existent `SW9–SW11`.
- **De-ghosting (p. 13–14 Table 11, p. 17):** Power-on default `PG2 02h = 0x55` (`0101 0101` in Table 8 vs `011` = `2 kΩ` off-time pull-down/pull-up in Table 11); firmware explicitly writes `0x33` (`2 kΩ` off-time only, zero static power loss) and sets `PHC = 1` (180° phase delay) on 2 of the 5 drivers (`U2`, `U11`) to reduce `VSYS` switching ripple.
- **Brownout during shutdown (p. 18):** If `VSYS` drops below 1.75 V while `SDB` is low, re-initialize all registers before/upon raising `SDB`. Firmware always re-initializes all 5 drivers on wake.
- **Address strapping via adjacent balls:** `ADDR2` (`E4`) and `ADDR1` (`D4`) sit immediately adjacent to `SDA` (`D3`), `SCL` (`E3`), `GND` (`F4`), and `VDD` (`F5`), so all 5 unique addresses (`0x20, 0x22, 0x25, 0x26, 0x2F`) strap directly on `B.Cu` inside the ball array with zero extra vias.

## Layout guidance from datasheet (p. 18)
1. Place `PVCC` (`A3`) and `VDD` (`F5`) decoupling capacitors (`1 µF` + `100 nF`, 100 nF closest) adjacent to the chip with tight ground return to `F4` (`GND`) and the `In2.Cu` ground plane.
2. Place `RSET` (`30 kΩ`) right next to `F3` (`RSET`) and `F4` (`GND`) (`F3` and `F4` are adjacent balls on the south row).
3. Connect `F4` (`GND`) directly to a ground via / `In2.Cu` plane for thermal and return-current conduction.
4. `SW1–SW8` balls (`A1, A2, A4, A5, A6, B1, B6, C1`) all lie on the outer perimeter ring and carry `204 mA` peak (`25 mA` avg) vs `11.3 mA` peak on `CS1–CS18`.
