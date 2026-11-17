# Chronomia 25-45 s, revision 2: upper rhythm, supporting hand, holds

Plan: opus-revision-2/upper-rhythm-holds-25-45.plan.json (schemaVersion 1, analysisId c84a84257355a2ae2f83).
Canonical plan SHA-256 (sort_keys, compact separators, ensure_ascii=False): ca3d3c5eebfbb3bd293d6b27c2bfbac82acb5f4122685819f540615c6b60a8dc

## Evidence used and its limits
- Data: combined/excerpt.analysis.json and excerpt.events.tsv, using each source's originalEvent features and upperEvidence (spectralChange, positiveChangeMagnitude, before/after/rising bins).
- Plots: combined-source-onsets.png and upper_spectrum_25-45.png. The spectrum was also inspected as enlarged crops of the existing PNG, with the editor bar/beat grid drawn on top. That is image annotation only; no new audio analysis was run.
- Reference editor views (Breaking Dawn 45 s, Luminaria 92 s, Break Through Myself 84 s) were used as geometry only:
  - chord groups interleaved with singles;
  - a held lane while taps continue elsewhere;
  - a held role that moves between lanes.

  No sequence was copied.
- No audio was listened to. Bin numbers are spectral energy coordinates, not performed pitches, and "upper" means the separated other.wav estimate. Each source's onset and band values are compared only within that source.
- Timing is fixed and not overridden: BPM 227, offset 0, no BPM markers, 16th-note grid (subdivision 4), max deviation 12 ms, and the template's acceleration data. The compiler owns chartMs = audioMs + offsetMs.

## What is different from the rejected drafts
This is not the 69-single skeleton with decoration. Each phrase uses two coordinated hand roles:
- a support hand on offbeat co-attacks (simultaneous accepted attacks from separate sources) plus taps labelled as drum or bass roles;
- an upper hand on upper attacks.

Chords mark measured co-attacks, and holds follow sustained upper-stem bands.

The result is 169 notes across 135 attack moments, with 32 chords and 6 holds. 117 of the 135 moments contain an accepted upper attack. The other 18 have no upper part, and each is labelled as a drum or bass role, never as melody.

## Phrase design

### A. 25.11-30.66 s (bars 23.12-28): offbeat co-attack groove
**Evidence:**
- In bars 25-28 all three upper onsets of 1.0 (26828, 28150, 28943) fall on 8th offbeats, together with accepted drum and bass events.
- Six of the seven other upper onsets at or above 0.76 are also offbeat co-attacks with bass and/or drums. The exception, CE0042 on beat 4, starts H1.
- Apart from 26432, 26894 and the bar-28 fill, drum events fall only on offbeats.
- Upper events between the offbeats add further spectral changes: 27225 (.24), 28018 (.22), 28282 (.21) and 29339 (.20).

**Gesture:**
- Lanes 0/1 play the offbeat spine, and lanes 2/3 play the upper line on beats and 16ths.
- Strong offbeat co-attacks become split-hand chords.
- One cell recurs where the evidence recurs: a high stab [1,3] (rising-bin family 79/80) moves to a 72-family stab [0,2] at slots 6 and 10 of bars 25 and 27.
- In bar 26 the measured stab sits at slot 10 (change .34), so the chord moves there rather than following a copied bar template.
- Bar 28 holds lane 3 (H1) while the support hand continues.
- The drums+bass 16th fill (CE0052-CE0055) rolls 0-1-2-3. That direction is a hand-flow choice, because drums carry no pitch evidence. The upper attacks inside the fill are review-only.

### B. 30.66-32.78 s (bars 29-30): section change, held texture, backbeat
**Evidence:**
- CE0056 is a three-source co-attack with upper onset 1.0 and positiveChangeMagnitude 7.75. The spectrum shows a broadband line and new held bands there.
- After it, upper onsets are weak (0.25-0.57) and spectral changes stay below .11. Many upper attacks in these bars are review-only.

**Gesture:**
- The fill lands on a three-note chord [0,1,2], with lane 0 held (H2).
- Meanwhile lanes 2/3 tap the drum events on beats 2 and 4 (30925, 31454; mid/high-dominant within drums) and the offbeat co-attacks.
- The upper 16ths CE0076-CE0078 lead into bar 31 as lanes 2-1-3. This is a contour hypothesis from rising-bin tops 75, 70, 82.

### C. 32.78-34.89 s (bars 31-32): accent bars and 75-band blocks
**Evidence:**
- CE0079 is the upper-only bar-31 downbeat, with the largest upper change in the window before 41 s (.40).
- CE0083 has rising 80/81 at a three-source co-attack.
- In bar 32 the spectrum shows two one-beat bright blocks at bins 75/74/76. Each starts at an upper+drum co-attack: CE0093 (change .36) and CE0099 (.28).

**Gesture:**
- CE0079 gets a phrase-start chord [0,2]. CE0083 repeats the high-stab shape [1,3].
- Each 75 block is approached by an upper 16th on lane 2, giving a recurring cell: approach, then [0,3] with lane 3 held for one beat (H3, H4).
- The other hand keeps an offbeat lane-1 pulse from co-attacks and drum/bass offbeats (32.2, 32.6, 32.10, 32.14).

### D. 34.89-37.00 s (bars 33-34): held low band under the upper texture
**Evidence:** bins 56/57 stay in the before/after bins of every upper event from CE0104 to CE0128. The spectrum shows a bright low band for two bars that brightens again near 36.1 s, and CE0118's top rising bin is 56.

**Gesture:**
- Lane 0 holds that band in two parts, split at the measured re-rise (H5, H6).
- Over it, the upper hand marks the accents at 35286 (84/85, .22), 35683 ([1,3], 80/81, .26), 36608 (82, .19) and 36740 ([1,2], .22).
- The left index takes the upper+drum events on beats 2 and 3.

### E. 37.00-39.12 s (bars 35-36): syncopated upper and rising sweeps
**Evidence:**
- CE0129 marks the bar-35 change. The upper attacks at 35.5, 35.7 and 35.9 fall off the beat.
- CE0139 has upper onset 1.0 with drums and bass.
- In bar 36 the bass source's low-band value is about 0 for its events from 38326 to 39119. That is a bass-source feature, not a claim about the mix. Meanwhile the upper spectrum shows rising diagonal ridges.
- Rising-bin tops go 67, 70, 75 and then add 82/87 across 36.4-36.8, and go 63, 65, 68, 67 across 36.9-36.13.

**Gesture:**
- CE0129 gets [1,3]. The three off-beat 16ths walk 3-2-1, a hand-flow choice. CE0139 takes [0,2].
- The two sweeps are charted as stairs 0-1-2-3 and 0-1-2-1.
- The landing CE0154 [0,2] is a drums+bass downbeat. The upper attack there is review-only.

### F. 39.12-44.93 s (bars 37-42): offbeat stab-chain climax
**Evidence:**
- The window's largest upper changes fall on offbeats, mostly with drums and bass: 42159 (.44), 42423 (.29), 42687 (.39), 42952 (onset 1.0), 43216 (.235), 44009 (.37), 44537 (.40) and 44802 (.32).
- The 43348 downbeat has a change of .38.
- That is phrase A's co-attack relationship with larger upper changes.

**Gesture:**
- Phrase A's stab vocabulary returns, intensified: offbeat chords alternate split shapes, with on-beat upper singles between them (42291, 42819, 43084).
- The [1,2,3] peak chord sits at CE0194.
- The visible rising ridge near 41.4-41.6 s is charted as stair 1-2-3. Its per-event rising-bin tops do not climb monotonically, so this is a textural reading of the visible ridge only.

## Holds
| # | Lane | Start -> end (chart ms) | Length | Sustained role in the evidence | Endpoint basis |
|---|---|---|---|---|---|
| H1 | 3 | CE0042 29339 -> CE0052 30396 | 16 ticks, 1057 ms | Bins 67/68/66 lead the before/after bins of every upper event CE0042-CE0051; continuous band through bar 28 | Gesture release on the first fill event so the hand can roll; the band itself lasts until CE0056 |
| H2 | 0 | CE0056 30661 -> CE0070 31850 | 18 ticks, 1189 ms | After the 30.66 s change, bin 68 (with low 49) stays in the top bins CE0058-CE0067 while upper attacks are weak | Measured: bin 68 is absent from CE0070's before-bins and 65/66/64 rise there |
| H3 | 3 | CE0093 34097 -> CE0096 34361 | 4 ticks, 264 ms | 75/74/76 rise (change .36) and stay on top at CE0094; first one-beat block | Measured: bin 80 rises at CE0096 (change .22) and 75 drops |
| H4 | 3 | CE0099 34626 -> CE0103 34890 | 4 ticks, 264 ms | 75 rises again (.28) and remains at CE0100/CE0102 | 75 is gone by CE0104 (34956); CE0103 is the bar-33 drum downbeat between those measurements |
| H5 | 0 | CE0104 34956 -> CE0116 35947 | 15 ticks, 991 ms | 56/55 rise and persist through bar 33 | Gesture release on the bar-34 drums+bass downbeat, 3 ticks before the measured re-rise at CE0118; the band itself continues |
| H6 | 0 | CE0118 36145 -> CE0129 37004 | 13 ticks, 859 ms | 56 is the top rising bin again (re-articulation) and persists through CE0128 | Measured section change: 56 leaves the after-bins at CE0129 (80/82 rise), and CE0130 shows new low 58/51 bands |

- **The held role alternates hands:** right in bar 28, left in bars 29-30, right in bar 32, left in bars 33-34.
- **No holds in the climax (39-45 s):** no upper band there persists more than about 3 ticks in the before/after bins. CE0194's 68/72 is gone by CE0196, and CE0208's 77 is gone by CE0211.
- **Endpoints:** these are gesture references, not certified acoustic releases.

## Chords
There are 32 chords: 30 two-note and 2 three-note (CE0056 and CE0194). Shapes: [0,2] x12, [1,3] x11, [1,2] x4, [0,3] x3, [0,1,2] x1, [1,2,3] x1.

29 of the 32 sit on accepted co-attacks that include an upper part plus drums and/or bass. The three exceptions:
- CE0079 and CE0129 are upper-only phrase-start downbeats (changes .40 and .22).
- CE0154 is a drums+bass landing after the sweeps.

Shapes reuse recurring rising-bin families where hand flow allows:
- [1,3] for the 79-82 family: CE0017, CE0030, CE0038, CE0083, CE0113, CE0129, CE0171, CE0197, CE0229.
- [0,2] for the 72 family: CE0020, CE0040, CE0178, CE0218, CE0226.
- [1,2] for 69/70: CE0023, CE0190, CE0202.
- [0,3] with a lane-3 hold for the 75 blocks: CE0093, CE0099.

Everywhere else the shape is a hand-flow choice. This is a recurrence device, not a pitch-to-key transcription.

## Review-only upper attacks deliberately not charted
None of these was snapped, retimed or replaced with a different-source event labelled as upper:
- CR-upper-00165 / 00166 (25719 / 25757 ms): plausibly the onset of the band near bin 72 visible from about 25.7 s.
- CR-upper-00208 / 00209 (30441 / 30514): upper attacks inside the drum fill.
- CR-upper-00228 (32232): the upper texture change around 32.25 s. The nearby CE0073 is bass-only and was not charted.
- CR-upper-00247 (34876): bar-33 downbeat. CE0103 is used only as a hold endpoint (drum event).
- CR-upper-00271 (39105): bar-37 downbeat. CE0154 is charted for its drum/bass role only.
- CR-upper-00296 (44382): bar-42 downbeat; not charted.

Human alignment review of these could add upper articulation where this plan leaves rests or drum-role notes.

## Machine checks (in memory; no chart or plan file written by the checker)
- **Custom checks:**
  - 135 unique entries, all selectable CE events (none from reviewRequired).
  - Every start and all 6 endpoints are on subdivision 4 with |deviation| <= 12 ms.
  - Hold lanes are among each entry's lanes, and endpoints come later than starts.
  - Same-lane starts are at least 2 ticks apart (132 ms).
  - No start falls inside a same-lane hold or less than 2 ticks after its release.
- **Project compiler:** Tools/ai-chart/build.compile_chart ran with the project venv, the read-only template and the plan on stdin.
  - valid=true, no errors.
  - 169 notes, 6 holds; checkedNotes 169, checkedHoldEnds 6; no off-grid starts or ends.
  - chordRate 0.237; lanes 0:35 / 1:45 / 2:46 / 3:43; peakNps1x 12, peakNps2xEstimated 22.
  - The only warning was the 213 propagated review entries.
- **Timing and acceleration:** compiled timing equals the template ({bpm 227, offsetMs 0, bpmChanges []}). autoCoef, speedLimitLines and stageDeltaLines are identical to the template.
- **Source integrity:** the template SHA-256 (c323becd...514f) and the analysis SHA-256 were unchanged before and after.
- **Heuristic limits:** the result sits at the validator's limits.
  - 22 notes per 2 s; the validator warns above 22.
  - 31 sub-100 ms adjacencies over 135 moments (0.23); the validator warns above 0.25.
  - A 188-note first pass exceeded both, so support taps and taps without spectral change were removed.
  - These heuristics do not certify playability.

## Uncertainties and QA requests
1. **Bin families:** the rising-bin families could be one part's notes, harmonics or chord partials. The shape reuse expresses recurrence only.
2. **Low bands:** the low 49/56/51 bands in the upper stem may be pad, harmonic content or leakage. H2, H5 and H6 express sustained upper-stem energy, not a certified instrument.
3. **Drum identity:** drum events are described only by their within-drum band profiles. Their instrument identity is unknown.
4. **Offbeat feel:** phrases A and F emphasise 8th offbeats because the measured co-attacks and largest upper changes are there. The bar alignment is supported by:
   - the fill into 30661;
   - changes on bar downbeats at 30661, 32775, 37004 and 43348;
   - mid/high drum events on beats 2/4 in bars 29 and 31.

   Whether the offbeat emphasis feels "pushed" can only be judged in the editor with audio.
5. **Density:** about 8.5 notes/s on average (169 notes in 19.8 s), peaking at 12 per second. By my count of visible notes, that is close to the three reference views (about 8-9.5 notes/s) but heavy for a Normal. Thin first the notes whose focus says "support role" or "drum role".
6. **Hardest moments:** a hold combined with a chord. These are CE0045 under H1, CE0056 starting H2, CE0113 under H5 and CE0125 under H6. Reduce them to singles if the skilled-player review finds them awkward.
7. **Scope:** the window ends mid-phrase at 44934. There is no whole-song extension, difficulty rating, or claim of quality or fun.
