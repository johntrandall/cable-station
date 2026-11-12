from pathlib import Path

from cable_station import tester_capture as em

FIX = Path(__file__).parent / "fixtures"


def test_decode_try2_finds_the_cable_answer():
    res = em.decode((FIX / "emarker-screen-try2.log").read_text())
    assert res, "no Discover Identity ACK found"
    r = res[-1]
    assert r["product_type"] == "passive cable"
    assert r["cable_vdo"] == "0x00084042"
    assert r["current"] == "5A"
    assert r["epr"] is False
    assert r["speed"] == "USB4 20G · USB 3.2 10G"
    assert r["label_line1"] == "USB4 20G · USB 3.2 10G"
    assert r["label_line2"] == "100W 5A"
    assert r["active"] is False


def test_decode_try4_matches_try2():
    a = em.decode((FIX / "emarker-screen-try2.log").read_text())[-1]
    b = em.decode((FIX / "emarker-screen-try4.log").read_text())[-1]
    assert (a["cable_vdo"], a["vendor_id"], a["product_id"]) == (b["cable_vdo"], b["vendor_id"], b["product_id"])


def test_frames_join_continuation_lines():
    text = "[1.0s] RAW[22]: 8F 51 41 A0 00 FF 00 00 00 18 00 00 00 00 00 00 \n                     00 00 42 40 08 00 \n[1.0s] SOP1: Data(VendorDefined)\n"
    fr = list(em.frames(text))
    assert len(fr) == 1 and fr[0][0] == 22 and len(fr[0][1]) == 22


def test_decode_epr_active_cable_synthetic():
    # Build a Discover Identity ACK: header type 15 with 5 objects; active cable (type 4); 5 A, EPR bit, speed code 3.
    vdm = 0xFF008041                       # SVID FF00, structured, ACK (cmd type 1), command 1
    idh = (4 << 27) | 0x05AC               # active cable, vendor 0x05AC
    cert, prod = 0, (0x1234 << 16)
    vdo = (3) | (2 << 5) | (3 << 9) | (1 << 17)   # speed 3, 5 A, 50 V, EPR
    objs = [vdm, idh, cert, prod, vdo]
    hdr = 0x0F | (len(objs) << 12)
    raw = hdr.to_bytes(2, "little") + b"".join(o.to_bytes(4, "little") for o in objs)
    line = f"[2.0s] RAW[{len(raw)}]: " + " ".join(f"{b:02X}" for b in raw) + " \n"
    r = em.decode(line)[0]
    assert r["active"] is True and r["epr"] is True and r["current"] == "5A"
    assert r["label_line1"] == "USB4 ≥40G · USB 3.2 10G Active"
    assert r["label_line2"] == "240W 5A EPR"
    assert r["vendor_id"] == "0x05AC" and r["product_id"] == "0x1234"


def test_decode_ignores_non_identity_frames():
    assert em.decode("[1.0s] RAW[2]: 01 01 \n[1.0s] SOP1: Control(GoodCRC)\n") == []
