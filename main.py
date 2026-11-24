#!/usr/bin/env python3
"""THE WORLD IN ONE PICTURE -- Tuesday, 24 November 2026.

A program that draws a one-page newspaper front page summing up the
world news of Tuesday 24 November 2026 and writes it to
/output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).

Pure Python 3 standard library only: no network, no clock, no random
numbers, no fonts from disk. The picture is drawn pixel by pixel with
a small 5x7 bitmap font defined below, and encoded as a PNG by hand
(zlib + struct), so two runs write byte-identical files.

Stories on the page (each verified as happening or first reported on
24 November 2026):
  - Chess: World Championship Game 1, Gukesh vs Sindarov, Geneva.
  - Space: Ariane 6 launches 36 Amazon Leo satellites from Kourou.
  - Sky: Beaver Supermoon peaks and passes the Pleiades.
  - Faith: 557th Guru Nanak Jayanti on Kartik Purnima.
  - Tech: Cisco and OpenAI launch the Shirudo project.
"""

import binascii
import math
import os
import struct
import zlib

# ---------------------------------------------------------------- font
# A 5x7 bitmap font, drawn from scratch. '#' is a set pixel, '.' empty.
# Only capitals, digits and common punctuation: the page is set in
# newspaper capitals throughout, which suits a front page.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "&": (".###.", "#...#", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "=": (".....", ".....", ".###.", ".....", ".###.", ".....", "....."),
    "*": (".....", ".#.#.", ".###.", "#####", ".###.", ".#.#.", "....."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
}

ALIASES = {"\u2014": "-", "\u2019": "'", "\u201c": '"', "\u201d": '"'}


def glyph(ch):
    """Bitmap rows for one character, with a few curly fallbacks."""
    if ch in FONT:
        return FONT[ch]
    if ch in ALIASES:
        return FONT[ALIASES[ch]]
    return FONT[" "]


def text_width(text, scale):
    return len(text) * 6 * scale


def wrap_text(text, max_width, scale):
    """Greedy word wrap; returns a list of lines fitting max_width."""
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split(" ")
        line = ""
        for word in words:
            trial = word if not line else line + " " + word
            if text_width(trial, scale) <= max_width or not line:
                line = trial
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines


# -------------------------------------------------------------- canvas
PAPER = (247, 239, 216)   # warm cream newsprint
PANEL = (251, 246, 233)   # slightly lighter panel
INK = (26, 26, 26)
NAVY = (20, 38, 77)
NAVY2 = (46, 74, 122)
GOLD = (201, 162, 39)
RED = (176, 42, 48)
GREY = (90, 90, 84)
WHITE = (255, 255, 255)
CREAM = (240, 217, 168)
SKY = (168, 205, 235)
MOON = (245, 233, 184)
ORANGE = (232, 120, 40)
YELLOW = (244, 196, 66)


class Canvas:
    def __init__(self, width, height, background):
        self.width = width
        self.height = height
        self.pixels = bytearray(background) * (width * height)

    def set_pixel(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = (y * self.width + x) * 3
            self.pixels[i] = color[0]
            self.pixels[i + 1] = color[1]
            self.pixels[i + 2] = color[2]

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            base = (yy * self.width + x) * 3
            for xx in range(w):
                i = base + xx * 3
                if 0 <= x + xx < self.width and 0 <= yy < self.height:
                    self.pixels[i] = color[0]
                    self.pixels[i + 1] = color[1]
                    self.pixels[i + 2] = color[2]

    def frame(self, x, y, w, h, color, thickness=2):
        self.rect(x, y, w, thickness, color)
        self.rect(x, y + h - thickness, w, thickness, color)
        self.rect(x, y, thickness, h, color)
        self.rect(x + w - thickness, y, thickness, h, color)

    def line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.set_pixel(x, y, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def thick_line(self, x0, y0, x1, y1, color, thickness=3):
        for ox in range(-(thickness // 2), thickness // 2 + 1):
            for oy in range(-(thickness // 2), thickness // 2 + 1):
                self.line(x0 + ox, y0 + oy, x1 + ox, y1 + oy, color)

    def circle(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)

    def ring(self, cx, cy, r, color, thickness=2):
        for t in range(thickness):
            rr = r - t
            for a in range(360):
                rad = math.radians(a)
                self.set_pixel(cx + int(rr * math.cos(rad)),
                               cy + int(rr * math.sin(rad)), color)

    def polygon(self, points, color):
        """Scanline fill for a simple polygon given as [(x, y), ...]."""
        ys = [p[1] for p in points]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.rect(int(xs[j]), y, max(1, int(xs[j + 1]) - int(xs[j])), 1, color)

    # -- text ------------------------------------------------------
    def draw_char(self, x, y, ch, scale, color):
        rows = glyph(ch)
        for r, row in enumerate(rows):
            for c, bit in enumerate(row):
                if bit == "#":
                    self.rect(x + c * scale, y + r * scale, scale, scale, color)

    def draw_text(self, x, y, text, scale, color):
        for ch in text:
            self.draw_char(x, y, ch, scale, color)
            x += 6 * scale

    def draw_text_center(self, cx, y, text, scale, color):
        self.draw_text(cx - text_width(text, scale) // 2, y, text, scale, color)

    def draw_block(self, x, y, text, scale, color, max_width, line_gap=4):
        lines = wrap_text(text, max_width, scale)
        for line in lines:
            self.draw_text(x, y, line, scale, color)
            y += 7 * scale + line_gap
        return y


# -------------------------------------------------------------- icons
def draw_chessboard(c, x, y, cell=32):
    """8x8 board with a white king, a black king and two pawns."""
    light = (239, 224, 184)
    dark = NAVY2
    c.frame(x - 3, y - 3, cell * 8 + 6, cell * 8 + 6, INK, 3)
    for row in range(8):
        for col in range(8):
            color = light if (row + col) % 2 == 0 else dark
            c.rect(x + col * cell, y + row * cell, cell, cell, color)

    def king(cx, cy, body, cross):
        c.circle(cx, cy - 2, 11, INK)
        c.circle(cx, cy - 2, 9, body)
        c.rect(cx - 2, cy - 18, 4, 10, cross)
        c.rect(cx - 6, cy - 14, 12, 4, cross)
        c.rect(cx - 9, cy + 6, 18, 5, body)
        c.rect(cx - 9, cy + 6, 18, 1, INK)

    def pawn(cx, cy, body):
        c.circle(cx, cy - 3, 7, INK)
        c.circle(cx, cy - 3, 5, body)
        c.rect(cx - 7, cy + 4, 14, 4, body)
        c.rect(cx - 7, cy + 4, 14, 1, INK)

    # White king on e1, black king on e8, pawns mid-board.
    king(x + 4 * cell + cell // 2, y + 7 * cell + cell // 2, WHITE, RED)
    king(x + 4 * cell + cell // 2, y + 0 * cell + cell // 2, INK, WHITE)
    pawn(x + 2 * cell + cell // 2, y + 6 * cell + cell // 2, WHITE)
    pawn(x + 5 * cell + cell // 2, y + 1 * cell + cell // 2, INK)


def draw_rocket(c, x, y, w, h):
    cx = x + w // 2
    c.draw_text(x + 4, y + h - 16, "10:45 UTC", 2, GREY)
    # stars
    for sx, sy in ((x + 8, y + 12), (x + w - 14, y + 22), (x + 20, y + 44),
                   (x + w - 26, y + 58)):
        c.rect(sx - 1, sy, 3, 1, GOLD)
        c.rect(sx, sy - 1, 1, 3, GOLD)
    # flame
    c.polygon([(cx - 9, y + 108), (cx + 9, y + 108), (cx, y + 138)], ORANGE)
    c.polygon([(cx - 5, y + 108), (cx + 5, y + 108), (cx, y + 126)], YELLOW)
    # fins
    c.polygon([(cx - 14, y + 84), (cx - 14, y + 108), (cx - 30, y + 112)], RED)
    c.polygon([(cx + 14, y + 84), (cx + 14, y + 108), (cx + 30, y + 112)], RED)
    # body
    c.rect(cx - 14, y + 34, 28, 76, WHITE)
    c.frame(cx - 14, y + 34, 28, 76, INK, 2)
    # nose
    c.polygon([(cx - 14, y + 34), (cx + 14, y + 34), (cx, y + 10)], RED)
    # window
    c.circle(cx, y + 58, 8, INK)
    c.circle(cx, y + 58, 6, SKY)
    # motion lines
    for ly in (y + 44, y + 64, y + 84):
        c.rect(x + 2, ly, 12, 2, GREY)
        c.rect(x + w - 14, ly + 8, 12, 2, GREY)


def draw_moon(c, x, y, w, h):
    cx = x + w // 2 - 16
    cy = y + h // 2 - 4
    c.circle(cx, cy, 44, GOLD)
    c.circle(cx, cy, 40, MOON)
    for ox, oy, r in ((-14, -10, 7), (10, 6, 9), (-2, 16, 5), (16, -16, 4)):
        c.circle(cx + ox, cy + oy, r, (214, 196, 138))
    # The Seven Sisters: a small cluster of gold stars, clear of the
    # moon disc in the upper right corner of the panel.
    for sx, sy in ((x + w - 28, y + 12), (x + w - 14, y + 22), (x + w - 34, y + 32),
                   (x + w - 20, y + 42), (x + w - 8, y + 38), (x + w - 28, y + 52),
                   (x + w - 14, y + 56)):
        c.rect(sx - 2, sy, 5, 1, GOLD)
        c.rect(sx, sy - 2, 1, 5, GOLD)
    c.draw_text(x + 4, y + h - 16, "14:54 UTC", 2, GREY)


def draw_temple(c, x, y, w, h):
    cx = x + w // 2
    base_y = y + 118
    # minarets
    for mx in (x + 8, x + w - 16):
        c.rect(mx, y + 62, 8, base_y - (y + 62), NAVY2)
        c.circle(mx + 4, y + 58, 6, GOLD)
    # dome
    c.circle(cx, base_y - 28, 36, GOLD)
    c.rect(cx - 36, base_y - 28, 72, 28, PAPER)
    c.rect(cx - 36, base_y - 28, 72, 3, INK)
    # finial + flag
    c.line(cx, base_y - 64, cx, base_y - 78, INK)
    c.polygon([(cx, base_y - 78), (cx + 16, base_y - 73), (cx, base_y - 68)], RED)
    # base
    c.rect(x + 12, base_y, w - 24, 34, CREAM)
    c.frame(x + 12, base_y, w - 24, 34, INK, 2)
    # arched door
    c.rect(cx - 10, base_y + 12, 20, 22, INK)
    c.circle(cx, base_y + 12, 10, INK)
    # side windows
    c.rect(x + 22, base_y + 10, 8, 12, NAVY2)
    c.rect(x + w - 30, base_y + 10, 8, 12, NAVY2)


def draw_shield(c, x, y, w, h):
    cx = x + w // 2
    cy = y + h // 2 - 6
    pts = [(cx - 38, cy - 44), (cx + 38, cy - 44), (cx + 38, cy - 2),
           (cx, cy + 48), (cx - 38, cy - 2)]
    c.polygon(pts, NAVY)
    pts2 = [(cx - 30, cy - 36), (cx + 30, cy - 36), (cx + 30, cy - 2),
            (cx, cy + 38), (cx - 30, cy - 2)]
    c.polygon(pts2, NAVY2)
    c.thick_line(cx - 16, cy - 2, cx - 4, cy + 12, WHITE, 5)
    c.thick_line(cx - 4, cy + 12, cx + 20, cy - 20, WHITE, 5)


# -------------------------------------------------------------- page
def draw_page(c):
    w = c.width
    # --- masthead -------------------------------------------------
    c.rect(0, 0, w, 148, NAVY)
    c.draw_text_center(w // 2, 40, "THE WORLD IN ONE PICTURE", 5, WHITE)
    c.draw_text_center(w // 2, 96, "TUESDAY, 24 NOVEMBER 2026", 3, GOLD)
    c.rect(0, 148, w, 6, RED)

    # --- lead story: chess ---------------------------------------
    c.rect(28, 170, 968, 300, PANEL)
    c.frame(28, 170, 968, 300, INK, 3)
    draw_chessboard(c, 52, 194, 32)
    tx = 368
    c.draw_text(tx, 190, "CHESS - GENEVA", 2, RED)
    c.draw_text(tx, 216, "THE YOUNGEST TITLE", 4, INK)
    c.draw_text(tx, 252, "MATCH IN HISTORY", 4, INK)
    c.draw_text(tx, 288, "BEGINS TODAY", 4, INK)
    c.draw_block(tx, 336,
                 "GUKESH DEFENDS HIS CROWN AGAINST SINDAROV IN GENEVA. "
                 "GAME 1 STARTS 3PM CET. SINDAROV HAS WHITE. $2.5M AT "
                 "STAKE. THE YOUNGEST WORLD TITLE MATCH EVER - BOTH "
                 "PLAYERS ARE 20.",
                 2, INK, 968 - tx - 24, line_gap=5)

    # --- 2x2 grid -------------------------------------------------
    panels = [
        (28, 486, "SPACE - KOUROU", "ROCKET LIFTS 36 SATELLITES INTO ORBIT",
         "ARIANE 6 LOFTS 36 AMAZON LEO SATELLITES FROM KOUROU, A DAY "
         "AFTER A DELAY.", draw_rocket),
        (524, 486, "SKY - WORLDWIDE", "BEAVER SUPERMOON MEETS THE SEVEN SISTERS",
         "THE FULL MOON PEAKS AT 14:54 UTC AND BRUSHES PAST THE "
         "PLEIADES BEFORE DAWN.", draw_moon),
        (28, 692, "FAITH - INDIA", "557TH GURU NANAK JAYANTI",
         "SIKHS MARK GURU NANAK'S BIRTH, FROM THE GOLDEN TEMPLE TO "
         "NANKANA SAHIB.", draw_temple),
        (524, 692, "TECH - TODAY", "CISCO AND OPENAI LAUNCH 'SHIRUDO'",
         "OPEN SOURCE TO DEFEND AGENTIC AI AT MACHINE SPEED, "
         "ANNOUNCED TODAY.", draw_shield),
    ]
    for px, py, kicker, headline, body, icon in panels:
        c.rect(px, py, 472, 190, PANEL)
        c.frame(px, py, 472, 190, INK, 2)
        icon(c, px + 12, py + 14, 124, 162)
        tx2 = px + 148
        c.draw_text(tx2, py + 14, kicker, 2, RED)
        c.draw_block(tx2, py + 38, headline, 3, INK, 472 - 148 - 16, line_gap=2)
        # body sits below the headline block (headline wraps to <= 3 lines)
        c.draw_block(tx2, py + 122, body, 2, INK, 472 - 148 - 16, line_gap=3)

    # --- bottom strip --------------------------------------------
    c.rect(0, 900, w, 96, NAVY)
    c.draw_text_center(w // 2, 918,
                       "ALSO TODAY: THANKSGIVING IS TWO DAYS AWAY IN THE USA.",
                       2, WHITE)
    c.draw_text_center(w // 2, 952,
                       "EVERY STORY HERE HAPPENED OR WAS FIRST REPORTED "
                       "ON 24 NOVEMBER 2026.",
                       2, GOLD)


# -------------------------------------------------------------- png
def png_bytes(c):
    raw = bytearray()
    for y in range(c.height):
        raw.append(0)  # filter: none
        start = y * c.width * 3
        raw += c.pixels[start:start + c.width * 3]

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", c.width, c.height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    canvas = Canvas(1024, 1024, PAPER)
    draw_page(canvas)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(png_bytes(canvas))
    print("wrote", path)


if __name__ == "__main__":
    main()
