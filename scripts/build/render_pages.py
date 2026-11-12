#!/usr/bin/env python3
"""Render the site's text pages.

Each data/pages/<name>.md becomes dist/<name>.html. The file starts with a
YAML frontmatter block carrying `title`. Every heading gets an id made from
its text, so other pages (the Workshop description among them) can link to
one section: features.html#destiny-trees. A line holding [TOC] becomes the
list of sections.
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

import markdown
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
PAGES_DIR = REPO_ROOT / "data" / "pages"
WORKSHOP_URL = "https://steamcommunity.com/sharedfiles/filedetails/?id=3668193813"
# The mod's Workshop description links to sections of these pages, so a
# renamed heading would leave a dead link on a page 11,000 subscribers see.
WORKSHOP_DESCRIPTION = "workshop_description.bbcode"
WORKSHOP_SECTION_LINK = re.compile(r"national_destinies_site/([\w-]+\.html)#([\w-]+)")

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title}, National Destinies</title>
<link rel="stylesheet" href="page.css" />
</head>
<body>
<header class="page-header">
  <a class="page-brand" href="index.html">National Destinies</a>
  <nav>
    <a href="index.html">Formables Atlas</a>
    <a href="{workshop_url}" target="_blank" rel="noopener noreferrer">Steam Workshop</a>
  </nav>
</header>
<main class="page">
<h1>{title}</h1>
{body}
</main>
</body>
</html>
"""


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
    body_html = md.convert(body)
    out = dist_dir / f"{source.stem}.html"
    out.write_text(
        PAGE_TEMPLATE.format(
            title=html.escape(str(meta["title"])),
            workshop_url=WORKSHOP_URL,
            body=body_html,
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
    for source in sorted(PAGES_DIR.glob("*.md")):
        print(f"wrote {render_page(source, dist_dir).relative_to(REPO_ROOT)}")

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
