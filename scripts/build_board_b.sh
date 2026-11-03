#!/usr/bin/env bash
# Rebuild variant b from nothing, one process per stage: sunflower LEDs, USB wire pads, EVQP7C01P buttons. Not routed.
set -euo pipefail
cd "$(dirname "$0")/.."
export PENDANT_VARIANT=${PENDANT_VARIANT:-b}
B=hw/round-pendant/$PENDANT_VARIANT/round-pendant.kicad_pcb; [ -e $B ] && mv $B $B.old.$(date +%s) || true
python3 scripts/board_outline.py
python3 scripts/board.py stack
python3 scripts/board.py rules
python3 scripts/board.py sync | tail -1
python3 scripts/board.py ${PENDANT_PLACE:-place_b}
python3 scripts/board.py anodes_b
python3 scripts/board.py zones_b
python3 scripts/board.py rules
