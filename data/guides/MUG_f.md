---
priority_starters:
  - tag: KRT
    note: "Kartids of Herat. Khorasani Sunni, sitting on the historical Timurid eastern frontier. The closest start to Babur's invasion route: Herat to Kabul to Punjab. Geographically the cleanest Mughal run."
  - tag: MZF
    note: "Muzaffarids. Farsi Sunni, the dominant Persian state at game start. A heavier Persian base before pivoting east through the Hindu Kush, with the Iranian-group culture path satisfying the allow."
  - tag: SRB
    note: "Sarbadars. Khorasani, but Shia rather than Sunni; if you keep the Shia religion you still satisfy `religion.group = religion_group:muslim`. Same Khorasan-to-Punjab geographic logic as KRT."
  - tag: CHB
    note: "Chobanids in Azerbaijan. Iranian-group, further west, longer march to Delhi. A more demanding option than KRT or MZF but mechanically valid."
hide_auto: true
---

## Concept

The Mughal Empire revives the Timurid imperial dream on Indian soil. The historical
reference is Babur's 1526 invasion through the Khyber Pass, the foundation of the
empire at Delhi and Agra after the Battle of Panipat, and Akbar's later synthesis
of Hindu and Muslim governance under the doctrine of *sulh-i-kul* (peace with all).
The mod's formation event names this directly: "We shall conquer as Babur conquered"
versus "We shall enlighten as Akbar enlightened."

The formable is mod-replaced (REPLACE block). The form_effect now sets country rank
to Empire if below it, fires the formation event, and grants severe stability. The
vanilla version only set the rank and was otherwise empty.

## Forming it

The `allow` requires the historical Mughal pattern: a Muslim conqueror from
Central Asia or Persia projecting into Hindustan.

1. **Start as a Muslim country with the right culture.** The allow accepts:
   - Iranian-group cultures (Farsi, Khorasani, Tajik, Lur, Mazanderani, Gilak, etc.).
   - Turkic-group cultures (Turkoman, Uzbek, Khorezmian, Azeri, etc.).
   - Any culture whose language is Afghani (Afghan, Pamiri, Ormur). No tag starts
     with these as a primary culture, so this clause matters mainly for cultural
     succession after conquest.
2. **Hold the three Mughal capitals.** The allow demands ownership of **Delhi**,
   **Agra**, and **Lahore**, in addition to the regional fraction. These are the
   historical Mughal heartland and they are not negotiable.
3. **Hold 80 percent of `hindustan_region`.** This is a dramatically higher
   fraction than the New World formables. You are not forming a frontier polity;
   you are conquering the subcontinent's plains.
4. **Form Mughal.** Pick your founding doctrine.

The practical path mirrors Babur's route: secure Khorasan or Persia, push through
the Hindu Kush, take the Punjab (Lahore), then the Yamuna-Ganges plain (Delhi,
Agra), then sweep the wider Hindustan region. KRT starts closest. MZF starts
richer but further west.

## Pick your founding doctrine on formation

Two 40-year modifiers, each tied to a destiny path:

- **We shall conquer as Babur conquered!** Modifier *Sword of Babur*. The
  conqueror's path: gunpowder and cavalry, the Panipat tradition, military
  expansion. Drives the Conqueror destiny line (iron fist, Timurid restoration).
- **We shall enlighten as Akbar enlightened.** Modifier *Light of Akbar*. The
  syncretist path: Sulh-i-Kul, jizya abolition, Hindu officers in the imperial
  service, the Ibadat Khana. Drives the Padshah destiny line (synthesis,
  artisans, world market).

## What happens on formation

- Country rank rises to Empire if below it.
- Severe stability bonus.
- Formation event fires with the two doctrine choices.

## After forming

The destiny tree splits two ways. The **Conqueror** path runs through Deccan and
Bengal subjugation toward a Timurid restoration capstone. The **Padshah** path
runs through Gujarat trade and the imperial workshop toward Golden Age or World
Market. Advance DHEs (Gunpowder Revolution, Sulh-i-Kul, Grand Trunk Road) fire
on matching advance research.

## Notes

- The mod uses REPLACE to layer formation event, severe stability, and rank
  promotion onto the vanilla `level = 4`, `fraction = 0.8` shell. The territorial
  bar is identical to vanilla.
- No `potential` block in the mod's REPLACE either; the gate is entirely in
  `allow`. Anyone who eventually meets the religion, culture, and territory
  requirements can form, regardless of their starting position.
- The three required locations (Delhi, Agra, Lahore) are absolute. Holding 80
  percent of Hindustan without one of these three will not open the form button.
