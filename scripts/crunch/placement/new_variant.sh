#!/usr/bin/env bash
# new_variant.sh NAME [JSON]: fresh variant NAME under hw/round-pendant/, built from nothing with this folder's board.py and the placement overrides in JSON.
set -euo pipefail
cd "$(dirname "$0")/../../.."
V=$1; D=hw/round-pendant/$V; P=scripts/crunch/placement
[ -e "$D/round-pendant.kicad_pcb" ] && { echo "$D already exists; every trial keeps its board" >&2; exit 1; }
mkdir -p "$D"
cp hw/round-pendant/c/*.kicad_sch hw/round-pendant/c/round-pendant.kicad_pro hw/round-pendant/c/round-pendant.kicad_dru hw/round-pendant/c/fp-lib-table hw/round-pendant/c/sym-lib-table "$D/"
cp -r hw/round-pendant/c/lib "$D/lib"
export PENDANT_VARIANT=$V PENDANT_PLACE=place_x PENDANT_MAP=${PENDANT_MAP:-design/study/b/spiral/build/chip_lsa.csv}
[ $# -ge 2 ] && export PENDANT_OVERRIDES=$2
python3 $P/board_outline.py
python3 $P/board.py stack
python3 $P/board.py rules
python3 $P/board.py sync | tail -1
python3 $P/board.py place_x
python3 $P/board.py anodes_b
python3 $P/board.py zones_b
python3 $P/board.py rules
# 8-layer form, then U3's real copper, unless the caller says otherwise.
if [ -z "${KEEP6:-}" ]; then
  python3 scripts/crunch/layers/mk8.py $D/round-pendant.kicad_pcb --plane-clear 0.2 --rp-clear 0.09 | tail -2
  [ -n "${NOU3:-}" ] || python3 $P/u3fix.py $D | grep -E "PGND|CFILT|band vias|NO SITE"
fi
