#!/usr/bin/env python3
"""Render entry.png: a one-page newspaper front page for Friday 20 November 2026.

Development-time generator (needs Pillow). The graded program, main.py, only
copies the finished PNG. Fully deterministic: no randomness, no clock, no
network, no external assets beyond the local DejaVu fonts.
"""

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
     "circle", RED, 50.4, 30.5, "Kyiv, Ukraine"),
    (2, "MARKETS IN FREEFALL", "Nikkei -4.5%, Kospi -4.7%, Taiex -6.2%",
     "bars", BLUE, 35.7, 139.7, "Tokyo, Japan"),
    (3, "ANTHROPIC'S AFTERMATH", "Record IPO day fails to halt sell-off",
     "ring", RED, 40.7, -74.0, "New York, US"),
    (4, "INDIA DEFIES THE ROUT", "Sensex +780; Nifty at 10-month high",
     "triangle", BLUE, 19.1, 72.9, "Mumbai, India"),
    (5, "POLAND ON ALERT", "Objects probed near Ukraine border",
     "cross", RED, 52.2, 21.0, "Warsaw, Poland"),
    (6, "EU SUMMONS MOSCOW", "Envoy called in over embassy damage",
     "square", BLUE, 50.8, 4.4, "Brussels, Belgium"),
    (7, "UK ARMS KYIV", "1,000+ long-range drones, 260m pound",
     "diamond", RED, 51.5, -0.1, "London, UK"),
    (8, "ARGENTINA VOTES", "Senate backs disability law, 71-0",
     "half", BLUE, -34.6, -58.4, "Buenos Aires, Argentina"),
    (9, "TRUMP PARDONS ROSE", "Posthumous pardon for Pete Rose",
     "target", RED, 38.9, -77.0, "Washington DC, US"),
    (10, "HORMUZ ON EDGE", "Tanker fire; Iran war in month nine",
     "triangle_down", BLUE, 26.5, 56.5, "Strait of Hormuz"),
    (11, "GENOA GROUNDED", "Flights suspended after drone sightings",
     "chevron", RED, 44.4, 8.9, "Genoa, Italy"),
    (12, "SHELTON'S TURIN BREAKTHROUGH", "Beats Jodar 7-6, 7-5; into semis",
     "grid", BLUE, 45.1, 7.7, "Turin, Italy"),
]

BRIEFS = [
    "US sanctions Comancheros and 'Ndrangheta gangs",
    "US court limits agriculture secretary's religious emails",
    "UK and EU agree youth mobility scheme, BBC understands",
    "Europe-wide youth action on living costs, housing, education",
    "COP31: Africa seeks tripled climate finance",
    "Czech leaders visit Israel, inspect missile systems",
    "Bukele to register for third presidential term in El Salvador",
    "FIFA presidential election set for 2027; three candidates",
    "Senegal boat capsizing kills four",
    "Gaza rescue crews respond on foot as vehicle fleet collapses",
    "B-2 pilots detail Operation Midnight Hammer strike on Iran",
    "Lula visits Chief Raoni as Brazil advances land recognition",
    "Meta revises 2030 climate targets amid AI build-out",
    "Six dead in gas explosion in Ponichala, Georgia",
    "5.6-magnitude quake strikes near New Caledonia",
    "Saudi air defences destroy two Houthi drones",
    "Houthis claim strikes on four Saudi targets",
    "Israeli airstrike hits Hezbollah missile site in Lebanon",
    "One dead, 15 hurt in fire at 18-storey block in France",
    "Malawi fuel crisis triggers violence",
    "Yemeni drivers hit by contaminated petrol",
    "White House: journalists must bag phones on China return flight",
    "Chicago man pleads not guilty in Hindu temple shooting plot",
    "Democrats: law firm gave $11.8m free legal work to Trump team",
    "Lion Academy Trust pays compensation over Prevent threat",
    "Storm Xavier: 50-knot winds forecast for 22 November",
    "Saudi Arabia warns of thunderstorms to 24 November",
    "India bundles out New Zealand for 368; Nicholls 175 not out",
    "Pakistan beat Sri Lanka by 8 wickets, seal Test series 1-0",
    "Pochettino's first Man Utd address: 'love' and unity; club 18th",
    "Peres Jepchirchir gets 3-year ban for EPO",
    "Rakshitha stuns Olympic champion Chen Yufei, Hong Kong Open",
    "Crystal Palace appoint Thomas Frank as manager",
    "Real Salt Lake beat Seattle on penalties, MLS wild card",
    "Wattimena ends Littler's Grand Slam darts defence 10-8",
    "Kenya win women's rugby sevens gold, Youth Olympics",
    "Chelsea beat PSG 1-0, top Champions League group",
    "Las Vegas GP first practice washed out by rain",
    "Bottas stays with Cadillac for 2027 F1 season",
    "NHL: 12 games \u2014 Canadiens, Flyers, Blues, Kings, Sabres, Jets win",
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
]

NUMBERS = ("100+ missiles \u2022 ~400 drones \u2022 8 killed, 28 injured \u2022 "
           "Nikkei -4.5% \u2022 Kospi -4.7% \u2022 Taiex -6.2% \u2022 Dow -1,101 \u2022 "
           "VIX 28.4 \u2022 Sensex +780 \u2022 71-0 vote \u2022 260m pound drones \u2022 "
           "5.6 quake \u2022 $97 Anthropic close")

REGIONS = ("EUROPE 12 \u2022 ASIA-PACIFIC 5 \u2022 AMERICAS 10 \u2022 "
           "MIDDLE EAST & AFRICA 11 \u2022 SPORT 14")

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
    6: (-2, -16), 7: (-18, -14), 8: (0, 0), 9: (-10, 12), 10: (0, 0),
    11: (18, 16), 12: (0, 12),
}

MAP_X0, MAP_Y0 = 28.0, 582.0
CELL_W, CELL_H = 13.0, 4.2
LAT_TOP, LAT_BOT = 80.0, -60.0


def geo(lat, lon):
    col = (lon + 180.0) / 6.0
    row = (LAT_TOP - lat) * len(MAP) / (LAT_TOP - LAT_BOT)
    return (MAP_X0 + (col + 0.5) * CELL_W, MAP_Y0 + (row + 0.5) * CELL_H)


# ------------------------------------------------------------------ icons ---

def icon(d, key, cx, cy, color, s=16):
    h = s / 2.0
    box = [cx - h, cy - h, cx + h, cy + h]
    if key == "circle":
        d.ellipse(box, fill=color)
    elif key == "ring":
        d.ellipse(box, outline=color, width=3)
    elif key == "triangle":
        d.polygon([(cx, cy - h), (cx + h, cy + h), (cx - h, cy + h)], fill=color)
    elif key == "triangle_down":
        d.polygon([(cx, cy + h), (cx + h, cy - h), (cx - h, cy - h)],
                  outline=color, width=2)
    elif key == "square":
        d.rectangle([cx - h + 1, cy - h + 1, cx + h - 1, cy + h - 1], fill=color)
    elif key == "diamond":
        d.polygon([(cx, cy - h), (cx + h, cy), (cx, cy + h), (cx - h, cy)], fill=color)
    elif key == "bars":
        for i, bh in enumerate((5, 9, 13)):
            x = cx - h + i * 5
            d.rectangle([x, cy + h - bh, x + 3, cy + h], fill=color)
    elif key == "cross":
        d.rectangle([cx - 2, cy - h, cx + 2, cy + h], fill=color)
        d.rectangle([cx - h, cy - 2, cx + h, cy + 2], fill=color)
    elif key == "target":
        d.ellipse(box, outline=color, width=2)
        d.ellipse([cx - 2.5, cy - 2.5, cx + 2.5, cy + 2.5], fill=color)
    elif key == "half":
        d.pieslice(box, 180, 360, fill=color)
    elif key == "chevron":
        d.line([(cx - h, cy + 3), (cx, cy - 4), (cx + h, cy + 3)], fill=color, width=3)
        d.line([(cx - h, cy + h), (cx, cy + 3), (cx + h, cy + h)], fill=color, width=3)
    elif key == "grid":
        for dx in (-1, 1):
            for dy in (-1, 1):
                d.rectangle([cx + dx * 4 - 3, cy + dy * 4 - 3,
                             cx + dx * 4 + 3, cy + dy * 4 + 3], fill=color)
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

        icon(d, ic, x + 24, y + 46, color, 16)

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

    dot_r = 1.7
    for r, row in enumerate(MAP):
        for c, ch in enumerate(row):
            if ch == "#":
                cx = MAP_X0 + (c + 0.5) * CELL_W
                cy = MAP_Y0 + (r + 0.5) * CELL_H
                d.ellipse([cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r], fill=BLUE)

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
    lf = font(8.5)
    nf = font(8.5, bold=True)
    for i, (num, head, deck, ic, color, lat, lon, label) in enumerate(FEATURES):
        y = 584 + i * 9.1
        d.text((lx, y - asc(lf)), str(num), font=nf, fill=RED)
        d.text((lx + 13, y - asc(lf)), label, font=lf, fill=INK)
        assert lx + 13 + lf.getlength(label) <= W - M

    # ---- briefs -------------------------------------------------------
    d.rectangle([M, 700, W - M, 700], fill=INK)
    text(d, M, 705, "ALSO ON 20 NOVEMBER", font(15, bold=True), INK)
    text(d, M + 196, 709, "40 MORE STORIES, IN BRIEF", font(9), DIM)
    d.rectangle([M, 721, W - M, 721], fill=LIGHT)

    col_w = (CW - 24) / 2.0
    brf = font(10.5)
    bnf = font(10.5, bold=True)
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
