#!/usr/bin/env bash
# check.sh VARIANT: placement_check plus KiCad DRC on the unrouted board, counted by type. A move only counts if placement passes and no courtyard, clearance or short error is new.
cd "$(dirname "$0")/../../.."; D=hw/round-pendant/$1
python3 .claude/skills/pcb-design/scripts/placement_check.py $D 2>&1 | grep -E "ERROR|error|PASS|FAIL|ratsnest" | cut -c1-160
T=$(mktemp -d); kicad-cli pcb drc --format json --severity-error --severity-warning -o $T/d.json $D/round-pendant.kicad_pcb >/dev/null 2>&1
python3 - $T/d.json <<'P'
import json,sys,collections
d=json.load(open(sys.argv[1])); c=collections.Counter(v["type"] for v in d["violations"]); print("drc", dict(c), "unconnected", len(d.get("unconnected_items",[])))
for v in d["violations"]:
    if v["type"] in ("courtyards_overlap","clearance","shorting_items","npth_inside_courtyard","pth_inside_courtyard","hole_clearance","copper_edge_clearance"):
        print(" ",v["type"],[i["description"][:60] for i in v["items"]])
P
rm -rf $T
