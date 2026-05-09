---
priority_starters:
  - tag: ENG
    note: "England. The British half of the historical Canadian story. Colonise the Canada region (Hudson Bay, the Maritimes, the St. Lawrence) and form from a New World capital."
  - tag: FRA
    note: "France. The French half of the historical story (Nouvelle-France, Quebec, Acadia). French-group cultures qualify for CAN as readily as British ones; a Quebec-anchored Catholic confederation is the most flavourful path."
  - tag: SCO
    note: "Scotland. British group, no entanglements in continental Europe. A clean Atlantic colonial run focused entirely on the north."
  - tag: NOR
    note: "Norway is sometimes raised in community discussion (Vinland flavour), but Norse cultures are not in the british_group or french_group, so NOR cannot form CAN unless its primary culture flips. Treat as flavour-only."
hide_auto: true
---

## Concept

Canada is the northern Confederation, the dominion that knit fur-trade frontier,
Atlantic fishery, and St. Lawrence farmland into a single transcontinental polity.
The mod's formation event treats it as a confederation moment: the Northern Dominion
(westward settlement, frontier endurance) versus the Great Trading Nation (river
networks, fur-trade economy, fishing fleets).

The formable is gated only by culture. Either **British group** (English, Scottish,
Welsh, Irish, etc.) or **French group** (Picard, Norman, Angevin, etc.) qualifies.
This is the only formable in the New World cluster that explicitly opens both
Anglophone and Francophone paths.

## Forming it

1. **Start as a British-group or French-group tag.** ENG, SCO, IRE, FRA, or their
   splinters.
2. **Colonise the Canada region.** You need a fraction of 0.35, roughly a third of the
   locations. Hudson Bay, Newfoundland, Acadia, the St. Lawrence valley, and the Great
   Lakes basin all sit inside `canada_region`.
3. **Move your capital into the region.** `capital_required = yes` forces your capital
   to be inside the Canada region at formation. Quebec, Montreal, or Halifax are the
   obvious anchors.
4. **Form Canada.** Pick one of two founding doctrines.

The bar is lower than USA's (the wider culture pool plus a slightly thinner
territorial fraction in the same geographic latitude band), but the practical path is
the same: a transatlantic colonial program that ends with a New World capital.

## Pick your founding doctrine on formation

Two 30-year modifiers, each tied to a destiny path:

- **We shall master this northern land.** Modifier *The Northern Dominion*. Frontier
  endurance, settler expansion. Unlocks the Pacific Reach destiny (Klondike Gold Rush,
  orderly frontier, Continental Dominion).
- **Our wealth flows through the waterways.** Modifier *The Great Trading Nation*.
  River-and-coast commerce, fur posts, Grand Banks fisheries. Unlocks the Atlantic
  Trade destiny (Caribbean Commerce, sugar triangle or free port, Global Trade
  Empire).

## After forming

The destiny tree splits two ways. **Pacific path** drives transcontinental reach
through the Klondike and ends in Continental Dominion (army or pax canadiana
capstone). **Atlantic path** runs through Caribbean trade and ends in a global
commercial-and-diplomatic emporium. The advance DHEs (Hudson's Bay Company,
Canadian Voltigeurs, Confederation) fire as you research the matching advances.

## Notes

- The vanilla form_effect is empty; the mod injects the formation event via INJECT.
- Both Anglophone and Francophone runs flip the country's confederation framing
  through the same event, but the underlying culture stays whatever you brought to
  formation. There is no automatic culture conversion to a new "Canadian" culture.
- Norse-group, German-group, or Iberian-group tags cannot form CAN regardless of
  how much of the region they hold. The culture gate is hard.
