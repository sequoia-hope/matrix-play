#!/usr/bin/env python3
"""drcq.py BOARD: kicad-cli DRC counts and samples, using the board's own project rules."""
import json,collections,subprocess,sys,tempfile,os
o=tempfile.mktemp(suffix='.json')
subprocess.run(["kicad-cli","pcb","drc","--format","json","--severity-error","-o",o,sys.argv[1]],capture_output=True)
d=json.load(open(o)); os.unlink(o)
print(collections.Counter(v['type'] for v in d['violations']),"unconnected",len(d['unconnected_items']))
for v in d['violations'][:int(sys.argv[2]) if len(sys.argv)>2 else 15]: print(v['type'],v['description'][:80],[i['description'][:50] for i in v['items']])
