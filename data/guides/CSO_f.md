---
priority_starters:
  - tag: CSO
    note: "The tag is itself a Red Turban Rebellion spawn. CSO represents Han Lin'er's faction, which claimed Song descent. When the situation fires, CSO releases somewhere along the Yangtze. Wait for the rebellions to end, hold Hangzhou, then form."
  - tag: MNG
    note: "Ming. The other big RTR spawn (Zhu Yuanzhang). Jianghuai-cultured, sanjiao, often the strongest faction by late rebellion. Conquer south to Hangzhou after the situation closes and form Sòng instead of Da Ming."
  - tag: WUU
    note: "Wu, the Yangtze delta faction (Zhang Shide). Wu-cultured, starts close to Hangzhou and is geographically the most natural Sòng successor. Smaller than Ming but already on top of the required location."
  - tag: CHE
    note: "Chen Yuliang's Chu-culture faction in the middle Yangtze. Less natural than Wu but a strong inland base if you want to push east into Hangzhou after the rebellions wind down."
hide_auto: true
---

## Concept

Sòng is the southern alternative to vanilla CHI (Yuan) and to MNG
(Ming). The fantasy is the Southern Song restored at Hangzhou: a
maritime, mercantile, Neo-Confucian empire built on paper money,
movable type, paddle-wheel warships, and the wen-wu civilian-over-
military settlement. The historical reference is the 1127 to 1279
Southern Song peak, before the Mongol conquest.

The tag is CSO (not SNG) because vanilla EU5 already uses SNG
elsewhere. In the 1337 setup it is one of the Red Turban Rebellion
release tags, named for Han Lin'er, whose faction claimed Song
descent. Forming it is a restoration, not a release.

## Forming it

The formation is gated by the Red Turban Rebellions situation. You
cannot form CSO while that situation is still active, so the entire
run is built around the post-rebellion settlement.

1. **Pick a Chinese-group tag.** CSO is open to any culture in
   chinese_group. CHI (Yuan) is excluded by name; everyone else
   qualifies. The cleanest starter is CSO itself, released as a
   Red Turban faction. MNG and WUU are the strongest siblings.
2. **Survive or end the Red Turban Rebellions.** The formable's
   `allow` block requires `is_situation_active = no` for the
   rebellions. Either ride out the situation or finish it (one
   faction unifying southern China or the Yuan reasserting control
   ends it).
3. **Own Hangzhou.** This is the only named location requirement.
   Hangzhou starts under CHI and is one of the most contested cities
   of the rebellion period.
4. **Hold 55 percent of southern China.** The `areas` pool covers
   Fujian, Hunan, Hubei, Jiangxi, Jiangnan, Huai, Zhejiang,
   Guangdong, Guangxi, Liangjiang, Guizhou, Hainan, and the three
   Sichuan basin areas. Standard Southern Song reach.
5. **Form Sòng.**

## Pick your founding doctrine on formation

Two 30-year doctrines:

- **Treasure of the Southern Seas.** The maritime Song. Paddle-wheel
  warships, Hangzhou trade junks, the Quanzhou and Guangzhou ports
  as engines of empire. Pushes the country toward naval and
  plutocratic societal values. Unlocks the Treasure Fleets destiny
  path.
- **Mandate of the Brush.** The Neo-Confucian Song. Examination
  bureaucracy, civilian supremacy over generals, Zhu Xi's synthesis
  as the orthodox curriculum. Pushes traditionalist and centralized.
  Unlocks the Mandate Restored destiny path.

## What happens on formation

- Capital moves to Hangzhou.
- Country rank rises to Kingdom if below it.
- Mild stability bonus.
- Formation event fires with the two doctrine choices.

## After forming

The destiny tree splits two ways:

- **Treasure Fleets.** Path A. Build the maritime commercial empire.
  Stage gates require Jinjiang and Longxi (the Fujian coast), then
  Malacca and Palembang (Nanyang choke points), then Kozhikode,
  Hormuz, and Temasek (Indian Ocean and the Strait of Singapore).
  Capstone building is the Treasure Fleet Harbor. Unlocked by the
  Treasure of the Southern Seas formation choice.
- **The Mandate Restored.** Path B. Recover the lost north and
  perfect Confucian governance. Stage gates require Banking embraced
  and 10,000 development, then Kaifeng and Luoyang (the Northern
  Song capitals), then Dadu (the Yuan capital, modern Beijing) at
  20,000 development. Capstone building is the Imperial Library.
  Unlocked by the Mandate of the Brush formation choice.

## Notes

- Vanilla content for CSO is light. Almost all Song-flavour systems
  (paddle-wheel ships, fire-lance corps, jiaozi paper money, Bi
  Sheng's movable type, Zhu Xi's academy) come from this mod's
  advance tree.
- The advance tree carries six DHE event chains: Paper Money
  Revolution, Battle of Caishi, Zhu Xi's synthesis, Gunpowder
  Arsenal, Bi Sheng's Movable Type, and the destiny milestone
  events. Most are conditional on the matching advance.
- Jinshi examinations are not on this tree (they belong to the
  Tang). Pair Sòng's Mandate of the Brush with vanilla
  Chinese-orthodoxy advances if you want a deep bureaucratic stack.
