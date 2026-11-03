#!/usr/bin/env bash
# Rebuild the board from nothing, in order, one process per stage.
set -euo pipefail
cd "$(dirname "$0")/.."
rm -f hw/round-pendant/a/round-pendant.kicad_pcb
python3 scripts/board_outline.py
python3 scripts/board.py stack
python3 scripts/board.py sync | tail -1
python3 scripts/board.py place
python3 scripts/board.py anodes
python3 scripts/board.py rules
