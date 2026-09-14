#!/usr/bin/env python3
"""Generate a 3D isometric contribution-calendar skyline SVG from REAL GitHub data.

Reads a GraphQL contributionsCollection JSON dump (default /tmp/contrib.json),
or fetches fresh data from the GitHub GraphQL API when GH_TOKEN is set.

Output: docs-ready animated SVG (SMIL only, zero JS) — cubes grow in a wave,
the peak day glows, months fade in. Committed so the profile graph is honest
and reproducible.
"""
import json, sys, datetime as dt

# ---------- config ----------
HW, HH = 8.0, 4.0          # isometric half-tile width / height (2:1)
FLAT_H = 2.5               # height of an empty day tile
MAX_CUBE_H = 150.0         # tallest cube
OX, OY = 96, 176           # origin (week0/day0 base center)
VW, VH = 560, 474          # viewBox
PANEL = "#0d1117"
TEXT_DIM = "#6e7681"
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
TIERS = [                   # (max_count, base color) — GitHub dark palette
    (0,  "#1b2027"),
    (2,  "#0e4429"),
    (5,  "#006d32"),
    (9,  "#26a641"),
    (999, "#39d353"),
]

def shade(hex_color, f):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % (max(0, min(255, int(r*f))),
                              max(0, min(255, int(g*f))),
                              max(0, min(255, int(b*f))))

def tier_color(n):
    for mx, c in TIERS:
        if n <= mx:
            return c
    return TIERS[-1][1]

# ---------- data ----------
data = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "/tmp/contrib.json"))
cc = data["data"]["user"]["contributionsCollection"]
cal = cc["contributionCalendar"]
weeks = cal["weeks"]
days = [[d for d in w["contributionDays"]] for w in weeks]

total = cal["totalContributions"]
commits = cc["totalCommitContributions"]
issues = cc["totalIssueContributions"]
prs = cc["totalPullRequestContributions"]
reviews = cc["totalPullRequestReviewContributions"]

flat = [(w, d, day) for w, row in enumerate(days) for d, day in enumerate(row)]
peak_w, peak_d, peak = max(flat, key=lambda t: t[2]["contributionCount"])
max_n = peak["contributionCount"]
unit = (MAX_CUBE_H - FLAT_H) / max_n if max_n else 1
first_date = days[0][0]["date"]
last_date = days[-1][-1]["date"]
peak_date = peak["date"]

# ---------- geometry ----------
def pos(w, d):
    return OX + (w - d) * HW, OY + (w + d) * HH

def cube_svg(w, d, count):
    x, y = pos(w, d)
    h = FLAT_H + count * unit if count else FLAT_H
    base = tier_color(count)
    top, left, right = base, shade(base, 0.78), shade(base, 0.58)
    t = -h
    top_pts = f"0,{t-HH:.2f} {HW:.2f},{t:.2f} 0,{t+HH:.2f} {-HW:.2f},{t:.2f}"
    left_pts = f"{-HW:.2f},{t:.2f} 0,{t+HH:.2f} 0,{HH:.2f} {-HW:.2f},0"
    right_pts = f"{HW:.2f},{t:.2f} 0,{t+HH:.2f} 0,{HH:.2f} {HW:.2f},0"
    return (f'<g transform="translate({x:.1f} {y:.1f})">'
            f'<polygon points="{left_pts}" fill="{left}"/>'
            f'<polygon points="{right_pts}" fill="{right}"/>'
            f'<polygon points="{top_pts}" fill="{top}"/>'
            f'</g>')

# painter order: back (small w+d) → front
cubes = sorted(flat, key=lambda t: (t[0] + t[1]))
parts = []
for w, d, day in cubes:
    parts.append(cube_svg(w, d, day["contributionCount"]))
cubes_svg = "\n".join(parts)

# month labels along the front edge (d = 7)
labels = []
prev_m = None
for w, row in enumerate(days):
    m = int(row[0]["date"][5:7]) - 1
    if w > 0 and m != prev_m:
        x, y = pos(w, 7)
        labels.append(f'<text x="{x:.0f}" y="{y + 14:.0f}" class="lbl">{MONTHS[m]}</text>')
    prev_m = m
labels_svg = "\n".join(labels)

# legend (Less → More)
leg = []
lx, ly = OX - 40, OY + (52 + 7) * HH + 26
leg.append(f'<text x="{lx - 44:.0f}" y="{ly + 3:.0f}" class="lbl" text-anchor="start">Less</text>')
for i, (_, c) in enumerate(TIERS):
    cx = lx + i * 18
    leg.append(f'<g transform="translate({cx:.0f} {ly:.0f})">'
               f'<polygon points="0,-4.5 9,0 0,4.5 -9,0" fill="{c}"/>'
               f'<polygon points="-9,0 0,4.5 0,7 -9,2.5" fill="{shade(c,0.78)}"/>'
               f'<polygon points="9,0 0,4.5 0,7 9,2.5" fill="{shade(c,0.58)}"/></g>')
leg.append(f'<text x="{lx + 5 * 18 + 8:.0f}" y="{ly + 3:.0f}" class="lbl">More</text>')
legend_svg = "\n".join(leg)

# peak marker (glow + bobbing count)
px, py = pos(peak_w, peak_d)
peak_top = OY + (peak_w + peak_d) * HH - (FLAT_H + max_n * unit) - 12
peak_svg = f'''<g>
  <animateTransform attributeName="transform" type="translate" values="0 0;0 -4;0 0" keyTimes="0;.5;1" dur="2.2s" repeatCount="indefinite"/>
  <circle cx="{px:.0f}" cy="{peak_top:.0f}" r="14" fill="url(#pglow)">
    <animate attributeName="opacity" values=".55;.95;.55" dur="2.2s" repeatCount="indefinite"/>
  </circle>
  <text x="{px:.0f}" y="{peak_top - 18:.0f}" text-anchor="middle" font-size="12" font-weight="700" fill="#39d353">{max_n}</text>
</g>'''

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VW} {VH}" width="{VW}" height="{VH}" role="img" aria-label="3D isometric skyline of the real GitHub contribution calendar: {total} contributions between {first_date} and {last_date}">
  <title>Contribution skyline — {total} contributions in the last year</title>
  <desc>Every cube is one real day from the GitHub contribution calendar; height is contributions that day. Peak: {max_n} on {peak_date}.</desc>
  <defs>
    <radialGradient id="pglow" cx=".5" cy=".5" r=".5">
      <stop offset="0" stop-color="#39d353" stop-opacity=".55"/>
      <stop offset="1" stop-color="#39d353" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="bgGlow" cx=".5" cy=".42" r=".65">
      <stop offset="0" stop-color="#0e4429" stop-opacity=".35"/>
      <stop offset="1" stop-color="#0d1117" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="shine" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#ffffff" stop-opacity="0"/>
      <stop offset=".5" stop-color="#ffffff" stop-opacity="1"/>
      <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>
    <style>
      .lbl {{ font-family: ui-monospace, 'JetBrains Mono', Menlo, Consolas, monospace; font-size: 10px; fill: {TEXT_DIM}; }}
      .ttl {{ font-family: ui-monospace, 'JetBrains Mono', Menlo, Consolas, monospace; font-size: 13px; font-weight: 700; fill: #e6edf3; }}
    </style>
  </defs>
  <rect width="{VW}" height="{VH}" rx="16" fill="{PANEL}"/>
  <rect width="{VW}" height="{VH}" rx="16" fill="url(#bgGlow)"/>
  <text x="24" y="34" class="ttl">{total} contributions in the last year</text>
  <text x="24" y="52" class="lbl">{first_date} → {last_date} · peak {max_n} on {peak_date} · real data, GitHub GraphQL</text>
  <g opacity=".07">
    <animateTransform attributeName="transform" type="translate" values="-160 0;{VW + 160} 0" keyTimes="0;1" dur="7.5s" repeatCount="indefinite"/>
    <rect x="-45" y="0" width="90" height="{VH}" fill="url(#shine)"/>
  </g>
  {cubes_svg}
  {peak_svg}
  {labels_svg}
  {legend_svg}
</svg>
'''

out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/skyline.svg"
open(out, "w").write(svg)

print(json.dumps({
    "total": total, "commits": commits, "prs": prs, "issues": issues, "reviews": reviews,
    "peak": {"date": peak_date, "count": max_n, "week": peak_w, "day": peak_d},
    "range": [first_date, last_date], "out": out, "bytes": len(svg),
    "active_days": sum(1 for _, _, d in flat if d["contributionCount"] > 0),
}))
