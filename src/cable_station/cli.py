"""The `cable-station` command.

Subcommands:
  station            the full-screen station (default when no subcommand is given)
  snapshot [--json]  what every USB-C port of this Mac sees right now: chip, link, partner
  decode LOG         decode a `km003c pd capture --raw` log and print the cable's e-marker fields
  print ID           reprint the flag of a recorded cable (--dry-run renders without printing)
  doctor             check the tools and folders the station needs
  config             print the settings in force and where they came from
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import asdict
from pathlib import Path

from . import __version__, config, records
from . import tester_capture as em


def cmd_station(s: config.Settings, a) -> int:
    from .station import CableStation
    if a.hours:
        s.capture_hours = a.hours
    if a.connector:
        s.connector = a.connector
    CableStation(s).run()
    return 0


def cmd_snapshot(s: config.Settings, a) -> int:
    if not config.is_macos():
        print("snapshot reads the Mac's port registry (ioreg) and needs macOS.", file=sys.stderr)
        return 2
    from . import mac_reader
    ports = mac_reader.read_ports()
    if a.json:
        out = {}
        for p, st in sorted(ports.items()):
            d = asdict(st)
            d["link_class"], d["link"] = st.link()
            if st.emarker:
                d["emarker"]["label_lines"] = list(st.emarker.label_lines())
                d["emarker"]["watts"] = st.emarker.watts
            out[p] = d
        print(json.dumps(out, indent=2, default=str))
    else:
        for p, st in sorted(ports.items()):
            print(st.summary())
    if a.read_test:
        from . import throughput
        vol = Path("/Volumes") / a.read_test if not a.read_test.startswith("/") else Path(a.read_test)
        if not vol.is_dir():
            print(f"volume {vol} is not mounted", file=sys.stderr)
            return 2
        res = throughput.read_throughput(vol, a.seconds)
        if res is None:
            print(f"no files of 256 MB or more on {vol} to read")
        else:
            print(f"read test (experimental): {res[0]:,.0f} MB/s over {res[1] / 1e6:,.0f} MB from {vol}")
    return 0


def cmd_decode(s: config.Settings, a) -> int:
    text = Path(a.log).read_text(errors="replace")
    res = em.decode(text)
    if not res:
        print("no cable Discover Identity ACK on SOP' found in the capture", file=sys.stderr)
        return 1
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        for r in res:
            print(em.format_result(r))
            print()
    return 0


def cmd_print(s: config.Settings, a) -> int:
    from .station import Printer
    store = records.Store(s.data_dir)
    rec = store.get(a.id if a.id.startswith("C") else f"C{a.id}")
    if rec is None:
        print(f"no record {a.id} in {s.data_dir}", file=sys.stderr)
        return 1
    s.ensure_dirs()
    line1, line2 = rec["data_label"], rec["power_label"].split(" · #")[0]
    printer = Printer(s)
    png, desc = printer.render(rec["id"], line1, line2, rec.get("label_note", ""))
    print(f"{rec['id']}: {line1} / {line2} · #{rec['id'][1:]}  ->  {png} ({desc})")
    if a.preview:
        printer.open_preview(png)
    if not a.render_only:
        print(printer.print(rec["id"], line1, line2, rec.get("label_note", ""), dry_run=a.dry_run))
    return 0


def cmd_doctor(s: config.Settings, a) -> int:
    ok = True

    def row(label, good, detail):
        nonlocal ok
        ok = ok and (good is not False)
        mark = {True: "ok  ", False: "MISSING", None: "info"}[good]
        print(f"{mark:8}{label:28}{detail}")

    row("config file", True if Path(s.source).is_file() else None, s.source if s.source != "defaults" else f"none (defaults in force; create {config.config_path()})")
    row("data dir (records)", s.data_dir.is_dir() or None, f"{s.data_dir}  ({len(records.Store(s.data_dir).read_all()) if s.data_dir.is_dir() else 0} cables)" if s.data_dir.is_dir() else f"{s.data_dir}  (created on first run)")
    row("state dir", s.state_dir.is_dir() or None, str(s.state_dir))
    km = shutil.which(s.km003c) or (s.km003c if Path(s.km003c).is_file() else None)
    row("km003c CLI (tester path)", bool(km), km or f"{s.km003c} not on PATH: build okhsunrog/km003c-rs (see README); modes 2 and 3 still work")
    pt = shutil.which("ptouch-label")
    row("ptouch-label (printing)", bool(pt), pt or "not on PATH: `uv tool install git+https://github.com/johntrandall/ptouch-label`; flags still render to the state dir")
    row("printer model", True, f"{s.printer_model}, {s.tape_mm} mm tape")
    if config.is_macos():
        from . import mac_reader
        row("tester on USB", mac_reader.tester_present() or None, "a POWER-Z device is on the USB tree" if mac_reader.tester_present() else "no POWER-Z device seen on USB (plug the tester's PC port into this Mac for mode 1)")
        try:
            ports = mac_reader.read_ports()
            row("Mac port registry", True, f"{len(ports)} USB-C ports readable (modes 2 and 3)")
        except Exception as e:
            row("Mac port registry", False, f"ioreg failed: {e}")
    else:
        row("Mac port registry", None, "not macOS: modes 2 and 3 (the Mac reader) are unavailable; the tester path and records work")
    row("partners", True, ", ".join(f"{k}: {', '.join(v) or 'any device'}" for k, v in s.partners.items()))
    print("\nall required tools present" if ok else "\nsomething is missing; the lines marked MISSING say what to install")
    return 0 if ok else 1


def cmd_config(s: config.Settings, a) -> int:
    d = asdict(s)
    d["data_dir"], d["state_dir"] = str(s.data_dir), str(s.state_dir)
    d["config_path"] = str(config.config_path())
    print(json.dumps(d, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="cable-station", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"cable-station {__version__}")
    ap.add_argument("--config", help="settings file (default ~/.config/cable-station/config.toml)")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("station", help="the full-screen station (default)")
    p.add_argument("--hours", type=float, help="length of one tester capture before it restarts")
    p.add_argument("--connector", help='connector type recorded for new cables, e.g. "USB-C to USB-C"')
    p.set_defaults(func=cmd_station)
    p = sub.add_parser("snapshot", help="what every USB-C port sees right now (macOS)")
    p.add_argument("--json", action="store_true")
    p.add_argument("--read-test", metavar="VOLUME", help="experimental: also read files from this mounted volume and report MB/s")
    p.add_argument("--seconds", type=float, default=8.0)
    p.set_defaults(func=cmd_snapshot)
    p = sub.add_parser("decode", help="decode a `km003c pd capture --raw` log")
    p.add_argument("log")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_decode)
    p = sub.add_parser("print", help="reprint a recorded cable's flag")
    p.add_argument("id", help="C17 or 17")
    p.add_argument("--dry-run", action="store_true", help="pass --dry-run to ptouch-label")
    p.add_argument("--render-only", action="store_true", help="render the PNG, do not call ptouch-label")
    p.add_argument("--preview", action="store_true", help="open the rendered PNG")
    p.set_defaults(func=cmd_print)
    p = sub.add_parser("doctor", help="check tools and folders")
    p.set_defaults(func=cmd_doctor)
    p = sub.add_parser("config", help="print the settings in force")
    p.set_defaults(func=cmd_config)
    return ap


def main(argv=None) -> int:
    ap = build_parser()
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    s = config.load(Path(a.config).expanduser() if a.config else None)
    if a.cmd is None:   # bare `cable-station` opens the station
        return cmd_station(s, argparse.Namespace(hours=None, connector=None))
    return a.func(s, a)


if __name__ == "__main__":
    sys.exit(main())
