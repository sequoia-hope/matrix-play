#!/usr/bin/env python3
"""critpass_d.py -- Pass 1 critical-net pre-route for Variant D (crystal, USB diff pair, QSPI, BOOTSEL).

Strips matrix nets (CS/SW) onto a temporary copy, routes unobstructed with ultraroute so crystal (0 vias, <=11mm),
USB_DM/DP (<=1 via, diff coupled), and QSPI (<=25mm) claim clean paths first, then locks ONLY those critical
tracks/vias onto hw/round-pendant/d/round-pendant.kicad_pcb ready for full matrix routing.
"""
import collections
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VARIANT = os.environ.get("PENDANT_VARIANT", "d")
HW = ROOT / f"hw/round-pendant/{VARIANT}"
PCB = HW / "round-pendant.kicad_pcb"
SCRATCH = Path("/tmp/d-critpass")

CRIT_PAT = re.compile(r"XIN|XOUT|C24-Pad1|USB_D|QSPI|R16-Pad2")


def main():
    SCRATCH.mkdir(parents=True, exist_ok=True)
    pro_bytes = (HW / "round-pendant.kicad_pro").read_bytes()

    # Save clean unrouted snapshot
    (HW / "route").mkdir(exist_ok=True)
    pre = HW / "route/preroute_8L.kicad_pcb"
    shutil.copy2(PCB, pre)

    # 1. Strip matrix nets on scratch board (MUST pass PCB so pcbnew finds round-pendant.kicad_pro,
    #    then copy .kicad_pro/.kicad_dru AFTER SaveBoard so SaveBoard cannot overwrite .kicad_pro!)
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts/two_pass.py"), "strip", str(PCB), str(SCRATCH / "round-pendant.kicad_pcb")],
        capture_output=True,
        text=True,
        check=True,
    )
    for fn in ("round-pendant.kicad_pro", "round-pendant.kicad_dru", "fp-lib-table", "sym-lib-table"):
        shutil.copy2(HW / fn, SCRATCH / fn)
    print("strip:", r.stdout.strip().splitlines()[-1])

    # 2. Route non-matrix nets on scratch board
    bin_r = subprocess.run([str(ROOT / "scripts/route.sh"), "--build"], capture_output=True, text=True, check=True)
    ur_bin = bin_r.stdout.strip().splitlines()[-1]
    routed_p1 = SCRATCH / "routed_p1.kicad_pcb"
    cmd = [
        ur_bin,
        "route",
        str(SCRATCH / "round-pendant.kicad_pcb"),
        "-o",
        str(routed_p1),
        "--strip",
        "--planes",
        "In2.Cu,In5.Cu",
        "--negotiate",
        "--rip-up",
        "--tighten",
        "--prefanout",
        "--prefanout-order",
        "inner",
        "--prefanout-mode",
        "inner",
        "--diff-pairs",
        "--shove-plough",
        "region",
        "--shove-reach",
        "0.5",
        "--shove-repair",
        "20",
        "--shove-ties",
        "--shove-passes",
        "60",
        "--shove-patience",
        "8",
        "--cell",
        "0.025",
        "--threads",
        "2",
        "--timeout",
        "240",
    ]
    p1 = subprocess.run(cmd, capture_output=True, text=True, check=True)
    (SCRATCH / "p1.log").write_text(p1.stdout + p1.stderr)
    for ln in (p1.stdout + p1.stderr).splitlines():
        if any(ln.startswith(k) for k in ("memory:", "prefanout:", "planes:", "pairs:", "negotiated", "rip-up:", "rules:", "open ", "routed ")):
            print("  p1:", ln)

    # 3. Dump unlocked non-matrix copper and filter to CRIT_PAT
    d_r = subprocess.run(
        [sys.executable, str(ROOT / "scripts/two_pass.py"), "dump", str(routed_p1)],
        capture_output=True,
        text=True,
        check=True,
    )
    items = json.loads(d_r.stdout.strip().splitlines()[-1])
    crit = [e for e in items if CRIT_PAT.search(e["net"])]
    crit_json = SCRATCH / "crit.json"
    crit_json.write_text(json.dumps(crit))
    counts = collections.Counter(e["net"].split("/")[-1] for e in crit)
    vias = collections.Counter(e["net"].split("/")[-1] for e in crit if "via" in e)
    print("critical items:", len(crit), "of", len(items), "by net:", dict(counts), "vias:", dict(vias))

    # 4. Merge locked critical copper onto PCB and refill zones
    shutil.copy2(pre, PCB)
    m_r = subprocess.run(
        [sys.executable, str(ROOT / "scripts/two_pass.py"), "merge", str(PCB), str(crit_json)],
        capture_output=True,
        text=True,
        check=True,
    )
    import pcbnew
    b_m = pcbnew.LoadBoard(str(PCB))
    pcbnew.ZONE_FILLER(b_m).Fill(b_m.Zones())
    pcbnew.SaveBoard(str(PCB), b_m)
    (HW / "round-pendant.kicad_pro").write_bytes(pro_bytes)
    print("merge:", m_r.stdout.strip().splitlines()[-1])


if __name__ == "__main__":
    main()
