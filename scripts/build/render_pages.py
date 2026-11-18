#!/usr/bin/env python3
"""Render the site's text pages.

Each data/pages/<name>.md becomes dist/<name>.html: the text before the first
heading opens the page, every heading starts a panel, and the headings are
listed in the sidebar, which is the Atlas's own. A picture is written ![what it shows](img/name.png) and
lives in dist/img/. The file starts with a
YAML frontmatter block carrying `title`. Every heading gets an id made from
its text, so other pages (the Workshop description among them) can link to
one section: features.html#destiny-trees.
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

import markdown
import yaml
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
PAGES_DIR = REPO_ROOT / "data" / "pages"
# The mod's Workshop description links to sections of these pages, so a
# renamed heading would leave a dead link on a page 11,000 subscribers see.
WORKSHOP_DESCRIPTION = "workshop_description.bbcode"
WORKSHOP_SECTION_LINK = re.compile(r"national_destinies_site/([\w-]+\.html)#([\w-]+)")

# A text page wears the Atlas's shell: the same sidebar and header, with the
# page's sections where the Atlas lists its formables.
PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>National Destinies, {title}</title>
<link rel="stylesheet" href="app.css" />
<link rel="stylesheet" href="page.css" />
</head>
<body>
<div id="app">
  <aside id="sidebar">
    {sidebar_header}
    <nav id="page-sections" aria-label="Sections">
{section_links}
    </nav>
  </aside>
  <main id="page-pane">
    <div class="page">
      <section class="card page-intro">
        <header><h2>{title}</h2></header>
        <div class="card-body">{intro}</div>
      </section>
      <a class="card atlas-feature" href="index.html">
        <img src="img/atlas.jpg" alt="The Formables Atlas with the Danubian Monarchy selected" />
        <div class="atlas-feature-text">
          <h2>Formables Atlas</h2>
          <p>Every formable country on the map, with what it takes to form it and a guide to its content.</p>
          <span class="atlas-feature-button">Open the Atlas</span>
        </div>
      </a>
{sections}
    </div>
  </main>
</div>
</body>
</html>
"""

ATLAS_SIDEBAR_HEADER = re.compile(r"<header>.*?</header>", re.S)
ATLAS_SUBTITLE = re.compile(r'(<div class="subtitle">).*?(</div>)')
ATLAS_PAGE_LINKS = re.compile(r'(?:<a class="features-link".*?</a>\s*)+')
SITE_PAGES = [("index.html", "Formables Atlas"), ("features.html", "Features"), ("banks.html", "Banks")]


def sidebar_header(dist_dir: Path, title: str, own_file: str) -> str:
    """The Atlas's own sidebar header, named for this page and linking to the others."""
    atlas = (dist_dir / "index.html").read_text(encoding="utf-8")
    header = ATLAS_SIDEBAR_HEADER.search(atlas).group(0)
    header = ATLAS_SUBTITLE.sub(lambda m: m.group(1) + title + m.group(2), header, count=1)
    links = "\n      ".join(
        f'<a class="features-link" href="{file}">{name}</a>'
        for file, name in SITE_PAGES if file != own_file
    )
    return ATLAS_PAGE_LINKS.sub(links + "\n      ", header, count=1)


# The Banks page is drawn in the browser from data/banks.json
# (scripts/build/extract_banks.py) by dist/banks.js, with the Content tab's cards.
BANKS_PAGE = "banks.html"
BANKS_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>National Destinies, Banks</title>
<link rel="stylesheet" href="app.css" />
<link rel="stylesheet" href="page.css" />
<link rel="stylesheet" href="content.css" />
<link rel="stylesheet" href="banks.css" />
</head>
<body>
<div id="app">
  <aside id="sidebar">
    {sidebar_header}
    <nav id="page-sections" aria-label="Sections"></nav>
  </aside>
  <main id="page-pane">
    <div class="page ct ct-page" id="banks"><p class="ct-note">Loading.</p></div>
  </main>
</div>
<script type="module" src="banks.js"></script>
</body>
</html>
"""


def write_banks_page(dist_dir: Path) -> Path:
    out = dist_dir / BANKS_PAGE
    out.write_text(
        BANKS_TEMPLATE.format(sidebar_header=sidebar_header(dist_dir, "Banks", BANKS_PAGE)),
        encoding="utf-8",
    )
    return out


# The page's backdrop is the Atlas's own map, cut to the band from Europe to
# India where most formables lie, as fractions of the base map's size.
BACKGROUND_SOURCE = REPO_ROOT / "data" / "basemap.png"
BACKGROUND_BAND = (0.40, 0.10, 0.78, 0.52)
BACKGROUND_WIDTH_PX = 2200


def write_background(dist_dir: Path) -> None:
    out = dist_dir / "img" / "map_background.jpg"
    if out.exists() and out.stat().st_mtime >= BACKGROUND_SOURCE.stat().st_mtime:
        return
    Image.MAX_IMAGE_PIXELS = None
    base = Image.open(BACKGROUND_SOURCE).convert("RGB")
    left, top, right, bottom = BACKGROUND_BAND
    band = base.crop((int(base.width * left), int(base.height * top),
                      int(base.width * right), int(base.height * bottom)))
    band.thumbnail((BACKGROUND_WIDTH_PX, BACKGROUND_WIDTH_PX))
    out.parent.mkdir(parents=True, exist_ok=True)
    band.save(out, quality=72)


SECTION = re.compile(r"(<h2 id=\"[^\"]+\">.*?</h2>)(.*?)(?=<h2 |\Z)", re.S)


def as_sections(body_html: str) -> tuple[str, str]:
    """The text before the first heading, and each heading with its text as
    one panel in the look of the Atlas's detail panel."""
    intro = body_html.split("<h2 ", 1)[0].strip()
    sections = "\n".join(
        f'<section class="card">\n<header>{heading}</header>\n'
        f'<div class="card-body">{text.strip()}</div>\n</section>'
        for heading, text in SECTION.findall(body_html)
    )
    return intro, sections


def split_frontmatter(text: str, source: Path) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        raise SystemExit(f"{source}: missing frontmatter")
    meta_text, _, body = text[4:].partition("\n---\n")
    meta = yaml.safe_load(meta_text) or {}
    if "title" not in meta:
        raise SystemExit(f"{source}: frontmatter has no title")
    return meta, body


def render_page(source: Path, dist_dir: Path) -> Path:
    meta, body = split_frontmatter(source.read_text(encoding="utf-8"), source)
    md = markdown.Markdown(
        extensions=["toc", "tables"],
        extension_configs={"toc": {"toc_depth": "2-2"}},
    )
    # A picture opens at full size when clicked: on the page it is shrunk to
    # the panel, and a game screenshot's text is small.
    body_html = re.sub(r'<img alt="[^"]*" src="([^"]+)" />',
                       lambda m: f'<a class="picture" href="{m.group(1)}">{m.group(0)}</a>',
                       md.convert(body))
    intro, sections = as_sections(body_html)
    title = html.escape(str(meta["title"]))
    out = dist_dir / f"{source.stem}.html"
    out.write_text(
        PAGE_TEMPLATE.format(
            title=title,
            sidebar_header=sidebar_header(dist_dir, title, out.name),
            section_links="\n".join(
                f'      <a class="formable-row" href="#{token["id"]}">{token["name"]}</a>'
                for token in md.toc_tokens
            ),
            intro=intro,
            sections=sections,
        ),
        encoding="utf-8",
    )
    return out


def broken_workshop_links(description: Path, dist_dir: Path) -> list[str]:
    """Links in the Workshop description to a section no page has."""
    broken = []
    for page, anchor in WORKSHOP_SECTION_LINK.findall(description.read_text(encoding="utf-8")):
        target = dist_dir / page
        if not target.exists() or f'id="{anchor}"' not in target.read_text(encoding="utf-8"):
            broken.append(f"{page}#{anchor}")
    return broken


def main() -> int:
    config = yaml.safe_load((REPO_ROOT / "build.config.yaml").read_text())
    dist_dir = REPO_ROOT / config["build"]["dist_dir"]
    write_background(dist_dir)
    for source in sorted(PAGES_DIR.glob("*.md")):
        print(f"wrote {render_page(source, dist_dir).relative_to(REPO_ROOT)}")
    print(f"wrote {write_banks_page(dist_dir).relative_to(REPO_ROOT)}")

    description = Path(config["mod_root"]).expanduser() / WORKSHOP_DESCRIPTION
    if description.exists():
        broken = broken_workshop_links(description, dist_dir)
        if broken:
            print(f"{description} links to sections that do not exist: {', '.join(broken)}",
                  file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
