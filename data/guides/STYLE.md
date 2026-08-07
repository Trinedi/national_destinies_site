# How to write a formable guide

A guide answers one question: **how do I get this, and what happens after?**
A player opens it mid-campaign, skims for thirty seconds, and leaves. It is a
checklist with enough flavour to explain why the checklist is worth doing. It
is not an essay, and it is not documentation of how the mod was built.

Rules are enforced by `scripts/check_guides.py`. Run it before committing.

## Structure

Use these headings, in this order, and do not invent new ones. 26 of 47
guides already match exactly.

```
## Concept
## Forming it
## Pick your founding doctrine on formation
## What happens on formation
## After forming
## Notes
```

Two sections may be dropped when they do not apply:

- **Pick your founding doctrine** when the formation event offers no choice.
- **Forming it** only for a formable nobody can press a button for. `BYZ_f`
  is the sole case: it is frontmatter-only, carrying a `special_notes` warn
  card instead of a body.

## Length

**There is no minimum.** A one-button formable deserves a short guide. The
shortest in the corpus is 257 words and it is fine. Never add a sentence to
reach a number: padding is a worse fault than brevity.

**Length follows how much the player must DO, not how much history exists.**
That is the whole rule, and it is enforced per section rather than as one
total, because a flat total let the fat hide in `After forming` (corpus
median 116 words, while the bad guides ran 300).

`scripts/formable_complexity.py` reads the formable definition and counts the
things a checklist has to state: named `owns = location:x` requirements,
other conditions, and how many territory pools the fraction spans. From that
it sets a per-section budget:

| Section | Budget |
|---|---|
| Concept | 160 |
| Forming it | 90 + 22/location + 18/condition, min 140, max 420 |
| Pick your founding doctrine | 40 + 55 per option |
| What happens on formation | 80 |
| After forming | 210, +60 per custom situation or disaster |
| Notes | 160 |

Two allowances are **earned from the mod files, never claimed in the guide**,
so no guide can talk itself into more room:

- **+130 words per extra formation road**, counted as numbered checklists
  under `Forming it`. A long prose guide with no checklist earns nothing.
- **+60 words per custom situation or disaster** the tag owns. DNM has to
  walk through three interlocking crisis systems; nobody else does.

A section over budget by more than 15% is an error. Under that it is a nudge,
because a budget is an estimate and a hard edge at exactly the estimate fires
on guides two words over and trains you to ignore it.

If a guide genuinely cannot fit, check the budget inputs before rewriting the
rule to suit the draft. That temptation has been wrong every time so far: a
three-doctrine guide felt like it needed 960 words until the corpus showed
that NIN does three doctrines and two roads in 803.

## Forming it must be a numbered checklist

Not prose. A player looking up requirements wants a list they can tick off.

```
1. **Kingdom rank or better**, or the Austrian Archduchy reform.
2. **Control Vienna.** You do not have to own it. It counts if the crown
   that owns it is your vassal or your union junior.
3. **Own your own capital.** Hungary needs Buda. Bohemia needs Prague.
```

Each step is a bolded imperative, then at most one sentence of qualification.
If a step needs three sentences, it is two steps.

**Multi-path formables get one checklist per road**, then a small table
showing what each origin already holds and what it still needs. Do not repeat
the same requirement once per origin in prose.

## Voice

Write to a player, in the second person, about their campaign.

**Never explain the mod's design. This is an error, not a style nit.** The
player does not care why a threshold sits where it does, what it used to be,
what would break if it changed, or that an absence was a decision rather than
an accident. Cut every sentence that argues for a choice instead of stating a
fact.

- No: "The bar is deliberately low because it counts direct ownership only,
  which is why the union road works at all."
- Yes: "Own about 45 locations yourself. Vassal land does not count."
- No: "The tree has no naval content at all, which is a stated design choice."
- Yes: "There are no ships anywhere in the tree."

Softening the justification does not remove it. "A kingdom that has to fight
for a mountain corridor to exist is a land power" is the same move in a nicer
suit, and it was still there after a rewrite that was supposed to have cut it.

Three habits that all count as design talk, and all are caught by the linter:

- **The mod as the actor.** "The mod treats", "the mod's formation event",
  "the tree builds around them". Say what the country is or does instead.
- **Development history.** The Workshop, the requester, "already exists in
  vanilla and has never had content", "the densest in this batch". None of
  this exists for the player.
- **Marking intent.** "deliberately", "by design", "on purpose", "not an
  oversight", "is the point". If an absence matters, state the absence.

Never write a note admitting the guide is incomplete. One guide shipped
"the mod's events file was not read in full for this guide"; that is a
message to the author, and it was deleted rather than reworded.

**No changelog voice.** "No longer the punishing start it once was" means
nothing to someone who never played the old version.

**No parenthetical explanation.** If it matters, it is a sentence. If it does
not, cut it. Short asides for a name or a date are fine; a parenthesis
carrying a clause is not.

**No design-room vocabulary.** Words we coin while building the mod read as
alien in a guide: lever, checkpoint, counter, branch, chain, exit, gate,
payoff, seed.

**State numbers plainly.** "Reach 80% war score", not "reach a high war
score". Every threshold a player must hit belongs in the guide as a figure.

## Script identifiers

Use plain names in **Concept** and **Forming it**: Buda, not `location:buda`.
A player reading requirements should never need to know a key.

Backticked identifiers are allowed in **Notes**, where a reader is already
looking for detail, and only when the identifier is genuinely useful to
someone editing or debugging.

## Frontmatter

`priority_starters` lists the countries worth starting as, best first, each
with a one-sentence note saying what that start already has and what it
implies. Keep notes to one sentence. `hide_auto: true` suppresses the
generated requirement block when the guide covers it better in prose.

## Checklist before committing

- Headings match the canonical list
- Every section is inside its budget (`check_guides.py --budgets`)
- No sentence explains, justifies, or marks a design decision
- `Forming it` is numbered
- No parentheses carrying a clause
- No sentence explaining a design decision
- Every threshold appears as a number
- Frontmatter parses
