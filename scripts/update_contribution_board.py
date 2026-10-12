#!/usr/bin/env python3
"""Generate a large, labeled GitHub contribution calendar SVG."""
from datetime import date, timedelta
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape
import os
import re
import sys

USERNAME = os.environ.get("GITHUB_USERNAME", "uskascent-svg")
OUTPUT = "assets/contribution-activity.svg"
TODAY = date.today()
START = TODAY - timedelta(days=364)
URL = f"https://github.com/users/{USERNAME}/contributions?from={START.isoformat()}&to={TODAY.isoformat()}"
GREEN = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = {}
        self.current_date = None
        self.tooltip_depth = 0
        self.tooltip_text = ""

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
            self.tooltip_depth = 1
            self.tooltip_text = ""

    def handle_data(self, data):
        if self.tooltip_depth:
            self.tooltip_text += data

    def handle_endtag(self, tag):
        if tag == "tool-tip" and self.tooltip_depth:
            text = " ".join(self.tooltip_text.split())
            match = re.search(r"(\d[\d,]*) contributions?", text)
            if self.current_date and match and self.current_date in self.days:
                self.days[self.current_date]["count"] = int(match.group(1).replace(",", ""))
            self.tooltip_depth = 0


def main():
    request = Request(URL, headers={"User-Agent": "uskascent-svg-contribution-calendar/1.0"})
    with urlopen(request, timeout=20) as response:
        html = response.read().decode("utf-8", errors="replace")
    parser = CalendarParser()
    parser.feed(html)
    if len(parser.days) < 300:
        raise RuntimeError(
            f"Expected at least 300 dates from GitHub; parsed {len(parser.days)}. "
            "Keeping the previously committed calendar."
        )

    # Align every column to Sunday so weekday labels and dates line up.
    grid_start = START - timedelta(days=(START.weekday() + 1) % 7)
    grid_end = TODAY + timedelta(days=(5 - TODAY.weekday()) % 7)
    weeks = ((grid_end - grid_start).days + 1) // 7
    cell, gap = 14, 3
    left, top = 62, 64
    step = cell + gap
    width = left + weeks * step + 24
    calendar_bottom = top + 7 * step + 22
    height = calendar_bottom + 20
    total = sum(parser.days.get((START + timedelta(days=i)).isoformat(), {}).get("count", 0) for i in range(365))

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">GitHub contribution activity for {escape(USERNAME)}</title>',
        '<desc id="desc">A large 365-day GitHub contribution calendar with month and weekday labels. Hover over a square to see the exact date and contribution count.</desc>',
        '<rect width="100%" height="100%" rx="10" fill="#0d1117" stroke="#30363d"/>',
        '<text x="20" y="27" font-family="Arial, sans-serif" font-size="18" font-weight="700" fill="#f0f6fc">CONTRIBUTION ACTIVITY</text>',
        f'<text x="20" y="47" font-family="Arial, sans-serif" font-size="11" fill="#8b949e">{total:,} contributions · {START.isoformat()} — {TODAY.isoformat()}</text>',
    ]

    # Month labels sit above the week in which each month begins.
    current = grid_start
    while current <= grid_end:
        if current.day == 1:
            col = (current - grid_start).days // 7
            x = left + col * step
            lines.append(f'<text x="{x}" y="61" font-family="Arial, sans-serif" font-size="10" fill="#8b949e">{current.strftime("%b")}</text>')
        current += timedelta(days=1)

    weekday_names = [(1, "Mon"), (3, "Wed"), (5, "Fri")]
    for row, name in weekday_names:
        y = top + row * step + cell - 2
        lines.append(f'<text x="20" y="{y}" font-family="Arial, sans-serif" font-size="10" fill="#8b949e">{name}</text>')

    current = grid_start
    while current <= grid_end:
        col = (current - grid_start).days // 7
        row = (current.weekday() + 1) % 7
        if START <= current <= TODAY:
            item = parser.days.get(current.isoformat(), {"count": 0, "level": 0})
            level = item["level"]
            x, y = left + col * step, top + row * step
            label = f'{current.isoformat()}: {item["count"]} contribution' + ("" if item["count"] == 1 else "s")
            lines.append(
                f'<g><title>{escape(label)}</title><rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{GREEN[level]}"/></g>'
            )
        current += timedelta(days=1)

    legend_y = top + 7 * step + 8
    lines.append(f'<text x="{left}" y="{legend_y}" font-family="Arial, sans-serif" font-size="10" fill="#8b949e">Less</text>')
    for i, color in enumerate(GREEN):
        lines.append(f'<rect x="{left + 34 + i * 17}" y="{legend_y - 10}" width="12" height="12" rx="2" fill="{color}"/>')
    lines.append(f'<text x="{left + 126}" y="{legend_y}" font-family="Arial, sans-serif" font-size="10" fill="#8b949e">More</text>')
    lines.append('</svg>')

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as file:
        file.write("\n".join(lines) + "\n")
    print(f"Updated {OUTPUT}: {len(parser.days)} dates, {total} contributions.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Contribution refresh failed: {error}", file=sys.stderr)
        sys.exit(1)
