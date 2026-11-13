# cable-station

**BETA, untested.** Version 0.1.0 is the first public packaging of a tool that has run on one machine; expect rough edges, and check the first few labels by hand.

Read what a USB-C cable can really do, keep one note per cable, and print a small flag that says so.

**Start here.** `cable-station` is a terminal program for sorting a drawer of USB-C cables. Every full-featured USB-C cable carries an **e-marker**, a chip that states the cable's ratings: how many amps it may carry, whether it supports 240 W Extended Power Range (EPR), which data speed it is wired for, and whether it is passive or active. The station reads that chip in one of two ways, records the result as a Markdown note, and prints a two-line wrap-flag label on a Brother P-touch so the answer travels with the cable. It was built around the ChargerLAB POWER-Z KM003C, a USB-C power and Power Delivery tester, and it also works with nothing but an Apple Silicon Mac.

## In plain terms

You have twenty black USB-C cables and no idea which one charges the laptop at full speed, which one is safe for the fast drive, and which one is a phone-charging cable that only does USB 2.0. Cables do not say. This program asks the chip inside each cable, writes down the answer, and prints a label such as `USB4 20G · USB 3.2 10G` over `100W 5A · #17` that you wrap around the cable.

- **One pass, labelled for good:** seat each cable once, press Enter, and the cable comes out of the drawer with a flag.
- **The answer comes from the cable itself:** the ratings are read from the e-marker chip, not guessed from the plug or the brand.
- **Every cable gets a number:** `#17` on the flag matches note `C17.md`, so a cable can be retested, retired, or found again.
- **Your records stay yours:** the notes are plain Markdown files in a folder you choose, readable in any editor and as a table in Obsidian.

## What it does

The station shows one table: the pending reading on top, every recorded cable below, and the rows whose chip identity matches the pending reading highlighted. Pressing Enter opens a preview of the flag; pressing Enter again prints it and writes the note. Two paths feed the pending reading:

1. **Tester path (primary).** The POWER-Z KM003C sits on USB with the cable under test seated in its socket. You run the tester's `USB-C eMarker` module (Application › Modules › USB-C eMarker); the station runs `km003c pd capture --raw` in the background, catches the cable's Discover Identity answer on the cable channel (SOP'), and decodes the ID Header and Cable VDO per the USB Power Delivery specification.
2. **Mac path.** On macOS, the Mac's own port controller asks the cable the same question when a device is plugged in through it. `cable-station` reads the answer from the I/O Registry (`Port-USB-C@N / CC / SOP'`) together with the link that trained (USB 2, USB 3, Thunderbolt or USB4) and the device on the far end. Modes 2 (drive) and 3 (dock) watch the ports for a partner device you name in the config.

A cable with no chip is, by the USB-C specification, a 3 A, 60 W, USB 2.0 cable, and the label says so. A cable that connects but never carries data is labelled `PWR ONLY · no data`; when its chip still answers, the note records the claim and says the data wires failed.

## Install

```bash
uv tool install cable-station
```

or, on macOS with Homebrew:

```bash
brew install johntrandall/tap/cable-station
```

Python 3.11 or newer, Textual 8 and Pillow are the only Python requirements. Two optional tools unlock the two optional features:

- **Tester path:** the `km003c` CLI from [okhsunrog/km003c-rs](https://github.com/okhsunrog/km003c-rs) (MIT or Apache-2.0). Build it with `cargo build --release -p km003c-cli` in a clone of that repository and put the binary on your PATH, or set `km003c = "/path/to/km003c"` in the config. The pull request [km003c-rs #67](https://github.com/okhsunrog/km003c-rs/pull/67) adds a `km003c cable` command that reads the e-marker directly; until it lands, the station uses the capture route described above.
- **Printing:** [`ptouch-label`](https://github.com/johntrandall/ptouch-label), which drives Brother PT-P750W and PT-P950NW printers over the network: `uv tool install git+https://github.com/johntrandall/ptouch-label`. Without it, the station still renders every flag as a PNG in its state folder.

`cable-station doctor` tells you which of these it can see.

## Quick start

```bash
cable-station doctor          # what is installed, where the records go
cable-station                 # the station (mode 1, tester)
cable-station snapshot        # macOS: every USB-C port's chip, link, and partner, right now
cable-station decode capture.log   # the e-marker from a saved `km003c pd capture --raw` log
cable-station print 17        # reprint cable #17's flag
```

A `snapshot` on a Mac with a dock on port 3 looks like this:

```text
port 1: connected True · nothing · link DisplayPort 8.1 Gbps (HBR3) · no e-marker answered
port 2: connected False · nothing · link no link · no e-marker answered
port 3: connected True · TS5 Plus / USB3 HUB · link Thunderbolt/USB4 40 Gb/s · chip vendor 0x2B1D product 0x192B passive ('USB4 20G · USB 3.2 10G', '240W 5A EPR') VDO 0x420A4E42
```

## The keys

| Key | What it does |
|---|---|
| `Enter` | Preview the pending reading's flag; `Enter` again prints it with a new number and writes the note. With nothing pending, reprints the highlighted row. Refused while a Mac reading is still settling (below). |
| `a` | Auto mode on or off. On, a settled reading in drive, dock or lightning mode is added and printed by itself: you touch only cables and labels. A power-only verdict still waits for `Enter`, because the Mac cannot tell a dead cable from a far end that is not plugged in yet. |
| `r` | Reprint the highlighted cable's flag (no new note). |
| `1` `2` `3` `4` | Mode (shown in the mode bar, not the footer): `1` tester (readings come from the POWER-Z capture), `2` drive, `3` dock (the Mac reads the cable plugged between it and the named partner), `4` lightning (an iPhone or iPad enumerating on the Mac is the reading). |
| `c` `p` | In lightning mode: `c` cycles the other end's plug (Lightning, USB-A to Lightning, USB-C to Lightning); `p` stages a power-only Lightning cable. |
| `n` | Stage the seated cable as chipless and untested (`no eMarker · USB 2.0 480M` over `60W 3A`); `Enter` prints it. |
| `w` | Write the pending reading into the highlighted row, a retest that keeps the number; press `w` twice. |
| `x` | Decommission the highlighted cable (broken or discarded); the record and number are kept; press `x` twice. `u` undoes it. |
| `s` | Discard the pending reading. |
| `q` | Quit; the capture stops with the station. |

The footer shows each key with a short name; hovering a key shows what it does.

Green rows share the pending reading's chip identity (vendor, product, cable VDO): the same cable again, or an identical one. Cyan rows are chipless cables of the same speed tier, which have no identity to compare.

## The label

Two lines on 9 mm tape, printed twice on one strip with a 20 mm wrap zone and a dotted fold line between, so both faces of the flag read the same.

| Line | Content | Examples |
|---|---|---|
| 1, data | Every mode the cable supports, highest first, separated by a middle dot, then `Active` on an active cable; a Thunderbolt link trained on the Mac names the generation with a bolt | `USB 2.0 480M` · `USB 3.2 5G` · `USB4 20G · USB 3.2 10G` · `USB4 ≥40G · USB 3.2 10G Active` · `TB4 ⚡ 40G · USB 3.2 10G` |
| 2, power | Watts, amps, `EPR` on 240 W cables, then the cable's number | `60W 3A · #3` · `100W 5A · #17` · `240W 5A EPR · #21` |
| no chip | Line 1 names the fact and the tested data speed; line 2 the specification default | `no eMarker · USB 2.0 480M` / `60W 3A · #8` |
| power only | A cable that charges but never carries data | `PWR ONLY · no data` / `60W 3A · #9` |

`≥40G` means the chip's speed code says USB4 Gen 3: verified to 40G and possibly higher, until an 80G cable has been read on this firmware. Watts come first because that is the question at the drawer; amps second because chargers and docks talk in amps. Nothing else goes on the flag: a missing marker means passive and not EPR.

## The data layout

Records live in the data folder (default `~/cable-station/cables`), one Markdown note per cable named `C<N>.md`. The frontmatter holds the fields; the body is free text.

```markdown
---
type: cable
id: C17
tested: 2026-11-12
connector: USB-C to USB-C
data_label: "USB4 20G · USB 3.2 10G"
power_label: "100W 5A · #17"
current_a: 5
epr: false
speed: "USB4 20G · USB 3.2 10G"
active: false
emarker: true
emarker_read: true
vendor: 0x2B1D
product: 0x192B
cable_vdo: 0x00084042
status: active
---

# C17 · USB4 20G · USB 3.2 10G · 100W 5A · #17
```

Beside the notes the station keeps `_cables.base`, an [Obsidian Base](https://help.obsidian.md/bases) that shows the folder as a table (view `1 · CABLES`). Point an Obsidian vault at the folder, or make the folder part of one. The station's own files (the capture log, each cable's raw capture, the rendered flag PNGs) go to the state folder, default `~/.local/state/cable-station`, and are not records.

## Configuration

Settings come from `~/.config/cable-station/config.toml`, overridden by `CABLE_STATION_*` environment variables. Every key is optional.

```toml
data_dir = "~/cable-station/cables"        # the records (CABLE_STATION_DATA)
state_dir = "~/.local/state/cable-station"  # logs, captures, previews (CABLE_STATION_STATE)
printer_model = "PT-P950NW"                 # ptouch-label --model (CABLE_STATION_PRINTER)
tape_mm = 9                                 # 6, 9, 12, 18 or 24 (CABLE_STATION_TAPE)
km003c = "km003c"                           # the tester CLI (CABLE_STATION_KM003C)
capture_hours = 3                           # one capture run before it restarts
connector = "USB-C to USB-C"                # recorded on new cables
vertical_offset_mm = 1.45                   # your printer's vertical calibration offset

[partners]
drive = ["Envoy", "Sabrent"]                # mode 2 watches ports where one of these appears (CABLE_STATION_DRIVE_PARTNERS)
dock = ["TS5"]                              # mode 3 (CABLE_STATION_DOCK_PARTNERS)
```

Partner names are matched against what macOS reports for the device on the far end of the cable. With no partners configured, modes 2 and 3 watch every port that gains a device.

**Settling.** A USB-C link trains in stages: USB 2 first, then USB 3 or Thunderbolt a few seconds later, and a port with nothing on the far end looks the same as a dead cable for a while. So a Mac reading shows at once, marked SETTLING with a countdown, but nothing is added to the database or printed until the port has held one reading for 8 s; a change on the port restarts the clock. A power-only verdict (`PWR ONLY · no data`) is always staged for `Enter`, with the question in the status line (is the far end plugged in?), never on the label.

## Limits

- **No throughput test yet.** A read-only "real work" test through the cable exists as a module (`cable-station snapshot --read-test VOLUME`) but is experimental and does not feed the label; its floors are provisional.
- **No power test yet.** The label's watts are what the chip claims. A worn cable still claims its rating; a voltage-drop test under load is planned, not built.
- **The Mac reader is macOS only.** It reads the I/O Registry. On Linux the tester path, the records, and printing all work.
- **The tester's eMarker module is a button press.** The KM003C sends the Discover Identity only while its `USB-C eMarker` screen is open, so each cable is one hands-on step on the tester. The vendor's serial protocol-trigger route does not reach the cable in the socket; a direct read is the subject of km003c-rs pull request #67.
- **Chipless does not mean USB 2.0.** Only the tester proves "no e-marker"; the Mac proves the link that trained. A Mac-only reading of a 20G or faster link proves a chip exists and is recorded as `emarker_read: false` until the tester reads it.
- **Verified on one machine.** The PD 2.0 versus 3.x layout of the cable VDO is chosen from ioreg's `Specification Revision`; checked on an M3 Max MacBook Pro running macOS 15, not against every Mac.

## Status

Beta, untested beyond one machine. The station has labelled one household's cable drawer; the vocabulary and keys are settled, the packaging is new. Next: the direct `km003c cable` read once km003c-rs #67 lands, a power test, and the throughput test as an opt-in.

## Credits

- [ChargerLAB POWER-Z KM003C](https://www.chargerlab.com/km003c-km002c-technical-support), the tester.
- [okhsunrog/km003c-rs](https://github.com/okhsunrog/km003c-rs) (MIT or Apache-2.0), the open-source driver and CLI for the tester, and [okhsunrog/km003c-protocol-research](https://github.com/okhsunrog/km003c-protocol-research), the protocol reference.
- [ptouch-label](https://github.com/johntrandall/ptouch-label), the P-touch printing tool.
- [Textual](https://textual.textualize.io/) for the terminal interface and [Pillow](https://python-pillow.org/) for the flag renderer.

## Contributing

Issues and pull requests at [github.com/johntrandall/cable-station](https://github.com/johntrandall/cable-station/issues). A capture log from a cable the decoder gets wrong is the most useful bug report: `km003c pd capture --raw --duration 60 > capture.log` while you open the tester's eMarker module, then attach the log.

## License

[MIT](https://github.com/johntrandall/cable-station/blob/main/LICENSE), John Randall.
