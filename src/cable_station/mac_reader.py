"""Read a USB-C cable's e-marker and trained link from the Mac's own port registry (macOS only).

The Mac's port controller runs the PD Discover Identity itself and macOS exposes the cable's VDOs under
`Port-USB-C@N / CC / SOP'` (IOObjectClass IOPortTransportComponentCCUSBPDSOPp). So with a partner device
on the far end, the Mac reads the chip the way the tester does, and also reports the link that trained
(USB2, USB3, CIO/Thunderbolt). Verified on an M3 Max MacBook Pro running macOS 15.

API: read_ports() -> {port_number: PortState}; parse_ports(plist_bytes) does the same from a saved
`ioreg -a -l -r -n Port-USB-C` plist (used by the tests). PortState.emarker is an EMarker or None (no chip
answered on SOP'); PortState.link() -> (class, label) for the trained link.
"""
from __future__ import annotations

import json
import plistlib
import subprocess
from dataclasses import dataclass, field

SPEED_LABEL = {0: "USB 2.0 480M", 1: "USB 3.2 5G", 2: "USB4 20G · USB 3.2 10G", 3: "USB4 ≥40G · USB 3.2 10G", 4: "USB4 80G · USB 3.2 10G"}
LATENCY_M = {1: "~1 m", 2: "~2 m", 3: "~3 m", 4: "~4 m", 5: "~5 m", 6: "~6 m", 7: "~7 m", 8: ">7 m"}
MAX_VBUS_V = {0: 20, 1: 30, 2: 40, 3: 50}


@dataclass
class EMarker:
    vendor_id: int
    product_id: int
    xid: int
    kind: str                 # passive | active | other
    speed_code: int
    current_a: int
    max_vbus_v: int | None
    epr: bool
    length: str
    cable_vdo: int
    raw_vdos: list[str]

    @property
    def watts(self) -> int:
        return 240 if (self.epr and self.current_a >= 5) else 20 * self.current_a

    def label_lines(self) -> tuple[str, str]:
        line1 = SPEED_LABEL.get(self.speed_code, f"speed code {self.speed_code}") + (" Active" if self.kind == "active" else "")
        line2 = f"{self.watts}W {self.current_a}A" + (" EPR" if self.epr else "")
        return line1, line2

    def as_reading(self) -> dict:
        """The same dict shape tester_capture.decode() returns, so records.from_decode() takes either."""
        line1, line2 = self.label_lines()
        return {"product_type": f"{self.kind} cable", "vendor_id": f"0x{self.vendor_id:04X}", "xid": f"0x{self.xid:08X}",
                "product_id": f"0x{self.product_id:04X}", "cable_vdo": f"0x{self.cable_vdo:08X}", "speed": SPEED_LABEL.get(self.speed_code, f"speed code {self.speed_code}"),
                "current": f"{self.current_a}A", "max_vbus": f"{self.max_vbus_v}V" if self.max_vbus_v else "", "epr": self.epr,
                "active": self.kind == "active", "label_line1": line1, "label_line2": line2}


def decode_emarker(meta: dict, spec_revision: int | None) -> EMarker | None:
    vdos = [int.from_bytes(b, "little") for b in meta.get("VDOs", [])]
    if len(vdos) < 4:
        return None
    id_header, cert, product, cable = vdos[0], vdos[1], vdos[2], vdos[3]
    kind = {3: "passive", 4: "active"}.get((id_header >> 27) & 7, "other")
    pd3 = (spec_revision or 0) >= 3
    return EMarker(vendor_id=id_header & 0xFFFF, product_id=(product >> 16) & 0xFFFF, xid=cert, kind=kind,
                   speed_code=cable & 7, current_a={1: 3, 2: 5}.get((cable >> 5) & 3, 3),
                   max_vbus_v=MAX_VBUS_V[(cable >> 9) & 3] if pd3 else None,
                   epr=bool((cable >> 17) & 1) if pd3 else False,   # PD 3.1 passive cable VDO bit 17, EPR Mode Capable
                   length=LATENCY_M.get((cable >> 13) & 0xF, "?"), cable_vdo=cable, raw_vdos=[f"0x{v:08x}" for v in vdos])


@dataclass
class PortState:
    port: int
    connected: bool = False
    transports_active: list = field(default_factory=list)
    partner_vid: int | None = None
    emarker: EMarker | None = None
    usb2_rate: str | None = None
    usb2_product: str | None = None
    usb3_rate: str | None = None
    usb3_product: str | None = None
    cio_active: bool = False
    cio_device: str | None = None
    cio_cable_speed: int | None = None
    tb_speed: str | None = None
    dp_rate: str | None = None

    def devices(self) -> str:
        return " / ".join(x for x in (self.cio_device, self.usb3_product, self.usb2_product) if x) or "nothing"

    def link(self) -> tuple[str, str]:
        """(class, text) of the link that trained through this cable."""
        if self.cio_active:
            g = (self.tb_speed or "").replace("Up to ", "")
            cls = "tb40" if "40" in g else ("tb20" if "20" in g else "tb")
            return cls, f"Thunderbolt/USB4 {g or 'link'}"
        if self.usb3_rate:
            return ("usb10" if "10" in self.usb3_rate else "usb5"), f"USB3 {self.usb3_rate}"
        if self.usb2_rate:
            return "usb2", f"USB2 {self.usb2_rate}"
        if self.dp_rate:
            return "dp", f"DisplayPort {self.dp_rate}"
        return "none", "no link"

    def summary(self) -> str:
        e = self.emarker
        chip = (f"chip vendor 0x{e.vendor_id:04X} product 0x{e.product_id:04X} {e.kind} {e.label_lines()} VDO 0x{e.cable_vdo:08X}"
                if e else "no e-marker answered")
        return f"port {self.port}: connected {self.connected} · {self.devices()} · link {self.link()[1]} · {chip}"


def _walk(node, out):
    out.append(node)
    for c in node.get("IORegistryEntryChildren", []):
        _walk(c, out)


def parse_ports(raw: bytes) -> dict[int, PortState]:
    """Parse the output of `ioreg -a -l -r -n Port-USB-C`."""
    roots = plistlib.loads(raw) if raw.strip() else []
    ports: dict[int, PortState] = {}
    for root in roots:
        num = root.get("PortNumber")
        if num is None:
            continue
        nodes: list[dict] = []
        _walk(root, nodes)
        st = PortState(port=num, connected=bool(root.get("ConnectionActive")), transports_active=list(root.get("TransportsActive", [])))
        for n in nodes:
            cls = n.get("IOObjectClass", "")
            desc = n.get("TransportDescription") or n.get("Description") or ""
            if cls == "IOPortTransportComponentCCUSBPDSOPp":
                st.emarker = decode_emarker(n.get("Metadata", {}), n.get("Specification Revision"))
            elif cls == "IOPortTransportComponentCCUSBPDSOP":
                st.partner_vid = n.get("Vendor ID")
            elif cls == "IOPortTransportStateUSB2" and n.get("Active"):
                st.usb2_rate, st.usb2_product = n.get("DataRateDescription"), n.get("Product")
            elif cls == "IOPortTransportStateUSB3" and n.get("Active"):
                st.usb3_rate, st.usb3_product = n.get("DataRateDescription"), n.get("Product")
            elif cls == "IOPortTransportStateCIO" and n.get("Active"):
                st.cio_active, st.cio_device, st.cio_cable_speed = True, n.get("Device Model Name") or n.get("Device Vendor Name"), n.get("CableSpeed")
            elif cls == "IOPortTransportStateDisplayPort" and n.get("Active") and "/CIO/" not in desc:
                st.dp_rate = n.get("LinkRateDescription")
        ports[num] = st
    return ports


def add_thunderbolt_speeds(ports: dict[int, PortState]) -> None:
    """Fill tb_speed from `system_profiler SPThunderboltDataType` (the trained Thunderbolt rate per receptacle)."""
    try:
        out = subprocess.run(["system_profiler", "-json", "SPThunderboltDataType"], capture_output=True, check=True, timeout=20).stdout
        for bus in json.loads(out).get("SPThunderboltDataType", []):
            rec = bus.get("receptacle_1_tag", {})
            try:
                num = int(rec.get("receptacle_id_key", ""))
            except ValueError:
                continue
            if num in ports and rec.get("receptacle_status_key") == "receptacle_connected":
                ports[num].tb_speed = rec.get("current_speed_key")
    except Exception:
        pass


def read_ports() -> dict[int, PortState]:
    raw = subprocess.run(["ioreg", "-a", "-l", "-r", "-n", "Port-USB-C"], capture_output=True, check=True, timeout=60).stdout
    ports = parse_ports(raw)
    add_thunderbolt_speeds(ports)
    return ports


def usb_devices() -> dict:
    """{location_id: (name, speed_text, [disks])} for every device on the Mac's USB tree right now."""
    try:
        out = subprocess.run(["system_profiler", "SPUSBDataType", "-json"], capture_output=True, text=True, timeout=20).stdout
        tree = json.loads(out).get("SPUSBDataType", [])
    except Exception:
        return {}
    found: dict = {}
    speeds = {"low_speed": "1.5 Mb/s", "full_speed": "12 Mb/s", "high_speed": "480 Mb/s", "super_speed": "5 Gb/s",
              "super_speed_plus": "10 Gb/s", "super_speed_plus_20": "20 Gb/s", "super_speed_plus_40": "40 Gb/s"}

    def walk(items):
        for it in items:
            if "location_id" in it:
                disks = [m.get("bsd_name") for m in it.get("Media", []) if m.get("bsd_name")]
                speed = speeds.get(it.get("device_speed", ""), it.get("device_speed", it.get("speed", "")))
                found[it["location_id"]] = (it.get("_name", "?"), speed, disks)
            walk(it.get("_items", []))
    walk(tree)
    return found


def tester_present() -> bool:
    """Is a POWER-Z tester on the host's USB tree? (macOS: system_profiler; elsewhere: assume yes.)"""
    try:
        import sys
        if sys.platform != "darwin":
            return True
        return any(any(k in v[0].upper() for k in ("POWER-Z", "POWER_Z", "POWERZ", "KM003C", "CHARGERLAB")) for v in usb_devices().values())
    except Exception:
        return True
