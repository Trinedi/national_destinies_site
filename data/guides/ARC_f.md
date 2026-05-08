---
priority_starters:
  - tag: CIL
    note: "Cilicia, the historical Hethumid kingdom. Already Armenian, already miaphysite, already owns Sis and most of the cilicia_area. The intended path: hold off the Mamluks, push into the Levant area, form ARC with the kingdom intact."
  - tag: ARM
    note: "Armenia (Caucasian, the Bagratid heartland). Excluded by ARC's `potential` block (`NOT = { tag = ARM }`). ARM has its own restoration arc; ARC is specifically the Mediterranean alt-history. Listed only to flag that this tag cannot form ARC."
  - tag: KCN
    note: "Khachen, an Armenian miaphysite principality in the Caucasus. Eligible by culture and religion but geographically far from Sis. Realistic only as a long restoration run that eventually pushes through Cilicia."
  - tag: SYU
    note: "Syunik. Same situation as KCN: Armenian miaphysite Caucasian principality with no easy line to Sis. A late-game restoration angle rather than a direct starter."
hide_auto: true
---

## Concept

Cilician Armenia is the alt-history of the Armenian Kingdom of
Cilicia surviving the 1375 Mamluk conquest and expanding westward
into a Mediterranean trade kingdom. The historical reference is the
Hethumid-Lusignan period (c. 1198 to 1375): an Armenian Christian
realm on the northeastern Mediterranean coast, plugged into Genoese
and Venetian networks through Ayas and Mopsuestia, courting the
Mongols against the Mamluks, and arguing for two centuries about
whether to formally unite with Rome.

ARC takes that fragile Mediterranean kingdom and gives it the
institutional weight to keep going. Tier 1 heritage covers Levon's
crown, the Italian merchant concessions, the Mongol embassies, the
Catholicate at Hromkla, Lusignan-era chivalric reform, and the
Cypriot Concord (the Lusignan house union with Cyprus).

The tag is ARC because vanilla EU5 already uses ARM for the Caucasian
Armenian heartland. ARC is specifically the Mediterranean cousin and
the `potential` block excludes ARM by design.

## Forming it

The formable accepts Armenian-cultured miaphysite countries other
than ARM itself.

1. **Be Armenian and miaphysite.** Both are required by `potential`.
   The `NOT = { tag = ARM }` clause keeps the Caucasian restoration
   path on its own track.
2. **Own Sis.** The seat of the Hethumid catholicate. CIL starts
   with it.
3. **Hold 50 percent of Cilicia plus Levant areas.** The fraction
   pool combines the cilicia_area and levant_area. You need half
   the locations across both.
4. **Form ARC.** It is Level 3 plausible.

CIL is by far the cleanest entry: Sis is already yours, you are
already miaphysite, and the cilicia_area is half-conquered on day
one. Pushing into the Levant area is the work. KCN or SYU starts
have to fight their way down through the Caucasus and Anatolia
before formation eligibility even opens up.

## Pick your founding doctrine on formation

The formation event offers two 30-year doctrines. Each swings a
societal value and gates one of the destiny paths.

- **Apostolic Sanctuary** (keep the kingdom undivided in faith).
  The highland clergy's answer: better isolation than the loss of
  the kingdom's soul. The Apostolic Church stands apart from
  Chalcedon and Rome alike. Pushes traditionalist_vs_innovative
  hard left. Gates the Levant Vanguard destiny path (Path A,
  Apostolic Imperium line).
- **Latin Union of Sis** (open the realm to Crusader Christendom).
  The barons' answer: better Cyprus than ruin, better the Pope than
  the desert. Formal union with Rome, Crusader court at Sis,
  Italian merchants in their own chapels at Ayas. Pushes
  outward_vs_inward hard left (toward outward). Gates the Cilician
  Reach destiny path (Path B, Mediterranean Apex line).

## What happens on formation

- Mild stability bonus.
- Country rank rises to Kingdom if currently Duchy or below.
- Capital moves to Sis.
- Formation event fires with the two doctrine choices.

## After forming

Tier 1 heritage covers the kingdom's foundational identity:
Levon's crown, the Italian merchant concessions, the Mongol
alliance, the Catholicate at Sis, Lusignan chivalric reform, and
the Cypriot Concord. Each comes with a DHE and a 15-year or 20-year
modifier choice.

The destiny tree splits two ways:

- **Path A: Apostolic Imperium.** Christian liberation push. Stage
  1 takes Jerusalem and Edessa (Urfa). Stage 2 takes Aleppo and
  Damascus (the great sees) with a choice between Conqueror's
  Charter (military) and Reconciled Sees (administrative). Stage 3
  capstone takes Acre and Mosul, with a choice of Armenian Jerusalem
  or Apostolic Inheritance modifier. Capstone building is the
  **Greater Catholicate**. Unlocked by the Apostolic Sanctuary
  formation choice.
- **Path B: Mediterranean Apex.** Italian-style Mediterranean trade
  empire. Stage 1 takes Antalya and Rhodes. Stage 2 builds the
  Aegean Condominium with a Genoese or Venetian axis. Stage 3
  capstone takes Alexandria and Smyrna with the Levantine Bourse
  or Armenian Lions modifier. Capstone building is the **Levantine
  Bourse**. Unlocked by the Latin Union of Sis formation choice.

## Notes

- The capital force-set to Sis means CIL keeps its capital on
  formation; KCN or SYU runs lose their Caucasian capital when ARC
  is formed.
- The Apostolic vs Latin choice is the kingdom's central historical
  tension, not a flavor toggle. Stage 2 modifiers on both paths
  reflect the choice (e.g. Reconciled Sees vs Conqueror's Charter
  on the Aleppo and Damascus stage). Pick deliberately.
- ARM (the Caucasian heartland) is deliberately blocked from ARC.
  The two are parallel restoration arcs, not interchangeable.
