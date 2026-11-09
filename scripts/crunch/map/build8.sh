#!/usr/bin/env bash
# build8.sh VARIANT MAP_CSV: build.sh, then the owner's 8-layer stack with the shared start board's rules (mk8.py, planes In2 and In5 at 0.2 mm clearance).
set -euo pipefail
R="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"; cd $R; D=hw/round-pendant/$1; S=hw/round-pendant/c/route
scripts/crunch/map/build.sh "$1" "$2"
python3 scripts/crunch/layers/mk8.py $D/round-pendant.kicad_pcb --gnd In2.Cu --power In5.Cu --plane-clear 0.2 --rp-clear 0.09 | tail -1
cp $S/preroute_8L.kicad_pro $D/round-pendant.kicad_pro; cp $S/preroute_8L.kicad_dru $D/round-pendant.kicad_dru
cp $D/round-pendant.kicad_pcb $D/route/preroute.kicad_pcb
