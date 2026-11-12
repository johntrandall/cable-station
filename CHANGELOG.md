# Changelog

## 0.1.0 (2026-11-12)

First release. Merges two earlier codebases into one package: a Mac-side reader of cable e-markers through the port registry, and a Textual station around the POWER-Z KM003C tester.

- `cable-station` (the station): modes 1 tester, 2 drive, 3 dock; preview before print; Enter, r, n, w, x, u, s keys; a highlighted table of every recorded cable.
- `cable-station snapshot [--json]`: every USB-C port's chip, link, and partner (macOS).
- `cable-station decode LOG`: the cable's e-marker from a `km003c pd capture --raw` log.
- `cable-station print ID`: reprint a recorded cable's flag.
- `cable-station doctor`: check the tools and folders.
- Records as Markdown notes with frontmatter plus a generated Obsidian Base.
- Settings from `~/.config/cable-station/config.toml` and `CABLE_STATION_*` environment variables.
- The read-only throughput test is kept as a module, off by default (`snapshot --read-test VOLUME`).
