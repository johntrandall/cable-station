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


def test_print_guard_holds_a_repeat_and_a_burst(tmp_path):
    """The same flag within REPEAT_GUARD_S, or more than BURST_N prints in BURST_S, is a reason to wait; otherwise None."""
    app = CableStation(make_settings(tmp_path), start_capture=False)
    assert app.print_guard("USB4 40G", "100W 5A", "C3", 1000.0) is None
    app.last_label = ("USB4 40G", "100W 5A", "C3", 1000.0)
    assert "same flag" in app.print_guard("USB4 40G", "100W 5A", "C3", 1005.0)
    assert app.print_guard("USB4 40G", "100W 5A", "C3", 1000.0 + app.REPEAT_GUARD_S) is None
    assert app.print_guard("USB4 40G", "100W 5A", "C4", 1005.0) is None            # another id: not a repeat
    app.prints = [1001.0, 1010.0, 1020.0]
    assert "flags printed" in app.print_guard("USB 3.2 10G", "60W 3A", "C9", 1025.0)
    assert app.print_guard("USB 3.2 10G", "60W 3A", "C9", 1001.0 + app.BURST_S + 0.1) is None


@pytest.mark.asyncio
async def test_a_held_print_needs_a_second_press_and_auto_never_overrides(tmp_path):
    s = make_settings(tmp_path)
    app = CableStation(s, start_capture=False)
    async with app.run_test() as pilot:
        await pilot.pause()
        app.mode = "drive"
        app.reading_from_port(port(usb3_rate="10 Gbps", usb3_product="Envoy Pro FX"), settled=True)
        await pilot.pause()
        await pilot.press("enter"); await pilot.pause()    # preview
        await pilot.press("enter"); await pilot.pause()    # print C1
        assert [r["id"] for r in records.Store(s.data_dir).read_all()] == ["C1"]
        # r on C1 at once: held, then printed on the second r
        await pilot.press("r"); await pilot.pause()
        assert app.confirm_print == "r"
        await pilot.press("r"); await pilot.pause()
        assert app.confirm_print is None and len(app.prints) == 2
        # auto mode: the same reading again on the same port is held, never printed
        app.last_print = None
        await pilot.press("a"); await pilot.pause()
        app.reading_from_port(port(usb3_rate="10 Gbps", usb3_product="Envoy Pro FX"), settled=True)
        await pilot.pause()
        assert app.pending is not None and len(records.Store(s.data_dir).read_all()) == 1
        assert "AUTO holds" in Path(s.log_path).read_text()
        await pilot.press("q")


@pytest.mark.asyncio
async def test_a_dropout_is_written_into_the_printed_cable_and_a_swap_is_only_logged(tmp_path):
    s = make_settings(tmp_path)
    app = CableStation(s, start_capture=False)
    async with app.run_test() as pilot:
        await pilot.pause()
        app.mode = "drive"
        app.port_printed[2] = ("C7", "no eMarker · USB 2.0 480M", 100.0)
        app.db.write(records.no_emarker_row("C7", "USB-C to USB-C", "Mac read: test"))
        live = port(usb2_rate="480 Mbps", usb2_product="Envoy Pro FX")
        gone = PortState(port=2, connected=False)
        assert app.watch_partner(live, 1000.0) is None
        assert app.watch_partner(live, 1005.0) is None           # still up: nothing to report
        ev = app.watch_partner(gone, 1010.0)                     # 10 s up: a swap
        assert ev == (2, "Envoy Pro FX", 10.0)
        app.port_gone(*ev)
        await pilot.pause()
        assert "DROPOUT" not in (app.db.get("C7") or {}).get("notes", "") and 2 in app.port_printed
        assert app.watch_partner(gone, 1012.0) is None           # reported once
        app.watch_partner(live, 2000.0)
        app.port_gone(*app.watch_partner(gone, 2000.0 + app.DROPOUT_MIN_S + 5))
        await pilot.pause()
        assert "DROPOUT" in app.db.get("C7")["notes"] and "Envoy Pro FX" in app.db.get("C7")["notes"]
        assert 2 not in app.port_printed
        assert "DROPOUT port 2" in Path(s.log_path).read_text()
        await pilot.press("q")
