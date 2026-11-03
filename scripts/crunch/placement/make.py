#!/usr/bin/env python3
"""make.py NAME: writes exp/NAME.json from a small recipe, for driver moves. U1/U2 move with all their parts; everything else that's listed legalizes."""
import json, sys
U1 = ["U1", "C30", "C31", "C32", "C33", "C34", "C35", "C36", "C37", "R30", "R31", "R32"]
U2 = ["U2", "C40", "C41", "C42", "C43", "C44", "C45", "C46", "C47", "R33", "R34", "R35"]
def drivers(p1, p2, t1=0, t2=0):
    c = []
    c.append(dict(refs=U1, centre=[-11.4, 3.4], angle=t1, shift=[p1[0]+11.4, p1[1]-3.4]))
    c.append(dict(refs=U2, centre=[10.6, 3.4], angle=t2, shift=[p2[0]-10.6, p2[1]-3.4]))
    return c
if __name__ == "__main__":
    pass
