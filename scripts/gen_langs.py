#!/usr/bin/env python3
"""Generate a Suyash-inspired terminal language-distribution SVG from public GitHub repository data.

The scheduled workflow refreshes this card daily; changes to this generator also trigger a refresh.
"""
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

OWNER = os.getenv("GITHUB_REPOSITORY_OWNER", "uskascent-svg")
TOKEN = os.getenv("GITHUB_TOKEN", "")
OUT = Path("assets/langs.svg")
COLORS = {
    "Python": "#3572A5", "TypeScript": "#3178c6", "JavaScript": "#f1e05a",
    "Java": "#b07219", "C++": "#f34b7d", "C": "#555555", "HTML": "#e34c26",
    "CSS": "#563d7c", "Shell": "#89e051", "PowerShell": "#012456",
    "Go": "#00ADD8", "Rust": "#dea584", "PHP": "#4F5D95", "Ruby": "#701516",
    "Jupyter Notebook": "#DA5B0B", "Dart": "#00B4AB", "Kotlin": "#A97BFF",
    "Swift": "#F05138", "SQL": "#e38c00", "Dockerfile": "#384d54",
}
headers = {"Accept": "application/vnd.github+json", "User-Agent": "language-stats-generator"}
if TOKEN:
    headers["Authorization"] = f"Bearer {TOKEN}"

def get_json(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)

totals = {}
page = 1
while page <= 10:
    repos = get_json(f"https://api.github.com/users/{OWNER}/repos?type=owner&per_page=100&page={page}")
    if not repos:
        break
    for repo in repos:
        if repo.get("fork") or repo.get("archived") or repo.get("size", 0) == 0:
            continue
        try:
            langs = get_json(repo["languages_url"])
        except (urllib.error.URLError, KeyError, json.JSONDecodeError):
            continue
        for language, byte_count in langs.items():
            totals[language] = totals.get(language, 0) + int(byte_count)
    if len(repos) < 100:
        break
    page += 1

total_bytes = sum(totals.values())
ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:8]
if not ranked or total_bytes == 0:
    raise SystemExit("No public repository language data found; refusing to generate misleading percentages.")

W, H = 370, 70 + len(ranked) * 31 + 25
parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Live programming language distribution for {escape(OWNER)} public repositories">']
parts += ['''<style>
text{font-family:'JetBrains Mono','Fira Code','SF Mono',Consolas,'Liberation Mono',Menlo,monospace}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}
.f{opacity:0;animation:fade .45s ease-out forwards}
@media(prefers-reduced-motion:reduce){.f{opacity:1;animation:none} .bar{transform:none;animation:none}}
</style>''']
parts.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="10" fill="#0d1117" stroke="#30363d"/>')
parts.append('<path d="M0.5 36V10.5a10 10 0 0 1 10-10h349a10 10 0 0 1 10 10V36z" fill="#161b22"/>')
parts.append('<line x1="0.5" y1="36" x2="369.5" y2="36" stroke="#30363d"/>')
parts.append('<circle cx="20" cy="18" r="6" fill="#ff5f57"/><circle cx="40" cy="18" r="6" fill="#febc2e"/><circle cx="60" cy="18" r="6" fill="#28c840"/>')
parts.append(f'<text x="185" y="23" text-anchor="middle" font-size="12.5" fill="#8b949e">languages · {escape(OWNER)}</text>')
parts.append(f'<g class="f" style="animation-delay:.1s"><text x="22" y="61" font-size="12.5"><tspan fill="#00ff9c">{escape(OWNER)}</tspan><tspan fill="#8b949e">@cloud:~$ </tspan><tspan fill="#c9d1d9">gh lang --top</tspan></text></g>')
bar_x, bar_w, y0 = 22, 326, 91
for i, (language, count) in enumerate(ranked):
    pct = count * 100 / total_bytes
    y = y0 + i * 31
    delay = .2 + i * .08
    color = COLORS.get(language, "#8b949e")
    label = escape(language[:22])
    parts.append(f'<text class="f" style="animation-delay:{delay:.2f}s" x="{bar_x}" y="{y}" font-size="13" fill="#c9d1d9">{label}</text>')
    parts.append(f'<text class="f" style="animation-delay:{delay:.2f}s" x="348" y="{y}" text-anchor="end" font-size="12.5" fill="#8b949e">{pct:4.1f}%</text>')
    parts.append(f'<rect x="{bar_x}" y="{y+7}" width="{bar_w}" height="7" rx="3.5" fill="#21262d"/>')
    parts.append(f'<rect class="bar" x="{bar_x}" y="{y+7}" width="{bar_w*pct/100:.2f}" height="7" rx="3.5" fill="{color}" style="transform-origin:{bar_x}px 0;transform:scaleX(0);animation:grow .9s ease-out {delay+.1:.2f}s forwards"/>')
parts.append(f'<text x="22" y="{H-13}" font-size="9.5" fill="#8b949e">Generated from public repos · percentages by code bytes</text>')
parts.append('</svg>')
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
print(f"Generated {OUT} from {len(totals)} language totals.")
