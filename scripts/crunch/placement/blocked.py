#!/usr/bin/env python3
"""blocked.py BOARD: which back-side parts stop LED cathode pads taking a via in the pad. A cathode with no via in its pad has to leave on F.Cu."""
import pcbnew,sys,math,collections,json
b=pcbnew.LoadBoard(sys.argv[1]);mm=pcbnew.ToMM
R=.275
back=[]
for f in b.GetFootprints():
    r=f.GetReference()
    if r[0]=='D': continue
    for p in f.Pads():
        q=p.GetBoundingBox()
        ep=p.GetNumber()==('17' if r=='U5' else '61') and r in('U1','U2','U3','U5')
        back.append((r,p.GetNumber(),mm(q.GetLeft())-100,mm(q.GetTop())-100,mm(q.GetRight())-100,mm(q.GetBottom())-100,ep))
c=collections.Counter(); tot=0; ep=collections.Counter(); bl=[]
vias=[(mm(t.GetPosition().x)-100,mm(t.GetPosition().y)-100,t.GetNetCode()) for t in b.GetTracks() if isinstance(t,pcbnew.PCB_VIA)]
for f in b.GetFootprints():
    r=f.GetReference()
    if r[0]!='D': continue
    for p in f.Pads():
        if p.GetNumber()=='3': continue
        tot+=1
        x,y=mm(p.GetPosition().x)-100,mm(p.GetPosition().y)-100
        hit=None
        for a in back:
            if math.hypot(max(a[2]-x,0,x-a[4]),max(a[3]-y,0,y-a[5]))<R:
                if a[6]: ep[a[0]]+=1
                else: hit=a[0]; break
        if hit: c[hit]+=1; bl.append((r,p.GetNumber(),hit))
print('cathode pads',tot,'blocked by a foreign pad',sum(c.values()),dict(c.most_common()),'over an exposed pad',dict(ep))
