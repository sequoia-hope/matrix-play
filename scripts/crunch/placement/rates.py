#!/usr/bin/env python3
"""rates.py VARIANT...: open LED ends per LED, by where the LED sits relative to the drivers. Also opens per class."""
import json,re,collections,pcbnew,sys
for v in sys.argv[1:]:
    d=json.load(open(f'hw/round-pendant/{v}/route/autoroute.json'))['runs'][0]
    b=pcbnew.LoadBoard(f'hw/round-pendant/{v}/route/s0.kicad_pcb');mm=pcbnew.ToMM
    f={x.GetReference():x for x in b.GetFootprints()}
    def ov(ref,chip):
        c=f[ref].GetPosition(); u=f[chip].GetPosition()
        return max(abs(mm(c.x-u.x)),abs(mm(c.y-u.y)))
    leds=[r for r in f if r[0]=='D']
    over=[r for r in leds if min(ov(r,'U1'),ov(r,'U2'))<3.9]
    near=[r for r in leds if 3.9<=min(ov(r,'U1'),ov(r,'U2'))<6]
    c=collections.Counter(); k=collections.Counter()
    for s in d['open_items']:
        net=re.search(r'\[([^\]]+)\]',s).group(1)
        k['matrix' if 'matrix' in net else 'other']+=1
        if 'matrix' not in net: continue
        for n,r in re.findall(r'Pad (\S+) \[[^\]]+\] of (\S+) on',s):
            if r[0]=='D': c['over' if r in over else 'near' if r in near else 'far']+=1
            else: c['chip']+=1
    far=len(leds)-len(over)-len(near)
    print(v,'open',d['open'],'plane',d['plane_open'],'err',d['new_errors'],'vias',d['vias'],dict(k),'| per LED over %.2f near %.2f far %.2f | chip-pin ends %d'%(c['over']/max(1,len(over)),c['near']/max(1,len(near)),c['far']/max(1,far),c['chip']))
