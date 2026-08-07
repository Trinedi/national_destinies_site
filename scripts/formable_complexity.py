#!/usr/bin/env python3
"""Measure how complicated each formable is to FORM, straight from the game files.

A guide's length should follow how much a player has to do, not how much
history exists about the country. This reads the formable definition (mod
first, then vanilla) and counts the things a checklist has to state:

  locations   named `owns = location:x` clauses, one checklist line each
  conditions  other requirements in `potential` / `allow` worth a line
  territory   how many area/region/province pools the fraction spans

Used by check_guides.py to set a per-guide budget. Run directly to dump the
table.
"""
from __future__ import annotations

import glob
import os
import re
import sys

MOD = os.path.expanduser("~/Projects/national_destinies/in_game/common/formable_countries")
VANILLA = os.path.expanduser(
    "~/.local/share/Steam/steamapps/common/Europa Universalis V/game"
    "/in_game/common/formable_countries"
)

# Keys that are bookkeeping rather than something a player must satisfy.
IGNORED = {
    "name", "flag", "adjective", "tag", "color", "level", "rule",
    "required_locations_fraction", "capital_required", "areas", "regions",
    "provinces", "locations", "form_effect", "potential", "allow",
}


def _block(text: str, start: int) -> str:
    """Return the brace-balanced block beginning at the '{' at or after start."""
    i = text.index("{", start)
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i + 1:j]
    return ""


def _strip_comments(text: str) -> str:
    return "\n".join(l.split("#")[0] for l in text.split("\n"))


def find_definition(key: str) -> str | None:
    pat = re.compile(rf"(?:INJECT:|REPLACE:)?{re.escape(key)}\s*=\s*\{{")
    for path in sorted(glob.glob(os.path.join(MOD, "*.txt"))) + \
            sorted(glob.glob(os.path.join(VANILLA, "*.txt"))):
        try:
            text = _strip_comments(open(path, encoding="utf-8-sig").read())
        except OSError:
            continue
        m = pat.search(text)
        if m:
            body = _block(text, m.start())
            # An INJECT carries only form_effect; fall through to the base def.
            if "potential" in body or "allow" in body or "areas" in body:
                return body
    return None


def _count_conditions(block: str) -> tuple[int, int]:
    """(named locations, other conditions) in a potential/allow block.

    Depth matters. A top-level `owns = location:x` is its own checklist line,
    but a nested one is a branch of an alternative (PNT and MRO both ask for
    "any two of four", which raw counting read as fourteen requirements). So
    a whole OR/AND group scores as ONE line, however many options it holds.
    """
    locs = other = 0
    depth = 0
    for line in block.split("\n"):
        s = line.strip()
        if not s:
            continue
        if depth == 0:
            if re.match(r"owns\s*=\s*location:", s):
                locs += 1
            elif re.match(r"[A-Za-z_.]+\s*[=<>?]", s):
                # A group opener counts once; its contents are alternatives.
                other += 1
        depth += s.count("{") - s.count("}")
    return locs, other


def profile(key: str) -> dict | None:
    body = find_definition(key)
    if body is None:
        return None
    out = {"locations": 0, "conditions": 0, "pools": 0}
    for field in ("potential", "allow"):
        m = re.search(rf"^\s*{field}\s*=\s*\{{", body, re.M)
        if not m:
            continue
        blk = _block(body, m.start())
        loc, oth = _count_conditions(blk)
        out["locations"] += loc
        out["conditions"] += oth
    for field in ("areas", "regions", "provinces", "locations"):
        m = re.search(rf"^\s*{field}\s*=\s*\{{", body, re.M)
        if m:
            out["pools"] += len(_block(body, m.start()).split())
    return out


MOD_ROOT = os.path.expanduser("~/Projects/national_destinies/in_game/common")


def crisis_systems(key: str) -> int:
    """Custom situations and disasters this formable owns.

    A tag with its own crisis chain genuinely has more to explain after
    formation than one without: DNM's post-formation section is a walkthrough
    of three interlocking systems. This is read from the mod files rather than
    declared in the guide, so it cannot be claimed to win budget.
    """
    tag = key[:-2].lower() if key.endswith("_f") else key.lower()
    n = 0
    for kind in ("situations", "disasters"):
        n += len(glob.glob(os.path.join(MOD_ROOT, kind, f"99_nd_{tag}.txt")))
    return n


def budget(prof: dict | None, roads: int = 1, doctrines: int = 2,
           crises: int = 0) -> dict:
    """Per-section word budgets, fitted at about 1.3x the corpus median.

    Medians measured 2026-08-07: Concept 102, Forming it 150, doctrine 96,
    What happens 36, After forming 116, Notes 80.
    """
    p = prof or {"locations": 2, "conditions": 3, "pools": 2}
    forming = 90 + 22 * p["locations"] + 18 * p["conditions"] + 130 * max(0, roads - 1)
    return {
        "Concept": 135,
        "Forming it": max(140, min(forming, 400)),
        "Pick your founding doctrine on formation": 40 + 45 * max(2, doctrines),
        "What happens on formation": 60,
        "After forming": 170 + 60 * crises,
        "Notes": 120,
    }


def total_budget(roads: int = 1, crises: int = 0) -> int:
    """Whole-guide cap, deliberately well under the sum of the sections.

    A guide should not max out every section at once. Without this, generous
    per-section budgets summed to 1006 words for GOT, which is looser than the
    flat cap they replaced, and the guide stayed a wall of text. 700 is the
    corpus's own soft ceiling; the allowances are the same earned ones.
    """
    return 700 + 130 * max(0, roads - 1) + 60 * crises


def main() -> int:
    guides = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "data", "guides")
    print(f"{'formable':22s} {'locs':>4s} {'cond':>5s} {'pools':>6s}  forming-budget")
    missing = []
    for path in sorted(glob.glob(os.path.join(guides, "*.md"))):
        key = os.path.basename(path)[:-3]
        if key == "STYLE":
            continue
        pr = profile(key)
        if pr is None:
            missing.append(key)
            continue
        print(f"{key:22s} {pr['locations']:4d} {pr['conditions']:5d} "
              f"{pr['pools']:6d}  {budget(pr)['Forming it']:4d}")
    if missing:
        print("\nno definition found: " + ", ".join(missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
