---
priority_starters:
  - tag: BEN
    note: "Benin. The only Edo-cultured tag and starts already owning Benin City at country rank kingdom. There is no other realistic entry."
hide_auto: true
---

## Concept

The Kingdom of Benin is the Edo state of Benin City, famous for its
moated earthworks, the Oba's bronze plaques, and the guild quarters of
Igun Street. Forming it is essentially a flavour upgrade for BEN: a
formation event, advance tree, and destiny branches around the Oba's
divine authority versus the City of Guilds.

## Forming it

1. **Start as BEN.** Edo culture is the formation gate, and BEN is the
   only tag with it.
2. **Hold Benin City.** BEN owns it at start, so this is automatic.
3. **Hit 90% of the Benin and Lower Niger areas.** A high fraction.
   Push west into Yoruba-adjacent territory (mahin, ugbodu, uromi) and
   east along the lower Niger; tolerated cultures (yoruba, ijaw) help
   absorb neighbours without unrest.
4. **Pick your path on formation.**
   - *The Oba is the kingdom*: divine authority, palace-centred
     monarchy.
   - *The guilds are the kingdom*: Igun guild craft, brass-casting and
     ivory-carving economy.

## Pick your founding doctrine on formation

The formation event offers two 20-year doctrines. Picking one also gates
which destiny path you can later take.

- **The Oba is the kingdom** (*Oba's Divine Authority*, 20 years).
  Sacred kingship: the Oba as the divine apex of Edo society, palace
  societies and the Eben sword warriors as the institutional core.
  Stat focus: crown estate power, legitimacy, infantry power,
  separatism reduction. Gates the Oba's Dominion destiny path (path A,
  Imperial Dominion line).
- **The guilds are the kingdom** (*City of Guilds*, 20 years). Igun
  Eronmwon brass-casters, Igbesanmwan ivory-carvers, and the Igun
  Street guild quarters as the institutional core. Stat focus:
  cultural tradition, production efficiency, trade efficiency,
  development, build cost reduction. Gates the Guild Imperium destiny
  path (path B, Guild Masters line).

## What happens on formation

- Country rank rises to Kingdom if currently Duchy or below (BEN
  already starts at rank_kingdom, so this is normally a no-op).
- Mild stability bonus.
- Formation event fires with the two doctrine choices.

## After forming

The destiny tree splits two ways:

- **Path A: The Oba's Dominion.** Conquest line. Stage 1 takes Oyo Ile
  and Calabar to dominate the Yoruba and Cross River frontiers. Stage
  2 reaches Kano and Ngazargamu, projecting Edo power into Hausaland
  and Bornu. Stage 3 takes Kumasi and Timbuktu and unlocks the **War
  Palace** (`nd_edo_war_palace`) capstone building. Unlocked by the
  Oba is the kingdom formation choice.
- **Path B: The Guild Imperium.** Economic and cultural line. Stage 1
  embraces banking and builds guild wealth. Stage 2 reaches a
  capital-market ivory trade and grows the Igun guilds. Stage 3 takes
  Ife (the Yoruba sacred capital) and unlocks the **Guild Masters'
  Hall** (`nd_edo_guild_masters_hall`) capstone building. Unlocked by
  the guilds are the kingdom formation choice.

## Notes

- Rank is set to kingdom if you are below it; BEN already starts at
  rank_kingdom, so the if-block is normally a no-op.
- The Igun Eronmwon (brass-casters) and Iyoba (queen mother) advance
  events both fire on research, so the artistic and political flavour
  comes through even on the more militaristic path.
