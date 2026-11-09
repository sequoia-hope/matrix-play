#!/usr/bin/env python3
"""export_and_cost.py -- Live LCSC qty-10 BOM cost comparison + 4-layer JLCPCB Gerber/BOM/CPL exporter."""
from __future__ import annotations

import argparse
import collections
import csv
import json
import math
import os
import re
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude/skills/pcb-design/scripts"))
sys.path.insert(0, str(ROOT / "scripts/sunflower"))

from kicad_files import find_project, load_schematic  # noqa: E402
from config import VARIANTS  # noqa: E402

UA = {"User-Agent": "Mozilla/5.0"}
LAYERS_4L = ",".join([
    "F.Cu", "In1.Cu", "In2.Cu", "B.Cu",
    "F.Paste", "B.Paste",
    "F.Silkscreen", "B.Silkscreen",
    "F.Mask", "B.Mask",
    "Edge.Cuts",
])


def natural(ref: str):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", ref)]


def lcsc_info(code: str, cache: dict) -> tuple[str, int, list[tuple[int, float]]]:
    if code in cache:
        return cache[code]
    url = f"https://wmsc.lcsc.com/ftps/wm/product/detail?productCode={code}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        d = json.load(r).get("result") or {}
    mpn = d.get("productModel") or code
    stock = int(d.get("stockNumber") or 0)
    lad = [
        (int(p["ladder"]), float(p["usdPrice"] if "usdPrice" in p else p.get("productPrice") or 0.0))
        for p in (d.get("productPriceList") or [])
    ]
    lad.sort(key=lambda x: x[0])
    cache[code] = (mpn, stock, lad)
    return mpn, stock, lad


def ladder_price(lad: list[tuple[int, float]], total_qty: int) -> float:
    if not lad:
        return 0.0
    best = lad[0][1]
    for step, p in lad:
        if total_qty >= step:
            best = p
    return best


def run_cost(qty: int = 10):
    cache: dict = {}
    targets = [(f"{k} (4L, {v.n}x XL-1615, {len(v.drivers)}x AW20198)", v.hw_dir / "sunflower.kicad_sch") for k, v in VARIANTS.items()]
    targets += [
        ("parallelogram p1-66 (4L)", ROOT / "hw/parallelogram/p1-66/parallelogram.kicad_sch"),
        ("parallelogram p2-132 (4L)", ROOT / "hw/parallelogram/p2-132/parallelogram.kicad_sch"),
        ("round-pendant-e (8L, 235x XL-1010, 5x WLCSP)", ROOT / "hw/round-pendant/e/round-pendant.kicad_sch"),
    ]
    out_summary = {}
    for label, sch_path in targets:
        sch = load_schematic(sch_path)
        cnt = collections.Counter()
        refs_by_c = collections.defaultdict(list)
        for r, s in sch.parts.items():
            if s.exclude_from_board or s.dnp or s.exclude_from_bom:
                continue
            c = s.fields.get("LCSC", "").strip()
            if c:
                cnt[c] += 1
                refs_by_c[c].append(r)
        tot = 0.0
        led_cost = 0.0
        drv_cost = 0.0
        mcu_cost = 0.0
        zero_stock = []
        for c, n in cnt.items():
            mpn, stock, lad = lcsc_info(c, cache)
            u = ladder_price(lad, n * qty)
            sub = u * n
            tot += sub
            if any(x.startswith("D") for x in refs_by_c[c]):
                led_cost += sub
            if c in ("C5137654", "C2678907"):
                drv_cost += sub
            if c in ("C42411118", "C42411119"):
                mcu_cost += sub
            if stock < n * qty:
                zero_stock.append((c, mpn, stock, n * qty))
        n_leds = sum(1 for r in sch.parts if r.startswith("D"))
        out_summary[label] = {
            "bom_per_board": round(tot, 2),
            "led_cost": round(led_cost, 2),
            "drv_ic_cost": round(drv_cost, 2),
            "mcu_plus_l1": round(mcu_cost, 2),
            "unique_lines": len(cnt),
            "total_placements": sum(cnt.values()),
            "n_leds": n_leds,
            "low_stock": zero_stock,
        }
        print(
            f"{label:<40} | BOM/bd @qty{qty}: ${tot:6.2f} "
            f"(LEDs ${led_cost:5.2f}, Drivers ${drv_cost:5.2f}, RP2350+L1 ${mcu_cost:4.2f}) "
            f"| lines={len(cnt)}, parts={sum(cnt.values())}, low_stock={zero_stock}"
        )

    # Also check counterfactual parts: XL-1615RGBC (C965840) & RP2040 (C2040)
    mpn_1615, stk_1615, lad_1615 = lcsc_info("C965840", cache)
    mpn_1010, stk_1010, lad_1010 = lcsc_info("C965834", cache)
    mpn_2040, stk_2040, lad_2040 = lcsc_info("C2040", cache)
    print("\n--- Option Pricing @ qty", qty, "---")
    for n_led in (66, 88, 110, 132):
        p1010 = ladder_price(lad_1010, n_led * qty)
        p1615 = ladder_price(lad_1615, n_led * qty)
        print(
            f"  {n_led} LEDs: XL-1010RGB (C965834, stk {stk_1010}): ${p1010:.4f}/ea = ${n_led*p1010:.2f}/bd "
            f"vs XL-1615RGBC (C965840, stk {stk_1615}): ${p1615:.4f}/ea = ${n_led*p1615:.2f}/bd "
            f"(delta: ${(p1615 - p1010)*n_led:+.2f}/bd)"
        )
    p2040 = ladder_price(lad_2040, qty)
    print(f"  RP2040 (C2040, stk {stk_2040}): ${p2040:.4f}/ea (needs NO L1 inductor -> 100% locally in-stock at JLC!)")
    (ROOT / "design/study/sunflower/cost.json").write_text(json.dumps(out_summary, indent=2) + "\n")


def export_fab(variant: str):
    import pcbnew

    spec = VARIANTS[variant]
    hw = spec.hw_dir
    pro, sch_path, pcb_path = find_project(hw)
    out_dir = hw / "fab"
    gdir = out_dir / "gerbers"
    gdir.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            "kicad-cli", "pcb", "export", "gerbers",
            "--layers", LAYERS_4L,
            "--subtract-soldermask",
            "-o", str(gdir) + "/",
            str(pcb_path),
        ],
        check=True,
    )
    subprocess.run(
        [
            "kicad-cli", "pcb", "export", "drill",
            "--format", "excellon",
            "--drill-origin", "absolute",
            "--excellon-units", "mm",
            "-o", str(gdir) + "/",
            str(pcb_path),
        ],
        check=True,
    )

    zpath = out_dir / f"sunflower-{variant}-gerbers.zip"
    gerber_files = sorted(f for f in gdir.iterdir() if f.is_file() and not f.name.endswith("-drl_map.gbr"))
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in gerber_files:
            zf.write(f, f.name)

    sch = load_schematic(sch_path)
    board = pcbnew.LoadBoard(str(pcb_path))
    fp_map = {fp.GetReference(): fp for fp in board.GetFootprints()}
    built_refs = sorted(
        (r for r, s in sch.parts.items() if not s.exclude_from_board and not s.dnp and not s.exclude_from_bom),
        key=natural,
    )

    # Verified against EasyEDA component API (0-deg package pads & c_origin) vs KiCad Top 0-deg footprint:
    # (rot_off_deg, pos_off_x_mm, pos_off_y_mm) in Top 0-deg Gerber coordinates (+X right, +Y up).
    JLC_CPL_FIXES: dict[str, tuple[float, float, float]] = {
        "C965840": (180.0, 0.0, 0.0),    # XL-1615RGBC-RF: EasyEDA 0 deg is 180 deg from XINGLIGHT Top View
        "C177225": (180.0, 0.0, 0.950),  # Molex 53261-0271: EasyEDA 0 deg inverted + origin at pad-bbox midpoint
        "C165948": (0.0, 0.0, 1.571),    # HRO TYPE-C-31-M-12: EasyEDA origin 1.571 mm north of KiCad anchor
        "C236117": (270.0, 0.0, 0.0),    # NTZD3155CT1G SOT-563: EasyEDA pin 1 BL vs KiCad TL
        "C5137654": (270.0, 0.0, 0.0),   # AW20198QNR QFN-40: EasyEDA pin 1 BL vs KiCad TL
        "C190862": (270.0, 0.0, 0.0),    # W25Q128JVPIQ WSON-8: EasyEDA pin 1 BL vs KiCad TL
        "C15999": (180.0, 0.0, 0.0),     # USBLC6-2P6 SOT-666: EasyEDA pin 1 BR vs KiCad TL
        "C189624": (270.0, 0.0, 0.0),    # LIS2DW12TR LGA-12: EasyEDA pin 1 BL vs KiCad TL
    }

    bom_groups: dict[tuple[str, str, str, str, str], list[str]] = {}
    cpl_rows: list[list[str]] = []
    for ref in built_refs:
        s = sch.parts[ref]
        fp = fp_map[ref]
        lcsc = s.fields.get("LCSC", "").strip()
        mpn = s.fields.get("MPN", "").strip()
        mfr = s.fields.get("Manufacturer", "").strip()
        pkg = s.footprint.split(":", 1)[-1] if ":" in s.footprint else s.footprint
        bom_groups.setdefault((s.value, pkg, lcsc, mpn, mfr), []).append(ref)
        pos = fp.GetPosition()
        x_mm = pcbnew.ToMM(pos.x)
        y_mm = -pcbnew.ToMM(pos.y)
        ki_rot = fp.GetOrientationDegrees()
        side = "Bottom" if fp.IsFlipped() else "Top"
        rot_off, dx0, dy0 = JLC_CPL_FIXES.get(lcsc, (0.0, 0.0, 0.0))
        rad = math.radians(ki_rot)
        rcos, rsin = math.cos(rad), math.sin(rad)
        if side == "Bottom":
            x_mm += dx0 * rcos + dy0 * rsin
            y_mm += dx0 * rsin - dy0 * rcos
            rot = (180.0 - ki_rot + rot_off) % 360.0
        else:
            x_mm += dx0 * rcos - dy0 * rsin
            y_mm += dx0 * rsin + dy0 * rcos
            rot = (ki_rot + rot_off) % 360.0
        cpl_rows.append([ref, f"{x_mm:.4f}mm", f"{y_mm:.4f}mm", side, f"{rot:.2f}"])

    bom_path = out_dir / "bom-jlcpcb.csv"
    with bom_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #", "MPN", "Manufacturer"])
        for (val, pkg, lcsc, mpn, mfr), refs in sorted(bom_groups.items(), key=lambda kv: natural(kv[1][0])):
            w.writerow([val, ",".join(refs), pkg, lcsc, mpn, mfr])

    cpl_path = out_dir / "cpl-jlcpcb.csv"
    with cpl_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        w.writerows(cpl_rows)

    print(f"Exported {zpath} ({len(gerber_files)} files), {bom_path} ({len(bom_groups)} lines), {cpl_path} ({len(cpl_rows)} parts)", flush=True)
    os._exit(0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cost", action="store_true")
    ap.add_argument("--qty", type=int, default=10)
    ap.add_argument("--export", choices=list(VARIANTS.keys()))
    args = ap.parse_args()
    if args.cost:
        run_cost(args.qty)
    if args.export:
        export_fab(args.export)
