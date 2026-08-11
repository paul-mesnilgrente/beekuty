#!/usr/bin/env python3
"""Génère l'image de partage social (Open Graph) du site.

Sortie : assets/images/og-default.png, 1200x630 — le format attendu par
Facebook, WhatsApp, LinkedIn et Twitter/X. PNG plutôt que WebP car tous les
crawlers sociaux ne décodent pas encore le WebP.

    python scripts/make_og_image.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent

WIDTH, HEIGHT = 1200, 630
BACKGROUND = "#F2EFED"  # $wild-sand
INK = "#333333"  # $night-rider
ACCENT = "#74CEB2"  # $downey

LOGO = ROOT / "assets/images/hand_logo.webp"
TITLE_FONT = ROOT / "assets/fonts/tahu.ttf"
BODY_FONT = ROOT / "assets/fonts/unicorns_are_awesome.otf"
OUTPUT = ROOT / "assets/images/og-default.png"

TITLE = "BeeKuty"
TAGLINE = "Institut de beauté & prothésie ongulaire"


def main() -> None:
    canvas = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)

    # Logo à gauche, marges généreuses pour survivre au recadrage carré que
    # certaines plateformes appliquent aux vignettes.
    logo = Image.open(LOGO).convert("RGBA")
    logo_height = 520
    logo_width = round(logo.width * logo_height / logo.height)
    logo = logo.resize((logo_width, logo_height), Image.LANCZOS)
    logo_x = 90
    canvas.paste(logo, (logo_x, (HEIGHT - logo_height) // 2), logo)

    draw = ImageDraw.Draw(canvas)
    text_x = logo_x + logo_width + 70

    title_font = ImageFont.truetype(str(TITLE_FONT), 150)
    tagline_font = ImageFont.truetype(str(BODY_FONT), 38)

    title_box = draw.textbbox((0, 0), TITLE, font=title_font)
    title_height = title_box[3] - title_box[1]
    title_y = HEIGHT // 2 - title_height - 30
    draw.text((text_x - title_box[0], title_y - title_box[1]), TITLE,
              font=title_font, fill=INK)

    rule_y = HEIGHT // 2 + 20
    draw.rounded_rectangle(
        [text_x, rule_y, text_x + 150, rule_y + 8], radius=4, fill=ACCENT
    )

    draw.text((text_x, rule_y + 45), TAGLINE, font=tagline_font, fill=INK)

    canvas.save(OUTPUT, "PNG", optimize=True)
    print(f"{OUTPUT.relative_to(ROOT)} — {OUTPUT.stat().st_size // 1024} Ko")


if __name__ == "__main__":
    main()
