#!/usr/bin/env bash
# mkfrom.sh NAME SRC_DIR BOARD: variant c-router-a-NAME with SRC_DIR's rules, schematic and libs, and BOARD as its board
set -euo pipefail
cd "$(dirname "$0")/../../.."
D=hw/round-pendant/c-router-a-$1; S=$2
[ -e "$D" ] && { echo "exists: $D" >&2; exit 1; }
mkdir -p $D; cp $S/*.kicad_sch $S/round-pendant.kicad_pro $S/round-pendant.kicad_dru $S/fp-lib-table $S/sym-lib-table $D/
cp -r $S/lib $D/lib; cp "$3" $D/round-pendant.kicad_pcb; echo $D
