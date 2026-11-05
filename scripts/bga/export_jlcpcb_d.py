#!/usr/bin/env python3
"""export_jlcpcb_d.py -- Export JLCPCB fabrication + PCBA assembly files for Variant D.

Outputs in hw/round-pendant/d/fab/ (or custom OUT_DIR):
  gerbers/                      8-layer Gerbers + Excellon drill + drill maps
  round-pendant-d-gerbers.zip   Upload to JLCPCB PCB quote
  bom-jlcpcb.csv                Upload to JLCPCB PCBA quote (BOM)
  cpl-jlcpcb.csv                Upload to JLCPCB PCBA quote (CPL / Pick & Place)

Schematic is the single source of truth for BOM values, footprints, MPNs, and LCSC codes;
board footprints provide exact placement centroids, sides, and rotations.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "pcb-design" / "scripts"))
from kicad_files import find_project, load_schematic  # noqa: E402

LAYERS_8L = ",".join([
    "F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu",
    "F.Paste", "B.Paste",
    "F.Silkscreen", "B.Silkscreen",
    "F.Mask", "B.Mask",
    "Edge.Cuts",
])


def natural(ref: str):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", ref)]


def run_cmd(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write("FAILED: " + " ".join(cmd) + "\n")
        sys.stderr.write(r.stdout + "\n" + r.stderr + "\n")
        sys.exit(r.returncode)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", type=Path, default=ROOT / "hw" / "round-pendant" / "d")
    ap.add_argument("--out", type=Path, default=ROOT / "hw" / "round-pendant" / "d" / "fab")
    args = ap.parse_args()

    pro, sch_path, pcb_path = find_project(args.project)
    out_dir = args.out
    gdir = out_dir / "gerbers"
    gdir.mkdir(parents=True, exist_ok=True)

    # 1. Export 8-layer Gerbers + Excellon drills
    run_cmd([
        "kicad-cli", "pcb", "export", "gerbers",
        "--layers", LAYERS_8L,
        "--subtract-soldermask",
        "-o", str(gdir) + "/",
        str(pcb_path),
    ])
    run_cmd([
        "kicad-cli", "pcb", "export", "drill",
        "--format", "excellon",
        "--drill-origin", "absolute",
        "--excellon-units", "mm",
        "-o", str(gdir) + "/",
        str(pcb_path),
    ])

    zpath = out_dir / "round-pendant-d-gerbers.zip"
    gerber_files = sorted(
        f for f in gdir.iterdir()
        if f.is_file() and not f.name.endswith("-drl_map.gbr")
    )
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in gerber_files:
            zf.write(f, f.name)

    # 2. Build BOM (from schematic source of truth) + CPL (from PCB centroids)
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
        key = (s.value, pkg, lcsc, mpn, mfr)
        bom_groups.setdefault(key, []).append(ref)

        pos = fp.GetPosition()
        x_mm = pcbnew.ToMM(pos.x)
        y_mm = -pcbnew.ToMM(pos.y)  # JLCPCB / Gerber +Y up convention
        side = "Bottom" if fp.IsFlipped() else "Top"
        rot = fp.GetOrientationDegrees() % 360.0
        cpl_rows.append([
            ref,
            f"{x_mm:.4f}mm",
            f"{y_mm:.4f}mm",
            side,
            f"{rot:.2f}",
        ])

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
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
