#!/usr/bin/env bash
# run_seed.sh SRC SEED [TIMEOUT]: same input board as SRC, another router seed, into SRC-sSEED. Measures noise.
cd "$(dirname "$0")/../../.."; S=$1; K=$2; T=${3:-600}; V=$S-s$K; D=hw/round-pendant/$V; mkdir -p $D
cp hw/round-pendant/c/*.kicad_sch hw/round-pendant/c/fp-lib-table hw/round-pendant/c/sym-lib-table $D/; cp -r hw/round-pendant/c/lib $D/lib; cp hw/round-pendant/$S/round-pendant.kicad_pro hw/round-pendant/$S/round-pendant.kicad_dru $D/
cp hw/round-pendant/$S/route/preroute.kicad_pcb $D/round-pendant.kicad_pcb 2>/dev/null || cp hw/round-pendant/$S/round-pendant.kicad_pcb $D/round-pendant.kicad_pcb
~/.claude/bin/reserve -c 4 --here -l "round-pendant crunch: placement $V ${T}s" -- python3 .claude/skills/pcb-design/scripts/autoroute.py $D --planes In2.Cu,In4.Cu --seeds 1 --timeout $T --threads 4 --memory 12G --extra "--prefanout-mode inner --seed $K" > /tmp/claude-1000/-home-sequoia-pcb-round-pendant/b747bb30-353b-4635-8cb8-3b492fc301c0/scratchpad/$V.out 2>&1; echo "exit $?"
python3 scripts/crunch/placement/rates.py $V 2>&1 | grep -v -E "Debug|assert|swig"
