#!/usr/bin/env bash
# newvar.sh NAME: make hw/round-pendant/c-layers-NAME from variant c's preroute board, per design/study/crunch/README.md.
set -euo pipefail
cd "$(dirname "$0")/../../.."
V=c-layers-$1; D=hw/round-pendant/$V
[[ -e $D ]] && { echo "$D exists; never overwrite a trial" >&2; exit 1; }
mkdir -p $D
S=hw/round-pendant/c
cp $S/*.kicad_sch $S/fp-lib-table $S/sym-lib-table $D/
cp -r $S/lib $D/lib
cp $S/route/preroute_v3.kicad_pcb $D/round-pendant.kicad_pcb
cp $S/route/preroute_v3.kicad_pro $D/round-pendant.kicad_pro
cp $S/route/preroute_v3.kicad_dru $D/round-pendant.kicad_dru
echo $D
