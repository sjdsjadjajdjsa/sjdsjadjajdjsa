import base64
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from kit import ASSETS, THEMES, star, svg, text, width, wrap

USER = os.environ.get("PROFILE_USER", "sjdsjadjajdjsa")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
FEATURED = ["prism", "hanami", "afterglow-viz"]
MORE = ["tonal", "rhythia-is-trash", "pg3d-rewrite", "ttyfy-theme"]
LANG = {"Rust": "#dea584", "Go": "#00add8", "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Python": "#3572a5", "QML": "#44a51c", "Shell": "#89e051"}
API = "https://api.github.com"


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


def project(name):
    r = call(f"/repos/{USER}/{name}")
    return dict(name=r["name"], desc=r["description"] or "", lang=r["language"] or "", stars=r["stargazers_count"])


def gather():
    user = call(f"/users/{USER}")
    repos = [r for r in call(f"/users/{USER}/repos?per_page=100&type=owner&sort=pushed") if not r["fork"] and not r["archived"] and r["name"] != USER]
    langs = {}
    for r in repos:
        for k, v in call(r["languages_url"][len(API):]).items():
            langs[k] = langs.get(k, 0) + v
    log = []
    for r in repos[:3]:
        c = call(f"/repos/{r['full_name']}/commits?per_page=1")[0]["commit"]
        log.append((r["name"], c["committer"]["date"], c["message"].splitlines()[0]))
    return dict(
        stats=[("stars", sum(r["stargazers_count"] for r in repos)), ("projects", len(repos)), ("contributions", contributions()), ("followers", user["followers"])],
        langs=sorted(langs.items(), key=lambda x: -x[1]),
        log=log,
    )


def preview(name):
    f = ASSETS / "previews" / f"{name}.jpg"
    return "data:image/jpeg;base64," + base64.b64encode(f.read_bytes()).decode() if f.exists() else None


def frame(t, w, h):
    return f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="{t["fill"]}" stroke="{t["line"]}"/>'


def lang(t, x, y, name, size):
    dot = f'<circle cx="{x + size * 0.3:g}" cy="{y - size * 0.36:g}" r="{size * 0.3:g}" fill="{LANG.get(name, t["faint"])}"/>'
    return dot + text(x + size * 0.95, y, name, t["sub"], size) if name else ""


def stars(t, xr, y, n, size):
    if not n:
        return ""
    s = f"{n:,}"
    ix = xr - width(s, size) - size * 0.9
    return star(ix, y - size * 0.36, size * 1.05, t["sub"]) + text(xr, y, s, t["sub"], size, 700, "end")


def picture(href, x, y, w, h):
    if not href:
        return ""
    clip = f'<clipPath id="pic"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/></clipPath>'
    return clip + f'<image href="{href}" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice" clip-path="url(#pic)"/>'


def featured_desk(t, p, key):
    W, H, x, xr = 1200, 248, 408, 1164
    body = frame(t, W, H - 16) + picture(preview(key), 16, 16, 356, 200)
    body += text(x, 42.3, p["name"], t["ink"], 36, 700) + stars(t, xr, 37.9, p["stars"], 24)
    for i, line in enumerate(wrap(p["desc"], 56, 3)):
        body += text(x, 92 + i * 32, line, t["sub"], 22)
    body += lang(t, x, 216, p["lang"], 20)
    return svg(W, H, f'{p["name"]}: {p["desc"]}', body)


def featured_mobile(t, p, key):
    W, x, xr = 800, 32, 768
    lines = wrap(p["desc"], 40, 3)
    h = 580 + (len(lines) - 1) * 42 + 62 + 36
    body = frame(t, W, h) + picture(preview(key), 16, 16, 768, 432)
    body += text(x, 520, p["name"], t["ink"], 48, 700) + stars(t, xr, 518, p["stars"], 32)
    for i, line in enumerate(lines):
        body += text(x, 580 + i * 42, line, t["sub"], 30)
    body += lang(t, x, h - 36, p["lang"], 28)
    return svg(W, h + 16, f'{p["name"]}: {p["desc"]}', body)


def more_desk(t, p, key):
    W, H, x, xr = 1200, 132, 36, 1164
    tail = stars(t, xr, 50, p["stars"], 22)
    lr = xr - (width(f'{p["stars"]:,}', 22) + 52 if p["stars"] else 0)
    lx = lr - width(p["lang"], 20) - 20 * 0.95
    body = frame(t, W, H - 16) + text(x, 50, p["name"], t["ink"], 28, 700) + tail + lang(t, lx, 50, p["lang"], 20)
    body += text(x, 88, wrap(p["desc"], 84, 1)[0], t["sub"], 22)
    return svg(W, H, f'{p["name"]}: {p["desc"]}', body)


def more_mobile(t, p, key):
    W, x, xr = 800, 32, 768
    lines = wrap(p["desc"], 40, 2)
    h = 122 + (len(lines) - 1) * 42 + 58 + 36
    body = frame(t, W, h) + text(x, 70, p["name"], t["ink"], 40, 700) + stars(t, xr, 68, p["stars"], 30)
    for i, line in enumerate(lines):
        body += text(x, 122 + i * 42, line, t["sub"], 30)
    body += lang(t, x, h - 36, p["lang"], 28)
    return svg(W, h + 16, f'{p["name"]}: {p["desc"]}', body)


def prompt(t, x, y, cmd, size):
    return text(x, y, "$", t["ok"], size, 700) + text(x + width("$ ", size), y, cmd, t["ink"], size)


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
    grow = f'<animate attributeName="width" values="0;{w}" dur="1.4s" fill="freeze" calcMode="spline" keySplines=".2 .8 .2 1"/>'
    clip = f'<clipPath id="grow"><rect x="{x}" y="{y}" width="{w}" height="{h}">{grow}</rect></clipPath>'
    return clip + f'<g clip-path="url(#grow)">{"".join(out)}</g>'


def stat(t, x, y, i, label, n, size):
    num = f"{n:,}"
    return text(x, y, num, t["spec"][i], size, 700) + text(x + width(num + " ", size), y, label, t["sub"], size)


def when(date):
    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ").strftime("%b %d")


def chrome(t, W, H, bh, size):
    dots = "".join(f'<circle cx="{bh / 2 + i * bh * 0.46:g}" cy="{bh / 2:g}" r="{bh / 8:g}" fill="{c}"/>' for i, c in enumerate(t["spec"][::2]))
    head = f'<path d="M.5 {bh}V14.5a14 14 0 0 1 14-14h{W - 29}a14 14 0 0 1 14 14V{bh}z" fill="{t["fill"]}"/>'
    rule = f'<line x1=".5" y1="{bh}" x2="{W - .5}" y2="{bh}" stroke="{t["line"]}"/>'
    return frame(t, W, H) + head + rule + dots + text(W / 2, bh / 2 + size * 0.36, "cj@github ~", t["faint"], size, 400, "middle")


def tail(t, x, W, y, s, stamp):
    cx = x + width("$ ", s) + s * 0.045
    blink = '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1.2s" repeatCount="indefinite"/>'
    cur = f'<rect x="{cx:g}" y="{y - s * 0.73:g}" width="{s * 0.51:g}" height="{s * 0.73:g}" fill="{t["sub"]}">{blink}</rect>'
    return prompt(t, x, y, "", s) + cur + text(W - x, y, stamp, t["faint"], round(s * 0.7), 400, "end")


def term_desk(t, d, stamp):
    W, H, x, s = 1200, 520, 36, 22
    b = chrome(t, W, H, 48, 16) + prompt(t, x, 100, "gh stats", s)
    cx = x
    for i, (label, n) in enumerate(p for p in d["stats"] if p[1] is not None):
        b += stat(t, cx, 136, i, label, n, s)
        cx += width(f"{n:,} {label}", s) + 48
    items = lang_items(t, d)
    b += prompt(t, x, 192, "langs", s) + bar(x, 212, W - 2 * x, 14, items)
    lx = x
    for label, _, c in items:
        b += f'<rect x="{lx:g}" y="{250}" width="14" height="14" rx="3" fill="{c}"/>'
        b += text(lx + 22, 263, label, t["sub"], 18)
        lx += 22 + width(label, 18) + 36
    b += prompt(t, x, 318, "git log -3", s)
    col = max((len(n) for n, _, _ in d["log"]), default=0) + 2
    room = int((W - 2 * x) / width("x", s)) - col - 8
    for i, (name, date, msg) in enumerate(d["log"]):
        y = 354 + i * 36
        msg = wrap(msg, room, 1)[0]
        b += text(x, y, name, t["spec"][(i * 2) % 6], s, 700) + text(x + width("x" * col, s), y, when(date), t["faint"], s)
        b += text(x + width("x" * (col + 8), s), y, msg, t["ink"], s)
    return svg(W, H, "Stats, languages and latest commits", b + tail(t, x, W, 482, s, stamp))


def term_mobile(t, d, stamp):
    W, H, x, s = 800, 884, 32, 28
    b = chrome(t, W, H, 56, 20) + prompt(t, x, 124, "gh stats", s)
    for i, (label, n) in enumerate(p for p in d["stats"] if p[1] is not None):
        b += stat(t, x + (i % 2) * 384, 172 + (i // 2) * 46, i, label, n, s)
    items = lang_items(t, d)
    b += prompt(t, x, 290, "langs", s) + bar(x, 312, W - 2 * x, 18, items)
    for i, (label, _, c) in enumerate(items):
        lx, ly = x + (i % 3) * 248, 372 + (i // 3) * 42
        b += f'<rect x="{lx}" y="{ly - 16}" width="18" height="18" rx="4" fill="{c}"/>' + text(lx + 28, ly, label, t["sub"], 22)
    b += prompt(t, x, 486, "git log -3", s)
    for i, (name, date, msg) in enumerate(d["log"]):
        y = 534 + i * 100
        b += text(x, y, name, t["spec"][(i * 2) % 6], s, 700) + text(W - x, y, when(date), t["faint"], s, 400, "end")
        b += text(x, y + 40, wrap(msg, 43, 1)[0], t["ink"], s)
    return svg(W, H, "Stats, languages and latest commits", b + tail(t, x, W, 846, s, stamp))


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    out.mkdir(parents=True, exist_ok=True)
    data = gather()
    stamp = "updated " + datetime.now(timezone.utc).strftime("%b %d, %H:%M UTC")
    cards = [(k, project(k), featured_desk, featured_mobile) for k in FEATURED] + [(k, project(k), more_desk, more_mobile) for k in MORE]
    for name, t in THEMES.items():
        (out / f"now-{name}.svg").write_text(term_desk(t, data, stamp))
        (out / f"now-{name}-mobile.svg").write_text(term_mobile(t, data, stamp))
        for key, p, desk, mobile in cards:
            (out / f"{key}-{name}.svg").write_text(desk(t, p, key))
            (out / f"{key}-{name}-mobile.svg").write_text(mobile(t, p, key))
