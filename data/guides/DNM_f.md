---
priority_starters:
  - tag: HAB
    note: "Austria itself. The natural path: you already own Vienna, you are the imperial seat, and you are in the best position to absorb Bohemia and Hungary or bring them into personal union. Forming DNM as HAB is the headline historical fantasy."
  - tag: HUN
    note: "Hungary. The underdog path: you are the kingdom that the historical composite monarchy treated as junior partner, and here you flip the script and bring Vienna and Prague under the Crown of Saint Stephen. You start in Buda, so you only need Vienna and either Prague or Bohemia satisfied to qualify."
  - tag: BOH
    note: "Bohemia. The rare path: an electoral kingdom of the Reich that, in this alt-history, absorbs the Austrian heartland and the Hungarian crown. You start in Prague, the hardest path because both Vienna and Buda are major external objectives."
hide_auto: true
---

## Concept

The Danubian Monarchy is the Habsburg dilemma made playable. To the Holy
Roman Emperor the German hegemony and the Danube super-state were
forever mutually exclusive: an emperor bound to the imperial diet, the
electors and the Reichstag could never centralize Austria, Bohemia and
Hungary into one obedient crown. Forming DNM resolves that dilemma the
only way it can be resolved, by rupture. You renounce the imperial
dignity, walk your hereditary, Bohemian and Hungarian lands out of the
Holy Roman Empire, and refound them as a sovereign empire of your own.

The German princes are left to their Reich; you take the Danube. This
is not Austria-Hungary, the dualist compromise that history would only
reach after a century of crisis. It is the centralized multi-ethnic
monarchy the Habsburgs always reached for and never grasped. The
Ausgleich payoff exists in this mod, but only as the compromise
resolution of the Nationalities Question disaster, not as the formable
itself.

## Forming it

The formable accepts Austrian, Hungarian or Bohemian origins. The
**potential** gate is Catholic plus one of: the Habsburg dynasty rules
you, or you are or once were HAB, HUN or BOH.

The **allow** gate is:

1. **Catholic, Kingdom rank or higher.**
2. **Own Vienna.** Always required, the imperial seat of the new realm
   regardless of which crown you started as.
3. **Own your origin crown's capital.** If you started as Austria you
   are already covered by the Vienna requirement; Hungary needs Buda;
   Bohemia needs Prague.
4. **Each constituent crown must be neutralized.** For HAB, HUN and BOH
   individually: you are that crown, that crown no longer exists, that
   crown is your subject, or you are senior in a personal union with
   it. Annexation is not forced. The historical composite monarchy was
   union-based, not absorption-based, and the formable preserves that
   identity.
5. **Hold about half of the Danubian territory pool.** Sixteen areas:
   the Austrian hereditary lands (Lower and Upper Austria, Styria,
   Carinthia, Carniola, Tyrol-Trentino), the Bohemian crown (Bohemia,
   Moravia, Silesia), and the Hungarian crown (Transdanubia, North and
   South Alfold, Slovakia, Transylvania, Croatia, Slavonia).

There is **no date gate**. The pacing comes from the work of unifying
two great powers plus surviving the formation shock.

## What happens on formation

The form effect does several things at once:

- **You leave the Holy Roman Empire.** Every HRE-owned location is
  removed and the country is detached from the imperial international
  organization. This is a deliberate, irreversible rupture.
- **Empire rank is granted.** HRE members are engine-blocked from
  empire rank, so leaving and ranking up happen in the same effect.
- **An origin variable is recorded.** `nd_dnm_origin_hab`,
  `nd_dnm_origin_hun` or `nd_dnm_origin_boh`, so the destiny tree and
  later events can branch on which crown you started as.
- **A 25-year grace variable is set.** `nd_dnm_grace` prevents both
  Disasters from firing in the first quarter-century, so a fresh
  formation is never bricked.
- **The formation event fires with two doctrinal options.** A 45-year
  timed modifier accompanies the choice, and a path variable is set
  for the destiny tree to use.
- **The Reaction of the Reich Situation activates.** See below.

## The two formation paths

| | Antemurale Christianitatis (path_a) | Gesamtmonarchie (path_b) |
|---|---|---|
| Identity | The bulwark of Christendom, the Ottoman frontier as the empire's reason to exist | The centralized total monarchy, three crowns welded into one chancery |
| Strong on | Manpower, levy size, garrison size, land morale, hostile attrition, diplomatic reputation, religious tolerance | Monthly control, cabinet and legislative efficiency, tax efficiency, reduced separatism, assimilation, cultures capacity |
| Cost | A small administrative penalty, the court is tied up on the frontier | A small military penalty, the court can't run the army and the realm at once |
| Destiny continuation | Conquest objectives along the Sava-Drava-Danube line and the Balkans, culminating in the Antemurale Bastion capstone | Institutional thresholds (treasury, total development, embraced institutions, enlightenment), culminating in the Staatskanzlei capstone |
| Disaster routing | Reassertion or fragmentation more likely | Ausgleich compromise reachable, Austria-Hungary payoff |

## The Reaction of the Reich (Situation)

Forming DNM activates a Situation that owns every external consequence
of the rupture. There is no parallel scripted backlash; the Situation
is the externalization, full stop.

- **The Holy Roman Emperor (the new one, after you stepped down) is
  granted `cb_imperial_ban` on you.** A real casus belli, not a flat
  opinion penalty. The Reich can actually go to war over this.
- **You take the `nd_dnm_reich_pariah` modifier**: diplomatic
  reputation -3, improve-relations impact -0.25, diplomatic-annexation
  cost +0.2, monthly prestige -0.1. Bearable, but not nothing.
- **The Reaction is escapable.** A monthly event chain offers a
  reconciliation path. When you accept accommodation, the Situation
  ends, the pariah modifier comes off, and the imperial-ban CB is
  revoked. A conquest player who never reconciles keeps facing the
  threat indefinitely.

## The Nationalities Question (Disaster)

Cannot fire in the first 25 years (the grace period). After that, it
arms when stability falls below zero and either more than a third of
your population is in an untolerated culture, or your control over the
home region is below 50 percent. It is the polyglot-empire crisis: a
ruling house commanding a patchwork of peoples and no single nation.

Three resolutions, set by your event choices during the disaster:

- **Centralized reassertion.** Crush the nationalist leagues once
  control is restored above a snapshot target. Strong central control,
  but lasting estate resentment baked into a permanent modifier.
- **The Ausgleich.** Accept the Compromise. Two co-equal realms under
  one dynasty, the dual monarchy in all but name. This is where the
  "Austria-Hungary" payoff lives in the mod, a permanent positive
  modifier representing the bound-by-consent settlement. Reachable
  cleanly through the Gesamtmonarchie path, or with high stability and
  legitimacy on any path.
- **Fragmentation.** Cede autonomy. A constituent crown actually
  breaks away as a sovereign kingdom (Hungary first, Bohemia as
  fallback), via `create_country_from_location`. Severe stability hit
  plus a thirty-year `Fractured Realm` modifier.

## The Pragmatic Sanction (Disaster)

The challenge to the indivisible inheritance, the War of the Austrian
Succession in spirit. Cannot fire in the first 25 years and requires
that you have researched the `nd_dnm_pragmatic_sanction` heritage
advance, so it only strikes an empire that proclaimed indivisibility
on paper. Triggers when a clear heir is missing or a regency is
ongoing and stability and legitimacy are low.

Two explicit resolutions:

- **Secure the succession.** Reachable via the `nd_dnm.24` event when
  legitimacy is above 50 or there is an heir. The Sanction is
  vindicated, a permanent positive modifier follows.
- **Negotiate terms.** Reachable via `nd_dnm.23`. You cede what must
  be ceded; the Sanction is broken, a thirty-year penalty follows but
  the realm survives.

Both Disasters block while the other is active (`has_any_active_disaster`
gate in `can_start`), so the empire is besieged sequentially, never
auto-piled-on.

## Strategy notes

- **Plan the formation, do not stumble into it.** You will be paying
  the HRE-exit cost, the Reaction Situation cost, and the marginal-
  victor recovery cost on top of each other. Form when you are strong,
  not when you barely qualify.
- **Decide your post-formation diplomacy in advance.** If you intend
  to reconcile with the Reich, the pariah years and the imperial-ban
  CB are temporary. If you intend to defy them, those costs are
  permanent until you destroy the Reich's leadership yourself.
- **The path choice is also a disaster routing.** Gesamtmonarchie
  makes the Ausgleich exit easy to reach later. Antemurale leaves the
  empire more likely to fracture or to need brute reassertion under
  pressure. Pick the path that matches the empire you want to end up
  with.
- **Hungary as origin is the easiest start.** Buda is your capital
  already, you need Vienna and Bohemia neutralized, and the path runs
  through territory you naturally expand into. Austria is the
  thematically default but Hungary is mechanically smoother for many
  campaigns.
- **DNM is terminal.** No further formable inherits it. The bureaucracy
  and destiny potentials all gate on `tag = DNM`, not `has_or_had_tag`,
  because there is no successor crown to preserve options across.
