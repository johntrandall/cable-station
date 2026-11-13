---
verdict: pass
sha: 61f9c57d842759f055754f428a7bec79be406777
looked_at: the station's main screen with auto mode on and a settling reading (screens/settling-auto-on.png), rendered by Textual's run_test; I also rendered it myself (140x24, Chrome headless screenshot of app.export_screenshot())
screenshot: dev-docs/runs/build-2026-11-13-0.1.2/screens/settling-auto-on.png
---

# GUI verdict: build 0.1.2

I read the lead designer's screenshot and then rendered the same state myself (drive mode, auto on, port 2 reading no eMarker · USB 2.0 480M, settled False, countdown 5 s); the two agree. The mode bar shows 1 TESTER, 2 DRIVE (reversed), 3 DOCK, 4 LIGHTNING, the connector, and AUTO ON (a). The main box is a yellow bordered line: "port 2: SETTLING, 5 s · reads no eMarker · USB 2.0 480M / 60W 3A · the link may still be training; nothing is added or printed until it settles". The status line says "settling". The table holds one pending row, "new? (#1)", with no eMarker · USB 2.0 480M. The footer reads ⏎ print, a auto, r reprint, n no chip, w update, x retire, s discard, q quit, then the palette hint, and shows none of keys 1 to 4. In my render, pressing Enter while settling added nothing to the database (0 rows). Not looked at: the hover tooltip itself (footer-tooltip.png exists but I did not open it; the tooltip text is checked in station.py).
