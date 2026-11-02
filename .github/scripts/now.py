import base64
import json
import os
import sys
import urllib.request
from pathlib import Path

from kit import ASSETS, ROOT, THEMES, star, svg, text, width, wrap

USER = os.environ.get("PROFILE_USER", "sjdsjadjajdjsa")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
FEATURED = ["prism", "hanami", "tonal", "nyx"]
HIDDEN = {"web-refs"}
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


def info(r):
    return dict(name=r["name"], desc=r["description"] or "", lang=r["language"] or "", stars=r["stargazers_count"])


def project(name):
    return info(call(f"/repos/{USER}/{name}"))


def gather():
    user = call(f"/users/{USER}")
    repos = [r for r in call(f"/users/{USER}/repos?per_page=100&type=owner&sort=pushed") if not r["fork"] and not r["archived"] and r["name"] != USER]
    langs = {}
    for r in repos:
        for k, v in call(r["languages_url"][len(API):]).items():
            langs[k] = langs.get(k, 0) + v
    return dict(
        stats=[("stars", sum(r["stargazers_count"] for r in repos)), ("projects", len(repos)), ("contributions", contributions()), ("followers", user["followers"])],
        langs=sorted(langs.items(), key=lambda x: -x[1]),
        repos=repos,
    )


def preview(name):
    f = ASSETS / "previews" / f"{name}.jpg"
    return "data:image/jpeg;base64," + base64.b64encode(f.read_bytes()).decode() if f.exists() else None


def frame(t, w, h):
    return frame_at(t, 0, w, h)


def frame_at(t, x, w, h):
    return f'<rect x="{x + .5:g}" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="{t["fill"]}" stroke="{t["line"]}"/>'


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



def grid_desk(t, p, side):
    W, H, gap = 600, 192, 8
    x0, cw, ch = (gap if side == "r" else 0), W - gap, H - 2 * gap
    x, xr = x0 + 28, x0 + cw - 28
    body = frame_at(t, x0, cw, ch) + text(x, 50, p["name"], t["ink"], 26, 700) + stars(t, xr, 48, p["stars"], 20)
    for i, line in enumerate(wrap(p["desc"], 44, 2)):
        body += text(x, 88 + i * 26, line, t["sub"], 20)
    return svg(W, H, f'{p["name"]}: {p["desc"]}', body + lang(t, x, ch - 26, p["lang"], 18))


def grid_mobile(t, p, side):
    W, H, gap = 400, 216, 8
    x0, cw, ch = (gap if side == "r" else 0), W - gap, H - 2 * gap
    x = x0 + 20
    body = frame_at(t, x0, cw, ch) + text(x, 54, p["name"], t["ink"], 30, 700)
    for i, line in enumerate(wrap(p["desc"], 22, 2)):
        body += text(x, 98 + i * 32, line, t["sub"], 26)
    foot = lang(t, x, ch - 24, p["lang"], 24)
    if p["stars"]:
        foot += stars(t, x0 + cw - 20, ch - 24, p["stars"], 24)
    return svg(W, H, f'{p["name"]}: {p["desc"]}', body + foot)


def wide_desk(t, p, side):
    W, H, gap, x = 1200, 192, 8, 28
    ch = H - 2 * gap
    body = frame(t, W, ch) + text(x, 50, p["name"], t["ink"], 26, 700) + stars(t, W - x, 48, p["stars"], 20)
    for i, line in enumerate(wrap(p["desc"], 94, 2)):
        body += text(x, 88 + i * 26, line, t["sub"], 20)
    return svg(W, H, f'{p["name"]}: {p["desc"]}', body + lang(t, x, ch - 26, p["lang"], 18))


def wide_mobile(t, p, side):
    W, H, gap, x = 800, 216, 8, 20
    ch = H - 2 * gap
    body = frame(t, W, ch) + text(x, 54, p["name"], t["ink"], 30, 700)
    for i, line in enumerate(wrap(p["desc"], 46, 2)):
        body += text(x, 98 + i * 32, line, t["sub"], 26)
    foot = lang(t, x, ch - 24, p["lang"], 24) + stars(t, W - x, ch - 24, p["stars"], 24)
    return svg(W, H, f'{p["name"]}: {p["desc"]}', body + foot)

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


def term_desk(t, d):
    W, H, x, s = 1200, 296, 36, 22
    b = chrome(t, W, H, 48, 16) + prompt(t, x, 100, "gh stats", s)
    cx = x
    for i, (label, n) in enumerate(p for p in d["stats"] if p[1] is not None):
        if i:
            b += text(cx - width("·  ", s), 136, "·", t["faint"], s)
        b += stat(t, cx, 136, label, n, s)
        cx += width(f"{n:,} {label}", s) + width("   ·  ", s) - width(" ", s)
    items = lang_items(t, d)
    b += prompt(t, x, 192, "langs", s) + bar(x, 210, W - 2 * x, 12, items) + legend(t, x, 256, items, 18)
    return svg(W, H, "Stars, projects, contributions, followers and languages", b)


def term_mobile(t, d):
    W, H, x, s = 800, 460, 32, 28
    b = chrome(t, W, H, 56, 20) + prompt(t, x, 124, "gh stats", s)
    for i, (label, n) in enumerate(p for p in d["stats"] if p[1] is not None):
        b += stat(t, x + (i % 2) * 384, 172 + (i // 2) * 46, label, n, s)
    items = lang_items(t, d)
    b += prompt(t, x, 290, "langs", s) + bar(x, 310, W - 2 * x, 16, items)
    b += legend(t, x, 370, items, 22, 3, 248, 42)
    return svg(W, H, "Stars, projects, contributions, followers and languages", b)


RAW = f"https://raw.githubusercontent.com/{USER}/{USER}/output"


def tag(key, alt, w):
    base = f"{RAW}/{key}"
    src = "".join(
        f'<source media="(prefers-color-scheme: {m}){q}" srcset="{base}-{m}{x}.svg">'
        for q, x in ((" and (max-width: 600px)", "-mobile"), ("", ""))
        for m in ("dark", "light")
    )
    return f'<picture>{src}<img src="{base}-dark.svg" alt="{alt}" width="{w}"></picture>'


def link(key, w):
    return f'<a href="https://github.com/{USER}/{key}">{tag(key, key, w)}</a>'


def layout(grid):
    rows = [link(k, "100%") for k in FEATURED]
    for i in range(0, len(grid) - 1, 2):
        rows.append(link(grid[i], "50%") + link(grid[i + 1], "50%"))
    if len(grid) % 2:
        rows.append(link(grid[-1], "100%"))
    stats = tag("now", "Stars, projects, contributions, followers and languages, refreshed every 6 hours", "100%")
    return f"<p>\n{chr(10).join(rows)}\n</p>\n\n<p>\n{stats}\n</p>\n"


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    out.mkdir(parents=True, exist_ok=True)
    data = gather()
    rest = [r for r in data["repos"] if r["name"] not in FEATURED and r["name"] not in HIDDEN]
    rest.sort(key=lambda r: r["created_at"], reverse=True)
    rest.sort(key=lambda r: -r["stargazers_count"])
    grid = [r["name"] for r in rest]
    cards = [(k, project(k), featured_desk, featured_mobile, k) for k in FEATURED]
    for i, r in enumerate(rest):
        lone = i == len(rest) - 1 and len(rest) % 2
        cards.append((r["name"], info(r), wide_desk if lone else grid_desk, wide_mobile if lone else grid_mobile, "lr"[i % 2]))
    for m, t in THEMES.items():
        (out / f"now-{m}.svg").write_text(term_desk(t, data))
        (out / f"now-{m}-mobile.svg").write_text(term_mobile(t, data))
        for key, p, desk, mobile, arg in cards:
            (out / f"{key}-{m}.svg").write_text(desk(t, p, arg))
            (out / f"{key}-{m}-mobile.svg").write_text(mobile(t, p, arg))
    (ROOT / "README.md").write_text(layout(grid))
