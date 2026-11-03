#!/usr/bin/env python3
"""spiral_sites.py -- the 234 matrix LED sites as dicts of x, y, a (radians), with each a's value as spiral_map.sites() gives it."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from sunflower import lattice, nudge


def sites():
    pts = lattice(); nudge(pts)
    return [dict(i=i, x=p[0], y=p[1], a=p[2]) for i, p in enumerate(pts)]
