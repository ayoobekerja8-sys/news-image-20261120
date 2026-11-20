#!/usr/bin/env python3
"""Render entry.png: a one-page newspaper front page for Friday 20 November 2026.

Development-time generator (needs Pillow). The graded program, main.py, only
copies the finished PNG. Fully deterministic: no randomness, no clock, no
network, no external assets beyond the local DejaVu fonts.
"""

import math
import os

from PIL import Image, ImageDraw, ImageFont

W = H = 1024
BG = "#f7f3ea"
INK = "#141414"
RED = "#b02a20"
BLUE = "#1d4e89"
RULE = "#8d8574"
LIGHT = "#c9c0ae"
DIM = "#57503f"

FONT_DIR = "/usr/share/fonts/truetype/dejavu/"
SERIF_BOLD = FONT_DIR + "DejaVuSerif-Bold.ttf"
SANS = FONT_DIR + "DejaVuSans.ttf"
SANS_BOLD = FONT_DIR + "DejaVuSans-Bold.ttf"

M = 28
CW = W - 2 * M

_fonts = {}


def font(size, bold=False, serif=False):
    key = (size, bold, serif)
    if key not in _fonts:
        name = SERIF_BOLD if serif else (SANS_BOLD if bold else SANS)
        _fonts[key] = ImageFont.truetype(name, size)
    return _fonts[key]


def asc(f):
    return f.getbbox("H")[1]


def text(d, x, y_top, s, f, fill=INK, align="left"):
    if align == "center":
        x -= f.getlength(s) / 2.0
    elif align == "right":
        x -= f.getlength(s)
    d.text((x, y_top - asc(f)), s, font=f, fill=fill)


def wrap(s, f, maxw, maxlines):
    words = s.split()
    lines, cur = [], ""
    for w in words:
        t = w if not cur else cur + " " + w
        if f.getlength(t) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if len(lines) > maxlines:
        lines = lines[:maxlines]
        last = lines[-1]
        while last and f.getlength(last + "\u2026") > maxw:
            last = last[:-1]
        lines[-1] = last.rstrip(" ,.;:") + "\u2026"
    for ln in lines:
        assert f.getlength(ln) <= maxw + 0.5, ln
    return lines


def one_line(s, f, maxw):
    if f.getlength(s) <= maxw:
        return s
    t = s
    while t and f.getlength(t + "\u2026") > maxw:
        t = t[:-1]
    return t.rstrip(" ,.;:") + "\u2026"


def flow(d, x0, y_top, maxw, line_h, segments, max_lines):
    lines, widths = [[]], [0.0]
    for s, f, color in segments:
        for word in s.split():
            w = f.getlength(word)
            sp = f.getlength(" ") if lines[-1] else 0.0
            if widths[-1] + sp + w > maxw and lines[-1]:
                lines.append([])
                widths.append(0.0)
                sp = 0.0
            lines[-1].append((word, f, color))
            widths[-1] += sp + w
    assert len(lines) <= max_lines, (len(lines), max_lines)
    for i, line in enumerate(lines):
        x = x0
        y = y_top + i * line_h
        for word, f, color in line:
            d.text((x, y - asc(f)), word, font=f, fill=color)
            x += f.getlength(word) + f.getlength(" ")
    return y_top + len(lines) * line_h


# ---------------------------------------------------------------- content ---

FEATURES = [
    (1, "KYIV UNDER FIRE", "100+ missiles, ~400 drones, 8 killed",
     "explosion", RED, 50.4, 30.5, "Kyiv, Ukraine"),
    (2, "MARKETS IN FREEFALL", "S&P -0.9%, Nasdaq -1.7%; 6th day down",
     "chart-down", BLUE, 35.7, 139.7, "Tokyo, Japan"),
    (3, "ANTHROPIC'S AFTERMATH", "ANT -12% premarket after +17% debut",
     "ring-down", RED, 40.7, -74.0, "New York, US"),
    (4, "INDIA DEFIES THE ROUT", "Sensex +780; Nifty at 10-month high",
     "chart-up", BLUE, 19.1, 72.9, "Mumbai, India"),
    (5, "POLAND ON ALERT", "Airspace violated: 2 missiles, 1 drone",
     "radar", RED, 52.2, 21.0, "Warsaw, Poland"),
    (6, "ESTONIA SHUTS BORDER", "Russia frontier closed for 6 months",
     "gate", BLUE, 59.4, 24.7, "Tallinn, Estonia"),
    (7, "UK ARMS KYIV", "1,000+ long-range drones, \u00a3260m",
     "drone", RED, 51.5, -0.1, "London, UK"),
    (8, "ARGENTINA VOTES", "Senate backs disability law, 71-0",
     "ballot", BLUE, -34.6, -58.4, "Buenos Aires, Argentina"),
    (9, "TRUMP PARDONS ROSE", "Posthumous pardon for Pete Rose",
     "baseball", RED, 38.9, -77.0, "Washington DC, US"),
    (10, "GTA VI: $2.36BN DAY ONE", "Sensor Tower: 24.6m copies in a day",
     "controller", BLUE, 40.7, -74.0, "New York, US"),
    (11, "RUSSELL TOPS WET VEGAS FP2", "1:47.272; Gasly +0.071, Leclerc 3rd",
     "racecar", RED, 36.2, -115.1, "Las Vegas, US"),
    (12, "SHELTON'S TURIN BREAKTHROUGH", "Into semis; Zverev tops group unbeaten",
     "tennis", BLUE, 45.1, 7.7, "Turin, Italy"),
]

BRIEFS = [
    "US sanctions Comancheros and 'Ndrangheta gangs",
    "US court limits agriculture secretary's religious emails",
    "UK and EU agree youth mobility scheme, BBC understands",
    "Europe-wide youth action on living costs, housing, education",
    "COP31: Africa seeks tripled climate finance",
    "Bukele to register for third presidential term in El Salvador",
    "Senegal boat capsizing kills four",
    "Gaza rescue crews respond on foot as vehicle fleet collapses",
    "B-2 pilots detail Operation Midnight Hammer strike on Iran",
    "Six dead in gas explosion in Ponichala, Georgia",
    "Houthis claim strikes on four Saudi targets",
    "Israeli airstrike hits Hezbollah missile site in Lebanon",
    "India bundles out New Zealand for 368; Nicholls 175 not out",
    "Pakistan beat Sri Lanka by 8 wickets, seal Test series 1-0",
    "Rakshitha stuns Olympic champion Chen Yufei, Hong Kong Open",
    "Crystal Palace appoint Thomas Frank as manager",
    "Chelsea beat PSG 1-0, top Champions League group",
    "NHL: 12 games \u2014 Canadiens, Flyers, Blues, Kings, Sabres, Jets win",
    "Peres Jepchirchir gets 3-year ban for EPO",
    "Czech leaders visit Israel, inspect missile systems",
    "Genoa flights suspended after drone sightings",
    "EU summons Moscow envoy over embassy damage",
    "Tanker fire as Iran war enters month nine",
    "Iraq deploys forces at Kataib Hezbollah stronghold",
    "US approves 879,000 AI chips for Chinese firms",
    "White House replaces national cyber director",
    "Italy fines Meta \u20ac805m over Android photo access",
    "FAA ground stop strands 1.5m travellers",
    "IMF: global public debt nears 100% of GDP",
    "SoftBank plunges over 16% in Tokyo rout",
    "Japan core CPI +2.2% fuels rate-hike bets",
    "Saudi defences intercept Houthi missile, five drones",
    "Pakistan kills 22 militants near Afghan border",
    "Intuit plunges 11% on plan to sell Mailchimp",
    "UK judge: RAF Fairford accused face trial in Nov 2027",
    "Ella Langley sweeps CMA Awards",
    "China-linked spies exploited VMware zero-day",
    "Virginia pulls out of Trump's school-choice plan",
    "N-able zero-days mined crypto on 21 servers",
    "US diesel prices set to keep falling, energy chief says",
]

EXCLUDED = [
    "Trump, Xi and Putin's Shenzhen summit and 'peace declaration'",
    "ICJ: Myanmar committed genocide against the Rohingya",
    "Anthropic's record $81.3bn IPO debut (closed $97, +17%)",
    "US Senate rejects Iran war-powers resolution 51-48",
    "Third Ukrainian strike on the Crimea Bridge",
    "Houthi missile damages Riyadh's PIF tower",
    "Kenya discharges its last Ebola patient",
    "England win ODI series 2-1 in Australia",
    "Trump: no Iran decision until new year (Axios)",
    "Senate passes energy-permitting bill 62-33",
]

NUMBERS = ("100+ missiles \u2022 ~400 drones \u2022 8 killed, 28 injured \u2022 "
           "Nikkei -4.5% \u2022 S&P -0.9% \u2022 Nasdaq -1.7% \u2022 ANT -12% \u2022 "
           "VIX 28.8 \u2022 10Y 5.06% \u2022 GTA $2.36bn \u2022 Sensex +780 \u2022 "
           "71-0 vote \u2022 \u00a3260m drones")

REGIONS = ("EUROPE 12 \u2022 ASIA-PACIFIC 6 \u2022 AMERICAS 16 \u2022 "
           "MIDDLE EAST & AFRICA 9 \u2022 SPORT 9")

assert len(FEATURES) + len(BRIEFS) == 52

SOURCES = ("Sources: CNN, BBC, Wall Street Journal, Reuters, AP \u2014 20 Nov 2026. "
           "Front page by alexxxwu.ai for make.fun.")

# Coarse schematic land mask: 60 columns (6 deg lon each) x 26 rows.
MAP = [
    "..........##################...#####..###########...########",
    "...########################...##############################",
    "..##########################################################",
    "..#########################...##############################",
    "..###################.......################################",
    "........#############.......################################",
    ".........############.......##########################......",
    ".........##########.........##########################......",
    "..........########..........##########################......",
    "...........######..........#############.##########.........",
    "............######.........#############.##########.........",
    "............######.........#############..#######...........",
    "..............###..........############...##..###.##........",
    "................###........############....#..##..##........",
    "................#######........#######.......#######........",
    ".................########......######.........##########....",
    ".................########......######.........##########....",
    ".................########......########...........######.###",
    "..................######........#######.........#######..###",
    "..................######........####.##.........########....",
    "..................#####.........####.............#######....",
    ".................####...........###..............#######..##",
    ".................###..................................#...##",
    ".................###........................................",
    ".................##.........................................",
    "..................#.........................................",
]

PIN_OFFSET = {
    1: (6, -8), 2: (0, 0), 3: (6, -10), 4: (0, 0), 5: (0, -18),
    6: (0, 0), 7: (-18, -14), 8: (0, 0), 9: (-10, 12), 10: (14, -22),
    11: (0, 0), 12: (0, 12),
}

MAP_X0, MAP_Y0 = 28.0, 582.0
CELL_W, CELL_H = 13.0, 4.2
LAT_TOP, LAT_BOT = 80.0, -60.0


def geo(lat, lon):
    col = (lon + 180.0) / 6.0
    row = (LAT_TOP - lat) * len(MAP) / (LAT_TOP - LAT_BOT)
    return (MAP_X0 + (col + 0.5) * CELL_W, MAP_Y0 + (row + 0.5) * CELL_H)


# ----------------------------------------------------------------- scenes ---

def scene(d, key, x, y, w, h, color):
    cx, cy = x + w / 2.0, y + h / 2.0
    if key == "explosion":
        ox, oy = cx, cy + 2
        pts = []
        for i in range(16):
            a = i * math.pi / 8.0 - math.pi / 2.0
            r = 10.5 if i % 2 == 0 else 4.6
            pts.append((ox + r * math.cos(a), oy + r * 0.92 * math.sin(a)))
        d.polygon(pts, fill=color)
        for i in range(4):
            a = i * math.pi / 2.0 + math.pi / 4.0
            dx, dy = ox + 12.6 * math.cos(a), oy + 11.0 * math.sin(a)
            d.ellipse([dx - 1.2, dy - 1.2, dx + 1.2, dy + 1.2], fill=color)
    elif key in ("chart-down", "chart-up"):
        base = y + h - 6
        heights = (6, 11, 16) if key == "chart-up" else (16, 11, 6)
        for i, bh in enumerate(heights):
            bx = x + 5 + i * 6
            d.rectangle([bx, base - bh, bx + 4, base], fill=color)
        ax = x + w - 9
        if key == "chart-down":
            d.line([(ax, y + 5), (ax, base - 4)], fill=color, width=2)
            d.polygon([(ax - 4, base - 8), (ax + 4, base - 8), (ax, base)],
                      fill=color)
        else:
            d.line([(ax, base), (ax, y + 9)], fill=color, width=2)
            d.polygon([(ax - 4, y + 8), (ax + 4, y + 8), (ax, y + 1)],
                      fill=color)
    elif key == "ring-down":
        r = 7.5
        d.ellipse([cx - r, y + 2, cx + r, y + 2 + 2 * r],
                  outline=color, width=2)
        d.line([(cx, y + 17), (cx, y + 21)], fill=color, width=2)
        d.polygon([(cx - 4, y + 20), (cx + 4, y + 20), (cx, y + 27)],
                  fill=color)
    elif key == "radar":
        ry = cy + 4
        for r in (5.5, 9.0, 12.5):
            d.arc([cx - r, ry - r, cx + r, ry + r], 205, 335,
                  fill=color, width=1)
        d.line([(cx, ry), (cx + 9, ry - 6)], fill=color, width=1)
        d.ellipse([cx + 10, ry - 9, cx + 14, ry - 5], fill=color)
    elif key == "gate":
        d.rectangle([x + 4, cy - 2, x + 7, y + h - 3], fill=color)
        d.rectangle([x + w - 8, cy - 2, x + w - 5, y + h - 3], fill=color)
        d.rectangle([x + 8, cy - 3, x + w - 9, cy + 1], fill=color)
        for i in range(4):
            sx = x + 10 + i * 5
            d.polygon([(sx, cy - 3), (sx + 3, cy - 3), (sx + 1, cy + 1),
                       (sx - 2, cy + 1)], fill=BG)
    elif key == "drone":
        d.rectangle([cx - 5, cy - 2, cx + 5, cy + 4], fill=color)
        d.line([(cx - 8, cy - 6), (cx + 8, cy - 6)], fill=color, width=1)
        d.line([(cx - 8, cy + 8), (cx + 8, cy + 8)], fill=color, width=1)
        for sx, sy in ((cx - 8, cy - 6), (cx + 8, cy - 6),
                       (cx - 8, cy + 8), (cx + 8, cy + 8)):
            d.ellipse([sx - 4, sy - 2, sx + 4, sy + 2], outline=color, width=1)
        d.line([(cx, cy - 2), (cx, cy - 6)], fill=color, width=1)
        d.line([(cx, cy + 4), (cx, cy + 8)], fill=color, width=1)
    elif key == "ballot":
        d.rectangle([cx - 11, cy - 7, cx + 11, cy + 10], outline=color, width=2)
        d.rectangle([cx - 6, cy - 5, cx + 6, cy - 2], fill=color)
        d.line([(cx - 6, cy + 4), (cx - 2, cy + 8), (cx + 8, cy - 3)],
               fill=color, width=2)
    elif key == "baseball":
        r = 10.0
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=2)
        d.arc([cx - r - 4, cy - r, cx + 3, cy + r], 300, 60, fill=color, width=1)
        d.arc([cx - 3, cy - r, cx + r + 4, cy + r], 120, 240, fill=color, width=1)
        for i in range(3):
            t = -0.5 + i * 0.5
            d.line([(cx - r * 0.85, cy + t * r * 0.8),
                    (cx - r * 0.55, cy + t * r * 0.8)], fill=color, width=1)
            d.line([(cx + r * 0.55, cy + t * r * 0.8),
                    (cx + r * 0.85, cy + t * r * 0.8)], fill=color, width=1)
    elif key == "controller":
        d.rounded_rectangle([cx - 12, cy - 6, cx + 12, cy + 7], radius=5,
                            outline=color, width=2)
        d.rectangle([cx - 8, cy - 1, cx - 5, cy + 2], fill=color)
        d.rectangle([cx - 9, cy - 0.5, cx - 4, cy + 1.5], fill=color)
        d.ellipse([cx + 5, cy - 3, cx + 8, cy], fill=color)
        d.ellipse([cx + 8, cy + 1, cx + 11, cy + 4], fill=color)
    elif key == "racecar":
        d.polygon([(x + 3, cy + 6), (x + 8, cy + 3), (x + 12, cy - 2),
                   (x + 20, cy - 2), (x + 25, cy + 2), (x + 31, cy + 3),
                   (x + 31, cy + 6)], fill=color)
        d.ellipse([x + 6, cy + 3, x + 13, cy + 10], outline=color, width=2)
        d.ellipse([x + 21, cy + 3, x + 28, cy + 10], outline=color, width=2)
        d.line([(x + 4, y + 9), (x + 4, cy + 1)], fill=color, width=1)
        for i in range(5):
            for j in range(2):
                sx = x + 4 + i * 3.2
                sy = y + 3 + j * 3.2
                if (i + j) % 2 == 0:
                    d.rectangle([sx, sy, sx + 2.6, sy + 2.6], fill=color)
    elif key == "tennis":
        r = 8.5
        bx = cx - 4
        d.ellipse([bx - r, cy - r, bx + r, cy + r], outline=color, width=2)
        d.arc([bx - r - 2, cy - r, bx + r, cy + r], 250, 110,
              fill=color, width=1)
        d.arc([bx - r, cy - r, bx + r + 2, cy + r], 70, 290,
              fill=color, width=1)
        hx, hy = cx + 9, cy - 3
        d.ellipse([hx - 6, hy - 6, hx + 6, hy + 6], outline=color, width=1)
        for i in range(3):
            d.line([(hx - 4 + i * 4, hy - 5), (hx - 4 + i * 4, hy + 5)],
                   fill=color, width=1)
        for i in range(3):
            d.line([(hx - 5, hy - 4 + i * 4), (hx + 5, hy - 4 + i * 4)],
                   fill=color, width=1)
        d.line([(hx - 5, hy + 5), (hx - 7, hy + 11)], fill=color, width=2)
    else:
        raise ValueError(key)


# ----------------------------------------------------------------- canvas ---

def main():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # ---- masthead -----------------------------------------------------
    d.rectangle([M, 14, W - M, 15], fill=INK)
    d.rectangle([M, 19, W - M, 19], fill=INK)

    name = font(58, serif=True)
    text(d, W / 2, 26, "THE WORLD IN ONE DAY", name, INK, "center")

    d.rectangle([M, 78, W - M, 79], fill=INK)

    dl = font(18, bold=True)
    text(d, W / 2, 88, "FRIDAY, 20 NOVEMBER 2026", dl, INK, "center")
    text(d, W - M, 93, "make.fun daily news image", font(8.5), DIM, "right")

    text(d, W / 2, 113, "52 STORIES  \u2022  FIVE CONTINENTS  \u2022  ONE DAY",
         font(11), DIM, "center")

    d.rectangle([M, 132, W - M, 134], fill=RED)
    d.rectangle([M, 138, W - M, 138], fill=LIGHT)

    # ---- lead banner --------------------------------------------------
    tag = font(13, bold=True)
    d.rectangle([M, 156, M + 54, 184], fill=RED)
    text(d, M + 27, 160, "LEAD", tag, "#ffffff", "center")
    d.rectangle([M + 62, 154, M + 64, 214], fill=RED)

    lx = M + 74
    lw = W - M - lx
    hf = font(27, bold=True)
    head_lines = wrap("KYIV UNDER FIRE: RUSSIA'S MASSIVE OVERNIGHT STRIKE ON UKRAINE",
                      hf, lw, 2)
    assert "\u2026" not in "".join(head_lines)
    for i, ln in enumerate(head_lines):
        text(d, lx, 152 + i * 30, ln, hf, INK)
    head_bottom = 152 + len(head_lines) * 30

    df = font(13.5)
    deck = ("More than 100 missiles and about 400 drones hit Ukraine overnight; "
            "8 killed, 28 injured, three Kyiv bridges damaged and power cut "
            "across regions.")
    deck_lines = wrap(deck, df, lw, 2)
    assert "\u2026" not in "".join(deck_lines)
    deck_top = head_bottom + 2
    for i, ln in enumerate(deck_lines):
        text(d, lx, deck_top + i * 16, ln, df, DIM)
    assert deck_top + len(deck_lines) * 16 <= 258

    # ---- feature grid -------------------------------------------------
    COLS, ROWS = 3, 4
    GAP = 10
    CARD_W = (CW - (COLS - 1) * GAP) / 3.0
    CARD_H = 68
    ROW_GAP = 7
    GRID_TOP = 266

    hf13 = font(13, bold=True)
    df11 = font(11)
    bf = font(11, bold=True)
    bf8 = font(8, bold=True)

    for idx, (num, head, deck, ic, color, lat, lon, label) in enumerate(FEATURES):
        r, c = divmod(idx, COLS)
        x = M + c * (CARD_W + GAP)
        y = GRID_TOP + r * (CARD_H + ROW_GAP)
        d.rectangle([x, y, x + CARD_W, y + CARD_H], outline=LIGHT, width=1)

        d.ellipse([x + 14, y + 10, x + 34, y + 30], fill=RED)
        d.text((x + 24, y + 20), str(num), font=bf8 if num > 9 else bf,
               fill="#ffffff", anchor="mm")

        scene(d, ic, x + 2, y + 32, 34, 28, color)

        tx = x + 42
        tw = CARD_W - 42 - 9
        lines = wrap(head, hf13, tw, 2)
        block = len(lines) * 14 + 4 + 12
        top = y + (CARD_H - block) / 2.0 + 1
        for i, ln in enumerate(lines):
            text(d, tx, top + i * 14, ln, hf13, INK)
        dl1 = one_line(deck, df11, tw)
        text(d, tx, top + len(lines) * 14 + 4, dl1, df11, DIM)

    assert GRID_TOP + ROWS * CARD_H + (ROWS - 1) * ROW_GAP <= 560

    # ---- map strip ----------------------------------------------------
    d.rectangle([M, 562, W - M, 562], fill=INK)
    text(d, M, 566, "WHERE IT HAPPENED", font(12.5, bold=True), RED)
    text(d, M + 158, 568, "\u2014 12 FEATURES PINNED", font(11), DIM)
    text(d, W - M, 569, "schematic map", font(8.5), DIM, "right")

    # graticule behind the dots
    map_w = len(MAP[0]) * CELL_W
    map_h = len(MAP) * CELL_H
    for lon in range(-180, 181, 30):
        gx = MAP_X0 + ((lon + 180.0) / 6.0) * CELL_W
        d.line([(gx, MAP_Y0), (gx, MAP_Y0 + map_h)], fill=LIGHT, width=1)
    for lat in range(-60, 81, 30):
        gy = MAP_Y0 + ((LAT_TOP - lat) * len(MAP) / (LAT_TOP - LAT_BOT)) * CELL_H
        d.line([(MAP_X0, gy), (MAP_X0 + map_w, gy)], fill=LIGHT, width=1)

    dot_r = 1.0
    for r, row in enumerate(MAP):
        for c, ch in enumerate(row):
            if ch == "#":
                for sy in (0.25, 0.75):
                    for sx in (0.25, 0.75):
                        cx = MAP_X0 + (c + sx) * CELL_W
                        cy = MAP_Y0 + (r + sy) * CELL_H
                        d.ellipse([cx - dot_r, cy - dot_r,
                                   cx + dot_r, cy + dot_r], fill=BLUE)

    pins = []
    for num, head, deck, ic, color, lat, lon, label in FEATURES:
        ax, ay = geo(lat, lon)
        dx, dy = PIN_OFFSET[num]
        px, py = ax + dx, ay + dy
        pins.append((num, px, py, ax, ay))
    for i in range(len(pins)):
        for j in range(i + 1, len(pins)):
            dist = ((pins[i][1] - pins[j][1]) ** 2 + (pins[i][2] - pins[j][2]) ** 2) ** 0.5
            assert dist >= 12.0, (pins[i][0], pins[j][0], dist)

    pf = font(7.5, bold=True)
    for num, px, py, ax, ay in pins:
        if abs(px - ax) > 1.5 or abs(py - ay) > 1.5:
            d.line([(ax, ay), (px, py)], fill=RED, width=1)
        d.ellipse([px - 6, py - 6, px + 6, py + 6], fill=RED, outline=BG, width=1)
        d.text((px, py), str(num), font=pf, fill="#ffffff", anchor="mm")

    lx = 820
    text(d, lx, 566, "", font(9))
    lf = font(7.2)
    nf = font(7.2, bold=True)
    for i, (num, head, deck, ic, color, lat, lon, label) in enumerate(FEATURES):
        y = 584 + i * 9.5
        d.text((lx, y - asc(lf)), str(num), font=nf, fill=RED)
        d.text((lx + 13, y - asc(lf)), label, font=lf, fill=INK)
        assert lx + 13 + lf.getlength(label) <= W - M

    # ---- briefs -------------------------------------------------------
    d.rectangle([M, 700, W - M, 700], fill=INK)
    text(d, M, 705, "ALSO ON 20 NOVEMBER", font(15, bold=True), INK)
    text(d, M + 240, 709, "40 MORE STORIES, IN BRIEF", font(9), DIM)
    d.rectangle([M, 721, W - M, 721], fill=LIGHT)

    col_w = (CW - 24) / 2.0
    brf = font(8.0)
    bnf = font(8.0, bold=True)
    top = 726
    lh = 10.2
    for i, brief in enumerate(BRIEFS):
        col, row = divmod(i, 20)
        x = M + col * (col_w + 24)
        y = top + row * lh
        num = 13 + i
        ns = str(num)
        d.text((x + 21 - bnf.getlength(ns), y - asc(bnf)), ns, font=bnf, fill=RED)
        d.text((x + 25, y - asc(brf)), one_line(brief, brf, col_w - 27), font=brf, fill=INK)
    assert top + 20 * lh <= 931

    # ---- date check strip ---------------------------------------------
    d.rectangle([0, 934, W, 970], fill=INK)
    end = flow(d, 24, 936, W - 48, 10.6,
               [("DATE CHECK \u2014 NOT FROM TODAY, FIRST REPORTED 19 NOVEMBER (EXCLUDED): ",
                 font(8.6, bold=True), "#ffffff"),
                ("  \u2022  ".join(EXCLUDED), font(8.6), "#d5cebe")],
               3)
    assert end <= 969, end

    # ---- bottom bar ---------------------------------------------------
    d.rectangle([M, 973, W - M, 973], fill=LIGHT)
    end = flow(d, M, 976, CW, 11.4,
               [("THE DAY IN NUMBERS: ", font(9.5, bold=True), RED),
                (NUMBERS, font(9.5, bold=True), INK)],
               2)
    assert end <= 999, end

    text(d, M, 1000, REGIONS, font(8.6, bold=True), INK)
    text(d, M, 1011, SOURCES, font(7.6), DIM)
    assert 1011 + 9 <= H

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    img.save(out, format="PNG", optimize=True)
    return out


if __name__ == "__main__":
    print(main())
