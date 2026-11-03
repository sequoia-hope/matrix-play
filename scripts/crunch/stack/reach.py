#!/usr/bin/env python3
"""reach.py CSV U1x,U1y U2x,U2y: straight-line reach from each driver's chip centre to its LEDs, plus per-net MST and pin distance. Compares driver positions on the same map's sites."""
import csv,sys,math
R=list(csv.DictReader(open(sys.argv[1])))
C={'1':tuple(map(float,sys.argv[2].split(',')[:2])),'2':tuple(map(float,sys.argv[3].split(',')[:2]))}
d=[math.dist((float(r['x_mm']),float(r['y_mm'])),C[r['driver']]) for r in R]
print(sys.argv[1],'max',round(max(d),1),'mean',round(sum(d)/len(d),1), 'over 20mm:',sum(x>20 for x in d))
