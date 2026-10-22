"""Text width from a font file (TTF, OTF or WOFF; standard library only), so a Brand Kit with its own fonts
gets exact text-fit checks. Without a font file, widths are estimated from the kit's average glyph width."""
from __future__ import annotations

import struct
import zlib


class Font:
    """Advance widths of one font. Raises ValueError for anything it can't read (e.g. WOFF2)."""

    def __init__(self, data: bytes):
        self.tables = _tables(data)
        for tag in ("head", "hhea", "hmtx", "cmap"):
            if tag not in self.tables:
                raise ValueError(f"the font has no '{tag}' table")
        self.units = struct.unpack(">H", self.tables["head"][18:20])[0]
        n_metrics = struct.unpack(">H", self.tables["hhea"][34:36])[0]
        hmtx = self.tables["hmtx"]
        self.advances = [struct.unpack(">H", hmtx[i * 4:i * 4 + 2])[0] for i in range(n_metrics)]
        self.glyph_of = _cmap(self.tables["cmap"])
        self._cache = {}

    def advance(self, ch: str) -> int:
        if ch not in self._cache:
            g = self.glyph_of(ord(ch))
            self._cache[ch] = self.advances[min(g, len(self.advances) - 1)] if self.advances else 0
        return self._cache[ch]

    def width(self, text: str, size: float) -> float:
        return sum(self.advance(ch) for ch in str(text)) * size / self.units


def _tables(data: bytes) -> dict:
    sig = data[:4]
    if sig == b"wOF2":
        raise ValueError("WOFF2 fonts can't be read here; include the .ttf or .otf instead")
    if sig == b"wOFF":
        n = struct.unpack(">H", data[12:14])[0]
        out = {}
        for i in range(n):
            tag, off, comp, orig, _ = struct.unpack(">4sIIII", data[44 + i * 20:64 + i * 20])
            raw = data[off:off + comp]
            out[tag.decode("latin-1")] = zlib.decompress(raw) if comp < orig else raw
        return out
    if sig not in (b"\x00\x01\x00\x00", b"OTTO", b"true"):
        raise ValueError("not a TrueType, OpenType or WOFF font")
    n = struct.unpack(">H", data[4:6])[0]
    out = {}
    for i in range(n):
        tag, _, off, length = struct.unpack(">4sIII", data[12 + i * 16:28 + i * 16])
        out[tag.decode("latin-1")] = data[off:off + length]
    return out


def _cmap(cmap: bytes):
    """A function codepoint → glyph index, from the best Unicode subtable (format 12, else 4)."""
    n = struct.unpack(">H", cmap[2:4])[0]
    records = [struct.unpack(">HHI", cmap[4 + i * 8:12 + i * 8]) for i in range(n)]
    subtables = {}
    for platform, encoding, offset in records:
        fmt = struct.unpack(">H", cmap[offset:offset + 2])[0]
        if (platform == 3 and encoding in (1, 10)) or platform == 0:
            subtables.setdefault(fmt, offset)
    if 12 in subtables:
        o = subtables[12]
        groups = struct.unpack(">I", cmap[o + 12:o + 16])[0]
        ranges = [struct.unpack(">III", cmap[o + 16 + i * 12:o + 28 + i * 12]) for i in range(groups)]

        def glyph12(c):
            for start, end, first in ranges:
                if start <= c <= end:
                    return first + c - start
            return 0
        return glyph12
    if 4 in subtables:
        o = subtables[4]
        seg = struct.unpack(">H", cmap[o + 6:o + 8])[0] // 2
        ends = struct.unpack(f">{seg}H", cmap[o + 14:o + 14 + seg * 2])
        starts_at = o + 16 + seg * 2
        starts = struct.unpack(f">{seg}H", cmap[starts_at:starts_at + seg * 2])
        deltas = struct.unpack(f">{seg}h", cmap[starts_at + seg * 2:starts_at + seg * 4])
        ro_at = starts_at + seg * 4
        range_offsets = struct.unpack(f">{seg}H", cmap[ro_at:ro_at + seg * 2])

        def glyph4(c):
            for i in range(seg):
                if starts[i] <= c <= ends[i]:
                    if range_offsets[i] == 0:
                        return (c + deltas[i]) & 0xFFFF
                    at = ro_at + i * 2 + range_offsets[i] + 2 * (c - starts[i])
                    g = struct.unpack(">H", cmap[at:at + 2])[0]
                    return (g + deltas[i]) & 0xFFFF if g else 0
            return 0
        return glyph4
    raise ValueError("the font has no Unicode character map")


class Measure:
    """Text width for one font role of a Brand Kit: exact from its font file, or estimated."""

    def __init__(self, font_file: bytes = None, avg_char_width: float = 0.55):
        self.font = Font(font_file) if font_file else None
        self.avg = avg_char_width

    def width(self, text: str, size: float) -> float:
        if self.font:
            return self.font.width(text, size)
        return len(str(text)) * size * self.avg

    def fits(self, text: str, size: float, width: float) -> bool:
        """Whether text fits on one line of this width (both in the same unit as size)."""
        if self.font:
            return self.font.width(text, size) <= width
        return len(str(text)) <= self.capacity(size, width)

    def capacity(self, size: float, width: float) -> int:
        """About how many characters fit on one line."""
        return max(1, int(width / (size * self.avg)))
