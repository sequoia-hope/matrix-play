#!/usr/bin/env python3
"""export_fab.py -- Export 8-layer JLCPCB Gerbers + Excellon drill + BOM + CPL + Schematic PDF for dense-square."""
from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude/skills/pcb-design/scripts"))
sys.path.insert(0, str(ROOT / "scripts/dense_square"))

from kicad_files import find_project, load_schematic  # noqa: E402
from config import VARIANTS  # noqa: E402

LAYERS_8L = ",".join([
    "F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu",
    "F.Paste", "B.Paste",
    "F.Silkscreen", "B.Silkscreen",
    "F.Mask", "B.Mask",
    "Edge.Cuts",
])


def natural(ref: str):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", ref)]


def export_fab(variant: str):
    import pcbnew

    spec = VARIANTS[variant]
    hw = spec.hw_dir
    _, sch_path, pcb_path = find_project(hw)
    out_dir = hw / "fab"
    out_dir.mkdir(parents=True, exist_ok=True)
    gdir = Path(f"/tmp/dense-square-gerbers-{variant}")
    if gdir.exists():
        for f in gdir.iterdir():
            if f.is_file():
                f.unlink()
    else:
        gdir.mkdir(parents=True, exist_ok=True)

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
            "--drill-origin", "absolute",
            "--excellon-units", "mm",
            "-o", str(gdir) + "/",
            str(pcb_path),
        ],
        check=True,
    )

    zpath = out_dir / f"dense-square-{variant}-gerbers.zip"
    gerber_files = sorted(f for f in gdir.iterdir() if f.is_file() and not f.name.endswith("-drl_map.gbr"))
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in gerber_files:
            zf.write(f, f.name)

    pdf_path = out_dir / f"dense-square-{variant}-schematic.pdf"
    render_pdf = ROOT / f"design/renders/schematic/dense-square-{variant}.pdf"
    if render_pdf.exists():
        shutil.copy2(render_pdf, pdf_path)
    else:
        subprocess.run(
            ["kicad-cli", "sch", "export", "pdf", "--output", str(pdf_path), str(sch_path)],
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
        fp = fp_map[ref]
        lcsc = s.fields.get("LCSC", "").strip()
        mpn = s.fields.get("MPN", "").strip()
        mfr = s.fields.get("Manufacturer", "").strip()
        pkg = s.footprint.split(":", 1)[-1] if ":" in s.footprint else s.footprint
        bom_groups.setdefault((s.value, pkg, lcsc, mpn, mfr), []).append(ref)
        pos = fp.GetPosition()
        x_mm = pcbnew.ToMM(pos.x)
        y_mm = -pcbnew.ToMM(pos.y)
        side = "Bottom" if fp.IsFlipped() else "Top"
        # LED_MHPA0808RGBDT (C404279) is defined directly in JLCPCB/EasyEDA -BR carrier-tape orientation (0 deg offset).
        rot = fp.GetOrientationDegrees() % 360.0
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

    print(
        f"Exported {zpath} ({len(gerber_files)} files), {pdf_path.name}, "
        f"{bom_path.name} ({len(bom_groups)} lines), {cpl_path.name} ({len(cpl_rows)} parts)",
        flush=True,
    )
    os._exit(0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("variant", choices=list(VARIANTS.keys()))
    args = ap.parse_args()
    export_fab(args.variant)
