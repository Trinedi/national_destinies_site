#!/usr/bin/env python3
"""Translate formable potential/allow blocks into human-readable bullets.

Reads formables.json, parses each formable's `potential_raw` and `allow_raw`
Paradox-script blocks, walks the resulting AST, and emits a structured
list of plain-English requirement clauses.

Output: rewrites formables.json in place with new fields:
  english_potential : [{level, kind, text, children?}, ...]
  english_allow     : same shape
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import yaml


def load_config(repo_root: Path) -> dict:
    with open(repo_root / "build.config.yaml") as f:
        return yaml.safe_load(f)


def expand_path(p: str) -> Path:
    return Path(os.path.expanduser(p)).resolve()


# ----- tokenizer ---------------------------------------------------------

TOKEN_RE = re.compile(
    r"""
    \#[^\n]*                  |   # comment
    (?P<op>(?:<=|>=|<>|!=|\?=|=|<|>))  |
    (?P<brace>[{}])           |
    "(?P<str>(?:[^"\\]|\\.)*)" |
    (?P<num>-?\d+(?:\.\d+)?)  |
    (?P<ref>[A-Za-z_][A-Za-z0-9_]*(?::[A-Za-z_][A-Za-z0-9_]*)+) |
    (?P<id>[A-Za-z_][A-Za-z0-9_]*)
    """,
    re.VERBOSE,
)


def tokenize(text: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for m in TOKEN_RE.finditer(text):
        if m.group(0).startswith("#"):
            continue
        if m.group("op"):
            out.append(("op", m.group("op")))
        elif m.group("brace"):
            out.append(("brace", m.group("brace")))
        elif m.group("str") is not None:
            out.append(("str", m.group("str")))
        elif m.group("num"):
            out.append(("num", m.group("num")))
        elif m.group("ref"):
            out.append(("ref", m.group("ref")))
        elif m.group("id"):
            out.append(("id", m.group("id")))
    return out


# ----- parser ------------------------------------------------------------
# Returns AST as nested clauses:
#   ('atom', key, op, value)
#   ('block', key, op, [clauses])

def parse_block(toks: list[tuple[str, str]], i: int) -> tuple[list, int]:
    stmts: list = []
    while i < len(toks):
        kind, val = toks[i]
        if kind == "brace" and val == "}":
            return stmts, i + 1
        # Skip stray tokens we cannot interpret.
        if kind not in ("id",) and val != "{":
            i += 1
            continue
        if kind == "id":
            key = val
            j = i + 1
            if j >= len(toks):
                stmts.append(("bare", key, None, None))
                break
            if toks[j][0] != "op":
                # bare identifier (rare); skip
                i = j
                continue
            op = toks[j][1]
            j += 1
            if j >= len(toks):
                break
            ntype, nval = toks[j]
            if ntype == "brace" and nval == "{":
                child, after = parse_block(toks, j + 1)
                stmts.append(("block", key, op, child))
                i = after
            else:
                stmts.append(("atom", key, op, nval))
                i = j + 1
        else:
            i += 1
    return stmts, i


def parse(text: str | None) -> list:
    if not text:
        return []
    toks = tokenize(text)
    stmts, _ = parse_block(toks, 0)
    return stmts


# ----- helpers -----------------------------------------------------------

def strip_ref(value: str) -> str:
    """`culture:swedish` -> `swedish`. Plain ids returned unchanged."""
    if ":" in value:
        return value.split(":", 1)[1]
    return value


def loc_lookup(loc: dict[str, str], *keys: str) -> str | None:
    for k in keys:
        if not k:
            continue
        v = loc.get(k)
        if v:
            return v
    return None


def prettify(name: str) -> str:
    return (
        name.replace("_", " ")
        .replace("  ", " ")
        .strip()
        .title()
    )


def loc_or_pretty(loc: dict[str, str], name: str, *extra_keys: str) -> str:
    return loc_lookup(loc, name, *extra_keys) or prettify(name)


# ----- atom renderers (per key) -----------------------------------------

def r_culture_atom(op: str, value: str, loc) -> str:
    base = strip_ref(value)
    name = loc_or_pretty(loc, base)
    return f"{name} culture"


def r_religion_atom(op: str, value: str, loc) -> str:
    base = strip_ref(value)
    name = loc_or_pretty(loc, base)
    return f"{name} religion"


def r_language_atom(op: str, value: str, loc) -> str:
    base = strip_ref(value)
    return f"{loc_or_pretty(loc, base)} language"


def r_group_atom(op: str, value: str, loc) -> str:
    # Inside `culture = { group = X }` style; bare context handled by caller.
    base = strip_ref(value)
    return f"{loc_or_pretty(loc, base)} group"


def r_owns_atom(op: str, value: str, loc) -> str:
    base = strip_ref(value)
    return f"Owns {loc_or_pretty(loc, base)}"


def r_country_exists(op: str, value: str, loc) -> str:
    tag = strip_ref(value)
    name = loc_or_pretty(loc, tag, tag + "_f")
    return f"{name} exists"


def r_has_variable(op: str, value: str, loc) -> str:
    return f"Has variable: {prettify(value)}"


def r_is_frankokratia_state(op: str, value: str, loc) -> str:
    return "Frankokratia state" if value == "yes" else "Not a Frankokratia state"


def r_yes_no_flag(label: str):
    def f(op: str, value: str, loc) -> str:
        if value == "yes":
            return label
        if value == "no":
            return f"Not: {label}"
        return f"{label} = {value}"
    return f


def r_current_age_or_later(op: str, value: str, loc) -> str:
    name = loc_or_pretty(loc, value)
    return f"{name} or later"


def r_current_age(op: str, value: str, loc) -> str:
    cmp_text = {
        "=": "is", "<": "before", ">": "after",
        "<=": "by", ">=": "at or after",
    }.get(op, op)
    name = loc_or_pretty(loc, value)
    return f"Age {cmp_text} {name}"


def r_country_rank_atom(op: str, value: str, loc) -> str:
    name = loc_or_pretty(loc, strip_ref(value))
    cmp_text = {
        "=": "rank", ">=": "at least", ">": "above",
        "<=": "at most", "<": "below",
    }.get(op, op)
    return f"{cmp_text.capitalize()} {name}"


def r_has_or_had_tag(op: str, value: str, loc) -> str:
    name = loc_or_pretty(loc, value, value + "_f")
    return f"Was or is {name}"


def r_has_advance(op: str, value: str, loc) -> str:
    return f"Has advance {loc_or_pretty(loc, value)}"


ATOM_HANDLERS = {
    "culture": r_culture_atom,
    "religion": r_religion_atom,
    "language": r_language_atom,
    "group": r_group_atom,
    "owns": r_owns_atom,
    "country_exists": r_country_exists,
    "has_variable": r_has_variable,
    "is_frankokratia_state": r_is_frankokratia_state,
    "current_age_or_later": r_current_age_or_later,
    "current_age": r_current_age,
    "country_rank": r_country_rank_atom,
    "has_or_had_tag": r_has_or_had_tag,
    "has_advance": r_has_advance,
    "always": r_yes_no_flag("Always"),
    "exists": r_yes_no_flag("Country exists"),
    "is_hegemon": r_yes_no_flag("Hegemon"),
    "in_civil_war": r_yes_no_flag("In civil war"),
    "at_war": r_yes_no_flag("At war"),
    "hundred_years_war": r_yes_no_flag("Hundred Years' War"),
    "hre": r_yes_no_flag("In the HRE"),
    "ilkhanate": r_yes_no_flag("Ilkhanate"),
}


# ----- block renderers ---------------------------------------------------

def render_clauses(stmts, loc) -> list[dict]:
    out: list[dict] = []
    for s in stmts:
        clause = render_clause(s, loc)
        if clause is not None:
            out.append(clause)
    return out


def render_clause(s, loc) -> dict | None:
    kind = s[0]
    if kind == "atom":
        _, key, op, val = s
        return render_atom(key, op, val, loc)
    if kind == "block":
        _, key, op, body = s
        return render_block(key, op, body, loc)
    return None


def render_atom(key: str, op: str, value: str, loc) -> dict:
    h = ATOM_HANDLERS.get(key)
    if h:
        return {"kind": "atom", "text": h(op, value, loc)}
    # Fallback: show the raw shape so users can still skim it.
    pretty_value = strip_ref(value)
    pretty_value = loc.get(pretty_value, prettify(pretty_value))
    return {"kind": "atom", "text": f"{prettify(key)}: {pretty_value}"}


def render_block(key: str, op: str, body: list, loc) -> dict | None:
    if key == "OR":
        return {"kind": "or", "text": "Any of:", "children": render_clauses(body, loc)}
    if key == "NOT":
        return {"kind": "not", "text": "Must not:", "children": render_clauses(body, loc)}
    if key == "AND":
        return {"kind": "and", "text": "All of:", "children": render_clauses(body, loc)}
    if key == "trigger_if":
        # Paradox conditional. Body has `limit = { ... }` then effects;
        # for our purposes treat as conditional clause group.
        return {"kind": "if", "text": "If:", "children": render_clauses(body, loc)}
    if key in ("trigger_else_if", "trigger_else"):
        return {"kind": "else_if", "text": prettify(key) + ":", "children": render_clauses(body, loc)}
    if key == "custom_tooltip":
        # Body is opaque scripted text; the loc'd tooltip carries the meaning.
        # Look for `text = X` or `tooltip = X` and emit that loc string.
        for c in body:
            if c[0] == "atom" and c[1] in ("text", "tooltip"):
                return {"kind": "atom", "text": loc_or_pretty(loc, c[3])}
        return None

    # culture = { has_culture_group = X } / culture = { ... }
    if key == "culture":
        return render_culture_block(body, loc)
    if key == "religion":
        return render_religion_block(body, loc)
    if key == "language":
        return render_language_block(body, loc)
    if key == "any_primary_or_accepted_or_tolerated_culture":
        return {
            "kind": "any_culture",
            "text": "Any primary, accepted, or tolerated culture matches:",
            "children": render_clauses(body, loc),
        }
    if key == "any_owned_location":
        return {
            "kind": "any_owned",
            "text": "Has any owned location matching:",
            "children": render_clauses(body, loc),
        }

    # Generic block fallback: render children verbatim.
    children = render_clauses(body, loc)
    if not children:
        return None
    return {"kind": "block", "text": prettify(key) + ":", "children": children}


def render_culture_block(body: list, loc) -> dict | None:
    # Common shapes:
    #   culture = { has_culture_group = culture_group:X }
    #   culture = { OR = { has_culture_group = X has_culture_group = Y } }
    #   culture = { has_culture = culture:Y }
    found = []
    for c in body:
        if c[0] == "atom":
            _, key, op, val = c
            if key == "has_culture_group":
                found.append(f"{loc_or_pretty(loc, strip_ref(val))} culture group")
            elif key == "has_culture":
                found.append(f"{loc_or_pretty(loc, strip_ref(val))} culture")
            elif key == "group":
                found.append(f"{loc_or_pretty(loc, strip_ref(val))} group")
        elif c[0] == "block":
            _, key, op, sub = c
            if key == "OR":
                ch = render_culture_options(sub, loc, "culture")
                if ch:
                    return {"kind": "or", "text": "Any culture of:", "children": ch}
    if not found:
        return None
    if len(found) == 1:
        return {"kind": "atom", "text": found[0]}
    return {"kind": "and", "text": "Culture must match:", "children": [{"kind": "atom", "text": t} for t in found]}


def render_religion_block(body: list, loc) -> dict | None:
    found = []
    for c in body:
        if c[0] == "atom":
            _, key, op, val = c
            if key == "has_religion_group":
                found.append(f"{loc_or_pretty(loc, strip_ref(val))} religion group")
            elif key == "religion":
                found.append(f"{loc_or_pretty(loc, strip_ref(val))} religion")
        elif c[0] == "block":
            _, key, op, sub = c
            if key == "OR":
                ch = render_culture_options(sub, loc, "religion")
                if ch:
                    return {"kind": "or", "text": "Any religion of:", "children": ch}
    if not found:
        return None
    if len(found) == 1:
        return {"kind": "atom", "text": found[0]}
    return {"kind": "and", "text": "Religion must match:", "children": [{"kind": "atom", "text": t} for t in found]}


def render_language_block(body: list, loc) -> dict | None:
    found = []
    for c in body:
        if c[0] == "atom":
            _, key, op, val = c
            found.append(f"{loc_or_pretty(loc, strip_ref(val))} {prettify(key)}")
    if not found:
        return None
    if len(found) == 1:
        return {"kind": "atom", "text": found[0]}
    return {"kind": "and", "text": "Language must match:", "children": [{"kind": "atom", "text": t} for t in found]}


def render_culture_options(body, loc, label_kind):
    out = []
    for c in body:
        if c[0] == "atom":
            _, key, op, val = c
            if key in ("has_culture_group", "religion_group"):
                out.append({"kind": "atom", "text": f"{loc_or_pretty(loc, strip_ref(val))} group"})
            elif key in ("has_culture", "religion"):
                out.append({"kind": "atom", "text": f"{loc_or_pretty(loc, strip_ref(val))} {label_kind}"})
            else:
                cl = render_atom(key, op, val, loc)
                if cl:
                    out.append(cl)
    return out


# ----- main --------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inplace", action="store_true",
                    help="Rewrite formables.json (default if no --out)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    cfg = load_config(repo_root)
    web = repo_root / cfg["build"]["web_data_dir"]
    fm_path = web / "formables.json"
    loc_path = web / "loc.json"
    for p in [fm_path, loc_path]:
        if not p.exists():
            print(f"error: {p} not found", file=sys.stderr)
            return 1

    fm = json.loads(fm_path.read_text())
    loc = json.loads(loc_path.read_text())["strings"]

    rendered = 0
    for r in fm["formables"]:
        pot = parse(r.get("potential_raw"))
        allow = parse(r.get("allow_raw"))
        r["english_potential"] = render_clauses(pot, loc)
        r["english_allow"] = render_clauses(allow, loc)
        if r["english_potential"] or r["english_allow"]:
            rendered += 1

    out_path = Path(args.out) if args.out else fm_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(fm, f, indent=2)
    print(f"rendered requirements for {rendered}/{len(fm['formables'])} formables")
    print(f"wrote {out_path} ({out_path.stat().st_size/1e6:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
