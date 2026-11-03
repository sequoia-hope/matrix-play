#!/usr/bin/env python3
"""powerclass.py VARIANT_DIR: give battery and USB power their real width as a net class, so the router targets it instead of 0.2 mm and DRC doesn't find 36 mm of underwidth VBAT.
VBAT, BAT_N at 0.3, VBUS at 0.25, via 0.3/0.15. VSYS is a plane net now, so its tracks are pad stubs into In5: its dru minimum drops from 0.3 to 0.2 (LESSONS.md exempts plane nets' stubs). That is a labelled rule change."""
import json, re, sys
from pathlib import Path
D = Path(sys.argv[1]); pro = D/"round-pendant.kicad_pro"; dru = D/"round-pendant.kicad_dru"
d = json.loads(pro.read_text()); ns = d["net_settings"]; tmpl = next(c for c in ns["classes"] if c["name"] == "POWER")
for name, w in (("BATTERY", .3), ("USB_POWER", .25)):
    ns["classes"].append(dict(tmpl, name=name, track_width=w, via_diameter=.3, via_drill=.15, priority=len(ns["classes"])))
ns["netclass_patterns"] = [p for p in ns["netclass_patterns"] if p["pattern"] not in ("VBAT", "/Power/BAT_N", "VBUS")]
ns["netclass_patterns"] += [{"netclass": "BATTERY", "pattern": "VBAT"}, {"netclass": "BATTERY", "pattern": "/Power/BAT_N"}, {"netclass": "USB_POWER", "pattern": "VBUS"}]
pro.write_text(json.dumps(d, indent=2))
t = dru.read_text(); t2 = re.sub(r"(\(rule \"VSYS current width\"\s*\(condition[^\n]*\n\s*\(constraint track_width \(min )0\.3mm", r"\g<1>0.2mm", t)
assert t != t2; dru.write_text(t2); print("classes added; VSYS min 0.2")
