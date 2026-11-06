#!/usr/bin/env python3
"""verify_variant.py -- Polish (clean_copper_8l + post_silk + models) and audit a routed dense-square board."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/dense_square"))
from config import VARIANTS  # noqa: E402


def refill_and_stats(pcb_path: Path, pro_bytes: bytes, solid_refs: list[tuple[str, str]]) -> dict:
    code = """
import json, os, sys, pcbnew
pcb_path = sys.argv[1]
solid_refs = json.loads(sys.argv[2])
b = pcbnew.LoadBoard(pcb_path)
for t in b.GetTracks():
    if t.IsLocked():
        t.SetLocked(False)
for z in b.Zones():
    if not z.GetIsRuleArea() and z.GetZoneName() in ("plane GND", "RP2350 band"):
        z.SetMinThickness(pcbnew.FromMM(0.14))
        if z.GetZoneName() == "plane GND":
            z.SetLocalClearance(pcbnew.FromMM(0.09))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(pcb_path, b)

um = pcbnew.ToMM
tracks = [t for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
vias = [t for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]
locked = sum(1 for t in b.GetTracks() if t.IsLocked())

fps = {f.GetReference(): f for f in b.GetFootprints()}
ep_stats = {}
for sref, pnum in solid_refs:
    ep = next(p for p in fps[sref].Pads() if p.GetNumber() == pnum and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD)
    bb = ep.GetBoundingBox()
    x0, y0, x1, y1 = um(bb.GetLeft()), um(bb.GetTop()), um(bb.GetRight()), um(bb.GetBottom())
    gnd_v = 0
    for_v = 0
    for v in vias:
        vx, vy = um(v.GetPosition().x), um(v.GetPosition().y)
        if x0 - 0.10 <= vx <= x1 + 0.10 and y0 - 0.10 <= vy <= y1 + 0.10:
            if v.GetNetname() == "GND":
                gnd_v += 1
            else:
                for_v += 1
    ep_stats[sref] = {"gnd_vias": gnd_v, "foreign_vias": for_v}

zones = {}
for z in b.Zones():
    if not z.GetIsRuleArea() and z.GetZoneName() in ("plane GND", "RP2350 band", "RP2350 ring"):
        for l in z.GetLayerSet().Seq():
            ps = z.GetFilledPolysList(l)
            zones[z.GetZoneName()] = {"pieces": ps.OutlineCount(), "area_mm2": round(ps.Area() / 1e12, 2)}

vip = 0
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or p.GetNetname() == "GND" or not p.GetNumber():
            continue
        bb = p.GetBoundingBox()
        x0, y0, x1, y1 = um(bb.GetLeft()), um(bb.GetTop()), um(bb.GetRight()), um(bb.GetBottom())
        for v in vias:
            vx, vy = um(v.GetPosition().x), um(v.GetPosition().y)
            if x0 <= vx <= x1 and y0 <= vy <= y1:
                vip += 1

print(json.dumps({
    "tracks": len(tracks),
    "vias": len(vias),
    "locked_copper": locked,
    "non_ep_via_in_pad": vip,
    "solid_eps": ep_stats,
    "zones": zones,
}), flush=True)
os._exit(0)
"""
    r = subprocess.run([sys.executable, "-c", code, str(pcb_path), json.dumps(solid_refs)], capture_output=True, text=True, check=True)
    (pcb_path.parent / "dense-square.kicad_pro").write_bytes(pro_bytes)
    return json.loads(r.stdout.strip().splitlines()[-1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("variant", choices=list(VARIANTS.keys()))
    ap.add_argument("--clean", action="store_true", help="run clean_copper_8l.py before post_silk")
    ap.add_argument("--silk", action="store_true", help="run post_silk + models")
    args = ap.parse_args()

    spec = VARIANTS[args.variant]
    hw = spec.hw_dir
    pcb = hw / "dense-square.kicad_pcb"
    pro = hw / "dense-square.kicad_pro"
    pro_bytes = pro.read_bytes()

    if args.clean:
        raw_bak = hw / "route/routed_raw_8L.kicad_pcb"
        raw_bak.parent.mkdir(parents=True, exist_ok=True)
        if not raw_bak.exists() or "(locked yes)" in pcb.read_text():
            shutil.copy2(pcb, raw_bak)
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/dense_square/clean_copper_8l.py"), str(raw_bak), str(pcb)],
            check=True,
        )
        pro.write_bytes(pro_bytes)

    if args.silk:
        subprocess.run([sys.executable, str(ROOT / "scripts/dense_square/pcb_gen.py"), args.variant, "post_silk"], check=True)
        subprocess.run([sys.executable, str(ROOT / "scripts/dense_square/pcb_gen.py"), args.variant, "models"], check=True)
        pro.write_bytes(pro_bytes)

    solid_refs = [("U3", "61"), ("U5", "17")] + [(drv.uref, "41") for drv in spec.drivers]
    stats = refill_and_stats(pcb, pro_bytes, solid_refs)

    drc_json = Path(f"/tmp/{args.variant}-drc-all.json")
    subprocess.run(
        ["kicad-cli", "pcb", "drc", "--format", "json", "--severity-all", "--output", str(drc_json), str(pcb)],
        check=True,
    )
    drc = json.loads(drc_json.read_text())
    errs = [v for v in drc["violations"] if v["severity"] == "error"]
    warns = [v for v in drc["violations"] if v["severity"] == "warning"]
    unconn = drc["unconnected_items"]

    ca = subprocess.run([sys.executable, str(ROOT / "scripts/bga/copper_audit.py"), str(pcb)], capture_output=True, text=True)
    pj = subprocess.run([sys.executable, str(ROOT / ".claude/skills/pcb-design/scripts/pad_joints.py"), str(hw)], capture_output=True, text=True)
    sc = subprocess.run([sys.executable, str(ROOT / ".claude/skills/pcb-design/scripts/sync_check.py"), str(hw)], capture_output=True, text=True)
    nc = subprocess.run(
        [
            sys.executable,
            str(ROOT / ".claude/skills/pcb-design/scripts/nets_check.py"),
            str(hw),
            "--nets",
            str(ROOT / f"design/nets-dense-square-{args.variant}.csv"),
            "--routed",
        ],
        capture_output=True,
        text=True,
    )

    summary = {
        "variant": args.variant,
        "n_leds": spec.n_leds,
        "n_drivers": len(spec.drivers),
        "pitch_mm": spec.pitch,
        **stats,
        "drc_errors": len(errs),
        "drc_warnings": len(warns),
        "drc_unconnected": len(unconn),
        "drc_error_types": [v["type"] for v in errs[:20]],
        "drc_warning_types": [v["type"] for v in warns[:20]],
        "copper_audit_rc": ca.returncode,
        "copper_audit_tail": ca.stdout.strip().splitlines()[-3:] if ca.stdout.strip() else [],
        "pad_joints_rc": pj.returncode,
        "pad_joints_tail": pj.stdout.strip().splitlines()[-2:] if pj.stdout.strip() else [],
        "sync_check_rc": sc.returncode,
        "nets_routed_rc": nc.returncode,
    }
    out_p = Path(f"/tmp/dense-square-verify-{args.variant}.json")
    out_p.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
