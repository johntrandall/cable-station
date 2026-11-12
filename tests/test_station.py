import pytest
import sys
from textual.widgets import DataTable

from cable_station import records
from cable_station.config import Settings
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
