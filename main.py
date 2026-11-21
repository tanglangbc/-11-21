#!/usr/bin/env python3
"""news-image-20261121 entry: draws a one-page newspaper front page summing
up the world news of Saturday 21 November 2026 and writes it to
/output/entry.png (1024x1024 PNG, standard library only).

The page is drawn from scratch in pure Python: a small RGB canvas with
integer drawing primitives, a hand-made 8x8 bitmap font scaled up for the
masthead, headlines and decks, one tiny illustration per story, and a
minimal PNG encoder (zlib + struct, both stdlib). No network, no file
reads, no randomness, no clock: two runs produce byte-identical output.

Run locally with:
    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (247, 243, 234)
INK = (20, 20, 20)
GRAY = (96, 92, 84)
RED = (179, 32, 44)
NAVY = (31, 58, 95)
TEAL = (15, 118, 110)
AMBER = (196, 122, 18)
WHITE = (255, 255, 255)
SKY = (214, 231, 240)

# ---------------------------------------------------------------------------
# 8x8 bitmap font: one byte per row, most significant bit on the left.
# Uppercase, digits and the punctuation the page uses. Hand-made here so the
# program needs no font file and no third-party package.
# ---------------------------------------------------------------------------

FONT = {
    "A": (0x18, 0x24, 0x42, 0x42, 0x7E, 0x42, 0x42, 0x42),
    "B": (0x7C, 0x42, 0x42, 0x7C, 0x42, 0x42, 0x42, 0x7C),
    "C": (0x3C, 0x42, 0x40, 0x40, 0x40, 0x40, 0x42, 0x3C),
    "D": (0x78, 0x44, 0x42, 0x42, 0x42, 0x42, 0x44, 0x78),
    "E": (0x7E, 0x40, 0x40, 0x7C, 0x40, 0x40, 0x40, 0x7E),
    "F": (0x7E, 0x40, 0x40, 0x7C, 0x40, 0x40, 0x40, 0x40),
    "G": (0x3C, 0x42, 0x40, 0x40, 0x4E, 0x42, 0x42, 0x3C),
    "H": (0x42, 0x42, 0x42, 0x7E, 0x42, 0x42, 0x42, 0x42),
    "I": (0x3E, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x3E),
    "J": (0x1E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x44, 0x38),
    "K": (0x42, 0x44, 0x48, 0x70, 0x48, 0x44, 0x42, 0x42),
    "L": (0x40, 0x40, 0x40, 0x40, 0x40, 0x40, 0x40, 0x7E),
    "M": (0x42, 0x66, 0x5A, 0x5A, 0x42, 0x42, 0x42, 0x42),
    "N": (0x42, 0x62, 0x52, 0x4A, 0x46, 0x42, 0x42, 0x42),
    "O": (0x3C, 0x42, 0x42, 0x42, 0x42, 0x42, 0x42, 0x3C),
    "P": (0x7C, 0x42, 0x42, 0x7C, 0x40, 0x40, 0x40, 0x40),
    "Q": (0x3C, 0x42, 0x42, 0x42, 0x42, 0x4A, 0x44, 0x3A),
    "R": (0x7C, 0x42, 0x42, 0x7C, 0x48, 0x44, 0x42, 0x42),
    "S": (0x3C, 0x42, 0x40, 0x3C, 0x02, 0x02, 0x42, 0x3C),
    "T": (0x7E, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08),
    "U": (0x42, 0x42, 0x42, 0x42, 0x42, 0x42, 0x42, 0x3C),
    "V": (0x42, 0x42, 0x42, 0x42, 0x42, 0x42, 0x24, 0x18),
    "W": (0x42, 0x42, 0x42, 0x42, 0x5A, 0x5A, 0x66, 0x42),
    "X": (0x42, 0x42, 0x24, 0x18, 0x18, 0x24, 0x42, 0x42),
    "Y": (0x42, 0x42, 0x24, 0x18, 0x08, 0x08, 0x08, 0x08),
    "Z": (0x7E, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x7E),
    "0": (0x3C, 0x42, 0x46, 0x4A, 0x52, 0x62, 0x42, 0x3C),
    "1": (0x08, 0x18, 0x28, 0x08, 0x08, 0x08, 0x08, 0x3E),
    "2": (0x3C, 0x42, 0x02, 0x02, 0x3C, 0x40, 0x40, 0x7E),
    "3": (0x3C, 0x42, 0x02, 0x1C, 0x02, 0x02, 0x42, 0x3C),
    "4": (0x04, 0x0C, 0x14, 0x24, 0x7E, 0x04, 0x04, 0x04),
    "5": (0x7E, 0x40, 0x7C, 0x02, 0x02, 0x02, 0x42, 0x3C),
    "6": (0x1C, 0x20, 0x40, 0x7C, 0x42, 0x42, 0x42, 0x3C),
    "7": (0x7E, 0x02, 0x04, 0x08, 0x10, 0x10, 0x10, 0x10),
    "8": (0x3C, 0x42, 0x42, 0x3C, 0x42, 0x42, 0x42, 0x3C),
    "9": (0x3C, 0x42, 0x42, 0x42, 0x3E, 0x02, 0x04, 0x38),
    " ": (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    ".": (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x18, 0x18),
    ",": (0x00, 0x00, 0x00, 0x00, 0x00, 0x18, 0x08, 0x10),
    ":": (0x00, 0x18, 0x18, 0x00, 0x00, 0x18, 0x18, 0x00),
    ";": (0x00, 0x18, 0x18, 0x00, 0x00, 0x18, 0x08, 0x10),
    "'": (0x08, 0x08, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00),
    "-": (0x00, 0x00, 0x00, 0x00, 0x7E, 0x00, 0x00, 0x00),
    "/": (0x02, 0x04, 0x04, 0x08, 0x08, 0x10, 0x10, 0x20),
    "(": (0x04, 0x08, 0x08, 0x10, 0x10, 0x10, 0x08, 0x04),
    ")": (0x10, 0x08, 0x08, 0x04, 0x04, 0x04, 0x08, 0x10),
    "$": (0x08, 0x3E, 0x28, 0x3E, 0x0A, 0x3E, 0x08, 0x00),
    "%": (0x61, 0x12, 0x08, 0x10, 0x20, 0x48, 0x86, 0x00),
    "&": (0x1C, 0x22, 0x22, 0x14, 0x08, 0x14, 0x22, 0x22),
    "!": (0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x00, 0x08),
    "?": (0x3C, 0x42, 0x02, 0x04, 0x08, 0x08, 0x00, 0x08),
    "+": (0x00, 0x08, 0x08, 0x3E, 0x08, 0x08, 0x00, 0x00),
    "=": (0x00, 0x00, 0x00, 0x7E, 0x00, 0x7E, 0x00, 0x00),
    "\u2022": (0x00, 0x00, 0x18, 0x18, 0x18, 0x00, 0x00, 0x00),
    '"': (0x14, 0x14, 0x14, 0x00, 0x00, 0x00, 0x00, 0x00),
}


# ---------------------------------------------------------------------------
# Pixel canvas: a plain RGB byte buffer with the few primitives the page
# needs. Everything is integer math, so output is fully deterministic.
# ---------------------------------------------------------------------------

class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = c[0]
            self.buf[i + 1] = c[1]
            self.buf[i + 2] = c[2]

    def fill_rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.buf[i] = c[0]
                self.buf[i + 1] = c[1]
                self.buf[i + 2] = c[2]

    def hline(self, x, y, w, c, t=1):
        self.fill_rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.fill_rect(x, y, t, h, c)

    def frame(self, x, y, w, h, c, t=2):
        self.fill_rect(x, y, w, t, c)
        self.fill_rect(x, y + h - t, w, t, c)
        self.fill_rect(x, y, t, h, c)
        self.fill_rect(x + w - t, y, t, h, c)

    def disc(self, cx, cy, r, c):
        # Filled disc, scanline by scanline.
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.fill_rect(cx - dx, cy + dy, dx * 2 + 1, 1, c)

    def ring(self, cx, cy, r, c, t=2):
        for dy in range(-r - t, r + t + 1):
            for dx in range(-r - t, r + t + 1):
                d = (dx * dx + dy * dy) ** 0.5
                if r - t <= d <= r + t:
                    self.px(cx + dx, cy + dy, c)

    def line(self, x0, y0, x1, y1, c, t=2):
        # Bresenham line with a square brush of side t.
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.fill_rect(x0 - t // 2, y0 - t // 2, t, t, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def triangle(self, x0, y0, x1, y1, x2, y2, c):
        # Filled triangle by scanline fill between its edges.
        ys = sorted([y0, y1, y2])
        for y in range(ys[0], ys[2] + 1):
            xs = []
            for (ax, ay, bx, by) in ((x0, y0, x1, y1),
                                     (x1, y1, x2, y2),
                                     (x2, y2, x0, y0)):
                if ay == by:
                    continue
                if min(ay, by) <= y <= max(ay, by):
                    t = (y - ay) / (by - ay)
                    xs.append(ax + t * (bx - ax))
            if len(xs) >= 2:
                xa, xb = int(min(xs)), int(max(xs))
                self.fill_rect(xa, y, xb - xa + 1, 1, c)


# ---------------------------------------------------------------------------
# Text helpers.
# ---------------------------------------------------------------------------

def _advance(scale):
    return 8 * scale + max(2, scale)


def text_w(s, scale):
    adv = _advance(scale)
    return len(s) * adv - max(2, scale)


def draw_text(cv, x, y, s, scale, c):
    adv = _advance(scale)
    cx = x
    for ch in s:
        glyph = FONT.get(ch)
        if glyph is not None:
            for row in range(8):
                bits = glyph[row]
                if bits == 0:
                    continue
                for col in range(8):
                    if bits & (0x80 >> col):
                        cv.fill_rect(cx + col * scale, y + row * scale,
                                     scale, scale, c)
        cx += adv


def draw_text_centered(cv, cx, y, s, scale, c):
    draw_text(cv, cx - text_w(s, scale) // 2, y, s, scale, c)


def wrap_lines(text, max_w, scale):
    words = text.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_block(cv, x, y, text, max_w, scale, c, leading=None):
    if leading is None:
        leading = 8 * scale + 2 * scale
    lines = wrap_lines(text, max_w, scale)
    for i, line in enumerate(lines):
        draw_text(cv, x, y + i * leading, line, scale, c)
    return y + len(lines) * leading


# ---------------------------------------------------------------------------
# Minimal PNG writer: signature, IHDR, one IDAT (zlib level 9, filter 0),
# IEND. Deterministic for identical pixels.
# ---------------------------------------------------------------------------

def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def png_bytes(cv):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.buf[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    data = b"\x89PNG\r\n\x1a\n"
    data += _chunk(b"IHDR", ihdr)
    data += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    data += _chunk(b"IEND", b"")
    return data


# ---------------------------------------------------------------------------
# The news: four stories, all first reported on Saturday 21 November 2026.
# Headlines and decks are written from the day's reporting (The Hindu, Dawn,
# The Manila Times, Times Now). Nothing here is invented: every fact below
# appeared in that day's news.
# ---------------------------------------------------------------------------

LEAD = {
    "kicker": "LEAD \u2022 THE HAGUE",
    "headline": "WORLD COURT: MYANMAR COMMITTED GENOCIDE",
    "deck": "THE INTERNATIONAL COURT OF JUSTICE RULES MYANMAR COMMITTED "
            "GENOCIDE AGAINST THE ROHINGYA, IN A LANDMARK VERDICT.",
}

SECONDARY = [
    {
        "kicker": "DIPLOMACY \u2022 SHENZHEN",
        "headline": "TRUMP, XI AND PUTIN MEET IN SHENZHEN",
        "deck": "THE THREE LEADERS HOLD A TRILATERAL SUMMIT ON THE APEC "
                "SIDELINES; INDIA TAKES NOTE.",
        "icon": "summit",
        "color": NAVY,
    },
    {
        "kicker": "WAR \u2022 POLAND",
        "headline": "RUSSIAN MISSILE CRASHES IN POLAND",
        "deck": "WARSAW CALLS IT A PROVOCATION AS RUSSIA POUNDS UKRAINE "
                "ANEW.",
        "icon": "burst",
        "color": RED,
    },
    {
        "kicker": "EARTHQUAKE \u2022 PERU",
        "headline": "6.9 QUAKE SHAKES PERU'S ANDES",
        "deck": "TREMORS FELT IN LIMA; NO CASUALTIES REPORTED.",
        "icon": "seismo",
        "color": TEAL,
    },
]


# ---------------------------------------------------------------------------
# One small illustration per story, drawn in a 110x110 box.
# ---------------------------------------------------------------------------

def draw_scales(cv, cx, cy, r):
    # The lead's picture: the scales of justice, for the world court.
    cv.disc(cx, cy, r, WHITE)
    cv.ring(cx, cy, r, NAVY, 3)
    # Central pole and top beam.
    cv.line(cx, cy - r + 14, cx, cy + r - 16, NAVY, 4)
    cv.line(cx - 34, cy - 26, cx + 34, cy - 26, NAVY, 4)
    cv.disc(cx, cy - 26, 5, RED)
    # Two hanging pans: a triangle bowl on each side.
    for sx in (cx - 34, cx + 34):
        cv.line(sx, cy - 26, sx, cy + 2, INK, 2)
        cv.triangle(sx - 16, cy + 2, sx + 16, cy + 2, sx, cy + 22, AMBER)
    # Base.
    cv.line(cx - 18, cy + r - 16, cx + 18, cy + r - 16, NAVY, 4)


def draw_icon(cv, x, y, kind, color):
    # 110x110 box, sky tint, thin frame, one simple picture inside.
    cv.fill_rect(x, y, 110, 110, SKY)
    cv.frame(x, y, 110, 110, color, 2)
    cx, cy = x + 55, y + 55
    if kind == "summit":
        # Three leaders at one table: three discs joined by lines.
        cv.line(x + 24, cy + 6, x + 86, cy + 6, color, 3)
        cv.disc(x + 24, cy - 8, 13, RED)
        cv.disc(cx, cy - 8, 13, AMBER)
        cv.disc(x + 86, cy - 8, 13, color)
        cv.fill_rect(x + 18, cy + 14, 74, 8, INK)
        cv.line(x + 24, cy + 22, x + 20, cy + 44, INK, 3)
        cv.line(x + 86, cy + 22, x + 90, cy + 44, INK, 3)
    elif kind == "burst":
        # An explosion burst: rays out of a hot centre.
        for k in range(12):
            a = math.radians(k * 30)
            x0 = int(cx + 12 * math.cos(a))
            y0 = int(cy + 12 * math.sin(a))
            x1 = int(cx + 38 * math.cos(a))
            y1 = int(cy + 38 * math.sin(a))
            cv.line(x0, y0, x1, y1, color, 3)
        cv.disc(cx, cy, 10, AMBER)
        cv.disc(cx, cy, 5, RED)
    elif kind == "seismo":
        # A seismograph trace zig-zagging across the box.
        pts = [(x + 8, cy + 6), (x + 26, cy + 6), (x + 34, cy - 26),
               (x + 44, cy + 30), (x + 54, cy - 18), (x + 62, cy + 22),
               (x + 72, cy - 8), (x + 80, cy + 6), (x + 102, cy + 6)]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            cv.line(ax, ay, bx, by, color, 3)
        cv.disc(x + 34, cy - 26, 3, RED)
        cv.disc(x + 44, cy + 30, 3, RED)


def build():
    # Clean layout: wide 64 px margins, one thin rule under the masthead,
    # one under the lead, and a source line at the foot. Lead story on top,
    # three illustrated stories below, lots of air.
    cv = Canvas(W, H, PAPER)

    # Masthead: nameplate, then the day.
    draw_text_centered(cv, W // 2, 56, "THE WORLD TODAY", 6, INK)
    draw_text_centered(cv, W // 2, 118, "SATURDAY 21 NOVEMBER 2026", 3, RED)
    cv.hline(64, 168, W - 128, INK, 2)

    # Lead story: red kicker, big headline, deck on the left with the
    # scales of justice on the right.
    draw_text(cv, 64, 196, LEAD["kicker"], 2, RED)
    draw_block(cv, 64, 226, LEAD["headline"], W - 128, 5, INK, leading=50)
    draw_block(cv, 64, 352, LEAD["deck"], 640, 2, INK, leading=22)
    draw_scales(cv, 880, 400, 58)
    cv.hline(64, 480, W - 128, INK, 1)

    # Three secondary stories, one row each: icon box on the left, gray
    # kicker, headline and deck on the right.
    y = 508
    for story in SECONDARY:
        draw_icon(cv, 64, y - 4, story["icon"], story["color"])
        draw_text(cv, 200, y, story["kicker"], 2, GRAY)
        end = draw_block(cv, 200, y + 26, story["headline"], W - 200 - 64,
                         3, INK, leading=32)
        draw_block(cv, 200, end + 8, story["deck"], W - 200 - 64, 2, INK,
                   leading=22)
        y += 150

    # Foot: where the stories come from.
    draw_text_centered(cv, W // 2, 986,
                       "SOURCES: THE HINDU \u2022 DAWN \u2022 MANILA TIMES "
                       "\u2022 TIMES NOW", 2, GRAY)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(build())
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
