#!/usr/bin/env python3
"""errs.py DRC.json LABEL: errors by type, width errors by net, and the first few of anything serious."""
import json,sys,collections,re
d=json.load(open(sys.argv[1])); c=collections.Counter(v['type'] for v in d['violations'])
print(sys.argv[2],dict(c),'unconnected',len(d['unconnected_items']))
tw=[v for v in d['violations'] if v['type']=='track_width']
print(' width by net',collections.Counter(re.search(r'\[([^\]]+)\]',v['items'][0]['description']).group(1).split('/')[-1] for v in tw).most_common(8))
for v in tw[:2]: print('  ',v['description'][:110])
for t in ('clearance','hole_clearance','length_out_of_range','items_not_allowed','via_count','shorting_items','annular_width'):
    for v in [v for v in d['violations'] if v['type']==t][:5]: print(' ',t,v['description'][:60],[i['description'][:55] for i in v['items']])
