import pytest
from PIL import Image

from cable_station import flag


@pytest.mark.parametrize("line1,line2", [
    ("USB 2.0 480M", "60W 3A"),
    ("USB4 20G · USB 3.2 10G", "100W 5A"),
    ("USB4 ≥40G · USB 3.2 10G Active", "240W 5A EPR"),
    ("no eMarker · USB 2.0 480M", "60W 3A · eMarker unread"),
])
def test_reachable_band_rule(tmp_path, line1, line2):
    """Every row of ink stays inside the band the printer can reach after its vertical offset."""
    out = tmp_path / "flag.png"
    desc = flag.render(str(out), line1, line2, tape=9, cable_id="C17", vertical_offset_mm=1.45)
    img = Image.open(out)
    H = flag.PRINTABLE_PX[9]
    assert img.size[1] == H
    first, last = flag.ink_rows(out)
    margin = flag.mm(1.45) + 1
    assert first >= margin, (desc, first)
    assert last <= H - margin - 1, (desc, last)
    assert "tape 9 mm" in desc


def test_two_faces_and_fold_line(tmp_path):
    out = tmp_path / "flag.png"
    flag.render(str(out), "USB 2.0 480M", "60W 3A", tape=9, cable_id="C1")
    img = Image.open(out).convert("L")
    W, H = img.size
    px = img.load()
    cx = W // 2
    # the fold line is the only ink in the middle column of the wrap zone
    assert any(px[cx, y] < 128 for y in range(H))
    for x in (cx - 40, cx + 40):
        assert not any(px[x, y] < 128 for y in range(H))
    # both faces carry ink
    assert any(px[x, y] < 128 for x in range(0, W // 4) for y in range(0, H, 2))
    assert any(px[x, y] < 128 for x in range(3 * W // 4, W) for y in range(0, H, 2))


def test_long_text_grows_the_flag(tmp_path):
    short = flag.render(str(tmp_path / "a.png"), "USB 2.0 480M", "60W 3A", cable_id="C1")
    long = flag.render(str(tmp_path / "b.png"), "USB4 ≥40G · USB 3.2 10G Active", "240W 5A EPR", cable_id="C123")
    mm_of = lambda d: int(d.split(", ")[2].split()[0])
    assert mm_of(long) >= mm_of(short)
    assert "font" in long


def test_other_tape_widths(tmp_path):
    for tape in (12, 24):
        out = tmp_path / f"{tape}.png"
        flag.render(str(out), "USB 3.2 5G", "60W 3A", tape=tape, cable_id="C2")
        assert Image.open(out).size[1] == flag.PRINTABLE_PX[tape]


def test_thunderbolt_bolt_is_drawn_and_stays_in_band(tmp_path):
    out = tmp_path / "tb.png"
    flag.render(str(out), "TB4 ⚡ 40G · USB 3.2 10G", "240W 5A EPR", tape=9, cable_id="C21", vertical_offset_mm=1.45)
    first, last = flag.ink_rows(out)
    margin = flag.mm(1.45) + 1
    assert first >= margin and last <= flag.PRINTABLE_PX[9] - margin - 1
