import pytest
import sys
from pathlib import Path
from textual.widgets import DataTable

from cable_station import records
from cable_station.config import Settings
from cable_station.mac_reader import PortState
from cable_station.station import CableStation, tier


def make_settings(tmp_path) -> Settings:
    s = Settings(data_dir=tmp_path / "cables", state_dir=tmp_path / "state", km003c=str(tmp_path / "no-such-km003c"))
    s.ensure_dirs()
    return s


@pytest.mark.asyncio
async def test_table_lists_records_and_marks_retired(tmp_path):
    s = make_settings(tmp_path)
    store = records.Store(s.data_dir)
    store.write(records.no_emarker_row("C1", "USB-C to USB-C"))
    row = records.no_emarker_row("C2", "USB-C to USB-C")
    row["data_label"], row["power_label"] = "USB4 20G · USB 3.2 10G", "100W 5A · #2"
    store.write(row)
    store.set_status("C1", "decommissioned")
    app = CableStation(s, start_capture=False)
    async with app.run_test() as pilot:
        await pilot.pause()
        t = app.query_one(DataTable)
        assert t.row_count == 2
        assert [str(c) for c in t.get_row_at(1)[:3]] == ["C2", "USB4 20G · USB 3.2 10G", "100W 5A"]
        assert str(t.get_row_at(0)[-1]).startswith("RETIRED")
        assert "2 cables" in app.sub_title
        assert (s.data_dir / "_cables.base").exists()


@pytest.mark.asyncio
async def test_missing_km003c_is_reported_not_fatal(tmp_path):
    s = make_settings(tmp_path)
    app = CableStation(s, start_capture=True)
    async with app.run_test() as pilot:
        await pilot.pause(0.3)
        assert "km003c not found" in s.log_path.read_text()
        assert app.query_one(DataTable).row_count == 0


@pytest.mark.asyncio
async def test_n_stages_a_chipless_reading_and_s_discards(tmp_path):
    s = make_settings(tmp_path)
    app = CableStation(s, start_capture=False)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()
        t = app.query_one(DataTable)
        assert t.row_count == 1 and str(t.get_row_at(0)[0]).startswith("new?")
        assert app.pending is not None
        await pilot.press("s")
        await pilot.pause()
        assert app.pending is None and t.row_count == 0
        assert records.Store(s.data_dir).read_all() == []   # nothing written without Enter


@pytest.mark.asyncio
async def test_x_twice_decommissions(tmp_path):
    s = make_settings(tmp_path)
    records.Store(s.data_dir).write(records.no_emarker_row("C5", "USB-C to USB-C"))
    app = CableStation(s, start_capture=False)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("x")
        await pilot.pause()
        assert records.Store(s.data_dir).get("C5")["status"] == "active"   # first x only asks
        await pilot.press("x")
        await pilot.pause()
        assert records.Store(s.data_dir).get("C5")["status"] == "decommissioned"
        await pilot.press("u")
        await pilot.pause()
        assert records.Store(s.data_dir).get("C5")["status"] == "active"


def test_tier():
    assert tier("no eMarker · USB 2.0 480M") == tier("USB 2.0 480M link") == "USB 2.0 480M"
    assert tier("PWR ONLY · no data") == "no data"


@pytest.mark.asyncio
async def test_mode_bar_and_lightning_power_only(tmp_path):
    s = make_settings(tmp_path)
    app = CableStation(s, start_capture=False)
    async with app.run_test() as pilot:
        await pilot.pause()
        from textual.widgets import Static
        assert "1 TESTER" in str(app.query_one("#mode", Static).render())
        if sys.platform != "darwin":
            return
        await pilot.press("4")
        await pilot.pause()
        assert app.mode == "lightning" and app.connector == "Lightning"
        await pilot.press("c")
        await pilot.pause()
        assert app.connector == "USB-A to Lightning"
        await pilot.press("p")
        await pilot.pause()
        assert app.pending[0]["label_line1"] == "Lightning PWR ONLY" and app.pending[0]["label_line2"] == "2.4A"
        await pilot.press("q")


def test_settle_left_counts_down_per_signature_and_restarts_on_a_new_one(tmp_path):
    """Every Mac reading settles: SETTLE_S from the first time a (port, signature) is seen, 0 after that; a new signature on the port starts its own clock."""
    app = CableStation(make_settings(tmp_path), start_capture=False)
    none = ("nothing", ("none", "no link"), None)
    usb2 = ("Envoy Pro FX", ("usb2", "USB2 480 Mbps"), None)
    assert app.settle_left("P1", none, 1000.0) == app.SETTLE_S
    assert app.settle_left("P1", none, 1003.5) == app.SETTLE_S - 3            # 4.5 s left, shown as 5
    assert app.settle_left("P1", none, 1000.0 + app.SETTLE_S) == 0
    assert app.settle_left("P1", usb2, 1006.0) == app.SETTLE_S                 # the link trained: a new signature, a new clock
    assert app.settle_left("P1", usb2, 1006.0 + app.SETTLE_S) == 0
    app.mac_first = {}   # what set_mode does when the mode changes: the timers start over
    assert app.settle_left("P1", none, 2000.0) == app.SETTLE_S


def port(**kw) -> PortState:
    return PortState(port=2, connected=True, **kw)


@pytest.mark.asyncio
async def test_a_provisional_reading_shows_but_cannot_be_added_or_printed(tmp_path):
    s = make_settings(tmp_path)
    app = CableStation(s, start_capture=False)
    async with app.run_test() as pilot:
        await pilot.pause()
        app.mode = "drive"
        app.reading_from_port(port(usb2_rate="480 Mbps (High Speed)", usb2_product="Envoy Pro FX"), settled=False)
        await pilot.pause()
        assert app.pending[0]["settled"] is False and app.query_one(DataTable).row_count == 1
        await pilot.press("enter")
        await pilot.pause()
        assert app.pending is not None and records.Store(s.data_dir).read_all() == []   # refused: still settling
        await pilot.press("w")
        await pilot.pause()
        assert records.Store(s.data_dir).read_all() == []
        app.show_settling(port(usb2_rate="480 Mbps (High Speed)", usb2_product="Envoy Pro FX"), 5)
        await pilot.pause()
        await pilot.press("q")


@pytest.mark.asyncio
async def test_auto_mode_adds_and_prints_a_settled_reading_but_holds_power_only(tmp_path):
    s = make_settings(tmp_path)
    app = CableStation(s, start_capture=False)
    async with app.run_test() as pilot:
        await pilot.pause()
        app.mode = "drive"
        await pilot.press("a")
        await pilot.pause()
        assert app.auto is True
        app.reading_from_port(port(usb3_rate="10 Gbps", usb3_product="Envoy Pro FX"), settled=True)
        await pilot.pause()
        rows = records.Store(s.data_dir).read_all()
        assert [r["data_label"] for r in rows] == ["no eMarker · USB 3.2 10G"] and app.pending is None
        assert rows[0]["label_note"] == ""
        # a chipless power-only verdict: staged, not printed; the hedge is in the status line, never on the label
        app.last_print = None   # a different cable, outside the correction window
        app.reading_from_port(port(transports_active=["CC"]), settled=True)
        await pilot.pause()
        assert app.pending[0]["label_line1"] == "PWR ONLY · no data" and app.pending[0]["label_note"] == ""
        assert len(records.Store(s.data_dir).read_all()) == 1
        assert "far end" in Path(s.log_path).read_text()    # the status line (also logged) carries the question
        await pilot.press("a")
        await pilot.pause()
        assert app.auto is False
        await pilot.press("q")


def test_footer_names_are_short_with_tooltips_and_no_mode_keys():
    shown = [b for b in CableStation.BINDINGS if b.show]
    assert {b.key for b in shown} == {"enter", "a", "r", "n", "w", "x", "s", "q"}
    assert all(b.tooltip for b in shown) and all(len(b.description) <= 12 for b in shown)
    assert all(not b.show for b in CableStation.BINDINGS if b.key in ("1", "2", "3", "4"))


def test_correction_for_flags_a_port_that_changes_soon_after_a_print(tmp_path):
    app = CableStation(make_settings(tmp_path), start_capture=False)
    assert app.correction_for("P1", "USB4 40G", 100.0) is None
    app.last_print = ("P1", "C9", "PWR ONLY · no data", 100.0)
    assert app.correction_for("P1", "USB4 40G", 130.0) == ("C9", "PWR ONLY · no data", 30)
    assert app.correction_for("P1", "PWR ONLY · no data", 130.0) is None       # same label: nothing to correct
    assert app.correction_for("P2", "USB4 40G", 130.0) is None                 # another port
    assert app.correction_for("P1", "USB4 40G", 100.0 + app.CORRECTION_WINDOW_S) is None
