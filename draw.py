#!/usr/bin/env python3
"""Render the one-image front page for Friday 20 November 2026.

Pure PIL: every shape, chart, flag and map is drawn with primitives in this
file.  No network, no clock, no randomness -- two runs produce the same bytes.
"""

import glob
import os
import sys

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- palette ---

SIZE = 1024
PAPER = "#F7F1E3"
NAVY = "#14213D"
RED = "#B42318"
INK = "#1A1A1A"
GREY = "#5A5A5A"
RULE = "#C9BFA8"
SEA = "#DCE7EC"
LAND = "#A9B7A2"
LAND_EDGE = "#7B8A76"
CONFIRMED = "#1F6B4A"
REPORTED = "#8A5A00"
WHITE = "#FFFFFF"

MARGIN = 22
LEFT = MARGIN
RIGHT = SIZE - MARGIN
INNER = RIGHT - LEFT
GUTTER = 8

# ------------------------------------------------------------------ fonts ---

_WANT = {
    "serif_bold": ("DejaVuSerif-Bold.ttf", "DejaVuSerif-Bold", "NotoSerif-Bold"),
    "sans": ("DejaVuSans.ttf", "DejaVuSans", "NotoSans-Regular"),
    "sans_bold": ("DejaVuSans-Bold.ttf", "DejaVuSans-Bold", "NotoSans-Bold"),
}

_FONT_PATH = {}
_FONT_CACHE = {}


def _find_font(kind):
    """Locate a real TTF on disk; never fall back to the bitmap default."""
    if kind in _FONT_PATH:
        return _FONT_PATH[kind]
    names = _WANT[kind]
    roots = [
        "/usr/share/fonts/truetype/dejavu",
        "/usr/share/fonts/truetype/noto",
        "/usr/share/fonts",
        "/usr/local/share/fonts",
        os.path.expanduser("~/.fonts"),
    ]
    picked = None
    for name in names:
        for root in roots:
            hit = os.path.join(root, name)
            if os.path.isfile(hit):
                picked = hit
                break
            for found in sorted(glob.glob(os.path.join(root, "**", name + "*"), recursive=True)):
                if found.lower().endswith((".ttf", ".otf")):
                    picked = found
                    break
            if picked:
                break
        if picked:
            break
    if picked is None:
        for found in sorted(glob.glob("/usr/share/fonts/**/*.ttf", recursive=True)):
            if "DejaVuSans" in found or "NotoSans" in found:
                picked = found
                break
    if picked is None:
        raise SystemExit("no usable TTF font found on this machine")
    _FONT_PATH[kind] = picked
    return picked


def font(kind, size):
    key = (kind, size)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(_find_font(kind), size)
    return _FONT_CACHE[key]


# ------------------------------------------------------------------ text ---

_warnings = []
_boxes = []
_in_art = False
_clip = None


def advance(fnt, s):
    return fnt.getbbox(s)[2]


def wrap(text, fnt, max_w):
    """Greedy word wrap measured with getbbox; never returns an over-wide line."""
    lines = []
    current = ""
    for word in text.split():
        trial = (current + " " + word).strip()
        if advance(fnt, trial) <= max_w or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def put(d, xy, text, fnt, fill, anchor="la", tag=None):
    d.text(xy, text, font=fnt, fill=fill, anchor=anchor)
    if not _in_art:
        x0, y0, x1, y1 = d.textbbox(xy, text, font=fnt, anchor=anchor)
        _boxes.append((x0, y0, x1, y1, tag or text[:24], _clip))


def clip_to(box):
    """Text drawn from here on is audited against this box."""
    global _clip
    _clip = box


def paragraph(d, x, y, text, fnt, fill, max_w, leading, max_lines=None, tag=""):
    lines = wrap(text, fnt, max_w)
    if max_lines is not None and len(lines) > max_lines:
        _warnings.append("%s: %d lines > %d" % (tag, len(lines), max_lines))
        lines = lines[:max_lines]
    for line in lines:
        if advance(fnt, line) > max_w + 0.5:
            _warnings.append("%s: line too wide (%d > %d)" % (tag, advance(fnt, line), max_w))
        put(d, (x, y), line, fnt, fill, tag=tag)
        y += leading
    return y


def tracked(d, cx, y, text, fnt, fill, extra=2.4):
    """Letter-spaced centred text (used for the masthead kicker)."""
    widths = [advance(fnt, ch) for ch in text]
    total = sum(widths) + extra * max(0, len(text) - 1)
    x = cx - total / 2.0
    for ch, wd in zip(text, widths):
        d.text((x, y), ch, font=fnt, fill=fill)
        x += wd + extra


def fit_headline(text, max_w, start=15, floor=9):
    """Shrink a headline until its longest word fits; never below the 9px rule."""
    size = start
    while size > floor:
        f = font("serif_bold", size)
        if max(advance(f, w) for w in text.split()) <= max_w:
            return f
        size -= 1
    return font("serif_bold", floor)


# ------------------------------------------------------------------ rules ---

def hline(d, x0, x1, y, fill=RULE, width=1):
    d.line([(x0, y), (x1, y)], fill=fill, width=width)


def double_rule(d, x0, x1, y, gap=3, fill=NAVY):
    hline(d, x0, x1, y, fill, 2)
    hline(d, x0, x1, y + gap, fill, 1)


def vrule(d, x, y0, y1, fill=RULE, width=1):
    d.line([(x, y0), (x, y1)], fill=fill, width=width)


# ---------------------------------------------------------- card furniture ---

def badge(d, x, y, label, bg):
    f = font("sans_bold", 9)
    w = advance(f, label) + 10
    d.rounded_rectangle([x, y, x + w, y + 13], radius=3, fill=bg)
    put(d, (x + 5, y + 2), label, f, WHITE)
    return x + w


def status_badge(d, x_right, y, status):
    f = font("sans_bold", 9)
    w = advance(f, status) + 10
    return badge(d, x_right - w, y, status, CONFIRMED if status == "CONFIRMED" else REPORTED)


def art_band(page, box, painter):
    """Draw an illustration into its own image so it can never spill over."""
    global _in_art
    x0, y0, x1, y1 = box
    band = Image.new("RGB", (max(1, x1 - x0), max(1, y1 - y0)), PAPER)
    _in_art = True
    try:
        painter(band, (0, 0, band.width, band.height))
    finally:
        _in_art = False
    page.paste(band, (x0, y0))


def audit():
    """Report text that escapes its box, the page, or collides with a neighbour."""
    problems = []
    for x0, y0, x1, y1, tag, clip in _boxes:
        if x0 < 16 or y0 < 16 or x1 > SIZE - 16 or y1 > SIZE - 16:
            problems.append("outside page: %r %s" % (tag, (round(x0), round(y0), round(x1), round(y1))))
        if clip is not None:
            cx0, cy0, cx1, cy1 = clip
            if x0 < cx0 - 0.5 or y0 < cy0 - 0.5 or x1 > cx1 + 0.5 or y1 > cy1 + 0.5:
                problems.append("escapes box: %r %s vs %s" % (
                    tag, (round(x0), round(y0), round(x1), round(y1)),
                    (round(cx0), round(cy0), round(cx1), round(cy1))))
    ordered = sorted(_boxes, key=lambda b: (b[1], b[0]))
    for i in range(len(ordered)):
        ax0, ay0, ax1, ay1, atag, aclip = ordered[i]
        for j in range(i + 1, len(ordered)):
            bx0, by0, bx1, by1, btag, bclip = ordered[j]
            if by0 >= ay1:
                break
            if aclip is not None and bclip is not None and aclip != bclip:
                continue
            ox = min(ax1, bx1) - max(ax0, bx0)
            oy = min(ay1, by1) - max(ay0, by0)
            if ox > 1.5 and oy > 1.5:
                problems.append("overlap %r / %r (%.1fx%.1f)" % (atag, btag, ox, oy))
    return problems


# ------------------------------------------------------------ illustrations ---

def _star(d, cx, cy, r, fill, points=8, inner=0.42):
    import math

    pts = []
    for i in range(points * 2):
        ang = math.pi * i / points - math.pi / 2
        rad = r if i % 2 == 0 else r * inner
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    d.polygon(pts, fill=fill)


def art_kyiv(im, b):
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    for i, shade in enumerate(("#080E20", "#0E1730", "#152244", "#1C2B52")):
        d.rectangle([x0, y0 + i * h // 4, x1, y0 + (i + 1) * h // 4], fill=shade)
    river = y0 + int(h * 0.66)
    d.rectangle([x0, river, x1, y1], fill="#0C1830")
    for k in range(3):
        yy = river + 4 + k * 4
        d.line([(x0 + 6 + k * 5, yy), (x1 - 12 - k * 7, yy)], fill="#1D3357")
    bank = [(0.02, 0.66), (0.05, 0.44), (0.09, 0.50), (0.12, 0.36), (0.15, 0.47),
            (0.19, 0.30), (0.22, 0.45), (0.26, 0.38), (0.30, 0.52), (0.34, 0.42),
            (0.38, 0.55), (0.43, 0.48), (0.48, 0.58), (0.53, 0.50), (0.58, 0.60),
            (0.64, 0.46), (0.70, 0.56), (0.76, 0.50), (0.82, 0.58), (0.88, 0.47),
            (0.94, 0.55), (0.99, 0.52)]
    for i in range(len(bank) - 1):
        fx, fh = bank[i]
        nx, nh = bank[i + 1]
        bx = x0 + fx * w
        bw = max(4, (nx - fx) * w + 1)
        top = min(y0 + fh * h, river - 6)
        d.rectangle([bx, top, bx + bw, river], fill="#060B18")
        for wy in range(int(top) + 3, river - 2, 5):
            d.point((bx + 2, wy), fill="#C9A227")
    for i, (bx, span) in enumerate(((0.10, 0.22), (0.40, 0.24), (0.70, 0.24))):
        sx = x0 + bx * w
        ex = sx + span * w
        d.line([(sx, river + 6), (ex, river + 6)], fill="#5A6A8A", width=2)
        for px in range(int(sx) + 3, int(ex), 9):
            d.line([(px, river + 6), (px, river + 12)], fill="#44536F")
    trails = [(0.06, 0.10, 0.20, 0.34), (0.30, 0.04, 0.36, 0.28), (0.58, 0.08, 0.62, 0.30),
              (0.80, 0.02, 0.72, 0.26), (0.92, 0.12, 0.86, 0.30)]
    for sx, sy, ex, ey in trails:
        d.line([(x0 + sx * w, y0 + sy * h), (x0 + ex * w, y0 + ey * h)], fill="#8A93A8")
        d.line([(x0 + ex * w, y0 + ey * h), (x0 + (ex + 0.03) * w, y0 + (ey + 0.05) * h)],
               fill="#E07A3A", width=2)
    for cx, cy, r in ((0.21, 0.36, 6), (0.37, 0.29, 5), (0.63, 0.31, 6), (0.86, 0.31, 5)):
        _star(d, x0 + cx * w, y0 + cy * h, r, "#E4572E")
        _star(d, x0 + cx * w, y0 + cy * h, r * 0.55, "#F2C14E", points=6)


def art_akvan(im, b):
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    d.rectangle([x0, y0, x1, y1], fill="#BFD8E0")
    coast = [(0.00, 0.00), (0.34, 0.00), (0.38, 0.18), (0.33, 0.34), (0.36, 0.50),
             (0.30, 0.62), (0.33, 0.78), (0.28, 1.00), (0.00, 1.00)]
    d.polygon([(x0 + fx * w, y0 + fy * h) for fx, fy in coast], fill=LAND, outline=LAND_EDGE)
    d.line([(x0 + 0.34 * w, y0), (x0 + 0.30 * w, y1)], fill="#8FA08A", width=1)
    cx, cy = x0 + 0.68 * w, y0 + 0.52 * h
    for i, rad in enumerate((0.46, 0.33, 0.20)):
        col = "#F2F7F9" if i % 2 == 0 else "#6E8FA6"
        start = 20 + i * 40
        d.arc([cx - rad * w, cy - rad * h * 1.7, cx + rad * w, cy + rad * h * 1.7],
              start, start + 250, fill=col, width=2)
    d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill="#FFFFFF", outline="#3E5C74")
    for k in range(9):
        rx = x0 + (0.40 + 0.062 * k) * w
        d.line([(rx, y0 + 0.08 * h), (rx - 3, y0 + 0.22 * h)], fill="#5C7C90")
    d.line([(x0 + 0.05 * w, y0 + 0.30 * h), (x0 + 0.26 * w, y0 + 0.30 * h)], fill="#6B7F63")


def art_ai_rout(im, b):
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    d.rectangle([x0, y0, x1, y1], fill="#FBF7EC")
    for i in range(1, 4):
        yy = y0 + h * i / 4.0
        d.line([(x0 + 6, yy), (x1 - 6, yy)], fill="#E4DCC8")
    d.line([(x0 + 6, y1 - 8), (x1 - 6, y1 - 8)], fill="#9C9280")
    d.line([(x0 + 6, y0 + 4), (x0 + 6, y1 - 8)], fill="#9C9280")
    candles = [(0.08, 0.30, 0.42, 0.52, 0.36), (0.20, 0.36, 0.50, 0.60, 0.42),
               (0.32, 0.44, 0.58, 0.70, 0.50), (0.44, 0.52, 0.68, 0.82, 0.60),
               (0.56, 0.62, 0.78, 0.92, 0.70), (0.68, 0.70, 0.86, 0.98, 0.80),
               (0.80, 0.80, 0.94, 1.02, 0.90)]
    for fx, top, bot, wick_top, wick_bot in candles:
        cxx = x0 + fx * w
        d.line([(cxx + 4, y0 + wick_top * h), (cxx + 4, y0 + wick_bot * h)], fill="#7A1A12")
        d.rectangle([cxx, y0 + top * h, cxx + 8, y0 + bot * h], fill="#B42318")
    pts = [(x0 + 0.08 * w, y0 + 0.30 * h), (x0 + 0.32 * w, y0 + 0.44 * h),
           (x0 + 0.56 * w, y0 + 0.62 * h), (x0 + 0.86 * w, y0 + 0.86 * h)]
    d.line(pts, fill="#B42318", width=2)
    ax, ay = x0 + 0.86 * w, y0 + 0.86 * h
    d.line([(ax, ay), (ax - 2, ay - 14)], fill="#B42318", width=3)
    d.polygon([(ax - 2, ay + 3), (ax - 8, ay - 9), (ax + 4, ay - 9)], fill="#B42318")
    put(d, (x0 + 10, y0 + 5), "NASDAQ -5.3%", font("sans_bold", 9), "#B42318")


def art_cop31(im, b):
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    d.rectangle([x0, y0, x1, y1], fill="#E8EFEA")
    r = int(h * 0.36)
    gx, gy = x0 + int(w * 0.24), y0 + h // 2
    d.ellipse([gx - r, gy - r, gx + r, gy + r], fill="#9CC3D5", outline="#3E5C74")
    d.arc([gx - r // 2, gy - r, gx + r // 2, gy + r], 0, 360, fill="#3E5C74")
    d.line([(gx - r, gy), (gx + r, gy)], fill="#3E5C74")
    d.arc([gx - r, gy - r // 2, gx + r, gy + r // 2], 0, 360, fill="#3E5C74")
    tx = x0 + int(w * 0.52)
    d.rectangle([tx, y0 + 6, tx + 5, y1 - 6], fill="#B42318")
    d.ellipse([tx - 3, y1 - 11, tx + 8, y1], fill="#B42318")
    d.line([(tx + 2, y0 + 12), (tx + 2, y1 - 10)], fill="#F7F1E3")
    for i, col in enumerate(("#B42318", "#14213D", "#1F6B4A")):
        fx = x0 + int(w * 0.66) + i * 13
        d.line([(fx, y0 + 6), (fx, y1 - 5)], fill="#5A5A5A")
        d.polygon([(fx, y0 + 6), (fx + 11, y0 + 10), (fx, y0 + 15)], fill=col)


def art_poland(im, b):
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    d.rectangle([x0, y0, x1, y1], fill="#EDE6D3")
    by = y0 + int(h * 0.62)
    for bx in range(int(x0 + 4), int(x1), 8):
        d.line([(bx, by), (bx + 4, by)], fill="#8C8574", width=2)
    d.line([(x0 + 4, by), (x1 - 4, by)], fill="#B9B0A0")
    d.arc([x0 + int(w * 0.10), y0 - int(h * 0.55), x0 + int(w * 0.95), y0 + int(h * 1.25)],
          250, 20, fill="#B42318", width=2)
    d.polygon([(x0 + int(w * 0.80), y0 + int(h * 0.34)),
               (x0 + int(w * 0.80) + 6, y0 + int(h * 0.52)),
               (x0 + int(w * 0.80) - 6, y0 + int(h * 0.52))], fill="#B42318")
    d.ellipse([x0 + int(w * 0.80) - 4, y0 + int(h * 0.52) - 4,
               x0 + int(w * 0.80) + 4, y0 + int(h * 0.52) + 4], fill="#B42318")
    _star(d, x0 + int(w * 0.55), y0 + int(h * 0.30), 5, "#E4572E")


def art_gta(im, b):
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    for i, shade in enumerate(("#F3B27A", "#E98B5A", "#C9624A", "#7A3B52")):
        d.rectangle([x0, y0 + i * h // 4, x1, y0 + (i + 1) * h // 4], fill=shade)
    d.ellipse([x0 + int(w * 0.62), y0 + int(h * 0.10), x0 + int(w * 0.80), y0 + int(h * 0.42)],
              fill="#F7E3A1")
    base = y0 + int(h * 0.80)
    towers = [(0.05, 0.30, 0.09), (0.15, 0.44, 0.10), (0.26, 0.22, 0.07),
              (0.34, 0.36, 0.11), (0.46, 0.18, 0.08), (0.55, 0.40, 0.12)]
    for fx, fh, fw in towers:
        bx = x0 + fx * w
        d.rectangle([bx, base - fh * h, bx + fw * w, base], fill="#2A1B33")
        for wy in range(int(base - fh * h) + 3, int(base) - 2, 6):
            d.point((bx + 3, wy), fill="#F2C14E")
    d.rectangle([x0, base, x1, y1], fill="#1B1226")
    for fx, fh in ((0.86, 0.52), (0.94, 0.44)):
        tx = x0 + fx * w
        d.line([(tx, base), (tx + 2, base - fh * h)], fill="#120C18", width=2)
        for k in range(4):
            d.line([(tx + 2, base - fh * h + k * 3), (tx + 8, base - fh * h - 2 + k * 3)],
                   fill="#120C18", width=1)
    put(d, (x0 + int(w * 0.30), y0 + int(h * 0.16)), "$", font("serif_bold", 22), "#F7E3A1")


def art_sensex(im, b):
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    d.rectangle([x0, y0, x1, y1], fill="#EDF2E8")
    put(d, (x0 + 6, y0 + h // 2 - 8), "\u20b9", font("sans_bold", 16), "#1F6B4A")
    pts = [(0.26, 0.78), (0.38, 0.70), (0.47, 0.74), (0.58, 0.52), (0.68, 0.56),
           (0.80, 0.30), (0.92, 0.22)]
    d.line([(x0 + fx * w, y0 + fy * h) for fx, fy in pts], fill="#1F6B4A", width=2)
    ax, ay = x0 + 0.92 * w, y0 + 0.22 * h
    d.polygon([(ax + 2, ay - 1), (ax - 9, ay - 2), (ax - 3, ay + 8)], fill="#1F6B4A")
    for fx, fy in pts:
        d.ellipse([x0 + fx * w - 2, y0 + fy * h - 2, x0 + fx * w + 2, y0 + fy * h + 2],
                  fill="#1F6B4A")


def art_gaza(im, b):
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    d.rectangle([x0, y0, x1, y1], fill="#E7DFCC")
    ruins = [(0.02, 0.34, 0.10), (0.13, 0.52, 0.09), (0.23, 0.28, 0.08),
             (0.32, 0.62, 0.11), (0.44, 0.40, 0.09)]
    for fx, fh, fw in ruins:
        bx = x0 + fx * w
        top = y1 - fh * h
        d.rectangle([bx, top, bx + fw * w, y1], fill="#8C8574")
        d.polygon([(bx, top), (bx + fw * w * 0.4, top - 5), (bx + fw * w, top + 3),
                   (bx + fw * w, top)], fill="#E7DFCC")
        for wy in range(int(top) + 5, int(y1) - 2, 7):
            d.rectangle([bx + 3, wy, bx + 6, wy + 3], fill="#6B6558")
    gy = y0 + int(h * 0.80)
    d.line([(x0 + int(w * 0.56), gy), (x0 + int(w * 0.94), gy)], fill="#5A5A5A", width=2)
    d.rectangle([x0 + int(w * 0.62), gy - 5, x0 + int(w * 0.88), gy], fill="#B42318")
    for fx in (0.60, 0.72, 0.86):
        px = x0 + fx * w
        d.ellipse([px - 3, gy - 15, px + 3, gy - 9], fill="#14213D")
        d.line([(px, gy - 9), (px, gy - 2)], fill="#14213D", width=2)
        d.line([(px, gy - 2), (px - 4, gy + 4)], fill="#14213D", width=2)
        d.line([(px, gy - 2), (px + 4, gy + 4)], fill="#14213D", width=2)


def art_chelsea(im, b):
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    d.rectangle([x0, y0, x1, y1], fill="#2E7D4F")
    for k in range(4):
        yy = y0 + h * (0.30 + k * 0.18)
        d.line([(x0, yy), (x1, yy)], fill="#3D9463")
    gy = y0 + int(h * 0.30)
    gx = x0 + int(w * 0.62)
    d.rectangle([gx, gy, gx + int(w * 0.26), gy + int(h * 0.40)], outline="#F7F1E3", width=2)
    for px in range(int(gx) + 3, int(gx + w * 0.26), 6):
        d.line([(px, gy + 2), (px, gy + h * 0.40)], fill="#DDE6DC")
    d.ellipse([x0 + int(w * 0.20), y1 - int(h * 0.34), x0 + int(w * 0.20) + 12,
               y1 - int(h * 0.34) + 12], fill="#FFFFFF", outline="#14213D")
    d.polygon([(x0 + int(w * 0.20) + 6, y1 - int(h * 0.34) + 1),
               (x0 + int(w * 0.20) + 10, y1 - int(h * 0.34) + 5),
               (x0 + int(w * 0.20) + 7, y1 - int(h * 0.34) + 8),
               (x0 + int(w * 0.20) + 3, y1 - int(h * 0.34) + 5)], fill="#14213D")
    d.rectangle([x0 + 4, y0 + 4, x0 + 62, y0 + 17], fill="#0C1B2A")
    put(d, (x0 + 8, y0 + 5), "CHE 1-0 PSG", font("sans_bold", 9), "#F7F1E3")


def art_ukeu(im, b):
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    d.rectangle([x0, y0, x1, y1], fill="#E4E9EF")
    fx, fy = x0 + int(w * 0.05), y0 + int(h * 0.18)
    fw, fh = int(w * 0.30), int(h * 0.64)
    d.rectangle([fx, fy, fx + fw, fy + fh], fill="#1B3A6B", outline="#8C8574")
    d.line([(fx + fw // 2, fy), (fx + fw // 2, fy + fh)], fill="#FFFFFF", width=5)
    d.line([(fx, fy + fh // 2), (fx + fw, fy + fh // 2)], fill="#FFFFFF", width=5)
    d.line([(fx + fw // 2, fy), (fx + fw // 2, fy + fh)], fill="#B42318", width=2)
    d.line([(fx, fy + fh // 2), (fx + fw, fy + fh // 2)], fill="#B42318", width=2)
    ex, ey = x0 + int(w * 0.63), y0 + int(h * 0.18)
    ew, eh = int(w * 0.30), int(h * 0.64)
    d.rectangle([ex, ey, ex + ew, ey + eh], fill="#1B3A6B", outline="#8C8574")
    import math

    for i in range(8):
        ang = math.pi * 2 * i / 8
        px = ex + ew / 2 + math.cos(ang) * ew * 0.33
        py = ey + eh / 2 + math.sin(ang) * eh * 0.33
        d.ellipse([px - 1.5, py - 1.5, px + 1.5, py + 1.5], fill="#F2C14E")
    ay = y0 + h // 2
    d.line([(fx + fw + 5, ay), (ex - 6, ay)], fill="#14213D", width=2)
    d.polygon([(ex - 4, ay), (ex - 12, ay - 4), (ex - 12, ay + 4)], fill="#14213D")


def art_riyadh(im, b):
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    d.rectangle([x0, y0, x1, y1], fill="#1A2540")
    for i in range(3):
        d.rectangle([x0, y0 + i * h // 3, x1, y0 + (i + 1) * h // 3],
                    fill=("#1A2540", "#223052", "#2A3A60")[i])
    towers = [(0.08, 0.46, 0.10), (0.24, 0.30, 0.08), (0.40, 0.58, 0.09),
              (0.56, 0.38, 0.11), (0.74, 0.50, 0.09)]
    for fx, fh, fw in towers:
        bx = x0 + fx * w
        d.rectangle([bx, y1 - fh * h, bx + fw * w, y1], fill="#0C1224")
        for wy in range(int(y1 - fh * h) + 4, int(y1) - 2, 6):
            d.point((bx + 2, wy), fill="#F2C14E")
    tx = x0 + int(w * 0.44)
    d.polygon([(tx - 6, y1), (tx - 3, y0 + int(h * 0.10)), (tx + 3, y0 + int(h * 0.10)),
               (tx + 6, y1)], fill="#0C1224")
    _star(d, x0 + int(w * 0.66), y0 + int(h * 0.26), 7, "#F2C14E")
    _star(d, x0 + int(w * 0.66), y0 + int(h * 0.26), 3.5, "#E4572E")
    d.line([(x0 + int(w * 0.90), y0 + 2), (x0 + int(w * 0.70), y0 + int(h * 0.24))],
           fill="#8A93A8")


def art_senate(im, b):
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    d.rectangle([x0, y0, x1, y1], fill="#EDE7D8")
    cx = x0 + int(w * 0.34)
    base = y1 - int(h * 0.10)
    d.rectangle([cx - int(w * 0.20), base - int(h * 0.20), cx + int(w * 0.20), base],
                fill="#D8D2C0", outline="#8C8574")
    for px in range(int(cx - w * 0.17), int(cx + w * 0.17), 6):
        d.line([(px, base - int(h * 0.18)), (px, base - 2)], fill="#8C8574")
    d.polygon([(cx - int(w * 0.22), base - int(h * 0.20)),
               (cx, base - int(h * 0.30)),
               (cx + int(w * 0.22), base - int(h * 0.20))], fill="#C4BEAC")
    d.pieslice([cx - int(w * 0.15), base - int(h * 0.58), cx + int(w * 0.15),
                base - int(h * 0.24)], 180, 360, fill="#D8D2C0", outline="#8C8574")
    d.line([(cx, base - int(h * 0.58)), (cx, base - int(h * 0.66))], fill="#8C8574", width=2)
    bx = x0 + int(w * 0.64)
    d.rectangle([bx, y1 - int(h * 0.36), bx + int(w * 0.26), y1 - int(h * 0.06)],
                fill="#14213D")
    d.polygon([(bx, y1 - int(h * 0.36)), (bx + int(w * 0.26), y1 - int(h * 0.36)),
               (bx + int(w * 0.13), y1 - int(h * 0.46))], fill="#22345C")
    d.line([(bx + int(w * 0.13), y1 - int(h * 0.30)), (bx + int(w * 0.13), y1 - int(h * 0.16))],
           fill="#F2C14E", width=2)
    put(d, (x0 + int(w * 0.52), y0 + int(h * 0.12)), "51-48", font("sans_bold", 10), "#B42318")


def art_cricket(im, b):
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    d.rectangle([x0, y0, x1, y1], fill="#CFE0BE")
    d.rectangle([x0 + int(w * 0.30), y0 + int(h * 0.20), x0 + int(w * 0.78), y1],
                fill="#DCCB9E")
    sx = x0 + int(w * 0.62)
    for k in range(3):
        px = sx + k * 5
        d.line([(px, y1 - int(h * 0.55)), (px, y1 - 3)], fill="#8C6239", width=2)
    d.line([(sx - 1, y1 - int(h * 0.57)), (sx + 11, y1 - int(h * 0.57))], fill="#8C6239", width=2)
    d.polygon([(x0 + int(w * 0.20), y1 - 4), (x0 + int(w * 0.26), y1 - 4),
               (x0 + int(w * 0.40), y0 + int(h * 0.22)), (x0 + int(w * 0.36), y0 + int(h * 0.18))],
              fill="#D9A15B", outline="#8C6239")
    d.line([(x0 + int(w * 0.36), y0 + int(h * 0.19)), (x0 + int(w * 0.40), y0 + int(h * 0.23))],
           fill="#8C6239", width=3)
    d.ellipse([x0 + int(w * 0.48), y0 + int(h * 0.10), x0 + int(w * 0.48) + 8,
               y0 + int(h * 0.10) + 8], fill="#B42318", outline="#5A120C")


ART = {
    1: art_kyiv, 2: art_akvan, 3: art_ai_rout, 4: art_cop31, 5: art_poland,
    6: art_gta, 7: art_sensex, 8: art_gaza, 9: art_chelsea, 10: art_ukeu,
    11: art_riyadh, 12: art_senate, 13: art_cricket,
}

# ------------------------------------------------------------------ content ---

NUMBERS = [
    ("-5.3%", "NASDAQ COMPOSITE"),
    ("-14%", "NVIDIA"),
    ("110+", "MISSILES AT UKRAINE"),
    ("400+", "DRONES AT UKRAINE"),
    ("90 km/h", "AKVAN PEAK GUSTS"),
    ("$2.36bn", "GTA VI DAY ONE"),
]

TIMELINE = [
    ("00:00", "IMD: Cyclone Akvan centred off the Odisha coast"),
    ("02:30", "Akvan landfall begins near Gopalpur"),
    ("05:50", "Landfall complete; now a deep depression"),
    ("07:00", "Kyiv mayor confirms three Dnipro bridges hit"),
    ("13:30", "COP31 talks slip into overtime in Antalya"),
    ("14:30", "Wall Street opens into the AI sell-off"),
    ("21:00", "Nasdaq closes down 5.3%; year's gains gone"),
]

FEATURES = [
    dict(n=1, region="EUROPE", head="KYIV UNDER FIRE",
         body="Russia fired 110+ missiles and 400+ drones at Ukraine overnight in its biggest "
              "strike of November. Three Dnipro bridges were hit and nine people killed; power "
              "cut in 11 regions.",
         src="Reuters", status="CONFIRMED"),
    dict(n=2, region="ASIA-PACIFIC", head="AKVAN COMES ASHORE",
         body="Cyclone Akvan crossed the Odisha coast near Gopalpur on Friday morning with winds "
              "of 70-80 km/h, gusting to 90, then weakened to a deep depression as heavy rain "
              "spread inland.",
         src="IMD", status="CONFIRMED"),
    dict(n=3, region="AMERICAS", head="THE AI ROUT",
         body="The Nasdaq plunged 5.3%, wiping out its gains for the year, as the AI sell-off "
              "deepened. Nvidia fell 14% after reports of an SEC accounting probe; Anthropic "
              "slid 9% a day after its record IPO.",
         src="Reuters / WSJ", status="CONFIRMED"),
    dict(n=4, region="EUROPE", head="COP31 RUNS INTO OVERTIME",
         body="Talks in Antalya spill past Friday's deadline as the draft deal drops all mention "
              "of fossil fuels and a $120bn adaptation target.",
         src="Reuters", status="REPORTED"),
    dict(n=5, region="EUROPE", head="MISSILE LANDS IN POLAND",
         body="A Russian Kh-101 missile crashed in Nowy Lipowiec and a drone crossed into Polish "
              "airspace during the overnight barrage on Ukraine.",
         src="ISW / Reuters", status="REPORTED"),
    dict(n=6, region="AMERICAS", head="GTA VI: $2.36BN DAY ONE",
         body="Rockstar's sequel sold 24.6 million copies in its first day, the biggest "
              "entertainment launch ever, Sensor Tower reports.",
         src="Sensor Tower", status="CONFIRMED"),
    dict(n=7, region="ASIA-PACIFIC", head="INDIA DEFIES THE ROUT",
         body="The Sensex rose 780 points to a 10-month high even as global markets slid, led by "
              "domestic buyers.",
         src="Reuters", status="REPORTED"),
    dict(n=8, region="MIDDLE EAST & AFRICA", head="GAZA CREWS WALK IN",
         body="Rescue teams respond on foot as their vehicle fleet collapses, carrying the "
              "injured through streets no ambulance can reach.",
         src="AP", status="REPORTED"),
    dict(n=9, region="SPORT", head="CHELSEA TOP THE GROUP",
         body="Chelsea beat Paris Saint-Germain 1-0 to finish top of their Champions League "
              "group on Friday night.",
         src="BBC", status="CONFIRMED"),
    dict(n=10, region="EUROPE", head="UK-EU YOUTH DEAL",
         body="Britain and the EU agree a youth mobility scheme, the BBC understands, easing "
              "work and travel for young people.",
         src="BBC", status="REPORTED"),
    dict(n=11, region="MIDDLE EAST & AFRICA", head="HOUTHIS HIT RIYADH",
         body="Houthi missiles damaged Riyadh's PIF tower, the group claims, as Saudi defences "
              "intercepted missiles and drones.",
         src="Reuters", status="REPORTED"),
    dict(n=12, region="AMERICAS", head="SENATE BLOCKS IRAN VOTE",
         body="The US Senate rejects an Iran war-powers resolution 51-48, leaving war authority "
              "with the White House.",
         src="AP", status="CONFIRMED"),
    dict(n=13, region="ASIA-PACIFIC", head="INDIA BUNDLE OUT NZ",
         body="India dismiss New Zealand for 368 in the Test, Nicholls unbeaten on 175, as the "
              "hosts take control.",
         src="Reuters", status="REPORTED"),
]

BRIEFS = [
    ("EUROPE", [
        "Italy fines Meta \u20ac805m over Android photo access \u2014 Reuters",
        "EU summons Moscow envoy over embassy damage \u2014 Reuters",
        "Genoa flights suspended after drone sightings \u2014 AP",
        "Czech leaders visit Israel, inspect missile systems \u2014 AP",
    ]),
    ("ASIA-PACIFIC", [
        "Japan core CPI +2.2% fuels rate-hike bets \u2014 Reuters",
        "SoftBank plunges over 16% in Tokyo rout \u2014 Bloomberg",
        "Pakistan beat Sri Lanka by 8 wickets, seal series 1-0 \u2014 Reuters",
        "Rakshitha stuns Olympic champion Chen Yufei \u2014 AP",
        "China-linked spies exploited VMware zero-day \u2014 Reuters",
    ]),
    ("AMERICAS", [
        "Senate passes energy-permitting bill 62-33 \u2014 AP",
        "FAA ground stop strands 1.5m travellers \u2014 AP",
        "Posthumous pardon for Pete Rose \u2014 AP",
        "US sanctions Comancheros and 'Ndrangheta gangs \u2014 Reuters",
    ]),
    ("MIDDLE EAST & AFRICA", [
        "Israeli airstrike hits Hezbollah missile site in Lebanon \u2014 Reuters",
        "Senegal boat capsizing kills four \u2014 AP",
        "Kenya discharges its last Ebola patient \u2014 Reuters",
        "B-2 pilots detail Midnight Hammer strike on Iran \u2014 AP",
        "Iraq deploys forces at Kataib Hezbollah stronghold \u2014 Reuters",
    ]),
    ("SPORT", [
        "England win ODI series 2-1 in Australia \u2014 BBC",
        "Crystal Palace appoint Thomas Frank as manager \u2014 BBC",
        "Shelton's Turin breakthrough into the semis \u2014 ATP",
        "Russell tops wet Vegas FP2 \u2014 Reuters",
        "Jepchirchir gets 3-year ban for EPO \u2014 AP",
    ]),
]

TABS = [("EUROPE", 8), ("ASIA-PACIFIC", 8), ("AMERICAS", 7),
        ("MIDDLE EAST & AFRICA", 7), ("SPORT", 6)]

DATE_LEFT = ("FIRST REPORTED 19 NOVEMBER (EXCLUDED):  Anthropic's record $81.3bn IPO debut, up 17%"
             " \u00b7 ICJ: Myanmar committed genocide against the Rohingya \u00b7 Third Ukrainian "
             "strike on the Crimea Bridge \u00b7 Trump, Xi and Putin's Shenzhen summit.")
DATE_RIGHT = ("NOT YET \u2014 NO VERDICT BY PRESS TIME:  COP31 final deal (talks in overtime) \u00b7 "
              "Full extent of Kerch Bridge damage \u00b7 Outcome of the Nvidia SEC probe.")

# --------------------------------------------------------------------- map ---

CONTINENTS = {
    "north_america": [
        (-168, 66), (-160, 60), (-152, 58), (-144, 60), (-133, 55), (-125, 49),
        (-124, 42), (-117, 32), (-110, 23), (-104, 20), (-97, 16), (-92, 15),
        (-88, 18), (-90, 22), (-97, 26), (-94, 29), (-89, 29), (-82, 25),
        (-80, 27), (-81, 32), (-76, 35), (-70, 42), (-64, 46), (-56, 51),
        (-64, 56), (-78, 62), (-95, 68), (-125, 70), (-150, 70), (-168, 66),
    ],
    "south_america": [
        (-81, 8), (-77, 8), (-72, 11), (-62, 10), (-52, 5), (-44, -2),
        (-35, -6), (-38, -13), (-40, -22), (-48, -25), (-54, -34), (-58, -38),
        (-62, -40), (-65, -45), (-68, -52), (-75, -52), (-73, -45), (-72, -38),
        (-71, -30), (-70, -20), (-75, -15), (-78, -5), (-81, 0), (-79, 5),
    ],
    "africa": [
        (-17, 15), (-17, 21), (-10, 27), (0, 32), (10, 34), (20, 32),
        (32, 31), (35, 25), (38, 18), (43, 12), (51, 12), (48, 5),
        (42, -1), (40, -10), (40, -16), (35, -22), (33, -28), (27, -34),
        (19, -34), (15, -28), (12, -18), (9, -5), (9, 4), (4, 6),
        (-5, 5), (-12, 8),
    ],
    "eurasia": [
        (-10, 36), (-9, 43), (-2, 46), (-4, 49), (2, 51), (8, 54),
        (5, 58), (12, 65), (18, 69), (30, 70), (42, 68), (55, 70),
        (70, 73), (85, 76), (100, 77), (115, 74), (130, 71), (145, 72),
        (160, 70), (178, 66), (180, 62), (160, 60), (155, 52), (143, 46),
        (135, 42), (129, 35), (122, 30), (120, 23), (108, 18), (105, 10),
        (100, 6), (98, 10), (95, 16), (92, 21), (88, 22), (80, 13),
        (77, 8), (72, 20), (68, 24), (62, 25), (57, 25), (56, 20),
        (52, 16), (45, 13), (43, 17), (39, 22), (35, 28), (34, 31),
        (36, 36), (30, 36), (26, 40), (23, 38), (18, 40), (14, 41),
        (12, 45), (8, 44), (3, 42), (0, 39),
    ],
    "britain": [
        (-5.7, 50.0), (-3.5, 50.4), (-1.4, 50.7), (0.9, 51.0), (1.7, 52.5),
        (0.3, 53.5), (-0.2, 54.5), (-1.6, 55.6), (-2.0, 57.0), (-3.0, 58.6),
        (-5.6, 58.5), (-6.2, 57.0), (-5.0, 55.6), (-3.2, 54.6), (-3.0, 53.4),
        (-4.6, 53.3), (-4.1, 52.3), (-5.2, 51.6), (-3.0, 51.3), (-4.7, 50.3),
    ],
    "australia": [
        (114, -22), (113, -26), (115, -34), (120, -34), (129, -32), (135, -35),
        (141, -38), (146, -39), (150, -37), (153, -28), (153, -25), (146, -19),
        (142, -11), (137, -12), (132, -11), (129, -15), (125, -14), (122, -17),
    ],
}

PINS = [
    (1, 30.5, 50.4, 10, -8),
    (2, 85.0, 19.8, 10, 0),
    (3, -74.0, 40.7, -13, -11),
    (4, 30.7, 36.9, 10, 12),
    (5, 22.0, 50.1, -18, -8),
    (6, -118.2, 34.1, -13, -11),
    (7, 72.9, 19.1, -16, 8),
    (8, 34.4, 31.5, 12, 16),
    (9, -0.1, 51.5, -16, -6),
    (10, 4.35, 50.85, 14, -16),
    (11, 46.7, 24.7, 14, -8),
    (12, -77.0, 38.9, -14, 6),
    (13, 78.0, 21.0, 4, 18),
]

LAT_TOP, LAT_BOTTOM = 78.0, -56.0


def project(lon, lat, box):
    x0, y0, x1, y1 = box
    px = x0 + (lon + 180.0) / 360.0 * (x1 - x0)
    py = y0 + (LAT_TOP - lat) / (LAT_TOP - LAT_BOTTOM) * (y1 - y0)
    return px, py


def point_in_poly(px, py, poly):
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > py) != (yj > py):
            xhit = (xj - xi) * (py - yi) / (yj - yi) + xi
            if px < xhit:
                inside = not inside
        j = i
    return inside


def draw_map(d, box):
    x0, y0, x1, y1 = box
    d.rectangle([x0, y0, x1, y1], fill=SEA, outline=LAND_EDGE)
    for lon in range(-150, 180, 30):
        px, _ = project(lon, 0, box)
        d.line([(px, y0 + 1), (px, y1 - 1)], fill="#CBDCE3")
    for lat in range(-40, 80, 20):
        _, py = project(0, lat, box)
        d.line([(x0 + 1, py), (x1 - 1, py)], fill="#CBDCE3")
    polys = []
    for name, pts in CONTINENTS.items():
        poly = [project(lon, lat, box) for lon, lat in pts]
        polys.append(poly)
        d.polygon(poly, fill=LAND, outline=LAND_EDGE)
    for num, lon, lat, dx, dy in PINS:
        px, py = project(lon, lat, box)
        if not any(point_in_poly(px, py, poly) for poly in polys):
            _warnings.append("pin %d falls in the sea at %.1f,%.1f" % (num, lon, lat))
        f = font("sans_bold", 9)
        put(d, (px + dx, py + dy), str(num), f, RED, anchor="mm")
        d.ellipse([px - 2.4, py - 2.4, px + 2.4, py + 2.4], fill=RED, outline="#FFFFFF")


# ------------------------------------------------------------------ blocks ---

def masthead(d):
    top = 24
    f9 = font("sans_bold", 9)
    put(d, (LEFT, top), "No. 324 \u00b7 PRICE: ONE DAY", f9, GREY)
    put(d, (RIGHT, top), "36 STORIES \u00b7 5 REGIONS", f9, GREY, anchor="ra")
    tracked(d, SIZE / 2, top + 1, "THE WORLD IN ONE DAY", font("sans_bold", 9), RED, 3.2)
    double_rule(d, LEFT, RIGHT, 40, 3, NAVY)
    put(d, (SIZE / 2, 46), "Friday 20 November 2026", font("serif_bold", 38), NAVY, anchor="ma")
    put(d, (SIZE / 2, 90),
        "Every story here happened, or was first reported, on Friday 20 November 2026.",
        font("sans", 11), GREY, anchor="ma")
    double_rule(d, LEFT, RIGHT, 104, 3, NAVY)


def numbers_strip(d, top, bottom):
    cells = len(NUMBERS)
    width = INNER / cells
    hline(d, LEFT, RIGHT, top, RULE)
    hline(d, LEFT, RIGHT, bottom, RULE)
    for i, (figure, caption) in enumerate(NUMBERS):
        x = LEFT + i * width
        if i:
            vrule(d, x, top + 4, bottom - 4, RULE)
        cx = x + width / 2
        put(d, (cx, top + 3), figure, font("serif_bold", 18), NAVY, anchor="ma")
        put(d, (cx, top + 25), caption, font("sans_bold", 9), GREY, anchor="ma")


def timeline(d, top, bottom):
    put(d, (LEFT, top), "THE DAY IN UTC", font("sans_bold", 9), RED)
    hline(d, LEFT + 92, RIGHT, top + 4, RULE)
    width = INNER / len(TIMELINE)
    y = top + 12
    for i, (stamp, text) in enumerate(TIMELINE):
        x = LEFT + i * width
        if i:
            vrule(d, x - 2, y, bottom - 2, RULE)
        put(d, (x + 4, y), stamp, font("sans_bold", 9), NAVY)
        paragraph(d, x + 4, y + 10, text, font("sans", 9), INK, width - 8, 10, 3,
                  tag="timeline %s" % stamp)


def feature_card(page, d, box, item, art_h):
    x0, y0, x1, y1 = box
    d.rectangle([x0, y0, x1, y1], fill="#FBF7EC", outline=RULE)
    art_band(page, (x0 + 1, y0 + 1, x1 - 1, y0 + 1 + art_h), ART[item["n"]])
    hline(d, x0 + 1, x1 - 1, y0 + 1 + art_h, RULE)
    pad = 6
    inner = (x1 - x0) - 2 * pad
    y = y0 + art_h + 4
    f9 = font("sans_bold", 9)
    d.rectangle([x0 + pad, y, x0 + pad + 15, y + 11], fill=NAVY)
    put(d, (x0 + pad + 7.5, y + 5.5), "%02d" % item["n"], f9, WHITE, anchor="mm")
    put(d, (x0 + pad + 20, y + 1), item["region"], f9, RED, tag="feat region %d" % item["n"])
    y += 14
    head_font = fit_headline(item["head"], inner, 17, 9)
    put(d, (x0 + pad, y), item["head"], head_font, NAVY, tag="feat head %d" % item["n"])
    y += head_font.getbbox(item["head"])[3] + 3
    y = paragraph(d, x0 + pad, y, item["body"], font("sans", 11), INK, inner, 12, 5,
                  tag="feature %d" % item["n"])
    y += 1
    src = "Source: " + item["src"]
    put(d, (x0 + pad, y + 1), src, font("sans", 9), GREY, tag="feat src %d" % item["n"])
    bx = status_badge(d, x1 - pad, y, item["status"])
    if y + 15 > y1 + 1:
        _warnings.append("feature %d overflows card by %.0fpx" % (item["n"], y + 15 - y1))
    if x0 + pad + advance(font("sans", 9), src) > bx - 4:
        _warnings.append("feature %d source line collides with badge" % item["n"])


def small_card(page, d, box, item, art_h):
    x0, y0, x1, y1 = box
    d.rectangle([x0, y0, x1, y1], fill="#FBF7EC", outline=RULE)
    art_band(page, (x0 + 1, y0 + 1, x1 - 1, y0 + 1 + art_h), ART[item["n"]])
    hline(d, x0 + 1, x1 - 1, y0 + 1 + art_h, RULE)
    pad = 5
    inner = (x1 - x0) - 2 * pad
    y = y0 + art_h + 4
    f9 = font("sans_bold", 9)
    d.rectangle([x0 + pad, y, x0 + pad + 14, y + 11], fill=NAVY)
    put(d, (x0 + pad + 7, y + 5.5), "%02d" % item["n"], f9, WHITE, anchor="mm")
    put(d, (x0 + pad + 18, y + 1), item["region"], f9, RED, tag="small region %d" % item["n"])
    y += 13
    head_font = fit_headline(item["head"], inner, 14, 9)
    y = paragraph(d, x0 + pad, y, item["head"], head_font, NAVY, inner,
                  head_font.size + 1, 2, tag="small head %d" % item["n"])
    y = paragraph(d, x0 + pad, y, item["body"], font("sans", 11), INK, inner, 11.3, 5,
                  tag="small body %d" % item["n"])
    src = "Source: " + item["src"]
    put(d, (x0 + pad, y + 1), src, font("sans", 9), GREY, tag="small src %d" % item["n"])
    bx = status_badge(d, x1 - pad, y, item["status"])
    if y + 15 > y1 + 1:
        _warnings.append("small %d overflows card by %.0fpx" % (item["n"], y + 15 - y1))
    if x0 + pad + advance(font("sans", 9), src) > bx - 4:
        _warnings.append("small %d source line collides with badge" % item["n"])


def date_check(d, box):
    x0, y0, x1, y1 = box
    d.rectangle([x0, y0, x1, y1], fill="#FBF3E9", outline=RED, width=2)
    put(d, (x0 + 8, y0 + 6), "DATE CHECK \u2014 WHAT WE LEFT OUT", font("sans_bold", 10), RED)
    hline(d, x0 + 8, x1 - 8, y0 + 19, "#E4B7B0")
    mid = x0 + (x1 - x0) // 2
    vrule(d, mid, y0 + 24, y1 - 6, "#E4B7B0")
    paragraph(d, x0 + 8, y0 + 24, DATE_LEFT, font("sans", 10), INK, mid - x0 - 18, 11.5, 6,
              tag="date left")
    paragraph(d, mid + 8, y0 + 24, DATE_RIGHT, font("sans", 10), INK, x1 - mid - 16, 11.5, 6,
              tag="date right")


def tabs_row(d, top):
    f = font("sans_bold", 9)
    labels = [(name, str(count)) for name, count in TABS]
    widths = [advance(f, name) + advance(f, count) + 22 for name, count in labels]
    spare = INNER - sum(widths)
    widths = [w + spare / len(widths) for w in widths]
    x = LEFT
    for (name, count), w in zip(labels, widths):
        d.rectangle([x, top, x + w - 4, top + 15], fill="#EFE7D4", outline=RULE)
        put(d, (x + 6, top + 3), name, f, NAVY)
        put(d, (x + w - 12, top + 3), count, f, RED, anchor="ra")
        x += w


def briefs_block(d, top, bottom):
    f = font("sans", 10)
    put(d, (LEFT, top), "ALSO ON \u2014 23 MORE STORIES", font("sans_bold", 9), RED)
    hline(d, LEFT + 160, RIGHT, top + 4, RULE)
    rows = []
    for region, items in BRIEFS:
        rows.extend(items)
    split = 13
    col_w = (INNER - 2 * GUTTER) / 2
    vrule(d, LEFT + col_w + GUTTER / 2, top + 10, bottom, RULE)
    y = top + 13
    for i, line in enumerate(rows):
        if i < split:
            x, yy = LEFT, top + 13 + i * 10.2
        else:
            x, yy = LEFT + col_w + GUTTER, top + 13 + (i - split) * 10.2
        put(d, (x, yy), line, f, INK)
        d.rectangle([x - 5, yy + 4, x - 3, yy + 6], fill=RED)


def footer(d, y):
    text = ("Sources: Reuters, AP, BBC, Bloomberg, IMD, ISW, Sensor Tower, ATP \u2014 20 Nov 2026. "
            "Front page by alexxxwu.ai for make.fun.")
    hline(d, LEFT, RIGHT, y - 4, RULE)
    put(d, (LEFT, y), text, font("sans", 9), GREY)


# ------------------------------------------------------------------- build ---

def build():
    page = Image.new("RGB", (SIZE, SIZE), PAPER)
    d = ImageDraw.Draw(page)

    d.rectangle([10, 10, SIZE - 10, SIZE - 10], outline=NAVY, width=1)
    d.rectangle([15, 15, SIZE - 15, SIZE - 15], outline=NAVY, width=2)

    masthead(d)

    num_top, num_bottom = 112, 154
    numbers_strip(d, num_top, num_bottom)

    tl_top, tl_bottom = 158, 204
    timeline(d, tl_top, tl_bottom)

    big_top, big_h = 208, 180
    col_w = (INNER - 2 * GUTTER) / 3.0
    for i in range(3):
        x = LEFT + i * (col_w + GUTTER)
        box = (int(x), big_top, int(x + col_w), big_top + big_h)
        feature_card(page, d, box, FEATURES[i], 66)

    small_top = 390
    small_h = 158
    row_w = (INNER - 4 * GUTTER) / 5.0
    for row in range(2):
        for i in range(5):
            idx = 3 + row * 5 + i
            x = LEFT + i * (row_w + GUTTER)
            y = small_top + row * (small_h + 5)
            box = (int(x), y, int(x + row_w), y + small_h)
            small_card(page, d, box, FEATURES[idx], 38)

    band_top, band_bottom = 716, 814
    map_box = (LEFT, band_top, LEFT + 380, band_bottom)
    put(d, (LEFT, band_top - 13), "WHERE IT HAPPENED", font("sans_bold", 9), RED)
    draw_map(d, map_box)
    put(d, (map_box[0] + 4, map_box[3] + 1), "1-13 = features above", font("sans", 9), GREY)
    dc_box = (LEFT + 388, band_top, RIGHT, band_bottom)
    date_check(d, dc_box)

    tabs_row(d, 820)
    briefs_block(d, 840, 984)
    footer(d, 988)

    for w in _warnings:
        print("layout warning: " + w, file=sys.stderr)
    for p in audit():
        print("audit: " + p, file=sys.stderr)
    return page


def main():
    page = build()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    page.save(out, "PNG", optimize=True)
    print("wrote %s (%dx%d)" % (out, page.width, page.height))


if __name__ == "__main__":
    main()
