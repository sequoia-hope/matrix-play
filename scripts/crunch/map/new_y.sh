#!/usr/bin/env bash
# new_y.sh VARIANT JSON MAP_CSV: placement's new_variant.sh recipe (overrides, 8 layers, U3 fix) using this folder's board_y.py, which honours a map's turn column.
# Env as board_y.py reads: PREF_STUB, ANODE_FIRST, PROBE_OUT. Refuses an existing variant; with PROBE_OUT set, stops after the probe.
set -euo pipefail
cd "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
V=$1; D=hw/round-pendant/$V; P=scripts/crunch/placement; B=scripts/crunch/map/board_y.py
[ -e "$D/round-pendant.kicad_pcb" ] && { echo "$D exists" >&2; exit 2; }
mkdir -p $D/route; cp hw/round-pendant/c/*.kicad_sch hw/round-pendant/c/round-pendant.kicad_pro hw/round-pendant/c/round-pendant.kicad_dru hw/round-pendant/c/fp-lib-table hw/round-pendant/c/sym-lib-table $D/; cp -r hw/round-pendant/c/lib $D/lib
export PENDANT_VARIANT=$V PENDANT_PLACE=place_x PENDANT_MAP=$3 PENDANT_OVERRIDES=$2
cp $3 $D/map.csv
python3 $P/board_outline.py
python3 $B stack; python3 $B rules; python3 $B sync | tail -1
python3 $B place_x | tail -1
python3 $B anodes_b | grep -E 'anode vias|probe|cathode|tiles'
[ -n "${PROBE_OUT:-}" ] && exit 0
python3 $B zones_b | tail -1
python3 $B rules
python3 scripts/crunch/layers/mk8.py $D/round-pendant.kicad_pcb --plane-clear 0.2 --rp-clear 0.09 | tail -1
python3 $P/u3fix.py $D | grep -E "PGND|CFILT|band vias|NO SITE"
cp $D/round-pendant.kicad_pcb $D/route/preroute.kicad_pcb
