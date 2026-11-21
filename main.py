#!/usr/bin/env python3
"""The World Today - 21 November 2026.

Draws a 1024x1024 newspaper front page using only the Python
standard library: a hand-built 5x7 pixel font, integer raster
drawing and a small PNG writer. No image assets, no fonts, no
network access. The picture is fully deterministic: the same
bytes come out on every run.

Usage:
    MAKEFUN_OUTPUT_DIR=out python3 main.py
Writes entry.png into the output directory (default /output).
"""

import math
import os
import struct
import zlib

WIDTH = 1024
HEIGHT = 1024

PAPER = (251, 247, 236)
INK = (17, 17, 17)
RED = (163, 22, 33)
BLUE = (31, 78, 121)
TEAL = (15, 118, 110)
GOLD = (180, 130, 29)
PALE = (220, 232, 240)
GREY = (105, 100, 88)

# 5x7 pixel font. Each glyph is seven rows; each row is a five-bit
# number where bit 4 is the leftmost pixel.
FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    " ": (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    ".": (0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C),
    ",": (0x00, 0x00, 0x00, 0x00, 0x0C, 0x04, 0x08),
    "'": (0x04, 0x04, 0x08, 0x00, 0x00, 0x00, 0x00),
    "-": (0x00, 0x00, 0x00, 0x0E, 0x00, 0x00, 0x00),
    ":": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00),
    ";": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x04, 0x08),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "%": (0x19, 0x1A, 0x02, 0x04, 0x08, 0x0B, 0x13),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x04),
    "?": (0x0E, 0x11, 0x01, 0x06, 0x04, 0x00, 0x04),
    "/": (0x01, 0x02, 0x02, 0x04, 0x08, 0x08, 0x10),
    '"': (0x0A, 0x0A, 0x00, 0x00, 0x00, 0x00, 0x00),
    "+": (0x00, 0x04, 0x04, 0x1F, 0x04, 0x04, 0x00),
    "·": (0x00, 0x00, 0x00, 0x04, 0x00, 0x00, 0x00),
}


class Canvas:
    """An RGB raster with integer drawing helpers."""

    def __init__(self, width, height, color):
        self.width = width
        self.height = height
        self.pixels = bytearray(bytes(color) * (width * height))

    def set(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = (y * self.width + x) * 3
            self.pixels[i:i + 3] = bytes(color)

    def hline(self, x, y, length, color):
        for dx in range(length):
            self.set(x + dx, y, color)

    def vline(self, x, y, length, color):
        for dy in range(length):
            self.set(x, y + dy, color)

    def fill_rect(self, x, y, w, h, color):
        for dy in range(h):
            self.hline(x, y + dy, w, color)

    def outline_rect(self, x, y, w, h, color, thick=1):
        for t in range(thick):
            self.hline(x + t, y + t, w - 2 * t, color)
            self.hline(x + t, y + h - 1 - t, w - 2 * t, color)
            self.vline(x + t, y + t, h - 2 * t, color)
            self.vline(x + w - 1 - t, y + t, h - 2 * t, color)

    def line(self, x0, y0, x1, y1, color):
        """Bresenham line, integer only."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def thick_line(self, x0, y0, x1, y1, color, thick=2):
        for ox in range(thick):
            for oy in range(thick):
                self.line(x0 + ox, y0 + oy, x1 + ox, y1 + oy, color)

    def circle(self, cx, cy, r, color):
        """Midpoint circle outline, integer only."""
        x, y, d = 0, r, 1 - r
        while x <= y:
            for px, py in ((cx + x, cy + y), (cx - x, cy + y),
                           (cx + x, cy - y), (cx - x, cy - y),
                           (cx + y, cy + x), (cx - y, cy + x),
                           (cx + y, cy - x), (cx - y, cy - x)):
                self.set(px, py, color)
            if d < 0:
                d += 2 * x + 3
            else:
                d += 2 * (x - y) + 5
                y -= 1
            x += 1

    def disc(self, cx, cy, r, color):
        """Filled circle via exact integer square roots."""
        for dy in range(-r, r + 1):
            dx = math.isqrt(r * r - dy * dy)
            self.hline(cx - dx, cy + dy, 2 * dx + 1, color)

    def fill_triangle(self, p1, p2, p3, color):
        (x1, y1), (x2, y2), (x3, y3) = sorted(
            (p1, p2, p3), key=lambda p: p[1])

        def edge_x(xa, ya, xb, yb, y):
            if yb == ya:
                return xa
            return xa + (xb - xa) * (y - ya) // (yb - ya)

        for y in range(y1, y3 + 1):
            if y < y2:
                xa = edge_x(x1, y1, x2, y2, y)
                xb = edge_x(x1, y1, x3, y3, y)
            else:
                xa = edge_x(x2, y2, x3, y3, y)
                xb = edge_x(x1, y1, x3, y3, y)
            if xa > xb:
                xa, xb = xb, xa
            self.hline(xa, y, xb - xa + 1, color)

    def glyph(self, x, y, char, scale, color):
        rows = FONT.get(char.upper(), FONT[" "])
        for r in range(7):
            bits = rows[r]
            for c in range(5):
                if bits >> (4 - c) & 1:
                    self.fill_rect(x + c * scale, y + r * scale,
                                   scale, scale, color)

    def text_width(self, text, scale):
        if not text:
            return 0
        return len(text) * 6 * scale - scale

    def draw_text(self, x, y, text, scale, color):
        for i, char in enumerate(text):
            self.glyph(x + i * 6 * scale, y, char, scale, color)

    def draw_centered(self, y, text, scale, color):
        x = (self.width - self.text_width(text, scale)) // 2
        self.draw_text(x, y, text, scale, color)

    def wrap(self, text, max_width, scale):
        lines, current = [], ""
        for word in text.split(" "):
            trial = word if not current else current + " " + word
            if self.text_width(trial, scale) <= max_width or not current:
                current = trial
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines


def png_chunk(kind, data):
    body = kind + data
    return (struct.pack(">I", len(data)) + body +
            struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF))


def write_png(path, canvas):
    raw = bytearray()
    stride = canvas.width * 3
    for y in range(canvas.height):
        raw.append(0)
        raw += canvas.pixels[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", canvas.width, canvas.height,
                       8, 2, 0, 0, 0)
    blob = (b"\x89PNG\r\n\x1a\n"
            + png_chunk(b"IHDR", ihdr)
            + png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + png_chunk(b"IEND", b""))
    with open(path, "wb") as fh:
        fh.write(blob)


# ---------------------------------------------------------------- icons

def draw_justice(cv, cx, cy):
    """Scales of justice inside a ring, for the lead story."""
    for r in (72, 71, 70):
        cv.circle(cx, cy, r, BLUE)
    cv.fill_rect(cx - 1, cy - 52, 3, 106, BLUE)
    cv.fill_rect(cx - 46, cy - 48, 92, 3, BLUE)
    for side in (-1, 1):
        px = cx + side * 46
        cv.thick_line(px, cy - 45, px - side * 18, cy - 26, BLUE)
        cv.thick_line(px, cy - 45, px + side * 18, cy - 26, BLUE)
        cv.fill_triangle((px - 18, cy - 26),
                         (px + 18, cy - 26), (px, cy - 8), GOLD)
    cv.disc(cx, cy - 47, 5, RED)
    cv.fill_rect(cx - 24, cy + 52, 48, 4, BLUE)
    cv.fill_rect(cx - 32, cy + 56, 64, 3, BLUE)


def draw_summit(cv, x, y):
    """Three flags over a skyline: the Shenzhen summit."""
    cv.fill_rect(x, y, 120, 120, PALE)
    cv.outline_rect(x, y, 120, 120, BLUE, 2)
    for bx, bh in ((8, 26), (28, 40), (48, 32), (68, 48), (88, 22)):
        cv.fill_rect(x + bx, y + 120 - bh, 16, bh, BLUE)
    for i, pole in enumerate((30, 60, 90)):
        cv.vline(x + pole, y + 18, 60, INK)
        fx, fy = x + pole - 10, y + 18
        if i == 0:
            for s in range(4):
                cv.fill_rect(fx, fy + s * 4, 20, 2,
                             RED if s % 2 == 0 else PAPER)
            cv.fill_rect(fx, fy, 8, 7, BLUE)
        elif i == 1:
            cv.fill_rect(fx, fy, 20, 14, RED)
            for sx, sy in ((3, 3), (9, 3), (3, 8), (9, 8)):
                cv.fill_rect(fx + sx, fy + sy, 2, 2, GOLD)
        else:
            cv.fill_rect(fx, fy, 20, 5, PAPER)
            cv.fill_rect(fx, fy + 5, 20, 4, BLUE)
            cv.fill_rect(fx, fy + 9, 20, 5, RED)


def draw_burst(cv, x, y):
    """Explosion burst: the missile in Poland."""
    cv.fill_rect(x, y, 120, 120, PALE)
    cv.outline_rect(x, y, 120, 120, RED, 2)
    cx, cy = x + 60, y + 60
    dirs = [(1, 0), (2, 1), (1, 1), (1, 2), (0, 1), (-1, 2),
            (-1, 1), (-2, 1), (-1, 0), (-2, -1), (-1, -1),
            (-1, -2), (0, -1), (1, -2), (1, -1), (2, -1)]
    for dx, dy in dirs:
        cv.thick_line(cx + dx * 8, cy + dy * 8,
                      cx + dx * 20, cy + dy * 20, RED)
    cv.disc(cx, cy, 11, RED)
    cv.disc(cx, cy, 5, GOLD)


def draw_quake(cv, x, y):
    """Andes peaks under a seismograph trace."""
    cv.fill_rect(x, y, 120, 120, PALE)
    cv.outline_rect(x, y, 120, 120, TEAL, 2)
    cv.fill_triangle((x + 8, y + 102), (x + 42, y + 56),
                     (x + 78, y + 102), TEAL)
    cv.fill_triangle((x + 58, y + 102), (x + 88, y + 70),
                     (x + 114, y + 102), TEAL)
    trace = [(8, 42), (25, 42), (32, 28), (40, 56), (48, 34),
             (55, 50), (66, 24), (74, 58), (82, 42), (112, 42)]
    for (ax, ay), (bx, by) in zip(trace, trace[1:]):
        cv.thick_line(x + ax, y + ay, x + bx, y + by, RED)


# ---------------------------------------------------------------- page

def draw_row(cv, top, kicker, headlines, body, icon):
    icon(cv, 48, top + 6)
    cv.draw_text(192, top + 8, kicker, 2, RED)
    y = top + 34
    for line in headlines:
        cv.draw_text(192, y, line, 3, INK)
        y += 26
    y += 6
    for line in cv.wrap(body, 780, 2):
        cv.draw_text(192, y, line, 2, INK)
        y += 20


def build_page():
    cv = Canvas(WIDTH, HEIGHT, PAPER)
    cv.outline_rect(28, 28, 968, 968, INK, 3)

    cv.draw_centered(48, "THE WORLD TODAY", 8, INK)
    cv.draw_text(48, 122, "VOL. II - NO. 325", 2, GREY)
    cv.draw_centered(122, "SATURDAY, 21 NOVEMBER 2026", 2, RED)
    cv.draw_text(774, 122, "PRICE: ONE DOLLAR", 2, GREY)
    cv.fill_rect(48, 160, 928, 4, INK)
    cv.fill_rect(48, 170, 928, 2, INK)

    cv.draw_text(48, 192, "LEAD · THE HAGUE", 2, RED)
    cv.draw_text(48, 216, "WORLD COURT RULES", 5, INK)
    cv.draw_text(48, 256, "MYANMAR COMMITTED", 5, INK)
    cv.draw_text(48, 296, "GENOCIDE", 5, INK)
    body = ("THE INTERNATIONAL COURT OF JUSTICE RULED MYANMAR "
            "COMMITTED GENOCIDE AGAINST THE ROHINGYA, IN A "
            "LANDMARK VERDICT.")
    y = 350
    for line in cv.wrap(body, 620, 2):
        cv.draw_text(48, y, line, 2, INK)
        y += 20
    draw_justice(cv, 858, 312)
    cv.fill_rect(48, 438, 928, 2, INK)

    draw_row(cv, 462, "DIPLOMACY · SHENZHEN",
             ["TRUMP, XI AND PUTIN", "MEET IN SHENZHEN"],
             "THE THREE LEADERS HELD A TRILATERAL SUMMIT ON THE "
             "APEC SIDELINES; INDIA TAKES NOTE.",
             draw_summit)
    cv.fill_rect(48, 606, 928, 2, INK)
    draw_row(cv, 618, "WAR · POLAND",
             ["RUSSIAN MISSILE CRASHES", "IN POLAND"],
             "WARSAW CALLS IT A PROVOCATION AS RUSSIA POUNDS "
             "UKRAINE ANEW.",
             draw_burst)
    cv.fill_rect(48, 762, 928, 2, INK)
    draw_row(cv, 774, "EARTHQUAKE · PERU",
             ["6.9 QUAKE SHAKES", "PERU'S ANDES"],
             "TREMORS FELT IN LIMA; NO CASUALTIES REPORTED.",
             draw_quake)

    cv.fill_rect(48, 922, 928, 2, INK)
    cv.draw_centered(940, "SOURCES: THE HINDU · DAWN · MANILA TIMES "
                          "· TIMES NOW", 2, GREY)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    page = build_page()
    write_png(os.path.join(out_dir, "entry.png"), page)


if __name__ == "__main__":
    main()
