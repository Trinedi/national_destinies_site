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
reach a number; padding is a worse fault than brevity, and the 700 figure
below is a ceiling to stay under rather than a target to reach.

**Soft ceiling 700 words of body, hard cap 900.** The corpus median is 574.
Past the hard cap it is a rewrite, not a trim.

A genuinely multi-road formable earns **+150 words per extra road**, counted
as numbered checklists under `Forming it`. DNM lays out two roads and so gets
850 and 1050. The allowance is earned rather than assumed: a long prose guide
with no checklist gets nothing, which is the point.

Length is the single clearest predictor of a bad guide. The eight guides that
prompted this document all sat between 1000 and 1300 words, and every one of
them had dropped the checklist in favour of prose. They earn no allowance and
fail on both counts.

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

**Never explain the mod's design.** The player does not care why a threshold
is set where it is, what it used to be, or what would break if it were
different. Cut every sentence that argues for a decision instead of stating
a fact.

- No: "The bar is deliberately low because it counts direct ownership only,
  which is why the union road works at all."
- Yes: "Own about 45 locations yourself. Vassal land does not count."

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
- Body is under 700 words, and no shorter than the formable actually needs
- `Forming it` is numbered
- No parentheses carrying a clause
- No sentence explaining a design decision
- Every threshold appears as a number
- Frontmatter parses
