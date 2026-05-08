---
priority_starters:
  - tag: MNG
    note: "Ming. The Jianghuai-cultured Red Turban spawn that historically reunified China. Best base for the long western push to Kashgar. Wait for the Red Turban Rebellions to end, take Jingzhao (Xi'an), then march west across Gansu to the Tarim Basin."
  - tag: CSO
    note: "Sòng (Han Lin'er's faction). Zhongyuan-cultured, well placed to seize Jingzhao after the rebellions. The Tang and Sòng formables share the same chinese_group culture pool, so a single CSO/MNG run can form whichever you reach the locations for first."
  - tag: CSI
    note: "Li Siqi's Qin-culture faction in Shaanxi. Sits directly on Jingzhao's doorstep. The fastest path to the western half of the requirements, but small and exposed during and after the rebellions."
  - tag: WUU
    note: "Wu, the Yangtze delta faction. Strong economic base, but a longer continental march to Jingzhao and especially Kashgar. Viable if you snowball east China first."
hide_auto: true
---

## Concept

Great Tang revives the Tang dynasty at its mid-eighth-century peak:
Chang'an as a cosmopolitan world-capital, the Anxi Protectorate
ruling the Tarim Basin, the Silk Road as imperial infrastructure,
and a Jinshi examination bureaucracy holding the whole system
together. The historical reference is the Kaiyuan era under Xuanzong,
before the An Lushan rebellion broke Tang reach into Central Asia.

The tag is TGD because vanilla EU5 already uses TNG. The capital
becomes Jingzhao (medieval Xi'an), and the formable explicitly
reaches into Xinjiang via the Kashgar gate, which is what separates
it from forming Sòng or generic vanilla China.

## Forming it

1. **Pick a Chinese-group tag.** TGD is open to any culture in
   chinese_group. There is no exclusion list, but in practice the
   only viable starters are the Red Turban faction tags (MNG, CSO,
   CSI, WUU, etc.) because they are the only Chinese-cultured
   countries that exist at game start. CHI (Yuan) is mongolian_culture
   and cannot form it.
2. **Wait out the Red Turban Rebellions.** The `allow` block
   requires `is_situation_active = no` for the rebellions and
   `in_civil_war = no`. You cannot form during the chaos.
3. **Own Jingzhao.** This is the Tang capital (modern Xi'an), held
   by CHI at start. The eastern half of the formation gate.
4. **Own Kashgar.** Held at start by DGH (the Dughlats, a Mongol
   khanate in the Tarim Basin). This is the western half and the
   reason TGD is harder than Sòng. You must push through the Hexi
   corridor and across the desert to take it.
5. **Hold 50 percent of north China, west China, east China, and
   Xinjiang regions.** The full Tang heartland plus the Tarim Basin.
6. **Form Great Tang.**

## Pick your founding doctrine on formation

Two 40-year doctrines:

- **Restore the Protectorates.** The expansionist Tang. Anxi and
  Beiting recreated, Sogdian merchants and Turkic generals back in
  imperial service, the Silk Road garrisoned end to end. Pushes
  outward and belligerent societal values. Unlocks the Western
  Restoration destiny path.
- **Golden Age of Letters.** The cultural Tang. Hanlin Academy,
  Tang poetry canon, Jinshi examinations as the path to office, the
  Nestorian Stele as the symbol of cosmopolitan tolerance. Pushes
  spiritualist and traditionalist. Unlocks the Cultural Ascendancy
  destiny path.

## What happens on formation

- Capital moves to Jingzhao.
- Country rank rises to Empire if below it.
- Severe stability bonus.
- Formation event fires with the two doctrine choices.

## After forming

The destiny tree splits two ways:

- **Western Restoration.** Path A. Push the Anxi frontier back to
  its eighth-century reach. Stage gates require Samarkand and
  Bukhara (the Sogdian heartland), then Karakorum and Balkh (the
  steppe and Bactrian gates), then Delhi and Baghdad (Tang reach
  beyond historical: a Pax Sinica that overshadows the Caliphate
  and the Sultanate). Capstone building is the Protectorate
  Command. Unlocked by Restore the Protectorates.
- **Cultural Ascendancy.** Path B. Civilizational empire. Stage
  gates require Banking embraced and 16,500 development, then a
  silk-trading capital market with 2,000 gold and 50 prestige, then
  the Scientific Revolution at 33,500 development. Capstone
  building is the Imperial Library. Unlocked by Golden Age of
  Letters.

## Notes

- TGD and CSO share the same chinese_group culture pool and both
  forbid forming during the Red Turban Rebellions. A single Chinese
  reunification run can form whichever you reach the gates for first;
  Sòng is the Yangtze and southern coast formable, Tang is the
  northern heartland plus Xinjiang.
- The Tarim Basin (Kashgar, Khotan, Turfan) is the slowest part of
  the run. Plan the Hexi corridor conquest before you commit to TGD,
  not after.
- The advance tree carries five DHE event chains: Anxi Protectorate
  Restored, Perfecting the Imperial Examination, the Nestorian
  Stele, Modao Infantry, and the Silk Road Renaissance. Most fire
  conditional on the matching advance.
