import base64
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"
FONT = "JetBrains Mono"
ADVANCE = 0.6
SPECTRUM = {
    "dark": ["#ff6b7a", "#ffa463", "#f7dc6f", "#7ee2a8", "#6ccfff", "#b99cff"],
    "light": ["#e23a4e", "#e2741c", "#c99a06", "#1f9d63", "#0b8fd3", "#7c5cf2"],
}
THEMES = {
    "dark": dict(ink="#f0eef8", sub="#9b98b3", faint="#6b6884", line="#2b2a3a", fill="#ffffff08", ok="#7ee2a8"),
    "light": dict(ink="#1b1a24", sub="#5f5c74", faint="#8e8aa3", line="#dedbe8", fill="#1b1a2405", ok="#1f9d63"),
}
for _k, _t in THEMES.items():
    _t["spec"] = SPECTRUM[_k]


def font_css():
    faces = []
    for weight, name in ((400, "Regular"), (700, "Bold")):
        data = base64.b64encode((ASSETS / "fonts" / f"mono-{name}.woff2").read_bytes()).decode()
        faces.append(f"@font-face{{font-family:'{FONT}';font-weight:{weight};src:url(data:font/woff2;base64,{data}) format('woff2')}}")
    return "".join(faces) + f"text{{font-family:'{FONT}',ui-monospace,monospace;font-kerning:none}}"


def width(s, size):
    return len(s) * size * ADVANCE


def text(x, y, s, fill, size, weight=400, anchor="start", extra=""):
    a = "" if anchor == "start" else f' text-anchor="{anchor}"'
    b = "" if weight == 400 else f' font-weight="{weight}"'
    return f'<text x="{x:g}" y="{y:g}" font-size="{size}"{b}{a} fill="{fill}" xml:space="preserve"{extra}>{escape(s)}</text>'


def wrap(s, n, lines):
    out, cur = [], ""
    for word in s.split():
        if cur and len(cur) + 1 + len(word) > n:
            out.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}" if cur else word
    out.append(cur)
    if len(out) > lines:
        words = out[lines - 1].split()
        while words and len(" ".join(words)) + 1 > n:
            words.pop()
        out = out[: lines - 1] + [" ".join(words).rstrip(" ,.;:") + "…"]
    return out


STAR = "M0-7.6 2.2-2.4 7.8-2.2 3.4 1.3 4.9 6.7 0 3.6-4.9 6.7-3.4 1.3-7.8-2.2-2.2-2.4z"


def star(x, y, size, fill):
    return f'<path transform="translate({x:g} {y:g}) scale({size / 16:g})" d="{STAR}" fill="{fill}"/>'


def svg(w, h, label, body, style=""):
    head = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(label)}">'
    return head + f"<style>{font_css()}{style}</style>" + body + "</svg>\n"
