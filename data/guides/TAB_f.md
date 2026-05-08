---
priority_starters:
  - tag: BOH
    note: "Bohemia. Czech-cultured, owns Husinec at start, and is the only realistic seed for the Hussite religion. The whole formation arc plays out as the Hussite Wars: trigger the wars, flip to Hussite, win the crusades, then form Tabor as the radical-republican settlement."
  - tag: MVA
    note: "Moravia. Moravian-cultured (also accepted by the formable), Catholic at start, smaller than BOH but already in the Bohemia and Moravia areas. A harder Hussite run because you do not own Husinec; you must take it from BOH or from whoever holds Bohemia by then."
hide_auto: true
---

## Concept

Tabor Republic is the Hussite radical wing made permanent. The
historical reference is the 1419 to 1452 Tabor Brotherhood: a
peasant-egalitarian commune of refugees and burghers on a hill in
southern Bohemia, governed by elective captains, defended by
Žižka's vozová hradba (war-wagon laager) and the píšťala
hand-cannon, and refusing the Compactata of Basel that absorbed the
moderate Utraquist wing back into Catholic legitimacy.

The alt-history premise is that Lipany (1434) is averted: the
radical Tabor and Sirotci field armies survive instead of being
crushed by the Utraquist-Catholic compromise. The chalice republic
becomes a sovereign continental state with the Four Articles of
Prague as constitutional law, married priesthood, vernacular
scripture, and communal property.

## Forming it

1. **Start as Bohemia (BOH) or Moravia (MVA).** The `potential`
   block accepts Czech or Moravian culture. BOH is by far the
   stronger seed: it starts Catholic but holds Husinec (Hus's
   birthplace), the named formation location.
2. **Trigger the Hussite Wars and flip to the Hussite religion.**
   This is not part of the formable itself; the religion comes from
   vanilla Bohemia's Hussite Wars mechanic (advances and generic
   actions in `country_BOH.txt` and `hussite_wars_actions.txt`). You
   cannot form Tabor until the country's religion is hussite.
3. **Hold Husinec.** The only named location requirement. Hus's
   birthplace, the symbolic hearth of the chalice movement.
4. **Hold 85 percent of Bohemia and Moravia.** A high fraction
   reflecting the formable's small territorial scope. Keep your
   Czech-Moravian core consolidated; Silesia and Lusatia are not
   required for formation but feature in the destiny tree.
5. **Form Tabor.** The form_effect grants the permanent
   `nd_tab_peasant_commune` modifier (mirroring vanilla
   peasant_republic_reform's country modifiers, so the player gets
   the institutional benefits without burning a major-reform slot).

## Pick your founding doctrine on formation

Two 20-year doctrines, both of which also flip the government type
to republic:

- **Commune of Brethren.** The radical wing. Communal property,
  married priesthood, women combatants, full Sirotci radicalism.
  Pushes plutocratic and communal societal values. Unlocks the
  Communal Republic destiny path.
- **Calixtine Compact.** The disciplined wing. Prokop the Great's
  institutional vision: chalice for all, but the Czech nobles lead
  and the war-wagon army stays under regular command. Pushes
  traditionalist and slightly conciliatory. Unlocks the Czech
  Reformation destiny path.

## What happens on formation

- Permanent Tabor Peasant Commune modifier applied (mirrors
  peasant_republic_reform's country modifiers).
- Mild stability bonus.
- Government type changes to republic on either choice.
- Formation event fires with the two doctrine choices.

## After forming

The destiny tree splits two ways:

- **Czech Reformation.** Path A. Export the chalice revolution
  across central Europe. Stage gates require Wrocław and Görlitz
  (Silesia and Lusatia), then Confessionalism embraced plus
  Wittenberg, then Augsburg, Geneva, and Leipzig with a continental
  Reformation army. Capstone building is the Synod Hall. Unlocked
  by Calixtine Compact.
- **Communal Republic.** Path B. Deepen the brotherhood at home.
  Stage gates require Meritocracy embraced, then a paper-trading
  capital market under the Renaissance, then the Enlightenment and
  3,000 gold. Capstone building is the Demokratický Sjezd
  (Democratic Congress). Unlocked by Commune of Brethren.

## Notes

- The Hussite religion does not exist at 1337 game start. It is
  spawned by Bohemia's vanilla Hussite Wars chain. Plan a BOH run
  that triggers and survives the Hussite Wars before you can form.
- The advance tree is unusually long (27 advances across all six
  ages) because it traces the full Hussite story from Conrad
  Waldhauser's 1360s preaching through Comenius and the Czech
  Brethren, to a 19th-century Czech-republican civic militia. It
  carries seven DHE event chains: war-wagon doctrine, Four
  Articles, Lipany averted, vernacular scripture, married
  priesthood, the Brotherhood Diet, and Czech humanism.
- MVA is accepted by the formable but is a much harder seed: you
  do not start with Husinec and you must convert to a religion that
  vanilla only spawns through BOH's wars chain.
