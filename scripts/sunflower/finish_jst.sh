#!/usr/bin/env bash
# finish_jst.sh <variant> -- after the JST re-route: clean copper on a copy, keep it only if it stays at 0 open,
# then silk (front seed web, back labels), 3D models and the full audit (verify_variant.py).
set -euo pipefail
v=$1; root="$(cd "$(dirname "$0")/../.." && pwd)"; cd "$root"
H=hw/sunflower/$v
cp $H/sunflower.kicad_pcb $H/route/jst_routed_raw.kicad_pcb
cp $H/sunflower.kicad_pro $H/route/jst_pro.bak
out=$(python3 scripts/sunflower/clean_copper_4l.py $H/route/jst_routed_raw.kicad_pcb $H/route/jst_cleaned.kicad_pcb 2>&1 | grep -v "Debug\|swig" | tail -1 || true)
cp $H/route/jst_pro.bak $H/sunflower.kicad_pro
echo "clean: $out"
if [[ "$out" == *"open=0"* ]]; then cp $H/route/jst_cleaned.kicad_pcb $H/sunflower.kicad_pcb; echo "using cleaned copper"; else echo "keeping raw router copper"; fi
python3 scripts/sunflower/pcb_gen.py $v post_silk 2>&1 | grep -v "Debug\|swig" | tail -3
python3 scripts/sunflower/pcb_gen.py $v models 2>&1 | grep -v "Debug\|swig" | tail -1
python3 scripts/sunflower/verify_variant.py $v 2>&1 | grep -v "Debug\|swig" | grep -E '"vias"|drc_(errors|warnings|unconnected)|error_types|copper_audit_rc|tracks=|pad_joints_rc|sync_check_rc|nets_routed_rc|pieces'
