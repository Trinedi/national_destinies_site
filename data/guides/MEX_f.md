---
priority_starters:
  - tag: CAS
    note: "Castile. The historical parent of New Spain. Colonise Mesoamerica from the Caribbean, fold the Aztec heartland into the empire, then form Mexico from a New World capital. The cleanest Iberian path."
  - tag: POR
    note: "Portugal. Iberian group qualifies, though Portuguese colonial focus historically pointed at Brazil and the Indies. A viable second-choice Iberian run for a player who wants to elbow Castile out of Mesoamerica."
  - tag: ARA
    note: "Aragon. Iberian group, Mediterranean-anchored. A long colonial program from a Mediterranean base, more painful than Castile but mechanically permitted."
  - tag: TNC
    note: "Tenochca (Mexica) at Tenochtitlan. The mestizo path: a Nahua-culture tag that converts to Christianity. The `allow` block accepts native cultures that adopt Christianity, mirroring the historical mestizo synthesis. TTZ (Texcoco) and TEP (Tepanec) are equally viable Nahua starters."
hide_auto: true
---

## Concept

Mexico is the post-independence republic born from three centuries of New Spain. The
mod's formation event frames it as the moment of independence: the Plan de Iguala's
Three Guarantees (Religion, Independence, Union) against the popular fervour of the
Grito de Dolores. Hidalgo and Morelos against Iturbide.

The mod's design references the mestizo identity directly: the formable accepts both
the Iberian colonial framing (Castile, Portugal, Aragon) and the Indigenous-converted
framing (a Native American culture that has adopted a Christian religion). This is
the only New World formable in this cluster that explicitly designs around the
indigenous-Catholic synthesis rather than treating natives as a hard exclusion.

## Forming it

The `potential` and `allow` are looser than USA or CAN, but more nuanced.

**Potential** opens the formable to anyone with an Iberian-group primary or accepted
culture, OR any Christian-religion country.

**Allow** narrows the actual click to two cases:
1. Your primary culture is Iberian-group, OR
2. Your primary culture is Native American AND your country religion is in the
   Christian group.

### Path 1: Iberian colonial power

1. **Start as CAS, POR, or ARA.** Push into the Caribbean and Mesoamerica through
   the standard colonisation flow.
2. **Take 50 percent of `mesoamerica_region`.** Aztec heartland, Yucatan, Guatemalan
   highlands, the Caribbean coast.
3. **Move your capital into Mesoamerica.** `capital_required = yes` enforces this.
   Tenochtitlan (Mexico City) is the obvious anchor.
4. **Form Mexico.**

### Path 2: Indigenous Christian path

1. **Start as a Mesoamerican tag.** Aztec is the obvious choice; smaller Mesoamerican
   tags work the same way mechanically.
2. **Convert your country religion to a Christian denomination.** Catholic is
   thematic. The conversion can come from missionary pressure, an event, or a
   peace-deal religion change.
3. **Hold 50 percent of Mesoamerica.** Native tags often start with a real chunk
   already.
4. **Form Mexico.** The mestizo synthesis fires through the same formation event the
   Spanish path uses.

The fraction (0.5) is significantly higher than USA or CAN (0.35), reflecting the
denser Mesoamerican geography and the greater historical specificity of the territory.

## Pick your founding doctrine on formation

Two 30-year modifiers:

- **Religion, Independence, Union: the Three Guarantees shall be our foundation.**
  Modifier *Three Guarantees*. The conservative-Catholic Plan de Iguala framing,
  binding the diverse peoples of Mexico under tradition and order.
- **The Cry of Dolores echoes still: the people's revolution continues!** Modifier
  *Cry of Dolores*. The popular-revolutionary framing of Hidalgo and Morelos,
  sovereignty rooted in the people rather than the colonial order.

## After forming

The destiny tree branches twice. **Northern March / Empire of Anahuac** path drives
imperial expansion under an iron hand or an imperial court, ending in Continental
Destiny (continental army or American dynasty). **Silver Republic / Liberal Republic
/ Arsenal of Democracy** path builds the silver-standard liberal economy through La
Reforma, ending in industrial dawn or an enlightened republic.

The advance DHEs (Bourbon Reforms, La Reforma, Silver Mining Revolution, Grito de
Dolores) fire on matching advance research.

## Notes

- The vanilla form_effect is empty; the mod injects the formation event via INJECT.
- The Native-Christian path is mechanically supported but socially demanding: you
  must drag your country religion across the gap before the `allow` opens. This is
  a multi-decade conversion project for an Aztec player.
- Iberian-group cultures from Iberia itself qualify equally; nothing forces a
  colonial Castilian to flip culture. The mestizo framing comes through the
  formation event narrative, not through a forced culture change.
