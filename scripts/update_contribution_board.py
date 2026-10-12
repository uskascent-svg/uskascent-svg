#!/usr/bin/env python3
"""Generate a 365-day chess-inspired SVG from GitHub's public contribution calendar."""
from datetime import date, timedelta
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape
import os
import re
import sys

USERNAME = os.environ.get("GITHUB_USERNAME", "uskascent-svg")
OUTPUT = "assets/chess-contributions.svg"
TODAY = date.today()
START = TODAY - timedelta(days=364)
URL = f"https://github.com/users/{USERNAME}/contributions?from={START.isoformat()}&to={TODAY.isoformat()}"
COLORS = ["#9c886b", "#b7d7a8", "#75b86d", "#3f8c50", "#1d5e37"]
LIGHT = "#e8dcc8"
DARK = "#9c886b"


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = {}
        self.current_date = None
        self.title_depth = 0
        self.title_text = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "td" and "ContributionCalendar-day" in attrs.get("class", ""):
            self.current_date = attrs.get("data-date")
            if self.current_date:
                try:
                    count = int(attrs.get("data-count", "0"))
                    level = int(attrs.get("data-level", "0"))
                except ValueError:
                    count, level = 0, 0
                self.days[self.current_date] = {
                    "count": max(0, count),
                    "level": min(4, max(0, level)),
                }
        if tag == "tool-tip" and self.current_date:
            self.title_depth = 1
            self.title_text = ""

    def handle_data(self, data):
        if self.title_depth:
            self.title_text += data

    def handle_endtag(self, tag):
        if tag == "tool-tip" and self.title_depth:
            text = " ".join(self.title_text.split())
            if self.current_date and text:
                match = re.search(r"(\d[\d,]*) contributions?", text)
                if match:
                    self.days[self.current_date]["count"] = int(match.group(1).replace(",", ""))
            self.title_depth = 0
            self.current_date = None


def main():
    request = Request(URL, headers={"User-Agent": "uskascent-svg-contribution-board/1.0"})
    with urlopen(request, timeout=20) as response:
        html = response.read().decode("utf-8", errors="replace")
    parser = CalendarParser()
    parser.feed(html)
    if len(parser.days) < 300:
        raise RuntimeError(
            f"Expected at least 300 dates in the public GitHub contribution calendar; "
            f"parsed only {len(parser.days)}. Keeping the last committed SVG."
        )

    days = []
    for offset in range(365):
        current = START + timedelta(days=offset)
        item = parser.days.get(current.isoformat(), {"count": 0, "level": 0})
        days.append((current, item["count"], item["level"]))

    # 53 columns × 7 rows gives a compact, GitHub-calendar-style rectangle.
    cell, gap = 28, 5
    cols, rows = 26, 14
    x0, y0 = 28, 90
    board_w = cols * cell
    total = sum(count for _, count, _ in days)
    width, height = 800, 510
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Live 365-day GitHub contributions for ' + escape(USERNAME) + '</title>',
        '<desc id="desc">A 365-day rectangular contribution board with 365 squares. Each square is one date; color intensity reflects public GitHub contribution activity. Hover over a square for its date and count. Updated daily by GitHub Actions.</desc>',
        '<rect width="100%" height="100%" rx="10" fill="#171411" stroke="#8d6b3f"/>',
        '<text x="24" y="30" font-family="monospace" font-size="18" fill="#f1d29a">365-DAY CONTRIBUTION CHESSBOARD</text>',
        f'<text x="24" y="52" font-family="monospace" font-size="13" fill="#c9b18b">{escape(USERNAME)} · {total:,} contributions in the last 365 days · refreshed {TODAY.isoformat()}</text>',
    ]
    for index, (day, count, level) in enumerate(days):
        col, row = index // rows, index % rows
        x, y = x0 + col * cell, y0 + row * cell
        base = LIGHT if (col + row) % 2 == 0 else DARK
        fill = base if count == 0 else COLORS[max(1, level)]
        label = f"{day.isoformat()}: {count} contribution" + ("" if count == 1 else "s")
        lines.append(
            f'<g><title>{escape(label)}</title><rect x="{x}" y="{y}" width="{cell-gap}" height="{cell-gap}" rx="1.5" fill="{fill}" stroke="#171411" stroke-width="0.4"/></g>'
        )
    legend_y = y0 + rows * cell + 13
    lines.extend([
        f'<text x="28" y="{legend_y}" font-family="monospace" font-size="11" fill="#c9b18b">LESS</text>',
    ])
    for i, color in enumerate([LIGHT, "#b7d7a8", "#75b86d", "#3f8c50", "#1d5e37"]):
        lines.append(f'<rect x="{82 + i*20}" y="{legend_y-7}" width="15" height="15" rx="2" fill="{color}"/>')
    lines.extend([
        f'<text x="{165}" y="{legend_y}" font-family="monospace" font-size="11" fill="#c9b18b">MORE</text>',
        '<text x="772" y="500" text-anchor="end" font-family="monospace" font-size="10" fill="#c9b18b">LIVE · DAILY</text>',
        '</svg>',
    ])
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as file:
        file.write("\n".join(lines) + "\n")
    print(f"Updated {OUTPUT}: {len(days)} dates, {total} contributions.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Contribution refresh failed: {error}", file=sys.stderr)
        sys.exit(1)
