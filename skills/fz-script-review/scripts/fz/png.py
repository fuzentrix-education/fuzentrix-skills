"""PNG images for animation elements: read, check for real transparency, remove a flat key-colour background,
fit into a box on a full 1920×1080 transparent frame, and write. Uses Pillow when the sandbox has it; otherwise
the standard library (8-bit, non-interlaced PNGs; nearest-neighbour scaling)."""
from __future__ import annotations

import io
import struct
import zlib

USE_PIL = True  # tests switch this off to exercise the standard-library path


def _pil():
    if not USE_PIL:
        return None
    try:
        from PIL import Image
        return Image
    except Exception:
        return None


class RGBA:
    """An image as width, height and RGBA bytes (4 per pixel, rows top to bottom)."""

    def __init__(self, w: int, h: int, data: bytearray):
        self.w, self.h, self.data = w, h, data

    def pixel(self, x: int, y: int) -> tuple:
        i = (y * self.w + x) * 4
        return tuple(self.data[i:i + 4])


def read(data: bytes) -> RGBA:
    Image = _pil()
    if Image:
        img = Image.open(io.BytesIO(data)).convert("RGBA")
        return RGBA(img.width, img.height, bytearray(img.tobytes()))
    return _decode(data)


def write(img: RGBA) -> bytes:
    Image = _pil()
    if Image:
        out = io.BytesIO()
        Image.frombytes("RGBA", (img.w, img.h), bytes(img.data)).save(out, format="PNG", optimize=True)
        return out.getvalue()
    raw = b"".join(b"\x00" + bytes(img.data[y * img.w * 4:(y + 1) * img.w * 4]) for y in range(img.h))

    def chunk(tag, body):
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", img.w, img.h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def _decode(data: bytes) -> RGBA:
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    pos, idat, palette, trns = 8, b"", None, None
    while pos < len(data):
        length, tag = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        if tag == b"IHDR":
            w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
        elif tag == b"PLTE":
            palette = body
        elif tag == b"tRNS":
            trns = body
        elif tag == b"IDAT":
            idat += body
        pos += 12 + length
    if depth != 8 or interlace:
        raise ValueError("only 8-bit, non-interlaced PNGs can be read without Pillow")
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    stride = w * channels
    raw = zlib.decompress(idat)
    prev = bytearray(stride)
    out = bytearray(w * h * 4)
    for y in range(h):
        f = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - channels] if i >= channels else 0
            b = prev[i]
            c = prev[i - channels] if i >= channels else 0
            if f == 1:
                line[i] = (line[i] + a) & 255
            elif f == 2:
                line[i] = (line[i] + b) & 255
            elif f == 3:
                line[i] = (line[i] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        prev = line
        for x in range(w):
            o = (y * w + x) * 4
            px = line[x * channels:(x + 1) * channels]
            if ctype == 6:
                out[o:o + 4] = px
            elif ctype == 2:
                out[o:o + 4] = bytes(px) + b"\xff"
            elif ctype == 0:
                out[o:o + 4] = bytes((px[0], px[0], px[0], 255))
            elif ctype == 4:
                out[o:o + 4] = bytes((px[0], px[0], px[0], px[1]))
            else:
                k = px[0]
                alpha = trns[k] if trns and k < len(trns) else 255
                out[o:o + 4] = palette[k * 3:k * 3 + 3] + bytes((alpha,))
    return RGBA(w, h, out)


def _border(img: RGBA, step: int = 4):
    for x in range(0, img.w, step):
        yield img.pixel(x, 0)
        yield img.pixel(x, img.h - 1)
    for y in range(0, img.h, step):
        yield img.pixel(0, y)
        yield img.pixel(img.w - 1, y)


def is_transparent(img: RGBA) -> bool:
    """A real cut-out: most of the border is see-through (a drawn checkerboard is not)."""
    border = list(_border(img))
    return sum(1 for p in border if p[3] < 32) >= 0.6 * len(border)


def on_key(img: RGBA, key: tuple) -> bool:
    border = list(_border(img))
    return sum(1 for p in border if _dist(p, key) < 60) >= 0.6 * len(border)


def _dist(p, key) -> float:
    return ((p[0] - key[0]) ** 2 + (p[1] - key[1]) ** 2 + (p[2] - key[2]) ** 2) ** 0.5


def key_out(img: RGBA, key: tuple, tolerance: float = 60) -> RGBA:
    """Make the key colour transparent, with a soft edge just outside the tolerance."""
    data = bytearray(img.data)
    for i in range(0, len(data), 4):
        d = _dist(data[i:i + 3], key)
        if d < tolerance:
            data[i + 3] = 0
        elif d < tolerance * 1.6:
            data[i + 3] = min(data[i + 3], int(255 * (d - tolerance) / (tolerance * 0.6)))
    return RGBA(img.w, img.h, data)


def fit(img: RGBA, box: tuple) -> tuple:
    """(x, y, w, h) of the image fitted inside box = (x, y, w, h), keeping its shape, centred."""
    bx, by, bw, bh = box
    scale = min(bw / img.w, bh / img.h)
    w, h = max(1, round(img.w * scale)), max(1, round(img.h * scale))
    return bx + (bw - w) // 2, by + (bh - h) // 2, w, h


def resize(img: RGBA, w: int, h: int) -> RGBA:
    Image = _pil()
    if Image:
        small = Image.frombytes("RGBA", (img.w, img.h), bytes(img.data)).resize((w, h), Image.LANCZOS)
        return RGBA(w, h, bytearray(small.tobytes()))
    out = bytearray(w * h * 4)
    for y in range(h):
        sy = min(img.h - 1, y * img.h // h)
        for x in range(w):
            sx = min(img.w - 1, x * img.w // w)
            i, o = (sy * img.w + sx) * 4, (y * w + x) * 4
            out[o:o + 4] = img.data[i:i + 4]
    return RGBA(w, h, out)


def on_frame(img: RGBA, x: int, y: int, width: int, height: int) -> RGBA:
    """The image pasted at (x, y) on a transparent frame of width × height."""
    frame = bytearray(width * height * 4)
    for row in range(img.h):
        fy = y + row
        if not 0 <= fy < height:
            continue
        x0, x1 = max(0, x), min(width, x + img.w)
        if x1 <= x0:
            continue
        src = (row * img.w + (x0 - x)) * 4
        frame[(fy * width + x0) * 4:(fy * width + x1) * 4] = img.data[src:src + (x1 - x0) * 4]
    return RGBA(width, height, frame)
