#!/usr/bin/env bash
# route_y.sh VARIANT TIMEOUT [SEED0_COUNT]: y5's route settings (2 threads, cell 0.025, 8 layers), booked, result copied to route/T<timeout>/.
set -uo pipefail
cd /home/sequoia/pcb/round-pendant; V=$1; T=$2; S=${3:-1}; D=hw/round-pendant/$V
~/.claude/bin/reserve -c 2 --here -l "round-pendant crunch: map $V ${T}s" -- python3 .claude/skills/pcb-design/scripts/autoroute.py $D --planes In2.Cu,In5.Cu --seeds $S --timeout $T --threads 2 --memory 12G --extra "--prefanout-mode inner --cell 0.025" 2>&1 | grep -E 'seed [0-9]+:|kept seed|exit|reserve: (no|fail|cancel)' | cut -c1-200
rc=${PIPESTATUS[0]}
mkdir -p $D/route/T$T; cp -f $D/route/autoroute.json $D/route/s*.log $D/route/s*.kicad_pcb $D/route/T$T/ 2>/dev/null
echo "$V T=$T rc=$rc"
