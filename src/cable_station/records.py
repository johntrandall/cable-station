"""The cable records: one Markdown note per cable, frontmatter as the fields, plus an Obsidian Base.

The notes are the database. Any Markdown editor can read them, and Obsidian shows the folder as a table
through the generated `_cables.base`. The station reads and writes the same notes.

Fields (frontmatter):
  id            C<N>, the serial this station assigns, printed on the flag as #N
  tested        ISO date of the e-marker read
  connector     e.g. "USB-C to USB-C"
  data_label    line 1 of the flag
  power_label   line 2 of the flag, with " · #N"
  current_a     3 or 5 (from the e-marker; 3 assumed when there is none)
  epr           true or false
  speed         "USB4 20G · USB 3.2 10G" and the like
  active        true or false
  emarker       true or false (false: chipless cable)
  emarker_read  true when a chip was read; false when the chip is known to exist but was never read
                (a 20G+ link proves a chip); then current_a and epr are "" (unknown)
  vendor        e-marker vendor id, hex
  product       e-marker product id, hex
  cable_vdo     the raw cable VDO word, hex
  tbt           Thunderbolt flag when known, else ""
  load_test     "pass", "fail" or "" (voltage-drop test; not run by this version)
  label_note    a short caveat printed after the power line, e.g. "eMarker unread"; "" normally
  status        "active" or "decommissioned" (a broken or discarded cable keeps its record and number)
  decommissioned  ISO date it was retired, else ""
  notes         free text
"""
from __future__ import annotations

import datetime
import re
from pathlib import Path

FIELDS = ["id", "tested", "connector", "data_label", "power_label", "current_a", "epr", "speed", "active", "emarker", "emarker_read",
          "vendor", "product", "cable_vdo", "tbt", "load_test", "label_note", "status", "decommissioned", "notes"]


def _q(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return '""'
    s = str(v)
    return '"' + s.replace('"', '\\"') + '"' if (s == "" or any(c in s for c in ':#·"[]{}') or s != s.strip()) else s


def _unq(s):
    s = s.strip()
    if s in ("true", "false"):
        return s == "true"
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1].replace('\\"', '"')
    return s


BASE = """filters:
  and:
    - type == "cable"
properties:
  id:
    displayName: ID
  data_label:
    displayName: Data
  power_label:
    displayName: Power
  current_a:
    displayName: A
  epr:
    displayName: EPR
  speed:
    displayName: Speed
  active:
    displayName: Active
  emarker:
    displayName: eMarker
  emarker_read:
    displayName: Chip read
  vendor:
    displayName: Vendor
  product:
    displayName: Product
  cable_vdo:
    displayName: Cable VDO
  tested:
    displayName: Tested
  load_test:
    displayName: Load test
  status:
    displayName: Status
  decommissioned:
    displayName: Retired
  notes:
    displayName: Notes
views:
  - type: table
    name: 1 · CABLES
    order:
      - id
      - data_label
      - power_label
      - current_a
      - epr
      - speed
      - active
      - emarker
      - emarker_read
      - vendor
      - product
      - cable_vdo
      - tested
      - load_test
      - status
      - decommissioned
      - notes
    sort:
      - property: id
        direction: ASC
"""


class Store:
    """The folder of cable notes."""

    def __init__(self, data_dir: Path | str):
        self.dir = Path(data_dir).expanduser()

    def path_of(self, cid: str) -> Path:
        return self.dir / f"{cid}.md"

    def read_all(self) -> list[dict]:
        self.dir.mkdir(parents=True, exist_ok=True)
        rows = []
        for p in sorted(self.dir.iterdir()):
            if not re.fullmatch(r"C\d+\.md", p.name):
                continue
            text = p.read_text()
            m = re.match(r"---\n(.*?)\n---\n?(.*)", text, re.S)
            if not m:
                continue
            row = {k: "" for k in FIELDS}
            for line in m.group(1).splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    if k.strip() in FIELDS:
                        row[k.strip()] = _unq(v)
            body = m.group(2).strip()
            # write() puts a generated "# C<N> · data · power" heading above the body; strip it so an
            # update does not stack a stale heading on top of the current one.
            while body.startswith(f"# {row['id']} ·"):
                body = body.split("\n", 1)[1].strip() if "\n" in body else ""
            row["body"] = body
            rows.append(row)
        rows.sort(key=lambda r: int(r["id"][1:]) if r["id"][1:].isdigit() else 0)
        return rows

    def get(self, cid: str) -> dict | None:
        return next((r for r in self.read_all() if r["id"] == cid), None)

    def next_id(self, rows: list[dict] | None = None) -> str:
        rows = self.read_all() if rows is None else rows
        nums = [int(r["id"][1:]) for r in rows if r["id"][1:].isdigit()]
        return f"C{max(nums, default=0) + 1}"

    def set_status(self, cid: str, status: str) -> dict | None:
        """Mark a cable active or decommissioned, keeping its note body."""
        for r in self.read_all():
            if r["id"] == cid:
                r["status"] = status
                r["decommissioned"] = datetime.date.today().isoformat() if status == "decommissioned" else ""
                body = r.pop("body", "")
                self.write(r, body)
                return r
        return None

    def update(self, cid: str, fields: dict) -> dict | None:
        """Replace fields of an existing record (a retest), keeping its id, number, and note body."""
        for r in self.read_all():
            if r["id"] == cid:
                body = r.pop("body", "")
                r.update(fields)
                r["power_label"] = f"{fields.get('power_label', r['power_label']).split(' · #')[0]} · #{cid[1:]}"
                self.write(r, body)
                return r
        return None

    def write(self, row: dict, body: str = "") -> Path:
        self.dir.mkdir(parents=True, exist_ok=True)
        row = dict(row)
        row.setdefault("status", "active")
        lines = ["---", "type: cable"] + [f"{k}: {_q(row.get(k, ''))}" for k in FIELDS] + ["---", ""]
        lines.append(f"# {row['id']} · {row.get('data_label', '')} · {row.get('power_label', '')}")
        lines.append("")
        lines.append(body or f"Recorded {row.get('tested', '')} from the cable's e-marker read. The flag on the cable carries `#{row['id'][1:]}`.")
        lines.append("")
        p = self.path_of(row["id"])
        p.write_text("\n".join(lines))
        return p

    def ensure_base(self) -> Path:
        """The Obsidian Base is generated: always the current shape."""
        self.dir.mkdir(parents=True, exist_ok=True)
        p = self.dir / "_cables.base"
        if not p.exists() or p.read_text() != BASE:
            p.write_text(BASE)
        return p


def from_decode(r: dict, cid: str, connector: str, source: str) -> dict:
    """Build a row from tester_capture.decode()'s dict (or the equivalent Mac-read dict)."""
    return {"id": cid, "tested": datetime.date.today().isoformat(), "connector": connector, "data_label": r["label_line1"],
            "power_label": f"{r['label_line2']} · #{cid[1:]}", "current_a": (r["current"] or "")[:-1], "epr": bool(r["epr"]),
            "speed": r["speed"], "active": bool(r["active"]), "emarker": True, "emarker_read": True, "vendor": r["vendor_id"], "product": r["product_id"],
            "cable_vdo": r["cable_vdo"], "tbt": "", "load_test": "", "notes": f"read by {source}"}


def no_emarker_row(cid: str, connector: str, notes: str = "") -> dict:
    return {"id": cid, "tested": datetime.date.today().isoformat(), "connector": connector, "data_label": "no eMarker · USB 2.0 480M",
            "power_label": f"60W 3A · #{cid[1:]}", "current_a": "3", "epr": False, "speed": "480M (assumed; enumeration test pending)",
            "active": False, "emarker": False, "emarker_read": False, "vendor": "", "product": "", "cable_vdo": "", "tbt": "", "load_test": "",
            "notes": (notes + " no e-marker: the tester never attached in either orientation.").strip()}


def same_record(rows: list[dict], r: dict) -> list[str]:
    """IDs of recorded cables whose chip identity (vendor, product, cable VDO) equals the reading's."""
    return [x["id"] for x in rows if x["emarker"] is True and x["vendor"] == r["vendor_id"] and x["product"] == r["product_id"] and x["cable_vdo"] == r["cable_vdo"]]
