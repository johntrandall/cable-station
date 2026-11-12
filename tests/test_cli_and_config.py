from pathlib import Path

from cable_station import cli, config

FIX = Path(__file__).parent / "fixtures"


def test_config_file_and_env(tmp_path, monkeypatch):
    p = tmp_path / "config.toml"
    p.write_text('data_dir = "~/somewhere/cables"\nprinter_model = "PT-P750W"\ntape_mm = 12\n[partners]\ndrive = ["MyDrive"]\n')
    for k in list(config.ENV_PREFIX + x for x in ("DATA", "STATE", "PRINTER", "TAPE", "KM003C", "DRIVE_PARTNERS", "DOCK_PARTNERS")):
        monkeypatch.delenv(k, raising=False)
    s = config.load(p)
    assert s.data_dir == Path("~/somewhere/cables").expanduser()
    assert s.printer_model == "PT-P750W" and s.tape_mm == 12
    assert s.partners == {"drive": ["MyDrive"]}
    monkeypatch.setenv("CABLE_STATION_PRINTER", "PT-P950NW")
    monkeypatch.setenv("CABLE_STATION_DATA", str(tmp_path / "d"))
    monkeypatch.setenv("CABLE_STATION_DOCK_PARTNERS", "Dock A, Dock B")
    s = config.load(p)
    assert s.printer_model == "PT-P950NW" and s.data_dir == tmp_path / "d" and s.partners["dock"] == ["Dock A", "Dock B"]


def test_defaults_when_no_file(tmp_path, monkeypatch):
    monkeypatch.setenv("CABLE_STATION_CONFIG", str(tmp_path / "missing.toml"))
    for k in ("DATA", "STATE", "PRINTER"):
        monkeypatch.delenv(config.ENV_PREFIX + k, raising=False)
    s = config.load()
    assert s.source == "defaults" and s.tape_mm == 9 and s.km003c == "km003c"


def test_cli_decode(capsys, tmp_path, monkeypatch):
    monkeypatch.setenv("CABLE_STATION_CONFIG", str(tmp_path / "missing.toml"))
    assert cli.main(["decode", str(FIX / "emarker-screen-try4.log")]) == 0
    out = capsys.readouterr().out
    assert "label_line2    100W 5A" in out


def test_cli_version(capsys):
    try:
        cli.main(["--version"])
    except SystemExit as e:
        assert e.code == 0
    assert "cable-station 0.1.1" in capsys.readouterr().out


def test_cli_print_render_only(capsys, tmp_path, monkeypatch):
    from cable_station import records
    monkeypatch.setenv("CABLE_STATION_CONFIG", str(tmp_path / "missing.toml"))
    monkeypatch.setenv("CABLE_STATION_DATA", str(tmp_path / "cables"))
    monkeypatch.setenv("CABLE_STATION_STATE", str(tmp_path / "state"))
    records.Store(tmp_path / "cables").write(records.no_emarker_row("C4", "USB-C to USB-C"))
    assert cli.main(["print", "4", "--render-only"]) == 0
    assert (tmp_path / "state" / "previews" / "C4.png").exists()
    assert "C4: no eMarker" in capsys.readouterr().out
    assert cli.main(["print", "C9", "--render-only"]) == 1


def test_cli_doctor_runs(capsys, tmp_path, monkeypatch):
    monkeypatch.setenv("CABLE_STATION_CONFIG", str(tmp_path / "missing.toml"))
    monkeypatch.setenv("CABLE_STATION_DATA", str(tmp_path / "cables"))
    monkeypatch.setenv("CABLE_STATION_STATE", str(tmp_path / "state"))
    cli.main(["doctor"])
    out = capsys.readouterr().out
    assert "km003c CLI" in out and "ptouch-label" in out
