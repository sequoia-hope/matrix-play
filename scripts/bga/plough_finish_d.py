#!/usr/bin/env python3
"""plough_finish_d.py -- Governed ultraroute --adopt plough search judged by KiCad DRC.

Uses the pinned vendor/ultraroute binary (`scripts/route.sh`) with `--adopt` (matching
`vendor/ultraroute/tools/search.py` and `.claude/skills/pcb-design/scripts/autoroute.py`)
to finish the last open signal connections without breaking any DRC rule, then unlocks
routed copper per LESSONS.md.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REFILL_PY = """
import os, sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[1], b)
sys.stdout.flush()
os._exit(0)
"""

UNLOCK_SIGNAL_COPPER_PY = """
import math, os, sys, pcbnew
CRIT_LOCK = ("+1V1", "VBAT", "BAT_N", "VBUS", "XIN", "XOUT", "C24-Pad1", "USB_D", "QSPI", "VREG_")
b = pcbnew.LoadBoard(sys.argv[1])
um = pcbnew.ToMM
fps = {f.GetReference(): f for f in b.GetFootprints()}
via_pts = {(v.GetNetname(), round(um(v.GetPosition().x), 3), round(um(v.GetPosition().y), 3)): v
           for v in b.GetTracks() if isinstance(v, pcbnew.PCB_VIA)}
pts = set()
for r in ("U1", "U2", "U10", "U11", "U12"):
    for p in fps[r].Pads():
        pts.add((p.GetNetname(), round(um(p.GetPosition().x), 3), round(um(p.GetPosition().y), 3)))
bcu_trks = [t for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA) and t.GetLayerName() == "B.Cu"]
bga_keep = set()
changed = True
while changed:
    changed = False
    for t in bcu_trks:
        if id(t) in bga_keep:
            continue
        n = t.GetNetname()
        p1 = (n, round(um(t.GetStart().x), 3), round(um(t.GetStart().y), 3))
        p2 = (n, round(um(t.GetEnd().x), 3), round(um(t.GetEnd().y), 3))
        m1 = any(pn == n and math.hypot(px - p1[1], py - p1[2]) < 0.12 for pn, px, py in pts)
        m2 = any(pn == n and math.hypot(px - p2[1], py - p2[2]) < 0.12 for pn, px, py in pts)
        if m1 or m2:
            bga_keep.add(id(t))
            changed = True
            for ep in (p1, p2):
                hit_via = [v for (vn, vx, vy), v in via_pts.items() if vn == n and math.hypot(vx - ep[1], vy - ep[2]) < 0.05]
                if hit_via:
                    for v in hit_via:
                        bga_keep.add(id(v))
                else:
                    pts.add(ep)
unlocked = 0
locked_crit = 0
for t in b.GetTracks():
    n = t.GetNetname()
    if any(k in n for k in CRIT_LOCK) or id(t) in bga_keep:
        if not t.IsLocked():
            t.SetLocked(True)
            locked_crit += 1
    else:
        if t.IsLocked():
            t.SetLocked(False)
            unlocked += 1
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[1], b)
print(f"unlocked {unlocked} non-critical items, locked {locked_crit} critical+BGA-escape items ({len(bga_keep)} BGA escape), refilled zones", flush=True)
os._exit(0)
"""

UNLOCK_TRACKS_PY = """
import os, sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
for t in b.GetTracks():
    t.SetLocked(False)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[1], b)
sys.stdout.flush()
os._exit(0)
"""

COSMETIC_TYPES = {
    "track_dangling",
    "via_dangling",
    "silk_over_copper",
    "silk_overlap",
    "silk_edge_clearance",
    "text_height",
    "text_thickness",
}

PLANE_NETS = {"GND", "VSYS", "+3V3"}


def get_ultraroute_bin() -> Path:
    r = subprocess.run([str(ROOT / "scripts" / "route.sh"), "--build"], capture_output=True, text=True, check=True)
    return Path(r.stdout.strip().splitlines()[-1])


def kicad_judge(pcb_path: Path, pro_bak: Path, dru_path: Path) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        c_pcb = Path(tmp) / pcb_path.name
        shutil.copy2(pcb_path, c_pcb)
        shutil.copy2(pro_bak, c_pcb.with_suffix(".kicad_pro"))
        if dru_path.exists():
            shutil.copy2(dru_path, c_pcb.with_suffix(".kicad_dru"))
        subprocess.run([sys.executable, "-c", REFILL_PY, str(c_pcb)], capture_output=True, check=True)
        drc_out = Path(tmp) / "drc.json"
        subprocess.run(
            ["kicad-cli", "pcb", "drc", "--format", "json", "--severity-error", "-o", str(drc_out), str(c_pcb)],
            capture_output=True,
            check=True,
        )
        d = json.loads(drc_out.read_text())

    def is_plane(u: dict) -> bool:
        return all(any(f"[{n}]" in i["description"] for n in PLANE_NETS) for i in u["items"])

    unconn = d.get("unconnected_items", [])
    sig_opens = [" / ".join(i["description"] for i in u["items"]) for u in unconn if not is_plane(u)]
    pln_opens = [" / ".join(i["description"] for i in u["items"]) for u in unconn if is_plane(u)]
    hard_errs = [v for v in d.get("violations", []) if v["type"] not in COSMETIC_TYPES]
    dang_errs = [v for v in d.get("violations", []) if v["type"] in ("track_dangling", "via_dangling")]
    return {
        "sig_open": len(sig_opens),
        "pln_open": len(pln_opens),
        "hard_err": len(hard_errs),
        "dangling": len(dang_errs),
        "sig_open_list": sig_opens,
        "pln_open_list": pln_opens,
        "hard_err_types": dict(collections.Counter(v["type"] for v in hard_errs)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pcb", type=Path)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=240)
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--memory", default="8G")
    args = ap.parse_args()

    pcb = args.pcb.resolve()
    out_dir = pcb.parent / "route"
    pro_path = pcb.with_suffix(".kicad_pro")
    pro_bak = out_dir / "round-pendant.kicad_pro.bak"
    if not pro_bak.exists():
        shutil.copy2(pro_path, pro_bak)
    dru_path = pcb.with_suffix(".kicad_dru")

    exe = get_ultraroute_bin()
    base_v = kicad_judge(pcb, pro_bak, dru_path)
    print(
        f"Initial KiCad verdict on {pcb.name}: sig_open={base_v['sig_open']}, "
        f"pln_open={base_v['pln_open']}, hard_err={base_v['hard_err']}, dangling={base_v['dangling']}",
        flush=True,
    )
    for o in base_v["sig_open_list"]:
        print(f"  open: {o}", flush=True)
    if base_v["sig_open"] == 0 and base_v["pln_open"] == 0 and base_v["hard_err"] == 0:
        print("Already 0 open and 0 hard errors!", flush=True)
        return 0

    best_pcb = out_dir / "plough_best.kicad_pcb"
    shutil.copy2(pcb, best_pcb)
    r_unl = subprocess.run([sys.executable, "-c", UNLOCK_SIGNAL_COPPER_PY, str(best_pcb)], capture_output=True, text=True, check=True)
    # CRITICAL: SaveBoard creates a blank default plough_best.kicad_pro (0.20 mm clearance!).
    # Copy the real .kicad_pro and .kicad_dru beside best_pcb so ultraroute reads 0.09 mm clearance + all DRU rules!
    shutil.copy2(pro_bak, best_pcb.with_suffix(".kicad_pro"))
    if dru_path.exists():
        shutil.copy2(dru_path, best_pcb.with_suffix(".kicad_dru"))
    print(" ", r_unl.stdout.strip(), flush=True)
    best_score = (base_v["hard_err"], base_v["sig_open"] + base_v["pln_open"], base_v["sig_open"])

    recipes = [
        ("ripreg_tight", [
            "--adopt",
            "--rip-region", "92.6,93.0,1.6",
            "--rip-region", "99.6,89.1,1.8",
            "--rip-region", "103.5,88.2,2.0",
            "--negotiate", "--rip-up",
            "--shove-plough", "region", "--shove-reach", "1.0", "--shove-cascade", "2",
            "--shove-repair", "10", "--shove-ties", "--shove-passes", "60", "--shove-patience", "8",
            "--tighten", "--planes", "In2.Cu,In5.Cu", "--cell", "0.025", "--blame",
        ]),
        ("ripreg_wide", [
            "--adopt",
            "--rip-region", "92.6,93.0,2.2",
            "--rip-region", "99.8,88.8,2.5",
            "--rip-region", "104.2,87.4,2.8",
            "--negotiate", "--rip-up",
            "--shove-plough", "region", "--shove-reach", "1.0", "--shove-cascade", "2",
            "--shove-repair", "12", "--shove-ties", "--shove-passes", "60", "--shove-patience", "8",
            "--tighten", "--planes", "In2.Cu,In5.Cu", "--cell", "0.025", "--blame",
        ]),
        ("cascade_region", [
            "--adopt", "--rip-up",
            "--shove-plough", "region", "--shove-reach", "1.0", "--shove-cascade", "3",
            "--shove-repair", "10", "--shove-ties", "--shove-passes", "60", "--shove-patience", "8",
            "--tighten", "--planes", "In2.Cu,In5.Cu", "--cell", "0.025", "--blame",
        ]),
    ]

    run_idx = 0
    for seed in range(1, args.seeds + 1):
        for rname, rflags in recipes:
            run_idx += 1
            cand = out_dir / f"plough_{rname}_s{seed}.kicad_pcb"
            cand.unlink(missing_ok=True)
            cmd = [
                str(exe), "route", str(best_pcb), "-o", str(cand),
                *rflags, "--threads", str(args.threads), "--timeout", str(args.timeout), "--seed", str(seed),
            ]
            gov = ["nice", "-n", "15", "timeout", str(args.timeout + 90)]
            if shutil.which("systemd-run"):
                gov = [
                    "systemd-run", "--user", "--scope", "--quiet",
                    "-p", f"MemoryMax={args.memory}", "-p", "MemorySwapMax=0",
                    "-p", f"CPUQuota={args.threads * 100}%",
                ] + gov
            print(f"[run {run_idx}] {rname} seed={seed} starting from best={best_score} ...", flush=True)
            r = subprocess.run(gov + cmd, capture_output=True, text=True)
            (out_dir / f"plough_{rname}_s{seed}.log").write_text(r.stdout + r.stderr)
            if r.returncode != 0 or not cand.exists():
                print(f"  router exited {r.returncode}: {(r.stderr or r.stdout).strip()[-300:]}", flush=True)
                continue
            v = kicad_judge(cand, pro_bak, dru_path)
            sc = (v["hard_err"], v["sig_open"] + v["pln_open"], v["sig_open"])
            tail = (r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout + r.stderr).strip() else ""
            print(
                f"  -> sig_open={v['sig_open']}, pln_open={v['pln_open']}, hard_err={v['hard_err']} "
                f"{v['hard_err_types'] or ''} ({tail})",
                flush=True,
            )
            for o in v["sig_open_list"]:
                print(f"     open: {o}", flush=True)
            if sc < best_score:
                best_score = sc
                shutil.copy2(cand, best_pcb)
                subprocess.run([sys.executable, "-c", REFILL_PY, str(best_pcb)], capture_output=True, check=True)
                shutil.copy2(pro_bak, best_pcb.with_suffix(".kicad_pro"))
                print(f"  ** NEW BEST: {best_score} **", flush=True)
            if v["sig_open"] == 0 and v["pln_open"] == 0 and v["hard_err"] == 0:
                shutil.copy2(cand, pcb)
                subprocess.run([sys.executable, "-c", UNLOCK_TRACKS_PY, str(pcb)], capture_output=True, check=True)
                shutil.copy2(pro_bak, pro_path)
                vf = kicad_judge(pcb, pro_bak, dru_path)
                print(
                    f"COMPLETE! Unlocked & refilled {pcb.name}: sig_open={vf['sig_open']}, "
                    f"pln_open={vf['pln_open']}, hard_err={vf['hard_err']}, dangling={vf['dangling']}",
                    flush=True,
                )
                return 0

    # Save best found so far even if > 0 open
    shutil.copy2(best_pcb, pcb)
    subprocess.run([sys.executable, "-c", REFILL_PY, str(pcb)], capture_output=True, check=True)
    shutil.copy2(pro_bak, pro_path)
    print(f"Finished search at best={best_score}", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
