#!/usr/bin/env bash
# buildy.sh VARIANT MAP_CSV: as placement's new_variant.sh with exp/y2.json overrides (drivers 2.4 mm north, cathode vias over EPs), with board_y.py's anode-behind turns. 8 layers, U3 copper from u3fix.py.
set -euo pipefail; cd /home/sequoia/pcb/round-pendant
V=$1; D=hw/round-pendant/$V; P=scripts/crunch/placement; B=scripts/crunch/orth/board_y.py
[ -e "$D" ] && { echo "$D exists" >&2; exit 1; }
mkdir -p $D/route; cp hw/round-pendant/c/*.kicad_sch hw/round-pendant/c/round-pendant.kicad_pro hw/round-pendant/c/round-pendant.kicad_dru hw/round-pendant/c/fp-lib-table hw/round-pendant/c/sym-lib-table $D/; cp -r hw/round-pendant/c/lib $D/lib; cp $2 $D/map.csv
export PENDANT_VARIANT=$V PENDANT_PLACE=place_x PENDANT_MAP=$2 ORTH_MAP=$2 PENDANT_OVERRIDES=$P/exp/y2.json
python3 $P/board_outline.py; python3 $B stack; python3 $B rules; python3 $B sync | tail -1
python3 $B place_x | tail -1; python3 $B anodes_b | grep -E 'anode vias|cathode|bend too|ep_|EP'; python3 $B zones_b | tail -1; python3 $B rules | tail -1
python3 scripts/crunch/layers/mk8.py $D/round-pendant.kicad_pcb --plane-clear 0.2 --rp-clear 0.09 | tail -1
python3 $P/u3fix.py $D | grep -E "PGND|CFILT|band vias|NO SITE"
cp $D/round-pendant.kicad_pcb $D/route/preroute.kicad_pcb
