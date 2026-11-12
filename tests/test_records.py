from cable_station import records
from cable_station import tester_capture as em
from pathlib import Path

FIX = Path(__file__).parent / "fixtures"


def test_round_trip(tmp_path):
    store = records.Store(tmp_path / "cables")
    assert store.read_all() == [] and store.next_id() == "C1"
    reading = em.decode((FIX / "emarker-screen-try2.log").read_text())[-1]
    row = records.from_decode(reading, "C1", "USB-C to USB-C", "test")
    p = store.write(row)
    assert p.name == "C1.md"
    text = p.read_text()
    assert text.startswith("---\ntype: cable\nid: C1\n")
    assert 'power_label: "100W 5A · #1"' in text          # quoted: holds a middle dot and a hash
    assert "epr: false" in text and "emarker: true" in text
    back = store.read_all()
    assert len(back) == 1
    r = back[0]
    assert r["id"] == "C1" and r["power_label"] == "100W 5A · #1" and r["epr"] is False and r["emarker"] is True
    assert r["cable_vdo"] == "0x00084042" and r["status"] == "active"
    assert store.next_id() == "C2"
    assert records.same_record(back, reading) == ["C1"]


def test_update_keeps_number_and_body(tmp_path):
    store = records.Store(tmp_path)
    store.write(records.no_emarker_row("C7", "USB-C to USB-C"), body="hand-written body")
    store.update("C7", {"data_label": "USB 3.2 5G", "power_label": "100W 5A", "emarker": True})
    r = store.get("C7")
    assert r["data_label"] == "USB 3.2 5G" and r["power_label"] == "100W 5A · #7" and r["emarker"] is True
    assert r["body"] == "hand-written body"


def test_decommission_and_reactivate(tmp_path):
    store = records.Store(tmp_path)
    store.write(records.no_emarker_row("C3", "USB-C to USB-C"))
    store.set_status("C3", "decommissioned")
    r = store.get("C3")
    assert r["status"] == "decommissioned" and r["decommissioned"]
    store.set_status("C3", "active")
    r = store.get("C3")
    assert r["status"] == "active" and r["decommissioned"] == ""


def test_ids_sort_numerically(tmp_path):
    store = records.Store(tmp_path)
    for cid in ("C10", "C2", "C1"):
        store.write(records.no_emarker_row(cid, "USB-C to USB-C"))
    assert [r["id"] for r in store.read_all()] == ["C1", "C2", "C10"]
    assert store.next_id() == "C11"


def test_ensure_base(tmp_path):
    store = records.Store(tmp_path)
    p = store.ensure_base()
    assert p.name == "_cables.base" and 'type == "cable"' in p.read_text()
    p.write_text("stale")
    store.ensure_base()
    assert p.read_text() == records.BASE


def test_quoting_round_trips_special_values(tmp_path):
    store = records.Store(tmp_path)
    row = records.no_emarker_row("C1", "USB-C to USB-C")
    row["notes"] = 'said "hello": [x] #tag'
    store.write(row)
    assert store.get("C1")["notes"] == 'said "hello": [x] #tag'
