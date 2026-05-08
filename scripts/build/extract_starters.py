#!/usr/bin/env python3
"""Derive recommended starting countries for each formable.

Reads:
  - in_game/setup/countries/*.txt        (tag -> culture, religion)
  - main_menu/setup/start/10_countries.txt (tag -> owned locations)
  - in_game/common/cultures/*.txt        (culture -> culture_groups)
  - in_game/common/religions/*.txt       (religion -> religion group)
  - dist/data/formables.json             (formable potential / required geography)
  - dist/data/geography.json             (location/area/region tree)

Writes:
  - dist/data/starters.json: { "<block_key>": {"candidates": [...], "version": 1} }

A candidate is scored on three axes:
  - culture match (formable's culture/has_primary_culture/culture_group gates)
  - religion match (formable's religion/religion_group/has_state_religion gates)
  - geography overlap (tag owns >=1 location inside the formable's must_own /
    locations / areas / regions union)

Top 8 per formable, sorted by score desc then by tag.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import yaml


def expand_path(p: str) -> Path:
    return Path(os.path.expanduser(p)).resolve()


def strip_comments(text: str) -> str:
    return re.sub(r"#[^\n]*", "", text)


def find_balanced_block(body: str, key: str) -> str | None:
    """Find `key = { ... }` and return the inner body (depth-aware)."""
    pat = re.compile(rf"\b{re.escape(key)}\s*=\s*\{{")
    for m in pat.finditer(body):
        start = m.end()
        depth = 1
        i = start
        while i < len(body) and depth > 0:
            if body[i] == "{":
                depth += 1
            elif body[i] == "}":
                depth -= 1
            i += 1
        if depth == 0:
            return body[start:i - 1]
    return None


def parse_country_setup(setup_dir: Path) -> dict[str, dict]:
    """Parse setup/countries/*.txt for tag -> {culture, religion}."""
    out: dict[str, dict] = {}
    block_re = re.compile(r"\b([A-Z][A-Z0-9]{2})\s*=\s*\{")
    for path in sorted(setup_dir.glob("*.txt")):
        text = strip_comments(path.read_text(encoding="utf-8-sig", errors="replace"))
        for m in block_re.finditer(text):
            tag = m.group(1)
            start = m.end()
            depth = 1
            i = start
            while i < len(text) and depth > 0:
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                i += 1
            body = text[start:i - 1]
            culture = re.search(r"\bculture_definition\s*=\s*([a-zA-Z0-9_]+)", body)
            religion = re.search(r"\breligion_definition\s*=\s*([a-zA-Z0-9_]+)", body)
            entry = out.setdefault(tag, {})
            if culture:
                entry["culture"] = culture.group(1)
            if religion:
                entry["religion"] = religion.group(1)
    return out


def parse_country_locations(start_path: Path) -> dict[str, list[str]]:
    """Parse 10_countries.txt -> {tag: [locations]} from own_control_core blocks.

    Falls back to own_core / own_control / own_integrated when own_control_core is
    absent so non-European tags with different ownership flags still register.
    """
    text = strip_comments(start_path.read_text(encoding="utf-8-sig", errors="replace"))
    countries_block = find_balanced_block(text, "countries")
    if countries_block is None:
        return {}
    inner = find_balanced_block(countries_block, "countries") or countries_block

    out: dict[str, list[str]] = {}
    block_re = re.compile(r"\b([A-Z][A-Z0-9]{2})\s*=\s*\{")
    for m in block_re.finditer(inner):
        tag = m.group(1)
        start = m.end()
        depth = 1
        i = start
        while i < len(inner) and depth > 0:
            if inner[i] == "{":
                depth += 1
            elif inner[i] == "}":
                depth -= 1
            i += 1
        body = inner[start:i - 1]

        locs: list[str] = []
        for key in ("own_control_core", "own_core", "own_control",
                    "own_integrated", "own_control_integrated"):
            sub = find_balanced_block(body, key)
            if not sub:
                continue
            locs.extend(re.findall(r"\b[a-z][a-zA-Z0-9_]*\b", sub))
        if locs:
            out[tag] = sorted(set(locs))
    return out


def parse_culture_groups(culture_dir: Path) -> dict[str, list[str]]:
    """Parse cultures/*.txt -> {culture: [groups]}."""
    out: dict[str, list[str]] = {}
    block_re = re.compile(r"\b([a-z][a-zA-Z0-9_]*)\s*=\s*\{")
    for path in sorted(culture_dir.glob("*.txt")):
        if path.name.startswith("00_"):
            continue
        text = strip_comments(path.read_text(encoding="utf-8-sig", errors="replace"))
        for m in block_re.finditer(text):
            culture = m.group(1)
            start = m.end()
            depth = 1
            i = start
            while i < len(text) and depth > 0:
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                i += 1
            body = text[start:i - 1]
            groups_block = find_balanced_block(body, "culture_groups")
            if not groups_block:
                continue
            groups = re.findall(r"\b[a-z][a-zA-Z0-9_]*_group\b", groups_block)
            if groups:
                out[culture] = groups
    return out


def parse_religion_groups(religion_dir: Path) -> dict[str, str]:
    """Parse religions/*.txt -> {religion: group}."""
    out: dict[str, str] = {}
    block_re = re.compile(r"\b([a-z][a-zA-Z0-9_]*)\s*=\s*\{")
    for path in sorted(religion_dir.glob("*.txt")):
        if path.name.startswith("00_"):
            continue
        text = strip_comments(path.read_text(encoding="utf-8-sig", errors="replace"))
        for m in block_re.finditer(text):
            religion = m.group(1)
            start = m.end()
            depth = 1
            i = start
            while i < len(text) and depth > 0:
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                i += 1
            body = text[start:i - 1]
            grp = re.search(r"\bgroup\s*=\s*([a-zA-Z0-9_]+)", body)
            if grp:
                out[religion] = grp.group(1)
    return out


# Predicates that pin a tag to a specific culture / religion.
# EU5 uses scoped values like `culture:czech` or `culture_group:scandinavian_group`.
# Block-form (`culture = { has_culture_group = ... }`) is matched separately.
CULTURE_KEYS = (
    "culture", "has_primary_culture", "primary_culture",
    "has_culture", "has_native_culture",
)
CULTURE_GROUP_KEYS = (
    "culture_group", "has_culture_group", "primary_culture_group",
)
RELIGION_KEYS = (
    "religion", "has_religion", "has_state_religion",
    "primary_religion",
)
RELIGION_GROUP_KEYS = (
    "religion_group", "has_religion_group",
)

SCOPED_VAL_RE = r"(?:[a-z_]+:)?([a-zA-Z0-9_]+)"


def _extract_keyed_values(raw: str, keys) -> set[str]:
    """Match `<key> = <scope?>:<value>` and `<key> = { has_X = <scope?>:<value> }`."""
    out: set[str] = set()
    for key in keys:
        # bare / scoped value form
        for m in re.finditer(rf"\b{re.escape(key)}\s*=\s*{SCOPED_VAL_RE}\b", raw):
            v = m.group(1)
            if v not in ("yes", "no"):
                out.add(v)
        # block form: gather all scoped values inside the next balanced { ... }
        for m in re.finditer(rf"\b{re.escape(key)}\s*=\s*\{{", raw):
            start = m.end()
            depth = 1
            i = start
            while i < len(raw) and depth > 0:
                if raw[i] == "{":
                    depth += 1
                elif raw[i] == "}":
                    depth -= 1
                i += 1
            block = raw[start:i - 1]
            for mm in re.finditer(r"\b[a-z_]+:([a-zA-Z0-9_]+)\b", block):
                out.add(mm.group(1))
            # also accept bare-token assignments inside the block (legacy)
            for mm in re.finditer(r"\b(?:culture|religion|culture_group|religion_group)\s*=\s*([a-zA-Z0-9_]+)\b", block):
                v = mm.group(1)
                if v not in ("yes", "no"):
                    out.add(v)
    return out


def extract_gates(raw: str | None) -> tuple[set[str], set[str], set[str], set[str]]:
    """Return (cultures, culture_groups, religions, religion_groups) gate sets."""
    if not raw:
        return set(), set(), set(), set()
    cultures = _extract_keyed_values(raw, CULTURE_KEYS)
    culture_grps = _extract_keyed_values(raw, CULTURE_GROUP_KEYS)
    religions = _extract_keyed_values(raw, RELIGION_KEYS)
    religion_grps = _extract_keyed_values(raw, RELIGION_GROUP_KEYS)
    return cultures, culture_grps, religions, religion_grps


def build_area_to_locations(geography: dict) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for loc_name, info in geography.get("locations", {}).items():
        area = info.get("area")
        if area:
            out.setdefault(area, []).append(loc_name)
    return out


def build_region_to_locations(geography: dict, area_to_locations: dict) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for region_name, info in geography.get("regions", {}).items():
        bag: list[str] = []
        for area in info.get("areas", []):
            bag.extend(area_to_locations.get(area, []))
        if bag:
            out[region_name] = bag
    return out


def formable_target_locations(rec: dict, area_to_locs: dict, region_to_locs: dict) -> set[str]:
    target: set[str] = set()
    for loc in rec.get("locations") or []:
        target.add(loc)
    for must in rec.get("must_own") or []:
        target.add(must)
    for area in rec.get("areas") or []:
        target.update(area_to_locs.get(area, []))
    for region in rec.get("regions") or []:
        target.update(region_to_locs.get(region, []))
    return target


def score_candidate(tag: str, country: dict, target_locs: set[str],
                    cultures: set[str], culture_grps: set[str],
                    religions: set[str], religion_grps: set[str],
                    culture_groups: dict, religion_groups: dict) -> tuple[int, dict] | None:
    culture = country.get("culture")
    religion = country.get("religion")
    own = country.get("locations") or []
    overlap = sum(1 for l in own if l in target_locs) if target_locs else 0

    has_culture_gate = bool(cultures or culture_grps)
    has_religion_gate = bool(religions or religion_grps)

    culture_match = False
    if has_culture_gate and culture:
        if culture in cultures:
            culture_match = True
        else:
            for grp in culture_groups.get(culture, []):
                if grp in culture_grps:
                    culture_match = True
                    break

    religion_match = False
    if has_religion_gate and religion:
        if religion in religions:
            religion_match = True
        else:
            grp = religion_groups.get(religion)
            if grp and grp in religion_grps:
                religion_match = True

    score = 0
    if has_culture_gate:
        if not culture_match:
            return None
        score += 4
    if has_religion_gate:
        if not religion_match:
            return None
        score += 3
    if target_locs:
        # Geography is a soft preference: tags fully outside the target region
        # are excluded, but having even one location in or adjacent to the
        # required geography is enough to qualify.
        if overlap == 0:
            return None
        score += 2 + min(overlap, 5)
    if not has_culture_gate and not has_religion_gate and not target_locs:
        return None

    return score, {
        "tag": tag,
        "culture": culture,
        "religion": religion,
        "owned_in_target": overlap,
    }


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_guide_file(path: Path):
    """Return (frontmatter_dict, html_body) for a guide markdown file."""
    import markdown
    text = path.read_text(encoding="utf-8")
    fm: dict = {}
    body = text
    m = FRONTMATTER_RE.match(text)
    if m:
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError as e:
            print(f"warn: bad frontmatter in {path.name}: {e}", file=sys.stderr)
            fm = {}
        body = text[m.end():]
    html = markdown.markdown(body, extensions=["extra", "smarty"]) if body.strip() else ""
    return fm, html


def load_guide_overrides(guides_dir: Path) -> dict[str, dict]:
    """Map block_key -> {notes_html, priority_starters, hide_auto, ...}."""
    out: dict[str, dict] = {}
    if not guides_dir.exists():
        return out
    for path in sorted(guides_dir.glob("*.md")):
        block_key = path.stem  # filename = block_key (e.g. YAV_f)
        fm, html = parse_guide_file(path)
        priority = []
        for entry in fm.get("priority_starters") or []:
            if not isinstance(entry, dict) or not entry.get("tag"):
                continue
            priority.append({
                "tag": entry["tag"],
                "note": entry.get("note") or entry.get("why") or "",
            })
        out[block_key] = {
            "notes_html": html.strip(),
            "priority_starters": priority,
            "hide_auto": bool(fm.get("hide_auto")),
        }
    return out


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent.parent
    with open(repo_root / "build.config.yaml") as f:
        cfg = yaml.safe_load(f)
    eu5 = expand_path(cfg["eu5_game_root"])
    web_data_dir = repo_root / cfg["build"]["web_data_dir"]
    guides_dir = repo_root / "data" / "guides"

    setup_dir = eu5 / "in_game/setup/countries"
    start_path = eu5 / "main_menu/setup/start/10_countries.txt"
    cultures_dir = eu5 / "in_game/common/cultures"
    religions_dir = eu5 / "in_game/common/religions"

    print(f"reading country setup ({setup_dir}) ...")
    countries = parse_country_setup(setup_dir)
    print(f"  {len(countries)} tags with culture/religion")

    print(f"reading start state ({start_path.name}) ...")
    locs_by_tag = parse_country_locations(start_path)
    print(f"  {len(locs_by_tag)} tags with owned locations")
    for tag, locs in locs_by_tag.items():
        countries.setdefault(tag, {})["locations"] = locs

    print("reading cultures ...")
    culture_groups = parse_culture_groups(cultures_dir)
    print(f"  {len(culture_groups)} cultures with group info")

    print("reading religions ...")
    religion_groups = parse_religion_groups(religions_dir)
    print(f"  {len(religion_groups)} religions with group info")

    print("reading geography + formables ...")
    with open(web_data_dir / "geography.json") as f:
        geography = json.load(f)
    with open(web_data_dir / "formables.json") as f:
        formables_doc = json.load(f)
    area_to_locs = build_area_to_locations(geography)
    region_to_locs = build_region_to_locations(geography, area_to_locs)

    print(f"reading hand-written guides ({guides_dir}) ...")
    overrides = load_guide_overrides(guides_dir)
    print(f"  {len(overrides)} guide overrides loaded")

    out: dict[str, dict] = {}
    skipped_no_gates = 0
    total_candidates = 0
    for rec in formables_doc["formables"]:
        block_key = rec["block_key"]
        override = overrides.get(block_key)
        cultures, culture_grps, religions, religion_grps = extract_gates(rec.get("potential_raw"))
        # Combine allow_raw too; some formables put location-or-religion gates there.
        if rec.get("allow_raw"):
            ac, agc, ar, agr = extract_gates(rec["allow_raw"])
            cultures |= ac; culture_grps |= agc; religions |= ar; religion_grps |= agr
        target_locs = formable_target_locations(rec, area_to_locs, region_to_locs)

        has_gates = bool(cultures or culture_grps or religions or religion_grps or target_locs)
        if not has_gates and not override:
            skipped_no_gates += 1
            continue

        scored: list[tuple[int, dict]] = []
        if has_gates:
            for tag, country in countries.items():
                res = score_candidate(
                    tag, country, target_locs,
                    cultures, culture_grps, religions, religion_grps,
                    culture_groups, religion_groups,
                )
                if res is None:
                    continue
                scored.append(res)

        # Don't recommend the formable's own tag.
        scored = [s for s in scored if s[1]["tag"] != rec.get("tag")]
        scored.sort(key=lambda s: (-s[0], s[1]["tag"]))

        if not scored and not override:
            continue

        # Strip auto-derived candidates already covered by priority_starters
        # so the lower list doesn't repeat the curated picks.
        priority = override["priority_starters"] if override else []
        priority_tags = {p["tag"] for p in priority}
        auto = [c[1] | {"score": c[0]} for c in scored[:8] if c[1]["tag"] not in priority_tags]
        if override and override.get("hide_auto"):
            auto = []

        out[block_key] = {
            "culture_gates": sorted(cultures),
            "culture_group_gates": sorted(culture_grps),
            "religion_gates": sorted(religions),
            "religion_group_gates": sorted(religion_grps),
            "candidates": auto,
        }
        if override:
            if override.get("notes_html"):
                out[block_key]["notes_html"] = override["notes_html"]
            if priority:
                # Enrich curated picks with the same culture/religion/territory
                # data we show for auto-derived entries, so the row layout matches.
                enriched = []
                for p in priority:
                    country = countries.get(p["tag"], {})
                    overlap = sum(
                        1 for l in country.get("locations", []) if l in target_locs
                    ) if target_locs else 0
                    enriched.append({
                        "tag": p["tag"],
                        "culture": country.get("culture"),
                        "religion": country.get("religion"),
                        "owned_in_target": overlap,
                        "note": p.get("note") or "",
                    })
                out[block_key]["priority_starters"] = enriched
        total_candidates += len(auto) + len(priority)

    out_path = web_data_dir / "starters.json"
    with open(out_path, "w") as f:
        json.dump({"version": 1, "guides": out}, f, indent=2)
    print(f"  {len(out)} formables with starters; {total_candidates} total candidates")
    print(f"  {skipped_no_gates} formables had no gates and were skipped")
    print(f"wrote {out_path} ({out_path.stat().st_size/1e3:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
