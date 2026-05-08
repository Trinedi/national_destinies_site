---
priority_starters:
  - tag: POR
    note: "Portugal owns Tomar at game start. Form a marriage of convenience or a quick war with Aragon for Peniscola, hit 50 percent of south Portugal plus Valencia plus Aragon, and the Templar Convent is yours. Strongest fit for the New Order of Christ path (Atlantic mandate, Sagres, sail-cross)."
  - tag: ARA
    note: "Aragon already owns Peniscola and Monzon. The Tomar half is the work: take it from POR by war or alliance. Strong fit for either formation choice; geographically anchored on Valencia and Aragon, the eastern half of the formable."
  - tag: CAS
    note: "Castile. Catholic Iberian, eligible by culture group. No starting cores in either Tomar or Peniscola/Monzon, but well placed to bully both POR and ARA into giving them up. Long-form imperial run; you become Templar Iberia rather than Castilian Iberia."
  - tag: KNI
    note: "Already a sovereign military order under `military_order_reform`, so the second OR branch in `potential` accepts you directly. Geographically extreme (you start on Rhodes and need Tomar plus Peniscola or Monzon in Iberia). Only viable as a long alt-history pivot or via subjects."
hide_auto: true
---

## Concept

The Knights of the Temple is the alt-history Templar successor that
refused the dissolution of 1312. The historical Order of Christ
(Portugal, 1319) and Order of Montesa (Aragon, 1317) preserved
fragments of Templar property and ritual; the mod merges those
fragments back into a single sovereign brotherhood with the eight-pointed
cross intact and the Castelo dos Templarios at Tomar as its capital.

The fantasy is a state that is half military order, half medieval
banking house, and half Atlantic exploration corporation: the bills
of exchange, the secret chapter, the Sagres navigation school, and
the cross-on-sail of Vasco da Gama, all institutionally unified
under the Pauperes Commilitones Christi rather than scattered across
royal patronage.

The tag is TKT because vanilla EU5 already uses TEM and TPL elsewhere.

## Forming it

The formable accepts Catholic Iberian, French, or British culture
groups, plus any country running `military_order_reform`.

1. **Be Catholic.** The `potential` requires `religion:catholic`.
2. **Be in an eligible culture group** (Iberian, French, or British)
   or already running the military order reform.
3. **Own Tomar.** The convent at Tomar (Castelo dos Templarios) is
   the institutional anchor. POR starts with it.
4. **Own either Peniscola or Monzon.** Both are Aragonese castles
   with documented Templar history. Either satisfies the second
   `allow` clause.
5. **Hit 50 percent of south Portugal plus Valencia plus Aragon.**
   The fraction pool is the three areas combined; you need half of
   the locations.
6. **Form TKT.** It is Level 3 plausible.

POR direct path: form alliances, push to take Peniscola or Monzon,
hold half the area pool. ARA direct path: push west into Portugal
for Tomar. CAS or a French/British starter: a longer Iberian
campaign that ends with the Templar Convent rather than a national
crown.

## Pick your founding doctrine on formation

The formation event offers two 30-year doctrines. Each swings a
societal value and gates one of the destiny paths.

- **The Old Order Restored** (Bernard's Rule, the secret chapter,
  the Beausant raised). The pre-1312 Templars refounded as they
  were: bills of exchange, gnostic chapter rituals, brother-knight
  commanderies. Pushes traditionalist_vs_innovative hard left.
  Gates the Continental Commanderies destiny path (Path A, Shadow
  Empire line).
- **The New Order of Christ** (cross-of-Christ on the sail, Atlantic
  mandate, papal reform). The Henry-the-Navigator framing: papal
  sanction, Atlantic factories, the sail-cross of the Carreira da
  India. Pushes land_vs_naval hard right (toward naval). Gates the
  Atlantic Islands destiny path (Path B, Atlantic Imperium line).

## What happens on formation

- Mild stability bonus.
- Country rank rises to Kingdom if currently Duchy or below.
- The `clergy_military_orders` privilege is granted to the Clergy
  estate, unlocking `military_order_reform` in the Government UI.
- The permanent `nd_tkt_militant_brotherhood` modifier (Sovereign
  Order of the Temple) is applied immediately.
- Formation event fires with the two doctrine choices.

## After forming

Tier 1 heritage covers the foundational Templar identity: the Tomar
Convent, the bills of exchange, the Sagres navigation school, the
secret chapter, the Beausant gonfanon, the Atlantic factories, the
Baphomet rumours, the Templar carrack, the Cartulary of Tomar. Each
comes with a DHE and a 15-year modifier choice.

The destiny tree splits two ways:

- **Path A: Shadow Empire.** Continental banking-and-court
  penetration. Build commanderies at Avignon and Troyes, penetrate
  the European courts as their treasurers, then the Shadow Empire
  capstone (London, Rome, Lyon, gold and prestige reserves). Capstone
  building is the **Grand Chapter**. Unlocked by the Old Order
  Restored formation choice.
- **Path B: Atlantic Imperium.** Atlantic exploration and trade
  empire. Take the Atlantic islands (Funchal, Ponta Delgada,
  Teguise), build African outposts (West African factor circuit),
  then the Atlantic Imperium capstone (Sao Tome, Maxorata,
  manufactories, capital sugar market). Capstone building is the
  **Atlantic Captain General**. Unlocked by the New Order of Christ
  formation choice.

## Notes

- The two formation modifiers run for 30 years (longer than HOS's 20),
  reflecting that TKT is one tier higher (Level 3 vs Level 2).
- The destiny paths are deliberately divergent: Shadow Empire
  rewards continental conquest and accumulated gold, Atlantic
  Imperium rewards overseas exploration and the manufactories
  institution. Pick the formation choice that matches your campaign,
  not the prettier modifier sheet.
- TKT pairs thematically with HOS as the two sovereign military-
  religious orders. HOS is Mediterranean-galley-medical; TKT is
  Atlantic-banker-explorer.
