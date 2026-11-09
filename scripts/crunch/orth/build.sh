#!/usr/bin/env bash
# build.sh VARIANT MAP_CSV: new c-orth variant, unrouted: same stages as scripts/build_board_b.sh with place_c, using board_orth.py (anode-behind turns when ORTH_MAP is set). Refuses an existing variant.
set -euo pipefail
R="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"; cd $R
export PENDANT_VARIANT=$1 PENDANT_MAP=$2 PENDANT_PLACE=place_c
[ "${ORTH_ANY:-}" ] || export ORTH_MAP=$2
D=hw/round-pendant/$1; S=hw/round-pendant/c; B=scripts/crunch/orth/board_orth.py
[ -e "$D" ] && { echo "build.sh: $D exists" >&2; exit 2; }
mkdir -p $D/route; cp $S/*.kicad_sch $S/round-pendant.kicad_pro $S/round-pendant.kicad_dru $S/fp-lib-table $S/sym-lib-table $D/; cp -r $S/lib $D/lib; cp $2 $D/map.csv
python3 scripts/board_outline.py
python3 $B stack; python3 $B rules; python3 $B sync | tail -1
python3 $B place_c | tail -1
python3 $B anodes_b | grep -E 'anode vias|cathode|bend too'
python3 $B zones_b | tail -1
python3 $B rules
cp $D/round-pendant.kicad_pcb $D/route/preroute.kicad_pcb
