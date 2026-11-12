"""Read-only throughput test through a cable (experimental, off by default).

Reads existing large files from a mounted volume on the far end of the cable with the page cache bypassed
(macOS `F_NOCACHE`), and compares the rate to a floor for the link class. It never writes. It is not part of
the station's labels yet: the floors are provisional, taken from one drive's vendor figures, and a slow
result can mean the drive, the dock, or the host rather than the cable. Kept as a module for a future
"real work" experiment; `cable-station snapshot --read-test VOLUME` runs it on request.
"""
from __future__ import annotations

import fcntl
import os
import time
from pathlib import Path

F_NOCACHE = 48  # fcntl command on macOS: bypass the unified buffer cache for this fd

# Read-throughput floors in MB/s per link class. Provisional.
THROUGHPUT_FLOOR_MBPS = {"tb40": 1500, "tb20": 900, "usb10": 600, "usb5": 300, "usb2": 25}


def read_throughput(volume: Path, seconds: float = 8.0, max_bytes: int = 6 << 30) -> tuple[float, int] | None:
    """(MB/s, bytes read) from existing files of 256 MB or more on `volume`, or None when there are none."""
    files: list[Path] = []
    for dirpath, _dirs, names in os.walk(volume):
        if "/." in dirpath:
            continue
        for name in names:
            p = Path(dirpath) / name
            try:
                if p.stat().st_size >= 256 << 20:
                    files.append(p)
            except OSError:
                pass
        if len(files) >= 40:
            break
    if not files:
        return None
    buf = bytearray(8 << 20)
    total, start = 0, time.monotonic()
    for p in files:
        try:
            fd = os.open(p, os.O_RDONLY)
        except OSError:
            continue
        try:
            try:
                fcntl.fcntl(fd, F_NOCACHE, 1)
            except OSError:
                pass  # not macOS: the cache stays on and the figure is optimistic
            while (n := os.readv(fd, [buf])) > 0:
                total += n
                if time.monotonic() - start >= seconds or total >= max_bytes:
                    break
        finally:
            os.close(fd)
        if time.monotonic() - start >= seconds or total >= max_bytes:
            break
    elapsed = time.monotonic() - start
    return (total / elapsed / 1e6 if elapsed > 0 else 0.0), total


def judge(mbps: float, link_class: str) -> bool | None:
    floor = THROUGHPUT_FLOOR_MBPS.get(link_class)
    return None if floor is None else mbps >= floor
