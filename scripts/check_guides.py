#!/usr/bin/env python3
"""Lint formable guides against data/guides/STYLE.md.

Usage:
    python3 scripts/check_guides.py            # all guides
    python3 scripts/check_guides.py DNM_f      # one guide
    python3 scripts/check_guides.py --summary  # counts only
    python3 scripts/check_guides.py --budgets  # show each guide's word budget

Exit code 1 if any guide has an error, 0 otherwise. Warnings never fail.
"""
from __future__ import annotations

import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import formable_complexity as fc  # noqa: E402

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

# How far over a section budget counts as an error rather than a nudge.
TOLERANCE = 1.15

# There is no minimum length. A one-button formable deserves a short guide,
# and a floor could only ever be met by padding. Budgets come from
# formable_complexity: how much a player must DO, not how much history exists.
# Sections are capped individually because a flat total let the fat hide in
# "After forming", where the corpus median is 116 words and bad guides run 300.

# Words we coin while designing the mod. They read as alien to a player.
JARGON = [
    "lever", "checkpoint", "counter", "branch", "chain", "payoff",
    "seed", "gate", "instance", "tooltip", "flag",
]

# Talking to the player about the mod's design instead of their campaign.
# This is the single most persistent failure in the corpus, so it is an error.
# "deliberately" and "by design" USED to be allowed here as terse "this absence
# is intentional" tags; that exemption was revoked 2026-08-07 by the user, who
# reads the whole category as design-room chatter regardless of how terse it is.
# Matched CASE-SENSITIVELY, and each pattern is anchored to the mod as the
# subject. A blunt \bdeliberate\b flagged "Pick deliberately" (advice to the
# player) and "deliberately standardised its own vernacular" (a fact about the
# historical Occitans); a blunt \bWorkshop\b flagged a goldsmith's workshop.
DESIGN_TALK = [
    # Stating that a decision was made, rather than stating the fact.
    (r"\b(is|are|was|were) a? ?deliberate", "deliberate"),
    (r"\bdeliberately (blocked|excluded|absent|omitted|left|kept|avoided|not|"
     r"divergent|coupled|shut|barred)\b", "deliberately X"),
    (r"\bon purpose\b", "on purpose"),
    (r"\bby design\b", "by design"),
    (r"\bdesign (choice|decision)\b", "design choice"),
    (r"\bnot an oversight\b", "not an oversight"),
    (r"\b(is|are) the point\b", "is the point"),
    (r"\bthat is the design\b", "that is the design"),
    # The mod, rather than the country, as the actor.
    (r"\b([Tt]he mod|[Tt]his content|[Tt]he tag|[Tt]he file|[Tt]he tree|"
     r"[Tt]his batch|[Tt]he batch)\s+"
     r"(treats|says|ships|builds|takes|does|refuses|owns|assumes|gives|uses|"
     r"spends|models|frames|handles)\b", "mod-as-actor"),
    (r"\b[Tt]he mod'?s\b", "the mod's"),
    # Development history the player was never part of.
    (r"\b[Tt]he requester(s)?\b", "the requester"),
    (r"\bWorkshop\b", "Workshop"),          # Steam Workshop, not a goldsmith's
    (r"\balready exists in vanilla\b", "already exists in vanilla"),
    (r"\bnever had any content\b", "never had any content"),
    (r"\bin th(is|e) batch\b", "in this batch"),
    # Arguing for a decision instead of stating a fact.
    (r"\bwhich is why\b", "which is why"),
    (r"\b[Tt]hat is why\b", "that is why"),
    (r"\bthe reason is\b", "the reason is"),
    (r"\bwe chose\b", "we chose"),
    (r"\bour design\b", "our design"),
    (r"\bused to be\b", "used to be"),
    (r"\bno longer the\b", "no longer the"),
    (r"\b(which )?is what makes\b", "is what makes"),
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


def sections(body: str) -> dict[str, str]:
    out = {}
    for chunk in re.split(r"^## ", body, flags=re.M)[1:]:
        name, _, rest = chunk.partition("\n")
        out[name.strip()] = rest
    return out


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

    secs = sections(body)
    forming = secs.get("Forming it", "")
    doctrine = secs.get("Pick your founding doctrine on formation", "")

    # Forming it must be a numbered checklist.
    if forming and not re.search(r"^\d+\. ", forming, re.M):
        errors.append("'Forming it' has no numbered checklist")

    # Budget each section from how complex the formable actually is to form.
    roads = max(1, len(re.findall(r"^1\. ", forming, re.M)))
    doctrines = max(2, len(re.findall(r"^- \*\*", doctrine, re.M)))
    budget = fc.budget(fc.profile(name), roads=roads, doctrines=doctrines,
                       crises=fc.crisis_systems(name))
    for sec, cap in budget.items():
        got = len(secs.get(sec, "").split())
        # A budget is an estimate, so a hard edge at exactly the estimate is
        # false precision: it fires on guides two words over and trains you to
        # ignore it. Only a real overrun is an error.
        if got > cap * TOLERANCE:
            errors.append(f"'{sec}' is {got} words, over its {cap} budget")
        elif got > cap:
            warns.append(f"'{sec}' is {got} words, just over its {cap} budget")

    # Whole-guide cap. Sections are budgeted generously one at a time, so
    # without this a guide can pass every section and still be a wall of text.
    total = fc.total_budget(roads=roads, crises=fc.crisis_systems(name))
    if words > total * TOLERANCE:
        errors.append(f"{words} words total, over the {total} cap; cut, do not shuffle")
    elif words > total:
        warns.append(f"{words} words total, just over the {total} cap")

    # Parentheses carrying a clause. Lists are fine and stay.
    clauses = [p for p in re.findall(r"\(([^)]+)\)", body)
               if len(p.split()) >= 5 and CLAUSE_MARKERS.search(p)]
    if clauses:
        errors.append(f"{len(clauses)} parenthetical clause(s), e.g. \"({clauses[0][:52]}...)\"")

    # Design talk aimed at the player.
    hits = []
    for pat, label in DESIGN_TALK:
        if re.search(pat, body):  # case-sensitive on purpose, see DESIGN_TALK
            hits.append(label)
    if hits:
        errors.append(f"talks about the mod's design: {', '.join(sorted(set(hits))[:4])}")

    # Design-room vocabulary.
    jargon = sorted({w for w in JARGON if re.search(rf"\b{w}s?\b", body, re.I)})
    if jargon:
        warns.append(f"design-room word(s): {', '.join(jargon)}")

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

    if "--budgets" in sys.argv:
        for p in paths:
            name = os.path.basename(p)[:-3]
            body = body_of(open(p, encoding="utf-8").read())
            secs = sections(body)
            forming = secs.get("Forming it", "")
            doctrine = secs.get("Pick your founding doctrine on formation", "")
            b = fc.budget(fc.profile(name),
                          roads=max(1, len(re.findall(r"^1\. ", forming, re.M))),
                          doctrines=max(2, len(re.findall(r"^- \*\*", doctrine, re.M))))
            got = len(body.split())
            print(f"{name:22s} {got:5d} / {sum(b.values()):5d}  " +
                  " ".join(f"{k.split()[0][:5]}:{len(secs.get(k,'').split())}/{v}"
                           for k, v in b.items()))
        return 0

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
