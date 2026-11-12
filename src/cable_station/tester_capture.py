"""Decode a USB-C cable's e-marker from a `km003c pd capture --raw` log.

Looks for the cable's Discover Identity ACK on SOP' (the cable channel) and returns the fields that
matter for a label: current rating, EPR, highest USB speed, passive or active, and the vendor ID.
Decoding follows the USB PD specification's ID Header and Cable VDO layouts (revision 3.x).

The POWER-Z KM003C sends the Discover Identity itself when its "USB-C eMarker" module runs; the capture
carries both the request and the cable's answer. The `km003c` CLI is okhsunrog's km003c-rs.
"""
from __future__ import annotations

import re

# Cable VDO speed codes (USB PD 3.x). Code 2 covers USB 3.2 Gen 2 (10G) and USB4 Gen 2 (20G), so the label
# names both tiers, highest first. Code 3 prints as ">=40G": verified to 40G, possibly higher.
SPEED = {0: "USB 2.0 480M", 1: "USB 3.2 5G", 2: "USB4 20G · USB 3.2 10G", 3: "USB4 ≥40G · USB 3.2 10G", 4: "USB4 80G · USB 3.2 10G"}
CURRENT = {0: None, 1: "3A", 2: "5A", 3: "reserved"}
PRODUCT = {3: "passive cable", 4: "active cable", 6: "VCONN-powered device"}
VOLT = {0: "20V", 1: "30V", 2: "40V", 3: "50V"}


def frames(text: str):
    """Yield (byte_count, [hex bytes]) for every RAW line, joined across continuation lines."""
    buf = None
    for line in text.splitlines():
        m = re.search(r"RAW\[(\d+)\]:\s*([0-9A-Fa-f ]+)$", line)
        if m:
            if buf:
                yield buf
            buf = [int(m.group(1)), m.group(2).split()]
            continue
        if buf and re.match(r"^\s+([0-9A-Fa-f]{2}\s*)+$", line):
            buf[1] += line.split()
            continue
        if buf and "SOP1" in line and buf[0] == len(buf[1]):
            yield buf
            buf = None
    if buf:
        yield buf


def words(bs: list[str]):
    b = bytes(int(x, 16) for x in bs)
    hdr = int.from_bytes(b[0:2], "little")
    objs = [int.from_bytes(b[i:i + 4], "little") for i in range(2, len(b) - 3, 4)]
    return hdr, objs


def decode(text: str) -> list[dict]:
    """Every Discover Identity ACK in the capture, as a dict per answer (the last one is the freshest)."""
    out = []
    for _n, bs in frames(text):
        hdr, objs = words(bs)
        if (hdr & 0x1F) != 15 or len(objs) < 4:   # Vendor_Defined with ID header + cert + product + VDO
            continue
        vdm = objs[0]
        if (vdm >> 16) != 0xFF00 or (vdm & 0x1F) != 1 or ((vdm >> 6) & 3) != 1:
            continue  # not a Discover Identity ACK with the PD standard SVID
        idh, cert, prod = objs[1], objs[2], objs[3]
        vdo = objs[4] if len(objs) > 4 else None
        ptype = (idh >> 27) & 7
        r = {"product_type": PRODUCT.get(ptype, f"type {ptype}"), "vendor_id": f"0x{idh & 0xFFFF:04X}",
             "xid": f"0x{cert:08X}", "product_id": f"0x{prod >> 16:04X}"}
        if vdo is not None and ptype in (3, 4):
            r["cable_vdo"] = f"0x{vdo:08X}"
            r["speed"] = SPEED.get(vdo & 7, f"code {vdo & 7}")
            r["current"] = CURRENT.get((vdo >> 5) & 3)
            r["max_vbus"] = VOLT[(vdo >> 9) & 3]
            r["epr"] = bool((vdo >> 17) & 1)   # passive cable VDO bit 17 = EPR Mode Capable (PD 3.1; bits 23:21 are the VDO version)
            r["vdo_version"] = (vdo >> 21) & 7
            r["latency_code"] = (vdo >> 13) & 0xF
            r["active"] = ptype == 4
            watts = {"3A": "60W", "5A": "100W"}.get(r["current"])
            if r["epr"] and r["current"] == "5A":
                watts = "240W"
            r["label_line1"] = r["speed"] + (" Active" if r["active"] else "")
            r["label_line2"] = f"{watts} {r['current']}" + (" EPR" if r["epr"] else "")
        out.append(r)
    return out


def format_result(r: dict) -> str:
    return "\n".join(f"{k:14} {v}" for k, v in r.items())
