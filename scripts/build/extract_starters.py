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


def parse_country_start_state(start_path: Path) -> dict[str, dict]:
    """Parse 10_countries.txt -> {tag: {locations, rank, accepted, tolerated, reforms, gov_type}}.

    Falls back across own_* keys for territory.
    """
    text = strip_comments(start_path.read_text(encoding="utf-8-sig", errors="replace"))
    countries_block = find_balanced_block(text, "countries")
    if countries_block is None:
        return {}
    inner = find_balanced_block(countries_block, "countries") or countries_block

    out: dict[str, dict] = {}
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

        entry: dict = {}

        locs: list[str] = []
        for key in ("own_control_core", "own_core", "own_control",
                    "own_integrated", "own_control_integrated"):
            sub = find_balanced_block(body, key)
            if not sub:
                continue
            locs.extend(re.findall(r"\b[a-z][a-zA-Z0-9_]*\b", sub))
        if locs:
            entry["locations"] = sorted(set(locs))

        # country_rank = country_rank:rank_kingdom (or just rank_kingdom)
        rank_m = re.search(r"\bcountry_rank\s*=\s*(?:[a-z_]+:)?([a-zA-Z0-9_]+)", body)
        if rank_m:
            entry["rank"] = rank_m.group(1)

        # government { type = monarchy ... }
        gov_block = find_balanced_block(body, "government")
        if gov_block:
            gt = re.search(r"\btype\s*=\s*(?:[a-z_]+:)?([a-zA-Z0-9_]+)", gov_block)
            if gt:
                entry["gov_type"] = gt.group(1)

        # accepted_cultures = { foo bar }
        for key, out_key in (("accepted_cultures", "accepted"),
                              ("tolerated_cultures", "tolerated")):
            sub = find_balanced_block(body, key)
            if sub:
                entry[out_key] = re.findall(r"\b[a-z][a-zA-Z0-9_]*\b", sub)

        # reforms = { reform_a reform_b ... } — list of government_reform names
        reforms_block = find_balanced_block(body, "reforms")
        if reforms_block:
            entry["reforms"] = re.findall(r"\b[a-z][a-zA-Z0-9_]*\b", reforms_block)

        if entry:
            out[tag] = entry
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


TAG_KEYS = ("tag", "was_tag", "had_tag", "has_or_had_tag")
RANK_KEYS = ("country_rank",)
REFORM_KEYS = ("has_reform",)
GOV_TYPE_KEYS = ("government_type",)


def _extract_uppercase_values(raw: str, keys) -> set[str]:
    """Match `<key> = <scope?>:<TAG>` where TAG is 3-5 uppercase chars."""
    out: set[str] = set()
    for key in keys:
        for m in re.finditer(rf"\b{re.escape(key)}\s*=\s*(?:[a-z_]+:)?([A-Z][A-Z0-9]{{2,4}})\b", raw):
            out.add(m.group(1))
    return out


def _accepted_culture_block_values(raw: str) -> tuple[set[str], set[str]]:
    """Pull culture / culture_group requirements from any
    `any_primary_or_accepted_or_tolerated_culture = { ... }` blocks.

    These widen the culture match to also accept tolerated/accepted cultures,
    not just the primary one.
    """
    cultures: set[str] = set()
    culture_grps: set[str] = set()
    for m in re.finditer(r"\bany_primary_or_accepted_or_tolerated_culture\s*=\s*\{", raw):
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
        # culture:foo / culture_group:foo / has_culture_group = culture_group:foo
        for mm in re.finditer(r"\bculture_group:([a-zA-Z0-9_]+)", block):
            culture_grps.add(mm.group(1))
        for mm in re.finditer(r"(?<!_)\bculture:([a-zA-Z0-9_]+)", block):
            cultures.add(mm.group(1))
    return cultures, culture_grps


def _strip_blocks(raw: str, keys) -> str:
    """Remove `<key> = { ... }` blocks (balanced) for any of the given keys.

    Used to drop `trigger_if = { limit = ..., ... }` and `NOT = { ... }`
    blocks before extracting gates, so their contents don't leak into the
    top-level constraint set.
    """
    pat = re.compile(rf"\b(?:{'|'.join(re.escape(k) for k in keys)})\s*=\s*\{{")
    out = []
    cursor = 0
    while True:
        m = pat.search(raw, cursor)
        if not m:
            out.append(raw[cursor:])
            break
        out.append(raw[cursor:m.start()])
        start = m.end()
        depth = 1
        i = start
        while i < len(raw) and depth > 0:
            if raw[i] == "{":
                depth += 1
            elif raw[i] == "}":
                depth -= 1
            i += 1
        cursor = i
    # Recurse: stripping a block may reveal nested blocks of the same kind.
    new = "".join(out)
    return new if new == raw else _strip_blocks(new, keys)


def _extract_predicates(raw: str) -> dict:
    """Pull all matchable predicates from a flat (no OR-aware) script blob."""
    out = {
        "cultures": _extract_keyed_values(raw, CULTURE_KEYS),
        "culture_groups": _extract_keyed_values(raw, CULTURE_GROUP_KEYS),
        "religions": _extract_keyed_values(raw, RELIGION_KEYS),
        "religion_groups": _extract_keyed_values(raw, RELIGION_GROUP_KEYS),
        "tags": _extract_uppercase_values(raw, TAG_KEYS),
        "ranks": _extract_keyed_values(raw, RANK_KEYS),
        "reforms": _extract_keyed_values(raw, REFORM_KEYS),
        "gov_types": _extract_keyed_values(raw, GOV_TYPE_KEYS),
    }
    accept_cul, accept_grp = _accepted_culture_block_values(raw)
    out["accept_cultures"] = accept_cul
    out["accept_culture_groups"] = accept_grp
    return out


def _extract_balanced_blocks(raw: str, key: str) -> list[tuple[str, int, int]]:
    """Yield (body, start_pos, end_pos) for every balanced `key = { ... }`."""
    out = []
    pat = re.compile(rf"\b{re.escape(key)}\s*=\s*\{{")
    for m in pat.finditer(raw):
        start = m.end()
        depth = 1
        i = start
        while i < len(raw) and depth > 0:
            if raw[i] == "{":
                depth += 1
            elif raw[i] == "}":
                depth -= 1
            i += 1
        out.append((raw[start:i - 1], m.start(), i))
    return out


def _extract_not_excludes(raw: str) -> set[str]:
    """Pull tag values from `NOT = { tag = X }` blocks for use as exclusions.

    Only handles the common shape `NOT = { tag = X }`; complex NOT bodies
    are skipped (we'd over-exclude if we tried to invert them).
    """
    out: set[str] = set()
    for body, _, _ in _extract_balanced_blocks(raw, "NOT"):
        # Only accept simple bodies: at most a couple of `tag = X` lines.
        tokens = re.findall(r"\b\w+\s*=\s*\S+", body)
        if not tokens:
            continue
        # Bail out if the body contains anything other than tag/has_or_had_tag.
        non_tag = [t for t in tokens if not re.match(r"\b(?:tag|has_or_had_tag|was_tag|had_tag)\b", t)]
        if non_tag:
            continue
        out |= _extract_uppercase_values(body, TAG_KEYS)
    return out


def extract_gates(raw: str | None) -> dict:
    """Parse OR-block-aware gates from a potential / allow blob.

    Returns:
      {
        "and_groups": [predicate_dict, ...],   # each must be fully satisfied
        "or_groups":  [predicate_dict, ...],   # each must satisfy at least one predicate
        "tag_excludes": set,                   # tags excluded by NOT { tag = X }
      }
    The AND group is the top-level (non-OR, non-trigger_if) predicates rolled
    up into one dict; each OR block contributes its own predicate dict.
    `trigger_if` bodies are added as additional OR groups (lossy but more
    correct than dropping them entirely; their conditional limit is ignored).
    """
    if not raw:
        return {"and_groups": [], "or_groups": [], "tag_excludes": set()}

    # Normalise EU5's dotted-scope syntax (`religion.group = religion_group:X`,
    # `culture.group = culture_group:X`) into the equivalent flat form.
    raw = re.sub(r"\breligion\.group\s*=", "religion_group =", raw)
    raw = re.sub(r"\bculture\.group\s*=", "culture_group =", raw)

    # NOT-block tag exclusions before we strip NOT blocks for the rest.
    tag_excludes = _extract_not_excludes(raw)

    # trigger_if blocks are conditional: they only apply when their `limit`
    # holds, and the conditions involve future game state (vassal
    # relationships, country existence). We can't reliably evaluate them at
    # game start, so we strip the blocks rather than over-filter. But we DO
    # collect any `tag = X` predicates from inside as "suggested starters"
    # for a score boost, since formables routinely list their canonical tags
    # this way (e.g. GBR's ENG/SCO/WLS/SBL trigger_if blocks).
    suggested_tags: set[str] = set()
    cleaned = raw
    for trigger_kind in ("trigger_if", "trigger_else_if"):
        for body, _, _ in _extract_balanced_blocks(cleaned, trigger_kind):
            body_no_limit = _strip_blocks(body, ("limit",))
            suggested_tags |= _extract_uppercase_values(body_no_limit, TAG_KEYS)

    # Now strip trigger_if/trigger_else_if/trigger_else and NOT blocks before
    # the main parse so they don't leak as AND-required predicates.
    cleaned = _strip_blocks(cleaned, ("trigger_if", "trigger_else_if", "trigger_else", "NOT"))

    # Identify top-level OR blocks, extract their inner content, and
    # remove them from the cleaned blob so what's left is the AND part.
    or_groups: list[dict] = []
    or_re = re.compile(r"\bOR\s*=\s*\{")
    pieces: list[str] = []
    cursor = 0
    for m in or_re.finditer(cleaned):
        if m.start() < cursor:
            continue
        pieces.append(cleaned[cursor:m.start()])
        start = m.end()
        depth = 1
        i = start
        while i < len(cleaned) and depth > 0:
            if cleaned[i] == "{":
                depth += 1
            elif cleaned[i] == "}":
                depth -= 1
            i += 1
        block = cleaned[start:i - 1]
        or_groups.append(_extract_predicates(block))
        cursor = i
    pieces.append(cleaned[cursor:])
    and_blob = "".join(pieces)

    return {
        "and_groups": [_extract_predicates(and_blob)],
        "or_groups": or_groups,
        "tag_excludes": tag_excludes,
        "suggested_tags": suggested_tags,
    }


def merge_gates(a: dict, b: dict) -> dict:
    """Union two gate descriptors (e.g. potential + allow)."""
    if not a:
        return dict(b) if b else {"and_groups": [], "or_groups": [], "tag_excludes": set()}
    if not b:
        return a
    return {
        "and_groups": (a.get("and_groups") or []) + (b.get("and_groups") or []),
        "or_groups": (a.get("or_groups") or []) + (b.get("or_groups") or []),
        "tag_excludes": (a.get("tag_excludes") or set()) | (b.get("tag_excludes") or set()),
        "suggested_tags": (a.get("suggested_tags") or set()) | (b.get("suggested_tags") or set()),
    }


def _predicate_matches(pred: dict, country: dict, tag: str,
                       culture_groups: dict, religion_groups: dict) -> tuple[bool, int, list[str]]:
    """Check if a candidate satisfies any of the predicates in `pred`.

    Returns (satisfied, score_bonus, axes_matched). For an AND group,
    every populated predicate axis must match. For an OR group, ONE
    populated predicate axis matching is enough -- callers decide.
    """
    culture = country.get("culture")
    religion = country.get("religion")
    rank = country.get("rank")
    gov_type = country.get("gov_type")
    reforms = country.get("reforms") or []

    matched = []
    score = 0

    if pred.get("tags"):
        if tag in pred["tags"]:
            matched.append("tag"); score += 8
        else:
            matched.append(None)  # populated but not matched
    if pred.get("ranks"):
        if rank and rank in pred["ranks"]:
            matched.append("rank"); score += 2
        else:
            matched.append(None)
    if pred.get("reforms"):
        if any(r in reforms for r in pred["reforms"]):
            matched.append("reform"); score += 2
        else:
            matched.append(None)
    if pred.get("gov_types"):
        if gov_type and gov_type in pred["gov_types"]:
            matched.append("gov_type"); score += 2
        else:
            matched.append(None)
    if pred.get("cultures") or pred.get("culture_groups"):
        if culture and _culture_matches([culture], pred.get("cultures") or set(),
                                         pred.get("culture_groups") or set(), culture_groups):
            matched.append("culture"); score += 4
        else:
            matched.append(None)
    if pred.get("accept_cultures") or pred.get("accept_culture_groups"):
        all_cul = [c for c in [culture] if c]
        all_cul += country.get("accepted") or []
        all_cul += country.get("tolerated") or []
        if _culture_matches(all_cul, pred.get("accept_cultures") or set(),
                             pred.get("accept_culture_groups") or set(), culture_groups):
            matched.append("accept_culture"); score += 3
        else:
            matched.append(None)
    if pred.get("religions") or pred.get("religion_groups"):
        rel_match = religion in (pred.get("religions") or set())
        if not rel_match and religion:
            grp = religion_groups.get(religion)
            if grp and grp in (pred.get("religion_groups") or set()):
                rel_match = True
        if rel_match:
            matched.append("religion"); score += 3
        else:
            matched.append(None)

    return matched, score


def _and_group_satisfied(pred: dict, country: dict, tag: str,
                         culture_groups: dict, religion_groups: dict) -> tuple[bool, int]:
    """Every populated axis must match."""
    matched, score = _predicate_matches(pred, country, tag, culture_groups, religion_groups)
    if not matched:
        return True, 0  # empty group, vacuously satisfied
    if any(m is None for m in matched):
        return False, 0
    return True, score


def _or_group_satisfied(pred: dict, country: dict, tag: str,
                        culture_groups: dict, religion_groups: dict) -> tuple[bool, int]:
    """At least one populated axis must match."""
    matched, score = _predicate_matches(pred, country, tag, culture_groups, religion_groups)
    if not matched:
        return True, 0
    if any(m is not None for m in matched):
        return True, score
    return False, 0


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


def formable_target_locations(rec: dict, geography: dict,
                              area_to_locs: dict, region_to_locs: dict) -> tuple[set[str], set[str]]:
    """Return (core_locs, region_locs).

    `core_locs` are the formable's must_own + explicit `locations` blocks
    (named individually). `region_locs` are everything reachable through
    areas / regions / provinces / sub_continents / continents -- the broader
    territory pool. Tags overlapping core_locs are weighted heavier.
    """
    core: set[str] = set()
    region: set[str] = set()

    for loc in rec.get("locations") or []:
        core.add(loc)
    for must in rec.get("must_own") or []:
        core.add(must)

    for area in rec.get("areas") or []:
        region.update(area_to_locs.get(area, []))
    for reg in rec.get("regions") or []:
        region.update(region_to_locs.get(reg, []))
    provinces = geography.get("provinces") or {}
    for prov in rec.get("provinces") or []:
        region.update(provinces.get(prov, {}).get("locations", []))
    subregions = geography.get("subregions") or {}
    continents = geography.get("continents") or {}
    for sub in rec.get("sub_continents") or []:
        for reg in subregions.get(sub, {}).get("regions", []):
            region.update(region_to_locs.get(reg, []))
    for cont in rec.get("continents") or []:
        for sub in continents.get(cont, {}).get("subregions", []):
            for reg in subregions.get(sub, {}).get("regions", []):
                region.update(region_to_locs.get(reg, []))

    # Don't double-count: locations already in core shouldn't bleed into region pool.
    region -= core
    return core, region


def _culture_matches(tag_cultures: list[str], cultures: set[str], culture_grps: set[str],
                     culture_groups: dict) -> bool:
    """Return True if any of the candidate's cultures (primary, accepted, or tolerated)
    satisfies the gate sets."""
    for c in tag_cultures:
        if c in cultures:
            return True
        for grp in culture_groups.get(c, []):
            if grp in culture_grps:
                return True
    return False


def score_candidate(tag: str, country: dict, core_locs: set[str], region_locs: set[str],
                    gates: dict, culture_groups: dict, religion_groups: dict,
                    is_explicit: bool = False) -> tuple[int, dict] | None:
    """Score a candidate against the gate set.

    is_explicit: this tag is named in one of the formable's tag predicates,
    which short-circuits the geography filter (the player is expected to
    take the required territory by war, not own it at start).

    Geography is split: `core_locs` are must_own + explicit `locations`
    (named one-by-one in the formable) and weighted heavier than `region_locs`
    (the broader pool from areas/regions/etc).
    """
    culture = country.get("culture")
    religion = country.get("religion")
    own = country.get("locations") or []
    own_set = set(own)
    core_overlap = sum(1 for l in own_set if l in core_locs) if core_locs else 0
    region_overlap = sum(1 for l in own_set if l in region_locs) if region_locs else 0

    score = 0
    saw_any = False

    # AND groups: every populated axis must match.
    for grp in gates.get("and_groups") or []:
        ok, s = _and_group_satisfied(grp, country, tag, culture_groups, religion_groups)
        if not ok:
            return None
        if s > 0:
            saw_any = True
            score += s

    # OR groups: at least one populated axis must match.
    for grp in gates.get("or_groups") or []:
        ok, s = _or_group_satisfied(grp, country, tag, culture_groups, religion_groups)
        if not ok:
            return None
        saw_any = True
        score += s

    has_geography = bool(core_locs or region_locs)
    if has_geography:
        any_overlap = core_overlap > 0 or region_overlap > 0
        if not any_overlap and not is_explicit:
            return None
        if any_overlap:
            saw_any = True
            # Core locations (must_own + named) weight 4x a region pool match.
            score += 4 * min(core_overlap, 5) + min(region_overlap, 5)

    if not saw_any:
        return None

    return score, {
        "tag": tag,
        "culture": culture,
        "religion": religion,
        "owned_in_target": core_overlap + region_overlap,
        "owned_in_core": core_overlap,
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
    start_state = parse_country_start_state(start_path)
    print(f"  {len(start_state)} tags with start-state data")
    for tag, fields in start_state.items():
        countries.setdefault(tag, {}).update(fields)

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

    # Validate priority_starter tags. Three error classes:
    #   * tag doesn't exist anywhere -> typo
    #   * tag is only a formable (no starting country) -> chain-only path,
    #     warn so the guide author confirms it's intentional
    #   * block_key isn't a real formable
    bad_refs: list[str] = []
    formable_keys = {rec["block_key"] for rec in formables_doc["formables"]}
    formable_tags = {rec.get("tag") for rec in formables_doc["formables"] if rec.get("tag")}
    for block_key, guide in overrides.items():
        if block_key not in formable_keys:
            bad_refs.append(f"  {block_key}.md: not a known formable block_key")
        for p in guide.get("priority_starters") or []:
            tag = p.get("tag")
            if not tag:
                continue
            if tag in countries:
                continue
            if tag in formable_tags:
                bad_refs.append(
                    f"  {block_key}.md: priority_starter '{tag}' has no starting country "
                    f"(it is only a formable). Likely meant a starting tag in that culture/region."
                )
                continue
            bad_refs.append(
                f"  {block_key}.md: priority_starter '{tag}' not found anywhere"
            )
    if bad_refs:
        print("warn: guide validation issues:")
        for line in bad_refs:
            print(line)

    # rank name -> level (rank_county = 1, rank_duchy = 2, rank_kingdom = 3, rank_empire = 4).
    # Tags with no rank field default to 0 (effectively unranked / tribal).
    RANK_LEVEL = {"rank_county": 1, "rank_duchy": 2, "rank_kingdom": 3, "rank_empire": 4}

    out: dict[str, dict] = {}
    skipped_no_gates = 0
    total_candidates = 0
    for rec in formables_doc["formables"]:
        block_key = rec["block_key"]
        override = overrides.get(block_key)
        gates = merge_gates(extract_gates(rec.get("potential_raw")),
                            extract_gates(rec.get("allow_raw")))
        core_locs, region_locs = formable_target_locations(rec, geography, area_to_locs, region_to_locs)
        tag_excludes = gates.get("tag_excludes") or set()

        # Per game rule: a tag's rank-level must be at or below the formable's
        # level to be eligible to form it (a kingdom cannot form a duchy-tier
        # formable, but a duchy can). Unknown/unranked tags treated as level 0.
        formable_level = rec.get("level")
        max_starter_level = formable_level if isinstance(formable_level, int) else None

        any_predicates = any(
            any(g.values()) for g in (gates.get("and_groups") or []) + (gates.get("or_groups") or [])
        )
        has_gates = bool(any_predicates or core_locs or region_locs)
        if not has_gates and not override:
            skipped_no_gates += 1
            continue

        # Tags explicitly named in any potential/allow tag_gate bypass the
        # level-rank ceiling: if the formable specifically lists you, the
        # game lets you form it regardless of your starting rank.
        explicit_tags: set[str] = set()
        for grp in (gates.get("and_groups") or []) + (gates.get("or_groups") or []):
            explicit_tags |= grp.get("tags") or set()

        suggested_tags = gates.get("suggested_tags") or set()

        scored: list[tuple[int, dict]] = []
        if has_gates:
            for tag, country in countries.items():
                if tag in tag_excludes:
                    continue
                # explicit OR suggested both bypass level-rank (suggested tags
                # come from trigger_if bodies and are the formable's canonical
                # candidates per the script).
                bypass_level = tag in explicit_tags or tag in suggested_tags
                if max_starter_level is not None and not bypass_level:
                    rank = country.get("rank")
                    rank_level = RANK_LEVEL.get(rank, 0)
                    if rank_level > max_starter_level:
                        continue
                res = score_candidate(
                    tag, country, core_locs, region_locs, gates,
                    culture_groups, religion_groups,
                    is_explicit=bypass_level,
                )
                if res is None:
                    continue
                # Suggested-tag boost: tags surfaced via trigger_if get
                # bumped up so they sort above the broader culture/religion pool.
                if tag in suggested_tags:
                    score, info = res
                    res = (score + 6, info)
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

        # Roll predicates from all groups together for the surfaced gate display.
        all_groups = (gates.get("and_groups") or []) + (gates.get("or_groups") or [])
        def _u(key):
            s = set()
            for g in all_groups:
                s |= g.get(key) or set()
            return sorted(s)

        out[block_key] = {
            "culture_gates": _u("cultures"),
            "culture_group_gates": sorted(set(_u("culture_groups")) | set(_u("accept_culture_groups"))),
            "religion_gates": _u("religions"),
            "religion_group_gates": _u("religion_groups"),
            "tag_gates": _u("tags"),
            "rank_gates": _u("ranks"),
            "reform_gates": _u("reforms"),
            "tag_excludes": sorted(tag_excludes),
            "suggested_tags": sorted(gates.get("suggested_tags") or []),
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
                    own = set(country.get("locations") or [])
                    core_o = sum(1 for l in own if l in core_locs)
                    region_o = sum(1 for l in own if l in region_locs)
                    enriched.append({
                        "tag": p["tag"],
                        "culture": country.get("culture"),
                        "religion": country.get("religion"),
                        "owned_in_target": core_o + region_o,
                        "owned_in_core": core_o,
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
