---
priority_starters:
  - tag: KNI
    note: "The Knights Hospitaller themselves. Already Catholic, already a military order, already on Rhodes. The cleanest run: hold what you have, take Malta and Cyprus, and the formable's 90 percent fraction is almost in your pocket on day one."
  - tag: CYP
    note: "Cyprus. Catholic Lusignan kingdom adjacent to Rhodes. Conquer Rhodes from KNI (or wait for the Ottomans to push them out and pick up the pieces) to satisfy the allow gate, then unify the eastern Mediterranean as a single Hospitalier realm."
  - tag: SIC
    note: "Sicily. Catholic, owns the Sicilian shore so Malta is a short hop. The Maltese path: take Malta, then push east into Rhodes for the second half of the Hospitalier provinces. Best fit for the Hospitalier Realm option (naval, hospital, corso)."
  - tag: NAP
    note: "Naples. Catholic Mezzogiorno, similar geographic angle to SIC but bigger and bulkier. Realistic if you can take Malta early and project east."
hide_auto: true
---

## Concept

The Sovereign Order of Saint John refounds the Knights Hospitaller as a
proper sovereign state rather than a wandering crusader brotherhood.
The historical reference is the Order's transition through Rhodes
(1310 to 1522) and Malta (1530 to 1798): a Catholic religious-military
corporation that became, in practice, an island kingdom with its own
fleet, hospital system, and licensed corsairs.

The mod treats HOS as the institutional answer to "what if the Order
never lost Rhodes, never had to beg Charles V for Malta, and instead
consolidated as a permanent Mediterranean island state." The langues
(Provence, Auvergne, France, Italy, Aragon, Castile, Germany, England)
become a confederal civil service. The Sacra Infermeria of Malta
becomes the imperial hospital. The Tribunale degli Armamenti regulates
the corso.

## Forming it

The formable accepts five entry tags: KNI, CYP, NAP, SIC, ARG, plus
anyone running the `military_order_reform` government reform.

1. **Be Catholic.** The `potential` requires `religion:catholic`.
2. **Hold Rhodes or Malta.** The `allow` block needs at least one of
   `location:rodos` or `location:malta`. KNI starts with Rhodes; SIC
   and NAP can take Malta from a coastal raid; CYP and ARG must push
   for Rhodes.
3. **Hit 90 percent of the Hospitalier provinces.** The required
   territory is `rodos_province` plus `cyprus_province` plus the
   `malta` location. With 0.9 fraction this is essentially a
   "hold all three" requirement: the Dodecanese, the island of
   Cyprus, and Malta.
4. **Pick the formable.** It is Level 2 plausible.

The KNI direct path is by far the easiest. CYP is a natural narrative
fit (Cypriot Lusignans absorbing the Rhodes Hospitallers) but requires
a war on Rhodes. SIC and NAP have to grab three separate island chains
that lie far from their core lands.

## Pick your founding doctrine on formation

The formation event offers two 20-year doctrines. Picking one also
swings a societal value and gates which destiny path you can later
take.

- **Crusading Order** (Sword of Christendom). The galleys never rest;
  the Order is what it has always been. Pushes belligerent_vs_conciliatory
  hard left. Gates the Reclaim the Levant destiny path (path A, Mare
  Nostrum line).
- **Hospitalier Realm** (Hospital, harbor, council). Sovereign island
  state; the corso, the Sacra Infermeria, and the langues are the
  institutional core. Pushes land_vs_naval hard right (toward naval).
  Gates the Lazaretto Network destiny path (path B, Sacra Infermeria
  Maxima line).

## What happens on formation

- Mild stability bonus.
- Country rank rises to Kingdom if currently Duchy or below.
- The `clergy_military_orders` privilege is granted to the Clergy
  estate. This unlocks `military_order_reform` in the Government UI
  if you want to formally adopt the reform.
- The permanent `nd_hos_militant_brotherhood` modifier (Sovereign
  Order of Saint John) is applied. Institutional benefits land
  immediately without needing to swap a reform slot.
- Formation event fires with the two doctrine choices.

## After forming

Tier 1 heritage covers the foundational Order identity: Hospitalier
Tradition, Knights Hospitaller infantry, Squadron of the Order
galleys, the langues system, the Statutes of Rhodes, the Tribunale
degli Armamenti, the Sacra Infermeria, Maltese Bastions, Codice del
Ordine. Each comes with a DHE and a 15-year modifier choice.

The destiny tree splits two ways:

- **Path A: Mare Nostrum.** Conquest line. Reclaim Acre and Tripoli
  (Levant), break the Ottoman Lake (Algiers and Tripoli), then the
  Mare Nostrum capstone (Constantinople, Tunis, Beirut). Capstone
  building is the **Grand Magistery**. Unlocked by the Crusading
  Order formation choice.
- **Path B: Sacra Infermeria Maxima.** Public-health hegemon line.
  Build the Lazaretto Network (banking institution, capital market
  silver), assert Continental Health Authority (Marseille, Genoa,
  Naples), then the Sacra Maxima capstone (manufactories, capital
  silver market). Capstone building is the **Lazaretto Imperial**.
  Unlocked by the Hospitalier Realm formation choice.

## Notes

- KNI starts with `crusade_sea_reform` and several Crusader laws
  already loaded. The HOS form effect grants the `clergy_military_orders`
  privilege rather than locking you into a specific reform, so you
  can keep KNI's existing Government setup or swap in
  `military_order_reform` from the unlocked list.
- The 90 percent fraction means you need almost all three island
  groups. Losing a single Cypriot location to a peace deal can break
  formation eligibility until you take it back.
- HOS pairs thematically with TKT (the Templar successor as Atlantic
  banking-state). Both are sovereign military-religious orders, but
  HOS leans Mediterranean-galley-medical and TKT leans
  Atlantic-banker-explorer.
