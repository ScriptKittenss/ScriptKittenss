#!/usr/bin/env python3
"""Fetch the live Moe Counter SVG, stagger the girls up/down in a wave,
and save it as a self-contained SVG. Run by the GitHub Action every 15 min
and once now to seed the first version."""
import math
import re
import urllib.request

URL = "https://count.getloli.com/get/@ScriptKittenss?theme=asoul&offset=12"
OUT = "assets/counter-staggered.svg"
AMP = 14  # max vertical dip in px

def main():
    req = urllib.request.Request(
        URL, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        svg = r.read().decode("utf-8", "ignore")

    m = re.search(r'<svg viewBox="0 0 (\d+) (\d+)" width="(\d+)" height="(\d+)"', svg)
    if not m:
        raise SystemExit("unexpected counter SVG root")
    vb_w, vb_h, w, h = map(int, m.groups())

    uses = list(re.finditer(r'<use x="(\d+)" xlink:href="#(\d+)"\s*/>', svg))
    n = len(uses)
    if n == 0:
        raise SystemExit("no digits found in counter SVG")

    # wave: ends high, middle dips down (a smile)
    ys = []
    for i in range(n):
        if n == 1:
            y = 0
        else:
            y = round(AMP * (1 - math.cos(2 * math.pi * i / (n - 1))) / 2)
        ys.append(y)

    # rebuild the <use> tags with staggered y, in order
    out = []
    last = 0
    for match, y in zip(uses, ys):
        out.append(svg[last:match.start()])
        x, d = match.groups()
        out.append(f'<use x="{x}" y="{y}" xlink:href="#{d}" />')
        last = match.end()
    out.append(svg[last:])
    svg = "".join(out)

    new_h = h + AMP
    svg = svg.replace(
        f'viewBox="0 0 {vb_w} {vb_h}" width="{w}" height="{h}"',
        f'viewBox="0 0 {vb_w} {new_h}" width="{w}" height="{new_h}"',
        1,
    )

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    digits = "".join(d for _, d in ((u.group(1), u.group(2)) for u in uses))
    print(f"staggered {n} digits, count={digits}, height={new_h}")

if __name__ == "__main__":
    main()
