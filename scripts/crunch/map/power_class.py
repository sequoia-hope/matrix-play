#!/usr/bin/env python3
"""power_class.py VARIANT: give the nets with a .kicad_dru current-width rule a netclass that already routes at that width: VBAT, VSYS, /Power/BAT_N 0.3 mm; VBUS 0.25 mm.

The router otherwise lays them at POWER's 0.2 mm and DRC flags tens of mm. A class wider than POWER only widens copper; no rule is relaxed. Edits the variant's .kicad_pro only.
"""
import copy, json, sys
p = f"hw/round-pendant/{sys.argv[1]}/round-pendant.kicad_pro"; d = json.load(open(p)); ns = d["net_settings"]
tmpl = next(c for c in ns["classes"] if c["name"] == "POWER"); top = max(c["priority"] for c in ns["classes"] if c["name"] != "Default")
WANT = {"POWER_0.30": (.3, ["VBAT", "VSYS", "/Power/BAT_N"]), "POWER_0.25": (.25, ["VBUS"])}
for i, (name, (w, nets)) in enumerate(WANT.items(), 1):
    c = copy.deepcopy(tmpl); c.update(name=name, track_width=w, priority=top+i); ns["classes"].append(c)
    for q in ns["netclass_patterns"]:
        if q["pattern"] in nets:
            q["netclass"] = name
print([(q["pattern"], q["netclass"]) for q in ns["netclass_patterns"] if q["netclass"].startswith("POWER_")])
json.dump(d, open(p, "w"), indent=2)
