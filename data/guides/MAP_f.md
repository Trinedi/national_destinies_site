---
priority_starters:
  - tag: MPC
    note: "Mapuche. The canonical Wallmapu starter. Already mapuche_culture, already in tain feyentun religion, and starts owning wenteche, the only required location. You can form MAP_f essentially as soon as you can fund the rank-up and clear the formable's plausible-mode prereqs."
  - tag: PHE
    note: "Picunche. Pikumche-cultured (mapudungun_group), so the culture potential is satisfied. Sits north of MPC in the central Chilean valley; you must take wenteche from MPC before forming. Pick this if you want to absorb the northern Mapuche heartland first."
hide_auto: true
---

## Concept

Wallmapu is the Mapuche federation as a sovereign kingdom. The
historical reference is the Arauco War: from the 1550s through the
late 19th century the Mapuche south of the Bio-Bio successfully
resisted Spanish, then Chilean, conquest. They turned back Pedro de
Valdivia at Tucapel (1553) under Lautaro, destroyed the Spanish "Seven
Cities" at Curalaba (1598), and forced the Spanish crown to negotiate
the Treaty of Quilin (1641), the only such recognition of an
indigenous American polity. The federation was structured as Lof
clans gathered into Rewes and nine-Rewe Aillarewes, governed by Lonko
peace-chiefs and elected wartime Toki, with no hereditary king.

The mod expresses this as a confederation that becomes a kingdom on
formation. The Toki Council Federation modifier is permanent. The
formation event then asks whether the Mapuche stay in the cordillera
behind the Bio-Bio, or ride east of the Andes and take the fight to
the Spanish settler frontier.

## Forming it

1. **Start as a mapudungun-group tag** (MPC or PHE). The potential
   gate is `culture_group:mapudungun_group`, which covers Mapuche,
   Picunche, Pehuenche, Williche, and Purun Awqa. Of these only MPC
   and PHE exist as starting tags in 1337.
2. **Own wenteche.** The `allow` block has a single hard requirement:
   `owns = location:wenteche`, the central Mapuche heartland in
   Ngulumapu. MPC starts with it. PHE must take it from MPC.
3. **Hold 90 percent of Ngulumapu and Puelmapu.** The required-
   locations fraction is 0.9 across Ngulumapu (the western, Chilean
   side of the Andes) and Puelmapu (the eastern, Argentine side).
   This is a high bar. Expect to fight your mapudungun neighbours and
   push east of the cordillera before the formable becomes available.
4. **Form Wallmapu.** Country rank rises to Kingdom on formation if
   below it.

## Pick your founding doctrine on formation

The formation event offers two 25-year doctrines:

- **Wallmapu Endurance.** The cordillera-defensive tradition.
  Hostile attrition, defensiveness, and morale. The shield that turned
  back Spain. Shifts your Offensive vs Defensive societal value
  sharply right (defensive). Path A of the destiny tree, the Free
  Republic of Reche, requires this choice.
- **Pillan's Spear.** The Lautaro doctrine of mounted offensive war.
  Light cavalry power, looted amount, and movement speed. Drives the
  huinca off the continent. Shifts Offensive vs Defensive sharply left
  (offensive). Path B, Continental Wallmapu, requires this choice.

## What happens on formation

- Country rank rises to Kingdom if below it.
- Formation event fires with the two doctrine choices.
- Permanent **Toki Federation** country modifier is granted (the Lof
  /Rewe/Aillarewe federation governance).
- Mild stability bonus.
- No capital move. Whatever your formation capital was stays.

## After forming

The destiny tree splits two ways. Both reward holding land beyond the
cordillera.

- **Free Republic of Reche.** The civic-diplomatic path. Codified
  Parlamento (annual treaty-assemblies), Free Republic of Reche
  (republican tradition, cabinet efficiency), and a capstone
  Recognized Among Nations stage that unlocks the Parlamento
  Permanente building and a major diplomatic boost. Unlocked by the
  Wallmapu Endurance formation choice.
- **Continental Wallmapu.** The imperial-expansion path. March of the
  Toki Mapu (own Valparaiso and Aconcagua), Cordillera Crossed (Cuyo
  and Kilmes), and Toki Apu of All Lands (Salta, Tandil, plus a
  75-army and 2000 development gate). Capstone is the Toki Apu Hall.
  Unlocked by the Pillan's Spear formation choice.

The path you cannot take with a given doctrine still appears in the
tree but its first stage requires the other path's variable, so
commit to your choice on formation.

## Notes

- The `rule = plausible` flag means MAP appears in the formables list
  to mapudungun-group countries even before the Bio-Bio frontier is
  pacified. Don't be surprised that it shows up early.
- The federation modifier is duration `-1` (permanent). Both doctrine
  modifiers stack on top of it for 25 years.
- DHE chain mirrors history: Tucapel triumph (Age 2) and Lautaro's
  doctrine for the first Mapuche cavalry corps; Curalaba uprising
  (Age 3); Treaty of Quilin (Age 4) where you can either codify the
  Spanish recognition (Quilin Compact) or refuse and remain unbroken.
