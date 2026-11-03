#!/usr/bin/env bash
# finish3.sh VARIANT: DRC to list dangling stubs and vias, then remove them, one fixed-point loop.
cd "$(dirname "$0")/../../.."; P=scripts/crunch/placement; V=$1
python3 $P/undangle.py $V 2>&1 | grep -v -E "Debug|swig|assert" | tail -2 | cut -c1-240
