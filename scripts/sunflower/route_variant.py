#!/usr/bin/env python3
"""route_variant.py -- Three-stage 4-layer ultraroute driver for hw/sunflower/<variant>/.

Stage 1: strips matrix CS/SW nets onto a scratch copy and routes critical MCU nets unobstructed
         (12 MHz crystal <=11 mm 0 vias, USB diff pair, QSPI <=25 mm), locking clean critical copper.
Stage 2: runs `.claude/skills/pcb-design/scripts/autoroute.py` with `--planes In1.Cu` (sequential negotiation + rip-up).
Stage 3: if Stage 2 leaves > 0 open (because negotiation + rip-up hit budget before MergeEscapes + Shove),
         unlocks non-crystal copper and runs `ultraroute --adopt --shove-plough region ... --tighten --blame`
         so region-ploughing + via cleanup + tighten run with a dedicated budget, judged by KiCad DRC.

Book cores before invoking:
    timeout 5400 ~/.claude/bin/reserve -c 4 --here -l "route p2-132" -- \
        python3 scripts/sunflower/route_variant.py p2-132 --fresh --seeds 1 --threads 4
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
sys.path.insert(0, str(ROOT / "scripts/sunflower"))
from config import VARIANTS  # noqa: E402

CRIT_PAT = re.compile(r"XIN|XOUT|C24-Pad1|USB_D|QSPI")
XTAL_PAT = re.compile(r"XIN|XOUT|C24-Pad1")


def refill_board(pcb_path: Path, pro_bytes: bytes):
    code = (
        "import os, sys, pcbnew\n"
        "b = pcbnew.LoadBoard(sys.argv[1])\n"
        "pcbnew.ZONE_FILLER(b).Fill(b.Zones())\n"
        "pcbnew.SaveBoard(sys.argv[1], b)\n"
        "os._exit(0)\n"
    )
    subprocess.run([sys.executable, "-c", code, str(pcb_path)], check=True)
    (pcb_path.parent / "sunflower.kicad_pro").write_bytes(pro_bytes)


def unlock_for_plough(pcb_path: Path, pro_bytes: bytes):
    """Keep GND/+1V1 pad/ring thermal vias, U3 B.Cu IOVDD/FB decap links, and 0-via crystal tracks locked; unlock everything else."""
    code = (
        "import os, re, sys, pcbnew\n"
        "XTAL = re.compile(r'XIN|XOUT|C24-Pad1')\n"
        "b = pcbnew.LoadBoard(sys.argv[1])\n"
        "B_CU = b.GetLayerID('B.Cu')\n"
        "_u3 = [f for f in b.GetFootprints() if f.GetReference() == 'U3'][0].GetPosition()\n"
        "U3X, U3Y = pcbnew.ToMM(_u3.x), pcbnew.ToMM(_u3.y)\n"
        "um = pcbnew.ToMM\n"
        "for t in b.GetTracks():\n"
        "    if isinstance(t, pcbnew.PCB_VIA):\n"
        "        if t.GetNetname() not in ('GND', '+1V1'):\n"
        "            t.SetLocked(False)\n"
        "    else:\n"
        "        x0, y0 = um(t.GetStart().x), um(t.GetStart().y)\n"
        "        u3_decap = t.IsLocked() and t.GetLayer() == B_CU and t.GetNetname() in ('+3V3', '+1V1') and abs(x0 - U3X) < 6.0 and abs(y0 - U3Y) < 7.0\n"
        "        if not XTAL.search(t.GetNetname()) and not u3_decap:\n"
        "            t.SetLocked(False)\n"
        "pcbnew.ZONE_FILLER(b).Fill(b.Zones())\n"
        "pcbnew.SaveBoard(sys.argv[1], b)\n"
        "os._exit(0)\n"
    )
    subprocess.run([sys.executable, "-c", code, str(pcb_path)], check=True)
    (pcb_path.parent / "sunflower.kicad_pro").write_bytes(pro_bytes)


def kicad_verdict(pcb_path: Path, pro_path: Path, dru_path: Path) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "sunflower.kicad_pcb"
        shutil.copy2(pcb_path, copy)
        shutil.copy2(pro_path, copy.with_suffix(".kicad_pro"))
        shutil.copy2(dru_path, copy.with_suffix(".kicad_dru"))
        subprocess.run(
            [
                sys.executable,
                "-c",
                "import os, sys, pcbnew; b = pcbnew.LoadBoard(sys.argv[1]); zf = pcbnew.ZONE_FILLER(b); zs = b.Zones(); zf.Fill(zs); pcbnew.SaveBoard(sys.argv[1], b); os._exit(0)",
                str(copy),
            ],
            check=True,
        )
        copy.with_suffix(".kicad_pro").write_bytes(pro_path.read_bytes())
        drc_out = Path(tmp) / "drc.json"
        subprocess.run(
            ["kicad-cli", "pcb", "drc", "--format", "json", "--severity-error", "-o", str(drc_out), str(copy)],
            capture_output=True,
            check=True,
        )
        d = json.loads(drc_out.read_text())
    unconn = d.get("unconnected_items", [])
    plane_opens = [u for u in unconn if all("[GND]" in i["description"] for i in u["items"])]
    sig_opens = [u for u in unconn if u not in plane_opens]
    cosmetic = {"track_dangling", "via_dangling", "silk_over_copper", "silk_overlap", "silk_edge_clearance", "text_height", "text_thickness"}
    hard_errs = [v for v in d.get("violations", []) if v["type"] not in cosmetic]
    real_hard = [v for v in hard_errs if v["type"] != "connection_width"]
    vias = len(re.findall(r"^\s*\(via\b", pcb_path.read_text(), re.M))
    return {
        "sig_open": len(sig_opens),
        "plane_open": len(plane_opens),
        "hard_err": len(hard_errs),
        "real_hard": len(real_hard),
        "total_err": len(d.get("violations", [])),
        "vias": vias,
        "sig_open_items": [" / ".join(i["description"] for i in u["items"]) for u in sig_opens],
        "hard_err_types": dict(collections.Counter(v["type"] for v in hard_errs)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("variant", choices=list(VARIANTS.keys()))
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=780, help="Stage 2 autoroute.py seconds per seed")
    ap.add_argument("--plough-timeout", type=int, default=600, help="Stage 3 --adopt region-plough seconds")
    ap.add_argument("--plough-seed", type=int, default=3, help="Stage 3 seed")
    ap.add_argument("--shove-reach", type=float, default=0.6, help="Stage 3 initial --shove-reach mm")
    ap.add_argument("--shove-repair", type=int, default=15, help="Stage 3 --shove-repair seconds")
    ap.add_argument("--rip-region", action="append", default=[], help="Stage 3 --rip-region X,Y,R (KiCad mm coords, Y positive)")
    ap.add_argument("--extra", default="--cell 0.025")
    ap.add_argument("--fresh", action="store_true", help="overwrite preroute_4L.kicad_pcb from current unrouted PCB")
    ap.add_argument("--continue-plough", action="store_true", help="skip Stage 1/2 and run Stage 3 --adopt plough directly on current PCB")
    args = ap.parse_args()

    spec = VARIANTS[args.variant]
    hw = spec.hw_dir
    pcb = hw / "sunflower.kicad_pcb"
    pro = hw / "sunflower.kicad_pro"
    dru = hw / "sunflower.kicad_dru"
    pro_bytes = pro.read_bytes()

    route_dir = hw / "route"
    route_dir.mkdir(exist_ok=True)
    pre = route_dir / "preroute_4L.kicad_pcb"
    bin_r = subprocess.run([str(ROOT / "scripts/route.sh"), "--build"], capture_output=True, text=True, check=True)
    ur_bin = bin_r.stdout.strip().splitlines()[-1]

    if not args.continue_plough:
        if args.fresh or not pre.exists():
            shutil.copy2(pcb, pre)
        else:
            shutil.copy2(pre, pcb)
            pro.write_bytes(pro_bytes)

        scratch = Path(f"/tmp/sunflower-crit-{args.variant}")
        scratch.mkdir(parents=True, exist_ok=True)

        # Stage 1: Critical MCU nets unobstructed
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts/two_pass.py"), "strip", str(pcb), str(scratch / "sunflower.kicad_pcb")],
            capture_output=True,
            text=True,
            check=True,
        )
        for fn in ("sunflower.kicad_pro", "sunflower.kicad_dru", "fp-lib-table", "sym-lib-table"):
            shutil.copy2(hw / fn, scratch / fn)
        print(f"[{args.variant}] Stage 1 strip:", r.stdout.strip().splitlines()[-1], flush=True)

        routed_p1 = scratch / "routed_p1.kicad_pcb"
        cmd_p1 = [
            ur_bin,
            "route",
            str(scratch / "sunflower.kicad_pcb"),
            "-o",
            str(routed_p1),
            "--strip",
            "--planes",
            "In1.Cu",
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
            str(min(2, args.threads)),
            "--timeout",
            "150",
        ]
        p1 = subprocess.run(cmd_p1, capture_output=True, text=True, check=True)
        (scratch / "p1.log").write_text(p1.stdout + p1.stderr)
        for ln in (p1.stdout + p1.stderr).splitlines():
            if any(ln.startswith(k) for k in ("prefanout:", "planes:", "pairs:", "negotiated", "rip-up:", "open ", "routed ")):
                print(f"  p1: {ln}", flush=True)

        d_r = subprocess.run(
            [sys.executable, str(ROOT / "scripts/two_pass.py"), "dump", str(routed_p1)],
            capture_output=True,
            text=True,
            check=True,
        )
        items = json.loads(d_r.stdout.strip().splitlines()[-1])
        crit = [e for e in items if CRIT_PAT.search(e["net"])]
        xtal_via_nets = {e["net"] for e in crit if "via" in e and XTAL_PAT.search(e["net"])}
        if xtal_via_nets:
            print(f"  dropping crystal nets with vias from Stage 1 lock: {xtal_via_nets}", flush=True)
            crit = [e for e in crit if e["net"] not in xtal_via_nets]

        crit_json = scratch / "crit.json"
        crit_json.write_text(json.dumps(crit))
        counts = collections.Counter(e["net"].split("/")[-1] for e in crit)
        vias = collections.Counter(e["net"].split("/")[-1] for e in crit if "via" in e)
        print(f"[{args.variant}] Stage 1 critical items: {len(crit)} of {len(items)}, vias={dict(vias)}, nets={dict(counts)}", flush=True)

        shutil.copy2(pre, pcb)
        m_r = subprocess.run(
            [sys.executable, str(ROOT / "scripts/two_pass.py"), "merge", str(pcb), str(crit_json)],
            capture_output=True,
            text=True,
            check=True,
        )
        pro.write_bytes(pro_bytes)
        refill_board(pcb, pro_bytes)
        print(f"[{args.variant}] Stage 1 merged: {m_r.stdout.strip().splitlines()[-1]}", flush=True)

        # Stage 2: Full matrix autoroute via skill's autoroute.py
        cmd_p2 = [
            sys.executable,
            str(ROOT / ".claude/skills/pcb-design/scripts/autoroute.py"),
            str(hw),
            "--planes",
            "In1.Cu",
            "--seeds",
            str(args.seeds),
            "--threads",
            str(args.threads),
            "--timeout",
            str(args.timeout),
        ]
        if args.extra:
            cmd_p2 += ["--extra", args.extra]
        p2 = subprocess.run(cmd_p2)
        pro.write_bytes(pro_bytes)
        refill_board(pcb, pro_bytes)
    else:
        p2 = subprocess.CompletedProcess([], 1)

    v2 = kicad_verdict(pcb, pro, dru)
    print(
        f"[{args.variant}] Stage 2 verdict: sig_open={v2['sig_open']}, plane_open={v2['plane_open']}, "
        f"hard_err={v2['hard_err']} {v2['hard_err_types']}, vias={v2['vias']}",
        flush=True,
    )
    if v2["sig_open"] == 0 and v2["plane_open"] == 0 and v2["hard_err"] == 0 and not args.rip_region:
        sys.exit(0)

    if args.plough_timeout <= 0:
        sys.exit(p2.returncode)

    # Stage 3: Governed --adopt region-plough finisher (runs MergeEscapes + Shove + Vias + Tighten directly!)
    plough_in = route_dir / "plough_in.kicad_pcb"
    plough_out = route_dir / "plough_out.kicad_pcb"
    shutil.copy2(pcb, plough_in)
    unlock_for_plough(plough_in, pro_bytes)
    shutil.copy2(pro, plough_in.with_suffix(".kicad_pro"))
    shutil.copy2(dru, plough_in.with_suffix(".kicad_dru"))
    plough_out.unlink(missing_ok=True)

    threads = max(1, min(args.threads, (os.cpu_count() or 2) // 2))
    gov = ["nice", "-n", "15", "timeout", str(args.plough_timeout + 120)]
    if shutil.which("systemd-run"):
        gov = [
            "systemd-run", "--user", "--scope", "--quiet",
            "-p", "MemoryMax=6G", "-p", "MemorySwapMax=0", "-p", f"CPUQuota={threads * 100}%",
        ] + gov
    cmd_p3 = [
        ur_bin, "route", str(plough_in), "-o", str(plough_out),
        "--adopt",
        "--shove-plough", "region", "--shove-reach", str(args.shove_reach),
        "--shove-repair", str(args.shove_repair), "--shove-ties", "--shove-passes", "60", "--shove-patience", "12",
        "--tighten", "--planes", "In1.Cu", "--cell", "0.025", "--blame",
        "--threads", str(threads), "--timeout", str(args.plough_timeout), "--seed", str(args.plough_seed),
    ]
    if args.rip_region:
        cmd_p3.append("--negotiate")
        for rr in args.rip_region:
            cmd_p3 += ["--rip-region", rr]
    print(f"[{args.variant}] Stage 3 --adopt region-plough ({args.plough_timeout} s) ...", flush=True)
    p3 = subprocess.run(gov + cmd_p3, capture_output=True, text=True)
    (route_dir / "plough.log").write_text(p3.stdout + p3.stderr)
    for ln in (p3.stdout + p3.stderr).splitlines():
        if any(ln.startswith(k) for k in ("negotiated", "rip-up:", "shove pass", "vias:", "pulled tight:", "routed ", "open ", "blame:", "deadline:", "memory:")):
            print(f"  p3: {ln}", flush=True)

    if plough_out.exists():
        v3 = kicad_verdict(plough_out, pro, dru)
        print(
            f"[{args.variant}] Stage 3 verdict: sig_open={v3['sig_open']}, plane_open={v3['plane_open']}, "
            f"hard_err={v3['hard_err']} {v3['hard_err_types']}, vias={v3['vias']}",
            flush=True,
        )
        for o in v3["sig_open_items"][:25]:
            print(f"    open: {o}", flush=True)
        score2 = (v2["real_hard"] > 0, v2["sig_open"] + v2["plane_open"], v2["sig_open"], v2["hard_err"], v2["vias"])
        score3 = (v3["real_hard"] > 0, v3["sig_open"] + v3["plane_open"], v3["sig_open"], v3["hard_err"], v3["vias"])
        if score3 <= score2:
            shutil.copy2(plough_out, pcb)
            pro.write_bytes(pro_bytes)
            refill_board(pcb, pro_bytes)
            print(f"[{args.variant}] Kept Stage 3 plough board: {v3['sig_open']} open, {v3['hard_err']} hard_err, {v3['vias']} vias", flush=True)
            sys.exit(0 if v3["sig_open"] == 0 and v3["plane_open"] == 0 and v3["hard_err"] == 0 else 1)

    sys.exit(1)


if __name__ == "__main__":
    main()
