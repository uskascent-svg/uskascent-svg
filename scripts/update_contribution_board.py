#!/usr/bin/env python3
"""Generate a chessboard-styled SVG from the public GitHub contribution calendar."""
from datetime import date, timedelta
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape
import os
import sys

USERNAME = os.environ.get("GITHUB_USERNAME", "uskascent-svg")
OUTPUT = "assets/chess-contributions.svg"
TODAY = date.today()
START = TODAY - timedelta(days=63)
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
                self.days[self.current_date] = {"count": max(0, count), "level": min(4, max(0, level))}
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
                # GitHub tooltip generally starts with the contribution count.
                import re
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
    if len(parser.days) < 40:
        raise RuntimeError(f"Expected a public GitHub contribution calendar; parsed only {len(parser.days)} days. Keeping the last committed SVG.")
    days = []
    for offset in range(64):
        current = START + timedelta(days=offset)
        key = current.isoformat()
        item = parser.days.get(key, {"count": 0, "level": 0})
        days.append((current, item["count"], item["level"]))

    # Last 64 days arranged chronologically in an 8x8 grid.
    cell_w, cell_h, gap = 24, 20, 2
    x0, y0 = 20, 43
    board_w, board_h = 8 * cell_w, 8 * cell_h
    total = sum(count for _, count, _ in days)
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="340" height="238" viewBox="0 0 340 238" role="img" aria-labelledby="title desc">',
        '<title id="title">Live GitHub contributions for ' + escape(USERNAME) + '</title>',
        '<desc id="desc">The latest 64 calendar days of public GitHub contributions, arranged as a chessboard. Hover over each square for the date and contribution count. Updated automatically by GitHub Actions.</desc>',
        '<rect width="340" height="238" rx="12" fill="#171411" stroke="#8d6b3f"/>',
        '<text x="18" y="24" font-family="monospace" font-size="11" fill="#f1d29a">LIVE CONTRIBUTIONS · LAST 64 DAYS</text>',
        f'<text x="18" y="36" font-family="monospace" font-size="8" fill="#c9b18b">{escape(USERNAME)} · {total} contributions in this window</text>',
        f'<g transform="translate({x0} {y0})">',
    ]
    for index, (day, count, level) in enumerate(days):
        col, row = index % 8, index // 8
        x, y = col * cell_w, row * cell_h
        base = LIGHT if (row + col) % 2 == 0 else DARK
        fill = base if count == 0 else COLORS[max(1, level)]
        label = f"{day.isoformat()}: {count} contribution" + ("" if count == 1 else "s")
        lines.append(f'<g><title>{escape(label)}</title><rect x="{x}" y="{y}" width="{cell_w-gap}" height="{cell_h-gap}" rx="2" fill="{fill}" stroke="#171411" stroke-width="0.5"/></g>')
    lines.extend([
        '</g>',
        '<g font-family="monospace" font-size="9" fill="#f1d29a">',
        '<text x="230" y="72">LIVE DATA</text>',
        '<text x="230" y="88">64 DAYS</text>',
        '<text x="230" y="104">HOVER CELLS</text>',
        '<text x="230" y="120">FOR COUNTS</text>',
        '</g>',
        '<text x="20" y="222" font-family="monospace" font-size="8" fill="#c9b18b">Source: public GitHub contribution calendar · refreshes daily</text>',
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
