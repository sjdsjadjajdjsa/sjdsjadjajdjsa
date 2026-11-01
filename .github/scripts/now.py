import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from html import escape
from pathlib import Path

USER = os.environ.get("PROFILE_USER", "sjdsjadjajdjsa")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN", "")
SPECTRUM = ["#ff5f6d", "#ffa25f", "#f9e27d", "#7ee2a8", "#6fd3ff", "#c69bff"]
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
THEMES = {
    "dark": dict(bg="#0e0d14", bar="#15131f", line="#2a2740", ink="#f2f0ff", sub="#8f8ca8", ok="#7ee2a8", rest="#3a3750", spec=SPECTRUM),
    "light": dict(bg="#fbfaff", bar="#f1eef9", line="#e3dff0", ink="#16141f", sub="#6b6882", ok="#1f9d63", rest="#cfcadf", spec=["#e5354a", "#e0761f", "#b58900", "#1f9d63", "#0a8fd1", "#8b5cf6"]),
}
W = 1200
CH = 0.6


def call(url, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None)
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def gather():
    api = "https://api.github.com"
    user = call(f"{api}/users/{USER}")
    repos = [
        r for r in call(f"{api}/users/{USER}/repos?per_page=100&type=owner&sort=pushed")
        if not r["fork"] and not r["archived"] and r["name"] != USER
    ]
    langs = {}
    for r in repos:
        for k, v in call(r["languages_url"]).items():
            langs[k] = langs.get(k, 0) + v
    log = []
    for r in repos[:3]:
        c = call(f"{api}/repos/{r['full_name']}/commits?per_page=1")[0]["commit"]
        log.append((r["name"], c["committer"]["date"], c["message"].splitlines()[0]))
    try:
        q = f'query{{user(login:"{USER}"){{contributionsCollection{{contributionCalendar{{totalContributions}}}}}}}}'
        total = call(f"{api}/graphql", {"query": q})["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    except Exception:
        total = None
    return dict(
        stars=sum(r["stargazers_count"] for r in repos),
        repos=len(repos),
        followers=user["followers"],
        contributions=total,
        langs=sorted(langs.items(), key=lambda x: -x[1]),
        log=log,
        projects=[(r["name"], r["description"] or "", r["language"] or "", r["stargazers_count"]) for r in repos],
    )


def text(x, y, s, fill, size=22, weight=400):
    return f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" font-weight="{weight}" fill="{fill}" xml:space="preserve">{escape(s)}</text>'


def width(s, size=22):
    return len(s) * size * CH


def prompt(t, y, cmd):
    return text(48, y, "$", t["ok"], weight=700) + text(48 + width("$ "), y, cmd, t["ink"])


def langs_rows(t, d, y):
    top = d["langs"][:5]
    rest = sum(v for _, v in d["langs"][5:])
    items = [(k, v, t["spec"][i]) for i, (k, v) in enumerate(top)] + ([("Other", rest, t["rest"])] if rest else [])
    total = sum(v for _, v, _ in items) or 1
    span, x, bar, legend, lx = W - 96, 48.0, [], [], 48.0
    for k, v, c in items:
        w = span * v / total
        bar.append(f'<rect x="{x:.1f}" y="{y}" width="{max(w - 3, 1):.1f}" height="14" rx="3" fill="{c}"/>')
        x += w
        label = f"{k} {v * 100 / total:.0f}%"
        legend.append(f'<rect x="{lx:.1f}" y="{y + 38}" width="12" height="12" rx="3" fill="{c}"/>' + text(lx + 20, y + 49, label, t["sub"], 18))
        lx += 20 + width(label, 18) + 32
    clip = f'<clipPath id="grow"><rect x="48" y="{y}" width="{span}" height="14"><animate attributeName="width" values="0;0;{span}" keyTimes="0;.45;1" dur="2s" fill="freeze" calcMode="spline" keySplines="0 0 1 1;.2 .8 .2 1"/></rect></clipPath>'
    return clip + f'<g clip-path="url(#grow)">{"".join(bar)}</g>' + "".join(legend)


def stats_row(t, d, y):
    parts = [("stars", d["stars"]), ("repos", d["repos"]), ("contributions", d["contributions"]), ("followers", d["followers"])]
    out, x = [], 48.0
    for i, (label, n) in enumerate(p for p in parts if p[1] is not None):
        num = f"{n:,}"
        out.append(text(x, y, num, t["spec"][i], weight=700) + text(x + width(num + " "), y, label, t["sub"]))
        x += width(f"{num} {label}") + 44
    return "".join(out)


def hue(t, name):
    return t["spec"][sum(map(ord, name)) % 6]


def log_rows(t, d, y):
    out, col = [], max((len(n) for n, _, _ in d["log"]), default=0) + 3
    room = int((W - 96) / width("x")) - col - 8
    for i, (name, date, msg) in enumerate(d["log"]):
        when = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ").strftime("%b %d")
        msg = msg if len(msg) <= room else msg[: room - 1].rstrip() + "…"
        row = y + i * 36
        out.append(text(48, row, name, hue(t, name), weight=700) + text(48 + width("x" * col), row, when, t["sub"]) + text(48 + width("x" * (col + 8)), row, msg, t["ink"]))
    return out


def group(i, body):
    return f'<g class="l" style="animation-delay:{i * 0.22:.2f}s">{body}</g>'


STYLE = "<style>.l{animation:in .5s ease-out both}@keyframes in{from{opacity:0;transform:translateY(6px)}}.c{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}</style>"


def card(t, d, stamp):
    rows = [
        prompt(t, 100, "whoami") + text(48, 136, "cj · rust, go and typescript · san francisco", t["sub"]),
        prompt(t, 192, "stats") + stats_row(t, d, 228),
        prompt(t, 284, "langs --by-bytes") + langs_rows(t, d, 302),
        prompt(t, 407, "git log -3 --oneline") + "".join(log_rows(t, d, 443)),
    ]
    h = 610
    dots = "".join(f'<circle cx="{28 + i * 22}" cy="24" r="6" fill="{c}"/>' for i, c in enumerate(SPECTRUM[::2]))
    head = (
        f'<rect x=".5" y=".5" width="{W - 1}" height="{h - 1}" rx="14" fill="{t["bg"]}" stroke="{t["line"]}"/>'
        f'<path d="M.5 48V14.5a14 14 0 0 1 14-14h{W - 29}a14 14 0 0 1 14 14V48z" fill="{t["bar"]}"/>'
        f'<line x1="0" y1="48" x2="{W}" y2="48" stroke="{t["line"]}"/>{dots}'
        + text(W / 2 - width("cj@github: ~", 16) / 2, 30, "cj@github: ~", t["sub"], 16)
    )
    tail = prompt(t, 571, "") + f'<rect class="c" x="{48 + width("$ ")}" y="553" width="12" height="22" fill="{t["ink"]}"/>'
    tail += text(W - 48 - width(stamp, 14), 571, stamp, t["sub"], 14)
    body = "".join(group(i, r) for i, r in enumerate(rows + [tail]))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="cj on GitHub: stats, languages and latest commits">'
        f"{STYLE}{head}{body}</svg>\n"
    )


def tile(t, repo, c, side):
    name, desc, lang, stars = repo
    w, h, gap = 600, 184, 8
    x0, cw, ch = (gap if side == "r" else 0), w - gap, h - 2 * gap
    body = "".join(text(x0 + 28, 90 + i * 26, line, t["sub"], 18) for i, line in enumerate(wrap(desc, 48)))
    star = f"★ {stars}" if stars else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(name)}: {escape(desc)}">'
        f'<clipPath id="r"><rect x="{x0}" width="{cw}" height="{ch}" rx="12"/></clipPath><g clip-path="url(#r)">'
        f'<rect x="{x0}" width="{cw}" height="{ch}" fill="{t["bg"]}"/><rect x="{x0}" width="5" height="{ch}" fill="{c}"/></g>'
        f'<rect x="{x0 + .5}" y=".5" width="{cw - 1}" height="{ch - 1}" rx="12" fill="none" stroke="{t["line"]}"/>'
        + text(x0 + 28, 52, name, t["ink"], 24, 700) + text(x0 + cw - 28 - width(star, 18), 50, star, c, 18, 700) + body
        + f'<circle cx="{x0 + 34}" cy="{ch - 29}" r="6" fill="{c}"/>' + text(x0 + 48, ch - 23, lang, t["sub"], 16)
        + "</svg>\n"
    )


def wrap(s, n, lines=2):
    out, cur = [], ""
    for w in s.split():
        if len(cur) + len(w) + 1 > n:
            out.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    out.append(cur)
    if len(out) > lines:
        out = out[:lines]
        words = out[-1].split()
        while len(" ".join(words)) + 1 > n:
            words.pop()
        out[-1] = " ".join(words).rstrip(" ,.") + "…"
    return out


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    out.mkdir(parents=True, exist_ok=True)
    data = gather()
    stamp = "updated " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    for name, t in THEMES.items():
        (out / f"now-{name}.svg").write_text(card(t, data, stamp))
        for repo in data["projects"]:
            for side in "lr":
                (out / f"repo-{repo[0]}-{name}-{side}.svg").write_text(tile(t, repo, hue(t, repo[0]), side))
