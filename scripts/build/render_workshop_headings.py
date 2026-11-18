#!/usr/bin/env python3
"""Draw the heading pictures the mod's Workshop description shows.

Steam's description is plain text with small blue headings, which reads as
a wall. Each section heading is instead a picture cut from the mod's own
logo: the cloth and the gold rules of its name band, with the heading
lettered on it. Steam shows a description picture only from a web address,
so the pictures are published with this site.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKSHOP_DESCRIPTION = "workshop_description.bbcode"
LOGO = ".metadata/thumbnail.png"
FONT = "loading_screen/fonts/CormorantGaramond/CormorantGaramond-Medium.ttf"
OUTPUT_FOLDER = "workshop"
SITE_URL = "https://trinedi.github.io/national_destinies_site/"

HEADINGS = {
    "features": "Features",
    "guides": "Guides",
    "compatibility": "Compatibility",
    "bugs-and-suggestions": "Bugs and suggestions",
    "translations": "Translations",
    "countries": "Countries",
    "ai-disclaimer": "AI Disclaimer",
}
HEADING_PICTURE = re.compile(
    r"\[img\]" + re.escape(SITE_URL + OUTPUT_FOLDER) + r"/([a-z0-9-]+)\.png\[/img\]"
)

# The widest Steam shows a description picture (its stylesheet caps
# `.workshopItemDescription img` at 630 pixels). The text column is about
# 14 pixels wider, so a picture cannot span it fully.
WIDTH = 630
# In the 512 pixel logo: the rows of the name band with its two gold rules,
# and columns of it left of the lettering, where only cloth shows.
BAND_ROWS = (212, 272)
CLOTH_COLUMNS = (90, 126)
GOLD_RULE_PIXEL = (100, 216)
END_RULE_WIDTH = 3
FONT_SIZE = 34
LETTER_TOP, LETTER_BOTTOM = (247, 240, 205), (203, 181, 118)
SHADOW = (18, 24, 22)


def band(logo: Image.Image) -> Image.Image:
    """The logo's band stretched to the column's width. The cloth is laid
    beside its mirror image so the weave meets itself without a seam."""
    cloth = logo.crop((CLOTH_COLUMNS[0], BAND_ROWS[0], CLOTH_COLUMNS[1], BAND_ROWS[1]))
    pair = Image.new("RGB", (cloth.width * 2, cloth.height))
    pair.paste(cloth, (0, 0))
    pair.paste(ImageOps.mirror(cloth), (cloth.width, 0))
    strip = Image.new("RGB", (WIDTH, cloth.height))
    for x in range(0, WIDTH, pair.width):
        strip.paste(pair, (x, 0))
    gold = logo.getpixel(GOLD_RULE_PIXEL)
    draw = ImageDraw.Draw(strip)
    top, bottom = END_RULE_WIDTH, strip.height - END_RULE_WIDTH
    draw.rectangle((0, top, END_RULE_WIDTH - 1, bottom), fill=gold)
    draw.rectangle((WIDTH - END_RULE_WIDTH, top, WIDTH - 1, bottom), fill=gold)
    return strip


def heading(strip: Image.Image, text: str, font: ImageFont.FreeTypeFont) -> Image.Image:
    picture = strip.copy()
    left, top, right, bottom = ImageDraw.Draw(picture).textbbox((0, 0), text, font=font)
    x = (picture.width - (right - left)) // 2 - left
    y = (picture.height - (bottom - top)) // 2 - top

    shadow = Image.new("L", picture.size, 0)
    ImageDraw.Draw(shadow).text((x + 1, y + 3), text, font=font, fill=200)
    picture.paste(SHADOW, mask=shadow.filter(ImageFilter.GaussianBlur(1.6)))

    letters = Image.new("L", picture.size, 0)
    ImageDraw.Draw(letters).text((x, y), text, font=font, fill=255)
    fade = Image.new("RGB", picture.size)
    fade_draw = ImageDraw.Draw(fade)
    for row in range(picture.height):
        share = min(1.0, max(0.0, (row - (y + top)) / max(1, bottom - top)))
        fade_draw.line(
            (0, row, picture.width, row),
            fill=tuple(round(a + (b - a) * share) for a, b in zip(LETTER_TOP, LETTER_BOTTOM)),
        )
    picture.paste(fade, mask=letters)
    return picture


def main() -> int:
    config = yaml.safe_load((REPO_ROOT / "build.config.yaml").read_text())
    mod_root = Path(config["mod_root"]).expanduser()
    out_dir = REPO_ROOT / config["build"]["dist_dir"] / OUTPUT_FOLDER

    used = HEADING_PICTURE.findall((mod_root / WORKSHOP_DESCRIPTION).read_text(encoding="utf-8"))
    unknown = sorted(set(used) - set(HEADINGS))
    if unknown:
        print(f"the Workshop description shows heading pictures this script cannot "
              f"letter: {', '.join(unknown)}. Add them to HEADINGS.", file=sys.stderr)
        return 1

    logo = Image.open(mod_root / LOGO).convert("RGB")
    font = ImageFont.truetype(str(Path(config["eu5_game_root"]).expanduser() / FONT), FONT_SIZE)
    strip = band(logo)
    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in out_dir.glob("*.png"):
        if stale.stem not in used:
            stale.unlink()
    for slug in dict.fromkeys(used):
        heading(strip, HEADINGS[slug], font).save(out_dir / f"{slug}.png")
    print(f"drew {len(set(used))} Workshop heading pictures into {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
