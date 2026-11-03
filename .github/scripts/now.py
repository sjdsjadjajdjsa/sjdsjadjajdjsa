import json
import os
import sys
import urllib.request
from pathlib import Path

from kit import THEMES, svg, text, width

USER = os.environ.get("PROFILE_USER", "sjdsjadjajdjsa")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
API = "https://api.github.com"
CURSOR = ".cur{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}@media (prefers-reduced-motion:reduce){.cur{animation:none}}"
ALT = "cj's terminal: name, location, GitHub stats and languages, refreshed every 6 hours"


def call(path, body=None):
    req = urllib.request.Request(API + path, data=json.dumps(body).encode() if body else None)
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def contributions():
    q = f'query{{user(login:"{USER}"){{contributionsCollection{{contributionCalendar{{totalContributions}}}}}}}}'
    try:
        return call("/graphql", {"query": q})["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    except Exception:
        return None


def gather():
    user = call(f"/users/{USER}")
    repos = [r for r in call(f"/users/{USER}/repos?per_page=100&type=owner&sort=pushed") if not r["fork"] and not r["archived"] and r["name"] != USER]
    langs = {}
    for r in repos:
        for k, v in call(r["languages_url"][len(API):]).items():
            langs[k] = langs.get(k, 0) + v
    return dict(
        name=user["name"] or USER,
        place=user["location"] or "",
        stats=[("stars", sum(r["stargazers_count"] for r in repos)), ("projects", len(repos)), ("contributions", contributions()), ("followers", user["followers"])],
        langs=sorted(langs.items(), key=lambda x: -x[1]),
    )


def frame(t, w, h):
    return f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="{t["fill"]}" stroke="{t["line"]}"/>'


def prompt(t, x, y, cmd, size):
    return text(x, y, "$", t["ok"], size, 700) + text(x + width("$ ", size), y, cmd, t["ink"], size)


def cursor(t, x, y, size):
    w, h = size * 0.6, size * 1.1
    return prompt(t, x, y, "", size) + f'<rect class="cur" x="{x + width("$ ", size):g}" y="{y - size * 0.86:g}" width="{w:g}" height="{h:g}" fill="{t["ink"]}"/>'


def whoami(t, x, y, d, size):
    out = text(x, y, d["name"], t["ink"], size, 700)
    if d["place"]:
        out += text(x + width(d["name"] + " ", size), y, "· " + d["place"], t["sub"], size)
    return out


def lang_items(t, d):
    top, rest = d["langs"][:5], sum(v for _, v in d["langs"][5:])
    items = [(k, v, t["spec"][i]) for i, (k, v) in enumerate(top)] + ([("Other", rest, t["faint"])] if rest else [])
    total = sum(v for _, v, _ in items) or 1
    return [(f"{k} {v * 100 / total:.0f}%", v / total, c) for k, v, c in items]


def bar(x, y, w, h, items):
    out, cx = [], x
    for i, (_, share, c) in enumerate(items):
        sw = w * share - (4 if i < len(items) - 1 else 0)
        out.append(f'<rect x="{cx:.2f}" y="{y}" width="{max(sw, 2):.2f}" height="{h}" rx="{h / 4:g}" fill="{c}"/>')
        cx += w * share
    return "".join(out)


def legend(t, x, y, items, size, cols=None, colw=0, rowh=0):
    out, lx = [], x
    for i, (label, _, c) in enumerate(items):
        if cols:
            lx, ly = x + (i % cols) * colw, y + (i // cols) * rowh
        else:
            ly = y
        k = size * 0.75
        out.append(f'<rect x="{lx:.2f}" y="{ly - k:.2f}" width="{k:g}" height="{k:g}" rx="{k / 4:g}" fill="{c}"/>')
        out.append(text(lx + k + size * 0.5, ly, label, t["sub"], size))
        if not cols:
            lx += k + size * 0.5 + width(label, size) + size * 1.8
    return "".join(out)


def chrome(t, W, H, bh, size):
    dots = "".join(f'<circle cx="{bh / 2 + i * bh * 0.42:g}" cy="{bh / 2:g}" r="{bh / 9:g}" fill="{t["line"]}"/>' for i in range(3))
    head = f'<path d="M.5 {bh}V14.5a14 14 0 0 1 14-14h{W - 29}a14 14 0 0 1 14 14V{bh}z" fill="{t["fill"]}"/>'
    rule = f'<line x1=".5" y1="{bh}" x2="{W - .5}" y2="{bh}" stroke="{t["line"]}"/>'
    return frame(t, W, H) + head + rule + dots + text(W / 2, bh / 2 + size * 0.36, "cj@github", t["faint"], size, 400, "middle")


def stat(t, x, y, label, n, size):
    num = f"{n:,}"
    return text(x, y, num, t["ink"], size, 700) + text(x + width(num + " ", size), y, label, t["sub"], size)


def stats(d):
    return [p for p in d["stats"] if p[1] is not None]


def term_desk(t, d):
    W, x, s, step, gap = 1200, 36, 22, 36, 60
    b = prompt(t, x, 100, "whoami", s)
    who, y = whoami(t, x, 100 + step, d, s), 100 + step + gap
    b += who + prompt(t, x, y, "gh stats", s)
    cx = x
    for i, (label, n) in enumerate(stats(d)):
        if i:
            b += text(cx - width("·  ", s), y + step, "·", t["faint"], s)
        b += stat(t, cx, y + step, label, n, s)
        cx += width(f"{n:,} {label}", s) + width("   ·  ", s) - width(" ", s)
    y += step + gap
    items = lang_items(t, d)
    b += prompt(t, x, y, "langs", s) + bar(x, y + 18, W - 2 * x, 12, items) + legend(t, x, y + 64, items, 18)
    y += 64 + gap
    b += cursor(t, x, y, s)
    H = y + 40
    return svg(W, H, ALT, chrome(t, W, H, 48, 16) + b, CURSOR)


def term_mobile(t, d):
    W, x, s, step, gap = 800, 32, 28, 46, 70
    b = prompt(t, x, 124, "whoami", s)
    who, y = whoami(t, x, 124 + step, d, s), 124 + step + gap
    b += who + prompt(t, x, y, "gh stats", s)
    rows = stats(d)
    for i, (label, n) in enumerate(rows):
        b += stat(t, x + (i % 2) * 384, y + step + (i // 2) * step, label, n, s)
    y += ((len(rows) + 1) // 2) * step + gap
    items = lang_items(t, d)
    b += prompt(t, x, y, "langs", s) + bar(x, y + 20, W - 2 * x, 16, items)
    b += legend(t, x, y + 80, items, 22, 3, 248, 42)
    y += 80 + ((len(items) + 2) // 3 - 1) * 42 + gap
    b += cursor(t, x, y, s)
    H = y + 44
    return svg(W, H, ALT, chrome(t, W, H, 56, 20) + b, CURSOR)


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    out.mkdir(parents=True, exist_ok=True)
    data = gather()
    for m, t in THEMES.items():
        (out / f"now-{m}.svg").write_text(term_desk(t, data))
        (out / f"now-{m}-mobile.svg").write_text(term_mobile(t, data))
