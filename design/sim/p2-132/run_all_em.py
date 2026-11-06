#!/usr/bin/env python3
"""run_all_em.py -- Master reproducible runner for p2-132 Electromagnetic / SI / PDN Simulation Suite (P0-P4)."""
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent

SCRIPTS = [
    "extract_board.py",
    "p0_kat.py",
    "p1_qspi_usb_fdtd.py",
    "p2_vreg_lx_em.py",
    "p3_i2c_matrix_emi.py",
    "p4_vsys_pdn.py",
]


def main():
    t0 = time.time()
    for scr in SCRIPTS:
        ts = time.time()
        print(f"\n==================== {scr} ====================", flush=True)
        rc = subprocess.call([sys.executable, "-u", str(HERE / scr)])
        if rc != 0:
            sys.exit(rc)
        print(f"--- {scr} completed in {time.time() - ts:.1f}s ---", flush=True)
    print(f"\nAll P1-P4 EM simulations completed in {time.time() - t0:.1f}s.", flush=True)


if __name__ == "__main__":
    main()
