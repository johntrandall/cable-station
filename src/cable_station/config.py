"""Settings for cable-station: a TOML file plus environment variables.

Resolution order for every setting: environment variable, then the config file, then the default.
The config file is `~/.config/cable-station/config.toml` (override the path with `CABLE_STATION_CONFIG`).
Nothing site-specific is hard-coded here: printer, partner device names, and the data folder all come
from the file or the environment.

Example `config.toml`:

    data_dir = "~/cable-station/cables"        # one Markdown note per cable, plus the Obsidian Base
    state_dir = "~/.local/state/cable-station"  # log, per-cable captures, rendered flag previews
    printer_model = "PT-P950NW"                 # ptouch-label --model
    tape_mm = 9                                 # tape loaded in the printer: 6, 9, 12, 18 or 24
    km003c = "km003c"                           # the km003c CLI (name on PATH or a full path)
    capture_hours = 3                           # how long one tester capture runs before it restarts
    connector = "USB-C to USB-C"

    [partners]
    drive = ["Envoy", "Sabrent"]                # drive-mode partner names as macOS reports them (empty: any device)
    dock = ["TS5"]                              # dock-mode partner names
"""
from __future__ import annotations

import os
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

ENV_PREFIX = "CABLE_STATION_"


def _env(name: str) -> str | None:
    v = os.environ.get(ENV_PREFIX + name)
    return v if v else None


def config_path() -> Path:
    return Path(_env("CONFIG") or "~/.config/cable-station/config.toml").expanduser()


@dataclass
class Settings:
    data_dir: Path = Path("~/cable-station/cables").expanduser()
    state_dir: Path = Path("~/.local/state/cable-station").expanduser()
    printer_model: str = "PT-P950NW"
    tape_mm: int = 9
    km003c: str = "km003c"
    capture_hours: float = 3.0
    connector: str = "USB-C to USB-C"
    # Vertical calibration offset of the printer, in mm: ink pushed off the band by this shift is clipped
    # by ptouch-label (it shrinks the label), so the renderer keeps all ink inside the reachable rows.
    vertical_offset_mm: float = 1.45
    # Partner device names (as macOS reports them) that modes 2 and 3 watch for; empty means any device.
    partners: dict[str, list[str]] = field(default_factory=lambda: {"drive": [], "dock": []})
    source: str = "defaults"

    @property
    def captures_dir(self) -> Path:
        return self.state_dir / "captures"

    @property
    def previews_dir(self) -> Path:
        return self.state_dir / "previews"

    @property
    def log_path(self) -> Path:
        return self.state_dir / "cable_watch.log"

    def ensure_dirs(self) -> None:
        for d in (self.data_dir, self.state_dir, self.captures_dir, self.previews_dir):
            d.mkdir(parents=True, exist_ok=True)


def load(path: Path | None = None) -> Settings:
    """Settings from the environment, the TOML file, and the defaults, in that order of precedence."""
    s = Settings()
    p = path or config_path()
    file: dict = {}
    if p.is_file():
        with open(p, "rb") as f:
            file = tomllib.load(f)
        s.source = str(p)
    if "data_dir" in file:
        s.data_dir = Path(file["data_dir"]).expanduser()
    if "state_dir" in file:
        s.state_dir = Path(file["state_dir"]).expanduser()
    for key in ("printer_model", "km003c", "connector"):
        if key in file:
            setattr(s, key, str(file[key]))
    if s.km003c.startswith("~"):
        s.km003c = str(Path(s.km003c).expanduser())
    if "tape_mm" in file:
        s.tape_mm = int(file["tape_mm"])
    if "capture_hours" in file:
        s.capture_hours = float(file["capture_hours"])
    if "vertical_offset_mm" in file:
        s.vertical_offset_mm = float(file["vertical_offset_mm"])
    if isinstance(file.get("partners"), dict):
        s.partners = {k: [str(x) for x in v] for k, v in file["partners"].items()}
    # Environment overrides.
    if _env("DATA"):
        s.data_dir = Path(_env("DATA")).expanduser()
    if _env("STATE"):
        s.state_dir = Path(_env("STATE")).expanduser()
    if _env("PRINTER"):
        s.printer_model = _env("PRINTER")
    if _env("TAPE"):
        s.tape_mm = int(_env("TAPE"))
    if _env("KM003C"):
        s.km003c = _env("KM003C")
    if _env("CONNECTOR"):
        s.connector = _env("CONNECTOR")
    if _env("CAPTURE_HOURS"):
        s.capture_hours = float(_env("CAPTURE_HOURS"))
    if _env("DRIVE_PARTNERS"):
        s.partners["drive"] = [x.strip() for x in _env("DRIVE_PARTNERS").split(",") if x.strip()]
    if _env("DOCK_PARTNERS"):
        s.partners["dock"] = [x.strip() for x in _env("DOCK_PARTNERS").split(",") if x.strip()]
    return s


def is_macos() -> bool:
    return sys.platform == "darwin"
