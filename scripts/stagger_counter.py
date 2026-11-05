#!/usr/bin/env python3
"""Stagger the Moe Counter girls up/down in a wave.

Usage:
    python3 scripts/stagger_counter.py [input.svg]

With no argument it fetches the live counter itself (browser headers).
With a file argument it reads the SVG from that file (used by the Action,
which fetches with curl because the counter service 403s urllib from
GitHub runners). On fetch failure it warns and exits 0 so the scheduled
run stays green and the last good SVG keeps showing.
"""
import math
import re
import sys
import urllib.request

URL = "https://count.getloli.com/get/@ScriptKittenss?theme=asoul&offset=12"
OUT = "assets/counter-staggered.svg"
AMP = 14  # max vertical dip in px

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept": "image/svg+xml,image/*,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_svg():
    req = urllib.request.Request(URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")


def main():
    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1], encoding="utf-8", errors="ignore") as f:
                svg = f.read()
        except OSError as e:
            print(f"WARN: could not read {sys.argv[1]}: {e}; keeping old SVG")
            return
        if "<svg" not in svg or "<use" not in svg:
            print("WARN: input is not a counter SVG; keeping old SVG")
            return
    else:
        try:
            svg = fetch_svg()
        except Exception as e:
            print(f"WARN: counter fetch failed ({e}); keeping old SVG")
            return

    m = re.search(r'<svg viewBox="0 0 (\d+) (\d+)" width="(\d+)" height="(\d+)"', svg)
    if not m:
        print("WARN: unexpected counter SVG root; keeping old SVG")
        return
    vb_w, vb_h, w, h = map(int, m.groups())

    uses = list(re.finditer(r'<use x="(\d+)" xlink:href="#(\d+)"\s*/>', svg))
    n = len(uses)
    if n == 0:
        print("WARN: no digits found in counter SVG; keeping old SVG")
        return

    # wave: ends high, middle dips down (a smile)
    ys = []
    for i in range(n):
        if n == 1:
            y = 0
        else:
            y = round(AMP * (1 - math.cos(2 * math.pi * i / (n - 1))) / 2)
        ys.append(y)

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
