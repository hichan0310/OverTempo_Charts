# Chronomia full-song design outside the human reference (Opus 5.5)

New files in this directory:

- `full.plan.json`: plan, schemaVersion 1, analysisId `8a57032b3a6f7755f84e`,
  758 entries, sha256 `80336c140b2fd4010179fa12db89fce2bd8a23a22ac4edb70376e1ac8a8833c2`.
- `assemble_full_plan.py`: the authored phrase design (`DESIGN`) plus a
  deterministic assembler. It validates in memory, smoke-compiles in memory, and
  writes the plan only if absent; a re-run verifies byte identity.
- `RATIONALE.md`: this file.

## Model and provenance

- Live runtime metadata: `PI_MODEL=claude-opus-5-5`, provider
  `anthropic-subscription`. Every assistant turn recorded in this session's log
  (task st_01a19669) reports `model: claude-opus-5-5`, `api: claude-sdk-oauth`,
  stopReason `toolUse`; this was re-checked during design and before writing.
  No rate-limit, usage-limit or fallback message occurred. The only GPT string in
  the log is a background memory-reflection record about other conversations.
- Nothing from cancelled task st_01a1959c was reused. The earlier persisted
  `full-design.events.tsv` (different analysisId `4cc22c065efa98c39594`) was
  not used; every selection here was made from the v2 pack in this session.
- Inputs: `full-mix-v2.analysis.json` (1725 selectable union events, 3206
  contributors, 2463 review-only attacks, 26 invalid-energy comparisons), its
  compact TSV, the user's Refined chart (read only), template
  `Chronomia_Normal.4k-speedcoef.json` (sha256 `c323becd...514f`, unchanged
  before and after), HUMAN_REFERENCE.md, OPUS_PROMPT.md, README.md, build.py,
  validate.py.
- No audio was listened to. No new detection, retiming, tolerance change,
  quantization of review-only attacks, pitch import or coefficient edit.
  Timing 227 BPM / offset 0 / no BPM markers and the source acceleration
  settings stay as in the template.

## Splice contract

- The plan has no event with chartMs in [25000, 45000) and no hold crossing
  either boundary. The parent splices the user's Refined geometry there
  unchanged: 180 notes, 14 holds, 145 onset moments, last note at 44802 ms.
- Four human onset moments have no v2 event: 27753, 31189, 39053 and
  40242 ms. They are human-authored exceptions for the parent to carry and
  attribute; this plan neither represents nor "confirms" them.
- Last AI start before the window: FG0270, 24978 ms (bar 23 s10, lane 3), two
  sixteenths before the human [0,2] chord at 25110 ms. First AI start after:
  FG0500, 45066 ms (bar 42 s10, chord [0,3]), four sixteenths after the human
  ending. FG0499 at exactly 45000 ms was left out because it would create a
  3-sixteenth gap after the user's last note.
- Same-lane rules were checked against AI notes plus the exact human notes:
  at least 2 sixteenths between starts, no start inside a hold, and at least 2
  sixteenths between a hold end and the next start in that lane.

## Evidence vocabulary and its limits

- Selectable events sit on the 1/16 grid within 12 ms. Source keys: `upper`
  (Demucs other stem, an upper-stem estimate, never called melody), `drums`,
  `bass`. Each plan `focus` begins with this provenance; events without an
  upper part say "rhythm-section support, not upper".
- Accent strength ("mix rise") is the positive CQT change of the unseparated
  original mix at the event, one method for the whole song. "Mix-confirmed"
  means the mix detector found an attack within 12 ms. Stem-normalized onset
  and rms values are never compared across stems; upper onset values are used
  only to rank nearby upper attacks.
- Sustain evidence for a hold: other-stem CQT bins present right after the start
  attack and right before every later upper attack up to the endpoint, plus
  energy continuity (rmsBefore at those attacks over rmsAfter at the start).
  Bins include harmonics; this indicates sustained energy, not a performed note.
  Such bands are common, so a hold also needs a phrase role and few upper
  re-attacks. Endpoints are selectable time references, not certified releases.
- Section boundaries below are inferred from shifts in mix-rise medians, other-
  stem absolute RMS, drum/bass contributor counts and repeated accent positions.
  They are readings of measurements, not listening.
- Chords are authorial accents; every chord uses one lane per hand.

## Calibration from the user's reference

Measured in the window: the user charted 133 of 149 even-sixteenth v2 events
and 12 of 79 odd ones; 24 of 34 chords sit on all-source co-attacks; median mix
rise is 14.9 at chords, 9.8 at single notes, 2.5 at unused events; onset gaps
are only 1, 2 and 4 sixteenths plus one 16 under a hold. Together with the
user's stated intent (steady flow, two-hand hits on important sounds, holds on
extended sounds) this is the target vocabulary. No reference lane sequence is
copied.

Outcome outside the window: chord rate 0.237 (reference 0.234); median mix rise
14.87 at chords vs 6.48 at singles; 34 of 758 moments on odd sixteenths, all in
measured contiguous figures or the bar-56 dotted figure; every event outside the
reference with mix rise of 14 or more is charted; 594 moments include an upper
part and 164 are rhythm-section only. No 5- or 7-sixteenth gaps occur.

## Phrases

| id | bars | seconds | moments | lane-notes | chords | holds |
|---|---|---|---|---|---|---|
| P01 intro | 3-6 | 3.17-7.14 | 16 | 18 | 2 | 0 |
| P02 intro | 7-10 | 7.40-11.50 | 19 | 20 | 1 | 0 |
| P03 build | 11-14 | 11.63-15.73 | 32 | 40 | 8 | 1 |
| P04 build | 15-18 | 15.86-20.02 | 33 | 37 | 4 | 0 |
| P05 break | 19-20 | 20.09-22.07 | 10 | 14 | 4 | 1 |
| P06 groove | 21-23 | 22.20-24.98 | 22 | 23 | 1 | 0 |
| human reference | 23.12-42.8 | 25.00-45.00 | (parent splice) | | | |
| P07 stabs | 42-46 | 45.07-49.63 | 38 | 47 | 9 | 0 |
| P08 drive | 47-52 | 49.69-55.90 | 49 | 59 | 10 | 0 |
| P09 call/response | 53-59 | 56.03-63.17 | 50 | 63 | 13 | 2 |
| P10 break | 60-66 | 63.44-70.57 | 20 | 24 | 4 | 3 |
| P11 main 2a | 67-75 | 70.84-80.22 | 74 | 91 | 17 | 0 |
| P12 main 2b | 76-83 | 80.35-88.68 | 62 | 82 | 20 | 0 |
| P13 main 2c | 84-90 | 88.81-96.08 | 58 | 73 | 15 | 0 |
| P14 stop + bridge | 91-100 | 96.21-106.72 | 36 | 38 | 2 | 7 |
| P15 build 2 | 101-108 | 106.78-115.11 | 51 | 61 | 10 | 0 |
| P16 climax A | 109-116 | 115.24-123.57 | 63 | 85 | 22 | 0 |
| P17 climax B | 117-121 | 123.70-128.85 | 41 | 55 | 14 | 0 |
| P18 pre-final break | 122-124 | 128.99-131.89 | 15 | 18 | 3 | 1 |
| P19 final section | 125-132 | 132.16-140.49 | 67 | 87 | 20 | 0 |
| P20 ending | 134-135 | 141.67-142.73 | 2 | 3 | 1 | 0 |

Each entry separates what was measured, my provisional musical reading, and the
geometry with why it follows that reading. "sN" is the sixteenth within a bar.

### Bars 0-2: rest
Measured: 34 detector events, but the largest mix rise is 0.73 and other-stem
RMS is about zero. Geometry: nothing charted; the chart starts with the first
substantial attack.

### P01-P02 intro (bars 3-10)
Measured: FG0035 at 3172 ms (upper+bass, rise 17) is the first real attack.
Bars 3-10 have low rise medians (0.9-2.4); upper+drums co-attacks fall on beat
slots in bars 4, 6, 7 and 10; the strongest local upper onsets sit at s0, s6,
s12 and s14 in bars 4 and 8 (onset 1.00 at 4.6 and 8.6).
Reading (provisional): a light beat-level pulse with a recurring push on the
"and" of beat 2; I cannot name the instrument.
Geometry: a closed [1,2] entrance chord, quarter-note taps alternating hands,
the s6 accent on an outer lane, and bar 8 restating bar 4's rhythm with
mirrored hands because the measured accents repeat. Weak bars 5, 7 and 9 thin to
3-4 taps; rests at 3.6-4.0 and 5.4/7.4-s12 cover weak or unselectable attacks.
Strength: positions strong; "statement and restatement" is an inference.

### P03-P04 build (bars 11-18)
Measured: FG0117 at 11630 ms has the largest rise so far (20.5); eighth slots are
fully populated; bar 13 accents at s0/s6/s12 (13, 15, 19; 13.12 upper-only);
bar 14 has contiguous mix-confirmed attacks s8-s11 then accents at s12/s14;
bar 15 has all-source eighths plus drum sixteenths; bar 18 s12-s15 contiguous.
Reading: the groove thickens to steady eighths, and the 0-6-12 accent grouping
already hinted in the intro becomes the build's signature.
Geometry: alternating-hand eighths; the opening accent held 4 sixteenths (band
69, no upper re-attack); 0-6-12 chords in bar 13; an ascending stair into
[0,2]/[1,3] paired jumps in bar 14; bar 15 kept straight so the drum odd
sixteenths do not stack a second run; 17.8 chord labelled a bass+drums accent
(rise 13); a descending pickup stair 18.12-15 into the bar-19 chord.

### P05 break (bars 19-20)
Measured: only 2 drum contributors in bar 19; hits at 19.0, 19.6, 20.2, 20.8
(12, 15, 15, 17); from FG0226 (20485 ms) to FG0232 (21278 ms) no upper re-attack
for 12 sixteenths, band 50-52 persists, continuity 1.13.
Reading: stop-time hits over a sustained upper layer.
Geometry: chords on the hits; the right hand holds lane 3 from 19.6 to 20.2
while the left hand taps the bass support at 19.8 and 20.0. FG0238 (20.13,
rise 7.7) is omitted because it would form a 3+1 figure; see review gaps.

### P06 groove into the reference (bars 21-23.10)
Measured: bass-only attacks (rise 10-17) on every beat, upper(+bass) attacks
(rise 6-10) on every offbeat.
Reading: an interlock of bass beats and upper offbeats, the texture the
reference continues.
Geometry: left hand on beats (lanes 0/1), right hand on offbeats (2/3), one
opening chord. The hand split is my authorial mapping of the two measured roles,
not a pitch claim. The last note (lane 3) avoids lanes 0 and 2 of the user's
first chord.

### P07 accent stabs (bars 42.10-46)
Measured: FG0500 (upper+drums, rise 15, upper onset 1.00); E-level accents at
43.6 (20, upper-only), 44.2 (21, upper-only), 45.0 (26), 45.6 (20), 45.12 (28,
bass); bars 44 and 46 have selectable events on all 16 slots with upper onsets
0.45-1.00.
Reading: the most accented passage so far, with continuous upper sixteenth
activity; the 0-6-12 figure returns at its strongest in bar 45.
Geometry: outer chords on upper-led hits, an inner chord on the bass hit 45.12;
eighth singles between; the continuous sixteenths are charted only as 4-note
coiled turns into the next downbeat (44.12-15 into 45.0, 46.12-15 into 47.0).

### P08 drive (bars 47-52)
Measured: drums+bass on most eighths; beat-3 accents 47.8 (15), 48.8 (13), 49.8
(17), 50.8 (17), 52.8 (14); 48.0 has no selectable event; bar 50 upper onsets
0.93 and 0.77 at s1 and s3.
Reading: a rhythm-section eighth drive with upper accents on beat 3.
Geometry: alternating-hand eighths, chords at s0 and/or s8, one sixteenth bounce
50.0-50.4 where the upper's odd attacks are locally strong.

### P09 syncopated call/response (bars 53-59)
Measured: other-stem RMS drops to about 0.08; A-bars (54, 56, 58) accent s0 and
s6 (54.6 E22, 54.14 drums+bass E21); B-bars (55, 57) have a contiguous s0-s4
figure into a C-level s4 accent and another at s10; in bar 55 there is no
selectable event at s6-s9 (the mix attacks at s6 and s8 are unselectable); band
74 persists s4 to s10 in both B-bars; bar 56's strongest second-half attacks are
s9/s12/s15 (B-level, drum-weighted, upper onset 0.19-0.29); bar 59 opens with a
drums-only E25 hit.
Reading: a two-bar call and response between syncopated hits and a
flurry-plus-sustain gesture; bar 56 carries a dotted cross-rhythm.
Geometry: chords on A-bar hits; B-bars use a hand-alternating zig-zag flurry
into a held chord released at the s10 hit; bar 56 charts the dotted chain
(open choice 2); bar 59's closing chord is labelled rhythm-section support.

### P10 break (bars 60-66)
Measured: rise medians 0.26-1.9; selectable upper accents in bars 60-61 sit
exactly at s0/s6/s12 (onset 1.00 at s6); bar 64 other-stem RMS 0.032 after a
drums+bass hit; hits at 65.0 (E20), 65.8 (C12), 66.0 (B8); bands persist
65.8 to 66.0 and 66.0 to 66.8.
Reading: a breakdown: dotted call, drop-out, then ringing half-bar hits.
Geometry: taps on 0-6-12 (bar 61 adds a weak-evidence hold); quiet taps at
0/8/12/14 in bars 62-63; bar 64 one chord and a full-bar rest; bars 65-66 hit
chords whose holds bridge to the next hit.

### P11 main 2a (bars 67-75)
Measured: 67.0 bass E22, then the bass-beat/upper-offbeat texture of P06; accent
profiles recur at a 4-bar distance (68 and 72 strongest at s0/s12; 69 and 73 at
s10 D16; 70 and 74 hits at s2/s4/s8/s12); bar 74 has contiguous upper sixteenths
s7-s15.
Reading: an 8-bar phrase made of two matching 4-bar halves.
Geometry: interlock entry in bar 67; half-bar chords in 68/72; s4/s10 chords
in 69/73; quarter "hammer" chords in 70 and a lighter version in 74; an ascending
stair 74.12-15 closes the phrase. Matching bars get matching chord positions
with different lanes, because the measured accents repeat.

### P12 main 2b (bars 76-83)
Measured: 0-6-12 accents in 76, 77, 79 and 80 with upper onset 1.00 at s6 in
77-80; 78.0 is weak and 78.2/78.12 are strongest; bars 81-83 peak at s4/s12
(81.4 D18 bass, 82.12 D19, 83.12 D17).
Reading: the dotted accent figure settles into a sustained groove, then gives way
to a backbeat.
Geometry: a repeating jump-pair cell ([0,2] on s0, [1,3] on s6, [0,2] on s12,
interlocking singles), a varied bar 78, then backbeat chords on s4/s12.

### P13 main 2c (bars 84-90)
Measured: bass contributors fall to 3-4 per bar in 84, 86 and 88; upper-only C10
accents at 84.4 and 84.12; bar 86 selectable on all 16 slots (86.2 onset 1.00,
86.3 0.89); bar 88 contiguous s8-s12; 89.10 and 90.8 missing.
Reading: lighter low end with upper and drums in front; "in front" is an
estimate from stem separation.
Geometry: eighth flow; a roll-back flurry after the 86.0 chord; paired jumps at
86.12/86.14; a descending stair 88.8-11 into a [1,3] chord.

### P14 stop and bridge (bars 91-100)
Measured: 91.0 D15 then weak events with band 74 to 91.8; bar 92 has no
selectable event at s6-s11 (a stop) and 92.12 has upper onset 1.00; bars 93-100
have rise medians 1.9-2.8 with many weak drum attacks; upper attacks cluster at
s0 and s10-s14; 97.0 has a mix attack but no selectable event; bar 100 is
contiguous from s10 to s15 into 101.0 (E20).
Reading: a low-energy bridge with sustained upper texture and light percussion.
Geometry: a held decay 91.0-91.8, the measured 12-sixteenth stop, then each
bridge bar as a downbeat (often held) plus a short s10-s14 answer; bar 97 starts
at 97.6, giving an 8-sixteenth breath instead of a 6-sixteenth wait; a riser
turn 100.12-15 lands on the bar-101 chord.

### P15 build 2 (bars 101-108)
Measured: 101.0 E20; accent density rises through 106; bar 106 contiguous
s8-s11 into 106.12 (drums+bass D17); bar 107 is selectable only at s0/s6/s12
(other slots mix-only); bar 108 weak until upper pickups at 108.12 (onset 1.00)
and 108.14.
Reading: a second build that mirrors the first, then a lull before the climax.
Geometry: chords grow from one per bar to paired accents; a descending stair
106.8-11 into [1,3] answers bar 14's ascending stair; 0-6-12 in bar 107; a
16-sixteenth rest 107.12-108.12; two pickups into 109.0.

### P16-P17 climax (bars 109-121)
Measured: 109.0 bass E21; all-source eighths with D-level rises on most beats;
continuous upper odd-sixteenth ornaments; 113.8, 116.8 and 118.0 missing;
119.0-119.4 contiguous; 121 accents at s0/s6/s12.
Reading: a four-on-the-floor climax with continuous upper figuration.
Geometry: half-bar beat chords; four-beat chord bars 110, 114 and 120, where all
four beats measure D-level; a pickup run 112.12-14; a flurry into 119.4; paired
jumps 118.12/118.14; 0-6-12 chords in 121. Most upper sixteenths stay uncharted
so the density remains below the user's own peak.

### P18 pre-final break (bars 122-124)
Measured: bar 122 drums+bass D15 beats; bar 123 strong only at s0/s6/s12;
FG1525 at 131101 ms (124.0) is the largest mix rise in the song (30.5); band
52-54/65 persists to 124.8 (E20) with continuity 0.96.
Geometry: beat singles with one chord; 0-6-12 taps; the biggest hit held on the
right hand and released at the second hit, then two drum taps.

### P19 final section (bars 125-132)
Measured: upper+drums dominate; strong offbeat accents 126.2 (D18), 128.6
(D18), 129.14 (D17), 130.10 (D16); 0-6-12 accents in 125 and 131; bar 132
selectable on every slot through s14.
Reading: a final restatement built on syncopation and the dotted figure.
Geometry: an outer-chord 0-6-12 statement (125) answered by inner chords (127);
offbeat accent chords; a flurry into 129.4; four chords in bar 130 (s0, s4, s10,
s12); a V-shaped 7-note run 132.8-14 into the stop.

### P20 ending (bars 133-141)
Measured: bar 133 is weak (median rise 0.89); 134.0 FG1643 (E24) is the final
hit, but its energy decays (continuity 0.31 to 135.0, 0.47 to 134.12), so no
hold is supported; 135.0 FG1653 is the last mix-confirmed upper attack (rise 4);
after 136.0 no rise exceeds 0.73; invalid-energy comparisons start at 146.8 s.
Geometry: rest through bar 133, final [0,3] chord, one last tap at 135.0,
nothing after.

## Holds

Grades: strong = no upper re-attack inside and continuity at least 0.65;
moderate = at most two re-attacks and continuity at least 0.7; weak = the rest.

| # | start -> end | ms | lane | sixteenths | band | inner upper | continuity | grade | role |
|---|---|---|---|---|---|---|---|---|---|
| 1 | FG0117 -> FG0120 | 11630-11894 | 0 | 4 | 69 | 0 | 0.78 | strong | bar-11 opening accent |
| 2 | FG0226 -> FG0232 | 20485-21278 | 3 | 12 | 50-52 | 0 | 1.13 | strong | break sustain over bass taps |
| 3 | FG0666 -> FG0668 | 58414-58811 | 2 | 6 | 74 | 0 | 0.70 | strong | covers the bar-55 stop |
| 4 | FG0688 -> FG0692 | 60529-60925 | 3 | 6 | 74, 75 | 1 | 0.75 | moderate | bar-57 B-bar sustain |
| 5 | FG0732 -> FG0736 | 64890-65286 | 3 | 6 | 56, 73 | 0 | 0.50 | weak | bar-61 answer |
| 6 | FG0777 -> FG0781 | 69251-69780 | 2 | 8 | 56-58, 69, 70 | 0 | 0.65 | strong | 65.8 hit rings to 66.0 |
| 7 | FG0781 -> FG0785 | 69780-70308 | 1 | 8 | 62, 73-75 | 1 | 0.80 | moderate | 66.0 hit; endpoint drums-only |
| 8 | FG1113 -> FG1121 | 96211-96740 | 3 | 8 | 74 | 5 | 0.76 | weak | bar-91 decay; soft re-attacks; endpoint bass-only |
| 9 | FG1134 -> FG1140 | 98326-98987 | 2 | 10 | 74 | 1 | 0.57 | weak | bar-93 hit to the next upper attack |
| 10 | FG1149 -> FG1156 | 99648-100176 | 3 | 8 | 48 | 1 | 0.85 | moderate | bar-94 bridge sustain |
| 11 | FG1159 -> FG1164 | 100441-100837 | 2 | 6 | 74 | 1 | 0.73 | moderate | bar-95 downbeat |
| 12 | FG1191 -> FG1195 | 102952-103216 | 3 | 4 | 61, 62, 74 | 1 | 0.85 | moderate | bar-97 entry |
| 13 | FG1205 -> FG1208 | 104009-104405 | 1 | 6 | 55 | 1 | 1.05 | moderate | bar 98; endpoint drums+bass |
| 14 | FG1223 -> FG1229 | 105859-106388 | 3 | 8 | 74 | 1 | 0.76 | moderate | bar-100 riser |
| 15 | FG1525 -> FG1529 | 131101-131630 | 3 | 8 | 52-54, 65 | 2 | 0.96 | moderate | the song's biggest hit |

Four strong, eight moderate, three weak. Band 74 recurs in several unrelated
passages; it may be a harmonic or a pad component, so it does not identify one
voice.

## Rests and gaps other than 1, 2 and 4 sixteenths

- 3 (x3): the bar-56 dotted chain. Open choice 2.
- 6 (x9): held stop at 55.4; dotted 0-6-12 bars 60, 61 (one held), 107 and 123.
  Open choice 1.
- 8 (x13): weak intro bars 5 and 7; the bar-19 hold; break bars 62-66; bridge
  holds in 94, 99 and 100; 96.14 to 97.6 (no selectable 97.0); the bar-124 hold.
- 10 (x3): intro entrance breath 3.6-4.0; holds at 93.0 and 98.6.
- 12 (x2): the measured stop 92.0-92.12; 95.0 hold then rest.
- 16 (x4): drop-out bar 64; bar-91 decay into the stop; pre-climax rest
  107.12-108.12; final decay 134.0-135.0.
- 18 (x1): the stop in bar 133 before the final hit.

## Open choices for the user's ear

These need a listener. I kept the measured reading and name the alternative
instead of guessing.

1. Dotted-quarter waits in sparse bars. Bars 60 (FG0719, FG0722, FG0726), 61
   (FG0729, FG0732 held, FG0736), 107 (FG1314, FG1317, FG1322) and 123 (FG1515,
   FG1520, FG1524) chart only the measured s0/s6/s12 attacks, leaving
   6-sixteenth waits. If these sound unclear rather than like a deliberate
   3+3+2 figure, chart only s0 and s12 there.
2. Bar 56 dotted chain FG0676, FG0678, FG0681, FG0683 (s6-s9-s12-s15,
   3-sixteenth spacing). It follows the strongest second-half attacks, but they
   are drum-weighted. The alternative is to drop s9 and s15 and keep s6 and s12.
3. The last tap FG1653 at 142731 ms after the final hit. Keep it if the last
   upper attack is audible as a tail note; otherwise end on the FG1643 chord.
4. Density at 2x: four-chord bars 110, 114, 120 and 130 and the 7-note run
   132.8-14. AI-part peak is 13 NPS at 1x (validator estimate 25 at 2x, advisory
   threshold 22); the user's own reference peaks at 15 (28 at 2x).
5. Weak holds 5, 8 and 9 above may be better as taps.

## Review gaps

- Downbeats with a mix attack but no selectable event: 48.0, 97.0 (unsnapped mix
  attack at 102539 ms), 118.0. No attack was invented; phrases resume on the
  next selectable event.
- Bar 55 s6-s9 mix attacks are unselectable; the stop is covered by hold 3.
- FG0238 (20.13, all sources, rise 7.7) was omitted to avoid a 3+1 figure.
- 2463 review-only attacks remain unselectable and unused. Bars 0-2 and
  everything after 135.0 contain only weak detector events or the
  invalid-energy tail and stay empty.
- Upper attributions are stem estimates; no claim is made about melody,
  foreground voice or pitch. Lane choices encode hand roles and accents, not
  pitch order.

## Validation (in memory; no chart written)

- `python3 -I assemble_full_plan.py` (py_compile clean) validated membership,
  the window exclusion, hold endpoints and boundaries, invalid-energy exclusion,
  one-lane-per-hand chords, same-lane spacing against the human notes, and
  non-empty hold bands. The plan round-trips as JSON.
- `compile_chart(analysis, plan, template)` in memory is valid: 938 notes, 15
  holds, 758 moments, chord rate 0.237, lanes 232/236/235/235, peak 13 NPS
  at 1x. Template `timing`, `autoCoef` and `specialNotes` are preserved.
  Warnings: 2x density advisory; 2463 review attacks excluded.
- AI notes plus the exact human notes evaluated together are valid: 1118 notes,
  29 holds, 903 moments, chord rate 0.237, lanes 276/286/280/276, peak
  15 NPS at 1x (the human reference's own peak).

## Limits

No listening, no editor or visual inspection of this plan, and no playtest.
Separation, detector and band evidence are estimates. Acceleration work remains
deferred. A skilled 4K player must judge feel and difficulty.
