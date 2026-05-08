---
priority_starters:
  - tag: TWK
    note: "Tawakoni. The only 1337 starter tag whose primary culture (tawakoni_culture) is in shoshoni_group. Starts on the southern Plains around melenudo/nokoni/waco, north of the Comanche heartland. You must conquer south to take kwahada (Llano Estacado) and penatuka (Penateka heartland), both held by XUM (Xumanos). The mod treats Numic-Plains migration as an Age 1 advance, so the formable is built around a TWK-style horseless southern Plains start that becomes a horse empire over the centuries."
hide_auto: true
---

## Concept

Comancheria is the Plains horse empire as a sovereign state. The
historical reference is the long 18th and early 19th century, when
the Numunu (Comanche) bands, Penateka, Yamparika, Quahadi, Nokoni,
and Kotsoteka, ran a tribute and raid economy across the southern
Plains and northern Mexico from the Llano Estacado out. The mod calls
this Numunu Sookobitu and structures it as a paraibo (peace chief)
plus tekwuniwapi (war chief) multi-band confederation rather than a
unitary kingdom, with cohesion held together through kinship,
captive incorporation, and the bison-and-horse economy.

This is alt-history. In 1337 the Numic bands were still in the Great
Basin and the Comanche as a distinct people did not yet exist. The
formable's potential gate is `culture_group:shoshoni_group`, so any
Shoshoni-group country may attempt the climb. The advance tree
treats horse mastery as a Renaissance-era arrival and the empire's
peak as Age 4 to Age 5, mirroring the historical timeline.

The tag is NUM, after Numunu (the Comanche endonym).

## Forming it

1. **Start as a shoshoni-group tag.** The potential gate covers
   tukudeka, bannock, kuccuntikka, penkwitikka, kusiutta, tetadeka,
   haivodika, watatikka, wiyimpihtikka, monachi, kuhtsutuuka, and
   tawakoni cultures. In 1337 only **TWK** (Tawakoni) starts with a
   shoshoni-group primary culture. Other shoshoni-group cultures
   exist as pops in the Great Basin but no tag holds them at game
   start.
2. **Conquer kwahada and penatuka.** The `allow` block requires both:
   kwahada is the Llano Estacado heart, penatuka is the Penateka
   homeland. Both belong to **XUM** (Xumanos) at game start. From a
   TWK opening you push southwest into XUM's territory.
3. **Hold 45 percent of the southern Plains arc.** Required fraction
   is 0.45 across Texas, Natahende, High Plains, Central Plains, and
   the Rockies. This is a wide spread but a low fraction, so a
   focused southern Plains and northern Texas conquest qualifies.
4. **Be at peace at home.** `in_civil_war = no` is part of `allow`.
5. **Form Comancheria.** Country rank rises to Kingdom on formation
   if below it. Capital sets to **kwahada**.

## Pick your founding doctrine on formation

The formation event offers two 30-year doctrines:

- **Continental Empire.** The raid-and-tribute war machine. Light
  cavalry power, movement speed, looted amount, manpower, and a
  large attrition penalty inflicted on hostile armies. The historical
  Comancheria of the Great Raid era. Shifts Offensive vs Defensive
  sharply left (offensive). Path A, Continental Tribute Empire,
  requires this choice.
- **Sovereign Nation.** The treaty state. Diplomatic reputation,
  improve-relations impact, separatism reduction, literacy, and
  assimilation speed. The Council of the Comanche Nation as a
  permanent seat of negotiation. Shifts Centralization vs
  Decentralization sharply left (centralization). Path B,
  Pan-Indigenous Confederation, requires this choice.

## What happens on formation

- Capital moves to **kwahada** (Llano Estacado).
- Country rank rises to Kingdom if below it.
- Permanent **Paraibo Confederation** country modifier is granted
  (the multi-band federation governance with paraibo peace chiefs
  and tekwuniwapi war chiefs).
- Mild stability bonus.
- Formation event fires with the two doctrine choices.

## After forming

The destiny tree splits two ways.

- **Continental Tribute Empire.** Push south into Mexico. Stage 1
  takes tamaulipeco and maratine (the Tamaulipas frontier) with a
  30-army gate. Stage 2 demands guachichil, cuencame, and chisos in
  Coahuila with a 50-army and 3500-development bar. Stage 3
  (continental hegemony) requires mapimi, cuanales, alazapa, and
  xumani plus a 75-army, 75-prestige, and 3000-gold gate. Capstone is
  the Imperial Bison Council. Unlocked by the Continental Empire
  formation choice.
- **Pan-Indigenous Confederation.** Build a treaty federation across
  the Plains. Stage 1 needs Legalism embraced plus 75 stability and
  50 prestige. Stage 2 takes he_sapa (the Black Hills) and awatixa
  with the printing press institution. Stage 3 demands bighorn_
  mountains, marapa, and minisose, plus 5000 development, 75
  prestige, and 75 stability. Capstone is the Treaty Hall. Unlocked
  by the Sovereign Nation formation choice.

The path you cannot take with a given doctrine still appears in the
tree but its first stage requires the other path's variable. Commit
on formation.

## Notes

- The advance tree mirrors history closely: Age 1 is pre-horse Numic
  tradition (numic migration, seasonal camps, skirmisher levies),
  Age 2 is the horse arriving and the Pueblo Revolt scattering its
  herds (horse mastery, Pueblo Lessons, paraibos confederation), Age
  3 to 5 is the high-empire Comanchero trade, captive incorporation,
  raid economy, Council of the Comanche Nation, and the Llano
  Estacado refuge.
- DHE events trigger off the major advances: horse arrival,
  Comanchero trade, captive incorporation, Council Hill
  negotiations, the Mexico-campaign Great Raid era, and the Llano
  Estacado heartland fortifications.
- The formable is `rule = plausible`, so it appears in the formables
  list to any shoshoni-group country, not only after the Plains have
  been pacified.
