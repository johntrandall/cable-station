"""Render a two-line USB cable wrap-flag as a PNG for `ptouch-label --image`.

A wrap-flag is one strip whose middle wraps around the cable and whose two ends stick together as a flag.
The same two lines are printed on each end so both flag faces read correctly. Line 2 ends with the cable's
number as " · #N" in the same type as the specs; the middle dot alone is the separator.

The reachable-band rule: the printer may print with a vertical calibration offset (1.45 mm on one PT-P950NW).
`ptouch-label` shrinks any label whose ink would be pushed off the band by that shift, so every row of ink,
including the fold line, stays inside H - 2 * offset rows. The tests check this.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DPI = 360
PRINTABLE_PX = {6: 64, 9: 106, 12: 150, 18: 234, 24: 320}  # printable rows per tape width (PT-P950NW family)
FONT_CANDIDATES = [
    ("/System/Library/Fonts/HelveticaNeue.ttc", 1),                        # macOS, bold face
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 0),           # Debian and Ubuntu
    ("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf", 0),                    # Fedora
    ("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", 0),                       # Arch
]
MIN_FONT = 30   # the reachable band (64 px at 9 mm under a 1.45 mm offset) caps two lines near 30 px; longer flags only help width


def mm(v: float) -> int:
    return round(v / 25.4 * DPI)


def _font_file() -> tuple[str, int] | None:
    for path, index in FONT_CANDIDATES:
        if Path(path).exists():
            return path, index
    return None


def load_font(size: int):
    f = _font_file()
    if f is None:
        return ImageFont.load_default(size=size)
    return ImageFont.truetype(f[0], size, index=f[1])


def fit_font(draw, lines, max_w, max_h):
    size = 200
    while size > 8:
        f = load_font(size)
        widths = [draw.textbbox((0, 0), t, font=f)[2] for t in lines]
        heights = [draw.textbbox((0, 0), t, font=f)[3] - draw.textbbox((0, 0), t, font=f)[1] for t in lines]
        if max(widths) <= max_w and sum(heights) + (len(lines) - 1) * size * 0.15 <= max_h:
            return f
        size -= 2
    return load_font(8)


def render(out, line1: str, line2: str, tape: int = 9, length: int = 70, wrap: int = 20, pad: float = 1.5,
           cable_id: str | None = None, vertical_offset_mm: float = 1.45) -> str:
    """Render the flag to `out` and return a one-line description of its geometry."""
    H = PRINTABLE_PX[tape]
    id_text = f" · #{cable_id.lstrip('C#')}" if cable_id else ""
    lines = [line1, line2 + id_text]
    reach = H - 2 * (mm(vertical_offset_mm) + 1)   # the rows the shifted band can still print
    while True:      # grow the flag, 10 mm at a time up to 130 mm, until the text fits at a readable size
        W = mm(length)
        face_w = (W - mm(wrap)) // 2
        img = Image.new("L", (W, H), 255)
        d = ImageDraw.Draw(img)
        font = fit_font(d, lines, face_w - mm(pad) * 2, reach)
        if font.size >= MIN_FONT or length >= 130:
            break
        length += 10
    id_font = font  # same weight and size as the specs; the separator alone marks it
    gap = font.size * 0.08
    boxes = [d.textbbox((0, 0), line1, font=font), d.textbbox((0, 0), line2, font=font)]
    id_w = (d.textlength(" · ", font=font) + d.textlength(id_text[3:], font=id_font)) if id_text else 0
    total_h = sum(b[3] - b[1] for b in boxes) + gap
    for face_x in (0, W - face_w):
        y = (H - total_h) / 2
        b = boxes[0]
        d.text((face_x + (face_w - (b[2] - b[0])) / 2 - b[0], y - b[1]), line1, font=font, fill=0)
        y += (b[3] - b[1]) + gap
        b = boxes[1]
        w2 = (b[2] - b[0]) + id_w
        x = face_x + (face_w - w2) / 2 - b[0]
        baseline = y - b[1] + font.getmetrics()[0]
        d.text((x, baseline), line2, font=font, fill=0, anchor="ls")
        if id_text:
            sep = " · "
            d.text((x + (b[2] - b[0]), baseline), sep, font=font, fill=0, anchor="ls")
            d.text((x + (b[2] - b[0]) + d.textlength(sep, font=font), baseline), id_text[len(sep):], font=id_font, fill=0, anchor="ls")
    # Fold line: a dotted vertical line at the exact centre of the wrap zone, kept clear of the tape edges.
    cx = W // 2
    margin = mm(vertical_offset_mm) + 2
    for y in range(margin, H - margin, 6):
        d.line([(cx, y), (cx, min(H - margin - 1, y + 2))], fill=0, width=2)
    img.save(out)
    return f"{W}x{H}px, tape {tape} mm, {length} mm long, font {font.size}px, faces {face_w / DPI * 25.4:.0f} mm, wrap {wrap} mm"


def ink_rows(path) -> tuple[int, int]:
    """(first, last) row that carries ink in a rendered flag; used to check the reachable-band rule."""
    img = Image.open(path).convert("L")
    w, h = img.size
    px = img.load()
    rows = [y for y in range(h) if any(px[x, y] < 128 for x in range(w))]
    return (rows[0], rows[-1]) if rows else (-1, -1)
