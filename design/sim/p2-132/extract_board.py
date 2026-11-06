#!/usr/bin/env python3
"""extract_board.py -- Read-only copper & stackup extraction from hw/parallelogram/p2-132/parallelogram.kicad_pcb."""
import json
import math
from collections import defaultdict
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[3]
PCB_PATH = ROOT / "hw/parallelogram/p2-132/parallelogram.kicad_pcb"
OUT_JSON = Path(__file__).resolve().parent / "work/p2-132-geom.json"

# Exact stackup from parallelogram.kicad_pcb (JLC04161H-7628, mm, z=0 at top of F.Cu):
# F.Cu:   z = [ -0.0350,  0.0000 ] (35 um)
# prepreg:      0.2104 mm, er = 4.4
# In1.Cu: z = [ -0.2606, -0.2454 ] (15.2 um) -- unbroken GND plane
# core:         1.0650 mm, er = 4.6
# In2.Cu: z = [ -1.3408, -1.3256 ] (15.2 um) -- inner signal
# prepreg:      0.2104 mm, er = 4.4
# B.Cu:   z = [ -1.5862, -1.5512 ] (35 um)
STACKUP = {
    "total_thickness_mm": 1.5862,
    "layers": {
        "F.Cu":   {"z_top":  0.0000, "z_bot": -0.0350, "z_mid": -0.0175, "t_mm": 0.0350},
        "In1.Cu": {"z_top": -0.2454, "z_bot": -0.2606, "z_mid": -0.2530, "t_mm": 0.0152},
        "In2.Cu": {"z_top": -1.3256, "z_bot": -1.3408, "z_mid": -1.3332, "t_mm": 0.0152},
        "B.Cu":   {"z_top": -1.5512, "z_bot": -1.5862, "z_mid": -1.5687, "t_mm": 0.0350},
    },
    "dielectrics": [
        {"name": "prepreg_top", "z_top": -0.0350, "z_bot": -0.2454, "t_mm": 0.2104, "er": 4.4, "tand": 0.02},
        {"name": "core",        "z_top": -0.2606, "z_bot": -1.3256, "t_mm": 1.0650, "er": 4.6, "tand": 0.02},
        {"name": "prepreg_bot", "z_top": -1.3408, "z_bot": -1.5512, "t_mm": 0.2104, "er": 4.4, "tand": 0.02},
    ],
    "solder_mask": {"t_mm": 0.015, "er": 3.5},
}

OX, OY = 100.0, 100.0
CU_LAYERS = ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu")


def mm(v: int) -> float:
    return round(pcbnew.ToMM(v), 5)


def rel_xy(pt) -> tuple[float, float]:
    return (round(pcbnew.ToMM(pt.x) - OX, 4), round(pcbnew.ToMM(pt.y) - OY, 4))


def main():
    b = pcbnew.LoadBoard(str(PCB_PATH))
    layer_id = {name: b.GetLayerID(name) for name in CU_LAYERS}
    id_to_layer = {v: k for k, v in layer_id.items()}

    footprints = {}
    pads_by_net = defaultdict(list)
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        fx, fy = rel_xy(fp.GetPosition())
        side = "B.Cu" if fp.IsFlipped() else "F.Cu"
        fp_pads = []
        for pad in fp.Pads():
            px, py = rel_xy(pad.GetPosition())
            sx, sy = mm(pad.GetSize().x), mm(pad.GetSize().y)
            net = pad.GetNetname()
            pad_layers = [nm for nm, lid in layer_id.items() if pad.IsOnLayer(lid)]
            rec = {
                "ref": ref,
                "pad": pad.GetNumber(),
                "net": net,
                "x": px,
                "y": py,
                "sx": sx,
                "sy": sy,
                "rot_deg": round(pad.GetOrientation().AsDegrees(), 2),
                "layers": pad_layers,
            }
            fp_pads.append(rec)
            pads_by_net[net].append(rec)
        footprints[ref] = {
            "ref": ref,
            "val": fp.GetValue(),
            "side": side,
            "x": fx,
            "y": fy,
            "rot_deg": round(fp.GetOrientation().AsDegrees(), 2),
            "pads": fp_pads,
        }

    tracks_by_net = defaultdict(list)
    vias_by_net = defaultdict(list)
    for tr in b.GetTracks():
        net = tr.GetNetname()
        if tr.GetClass() == "PCB_VIA":
            v = pcbnew.Cast_to_PCB_VIA(tr)
            vx, vy = rel_xy(v.GetPosition())
            vias_by_net[net].append({
                "x": vx,
                "y": vy,
                "size": mm(v.GetWidth(layer_id["F.Cu"])),
                "drill": mm(v.GetDrillValue()),
                "net": net,
            })
        else:
            lid = tr.GetLayer()
            if lid not in id_to_layer:
                continue
            x1, y1 = rel_xy(tr.GetStart())
            x2, y2 = rel_xy(tr.GetEnd())
            length = round(math.hypot(x2 - x1, y2 - y1), 5)
            if length < 1e-5:
                continue
            tracks_by_net[net].append({
                "layer": id_to_layer[lid],
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "w": mm(tr.GetWidth()),
                "len": length,
                "net": net,
            })

    zones = []
    for z in b.Zones():
        if z.GetIsRuleArea():
            # Record rule areas too (especially L1 cutout on In1.Cu!)
            outline = z.Outline()
            pts = []
            if outline.OutlineCount() > 0:
                ol = outline.Outline(0)
                pts = [rel_xy(ol.CPoint(i)) for i in range(ol.PointCount())]
            zones.append({
                "kind": "rule_area",
                "name": z.GetZoneName(),
                "layers": [b.GetLayerName(lid) for lid in z.GetLayerSet().Seq()],
                "outline": pts,
            })
            continue
        net = z.GetNetname()
        for nm, lid in layer_id.items():
            if not z.IsOnLayer(lid):
                continue
            poly = z.GetFilledPolysList(lid)
            polys_out = []
            for oi in range(poly.OutlineCount()):
                ol = poly.Outline(oi)
                ext = [rel_xy(ol.CPoint(k)) for k in range(ol.PointCount())]
                holes = []
                for hi in range(poly.HoleCount(oi)):
                    hl = poly.Hole(oi, hi)
                    holes.append([rel_xy(hl.CPoint(k)) for k in range(hl.PointCount())])
                polys_out.append({"exterior": ext, "holes": holes})
            if polys_out:
                zones.append({
                    "kind": "copper_zone",
                    "net": net,
                    "layer": nm,
                    "polygons": polys_out,
                })

    # Compute per-net summary
    net_summary = {}
    all_nets = sorted(set(tracks_by_net) | set(vias_by_net) | set(pads_by_net))
    for net in all_nets:
        if not net:
            continue
        trs = tracks_by_net.get(net, [])
        vs = vias_by_net.get(net, [])
        by_layer = defaultdict(float)
        widths = sorted({t["w"] for t in trs})
        for t in trs:
            by_layer[t["layer"]] += t["len"]
        net_summary[net] = {
            "total_len_mm": round(sum(t["len"] for t in trs), 3),
            "by_layer_mm": {k: round(v, 3) for k, v in by_layer.items()},
            "widths_mm": widths,
            "n_segments": len(trs),
            "n_vias": len(vs),
            "n_pads": len(pads_by_net.get(net, [])),
        }

    out = {
        "board": "parallelogram/p2-132",
        "pcb_path": str(PCB_PATH.relative_to(ROOT)),
        "stackup": STACKUP,
        "footprints": footprints,
        "tracks_by_net": dict(tracks_by_net),
        "vias_by_net": dict(vias_by_net),
        "zones": zones,
        "net_summary": net_summary,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2))
    print(f"Wrote {OUT_JSON} ({OUT_JSON.stat().st_size / 1024:.1f} KB)")
    for k in [
        "/MCU/QSPI_SCLK", "/MCU/QSPI_SD0", "/MCU/QSPI_SD1", "/MCU/QSPI_SD2", "/MCU/QSPI_SD3", "/MCU/QSPI_SS",
        "/Power/USB_DP_C", "/Power/USB_DM_C", "USB_DP", "USB_DM", "/MCU/USB_DP_MCU", "/MCU/USB_DM_MCU",
        "/MCU/VREG_LX", "+1V1", "+3V3", "VSYS", "VBAT", "VBUS",
        "I2C_SDA", "I2C_SCL", "/MCU/ACC_SDA", "/MCU/ACC_SCL", "/MCU/LIGHT",
        "/Driver 1 and matrix/SW1_1", "/Driver 1 and matrix/SW1_11", "/Driver 1 and matrix/CS1_1",
        "/Driver 2 and matrix/SW2_1", "/Driver 2 and matrix/CS2_1",
    ]:
        if k in net_summary:
            s = net_summary[k]
            print(f"  {k:32s} len={s['total_len_mm']:6.2f} mm  vias={s['n_vias']:2d}  w={s['widths_mm']}  layers={s['by_layer_mm']}")


if __name__ == "__main__":
    main()
