#!/usr/bin/env python3
"""Write the list of countries into the mod's Workshop description.

Workshop search reads the description, so a player who searches "Muisca"
finds the mod only if the page names it. The list is the paragraphs under
the description's Countries heading, rewritten here from the same data the
Atlas shows, so it cannot fall behind the mod.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKSHOP_DESCRIPTION = "workshop_description.bbcode"
COUNTRIES_SECTION = re.compile(r"(\[h2\]Countries\[/h2\]\n).*?(?=\n\[h2\])", re.S)
# Steam refuses a longer description.
STEAM_DESCRIPTION_LIMIT = 8000

LOC_REFERENCE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)\$")
SCRIPT_MARKUP = re.compile(r"\[[^\]]*\]")


def resolve(value: str, strings: dict[str, str], depth: int = 0) -> str:
    if depth > 5:
        return value
    value = LOC_REFERENCE.sub(
        lambda m: resolve(strings[m.group(1)], strings, depth + 1)
        if m.group(1) in strings else m.group(0),
        value,
    )
    return SCRIPT_MARKUP.sub("", value).strip()


def country_name(record: dict, strings: dict[str, str]) -> str:
    """The name the Atlas lists the formable under, without its variant."""
    tag = record.get("tag")
    for key in (tag, record.get("name"), record["block_key"], tag and f"{tag}_f"):
        # A tag's own name can be blank (TAB): the next key then names it.
        name = resolve(strings.get(key) or "", strings) if key else ""
        if name:
            return name
    return re.sub(r"_f$", "", record["block_key"]).replace("_", " ")


def formable_title(record: dict, strings: dict[str, str]) -> str:
    return resolve(strings.get(record["block_key"]) or "", strings)


def names(records: list[dict], shared: set[str], strings: dict[str, str]) -> str:
    """Two countries can share a name (Tibet and the Tibetan Empire): each
    is then listed by its formable's own title, as the Atlas does."""
    listed = set()
    for record in records:
        name = country_name(record, strings)
        listed.add(formable_title(record, strings) or name if name in shared else name)
    return ", ".join(sorted(listed, key=str.casefold))


def names_shared_by_tags(records: list[dict], strings: dict[str, str]) -> set[str]:
    tags_by_name: dict[str, set] = {}
    for record in records:
        tags_by_name.setdefault(country_name(record, strings), set()).add(record.get("tag"))
    return {name for name, tags in tags_by_name.items() if len(tags) > 1}


def main() -> int:
    config = yaml.safe_load((REPO_ROOT / "build.config.yaml").read_text())
    data_dir = REPO_ROOT / config["build"]["web_data_dir"]
    description = Path(config["mod_root"]).expanduser() / WORKSHOP_DESCRIPTION

    formables = json.loads((data_dir / "formables.json").read_text(encoding="utf-8"))["formables"]
    strings = json.loads((data_dir / "loc.json").read_text(encoding="utf-8"))["strings"]
    new = [r for r in formables if r["source"] == "mod_new"]
    enhanced = [r for r in formables if r["source"].startswith("vanilla+mod")]

    text = description.read_text(encoding="utf-8")
    if not COUNTRIES_SECTION.search(text):
        print(f"{description} has no Countries section to fill", file=sys.stderr)
        return 1
    shared = names_shared_by_tags(new + enhanced, strings)
    section = (
        f"[b]New[/b] {names(new, shared, strings)}\n\n"
        f"[b]From the base game[/b] {names(enhanced, shared, strings)}\n"
    )
    text = COUNTRIES_SECTION.sub(lambda m: m.group(1) + section, text)
    if len(text) > STEAM_DESCRIPTION_LIMIT:
        print(f"{description} is {len(text)} characters, over Steam's "
              f"{STEAM_DESCRIPTION_LIMIT}", file=sys.stderr)
        return 1
    description.write_text(text, encoding="utf-8")
    print(f"wrote {len(new)} new and {len(enhanced)} base game formables into {description}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
