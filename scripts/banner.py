from pathlib import Path

SPECTRUM = ["#ff5f6d", "#ffa25f", "#f9e27d", "#7ee2a8", "#6fd3ff", "#c69bff"]
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
THEMES = {
    "dark": dict(bg0="#1b1833", bg1="#0b0b10", ink="#f2f0ff", sub="#a9a6c4", beam="#ffffff", glass="#ffffff", dot="#ffffff"),
    "light": dict(bg0="#ffffff", bg1="#ece9f7", ink="#16141f", sub="#5d5a73", beam="#2a2735", glass="#2a2735", dot="#2a2735"),
}


def rays():
    ex, ey = 905, 158
    out = []
    for i, c in enumerate(SPECTRUM):
        y = 62 + i * 40
        d = i * 0.35
        out.append(
            f'<polygon points="{ex},{ey - 3 + i * 1.2} {ex},{ey + 1 + i * 1.2} 1200,{y + 20} 1200,{y}" fill="{c}" opacity=".9">'
            f'<animate attributeName="opacity" values=".55;1;.55" dur="3.6s" begin="{d}s" repeatCount="indefinite"/></polygon>'
            f'<line x1="{ex}" y1="{ey - 1 + i * 1.2}" x2="1200" y2="{y + 10}" stroke="#fff" stroke-opacity=".55" stroke-width="2" stroke-dasharray="6 46">'
            f'<animate attributeName="stroke-dashoffset" from="52" to="0" dur="1.2s" begin="{d}s" repeatCount="indefinite"/></line>'
        )
    return "".join(out)


def banner(t):
    stops = "".join(f'<stop offset="{i / 5:.1f}" stop-color="{c}"/>' for i, c in enumerate(SPECTRUM))
    label = "cj. I build tools for the terminal, the desktop and Spotify."
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="320" viewBox="0 0 1200 320" role="img" aria-label="{label}">'
        f'<defs><linearGradient id="g" x1="0" x2="1">{stops}'
        f'<animate attributeName="x1" values="0;-1;0" dur="8s" repeatCount="indefinite"/>'
        f'<animate attributeName="x2" values="1;2;1" dur="8s" repeatCount="indefinite"/></linearGradient>'
        f'<radialGradient id="b" cx=".7" cy=".45" r=".9"><stop offset="0" stop-color="{t["bg0"]}"/><stop offset="1" stop-color="{t["bg1"]}"/></radialGradient>'
        f'<pattern id="p" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="{t["dot"]}" fill-opacity=".07"/></pattern>'
        f'<filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="6"/></filter>'
        f'<clipPath id="c"><rect width="1200" height="320" rx="16"/></clipPath></defs>'
        f'<g clip-path="url(#c)"><rect width="1200" height="320" fill="url(#b)"/><rect width="1200" height="320" fill="url(#p)"/>'
        f'<line x1="560" y1="214" x2="819" y2="150" stroke="{t["beam"]}" stroke-width="4" stroke-linecap="round" opacity=".9"/>'
        f'<line x1="560" y1="214" x2="819" y2="150" stroke="{t["beam"]}" stroke-width="2" stroke-dasharray="6 40" stroke-opacity=".9">'
        f'<animate attributeName="stroke-dashoffset" from="46" to="0" dur="1.2s" repeatCount="indefinite"/></line>'
        f'<polygon points="819,148 819,152 905,161 905,155" fill="{t["beam"]}" opacity=".45"/>'
        f'<g filter="url(#glow)" opacity=".7">{rays()}</g>{rays()}'
        f'<polygon points="865,62 775,232 955,232" fill="{t["glass"]}" fill-opacity=".06" stroke="{t["glass"]}" stroke-opacity=".75" stroke-width="2" stroke-linejoin="round"/>'
        f'<polygon points="865,92 802,214 928,214" fill="none" stroke="{t["glass"]}" stroke-opacity=".12" stroke-width="1"/></g>'
        f'<text x="80" y="142" font-family="{MONO}" font-size="96" font-weight="700" fill="{t["ink"]}">cj</text>'
        f'<rect x="80" y="166" width="220" height="8" rx="4" fill="url(#g)"/>'
        f'<text font-family="{MONO}" font-size="24" fill="{t["sub"]}"><tspan x="80" y="220">I build tools for the terminal,</tspan>'
        f'<tspan x="80" y="254">the desktop and Spotify.</tspan></text>'
        f'<rect x="440" y="236" width="13" height="22" fill="{t["sub"]}">'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1.1s" repeatCount="indefinite"/></rect>'
        f'</svg>\n'
    )


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent / "assets"
    for name, t in THEMES.items():
        (root / f"banner-{name}.svg").write_text(banner(t))
