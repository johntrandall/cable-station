"""The cable station: a small full-screen app around the tester.

One table, aligned so cables compare: the pending reading is the first row (ID "new?"), every recorded
cable follows, and rows whose e-marker record matches the pending reading are highlighted. Keys:
  Enter   preview, then print the pending reading with a NEW number and write its note
  r       reprint the highlighted row's number (no new note)
  1 2 3 4 mode: 1 tester (readings from the POWER-Z capture), 2 drive, 3 dock (the Mac reads the cable),
          4 lightning (an iPhone or iPad enumerating on the Mac is the reading; c cycles the other plug, p records power only)
  n       stage the seated cable as chipless, untested (Enter prints it)
  w       write the pending reading into the highlighted row (a retest keeps its number); w twice
  x       decommission the highlighted cable; x twice
  u       undo a decommission
  s       discard the pending reading
  q       quit (the capture stops with the app)
The records are Markdown notes (records.py) with an Obsidian Base as their table.
"""
from __future__ import annotations

import asyncio
import datetime
import math
import subprocess
import sys
import time
from pathlib import Path

from rich.text import Text
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable, Footer, Static

from . import flag, mac_reader, records
from . import tester_capture as em
from .config import Settings

COLS = ("ID", "data", "power", "A", "EPR", "active", "chip", "vendor", "product", "VDO", "tested", "load", "status")


def yn(v):
    return "yes" if v is True else ("no" if v is False else str(v))


def tier(label: str) -> str:
    """The speed tier of a data label, for the loose 'same label' match: 'no eMarker · USB 2.0 480M' and
    'USB 2.0 480M link' are the same tier."""
    return label.replace("no eMarker · ", "").replace(" link", "").replace("PWR ONLY · no data", "no data").strip()


class Printer:
    """Renders flags into the state dir and prints them with ptouch-label."""

    def __init__(self, settings: Settings):
        self.s = settings

    def render(self, cid: str, line1: str, line2: str, note: str = "") -> tuple[Path, str]:
        """Render the flag PNG and return (path, one-line description of its size). A note prints after the power text."""
        png = self.s.previews_dir / f"{cid}.png"
        png.parent.mkdir(parents=True, exist_ok=True)
        text2 = f"{line2} · {note}" if note else line2
        desc = flag.render(str(png), line1, text2, tape=self.s.tape_mm, cable_id=cid, vertical_offset_mm=self.s.vertical_offset_mm)
        return png, desc

    def print(self, cid: str, line1: str, line2: str, note: str = "", dry_run: bool = False) -> str:
        png, _ = self.render(cid, line1, line2, note)
        cmd = ["ptouch-label", "--model", self.s.printer_model, "--for", "cable", "--image", str(png)]
        if dry_run:
            cmd.append("--dry-run")
        try:
            out = subprocess.run(cmd, capture_output=True, text=True)
        except FileNotFoundError:
            return f"ptouch-label not found on PATH; flag rendered at {png}"
        text = out.stdout + out.stderr
        cut = [l for l in text.splitlines() if l.startswith("Cuts:") or "Sent to" in l or "rror" in l or "scaled" in l] or [out.stderr.strip()[-120:]]
        return " · ".join(cut)

    @staticmethod
    def open_preview(png: Path) -> None:
        if sys.platform == "darwin":
            subprocess.run(["open", "-g", "-a", "Preview", str(png)])
        else:
            subprocess.Popen(["xdg-open", str(png)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class CableStation(App):
    TITLE = "Cable station · POWER-Z KM003C · BETA, untested"
    SETTLE_S = 8                # a Mac reading is settled when the port has held one signature this long: links train in stages (USB 2, then USB 3 or Thunderbolt) within a few seconds
    CORRECTION_WINDOW_S = 120   # a port that changes its reading this soon after a print probably still holds the printed cable
    CSS = """
    #mode { height: 1; padding: 0 2; background: $accent; color: $text; text-style: bold; }
    #reading { height: auto; max-height: 12; padding: 0 1; border: round $accent; }
    #status { height: 1; padding: 0 2; color: $text-muted; }
    DataTable { height: 1fr; }
    """
    # The footer shows the short name; hovering a key shows its tooltip. The mode keys 1-4 live in the mode bar, not here.
    BINDINGS = [
        Binding("enter", "print_new", "print", priority=True,
                tooltip="Preview the pending reading's flag; Enter again adds it to the database as a NEW cable and prints. With nothing pending: reprint the highlighted row."),
        Binding("a", "toggle_auto", "auto",
                tooltip="Auto mode on or off. On: a settled reading in drive, dock or lightning mode is added and printed by itself; you touch only cables and labels. A power-only verdict still waits for Enter."),
        Binding("r", "reprint", "reprint", tooltip="Reprint the highlighted cable's flag (no new record)."),
        Binding("1", "mode_tester", "tester", show=False, tooltip="Mode 1: readings come from the POWER-Z capture."),
        Binding("2", "mode_drive", "drive", show=False, tooltip="Mode 2: the Mac reads the cable plugged between it and the drive."),
        Binding("3", "mode_dock", "dock", show=False, tooltip="Mode 3: the Mac reads the cable plugged between it and the dock."),
        Binding("4", "mode_lightning", "lightning", show=False, tooltip="Mode 4: an iPhone or iPad enumerating on the Mac is the reading."),
        Binding("c", "toggle_connector", "connector", show=False, tooltip="Lightning mode: cycle the other end's plug (Lightning, USB-A, USB-C)."),
        Binding("p", "power_only", "power only", show=False, tooltip="Lightning mode: stage a power-only Lightning cable."),
        Binding("n", "no_emarker", "no chip", tooltip="Stage the seated cable as chipless and untested (no eMarker · USB 2.0 480M over 60W 3A); Enter prints it."),
        Binding("w", "write_into", "update", tooltip="Write the pending reading into the highlighted row: a retest that keeps its number, then reprint. Press w twice."),
        Binding("x", "decommission", "retire", tooltip="Decommission the highlighted cable (broken or discarded); its record and number stay. Press x twice. u undoes it."),
        Binding("u", "reactivate", "undo retire", show=False, tooltip="Put a decommissioned cable back in service."),
        Binding("s", "discard", "discard", tooltip="Discard the pending reading."),
        Binding("q", "quit", "quit", tooltip="Quit; the capture stops with the station."),
        Binding("ctrl+c", "quit", "quit", show=False, priority=True),
    ]

    def __init__(self, settings: Settings, start_capture: bool = True):
        super().__init__()
        self.s = settings
        self.db = records.Store(settings.data_dir)
        self.printer = Printer(settings)
        self.hours, self.connector = settings.capture_hours, settings.connector
        self.start_capture = start_capture
        self.pending = None      # (record, time, runs, capture lines)
        self.mode = "tester"
        self.auto = False        # a: auto mode adds and prints each settled reading by itself (drive, dock, lightning)
        self.mac_seen = {}       # port -> (signature, settled) of the reading last staged from it
        self.mac_first = {}      # (port, signature) -> when that signature was first seen (the settle timer)
        self.last_print = None   # (port, cable id, label line 1, time) of the last print that came from a Mac port
        self.last_key, self.last_mono = None, 0.0
        self.proc = None
        self.previewed = False
        self.confirm_x = None
        self.confirm_w = None
        self._mac_watching = False
        self._stop = False
        self.settings = settings
        drive = ", ".join(settings.partners.get("drive", [])) or "any device"
        dock = ", ".join(settings.partners.get("dock", [])) or "any device"
        self.MODES = {"tester": "TESTER: run the eMarker module on the POWER-Z; readings arrive from its capture",
                      "drive": f"DRIVE: plug each cable between this Mac and a drive ({drive}); the Mac reads it",
                      "dock": f"DOCK: plug each cable between this Mac and the dock ({dock}); the Mac reads it",
                      "lightning": "LIGHTNING: plug the Lightning end into an iPhone or iPad and the other end into the Mac or the dock; p records power only; c records the other end's plug (A or C) if you want it"}

    # ----- layout -----

    def compose(self) -> ComposeResult:
        yield Static("", id="mode")
        yield Static("BETA, UNTESTED · waiting for a reading · seat a cable · tester: Application › Modules › USB-C eMarker · rotate the plug if asked", id="reading")
        yield Static("", id="status")
        yield DataTable(id="cables", cursor_type="row", zebra_stripes=True)
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(DataTable).add_columns(*COLS)
        self.s.ensure_dirs()
        self.db.ensure_base()
        self.show_mode()
        self.refresh_table()
        if self.start_capture:
            self.set_status("capture starting")
            self.capture()
        else:
            self.set_status("capture not started")

    def log_line(self, line: str) -> None:
        try:
            with open(self.s.log_path, "a") as f:
                f.write(f"[{datetime.datetime.now():%H:%M:%S}] {line.rstrip()}\n")
        except OSError:
            pass

    def set_status(self, text: str) -> None:
        self.query_one("#status", Static).update(f"{datetime.datetime.now():%H:%M:%S}  {text}")
        self.log_line(text)
        self.update_title()

    def update_title(self) -> None:
        n = len(self.db.read_all())
        state = "reading pending" if self.pending else ("tester connected" if (self.proc and self.proc.returncode is None) else "tester absent")
        self.sub_title = f"BETA, untested · {n} cables · mode {self.mode} · {state}"

    def refresh_table(self) -> None:
        t = self.query_one(DataTable)
        keep = None
        if t.row_count and t.cursor_row < t.row_count:
            keep = str(t.get_row_at(t.cursor_row)[0]).split()[0]
        t.clear()
        rows = self.db.read_all()
        pend = self.pending[0] if self.pending else None
        matches = set(records.same_record(rows, pend)) if (pend and pend.get("cable_vdo")) else set()
        # chipless (or unread) readings have no identity: a weaker "same label" match, shown in cyan, not green
        label_matches = set()
        if pend and not pend.get("cable_vdo"):
            label_matches = {r["id"] for r in rows if not r["cable_vdo"] and tier(r["data_label"]) == tier(pend["label_line1"])}
        if pend:
            nxt = self.db.next_id(rows)
            cells = [f"new? (#{nxt[1:]})", pend["label_line1"], pend["label_line2"], (pend["current"] or "")[:-1], yn(pend["epr"]), yn(pend["active"]),
                     ("yes" if pend["cable_vdo"] else ("unread" if pend.get("product_type", "").startswith("e-marked") else "no")), pend["vendor_id"], pend["product_id"], pend["cable_vdo"], datetime.date.today().isoformat(), "", ""]
            t.add_row(*[Text(c, style="bold yellow") for c in cells], key="__pending__")
        for r in rows:
            chip = "unread" if (r["emarker"] is True and r.get("emarker_read") is False) else yn(r["emarker"])
            cells = [r["id"], r["data_label"], r["power_label"].split(" · #")[0], r["current_a"] or "?", yn(r["epr"]) if r["epr"] != "" else "?", yn(r["active"]), chip,
                     r["vendor"], r["product"], r["cable_vdo"], r["tested"], r["load_test"]]
            cells.append("RETIRED " + (r.get("decommissioned") or "") if r.get("status") == "decommissioned" else "")
            if r.get("status") == "decommissioned":
                cells = [Text(str(c), style="dim strike") for c in cells]
            elif r["id"] in matches:
                cells = [Text(c, style="bold green") for c in cells]
                cells[0] = Text(f"{r['id']} =", style="bold green")
            elif r["id"] in label_matches:
                cells = [Text(str(c), style="bold cyan") for c in cells]
                cells[0] = Text(f"{r['id']} ~", style="bold cyan")
            t.add_row(*cells, key=r["id"])
        ids = [r["id"] for r in rows]
        if not matches and label_matches:
            t.move_cursor(row=(1 if pend else 0) + ids.index(sorted(label_matches, key=lambda x: int(x[1:]))[-1]))
        elif matches:
            t.move_cursor(row=(1 if pend else 0) + ids.index(sorted(matches, key=lambda x: int(x[1:]))[-1]))
        elif pend:
            t.move_cursor(row=0)
        elif keep in ids:
            t.move_cursor(row=ids.index(keep))   # the highlight stays on the row the user had

    def show_pending(self) -> None:
        self.update_title()
        r, when, runs, _ = self.pending
        rows = self.db.read_all()
        same = records.same_record(rows, r) if r.get("cable_vdo") else []
        if not same and not r.get("cable_vdo"):
            same_label = [x["id"] for x in rows if not x["cable_vdo"] and tier(x["data_label"]) == tier(r["label_line1"])]
            if same_label:
                self.query_one("#reading", Static).update(Text(f"{when}  run {runs}:  {r['label_line1']}  /  {r['label_line2']}   SAME TIER as {', '.join(same_label)} (cyan; chipless cables have no identity to compare): same cable → r or s · another → Enter", style="bold"))
                self.refresh_table()
                return
        hint = f"   SAME RECORD as {', '.join(same)} (highlighted): same cable again → s or r · another identical cable → Enter" if same else "   new record → Enter prints it"
        t = Text()
        t.append(f"{when}  run {runs}:  ", style="bold")
        t.append(f"{r['label_line1']}  /  {r['label_line2']}", style="bold yellow")
        t.append(hint)
        self.query_one("#reading", Static).update(t)
        self.refresh_table()

    # ----- the tester path -----

    @work(exclusive=True)
    async def capture(self) -> None:
        cmd = [self.s.km003c, "pd", "capture", "--raw", "--duration", str(int(self.hours * 3600))]
        try:
            self.proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        except FileNotFoundError:
            self.set_status(f"km003c not found ({self.s.km003c}): tester mode is off; modes 2 and 3 still work. See `cable-station doctor`.")
            return
        self.set_status(f"capture running for {self.hours:g} h")
        since = []
        loop = asyncio.get_running_loop()
        while True:
            raw = await self.proc.stdout.readline()
            if not raw:
                self.set_status("tester gone: waiting for it to come back on USB (plug its HID port into this computer)")
                while not mac_reader.tester_present():
                    await asyncio.sleep(3)
                await asyncio.sleep(2)
                self.proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
                self.set_status("tester back: capture running again")
                since = []
                continue
            line = raw.decode(errors="replace")
            since.append(line)
            if "** CONNECT **" in line:
                since = [line]
                continue
            if "RAW[" in line or line.startswith("      "):
                res = em.decode("".join(since[-40:]))
                if res and res[-1].get("cable_vdo"):
                    r = res[-1]
                    k = (r["cable_vdo"], r["vendor_id"], r["product_id"])
                    now = loop.time()
                    if k == self.last_key and now - self.last_mono < 3:
                        continue
                    if self.mode != "tester":
                        continue
                    runs = self.pending[2] + 1 if (self.pending and k == self.last_key) else 1
                    self.last_key, self.last_mono = k, now
                    self.pending = (r, f"{datetime.datetime.now():%H:%M:%S}", runs, list(since))
                    since = []
                    self.show_pending()
                    self.set_status(f"reading run {runs}: {r['label_line1']} / {r['label_line2']}")

    # ----- printing and recording -----

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        # Enter on a recorded row with nothing pending reprints that row; otherwise it prints the pending reading
        if self.pending is None:
            self.action_reprint()
        else:
            self.action_print_new()

    def _finish(self, cid, msg: str) -> None:
        self.pending = None
        self.previewed = False
        self.query_one("#reading", Static).update(f"{msg}  ·  next cable: seat it and run the eMarker module")
        self.refresh_table()

    def action_print_new(self) -> None:
        if not self.pending:
            self.action_reprint()
            return
        r, when, runs, lines = self.pending
        if not r.get("settled", True):
            self.set_status(f"port {r.get('port')} is still settling: nothing is added or printed until it has held one reading for {self.SETTLE_S} s")
            return
        cid = self.db.next_id()
        if not self.previewed:
            png, desc = self.printer.render(cid, r["label_line1"], r["label_line2"], r.get("label_note", ""))
            self.printer.open_preview(png)
            self.previewed = True
            self.query_one("#reading", Static).update(f"PREVIEW opened: {r['label_line1']} / {r['label_line2']} · #{cid[1:]}\n  {desc}\n  Enter again = add {cid} to the database and print · s = cancel")
            self.set_status(f"preview of {cid}: {desc}. Enter prints, s cancels.")
            return
        self.previewed = False
        if r.get("cable_vdo"):
            row = records.from_decode(r, cid, self.connector, "cable-station (Mac read)" if r.get("source") == "mac" else "cable-station (tester)")
            row["data_label"], row["speed"] = r["label_line1"], r["speed"]
            if r.get("data_test"):
                row["notes"] = r["data_test"]
        else:
            row = records.no_emarker_row(cid, self.connector, "")
            row["data_label"], row["speed"] = r["label_line1"], r["speed"]
            row["power_label"] = f"{r['label_line2']} · #{cid[1:]}"
            row["label_note"] = r.get("label_note", "")
            row["notes"] = f"Mac read: {r.get('data_test', '')}" if r.get("source") == "mac" else f"Data test: {r.get('data_test', '')}"
            if r.get("source") == "mac":
                row["emarker"], row["emarker_read"] = False, True     # the Mac asked on SOP' and nothing answered: verified chipless
            if r.get("product_type", "").startswith("e-marked"):
                row["emarker"], row["emarker_read"], row["active"] = True, False, bool(r.get("active"))
                row["current_a"], row["epr"] = "", ""     # unknown until a chip read
        self.db.write(row)
        if lines:
            (self.s.captures_dir / f"emarker-{cid}.log").write_text("".join(lines))
        self.set_status(f"[{cid}] PRINTED {r['label_line1']} / {r['label_line2']} · #{cid[1:]}   {self.printer.print(cid, r['label_line1'], r['label_line2'], r.get('label_note', ''))}")
        if r.get("port") is not None:
            self.last_print = (r["port"], cid, r["label_line1"], time.time())
        self._finish(cid, f"printed as {cid}")

    def action_reprint(self) -> None:
        t = self.query_one(DataTable)
        if t.row_count == 0:
            return
        row = t.get_row_at(t.cursor_row)
        cid = str(row[0]).split()[0]
        if cid.startswith("new?"):
            self.set_status("select a recorded row to reprint, or Enter to print the new reading")
            return
        line1, line2 = str(row[1]), str(row[2])
        rec = self.db.get(cid) or {}
        note = rec.get("label_note", "")
        self.set_status(f"[{cid}] REPRINTED {line1} / {line2} · #{cid[1:]}   {self.printer.print(cid, line1, line2, note)}")
        self._finish(cid, f"reprinted {cid}")

    # ----- the Mac path (modes 2 and 3) -----

    def show_mode(self) -> None:
        names = {"tester": "1 TESTER", "drive": "2 DRIVE", "dock": "3 DOCK", "lightning": "4 LIGHTNING"}
        bar = "   ".join((f"[reverse] {v} [/reverse]" if k == self.mode else f" {v} ") for k, v in names.items())
        auto = "[reverse] AUTO ON [/reverse]" if self.auto else " AUTO off "
        self.query_one("#mode", Static).update(f"MODE:  {bar}      connector: {self.connector}      {auto} (a)")

    def action_toggle_auto(self) -> None:
        """a: auto mode. A settled reading in drive, dock or lightning mode is added and printed without a key;
        a power-only verdict still waits for Enter (the Mac cannot tell a dead cable from a far end not yet plugged in)."""
        self.auto = not self.auto
        self.show_mode()
        note = " (tester mode: readings there still need Enter)" if self.mode == "tester" else ""
        self.set_status(f"auto mode {'ON: settled readings are added and printed by themselves; power-only verdicts still wait for Enter' if self.auto else 'off: Enter prints'}{note}")
        if self.auto and self.pending and self.pending[0].get("settled", True):
            self.auto_print()

    def auto_print(self) -> None:
        """Add and print the pending reading with no preview, when auto mode allows it."""
        r = self.pending[0] if self.pending else None
        if not r or not self.auto or not r.get("settled", True) or r.get("source") not in ("mac", "lightning"):
            return
        if r["label_line1"].startswith("PWR ONLY"):
            self.set_status(f"AUTO holds a power-only verdict: is the far end plugged in? Enter prints {r['label_line1']}, s discards")
            return
        self.previewed = True
        self.action_print_new()

    def set_mode(self, mode: str) -> None:
        self.mode = mode
        self.mac_seen = {}
        self.mac_first = {}
        if mode == "lightning" and "Lightning" not in self.connector:
            self.connector = "Lightning"
        if mode != "lightning" and "Lightning" in self.connector:
            self.connector = self.s.connector if "Lightning" not in self.s.connector else "USB-C to USB-C"
        self.show_mode()
        self.query_one("#reading", Static).update(f"{self.MODES[mode]}  ·  seat or plug a cable; the reading appears here")
        self.set_status(f"mode: {mode}")
        self.update_title()
        if mode != "tester" and not self._mac_watching:
            if sys.platform != "darwin":
                self.set_status("the Mac reader needs macOS (it reads ioreg); modes 2 and 3 do nothing here")
                return
            self._mac_watching = True
            self.mac_watch()

    def action_mode_tester(self) -> None:
        self.set_mode("tester")

    def action_mode_drive(self) -> None:
        self.set_mode("drive")

    def action_mode_dock(self) -> None:
        self.set_mode("dock")

    def action_mode_lightning(self) -> None:
        self.set_mode("lightning")

    def action_toggle_connector(self) -> None:
        if self.mode != "lightning":
            return
        cycle = ["Lightning", "USB-A to Lightning", "USB-C to Lightning"]
        self.connector = cycle[(cycle.index(self.connector) + 1) % 3] if self.connector in cycle else "Lightning"
        self.show_mode()
        self.set_status(f"connector: {self.connector} (c toggles)")

    def action_power_only(self) -> None:
        """p: in Lightning mode, the phone charges but never appears: a power-only Lightning cable."""
        if self.mode != "lightning":
            return
        rec = {"label_line1": "Lightning PWR ONLY", "label_line2": "USB-C PD" if "USB-C" in self.connector else "2.4A", "label_note": "",
               "current": "", "epr": False, "active": False, "vendor_id": "", "product_id": "", "cable_vdo": "", "product_type": "lightning cable",
               "speed": "none", "source": "lightning", "data_test": f"{self.connector}: the device charged but never enumerated on the Mac (operator)"}
        self.pending = (rec, f"{datetime.datetime.now():%H:%M:%S}", 1, [])
        self.show_pending()
        self.set_status("Lightning power-only staged. Enter prints, s discards.")

    def reading_from_ios(self, name: str, speed: str) -> None:
        if self.mode == "lightning" and "Lightning" not in self.connector:
            self.connector = "Lightning"
        rec = {"label_line1": "Lightning 480M", "label_line2": "USB-C PD" if "USB-C" in self.connector else "2.4A", "label_note": "",
               "current": "", "epr": False, "active": False, "vendor_id": "", "product_id": "", "cable_vdo": "", "product_type": "lightning cable",
               "speed": "480M", "source": "lightning", "data_test": f"{self.connector}: {name} enumerated at {speed}"}
        runs = self.pending[2] + 1 if (self.pending and self.pending[0].get("data_test") == rec["data_test"]) else 1
        self.pending = (rec, f"{datetime.datetime.now():%H:%M:%S}", runs, [])
        self.show_pending()
        self.set_status(f"lightning: {name} at {speed} → {rec['label_line1']} / {rec['label_line2']} ({self.connector}; c sets the other end's plug). Enter prints, s discards.")
        self.auto_print()

    def _watched(self, port: mac_reader.PortState) -> bool:
        names = (port.cio_device or "") + " " + (port.usb3_product or "") + " " + (port.usb2_product or "")
        partners = self.s.partners.get(self.mode, ())
        if port.connected and partners and any(k.upper() in names.upper() for k in partners):
            return True
        if port.connected and not partners and port.devices() != "nothing":
            return True   # no partner names configured: any device on the far end counts
        # a power-only (or dead-data) cable: the CC wire connected, nothing else; the drive on the far end never appears
        return port.connected and port.transports_active == ["CC"] and port.devices() == "nothing"

    @work(thread=True)
    def mac_watch(self) -> None:
        """Drive and dock modes: poll the Mac's ports; a new or changed cable on the watched partner becomes the pending reading.
        Lightning mode: poll the USB tree for an iPhone, iPad or iPod; its appearance is the reading."""

        def nap(seconds):
            end = time.time() + seconds
            while time.time() < end and not self._stop:
                time.sleep(0.1)

        while self.mode != "tester" and not self._stop:
            if self.mode == "lightning":
                try:
                    devs = {k: v for k, v in mac_reader.usb_devices().items() if any(x in v[0] for x in ("iPhone", "iPad", "iPod"))}
                except Exception:
                    devs = {}
                for k, v in devs.items():
                    if self.mac_seen.get(k) != v[:2]:
                        self.mac_seen[k] = v[:2]
                        self.call_from_thread(self.reading_from_ios, v[0], v[1])
                for k in [k for k in self.mac_seen if k not in devs]:
                    self.mac_seen.pop(k)
                nap(2)
                continue
            try:
                ports = mac_reader.read_ports()
            except Exception as e:
                self.call_from_thread(self.set_status, f"Mac read failed: {e}")
                nap(3)
                continue
            now = time.time()
            for p in ports.values():
                if not self._watched(p):
                    self.mac_seen.pop(p.port, None)
                    for k in [k for k in self.mac_first if k[0] == p.port]:
                        self.mac_first.pop(k)
                    continue
                sig = (p.devices(), p.link(), tuple(p.emarker.raw_vdos) if p.emarker else None)
                if self.mac_seen.get(p.port) == (sig, True):
                    continue
                left = self.settle_left(p.port, sig, now)
                if left:
                    if self.mac_seen.get(p.port) != (sig, False):
                        self.mac_seen[p.port] = (sig, False)
                        self.call_from_thread(self.reading_from_port, p, False)
                    self.call_from_thread(self.show_settling, p, left)
                    continue
                self.mac_seen[p.port] = (sig, True)
                self.call_from_thread(self.reading_from_port, p, True)
            nap(2)
        self._mac_watching = False

    def settle_left(self, port, sig, now: float) -> int:
        """Whole seconds until the (port, signature) reading counts as settled: SETTLE_S from the first time it was seen,
        0 once it has stood that long. A new signature on the port starts its own timer, so a link that trains in stages
        (USB 2 first, then USB 3 or Thunderbolt) is reported, and may be printed, only in its final state."""
        first = self.mac_first.setdefault((port, sig), now)
        return max(0, math.ceil(self.SETTLE_S - (now - first)))

    def show_settling(self, p: mac_reader.PortState, left: int) -> None:
        """The main box while a port's reading settles: the provisional verdict and the countdown; nothing can be printed yet."""
        if not self.pending or self.pending[0].get("settled", True) or self.pending[0].get("port") != p.port:
            return
        r = self.pending[0]
        what = "NO DATA YET: a dead cable, or the far end is not plugged in" if p.link()[0] == "none" else f"reads {r['label_line1']} / {r['label_line2']}"
        self.query_one("#reading", Static).update(Text(f"port {p.port}: SETTLING, {left} s · {what} · the link may still be training; nothing is added or printed until it settles", style="bold yellow"))

    def correction_for(self, port, label_line1: str, now: float):
        """The last print came from this port within CORRECTION_WINDOW_S and the port now reads a different label:
        return (cable id, old label, seconds since the print); the printed flag may be wrong. None otherwise."""
        lp = self.last_print
        if lp and lp[0] == port and now - lp[3] < self.CORRECTION_WINDOW_S and lp[2] != label_line1:
            return lp[1], lp[2], int(now - lp[3])
        return None

    def reading_from_port(self, p: mac_reader.PortState, settled: bool = True) -> None:
        """Stage the port's reading. Provisional (settled False) readings show but cannot be added or printed."""
        link_cls, link_txt = p.link()
        e = p.emarker
        if e and link_cls == "none":
            # the chip answers but no data link trained, not even USB 2.0: power and CC work, the data wires do not
            claim1, claim2 = e.label_lines()
            rec = {"label_line1": "PWR ONLY · no data", "label_line2": claim2, "label_note": "data wires failed", "current": f"{e.current_a}A", "epr": e.epr,
                   "active": e.kind == "active", "vendor_id": f"0x{e.vendor_id:04X}", "product_id": f"0x{e.product_id:04X}", "cable_vdo": f"0x{e.cable_vdo:08X}",
                   "product_type": f"{e.kind} cable", "speed": "none (chip claims " + claim1 + ")", "source": "mac",
                   "data_test": f"Mac read on port {p.port}: chip answered on SOP' and claims {claim1} / {claim2}, but no data link trained with {p.devices() if p.devices() != 'nothing' else 'the partner'} (power and CC only): data wires failed"}
        elif e:
            line1, line2 = e.label_lines()
            if link_cls in ("tb40", "tb20") or (p.tb_speed and "80" in p.tb_speed):
                # Thunderbolt: TB3-era chips report a USB 10G/20G code while the link trains at 40G; USB4-generation chips are TB4; 80G is TB5 (inferred from the specifications' history)
                gen = "TB5" if (p.tb_speed and "80" in p.tb_speed) else ("TB4" if e.speed_code >= 3 else "TB3")
                rate = "80G" if gen == "TB5" else ("40G" if link_cls == "tb40" else "20G")
                line1 = f"{gen} ⚡ {rate} · USB 3.2 10G" + (" Active" if e.kind == "active" else "")
            rec = {"label_line1": line1, "label_line2": line2, "label_note": "", "current": f"{e.current_a}A", "epr": e.epr, "active": e.kind == "active",
                   "vendor_id": f"0x{e.vendor_id:04X}", "product_id": f"0x{e.product_id:04X}", "cable_vdo": f"0x{e.cable_vdo:08X}",
                   "product_type": f"{e.kind} cable", "speed": line1, "source": "mac",
                   "data_test": f"Mac read on port {p.port}: chip answered on SOP' ({', '.join(e.raw_vdos)}); link trained {link_txt} with {p.devices()}"}
        else:
            t = {"usb2": "USB 2.0 480M", "usb5": "USB 3.2 5G", "usb10": "USB 3.2 10G", "tb20": "USB4 20G", "tb40": "USB4 40G"}.get(link_cls, link_txt)
            rec = {"label_line1": f"no eMarker · {t}" if link_cls != "none" else "PWR ONLY · no data", "label_line2": "60W 3A", "label_note": "",
                   "current": "3A", "epr": False, "active": False, "vendor_id": "", "product_id": "", "cable_vdo": "", "product_type": "chipless cable",
                   "speed": t, "source": "mac", "data_test": f"Mac read on port {p.port}: no chip answered on SOP'; link trained {link_txt} with {p.devices()}"}
        runs = self.pending[2] + 1 if (self.pending and self.pending[0].get("data_test") == rec["data_test"]) else 1
        rec["port"], rec["settled"] = p.port, settled
        self.pending = (rec, f"{datetime.datetime.now():%H:%M:%S}", runs, [])
        self.show_pending()
        if not settled:
            self.set_status(f"{self.mode} mode, port {p.port}: {rec['label_line1']} / {rec['label_line2']}, settling")
            return
        corr = self.correction_for(p.port, rec["label_line1"], time.time())
        if corr:
            cid, old, ago = corr
            self.query_one("#reading", Static).update(Text(
                f"CORRECTION? {cid} printed {ago} s ago from this port as '{old}'; the port now reads '{rec['label_line1']}'. "
                f"If it is the same cable: highlight {cid} and press w twice to fix it and reprint.", style="bold red"))
            self.set_status(f"port {p.port} changed after {cid} was printed: w to correct it, or Enter if this is a different cable")
            return
        if link_cls == "none":
            # the hedge is for the operator, never for the label: the Mac cannot tell a dead cable from a far end not yet plugged in
            self.set_status(f"port {p.port}: {rec['label_line1']}, nothing enumerated in {self.SETTLE_S} s. Is the far end plugged in? Enter prints it as power only, s discards.")
        else:
            self.set_status(f"{self.mode} mode, port {p.port}: {rec['label_line1']} / {rec['label_line2']}. Enter prints, w writes into the highlighted row, s discards.")
        self.auto_print()

    # ----- the other keys -----

    def on_key(self, event) -> None:
        if event.key != "x":
            self.confirm_x = None
        if event.key != "w":
            self.confirm_w = None

    def action_no_emarker(self) -> None:
        """Stage a chipless, untested cable as the pending reading; Enter prints it (never prints by itself)."""
        rec = {"label_line1": "no eMarker · USB 2.0 480M", "label_line2": "60W 3A", "current": "3A", "epr": False, "active": False,
               "vendor_id": "", "product_id": "", "cable_vdo": "", "product_type": "chipless cable", "speed": "480M (assumed, untested)",
               "data_test": "none: recorded as untested chipless"}
        self.pending = (rec, f"{datetime.datetime.now():%H:%M:%S}", 1, [])
        self.show_pending()
        self.set_status("staged an untested chipless cable (480M assumed). Enter prints it, s discards.")

    def _highlighted_id(self):
        t = self.query_one(DataTable)
        if t.row_count == 0:
            return None
        cid = str(t.get_row_at(t.cursor_row)[0]).split()[0]
        return None if cid.startswith("new?") else cid

    def action_decommission(self) -> None:
        cid = self._highlighted_id()
        if not cid:
            self.set_status("highlight a recorded cable first (↑↓)")
            return
        if self.confirm_x != cid:
            self.confirm_x = cid
            self.set_status(f"decommission {cid} (broken or discarded)? press x again to confirm, anything else cancels")
            return
        self.confirm_x = None
        self.db.set_status(cid, "decommissioned")
        self.set_status(f"[{cid}] DECOMMISSIONED {datetime.date.today().isoformat()}; the record and number are kept")
        self.refresh_table()

    def action_reactivate(self) -> None:
        cid = self._highlighted_id()
        if not cid:
            return
        self.db.set_status(cid, "active")
        self.set_status(f"[{cid}] back in service")
        self.refresh_table()

    def action_write_into(self) -> None:
        """w: write the pending reading into the highlighted row (a retest keeps its number), then reprint."""
        if not self.pending:
            self.set_status("nothing pending to write")
            return
        if not self.pending[0].get("settled", True):
            self.set_status(f"port {self.pending[0].get('port')} is still settling: nothing is written until it has held one reading for {self.SETTLE_S} s")
            return
        cid = self._highlighted_id()
        if not cid:
            self.set_status("highlight the row to update (↑↓), then w")
            return
        if self.confirm_w != cid:
            self.confirm_w = cid
            self.set_status(f"update {cid} with this reading (it keeps #{cid[1:]}) and reprint its flag? press w again to confirm")
            return
        self.confirm_w = None
        r = self.pending[0]
        fields = {"data_label": r["label_line1"], "power_label": r["label_line2"], "speed": r["speed"], "active": bool(r.get("active")),
                  "label_note": r.get("label_note", ""), "tested": datetime.date.today().isoformat(), "notes": r.get("data_test", "")}
        if r.get("cable_vdo"):
            fields.update({"emarker": True, "emarker_read": True, "current_a": (r["current"] or "")[:-1], "epr": bool(r["epr"]),
                           "vendor": r["vendor_id"], "product": r["product_id"], "cable_vdo": r["cable_vdo"]})
        elif r.get("source") == "mac":
            fields.update({"emarker": False, "emarker_read": True, "current_a": "3", "epr": False, "vendor": "", "product": "", "cable_vdo": ""})
        self.db.update(cid, fields)
        self.set_status(f"[{cid}] UPDATED and REPRINTED {r['label_line1']} / {r['label_line2']} · #{cid[1:]}   {self.printer.print(cid, r['label_line1'], r['label_line2'], r.get('label_note', ''))}")
        self._finish(cid, f"{cid} updated with the new reading")

    def action_discard(self) -> None:
        self.set_status("reading discarded")
        self._finish(None, "discarded")

    async def action_quit(self) -> None:
        self._stop = True
        self.mode = "tester"          # ends the Mac-watch thread's loop
        if self.proc and self.proc.returncode is None:
            self.proc.terminate()
        self.workers.cancel_all()
        self.exit()
