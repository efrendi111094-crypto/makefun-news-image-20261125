#!/usr/bin/env python3
"""Wednesday 25 November 2026, drawn as one newspaper front page.

A deterministic, standard-library-only Python 3.13 program. It paints a
1024x1024 PNG at /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png)
that sums up the world news of Wednesday 25 November 2026: two oil
tankers hit mines and burn in the Strait of Hormuz, Washington proposes
new tariffs on 14 trading partners, the US economy prints 4.3% GDP
growth with October PCE inflation at 3.8%, Asian markets rout as the
Nasdaq slides toward a bear market, Gukesh and Sindarov draw game two
of the chess title match in 20 moves, China launches Shenzhou-24 with
the first Pakistani astronaut aboard, and thirty more stories, with a
date-checked box for yesterday's news.

Every headline and figure comes from reporting first published on
25 November 2026 (Reuters, AP, Just Security Early Edition, Zacks/BEA,
ChessBase, CMSA, IANS, FIDE), or from events that happen on that
Wednesday itself. Stories first reported on 24 November or earlier are
not presented as today's news: they sit in an explicit "LEFT OUT AS
OLDER NEWS" box, dated, and upcoming events sit in a "NOT YET" line.
Each story carries a source tag - CONFIRMED, REPORTED or FORECAST -
explained in the legend.

The picture is drawn, not pasted: a hand-built 5x7 bitmap typeface
stored as rows of hashes and dots, a small rasteriser (filled
rectangles, lines, discs, triangles, polygons) over an RGB buffer, and
a PNG writer built on zlib and struct. There is no network access, no
clock, no randomness, so the same source always produces the same PNG
bytes.

Layout, top to bottom: a navy masthead naming the date, a lead story
with a drawn Hormuz scene, three rows of illustrated cards (five, four
and four), a two-column "more today" briefs strip, a world map with
pins beside a Wednesday timeline, a by-the-numbers strip, the left-out
box, the not-yet line, and a sources footer.
"""

import os
import struct
import zlib
from pathlib import Path

# ---------------------------------------------------------------------------
# Page geometry and palette
# ---------------------------------------------------------------------------
W = 1024
H = 1024
MARGIN = 24                       # side margin
CW = W - 2 * MARGIN               # content width, 976

PAPER = (250, 246, 238)           # warm newsprint
INK = (18, 18, 20)                # near-black type
NAVY = (14, 28, 58)               # masthead band
NAVY_LT = (30, 48, 92)            # lighter navy
CRIMSON = (172, 32, 32)           # accent red
GOLD = (196, 146, 50)             # warm gold
GREY = (102, 98, 90)              # secondary type
RULE = (72, 68, 60)               # thin rules
SEA = (16, 96, 104)               # map sea
GREEN = (28, 104, 58)             # positive accent
SNOW = (252, 250, 244)
CREAM = (236, 228, 204)           # pale panel
SKY = (168, 198, 224)             # pale daytime sky
AMBER = (228, 134, 38)
LEAF = (44, 128, 68)
SLATE = (52, 58, 74)              # dark board squares
IVORY = (238, 230, 208)           # light board squares
FIRE = (224, 84, 24)              # flame orange
SMOKE = (88, 84, 80)
TEAL = (14, 110, 110)

# ---------------------------------------------------------------------------
# Bitmap typeface: 5 wide, 7 tall. '#' is ink, '.' is blank.
# ---------------------------------------------------------------------------
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
}

FONT.update({
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".....", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".....", "..##.", "..#.."),
    ":": (".....", "..#..", ".....", ".....", ".....", "..#..", "....."),
    ";": (".....", "..#..", ".....", ".....", ".....", "..##.", "..#.."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "'": ("..#..", "..#..", ".....", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "....#", "...#.", "...#.", "..#..", ".#...", "#...."),
    "%": ("#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "&": (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "#": (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    "*": (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    "<": ("...#.", "..#..", ".#...", "#....", ".#...", "..#..", "...#."),
    ">": (".#...", "..#..", "...#.", "....#", "...#.", "..#..", ".#..."),
    "[": (".###.", ".#...", ".#...", ".#...", ".#...", ".#...", ".###."),
    "]": (".###.", "...#.", "...#.", "...#.", "...#.", "...#.", ".###."),
    "@": (".###.", "#...#", "#.###", "#.#.#", "#.###", "#....", ".###."),
    "^": ("..#..", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "~": (".....", ".....", ".##.#", "#.#.#", ".....", ".....", "....."),
    "\\": ("#....", "#....", ".#...", "..#..", "...#.", "....#", "....#"),
    "|": ("..#..", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
})

# ---------------------------------------------------------------------------
# Canvas: an RGB buffer with tiny drawing primitives
# ---------------------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bytes(bg) * (w * h))

    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def hline(self, x, y, w, c):
        self.rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.rect(x, y, 1, h, c)

    def line(self, x0, y0, x1, y1, c):
        # Bresenham's line.
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.put(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c):
        # Filled circle.
        for yy in range(cy - r, cy + r + 1):
            dx = int((r * r - (yy - cy) * (yy - cy)) ** 0.5) if abs(yy - cy) <= r else 0
            self.rect(cx - dx, yy, 2 * dx + 1, 1, c)

    def ring(self, cx, cy, r, c):
        # Circle outline, one pixel thick.
        steps = max(8, int(6.28 * r))
        for k in range(steps):
            a = 6.283185307 * k / steps
            self.put(int(cx + r * _cos(a) + 0.5), int(cy + r * _sin(a) + 0.5), c)

    def tri(self, x0, y0, x1, y1, x2, y2, c):
        # Filled triangle via scanlines.
        pts = sorted(((x0, y0), (x1, y1), (x2, y2)), key=lambda p: p[1])
        (ax, ay), (bx, by), (cx, cy) = pts
        if ay == cy:
            return
        for y in range(ay, cy + 1):
            t1 = (y - ay) / (by - ay) if by != ay else 0.0
            t2 = (y - ay) / (cy - ay)
            xa = ax + (bx - ax) * t1 if y <= by else bx + (cx - bx) * ((y - by) / (cy - by) if cy != by else 0.0)
            xb = ax + (cx - ax) * t2
            if xa > xb:
                xa, xb = xb, xa
            self.rect(int(xa), y, int(xb) - int(xa) + 1, 1, c)

    def poly(self, points, c):
        # Filled polygon (convex-ish blobs) via scanlines.
        if len(points) < 3:
            return
        ys = [p[1] for p in points]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / (y1 - y0)
                    xs.append(x0 + (x1 - x0) * t)
            if len(xs) >= 2:
                xs.sort()
                self.rect(int(xs[0]), y, int(xs[-1]) - int(xs[0]) + 1, 1, c)

    def frame(self, x, y, w, h, c, t=1):
        self.rect(x, y, w, t, c)
        self.rect(x, y + h - t, w, t, c)
        self.rect(x, y, t, h, c)
        self.rect(x + w - t, y, t, h, c)

    def grain(self, x, y, w, h, amount=9):
        # Deterministic speckle: same (x, y) always gives the same delta.
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                v = (xx * 374761393 + yy * 668265263) & 0x7FFFFFFF
                v = (v ^ (v >> 13)) * 1274126177 & 0x7FFFFFFF
                d = (v % (2 * amount + 1)) - amount
                if d:
                    i = (yy * self.w + xx) * 3
                    for k in range(3):
                        nv = self.px[i + k] + d
                        self.px[i + k] = 0 if nv < 0 else (255 if nv > 255 else nv)


def _cos(a):
    # Cosine via Taylor series, good enough for ring placement.
    a = a % 6.283185307
    return 1 - a * a / 2 + a ** 4 / 24 - a ** 6 / 720


def _sin(a):
    a = a % 6.283185307
    return a - a ** 3 / 6 + a ** 5 / 120 - a ** 7 / 5040


# ---------------------------------------------------------------------------
# Text: glyph drawing, wrapping, paragraphs
# ---------------------------------------------------------------------------
def draw_glyph(cv, ch, x, y, scale, color):
    g = FONT.get(ch)
    if g is None:
        return
    for r, row in enumerate(g):
        for c, bit in enumerate(row):
            if bit == "#":
                cv.rect(x + c * scale, y + r * scale, scale, scale, color)


def draw_text(cv, s, x, y, scale, color):
    """Draw string s at (x, y); glyph cell is 5x7 times scale, 1px gap."""
    s = s.upper()
    cx = x
    step = 6 * scale
    for ch in s:
        if ch == " ":
            cx += step
            continue
        draw_glyph(cv, ch, cx, y, scale, color)
        cx += step
    return cx


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def wrap_words(text, max_chars):
    """Greedy word wrap into lines of at most max_chars characters."""
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= max_chars:
            cur += " " + w
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_para(cv, text, x, y, max_chars, scale, color, leading=None):
    """Draw a wrapped paragraph; return the y just below its last line."""
    if leading is None:
        leading = 7 * scale + 2
    lines = wrap_words(text, max_chars)
    for ln in lines:
        draw_text(cv, ln, x, y, scale, color)
        y += leading
    return y


def centre_text(cv, s, cx, y, scale, color):
    draw_text(cv, s, cx - text_width(s, scale) // 2, y, scale, color)


# ---------------------------------------------------------------------------
# PNG writer: zlib + struct, no external code
# ---------------------------------------------------------------------------
def _png_chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * stride:(y + 1) * stride]
    png = b"\x89PNG\r\n\x1a\n"
    png += _png_chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
    png += _png_chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += _png_chunk(b"IEND", b"")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(png)
    return len(png)


# ---------------------------------------------------------------------------
# Mini scenes: every illustration is drawn from rectangles, lines, discs
# ---------------------------------------------------------------------------
def draw_hormuz(cv, x, y, w, h):
    """Two tankers burning on a dusk sea, in the hero panel."""
    # Sky bands, dusk orange to deep navy.
    bands = [(238, 176, 96), (224, 138, 66), (196, 102, 62), (150, 74, 74),
             (96, 62, 88), (52, 48, 86)]
    for i, c in enumerate(bands):
        cv.rect(x, y + i * (h // 2) // 6, w, (h // 2) // 6 + 1, c)
    # Low sun.
    cv.disc(x + w - 70, y + 34, 16, (255, 214, 130))
    cv.disc(x + w - 70, y + 34, 11, (255, 232, 170))
    # Sea.
    cv.rect(x, y + h // 2, w, h - h // 2, (18, 52, 84))
    cv.rect(x, y + h // 2, w, 2, (120, 170, 200))
    for k in range(9):
        wx = x + 12 + k * 44
        wy = y + h // 2 + 12 + (k % 3) * 14
        cv.hline(wx, wy, 26, (90, 140, 180))
    # Tanker one, listing to port.
    hx, hy = x + 26, y + h - 62
    cv.rect(hx, hy, 150, 22, (28, 28, 34))
    cv.rect(hx + 8, hy - 14, 60, 14, (120, 40, 36))
    cv.rect(hx + 76, hy - 14, 58, 14, (90, 90, 96))
    cv.rect(hx + 138, hy - 26, 12, 26, (200, 200, 204))
    cv.rect(hx + 8, hy - 26, 18, 12, (240, 120, 40))
    # Flames and smoke over tanker one.
    cv.tri(hx + 22, hy - 26, hx + 30, hy - 52, hx + 40, hy - 26, FIRE)
    cv.tri(hx + 40, hy - 26, hx + 50, hy - 60, hx + 60, hy - 26, (240, 160, 40))
    cv.tri(hx + 58, hy - 26, hx + 66, hy - 48, hx + 76, hy - 26, FIRE)
    cv.disc(hx + 34, hy - 62, 7, SMOKE)
    cv.disc(hx + 46, hy - 74, 9, (70, 66, 62))
    cv.disc(hx + 58, hy - 86, 8, SMOKE)
    # Tanker two, further off, bow down.
    hx2, hy2 = x + w - 190, y + h - 46
    cv.rect(hx2, hy2, 130, 18, (24, 24, 30))
    cv.rect(hx2 + 10, hy2 - 10, 46, 10, (96, 32, 30))
    cv.rect(hx2 + 62, hy2 - 10, 44, 10, (74, 74, 80))
    cv.rect(hx2 + 112, hy2 - 20, 10, 20, (180, 180, 184))
    cv.tri(hx2 + 24, hy2 - 10, hx2 + 32, hy2 - 34, hx2 + 42, hy2 - 10, FIRE)
    cv.tri(hx2 + 44, hy2 - 10, hx2 + 54, hy2 - 40, hx2 + 64, hy2 - 10, (240, 160, 40))
    cv.disc(hx2 + 40, hy2 - 44, 6, SMOKE)
    cv.disc(hx2 + 52, hy2 - 54, 7, (70, 66, 62))
    # Fire glow on the water.
    cv.rect(hx + 10, hy + 22, 130, 3, (220, 110, 50))
    cv.rect(hx2 + 8, hy2 + 18, 110, 3, (200, 96, 44))


def draw_rocket(cv, x, y, w, h):
    cv.rect(x, y, w, h, (12, 16, 38))
    for k in range(14):
        px = x + 6 + (k * 37) % (w - 12)
        py = y + 4 + (k * 23) % (h - 8)
        cv.put(px, py, SNOW)
        cv.put(px + 1, py, SNOW)
    # Rocket body, sized to the 40px art strip.
    bx = x + w // 2
    cv.rect(bx - 7, y + 8, 14, 16, SNOW)
    cv.tri(bx - 7, y + 8, bx + 7, y + 8, bx, y + 1, CRIMSON)
    cv.rect(bx - 7, y + 24, 14, 3, CRIMSON)
    cv.tri(bx - 13, y + 22, bx - 7, y + 22, bx - 7, y + 29, CRIMSON)
    cv.tri(bx + 7, y + 22, bx + 13, y + 22, bx + 7, y + 29, CRIMSON)
    cv.disc(bx, y + 16, 3, SKY)
    # Flame.
    cv.tri(bx - 5, y + 27, bx + 5, y + 27, bx, y + 38, FIRE)
    cv.tri(bx - 3, y + 27, bx + 3, y + 27, bx, y + 34, (240, 200, 60))
    # Ground line and station ring.
    cv.hline(x + 4, y + h - 2, w - 8, GREY)
    cv.ring(x + w - 22, y + 12, 7, GOLD)


def draw_chess(cv, x, y, w, h):
    cv.rect(x, y, w, h, CREAM)
    sq = 9
    ox, oy = x + 6, y + 2
    for r in range(4):
        for c in range(4):
            col = IVORY if (r + c) % 2 == 0 else SLATE
            cv.rect(ox + c * sq, oy + r * sq, sq, sq, col)
    # White king and black knight, drawn as simple crowns.
    cv.disc(ox + 4, oy + 4, 3, SNOW)
    cv.rect(ox + 1, oy + 1, 7, 2, GOLD)
    cv.disc(ox + 31, oy + 31, 3, INK)
    cv.rect(ox + 28, oy + 28, 7, 2, CRIMSON)
    # Score boxes on the right.
    cv.rect(x + 50, y + 2, w - 56, 10, NAVY)
    draw_text(cv, "1-1", x + 54, y + 3, 1, SNOW)
    cv.rect(x + 50, y + 14, w - 56, 10, SNOW)
    draw_text(cv, "20 MOVES", x + 54, y + 15, 1, INK)
    cv.rect(x + 50, y + 26, w - 56, 10, (226, 214, 180))
    draw_text(cv, "GAME 2", x + 54, y + 27, 1, INK)


def draw_chart_down(cv, x, y, w, h):
    cv.rect(x, y, w, h, (16, 22, 44))
    cv.hline(x + 6, y + h - 6, w - 12, (90, 110, 150))
    cv.vline(x + 6, y + 4, h - 10, (90, 110, 150))
    pts = [(x + 8, y + 8), (x + 26, y + 11), (x + 44, y + 10),
           (x + 62, y + 16), (x + 80, y + 15), (x + 98, y + 20),
           (x + 116, y + 19), (x + 134, y + 25), (x + 152, y + 27),
           (x + 170, y + 31)]
    for i in range(len(pts) - 1):
        cv.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], CRIMSON)
        cv.line(pts[i][0], pts[i][1] + 1, pts[i + 1][0], pts[i + 1][1] + 1, CRIMSON)
    for px, py in pts:
        cv.disc(px, py, 2, (255, 120, 100))
    draw_text(cv, "-6.16%", x + w - 52, y + 4, 1, (255, 150, 130))


def draw_bars(cv, x, y, w, h):
    cv.rect(x, y, w, h, (232, 226, 200))
    base = y + h - 8
    vals = [(12, GREEN), (18, GREEN), (24, GREEN), (16, AMBER), (8, CRIMSON)]
    labels = ["GDP", "PCE", "INC", "DUR", "JOB"]
    for i, (v, c) in enumerate(vals):
        bx = x + 8 + i * 36
        cv.rect(bx, base - v, 22, v, c)
    cv.hline(x + 6, base, w - 12, INK)
    for i, lab in enumerate(labels):
        draw_text(cv, lab, x + 10 + i * 36, base + 2, 1, GREY)
    draw_text(cv, "4.3%", x + 10, y + 2, 1, GREEN)


def draw_chip(cv, x, y, w, h):
    cv.rect(x, y, w, h, (20, 26, 52))
    cx, cy = x + w // 2, y + h // 2
    cv.rect(cx - 16, cy - 14, 32, 28, (36, 44, 84))
    cv.frame(cx - 16, cy - 14, 32, 28, GOLD, 2)
    cv.rect(cx - 7, cy - 6, 14, 12, (120, 200, 240))
    for k in range(4):
        px = cx - 12 + k * 8
        cv.vline(px, cy - 20, 6, GOLD)
        cv.vline(px, cy + 14, 6, GOLD)
        py = cy - 10 + k * 7
        cv.hline(cx - 24, py, 8, GOLD)
        cv.hline(cx + 16, py, 8, GOLD)
    draw_text(cv, "NVDA", x + 6, y + 4, 1, SNOW)
    cv.tri(x + w - 26, y + 6, x + w - 14, y + 6, x + w - 20, y + 16, CRIMSON)


def draw_refinery(cv, x, y, w, h):
    cv.rect(x, y, w, h, (232, 210, 170))
    base = y + h - 4
    cv.hline(x, base, w, INK)
    # Distillation towers, sized to the 40px art strip.
    for tx, th in ((x + 14, 16), (x + 40, 22), (x + 96, 14)):
        cv.rect(tx, base - th, 16, th, (120, 118, 112))
        cv.rect(tx, base - th, 16, 3, (90, 88, 84))
    cv.rect(x + 66, base - 12, 22, 12, (150, 146, 138))
    # Flames.
    cv.tri(x + 18, base - 16, x + 22, base - 28, x + 26, base - 16, FIRE)
    cv.tri(x + 44, base - 22, x + 48, base - 33, x + 52, base - 22, (240, 160, 40))
    cv.tri(x + 100, base - 14, x + 104, base - 24, x + 108, base - 14, FIRE)
    cv.disc(x + 48, base - 36, 4, SMOKE)
    draw_text(cv, "RAS TANURA", x + 118, y + 4, 1, CRIMSON)


def draw_cricket(cv, x, y, w, h):
    cv.rect(x, y, w, h, (26, 92, 52))
    # Pitch strip.
    cv.rect(x, y + h - 8, w, 8, (210, 190, 150))
    # Stumps.
    for k in range(3):
        cv.vline(x + 16 + k * 5, y + h - 26, 18, (240, 220, 170))
    cv.hline(x + 16, y + h - 28, 12, (240, 220, 170))
    # Bat mid-swing, kept inside the 40px strip.
    cv.line(x + 118, y + 8, x + 88, y + 28, (214, 178, 120))
    cv.line(x + 119, y + 8, x + 89, y + 28, (214, 178, 120))
    cv.line(x + 88, y + 28, x + 72, y + 34, (120, 84, 50))
    # Ball flying.
    cv.disc(x + 150, y + 12, 5, CRIMSON)
    cv.disc(x + 150, y + 12, 2, SNOW)
    cv.line(x + 138, y + 18, x + 130, y + 24, SNOW)
    cv.line(x + 142, y + 22, x + 136, y + 28, SNOW)
    # Score box.
    cv.rect(x + 8, y + 4, 62, 14, SNOW)
    draw_text(cv, "204* 53", x + 12, y + 7, 1, INK)


def draw_boat(cv, x, y, w, h):
    cv.rect(x, y, w, h, SKY)
    cv.disc(x + w - 26, y + 12, 9, (255, 226, 150))
    # Sea.
    cv.rect(x, y + h // 2, w, h - h // 2, SEA)
    for k in range(4):
        cv.hline(x + 8 + k * 46, y + h // 2 + 8 + (k % 2) * 12, 30, (140, 200, 210))
    # Overcrowded boat.
    bx, by = x + 30, y + h // 2 - 4
    cv.poly([(bx, by), (bx + 120, by), (bx + 108, by + 16), (bx + 12, by + 16)], (96, 60, 40))
    for k in range(9):
        px = bx + 12 + k * 12
        cv.disc(px, by - 4, 4, (240, 120, 60) if k % 2 else (40, 90, 160))
    draw_text(cv, "2,100 IN A DAY", x + 8, y + 4, 1, NAVY)


def draw_globe(cv, x, y, w, h):
    cv.rect(x, y, w, h, (210, 226, 238))
    cx, cy = x + w // 2, y + h // 2
    cv.disc(cx, cy, 17, SEA)
    cv.ring(cx, cy, 17, NAVY)
    cv.line(cx - 17, cy, cx + 17, cy, (140, 200, 210))
    cv.line(cx, cy - 17, cx, cy + 17, (140, 200, 210))
    # Rough continents.
    cv.poly([(cx - 11, cy - 9), (cx - 4, cy - 10), (cx - 1, cy - 3), (cx - 8, cy - 1)], LEAF)
    cv.poly([(cx + 1, cy - 7), (cx + 10, cy - 9), (cx + 11, cy - 1), (cx + 4, cy + 1)], LEAF)
    cv.poly([(cx - 7, cy + 4), (cx + 1, cy + 6), (cx - 1, cy + 11), (cx - 10, cy + 8)], LEAF)
    # Pins.
    for px, py in ((cx - 8, cy - 6), (cx + 7, cy - 4), (cx - 3, cy + 7)):
        cv.disc(px, py, 2, CRIMSON)
        cv.disc(px, py, 1, SNOW)


def draw_satellite(cv, x, y, w, h):
    cv.rect(x, y, w, h, (12, 16, 38))
    for k in range(16):
        px = x + 6 + (k * 41) % (w - 12)
        py = y + 4 + (k * 29) % (h - 8)
        cv.put(px, py, SNOW)
    cx, cy = x + w // 2, y + h // 2
    cv.rect(cx - 30, cy - 4, 22, 8, (90, 140, 220))
    cv.rect(cx + 8, cy - 4, 22, 8, (90, 140, 220))
    cv.rect(cx - 8, cy - 7, 16, 14, (200, 200, 210))
    cv.disc(cx, cy, 3, GOLD)
    cv.line(cx - 30, cy - 8, cx + 30, cy + 8, (140, 180, 230))
    draw_text(cv, "1,000,000", x + 6, y + 4, 1, SNOW)


def draw_tariff(cv, x, y, w, h):
    cv.rect(x, y, w, h, (226, 220, 200))
    draw_text(cv, "14 PARTNERS", x + 8, y + 2, 1, CRIMSON)
    cv.line(x + 8, y + 12, x + 90, y + 12, CRIMSON)
    # Container ship, sized to the 40px art strip.
    cv.rect(x, y + h - 10, w, 10, SEA)
    cv.rect(x + 16, y + h - 22, 150, 12, (30, 30, 36))
    cols = [(CRIMSON), (GOLD), (TEAL), (NAVY_LT), (LEAF)]
    for i, c in enumerate(cols):
        cv.rect(x + 22 + i * 28, y + 14, 24, 12, c)
    cv.rect(x + 150, y + 14, 12, 12, (200, 200, 204))


def draw_hostage(cv, x, y, w, h):
    cv.rect(x, y, w, h, (232, 224, 200))
    # Supermarket block, sized to the 40px art strip.
    cv.rect(x + 12, y + 4, 110, 18, (200, 60, 50))
    cv.rect(x + 12, y + 22, 110, 4, SNOW)
    draw_text(cv, "EXITO", x + 18, y + 9, 1, SNOW)
    # Doors open, people out.
    cv.rect(x + 60, y + 26, 14, 10, NAVY)
    for k in range(4):
        px = x + 30 + k * 26
        cv.disc(px, y + 32, 3, (40, 90, 160) if k % 2 else LEAF)
    cv.disc(x + w - 22, y + 10, 6, GREEN)
    draw_text(cv, "FREED", x + w - 46, y + 22, 1, GREEN)


def draw_drone(cv, x, y, w, h):
    cv.rect(x, y, w, h, (40, 44, 60))
    # Night sky, refinery below, sized to the 40px art strip.
    cv.rect(x, y + h - 6, w, 6, (24, 24, 30))
    for tx in (x + 20, x + 60, x + 120):
        cv.rect(tx, y + h - 22, 14, 16, (90, 88, 84))
    cv.tri(x + 24, y + h - 22, x + 27, y + h - 32, x + 30, y + h - 22, FIRE)
    cv.tri(x + 124, y + h - 22, x + 127, y + h - 30, x + 130, y + h - 22, FIRE)
    # Drone silhouette.
    cx, cy = x + w // 2, y + 12
    cv.rect(cx - 10, cy - 3, 20, 6, (200, 200, 210))
    cv.hline(cx - 18, cy - 6, 36, (200, 200, 210))
    cv.disc(cx - 18, cy - 6, 3, (220, 220, 230))
    cv.disc(cx + 18, cy - 6, 3, (220, 220, 230))
    cv.disc(cx, cy + 8, 2, CRIMSON)
    draw_text(cv, "2 REFINERIES", x + 8, y + 2, 1, SNOW)


def draw_mine(cv, x, y, w, h):
    cv.rect(x, y, w, h, (232, 226, 210))
    # Gold-mine hillside.
    cv.poly([(x, y + h), (x + w // 2, y + 8), (x + w, y + h)], (150, 120, 70))
    cv.poly([(x, y + h), (x + 30, y + 30), (x + 70, y + h)], (120, 92, 52))
    # Tunnel mouth.
    cv.disc(x + w // 2, y + h - 12, 9, INK)
    # Rescue lamp.
    cv.disc(x + 20, y + 12, 4, GOLD)
    cv.line(x + 20, y + 12, x + 34, y + 26, GOLD)
    draw_text(cv, "TOLL 6", x + w - 52, y + 4, 1, CRIMSON)


# ---------------------------------------------------------------------------
# The day's news. Every item was first reported, or happened, on
# Wednesday 25 November 2026. [C] = CONFIRMED, [R] = REPORTED,
# [F] = FORECAST. Older items live in LEFT_OUT, never in the main grid.
# ---------------------------------------------------------------------------
HERO = {
    "kicker": "LEAD  |  STRAIT OF HORMUZ  |  [C]",
    "headline": ["TWO TANKERS HIT MINES,", "BURN IN THE STRAIT OF HORMUZ"],
    "body": ("Iran's Revolutionary Guard says the two vessels struck naval "
             "mines while using an unauthorised route through the world's "
             "busiest oil chokepoint. No casualty toll is given. Traders "
             "brace for disruption: a fifth of seaborne crude passes "
             "through the strait. Tehran says it stays open to talks on "
             "lifting sanctions."),
}

CARDS = [
    {"art": "tariff", "kicker": "TRADE  |  WASHINGTON", "tag": "[C]",
     "head": "US PROPOSES TARIFFS ON 14 PARTNERS",
     "body": "Section 301 probe after an 8-month inquiry into excess capacity. China faces the highest rates."},
    {"art": "bars", "kicker": "US ECONOMY  |  DATA DUMP", "tag": "[C]",
     "head": "GDP 4.3%, PCE 3.8%: HOT DATA",
     "body": "Q3 growth revised up from 3.4%. Core PCE 3.3% tops forecast. Claims fall to 189,000. Income jumps 0.7%."},
    {"art": "chart", "kicker": "MARKETS  |  THE ROUT", "tag": "[C]",
     "head": "NASDAQ NEARS BEAR MARKET",
     "body": "Nasdaq falls 2% on Wednesday, near 20% below its October peak. KOSPI plunges 6.16%, Nikkei drops 2.78%."},
    {"art": "chip", "kicker": "NVIDIA  |  THE COMEBACK", "tag": "[C]",
     "head": "BOOKER PROBES HUANG RETURN",
     "body": "Top Senate antitrust Democrat demands answers on the CEO's return. The DOJ ran no probe first, sources say. Shares slide 8%."},
    {"art": "chess", "kicker": "CHESS  |  GENEVA", "tag": "[C]",
     "head": "GAME 2: A 20-MOVE DRAW",
     "body": "Gukesh's London System meets Sindarov's 7...Qb6. Threefold repetition ends it in 1 hr 57 min. Match level at 1-1."},
    {"art": "rocket", "kicker": "SPACE  |  CHINA", "tag": "[C]",
     "head": "FIRST PAKISTANI IN SPACE",
     "body": "Shenzhou-24 lifts off at dawn and docks with Tiangong in 3.5 hours. Muhammad Zeeshan Ali is the first foreign guest aboard."},
    {"art": "refinery", "kicker": "YEMEN  |  SAUDI ARABIA", "tag": "[R]",
     "head": "HOUTHIS HIT RAS TANURA",
     "body": "Yemen's Houthis say they struck Saudi Arabia's Ras Tanura refinery, causing fires. A rocket also hits Jazan port."},
    {"art": "drone", "kicker": "UKRAINE  |  RUSSIA", "tag": "[C]",
     "head": "DRONES SET 2 REFINERIES ABLAZE",
     "body": "Ukrainian drones hit Rosneft's Syzran and Kuibyshev plants. One killed. 145 drones downed overnight."},
    {"art": "street", "kicker": "GAZA  |  ISRAEL-HAMAS WAR", "tag": "[C]",
     "head": "ISRAEL KILLS HAMAS COLONEL",
     "body": "Mohammad Abuelouf, who ran Hamas interior security, is killed with his wife and two children, Gaza medics say."},
    {"art": "globe", "kicker": "PACIFIC  |  CANBERRA", "tag": "[C]",
     "head": "SOLOMONS SIGN CANBERRA PACT",
     "body": "Australia and Solomon Islands sign a treaty barring any foreign military or security base on the islands."},
    {"art": "cricket", "kicker": "CRICKET  |  DOHA", "tag": "[C]",
     "head": "SOORYAVANSHI 204 OFF 53",
     "body": "India A's teenager smashes 28 sixes against UAE in the Rising Stars Asia Cup - a white-ball record innings."},
    {"art": "boat", "kicker": "MIGRATION  |  SPAIN", "tag": "[C]",
     "head": "RECORD DAY IN CANARIES",
     "body": "More than 2,100 migrants reach Spain's Canary Islands in 24 hours, a single-day record. 28,103 so far this year."},
    {"art": "hostage", "kicker": "COLOMBIA  |  CARTAGENA", "tag": "[C]",
     "head": "HOSTAGES FREED IN CARTAGENA",
     "body": "Security forces storm an Exito supermarket and free all remaining hostages. One captor is killed in the raid."},
]

BRIEFS = [
    ("SUDAN", "RSF drone strikes kill 19 civilians and wound 20 in two cities.", "[C]"),
    ("POPE", "Leo XIV laments the COP31 talks failing to reach a deal.", "[C]"),
    ("SYRIA", "IS attack kills 2 security men and wounds 5 in Hasaka.", "[C]"),
    ("NIGER", "Saudi national kidnapped by suspected IS militants.", "[R]"),
    ("NIGERIA", "At least 30 killed in land-dispute attacks in Niger state.", "[R]"),
    ("OPEC+", "Output capacity review due by year-end; ministers meet 29 Nov.", "[C]"),
    ("POLAND", "Seeks a permanent US base after 2 incursions in 4 days.", "[C]"),
    ("GERMANY", "Q3 GDP final due; Merz calls Russia a growing threat.", "[C]"),
    ("AUSTRALIA", "October CPI released as the rate path stays in focus.", "[C]"),
    ("FED", "Beige Book at 2pm ET; Bailey testifies in London.", "[C]"),
    ("CHINA", "Official sentenced to death for leaking 100 state secrets.", "[R]"),
    ("JAPAN", "Factory PMI 53.7; Tokyo eyes the No. 3 AI power spot.", "[C]"),
    ("KYIV", "Zelenskyy to appeal to Congress if no deal by year-end.", "[R]"),
    ("UN", "Chief warns AI is revolutionising warfare.", "[C]"),
    ("NILE", "Egypt and Sudan agree to protect water rights.", "[C]"),
    ("SPACEX", "US greenlights a plan for 1,000,000 satellites.", "[R]"),
    ("MICROSOFT", "'Code Red' after a historic outage, sources say.", "[R]"),
    ("CYBER", "CrowdStrike buys Zscaler in a $44bn deal.", "[R]"),
    ("CYBER", "Decathlon breach exposes 130,000 customers.", "[R]"),
    ("INDIA", "$1.2bn plan to build critical equipment at home.", "[C]"),
    ("PAKISTAN", "Fatima Sana named captain for West Indies tour.", "[C]"),
    ("HOCKEY", "India beat Japan 4-0 and reach world No. 5.", "[C]"),
    ("BOGOR", "Mine toll rises to 6; about 20 miners still trapped.", "[C]"),
    ("UCL", "Pochettino's Man Utd debut at Sporting leads the night.", "[C]"),
]

NUMBERS = [
    ("2", "TANKERS HIT"),
    ("14", "TARIFF PARTNERS"),
    ("4.3%", "US GDP"),
    ("3.8%", "OCT PCE"),
    ("189K", "JOBLESS CLAIMS"),
    ("-6.16%", "KOSPI"),
    ("204", "RUNS OFF 53"),
    ("2,100", "MIGRANTS, 1 DAY"),
    ("19", "KILLED IN SUDAN"),
    ("1M", "SATELLITES"),
]

TIMELINE = [
    ("04:56", "SHENZHOU-24 DOCKS WITH TIANGONG"),
    ("13:30", "US DATA DUMP: PCE, GDP, CLAIMS"),
    ("14:00", "CHESS GAME 2 BEGINS IN GENEVA"),
    ("15:57", "GAME 2 DRAWN AFTER 20 MOVES"),
    ("19:00", "FED BEIGE BOOK; UCL NIGHT KICKS OFF"),
]

LEFT_OUT = ("LEFT OUT AS OLDER NEWS  |  HUAWEI GUILTY VERDICT (TUE 24 NOV) - "
            "MISS UNIVERSE: BARRETO CROWNED (TUE 24 NOV) - RIYADH TOWER ATTACK, "
            "11 HURT (TUE) - DOW FIRST CLOSE ABOVE 50,000 (TUE) - DELL RECORD Q3 "
            "(TUE) - EL CHAPO ISIDRO CAPTURED (20 NOV) - UCL TUE: REAL 5-1 PSV, "
            "ARSENAL 1-1 DORTMUND, CITY 2-2 NAPOLI - NBA: TATUM 41, CELTICS "
            "131-116 WIZARDS (TUE)")

NOT_YET = ("NOT YET  |  THANKSGIVING THU 26 NOV: US MARKETS SHUT, MACY'S PARADE "
           "08:30 ET - OPEC+ MEETS SUN 29 NOV - CHESS GAME 3 THU - INDIA V NZ "
           "2ND TEST FRI 27 NOV, CHRISTCHURCH")

FOOTER = ("SOURCES: REUTERS - AP - JUST SECURITY - ZACKS / BEA - CHESSBASE - "
          "CMSA - IANS - FIDE  |  ALL STORIES FIRST REPORTED OR HAPPENING "
          "25 NOV 2026  |  LEGEND: [C] CONFIRMED  [R] REPORTED  [F] FORECAST")

STORY_COUNT = 1 + len(CARDS) + len(BRIEFS)   # hero + cards + briefs = 38


def draw_street(cv, x, y, w, h):
    """A city street at dusk, smoke over the rooftops."""
    cv.rect(x, y, w, h, (222, 206, 178))
    # Sky and smoke.
    cv.disc(x + 40, y + 10, 8, SMOKE)
    cv.disc(x + 56, y + 6, 6, (110, 106, 100))
    cv.disc(x + 140, y + 12, 7, SMOKE)
    # Rooftops, sized to the 40px art strip.
    for bx, bh in ((x + 8, 20), (x + 44, 26), (x + 84, 17), (x + 120, 23), (x + 152, 18)):
        cv.rect(bx, y + h - bh - 6, 30, bh, (120, 100, 80))
        cv.rect(bx, y + h - bh - 6, 30, 3, (90, 74, 58))
    cv.rect(x, y + h - 6, w, 6, (70, 66, 60))
    # Windows lit.
    for k in range(6):
        wx = x + 14 + k * 28
        cv.rect(wx, y + h - 18, 6, 7, (255, 210, 110))
    draw_text(cv, "GAZA CITY", x + 8, y + 4, 1, CRIMSON)


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
ART = {
    "tariff": draw_tariff, "bars": draw_bars, "chart": draw_chart_down,
    "chip": draw_chip, "chess": draw_chess, "rocket": draw_rocket,
    "refinery": draw_refinery, "drone": draw_drone, "street": draw_street,
    "globe": draw_globe, "cricket": draw_cricket, "boat": draw_boat,
    "hostage": draw_hostage, "mine": draw_mine,
}


def draw_masthead(cv):
    cv.rect(0, 0, W, 78, NAVY)
    cv.rect(0, 76, W, 2, GOLD)
    draw_text(cv, "THE WORLD IN ONE DAY", MARGIN, 12, 3, SNOW)
    draw_text(cv, "WEDNESDAY 25 NOVEMBER 2026", W - MARGIN - text_width("WEDNESDAY 25 NOVEMBER 2026", 2), 14, 2, GOLD)
    draw_text(cv, "38 SOURCED STORIES FROM 7 REGIONS  |  ALL EVENTS FIRST REPORTED OR HAPPENING 25 NOV 2026",
              MARGIN, 50, 1, (200, 190, 160))
    draw_text(cv, "LEGEND: [C] CONFIRMED  [R] REPORTED  [F] FORECAST",
              W - MARGIN - text_width("LEGEND: [C] CONFIRMED  [R] REPORTED  [F] FORECAST", 1), 50, 1, (200, 190, 160))


def draw_hero(cv, y, h):
    cv.frame(MARGIN, y, CW, h, RULE, 1)
    cv.rect(MARGIN + 1, y + 1, 400, h - 2, SKY)
    draw_hormuz(cv, MARGIN + 1, y + 1, 400, h - 2)
    tx = MARGIN + 416
    tw = CW - 416 - 16
    draw_text(cv, HERO["kicker"], tx, y + 10, 1, CRIMSON)
    hy = y + 28
    for ln in HERO["headline"]:
        draw_text(cv, ln, tx, hy, 2, INK)
        hy += 18
    by = draw_para(cv, HERO["body"], tx, hy + 6, 88, 1, INK, leading=10)
    cv.hline(tx, y + h - 34, tw, RULE)
    draw_text(cv, "2 TANKERS  |  NAVAL MINES  |  NO TOLL GIVEN  |  1/5 OF SEABORNE CRUDE",
              tx, y + h - 24, 1, GREY)
    draw_text(cv, "SOURCE: IRGC STATEMENT, VIA JUST SECURITY", tx, y + h - 13, 1, GREY)
    return y + h


def draw_card(cv, card, x, y, w, h):
    cv.frame(x, y, w, h, RULE, 1)
    ART[card["art"]](cv, x + 1, y + 1, w - 2, 40)
    draw_text(cv, card["kicker"], x + 8, y + 46, 1, CRIMSON)
    lines = wrap_words(card["head"], 28)
    hy = y + 57
    for ln in lines[:2]:
        draw_text(cv, ln, x + 8, hy, 1, INK)
        hy += 9
    body = wrap_words(card["body"], 28)
    max_body = 4 if len(lines) > 1 else 5
    by = hy + 3
    for ln in body[:max_body]:
        draw_text(cv, ln, x + 8, by, 1, GREY)
        by += 9
    draw_text(cv, card["tag"] + "  " + card["kicker"].split("|")[0].strip(),
              x + 8, y + h - 11, 1, GREY)


def draw_cards(cv, y):
    row_h = 132
    gap = 6
    idx = 0
    for n in (5, 4, 4):
        w = (CW - (n - 1) * 8) // n
        total = n * w + (n - 1) * 8
        x0 = MARGIN + (CW - total) // 2
        for i in range(n):
            draw_card(cv, CARDS[idx], x0 + i * (w + 8), y, w, row_h)
            idx += 1
        y += row_h + gap
    return y - gap


def draw_briefs(cv, y, h):
    draw_text(cv, "MORE TODAY", MARGIN, y, 1, INK)
    cv.hline(MARGIN + text_width("MORE TODAY", 1) + 8, y + 3, CW - text_width("MORE TODAY", 1) - 8, RULE)
    col_w = (CW - 16) // 2
    rows = 12
    for ci in range(2):
        bx = MARGIN + ci * (col_w + 16)
        for ri in range(rows):
            item = BRIEFS[ci * rows + ri]
            line = item[0] + "  " + item[1] + " " + item[2]
            draw_text(cv, line[:77], bx, y + 12 + ri * 9, 1, INK)
    return y + 12 + rows * 9


def draw_map(cv, x, y, w, h):
    cv.rect(x, y, w, h, SEA)
    cv.frame(x, y, w, h, RULE, 1)
    # Stylised continents as blobs.
    cv.poly([(x + 20, y + 22), (x + 90, y + 8), (x + 150, y + 16), (x + 140, y + 44),
             (x + 80, y + 50), (x + 30, y + 40)], (74, 128, 84))
    cv.poly([(x + 120, y + 52), (x + 150, y + 56), (x + 158, y + 78), (x + 130, y + 82),
             (x + 118, y + 66)], (74, 128, 84))
    cv.poly([(x + 220, y + 18), (x + 260, y + 10), (x + 280, y + 30), (x + 250, y + 44),
             (x + 222, y + 34)], (74, 128, 84))
    cv.poly([(x + 240, y + 48), (x + 290, y + 44), (x + 310, y + 62), (x + 280, y + 80),
             (x + 244, y + 72)], (74, 128, 84))
    cv.poly([(x + 320, y + 12), (x + 430, y + 8), (x + 460, y + 30), (x + 440, y + 52),
             (x + 360, y + 50), (x + 322, y + 34)], (74, 128, 84))
    cv.poly([(x + 420, y + 62), (x + 452, y + 60), (x + 458, y + 76), (x + 428, y + 80)], (74, 128, 84))
    draw_text(cv, "WORLD MAP - WHERE IT HAPPENED", x + 6, y + 4, 1, SNOW)
    pins = [("HORMUZ", 0.70, 0.42, 1), ("GENEVA", 0.56, 0.34, 1),
            ("KYIV", 0.63, 0.30, -1), ("GAZA", 0.64, 0.44, 1),
            ("CANBERRA", 0.94, 0.72, -1), ("CARTAGENA", 0.33, 0.52, 1),
            ("BOGOR", 0.84, 0.60, 1), ("DOHA", 0.69, 0.46, -1),
            ("CANARIES", 0.50, 0.40, 1), ("WASHINGTON", 0.32, 0.36, 1)]
    for name, fx, fy, side in pins:
        px = x + int(fx * w)
        py = y + int(fy * h)
        cv.disc(px, py, 3, CRIMSON)
        cv.disc(px, py, 1, SNOW)
        lx = px + 5 if side > 0 else px - 5 - text_width(name, 1)
        ly = py - 3 if side > 0 else py + 5
        draw_text(cv, name, lx, ly, 1, SNOW)


def draw_timeline(cv, x, y, w, h):
    draw_text(cv, "WEDNESDAY IN FIVE MOMENTS (UTC)", x, y, 1, INK)
    cv.hline(x, y + 10, w, RULE)
    for i, (t, txt) in enumerate(TIMELINE):
        ry = y + 16 + i * 14
        draw_text(cv, t, x, ry, 1, CRIMSON)
        draw_text(cv, txt, x + 44, ry, 1, INK)
        if i < len(TIMELINE) - 1:
            cv.vline(x + 12, ry + 8, 6, GOLD)


def draw_numbers(cv, y, h):
    cv.rect(MARGIN, y, CW, h, NAVY)
    n = len(NUMBERS)
    iw = CW // n
    for i, (val, lab) in enumerate(NUMBERS):
        cx = MARGIN + i * iw
        centre_text(cv, val, cx + iw // 2, y + 5, 2, GOLD)
        centre_text(cv, lab, cx + iw // 2, y + 21, 1, SNOW)
        if i:
            cv.vline(cx, y + 4, h - 8, NAVY_LT)
    return y + h


def draw_leftout(cv, y, h):
    cv.rect(MARGIN, y, CW, h, (246, 232, 214))
    cv.frame(MARGIN, y, CW, h, CRIMSON, 1)
    draw_text(cv, "LEFT OUT AS OLDER NEWS", MARGIN + 8, y + 5, 1, CRIMSON)
    draw_para(cv, LEFT_OUT.split("|", 1)[1].strip(), MARGIN + 8, y + 16, 158, 1, GREY, leading=9)
    return y + h


def draw_bottom(cv, y):
    y = draw_para(cv, NOT_YET, MARGIN, y, 160, 1, INK, leading=9)
    y += 2
    y = draw_para(cv, FOOTER, MARGIN, y, 160, 1, GREY, leading=9)
    return y


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    cv = Canvas(W, H, PAPER)
    draw_masthead(cv)
    y = 84
    y = draw_hero(cv, y, 168)
    y += 6
    y = draw_cards(cv, y)
    y += 6
    y = draw_briefs(cv, y, 0)
    y += 6
    map_y = y
    draw_map(cv, MARGIN, map_y, 476, 86)
    draw_timeline(cv, MARGIN + 492, map_y, CW - 492, 86)
    y = map_y + 86 + 4
    y = draw_numbers(cv, y, 32)
    y += 4
    y = draw_leftout(cv, y, 48)
    y += 4
    y = draw_bottom(cv, y)
    cv.grain(0, 0, W, H, amount=6)
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    size = write_png(cv, os.path.join(out, "entry.png"))
    print(f"wrote {size} bytes, final y={y}")
    assert y <= H, f"layout overflow: final y {y} > {H}"


if __name__ == "__main__":
    main()
