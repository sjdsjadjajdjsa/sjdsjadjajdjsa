import math
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont
from kit import ASSETS, THEMES, svg, text
from optics import prism

GLYPHS = {}
for _w, _n in ((400, "Regular"), (700, "Bold")):
    _f = TTFont(ASSETS / "fonts" / f"mono-{_n}.woff2")
    GLYPHS[_w] = (_f.getGlyphSet(), _f.getBestCmap())


def bounds(ch, weight):
    gs, cmap = GLYPHS[weight]
    pen = BoundsPen(gs)
    gs[cmap[ord(ch)]].draw(pen)
    return pen.bounds


def ink_x(x, s, size, weight):
    return x - bounds(s[0], weight)[0] * size / 1000


def ink_right(x, s, size, weight):
    return x + (len(s) - 1) * 0.6 * size + bounds(s[-1], weight)[2] * size / 1000


def title(t, x, top, name, tag, lines):
    b = top + bounds("j", 700)[3] * name / 1000
    nx = ink_x(x, "cj", name, 700)
    out = [text(nx, b, "cj", t["ink"], name, 700)]
    uy = b - bounds("j", 700)[1] * name / 1000 + round(name * 0.1)
    uh = round(name * 0.05)
    out.append(f'<rect x="{x}" y="{uy:g}" width="{ink_right(nx, "cj", name, 700) - x:g}" height="{uh}" rx="{uh / 2:g}" fill="url(#spec)"/>')
    b = uy + uh + round(tag * 1.75)
    for i, line in enumerate(lines):
        lx = ink_x(x, line, tag, 400)
        out.append(text(lx, b + i * round(tag * 1.45), line, t["sub"], tag))
    return out, lx, b + (len(lines) - 1) * round(tag * 1.45)


def far(q, d, fx):
    k = (fx - q[0]) / d[0]
    return (q[0] + d[0] * k, q[1] + d[1] * k)


def pts(*ps):
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in ps)


def scene(t, c, W):
    ns = [1.42 + 0.2 * k / 6 for k in range(7)]
    g = prism(c["cx"], c["by"], c["s"], 0.5, 1.5, ns)
    p, d0 = g["p"], g["d0"]
    s = far(p, d0, c["beam"])
    qs = [q for q, _ in g["rays"]]
    fs = [far(q, d, W + 80) for q, d in g["rays"]]
    return g, p, s, qs, fs


def beam(t, p, s):
    L = math.dist(p, s)
    line = f'x1="{s[0]:.2f}" y1="{s[1]:.2f}" x2="{p[0]:.2f}" y2="{p[1]:.2f}"'
    return (
        f'<line {line} stroke="url(#beam)" stroke-width="3" stroke-linecap="round"/>'
        f'<line {line} stroke="{t["streak"]}" stroke-width="3" stroke-linecap="round" stroke-dasharray="70 {L + 300:.0f}">'
        f'<animate attributeName="stroke-dashoffset" values="70;{-L:.0f}" dur="4.8s" repeatCount="indefinite"/></line>'
    )


def bands(t, p, qs, fs, fr):
    spec, out, glow = t["spec"], [], []
    kt = f"0;{fr:.3f};{min(fr + 0.12, 0.98):.3f};1"
    for k, col in enumerate(spec):
        poly = pts(qs[k], qs[k + 1], fs[k + 1], fs[k])
        glow.append(f'<polygon points="{poly}" fill="{col}"/>')
        out.append(
            f'<polygon points="{pts(p, qs[k], qs[k + 1])}" fill="{col}" opacity=".45"/>'
            f'<polygon points="{poly}" fill="{col}" opacity=".86">'
            f'<animate attributeName="opacity" values=".86;.86;1;.86" keyTimes="{kt}" dur="4.8s" repeatCount="indefinite"/></polygon>'
        )
    return f'<g filter="url(#glow)" opacity="{t["glow"]}">{"".join(glow)}</g>' + "".join(out)


def inset(a, l, f, k):
    x, y = a[0] + f * (l[0] - a[0]), a[1] + f * (l[1] - a[1])
    return (x + k * math.sqrt(3) / 2, y + k / 2)


def glass(t, g):
    a, l, r = g["a"], g["l"], g["r"]
    u, v = (inset(a, l, f, 7) for f in (0.14, 0.86))
    return (
        f'<polygon points="{pts(a, l, r)}" fill="url(#glass)" stroke="{t["edge"]}" stroke-width="2" stroke-linejoin="round"/>'
        f'<line x1="{u[0]:.2f}" y1="{u[1]:.2f}" x2="{v[0]:.2f}" y2="{v[1]:.2f}" stroke="{t["edge"]}" stroke-opacity=".25" stroke-width="1"/>'
    )


LOOK = {
    "dark": dict(bg0="#1d1a36", bg1="#0c0b12", beam="#ffffff", streak="#ffffff", edge="#ffffff", pane="#ffffff", glow=".5", pa=".16", rim="#ffffff17"),
    "light": dict(bg0="#ffffff", bg1="#eceaf5", beam="#34304a", streak="#ffffff", edge="#2b2838", pane="#2b2838", glow=".3", pa=".06", rim="#1b1a2417"),
}


def defs(t, s, p, W, H):
    stops = "".join(f'<stop offset="{i / 5:.1f}" stop-color="{c}"/>' for i, c in enumerate(t["spec"]))
    return (
        f'<defs><linearGradient id="spec">{stops}</linearGradient>'
        f'<linearGradient id="beam" gradientUnits="userSpaceOnUse" x1="{s[0]:.2f}" y1="{s[1]:.2f}" x2="{p[0]:.2f}" y2="{p[1]:.2f}">'
        f'<stop offset="0" stop-color="{t["beam"]}" stop-opacity="0"/><stop offset=".6" stop-color="{t["beam"]}"/></linearGradient>'
        f'<linearGradient id="glass" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t["pane"]}" stop-opacity="{t["pa"]}"/><stop offset="1" stop-color="{t["pane"]}" stop-opacity=".03"/></linearGradient>'
        f'<radialGradient id="bg" cx=".72" cy=".38" r=".85"><stop offset="0" stop-color="{t["bg0"]}"/><stop offset="1" stop-color="{t["bg1"]}"/></radialGradient>'
        f'<filter id="glow" x="-10%" y="-30%" width="120%" height="160%"><feGaussianBlur stdDeviation="12"/></filter>'
        f'<clipPath id="frame"><rect width="{W}" height="{H}" rx="14"/></clipPath></defs>'
    )


LINES = ["I build tools for the terminal,", "the desktop and Spotify."]
DESK = dict(W=1200, H=320, x=88, top=None, name=120, tag=26, cx=880, by=212, s=200, beam=620)
MOBILE = dict(W=800, H=600, x=56, top=64, name=128, tag=36, cx=480, by=520, s=190, beam=-40)


def cursor(t, lx, b, tag):
    x = lx + (len(LINES[-1]) + 1.075) * 0.6 * tag
    return (
        f'<rect x="{x:.2f}" y="{b - 0.73 * tag:.2f}" width="{0.51 * tag:.2f}" height="{0.73 * tag:.2f}" fill="{t["sub"]}">'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1.2s" repeatCount="indefinite"/></rect>'
    )


def block(t, c):
    top = c["top"]
    if top is None:
        _, _, b = title(t, c["x"], 0, c["name"], c["tag"], LINES)
        top = (c["H"] - b - 0.2 * c["tag"]) / 2
    parts, lx, b = title(t, c["x"], top, c["name"], c["tag"], LINES)
    return "".join(parts) + cursor(t, lx, b, c["tag"])


def banner(name, c):
    t = {**THEMES[name], **LOOK[name]}
    W, H = c["W"], c["H"]
    g, p, s, qs, fs = scene(t, c, W)
    L = math.dist(p, s)
    art = beam(t, p, s) + bands(t, p, qs, fs, L / (L + 70)) + glass(t, g)
    body = (
        defs(t, s, p, W, H)
        + f'<g clip-path="url(#frame)"><rect width="{W}" height="{H}" fill="url(#bg)"/>{art}</g>'
        + f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="13.5" fill="none" stroke="{t["rim"]}"/>'
        + block(t, c)
    )
    return svg(W, H, "cj. I build tools for the terminal, the desktop and Spotify.", body)


if __name__ == "__main__":
    for name in THEMES:
        (ASSETS / f"banner-{name}.svg").write_text(banner(name, DESK))
        (ASSETS / f"banner-{name}-mobile.svg").write_text(banner(name, MOBILE))
