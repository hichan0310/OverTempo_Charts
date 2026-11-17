# Quarter-beat refinement of the reviewed 169-note excerpt

The user reviewed `Chronomia_AI_Upper_Rhythm_Holds_25-45.4k-speedcoef.json`
and found it substantially improved, but too many unnecessary within-beat 1/4
and 3/4 articulations obscured the groove. Some such articulations must remain.
This is selective refinement, not replacement by the superseded 80-event audit.

Output: `Chronomia_AI_Upper_Rhythm_Holds_25-45_Refined.4k-speedcoef.json`.
The reviewed 169-note baseline is unchanged.

## Result

- 169 -> 146 notes; 135 -> 112 attack moments.
- Within-beat sub1/sub3 starts: 29 -> 6.
- Holds: 6 -> 4. Chord moments: all 32 preserved.
- All 146 surviving note records are exactly equal to their baseline records.
  No new attack, lane change, retiming, shifted hold release or coefficient edit.
- Original timing, special notes, acceleration and all other non-editor source
  settings are unchanged. BPM 227, offset 0, subdivision 4 remain fixed.
- Structural validator: valid, no errors or warnings; 146 starts and four hold
  endpoints checked, no off-grid positions or overlaps.
- The baseline's 213 source-specific review entries remain unselectable.

## Kept odd-sixteenth figures

- CE0053 / CE0055: internal steps of CE0052-CE0055's four-step drum fill into
  the CE0056 landing. Measured mix attacks and visible narrow stripes support
  the complete figure, rather than isolated ornaments.
- CE0147 / CE0149 / CE0152: internal steps and turn of the bar-36 sweep,
  preserving its sub0/sub2 neighbours. Existing mix attacks support a connected
  articulation and the existing source spectrum shows rising ridges.
- CE0167: retained as one pickup into the bar-38 anchor. It has a measured mix
  attack and a clear following beat. Keeping this pickup is an authorial choice,
  not a claim of listening or a certified melodic voice.

## Removed starts

- Isolated or irregular blips: CE0005, CE0012, CE0032, CE0072, CE0087.
- Unsupported or rhythmically weak approaches/pickups: CE0076, CE0078, CE0092,
  CE0098, CE0128, CE0142, CE0223. The block landings and existing main pulse stay.
- The scattered sub1/sub3 string around bar 35: CE0132, CE0134, CE0136. It
  straddled a stronger uncharted accent rather than forming a coherent figure.
  No replacement accent was inserted in this deletion-only refinement.
- Disconnected build-up picks: CE0158, CE0163, CE0172, CE0173.
- CE0186's weak middle stair step and CE0219's ornament after the stab.
- CE0118 / H6: a stem-spectral re-strike without a stable mix attack.
- CE0104 / H5: the uncertain low-band hold head immediately after the bar-33
  downbeat. Its whole hold is removed instead of moving its head or extending
  another hold. H1-H4 remain unchanged.

## Evidence and limits

The Opus 5.5 audit supplied 22 removal recommendations, five keeps and two
uncertain entries. The parent removed the uncertain H5 to prioritize the user's
groove-clarity request, and retained the mix-backed CE0167 pickup. The decisions
use phrase/run roles and original-mix evidence, not blanket removal by grid slot
or an arbitrary density target.

No audio listening was performed. The user has not yet reviewed this 146-note
refinement. Spectral/detector evidence remains estimated; the remaining 213
reviews are not silently resolved.

The original temporary analysis disappeared at reboot. This deletion-only
derivation uses the already compiled and grid-validated baseline. No fabricated
analysis was created to rerun the compiler. The standalone structural validator
was rerun on every surviving start and hold end; exact-subset preservation was
checked separately. Biome LSP is unavailable; JSON parsing and executable
validation are the available machine checks.

Real editor views at 34.0 and 37.5 seconds were displayed and examined: the two
short right-lane block holds survive, the uncertain left-lane holds are absent,
and the bar-35 scattered sixteenths are removed while the bar-36 run remains.
The paired full-excerpt playback evidence is recorded separately.
