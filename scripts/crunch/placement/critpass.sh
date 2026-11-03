#!/usr/bin/env bash
# critpass.sh VARIANT T1 T2 "EXTRA": control pass as in twopass.sh, but only the critical nets' copper is kept (locked) for the full route: crystal, USB, QSPI, D235's resistors, the BOOTSEL resistor. Everything else routes freely, matrix included.
set -uo pipefail
cd "$(dirname "$0")/../../.."; V=$1; T1=$2; T2=$3; X=${4:-}; P=scripts/crunch/placement; B=hw/round-pendant/$V; Q=hw/round-pendant/$V-p1
mkdir -p $Q; cp $B/*.kicad_sch $B/round-pendant.kicad_pro $B/round-pendant.kicad_dru $B/fp-lib-table $B/sym-lib-table $Q/; cp -r $B/lib $Q/lib
python3 scripts/two_pass.py strip $B/round-pendant.kicad_pcb $Q/round-pendant.kicad_pcb 2>/dev/null | tail -1
$P/run2.sh $V-p1 $T1 "$X"
python3 scripts/two_pass.py dump $Q/round-pendant.kicad_pcb 2>/dev/null | tail -1 > $Q/p1.json
python3 - $Q/p1.json $Q/crit.json <<'P'
import json,re,sys,collections
d=json.load(open(sys.argv[1]))
pat=re.compile(r"XIN|XOUT|C24-Pad1|USB_D|QSPI|D235|R16-Pad2")
k=[e for e in d if pat.search(e["net"])]
json.dump(k,open(sys.argv[2],"w")); print("kept",len(k),"of",len(d),collections.Counter(e["net"].split("/")[-1] for e in k).most_common())
P
python3 scripts/two_pass.py merge $B/round-pendant.kicad_pcb $Q/crit.json 2>/dev/null | tail -1
$P/run2.sh $V $T2 "$X"
