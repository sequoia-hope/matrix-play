#!/usr/bin/env bash
# run2.sh VARIANT TIMEOUT "EXTRA": 2 cores, 2 threads (the router gives the same order for any count from 2 up), planes In2 and In5.
cd "$(dirname "$0")/../../.."; V=$1; T=${2:-1200}; X=${3:-}
~/.claude/bin/reserve -c 2 --here -l "round-pendant crunch: placement $V ${T}s $X" -- python3 .claude/skills/pcb-design/scripts/autoroute.py hw/round-pendant/$V --planes In2.Cu,In5.Cu --seeds 1 --timeout $T --threads 2 --memory 12G --extra "--prefanout-mode inner $X" > /tmp/claude-1000/-home-sequoia-pcb-round-pendant/b747bb30-353b-4635-8cb8-3b492fc301c0/scratchpad/$V.out 2>&1
rc=$?; echo "exit $rc"; [ $rc = 75 ] && { echo "NOT RUN (75)"; exit 75; }
python3 scripts/crunch/placement/rates.py $V 2>&1 | grep -v -E "Debug|assert|swig"
grep -E "^prefanout:|^negotiated|^rip-up|^routed|^deadline" hw/round-pendant/$V/route/s0.log | cut -c1-150
