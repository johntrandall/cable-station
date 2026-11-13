# Changelog

## 0.1.2 (2026-11-13)

- Station: a Mac reading (drive and dock modes) is not added or printed until the port has held one reading for 8 s. It shows at once, marked SETTLING with a countdown; `Enter` and `w` are refused meanwhile, and a change on the port restarts the clock. Before, only the no-link verdict waited, so a link still training to USB 3 or Thunderbolt could be printed as USB 2.
- Station: the hedge "confirm the drive is on the far end" no longer prints on a label. A chipless power-only verdict puts the question in the status line instead; `label_note` holds only facts about the cable.
- Station: auto mode (`a`, shown in the mode bar). On, a settled reading in drive, dock or lightning mode is added to the database and printed with no key pressed; a power-only verdict still waits for `Enter`. Off by default.
- Station: the footer shows short names with a tooltip on hover for each key; the mode keys 1 to 4 are in the mode bar only.

## 0.1.1 (2026-11-12)

- Flag: the drawn Thunderbolt bolt is clamped to the text's ink height, so no ink leaves the band the printer can reach after its vertical offset.
- Station (drive and dock modes): a port with no data link is not called power only until that state has stood for 8 s; meanwhile the main box says NO DATA YET with a countdown, since links train within a few seconds.
- Station: when a port reports a different label within 2 minutes of printing a cable from that port, the main box shows a CORRECTION? notice naming the printed id, so the wrong flag can be fixed with w and reprinted.

## 0.1.0 (2026-11-12)

First release. Merges two earlier codebases into one package: a Mac-side reader of cable e-markers through the port registry, and a Textual station around the POWER-Z KM003C tester.

- `cable-station` (the station): modes 1 tester, 2 drive, 3 dock, 4 lightning; a mode bar; preview before print; Enter, r, n, w, x, u, s, c, p keys; a highlighted table of every recorded cable.
- Thunderbolt labels TB3, TB4, and TB5 with a drawn bolt; a chip that answers with no data link reads as `PWR ONLY · no data` (data wires failed).
- Marked BETA, untested in the title, the main box, and the README.
- `cable-station snapshot [--json]`: every USB-C port's chip, link, and partner (macOS).
- `cable-station decode LOG`: the cable's e-marker from a `km003c pd capture --raw` log.
- `cable-station print ID`: reprint a recorded cable's flag.
- `cable-station doctor`: check the tools and folders.
- Records as Markdown notes with frontmatter plus a generated Obsidian Base.
- Settings from `~/.config/cable-station/config.toml` and `CABLE_STATION_*` environment variables.
- The read-only throughput test is kept as a module, off by default (`snapshot --read-test VOLUME`).
