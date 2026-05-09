---
priority_starters:
  - tag: ENG
    note: "England. The historical parent. Colonise the East Coast region first, then either let your colonies break free or hold the territory yourself and form USA from the metropole. Owns the dominant culture group out of the gate."
  - tag: SCO
    note: "Scotland. British culture group, free to pursue Atlantic colonisation without the diplomatic entanglements of the English crown. Colonising Virginia and New England as Scotland is the cleanest non-English Anglophone path."
  - tag: ULS
    note: "Ulster. Anglo-Irish, Catholic, on the British Isles. Realistic only via the Ireland chain: unify the island as IRE first, then mount Atlantic colonisation. The longest underdog path."
hide_auto: true
---

## Concept

The United States is the revolutionary republic born of thirteen British colonies clinging
to the Atlantic seaboard. The historical reference is 1776 to roughly 1830: the
Constitution drafted in Philadelphia, the War of 1812, the Monroe Doctrine, the Lewis and
Clark expedition, and the early industrial transformation at Springfield Armory. The
mod's formation event names this explicitly: "Birth of the Republic", power divided,
rights enumerated, and sovereignty vested in the people.

The formable is gated only by culture. The `potential` requires a non-Native-American
culture in the **British group** (English, Scottish, Welsh, Irish, Cornish,
Anglo-Irish, etc.). There is no Allow block, so once the territory and culture line up,
formation just works.

## Forming it

1. **Start as a British-group tag.** ENG, SCO, IRE, or any of their splinters. There is
   no requirement that you be at war for independence in the EU5 sense; the gate is
   purely territorial and cultural.
2. **Project across the Atlantic.** Colonise or conquer the **East Coast region**. You
   need a fraction of 0.35, roughly a third of the locations.
3. **Hold the capital in-region.** `capital_required = yes` means your capital must sit
   inside the East Coast region at the moment of formation. Move it to a colonial
   location (Boston, Philadelphia, New York, Charleston) before you click form.
4. **Form USA.** Pick one of three founding doctrines on formation.

A British colonial power that has settled the seaboard but never lost the colonies can
relocate the capital to the New World and form USA directly. A European-based player
with no colonial program will not see this formable; the capital-in-region rule blocks
it.

## Pick your founding doctrine on formation

Three 40-year modifiers, each tied to a destiny path:

- **The tree of liberty must be watered.** Modifier *Spirit of '76*. Revolutionary
  fervour, citizen-soldier defence. Unlocks the Republican Experiment destiny path
  (republican institutions, industrial revolution, Beacon of Liberty).
- **From sea to shining sea.** Modifier *Manifest Destiny*. Westward settlement and
  expansion. Unlocks the Frontier destiny path (Oregon Trail, Gold Rush, American
  Imperium).
- **A government of laws, not of men.** Modifier *City upon a Hill*. Strong republican
  institutions as a model for the world. The third option is a flavour pick with no
  dedicated destiny continuation.

## After forming

The destiny tree branches twice. **Frontier path** drives Pacific reach via the Oregon
Trail, with Gold Rush or Pacific Trade modifiers, capping at American Imperium. **Republic
path** builds canal networks and the American System of Manufactures, capping at Beacon
of Liberty. The five DHE advance events (Constitutional Convention, War of 1812, Monroe
Doctrine, Lewis and Clark, American System) fire as you research the matching advances.

## Notes

- The vanilla form_effect is empty; the mod injects the formation event via INJECT.
- Native American cultures are explicitly excluded by `is_culture_native_american = no`.
  Any indigenous tag is locked out regardless of territory held.
- No religion gate. A Catholic Irish coloniser is just as eligible as a Protestant
  Englishman.
