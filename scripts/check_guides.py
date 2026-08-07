#!/usr/bin/env python3
"""Lint formable guides against data/guides/STYLE.md.

Usage:
    python3 scripts/check_guides.py            # all guides
    python3 scripts/check_guides.py DNM_f      # one guide
    python3 scripts/check_guides.py --summary  # counts only

Exit code 1 if any guide has an error, 0 otherwise. Warnings never fail.
"""
from __future__ import annotations

import glob
import os
import re
import sys

GUIDE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "data", "guides")

CANONICAL = [
    "Concept",
    "Forming it",
    "Pick your founding doctrine on formation",
    "What happens on formation",
    "After forming",
    "Notes",
]

# Frontmatter-only guides: a formable nobody can press a button for.
BODYLESS_OK = {"BYZ_f"}

# There is no minimum. A simple formable deserves a short guide, and a floor
# would only ever be satisfied by padding. The cap catches essays.
WORDS_MAX, WORDS_HARD = 700, 900
# Extra headroom per additional formation road laid out as a checklist.
ROAD_ALLOWANCE = 150

# Words we coin while designing the mod. They read as alien to a player.
JARGON = [
    "lever", "checkpoint", "counter", "branch", "chain", "payoff",
    "seed", "gate", "instance", "tooltip", "flag",
]

# Phrases where the guide narrates the mod's own design to the player.
# "deliberately" and "by design" are NOT here: the corpus uses them as terse
# "this absence is intentional, not a bug" tags, which is useful to a player.
RATIONALE = [
    "this is why", "the reason is", "we chose", "our design",
    "the mod treats", "used to be", "no longer the", "which is why",
]

# A parenthesis carrying a clause reads as an aside the sentence should have
# absorbed. A parenthesis carrying a LIST is useful and stays: enumerations of
# tags, cities or dates are the corpus's most common and most legible use.
CLAUSE_MARKERS = re.compile(
    r"\b(is|are|was|were|has|have|had|can|will|would|should|must|does|do|"
    r"makes|gives|means|because|since|so that|which|who|that you|if you)\b",
    re.I,
)


def body_of(text: str) -> str:
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            return parts[2]
    return text


def check(path: str) -> tuple[list[str], list[str]]:
    name = os.path.basename(path)[:-3]
    text = open(path, encoding="utf-8").read()
    body = body_of(text)
    errors: list[str] = []
    warns: list[str] = []

    heads = [m.group(1).strip() for m in re.finditer(r"^## (.+)$", body, re.M)]
    words = len(body.split())

    if not heads and not words:
        if name not in BODYLESS_OK:
            errors.append("empty body and not a known frontmatter-only guide")
        return errors, warns

    # Headings must be canonical and in order.
    unknown = [h for h in heads if h not in CANONICAL]
    if unknown:
        errors.append(f"non-canonical heading(s): {', '.join(unknown)}")
    ordered = [h for h in heads if h in CANONICAL]
    if ordered != sorted(ordered, key=CANONICAL.index):
        errors.append("headings out of canonical order")
    if "Concept" not in heads:
        errors.append("missing '## Concept'")
    if "Forming it" not in heads and name not in BODYLESS_OK:
        errors.append("missing '## Forming it'")

    # Forming it must be a numbered checklist.
    m = re.search(r"^## Forming it\s*$(.*?)(?=^## |\Z)", body, re.M | re.S)
    if m and not re.search(r"^\d+\. ", m.group(1), re.M):
        errors.append("'Forming it' has no numbered checklist")

    # Length. The cap scales with how many formation roads the guide lays out
    # as checklists, because a multi-road formable genuinely needs the space.
    # The allowance is earned, not assumed: it is granted per numbered list in
    # "Forming it", so a long prose guide with no checklist gets nothing.
    roads = len(re.findall(r"^1\. ", m.group(1), re.M)) if m else 1
    allowance = ROAD_ALLOWANCE * max(0, roads - 1)
    hard = WORDS_HARD + allowance
    soft = WORDS_MAX + allowance
    extra = f" (+{allowance} for {roads} formation roads)" if allowance else ""
    if words > hard:
        errors.append(f"{words} words, over the {hard} hard cap{extra}; rewrite rather than trim")
    elif words > soft:
        warns.append(f"{words} words, over the {soft} target{extra}")

    # Parentheses carrying a clause. Lists are fine and stay.
    clauses = [p for p in re.findall(r"\(([^)]+)\)", body)
               if len(p.split()) >= 5 and CLAUSE_MARKERS.search(p)]
    if clauses:
        errors.append(f"{len(clauses)} parenthetical clause(s), e.g. \"({clauses[0][:52]}...)\"")

    # Design rationale aimed at the player.
    for phrase in RATIONALE:
        if re.search(rf"\b{re.escape(phrase)}\b", body, re.I):
            errors.append(f"explains a design decision: '{phrase}'")
            break

    # Design-room vocabulary.
    hits = sorted({w for w in JARGON if re.search(rf"\b{w}s?\b", body, re.I)})
    if hits:
        warns.append(f"design-room word(s): {', '.join(hits)}")

    # Script identifiers outside Notes.
    before_notes = body.split("## Notes")[0]
    ids = re.findall(r"`([a-z_]+[:=][^`]*|[a-z_]{5,})`", before_notes)
    if ids:
        warns.append(f"script identifier(s) before Notes: {', '.join(sorted(set(ids))[:3])}")

    return errors, warns


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    summary = "--summary" in sys.argv
    paths = sorted(glob.glob(os.path.join(GUIDE_DIR, "*.md")))
    paths = [p for p in paths if os.path.basename(p) != "STYLE.md"]
    if args:
        want = {a.removesuffix(".md") for a in args}
        paths = [p for p in paths if os.path.basename(p)[:-3] in want]

    bad = clean = 0
    total_e = total_w = 0
    for p in paths:
        errors, warns = check(p)
        total_e += len(errors)
        total_w += len(warns)
        if errors:
            bad += 1
        else:
            clean += 1
        if summary or not (errors or warns):
            continue
        print(f"\n{os.path.basename(p)}")
        for e in errors:
            print(f"  ERROR   {e}")
        for w in warns:
            print(f"  warn    {w}")

    print(f"\n{len(paths)} guides: {clean} without errors, {bad} with errors "
          f"({total_e} errors, {total_w} warnings)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
