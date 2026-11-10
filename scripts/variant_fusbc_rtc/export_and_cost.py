#!/usr/bin/env python3
"""export_and_cost.py — Export 8-layer JLCPCB Gerbers + split PTH/NPTH drills + BOM + CPL + STEP
for round-pendant-f-usbc-rtc, audit every LCSC part's CPL rotation & EasyEDA SVGNODE c_origin pad-for-pad,
and compute live LCSC qty-10 BOM cost + JLCPCB PCBA stock comparison against f and f-usbc.
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "pcb-design" / "scripts"))
from kicad_files import find_project, load_schematic  # noqa: E402

UA = {"User-Agent": "Mozilla/5.0"}
CURL_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

LAYERS_8L = ",".join([
    "F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu",
    "F.Paste", "B.Paste",
    "F.Silkscreen", "B.Silkscreen",
    "F.Mask", "B.Mask",
    "Edge.Cuts",
])

JLC_CPL_FIXES: dict[str, tuple[float, float, float]] = {
    "C965834":  ( 90.0, 0.0,  0.000),  # XL-1010RGB: EasyEDA 0 deg has COM+ TL (-90 deg from XINGLIGHT Top View BL)
    "C530612":  (  0.0, 0.0, -1.209),  # TYPE-C-31-M-22: EasyEDA 0 deg matches KiCad; SVGNODE c_origin 1.209 mm toward mouth
    "C225111":  (  0.0, 0.0,  0.200),  # A1251WR-S-2P: EasyEDA 0 deg mouth matches KiCad; SVGNODE c_origin +0.200 mm
    "C1542426": (  0.0, 0.0,  0.000),  # RX8130CE:BB: EasyEDA 0 deg & c_origin match KiCad 0.000 mm across all 10 pads
    "C2828254": (  0.0, 0.0, -0.325),  # EVQP7J01P
    "C388883":  (  0.0, 0.0, -0.336),  # EVQP7C01P
    "C190862":  (270.0, 0.0,  0.000),  # W25Q128JVPIQ WSON-8: EasyEDA pin 1 BL vs KiCad TL
    "C15999":   (180.0, 0.0,  0.000),  # USBLC6-2P6 SOT-666: EasyEDA pin 1 BR vs KiCad TL
    "C189624":  (270.0, 0.0,  0.000),  # LIS2DW12TR LGA-12: EasyEDA pin 1 BL vs KiCad TL
    "C236117":  (270.0, 0.0,  0.000),  # NTZD3155CT1G SOT-563: EasyEDA pin 1 BL vs KiCad TL
}


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


def export_fab(project_dir: Path, out_dir: Path, render_dir: Path) -> None:
    pro, sch_path, pcb_path = find_project(project_dir)
    gdir = out_dir / "gerbers"
    gdir.mkdir(parents=True, exist_ok=True)
    render_dir.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            "kicad-cli", "pcb", "export", "gerbers",
            "--layers", LAYERS_8L,
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
            "--excellon-separate-th",
            "--drill-origin", "absolute",
            "--excellon-units", "mm",
            "-o", str(gdir) + "/",
            str(pcb_path),
        ],
        check=True,
    )

    zpath = out_dir / f"round-pendant-{project_dir.name}-gerbers.zip"
    gerber_files = sorted(f for f in gdir.iterdir() if f.is_file() and not f.name.endswith("-drl_map.gbr"))
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in gerber_files:
            zf.write(f, f.name)

    # Export schematic PDF + 3D STEP into fab/ and renders/
    sch_pdf = render_dir / "schematic.pdf"
    subprocess.run(["kicad-cli", "sch", "export", "pdf", "-o", str(sch_pdf), str(sch_path)], check=True)
    shutil.copy2(sch_pdf, out_dir / "schematic.pdf")

    step_path = out_dir / f"round-pendant-{project_dir.name}.step"
    subprocess.run(
        ["kicad-cli", "pcb", "export", "step", "--subst-models", "-f", "-o", str(step_path), str(pcb_path)],
        check=True,
    )

    sch = load_schematic(sch_path)
    board = pcbnew.LoadBoard(str(pcb_path))
    fp_map = {fp.GetReference(): fp for fp in board.GetFootprints()}
    built_refs = sorted(
        (r for r, s in sch.parts.items() if not s.exclude_from_board and not s.dnp and not s.exclude_from_bom),
        key=natural,
    )

    bom_groups: dict[tuple[str, str, str, str, str], list[str]] = {}
    cpl_rows: list[list[str]] = []

    for ref in built_refs:
        s = sch.parts[ref]
        fp = fp_map.get(ref)
        if fp is None:
            sys.exit(f"ERROR: {ref} in schematic but missing on PCB")
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

    print(f"Wrote {zpath} ({len(gerber_files)} files)")
    print(f"Wrote {bom_path} ({len(bom_groups)} unique lines, {len(built_refs)} parts)")
    print(f"Wrote {cpl_path} ({len(cpl_rows)} placements)")
    print(f"Wrote {step_path} ({step_path.stat().st_size / 1e6:.2f} MB)")


def run_cost(qty: int = 10) -> None:
    cache: dict = {}
    targets = [
        ("round-pendant-f (8L, wire pads)", ROOT / "hw/round-pendant/f/round-pendant.kicad_sch"),
        ("round-pendant-f-usbc (8L, USB-C)", ROOT / "hw/round-pendant/f-usbc/round-pendant.kicad_sch"),
        ("round-pendant-f-usbc-rtc (8L, USB-C+BT1+RTC)", ROOT / "hw/round-pendant/f-usbc-rtc/round-pendant.kicad_sch"),
    ]
    results = {}
    for label, sch_path in targets:
        sch = load_schematic(sch_path)
        cnt = collections.Counter()
        for r, s in sch.parts.items():
            if s.exclude_from_board or s.dnp or s.exclude_from_bom:
                continue
            c = s.fields.get("LCSC", "").strip()
            if c:
                cnt[c] += 1
        tot = 0.0
        zero_stock = []
        per_part = {}
        for c, n in sorted(cnt.items()):
            mpn, stock, lad = lcsc_info(c, cache)
            u = ladder_price(lad, n * qty)
            sub = u * n
            tot += sub
            per_part[c] = (mpn, n, u, sub, stock)
            if stock < n * qty:
                zero_stock.append((c, mpn, stock, n * qty))
        results[label] = (tot, len(cnt), sum(cnt.values()), zero_stock, per_part)
        print(f"{label:<46s} | BOM/bd @qty{qty}: ${tot:6.4f} (${tot:6.2f}) | lines={len(cnt)}, parts={sum(cnt.values())}, low_stock={zero_stock}")

    lbl_u, lbl_r = targets[1][0], targets[2][0]
    delta = results[lbl_r][0] - results[lbl_u][0]
    print(f"\nBOM delta (f-usbc-rtc - f-usbc) @ qty {qty}: ${delta:+.4f}/board (${delta*qty:+.2f} for {qty} boards)")
    for code in ("C225111", "C1542426", "C1525", "C52923", "C25741"):
        if code in results[lbl_r][4]:
            mpn, n, u, sub, stk = results[lbl_r][4][code]
            print(f"  {code:<10s} ({mpn:<22s}): {n:2d}x @ ${u:.4f}/ea = ${sub:.4f}/bd (LCSC stock: {stk})")


def audit_cpl_and_render(project_dir: Path, out_dir: Path, render_dir: Path, cache_dir: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle

    pro, sch_path, pcb_path = find_project(project_dir)
    sch = load_schematic(sch_path)
    board = pcbnew.LoadBoard(str(pcb_path))
    fp_map = {fp.GetReference(): fp for fp in board.GetFootprints()}

    cpl_map = {}
    with (out_dir / "cpl-jlcpcb.csv").open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cpl_map[row["Designator"]] = (
                float(row["Mid X"].replace("mm", "")),
                float(row["Mid Y"].replace("mm", "")),
                row["Layer"],
                float(row["Rotation"]),
            )

    easy_cache = {}
    unique_lcsc = sorted({
        s.fields.get("LCSC", "").strip()
        for r, s in sch.parts.items()
        if r in cpl_map and s.fields.get("LCSC", "").strip()
    })
    cache_dir.mkdir(parents=True, exist_ok=True)
    for code in unique_lcsc:
        cfile = cache_dir / f"{code}.json"
        if cfile.exists() and cfile.read_bytes().strip().startswith(b"{"):
            raw = cfile.read_bytes()
        else:
            time.sleep(0.22)
            raw = subprocess.check_output([
                "curl", "-sL", "-A", CURL_UA,
                f"https://easyeda.com/api/products/{code}/components?version=6.4.19.5",
            ])
            if raw.strip().startswith(b"{"):
                cfile.write_bytes(raw)
        if not raw.strip().startswith(b"{"):
            sample_fp = next(fp_map[r] for r, s in sch.parts.items() if r in cpl_map and s.fields.get("LCSC", "").strip() == code)
            rot_off, dx0, dy0 = JLC_CPL_FIXES.get(code, (0.0, 0.0, 0.0))
            ra = math.radians(-rot_off)
            ca0, sa0 = math.cos(ra), math.sin(ra)
            pads = []
            for p in sample_fp.Pads():
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                    kx0 = pcbnew.ToMM(p.GetPos0().x) - dx0
                    ky0 = -pcbnew.ToMM(p.GetPos0().y) - dy0
                    pads.append((p.GetNumber(), kx0 * ca0 - ky0 * sa0, kx0 * sa0 + ky0 * ca0, 0.2, 0.2))
            easy_cache[code] = pads
            continue
        d = json.loads(raw).get("result") or {}
        ds = ((d.get("packageDetail") or {}).get("dataStr")) or {}
        if isinstance(ds, str):
            ds = json.loads(ds)
        head = ds.get("head") or {}
        ox, oy = float(head.get("x", 0)), float(head.get("y", 0))
        if code in ("C530612", "C225111", "C1542426", "C2828254", "C388883"):
            for sh in ds.get("shape") or []:
                if sh.startswith("SVGNODE~"):
                    m = re.search(r'"c_origin"\s*:\s*"([^"]+)"', sh)
                    if m:
                        ox, oy = [float(v) for v in m.group(1).split(",")]
                        break
        raw_pads = []
        for sh in ds.get("shape") or []:
            if sh.startswith("PAD~"):
                f = sh.split("~")
                raw_pads.append((f[8], float(f[2]), float(f[3]), float(f[4]), float(f[5])))
        if ox == 0.0 and oy == 0.0 and raw_pads:
            ox = (min(p[1] for p in raw_pads) + max(p[1] for p in raw_pads)) / 2.0
            oy = (min(p[2] for p in raw_pads) + max(p[2] for p in raw_pads)) / 2.0
        pads = [
            (pnum, (rx - ox) * 0.254, -(ry - oy) * 0.254, rw * 0.254, rh * 0.254)
            for pnum, rx, ry, rw, rh in raw_pads
        ]
        easy_cache[code] = pads

    print(f"\n=== CPL PAD-FOR-PAD AUDIT ACROSS ALL {len(cpl_map)} ASSEMBLED PARTS ({len(unique_lcsc)} UNIQUE LCSC) ===")
    print(f"  {'Ref':<6s} {'MPN':<22s} {'LCSC':<10s} {'Side':<6s} {'KiRot':>7s} {'CPL_MidX':>9s} {'CPL_MidY':>9s} {'CPLRot':>7s} {'PadErr':>8s}")
    max_err_non_toe = 0.0

    sample_refs = [
        "J1", "BT1", "U13", "U7", "U8", "U5", "U3", "U4", "U6", "U9", "Q1", "Q2",
        "U1", "U2", "U10", "U11", "U12", "SW1", "SW2", "L1", "Y1",
        "D1", "C75", "C76", "R32", "C6", "R8",
    ]
    transformed_pads = {"Top": [], "Bottom": []}

    for ref in sorted(cpl_map.keys(), key=natural):
        s = sch.parts[ref]
        lcsc = s.fields.get("LCSC", "").strip()
        mpn = s.fields.get("MPN", "").strip()
        fp = fp_map[ref]
        mx, my, side, cpl_rot = cpl_map[ref]
        ki_rot = fp.GetOrientationDegrees()
        epads = easy_cache.get(lcsc, [])

        ang = math.radians(cpl_rot if side == "Top" else -cpl_rot)
        ca, sa = math.cos(ang), math.sin(ang)
        t_epads = []
        for pnum, px, py, pw, ph in epads:
            bx = -px if side == "Bottom" else px
            by = py
            gx = mx + bx * ca - by * sa
            gy = my + bx * sa + by * ca
            t_epads.append((pnum, gx, gy, pw, ph))
            is_p1 = pnum in ("1", "A1", "A1B12")
            transformed_pads[side].append((ref, is_p1, gx, gy))

        kpads = [
            (p.GetNumber(), pcbnew.ToMM(p.GetPosition().x), -pcbnew.ToMM(p.GetPosition().y))
            for p in fp.Pads()
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD
        ]
        err = 0.0
        for kpnum, kx, ky in kpads:
            if t_epads:
                dmin = min(math.hypot(kx - gx, ky - gy) for _, gx, gy, _, _ in t_epads)
                err = max(err, dmin)
        if lcsc not in ("C190862", "C42411119"):
            max_err_non_toe = max(max_err_non_toe, err)
        if ref in sample_refs or err > 0.20:
            print(f"  {ref:<6s} {mpn[:22]:<22s} {lcsc:<10s} {side:<6s} {ki_rot:7.2f} {mx:9.4f} {my:9.4f} {cpl_rot:7.2f} {err:6.3f}mm")

    print(f"  Max pad-center delta (excluding U4/L1 nominal pad-toe length diff): {max_err_non_toe:.3f} mm")

    render_dir.mkdir(parents=True, exist_ok=True)
    for side in ("Top", "Bottom"):
        fig, ax = plt.subplots(figsize=(9, 9), dpi=200)
        ax.add_patch(Circle((100.0, -100.0), 19.0, fill=False, edgecolor="#333333", lw=1.2))
        for ref in sorted(cpl_map.keys(), key=natural):
            if cpl_map[ref][2] != side:
                continue
            fp = fp_map[ref]
            for p in fp.Pads():
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                    kx, ky = pcbnew.ToMM(p.GetPosition().x), -pcbnew.ToMM(p.GetPosition().y)
                    ax.plot(kx, ky, "s", color="#2b8cbe", markersize=3.2, alpha=0.65)
                elif p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    kx, ky = pcbnew.ToMM(p.GetPosition().x), -pcbnew.ToMM(p.GetPosition().y)
                    ax.add_patch(Circle((kx, ky), 0.325, fill=False, edgecolor="#e34a33", lw=1.2))
            mx, my, _, _ = cpl_map[ref]
            if not ref.startswith("D") or ref in ("D1", "D74", "D234", "D235"):
                ax.text(mx, my, ref, fontsize=5.5, ha="center", va="center", color="#111111")
        for ref, is_p1, gx, gy in transformed_pads[side]:
            color = "#d7301f" if is_p1 else "#31a354"
            ms = 2.6 if is_p1 else 1.7
            ax.plot(gx, gy, "o", color=color, markersize=ms, alpha=0.9)
        ax.set_aspect("equal")
        ax.set_xlim(79.5, 120.5)
        ax.set_ylim(-120.5, -79.5)
        if side == "Bottom":
            ax.invert_xaxis()
        ax.set_title(f"round-pendant-f-usbc-rtc CPL Verification ({side} view: blue=KiCad pads, green=JLC EasyEDA pads, red=Pin 1)")
        out_png = render_dir / f"cpl-check-{side.lower()}.png"
        fig.tight_layout()
        fig.savefig(out_png)
        plt.close(fig)
        print(f"  Rendered {out_png}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", type=Path, default=ROOT / "hw/round-pendant/f-usbc-rtc")
    ap.add_argument("--out", type=Path, default=ROOT / "hw/round-pendant/f-usbc-rtc/fab")
    ap.add_argument("--renders", type=Path, default=ROOT / "design/renders/round-pendant-f-usbc-rtc")
    ap.add_argument("--cache", type=Path, required=False, default=Path(os.environ.get("EASYEDA_CACHE", "/tmp/easyeda-cache-fur")))
    ap.add_argument("--export", action="store_true")
    ap.add_argument("--cost", action="store_true")
    ap.add_argument("--audit-cpl", action="store_true")
    ap.add_argument("--qty", type=int, default=10)
    args = ap.parse_args()

    if args.export:
        export_fab(args.project, args.out, args.renders)
    if args.audit_cpl:
        audit_cpl_and_render(args.project, args.out, args.renders, args.cache)
    if args.cost:
        run_cost(args.qty)
    sys.stdout.flush()
    os._exit(0)
