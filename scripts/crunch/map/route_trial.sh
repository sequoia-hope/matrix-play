#!/usr/bin/env bash
# route_trial.sh VARIANT TIMEOUT [SEEDS]: book 4 cores, route a c-map variant as README says, and keep the result under route/T<timeout>/.
set -uo pipefail
R=/home/sequoia/pcb/round-pendant; cd $R
V=$1; T=$2; S=${3:-1}; D=hw/round-pendant/$V
~/.claude/bin/reserve -c 4 --here -l "round-pendant crunch: map $V ${T}s" -- python3 .claude/skills/pcb-design/scripts/autoroute.py $D --planes ${PLANES:-In2.Cu,In5.Cu} --seeds $S --timeout $T --threads 4 --memory 12G --extra "--prefanout-mode inner" 2>&1 | grep -E 'seed [0-9]+:|kept seed|exit|reserve' | cut -c1-200
rc=${PIPESTATUS[0]}
mkdir -p $D/route/T$T; cp -f $D/route/autoroute.json $D/route/s*.log $D/route/s*.kicad_pcb $D/route/T$T/ 2>/dev/null
echo "$V T=$T rc=$rc"
