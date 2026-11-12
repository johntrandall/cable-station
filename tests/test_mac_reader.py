from pathlib import Path

from cable_station import mac_reader

FIX = Path(__file__).parent / "fixtures"


def test_parse_ports_fixture():
    ports = mac_reader.parse_ports((FIX / "ioreg-ports.plist").read_bytes())
    assert sorted(ports) == [1, 2, 3]
    assert ports[2].connected is False and ports[2].link() == ("none", "no link")
    p1 = ports[1]
    assert p1.connected and p1.emarker is None and p1.link()[0] == "dp"
    p3 = ports[3]
    assert p3.connected and p3.cio_active and "TS5" in p3.devices()
    e = p3.emarker
    assert e is not None
    assert (e.vendor_id, e.product_id) == (0x2B1D, 0x192B)
    assert e.kind == "passive" and e.current_a == 5 and e.epr is True and e.max_vbus_v == 50
    assert e.label_lines() == ("USB4 20G · USB 3.2 10G", "240W 5A EPR")
    assert e.cable_vdo == 0x420A4E42
    # Without system_profiler the Thunderbolt rate is unknown: class "tb"; with it, "tb40".
    assert p3.link()[0] == "tb"
    p3.tb_speed = "40 Gb/s"
    assert p3.link() == ("tb40", "Thunderbolt/USB4 40 Gb/s")


def test_decode_emarker_known_vdos():
    meta = {"VDOs": [bytes.fromhex(h) for h in ("1d2b601c", "00000000", "11042b19", "424e0a42")]}
    e = mac_reader.decode_emarker(meta, 3)
    assert e and e.kind == "passive" and e.vendor_id == 0x2B1D and e.product_id == 0x192B
    assert e.speed_code == 2 and e.current_a == 5 and e.max_vbus_v == 50 and e.epr
    assert e.watts == 240 and e.length == "~2 m"
    r = e.as_reading()
    assert r["cable_vdo"] == "0x420A4E42" and r["label_line2"] == "240W 5A EPR" and r["vendor_id"] == "0x2B1D"


def test_decode_emarker_pd2_has_no_epr():
    meta = {"VDOs": [bytes.fromhex(h) for h in ("1d2b601c", "00000000", "11042b19", "424e0a42")]}
    e = mac_reader.decode_emarker(meta, 2)
    assert e.epr is False and e.max_vbus_v is None and e.watts == 100


def test_decode_emarker_short():
    assert mac_reader.decode_emarker({"VDOs": [b"\0\0\0\0"]}, 3) is None
