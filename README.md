# cable-station

**Start here.** `cable-station` tests USB-C cables on an Apple Silicon Mac and prints a wrap-flag label for each one on the P-touch. It replaces menu-driving the POWER-Z KM003C for the common question "what is this cable?". Built 2026-11-11 on SusanBones (MacBook Pro, M3 Max). Terms: an **e-marker** is the small chip inside many USB-C cables that states the cable's ratings; macOS reads it over the USB Power Delivery (PD) wire, where the cable answers as **SOP'** ("SOP prime"). A **wrap-flag** is a label printed twice with a blank middle that wraps around the cable so both faces read.

## How to run it

```bash
cable-station                 # interactive: plug, read, print, eject, unplug, repeat
cable-station --snapshot      # what every Mac USB-C port sees right now
cable-station --snapshot --json   # same, for agents
cable-station --self-test     # decoder check against a known cable
```

Setup: one cable end in **Mac USB-C port 2** (the free one on SusanBones), the other end in the partner drive, by default the OWC Envoy Pro FX **Razor Crest** (volume `RazorCrest`). Move Razor Crest off the dock first (eject it). The station ejects Razor Crest after each test and tells you when to unplug. Labels print on Iris (PT-P950NW, 9 mm tape) unless `--model` says otherwise. Results append to `~/.local/share/cable-station/results.jsonl`; flag images go to `~/.local/share/cable-station/flags/`.

USB-A to USB-C cables: the Mac has no USB-A port, so this layout does not test them yet (plan: A end into a TS5 Plus USB-A port, C end into the Envoy, and read the Envoy's USB speed from the USB tree).

## What it measures, in order of trust

| Layer | Source | What it proves |
|---|---|---|
| 1. Claims | e-marker via IORegistry `Port-USB-C@N/CC/SOP'` VDOs | What the cable says it can do: speed, current, max voltage (EPR = 240 W), length class, vendor. |
| 2. Negotiated link | IORegistry `CIO`, `USB3`, `USB2` transports + `system_profiler SPThunderboltDataType` | The link actually trained at that speed through this cable. Marginal cables train down (40G → 20G, 10G → 5G). |
| 3. Real data | Read-only read of existing large files on the partner, page cache bypassed (`F_NOCACHE`) | The cable moves data at the speed of the link, without errors and retries slowing it. |

The label is built from layer 2, checked by layer 3. Layer 1 only contributes the power suffix (`+ 240W`), and the screen says that part is claimed, not measured. When the chip claims more than the link reached, the screen says "the chip overclaims or the cable is damaged" and the label shows what was measured.

Throughput floors (provisional, for the Envoy Pro FX): Thunderbolt 40G ≥ 1500 MB/s, 20G ≥ 900, USB 10G ≥ 600, 5G ≥ 300, USB 2 ≥ 25. Observed 2026-11-11: about 790 MB/s through the TS5 Plus dock's 10 Gb/s USB path.

## Limits

- **No e-marker does not mean no data.** USB 2.0 USB-C cables and every USB-A to USB-C cable normally have no chip. The link test still labels them.
- **The partner sets the ceiling.** Razor Crest is Thunderbolt 3, so nothing above 40G is verified, and Apple Silicon does not support USB 20 Gb/s (Gen 2x2) at all. An 80G (Thunderbolt 5) cable is labelled 40G-verified with the 80G claim noted.
- **Power is not measured yet.** See below.
- **Dead CC wire:** a cable whose CC wire is broken never connects at all. Press Enter at the plug prompt and the station records it as dead.
- The PD 2.0 vs 3.x layout of the cable VDO is chosen from ioreg's `Specification Revision` (>= 3 treated as PD 3.x). That mapping is Observed on one M3 cable, not checked against the spec text.

## Power test (planned, not built)

The Mac reports its own input voltage and current (`ioreg -rn AppleSmartBattery` → `PowerTelemetryData.SystemVoltageIn` / `SystemCurrentIn`) and the negotiated contract (`AdapterDetails`: watts, voltage). With the cable between a charger and the Mac, swinging the Mac's load (a CPU burn) and taking ΔV/ΔI gives the loop resistance; subtracting a known-good reference cable leaves the cable's own resistance. A genuine 5 A cable must drop under 0.75 V across VBUS and ground at 5 A (USB-C spec: ≤ 500 mV VBUS, ≤ 250 mV ground), so about 0.15 Ω; a 3 A cable about 0.25 Ω. A cheap cable whose chip claims 5 A shows up as too much resistance. The KM003C at the charger end, read over its USB data port, would replace the slope trick with a direct voltage reading. Untested; the dock also powers the Mac and may need unplugging during a power test.
