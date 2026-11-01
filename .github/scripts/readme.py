from kit import ROOT
from now import FEATURED, MORE, USER

RAW = f"https://raw.githubusercontent.com/{USER}/{USER}/output"
SMALL = "(max-width: 600px)"


def picture(base, alt):
    sources = "".join(
        f'<source media="(prefers-color-scheme: {name}){q}" srcset="{base}-{name}{suffix}.svg">'
        for q, suffix in ((f" and {SMALL}", "-mobile"), ("", ""))
        for name in ("dark", "light")
    )
    return f'<picture>{sources}<img src="{base}-dark.svg" alt="{alt}" width="100%"></picture>'


def card(key):
    return f'<a href="https://github.com/{USER}/{key}">{picture(f"{RAW}/{key}", key)}</a>'


if __name__ == "__main__":
    parts = [
        "\n".join(card(k) for k in FEATURED + MORE),
        picture(f"{RAW}/now", "Stats, languages and latest commits, refreshed every 6 hours"),
    ]
    (ROOT / "README.md").write_text("".join(f"<p>\n{p}\n</p>\n\n" for p in parts).rstrip() + "\n")
