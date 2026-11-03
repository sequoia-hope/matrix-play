#!/usr/bin/env bash
# Variant b, from the built board: control and power first, then the matrix. Args: seconds for pass 1, seconds for pass 2.
set -uo pipefail
cd "$(dirname "$0")/.."
B=hw/round-pendant/b; P=$B/route/p1; AR=.claude/skills/pcb-design/scripts/autoroute.py
[ -e $P ] && mv $P $P.old.$(date +%s); mkdir -p $P; cp $B/*.kicad_sch $B/round-pendant.kicad_pro $B/round-pendant.kicad_dru $B/fp-lib-table $B/sym-lib-table $P/; cp -r $B/lib $P/lib
python3 scripts/two_pass.py strip $B/route/preroute.kicad_pcb $P/round-pendant.kicad_pcb 2>/dev/null | tail -1
python3 $AR $P --planes In2.Cu,In4.Cu --seeds 1 --timeout "$1" --threads 4 --memory 12G 2>&1 | grep -E 'kept seed|^exit' | cut -c1-200
grep -E '^(prefanout|negotiated|rip-up|deadline|routed)' $P/route/s0.log | cut -c1-140
[ "$2" = 0 ] && exit 0
[ -f $P/route/s0.log ] || { echo 'pass 1 did not run'; exit 1; }
python3 scripts/two_pass.py dump $P/round-pendant.kicad_pcb 2>/dev/null | tail -1 > $B/route/p1.json
cp $B/route/preroute.kicad_pcb $B/round-pendant.kicad_pcb
python3 scripts/two_pass.py merge $B/round-pendant.kicad_pcb $B/route/p1.json 2>/dev/null | tail -1
PENDANT_VARIANT=b python3 scripts/board.py rules
python3 $AR $B --planes In2.Cu,In4.Cu --seeds 1 --timeout "$2" --threads 4 --memory 12G 2>&1 | grep -E 'kept seed|^exit' | cut -c1-200
grep -E '^(negotiated|rip-up|deadline|routed|refinished)' $B/route/s0.log | cut -c1-140
