#!/usr/bin/env bash
# twopass.sh VARIANT T1 T2 "EXTRA": control and power nets first with matrix pads off net, then the matrix round them. VARIANT must be freshly built and unrouted; pass 1 goes to VARIANT-p1.
set -uo pipefail
cd "$(dirname "$0")/../../.."; V=$1; T1=$2; T2=$3; X=${4:-}; P=scripts/crunch/placement; B=hw/round-pendant/$V; Q=hw/round-pendant/$V-p1
mkdir -p $Q; cp $B/*.kicad_sch $B/round-pendant.kicad_pro $B/round-pendant.kicad_dru $B/fp-lib-table $B/sym-lib-table $Q/; cp -r $B/lib $Q/lib
python3 scripts/two_pass.py strip $B/round-pendant.kicad_pcb $Q/round-pendant.kicad_pcb 2>/dev/null | tail -1
$P/run2.sh $V-p1 $T1 "$X"
python3 scripts/two_pass.py dump $Q/round-pendant.kicad_pcb 2>/dev/null | tail -1 > $Q/p1.json
python3 scripts/two_pass.py merge $B/round-pendant.kicad_pcb $Q/p1.json 2>/dev/null | tail -1
$P/run2.sh $V $T2 "$X"
