# Chronomia remap study, 2026-10-31

This is a chart-design reference study, not a claim that an OverTempo level is
equivalent to a DJMAX rating. No source chart sequence is transplanted.

## Evidence status after the restart

This document is not a completed music-to-chart study or an approved Chronomia
design. The first pass inspected silent score layouts. It did not establish
which instrument, articulation, mood, or phrase caused an individual placement.
No audio listening is claimed. In the tables below, "voice" in an initial
description means a visually separable lane activity, not an identified sound.

Keep these evidence layers separate:

- A favorable player evaluation establishes that player's opinion of the
  identified mode/difficulty. It does not establish community consensus.
- A rendered score establishes visible attacks, spacing, holds, and lane shapes.
- Composer or player prose can establish an attributed description of the music.
  It does not align that description with a particular score bar automatically.
- A proposed relationship between the two remains a hypothesis until its
  sound-to-note alignment is supported.

The new Opus investigation must address that last gap before chart production.
Do not generate a full-song pattern from fixed eight-bar blocks, RMS alone,
arbitrary chord positions, or a sixteen-slot motif masked by available attacks.
Grid correctness cannot validate musical selection.

## Opus restart: sound-to-shape explanations

The retry ran Claude Opus 5.5 through Claude Code 2.1.314. Its memo is at
`/tmp/rgresearch/evidence_memo.md`. It reports no listening. The parent directly
retrieved and checked the two written sources below; YouTube's plain-text
fetch did not expose the additional video descriptions.

### Directly checked creator account

ValenBoA's DPC2024 retrospective:
<https://gall.dcinside.com/mgallery/board/view/?id=djmaxrespect&no=803502>

- **welcome to the space, 4B SC01, author level 7:** the recurring drum fill
  changes subdivision. The author remembers four 32nds followed by four 24ths,
  and uses a trill followed by a stair to make that distinction physical.
  This is the author's choice, not a universal subdivision rule.
- **Same chart, interlude:** the author selects kick attacks instead of melody
  for a repeated burst. Changing the chosen voice changes the gesture's role.
- **Space Challenger, 5B SC01, author level 10:** descending vocal samples become
  descending placement; low piano occupies sides while melody stays on keys.
  The author explicitly sacrifices some pitch fidelity for the remake's
  symmetry. The 5B shared-center ergonomics do not transfer literally to 4K.

These establish intentional musical correspondence. Favorable contest results
reported in the Opus memo are a separate evidence claim; the author's own post
does not independently establish those ratings.

### Directly checked same-song positive and negative evaluations

KuRo's subjective DPC2026 4B evaluations:
<https://gall.dcinside.com/mgallery/board/view/?id=djmaxrespect&no=2182860>

- **sangsangchum:** #269 is praised for expressing the song's trills and pitch;
  #219 is criticized for pitch mismatch and uneven density.
- **Over Me:** #119 is praised for keysound selection and pitch; #477 is
  criticized for excessive close doubles between otherwise enjoyable figures.
- **Odysseus:** #173 receives praise for preserving the rhythmic character under
  a chord-based texture. Other entries lose approval for excessive close doubles
  or unsuitable imported vocabulary.

These are one player's comparisons, not consensus or independent listening here.
The charts themselves were not inspected in this pass. The useful controlled
comparison holds the song constant: more difficulty or more shapes is not the
distinguishing feature of the preferred version.

### Additional video-source findings, with a narrower verification boundary

Opus retrieved mdcurtis99's descriptions for Lost Temple 4B DPC2024:
<https://www.youtube.com/watch?v=r6R_W_uI5Hc>
and a separate curator's evaluation:
<https://www.youtube.com/watch?v=tTTQ6sJvzZ0>.
It reports effects assigned to fixed outer lanes, alternating pitch represented
by alternating sides, and opposed kick/snare runs represented by opposed
directions. It also reports deliberately visual, nonliteral long-note chords.
These are attributed child-source findings; the parent could not recover the
descriptions through its plain-text fetch. Video positions must not be treated
as verified song times.

Reject two overextensions from the memo:

1. A DJMAX "blank note" lacks an assigned keysound; it can still follow an
   audible vocal or instrument in the backing music. It is not synonymous with
   an unsupported audio attack in OverTempo.
2. MIRROR preserves a directional relationship while reversing its orientation.
   Arbitrary RANDOM does not necessarily preserve contour. No universal
   invariance or literal low-to-high lane mapping is established.

### Consequences for the new Chronomia design

For each real phrase, record the chosen attack layer, recurring rhythmic cell,
pitch/contour evidence when available, rests or sustained material, and the
audible change at its boundary. Then state why an anchor, direction, alternation,
or chord-weight change expresses it. Identify trade-offs separately.

The earlier fixed-block proposal is rejected: numerical onset/RMS averages do
not identify lead voices, exact phrase boundaries, pitch contours, or simultaneous
musical layers. Chords cannot be justified by loudness alone. A timing candidate
list is an input to this decision, not its substitute. Chronomia's actual
voice/phrase attribution remains open; no new chart is approved by this study.

## Chronomia measured-source follow-up

The next pass adds measured source estimates rather than pretending to listen:

- Demucs 4.0.1 `htdemucs`, CUDA, zero random shifts, seven-second segments.
  Float WAV outputs use clamp mode so stems are not independently rescaled.
- Scratch outputs:
  `/tmp/chronomia-sc-study-20261031/stems/htdemucs/4-03 Chronomia/`,
  `full.stems.analysis.json`, and `layers.measured.json`.
- The original audio SHA-256 is
  `d034151fd60a28638eda05894f4313e9f27ef2812d9986c0bb4a71c7023e13fb`.
  Both analyzed chunks reference the same source hash.
- The merged analysis contains 1,226 selectable attacks and 797 excluded review
  attacks. Every selected attack remains on subdivision 4 at BPM 227, offset 0;
  the maximum measured attack/grid difference is 11.989 ms under the 12 ms
  selection threshold. No timing values were adjusted to admit rejected attacks.
- The source chart's first 3,172 ms event is not silently restored: the detected
  peak is 3,157.914 ms, outside that threshold, so it remains a review item.
- Stem-aware analysis leaves both chunks' candidate times unchanged. The later
  chunk extends its duration metadata from 76.816 to 76.816689 seconds to cover
  the exact audio end; BPM, offset, and BPM markers do not change.

The measured plot shows drum/bass energy dropping while `other` continues near
the mid-song break and around 97-106 seconds, with renewed multi-layer activity
afterward. These are arrangement hypotheses supported by separated signals, not
certified phrase boundaries, named instruments, or mood labels.

Important: each stem's event onset is normalized independently. A nearly silent
`vocals` output can still have a large normalized onset. It is not evidence of
singing, relative loudness, or an added simultaneous voice. Absolute RMS and raw
positive flux were measured separately to avoid that mistaken comparison.
Neither identifies perceived musical dominance or melodic pitch.

## Reviewable 25-45 second Opus comparisons

These are excerpts, not the promised whole-song draft and not SC-rated maps.
**Rejected by the user on 2026-10-31:** upper melody/texture was not represented
and timing felt late. Do not extend A, B, or C as an accepted baseline. In B,
all 14 selected events at 25-29.6 s were bass-labelled; only 5 of 36 at 29.6-38.1 s
were other-labelled. The upper-led label was not supported by its selection.

### Correction investigation after that rejection

The subsequent 69-single-note upper-ridge excerpt was also rejected. The user's
feedback was: "일단 현재 내가 확인한 너가 짠 채보는 아주 아주 거지같고 전혀 어딜 봐도 좋은 채보가 아니야."
They added: "39초 부근부터 있는 채보는 그나마 낮은 난이도로 어느 정도는 봐줄만한 정도이지만 여전히 쓸만한 채보와는 거리가 아주아주 멀어."
This is not approval of the passage after 39 s, and this plan must not be extended.

The plan contains only singles and only the separated other-source events.
Its bans on uncertain simultaneity removed all chord gestures; no independent
rhythm-section attacks were supplied for combination. That is a concrete design
restriction, not proof that the music itself has only one part. The resulting
musical thinness is a failure hypothesis consistent with the user feedback,
not an established complete explanation. The busier C section is still rejected.
The next comparison must preserve the upper focus while supplying independently
timed rhythmic support, not revert to bass off-beats labelled as melody.

### Direct comparison with the user's project charts

After the user explicitly requested these references, the parent opened and
visually examined six editor view positions, not just JSON statistics:

- `Breaking_Dawn_base`: 45 s and 112 s. The first view combines recurring
  outside-key chords with inner singles; the latter carries an extended
  single-note flow with repeating outer-key axes and changes of hand motion.
- `Luminaria_osu_base`: 46 s and 92 s. Holds continue while other lanes play
  taps, then the held lane changes. Tap/chord groups connect into and out of
  those holds rather than treating sustained material as empty space.
- `Break_Through_Myself_osu_base`: 41 s and 84 s. Recurring chord shapes are
  interleaved with singles and short holds, retaining a recurring hand pattern
  through local changes.

These are observed score structures. Which instruments they represent was not
established by listening, and their sequences must not be transplanted.
The rejected 69-note plan instead mapped individual ridge changes to isolated
singles, with no rhythmic support, holds or chords. Merely adding notes or
chords does not establish the missing phrase structure.

`OPUS_PROMPT.md` explicitly restricts the AI pilot to "four-key, tap-only";
the editor and these reference charts demonstrably support holds. The user
resolved the scope: "롱노트 포함, 하지만 너가 잘 다룰 자신이 없다면 탭 전용도 상관없음."
Holds are now permitted, not mandatory. Uncertain sustained material may remain
taps; the old pilot restriction is not an engine limitation.

Two deterministic waveform failures are now covered by regression tests:

- The old detector missed an impulse at 1,000 ms and selected a decaying tone's
  spurious 1,125 ms event instead of its actual 1,000 ms start.
- A loud earlier accent caused the quieter continuous pitch change at 1,000 ms
  to disappear, despite a real change in the waveform's frequency.

The corrected detector separates attack timing from descriptive band features,
uses 512-sample log-mel frames at 64-sample hops, and normalizes within one second
instead of against a distant global maximum. It retains adjacent pitch changes
rather than applying frequency-max vibrato suppression. All 14 pipeline tests
pass, including the unchanged older tests and both new failures.

Analysis and browser MP3 decoding agree in native sample count and duration.
Their 24-46 s energy envelopes correlate 0.999964 at 0 ms lag, refuting a global codec
offset for that window. Native browser playback scheduling also showed no explicit
BGM preroll. Hardware output latency remains separate and was not measured on the
user's actual device. No source BPM or offset was changed.

The later native hit trace exposed a separate preview issue: immediate hit
creation on animation frames was up to 38 chart ms late at 2x. The editor now
schedules ahead against the BGM AudioContext anchor, cancels pending hits on
stop/resync and respects loop boundaries. All five editor JS suites pass. In
owned Chromium, all 69 fixture hits at both 1x and 2x were scheduled ahead at
their mapped context times (maximum numerical error below 1e-11 chart ms).
A real pause also cancelled a pending hit before its start. This verifies
reservation timing, not perceived audio latency or the rejected chart's quality.

The replacement input is the separated `other.wav` itself, not mixed-audio
candidates relabelled as upper notes. Its merged dataset is
`/tmp/chronomia-correction-20261031/upper.full.analysis.json`, with 1,190 selectable
source attacks and 967 review items on the existing subdivision 4 grid. The 25-45 s
window contains 170 selectable upper-source attacks. The 3,172 ms grid event is
supported by a newly measured 3,175.329 ms upper-source attack.

Measured CQT energy before/after each event, rising frequency bins, and source RMS
are supplied with a whole-song spectral plot. They distinguish changing material
from static accompaniment but are not certified performed notes. Basic Pitch's
absolute-pitch calibration failed; a separate fast onset/class holdout also missed
its declared precision gate. Neither model result is used as Chronomia pitch truth.
Quiet introduction leakage and late decay candidates still need deliberate
selection, not automatic conversion to notes. A corrected chart has not yet been
verified from this new input.

Opus reached its provider usage limit after saving all three plans and their
rationale. The parent recovered them, compiled separate chart files, and did the
checks below. No fallback model is credited with their pattern design.

| File in `Songs/Chronomia/` | Reading | Notes / chords | Minimum same-lane gap |
| --- | --- | ---: | ---: |
| `Chronomia_AI_Study_A_25-45.4k-speedcoef.json` | Bass-estimate anchors, then anchored chords and drum-class lane roles | 97 / 27 | 264 ms |
| `Chronomia_AI_Study_B_25-45.4k-speedcoef.json` | Upper-texture singles, selected runs, cross-hand sixteenths | 91 / 0 | 198 ms |
| `Chronomia_AI_Study_C_25-45.4k-speedcoef.json` | Recurring lane pairs, boundary chords, accent skeleton | 89 / 14 | 264 ms |

Design source files and per-event explanations:
`/tmp/chronomia-sc-study-20261031/design-opus/EVIDENCE_MEMO.md`,
`PLAN_RATIONALE.md`, `plans/`, and `derived/excerpt_event_evidence.json`.

The compiler and standalone validator pass for all 277 notes: no off-grid notes,
invalid lanes, or duplicates. Parent checks find no same-hand adjacent-sixteenth
transition. Source `timing`, `specialNotes`, and all `autoCoef` settings/curve data
are identical in each draft; the original source chart SHA-256 remains
`c323becd97f68d97b529633248e31e587be3ff7e2a7308e6730bccc0e051514f`.
Biome diagnostics were unavailable because the server is not installed; JSON
parsing and the actual compiler/validator checks were run instead.

An isolated desktop browser loaded all three actual files with notes and decoded
waveform visible, including A at 25/30 seconds, B at 38, and C at 40. A's real play
button at rate 2 advanced the displayed position from 30,000 to 32,025 ms while
showing Pause. This establishes playback state progression, not that anyone heard
the output or certified synchronization. The user's actual browser was not
inspected. Phone emulation selected C and sought correctly, but the existing
wide editor layout clips horizontally; desktop is the verified usable surface.
The QA browser/profile were removed; the editor server remains running.

### Why this is still an alignment review

The remeasurement found that many quarter-pulse attacks in bars 21-35 are
review-only. Mix peaks often precede the grid by 13-20 ms while mid-band drum
transients are nearer. Keeping only the accidental selectable subset would invent
accents, so all three plans deliberately omit that pulse. Six bass off-beats and
several later co-accents also remain unavailable. Those holes are not musical
rests. A grid-perfect output can therefore still under-represent the music.

No timing, offset, BPM marker, or tolerance was changed to hide this problem.
The next decision requires confirming the selected audible layer and alignment;
these excerpts do not settle that question or justify whole-song generation.

## Direct visual references

The following original-placement 4B SC scores were rendered and inspected in a
separate browser. The level column counts the displayed SC stars, not the site's
separate decimal "Floor" estimate. Metadata can change after game updates.

| Score | Displayed SC | Directly observed structure | Design application |
| --- | ---: | --- | --- |
| [L](https://ez2pattern.kr/djmax/chart/L/4B/SC) | 11 | Sparse opening accents develop into consecutive moving singles; recurring outer anchors and occasional doubles. | Develop a contour over several bars instead of choosing each lane independently. |
| [Binary World](https://ez2pattern.kr/djmax/chart/Binary%20World/4B/SC) | 10 | Bars 13-27 maintain outer rhythmic anchors with a moving inner voice; paired accents recur at corresponding positions. | Keep recurring rhythmic roles identifiable across phrase repetitions. |
| [NB RANGER - Virgin Force](https://ez2pattern.kr/djmax/chart/NB%20RANGER%20-%20Virgin%20Force/4B/SC) | 10 | Bars 15-26 use sustained voices and spare taps; bars 30-36 introduce paired accents and moving singles. | Change texture at phrase boundaries; do not maintain one uniform density. Holds themselves are not copied into this tap-only pipeline. |
| [Airwave](https://ez2pattern.kr/djmax/chart/Airwave/4B/SC) | 11 | Bars 35-41 repeat a short contour; later runs change direction and introduce occasional doubles. | Repeat and vary a motif rather than cycling one stair for a whole song. |
| [Deadly Bomber](https://ez2pattern.kr/djmax/chart/Deadly%20Bomber/4B/SC) | 10 | Bars 17-24 repeat chord accents against a moving voice, followed by a lower-density texture. | Use supported percussion accents to layer chords, followed by release. |
| [Nightmare](https://ez2pattern.kr/djmax/chart/Nightmare/4B/SC) | 15 | The final inspected bars 79-85 concentrate repeated chords, unlike the moving voices and sustained sections earlier. | A concentrated difficulty peak needs preparation and release. Do not copy its sustained chordjacks into 2x OverTempo. |
| [Daydream](https://ez2pattern.kr/djmax/chart/Daydream/4B/SC) | 11 | Bars 30-40 combine repeated pairs with inner/outer motion, then bars 41-44 reduce density. | Define phrase-level density and hand-motion changes before filling individual notes. |

WhiteBlue SC10 was also opened, but its score viewer returned "chart data not
available"; it is excluded from pattern evidence. Search-only descriptions and
unseen gameplay videos are not treated as visual observations.

## Expanded comparison set

The following are additional silent layout observations returned by independent
research tracks. They are useful comparisons, not verified audio mappings.
Printed viewer bar numbers are used; columns read bottom to top.

| 4B SC score | Inspected ranges or transitions | Visible distinction | Evaluation scope |
| --- | --- | --- | --- |
| Malicious Mischance | 3-10, 39-46, 69-88 | Interleaved taps, chords, and holds thin sharply at 43-46; mixed activity returns before a sparse held ending. | A firsthand 4B player explicitly praises the chart. |
| ELIXIR | 2-9, 38-45, 58-65, 76-83, 88-101 | Spaced opening vocabulary, exposed repeated singles at 58-61, later interleaving and chord accents, then final space. | Same reviewer explicitly calls the chart good. |
| Vertical Eclipse | 2-9, 38-45, 54-61, 78-85, 104-116 | Sparse figures return at 54-61; late streams and chord interruptions end in holds and release. | Same reviewer calls it fun but warns about its ending. |
| Tok9 Train | 2-9, 30-33, 38-45, 62-75 | Moving figures repeatedly meet broad simultaneous/held punctuation rather than one continuous chord stream. | Same reviewer praises the 4B chord chart; their negative 6B remark is separate. |
| Back to the oldschool | 2-9, 22-24, 38-45, 58-65, 78-90 | Early gaps contrast with an eighth-note anchor at 24 and a later denser chordal development. | Same reviewer explicitly calls the chart fun. |
| Watch Your Step | 3-5, 19-22, 35-38, 49-50 | Recurrent chord rhythm develops into turns; bar 50 is a distinct fast cycle, not the whole chart's vocabulary. | Praise lead referred to MX with unspecified button mode, not this SC layout. |
| Tok! Tok! Tok! | 15-18, 39-42, 59-62, 85-88 | Bursts contract into sparse or side-only sustained intervals; the ending adds broad attacks. | No independently established exact-chart endorsement. |
| U.A.D | 3-5, 31-42, 59-66 | Clipped gestures, holds, and a six-notes-per-beat passage at 39-42 have distinct articulations. | A fast-arpeggio praise lead lacks exact button-mode alignment. |
| Mind Control | 2-5, 49-53, 85-90 | Quarter-note anchors, large holds, alternating whole-hand doubles, gaps, and a triplet interruption differ categorically. | Favorable 4B/6B testimony does not identify the SC difficulty. |
| LAMIA | 5-12, 49-56, 77-80, 105-108 | Exposed recurring figures contrast with broad held gestures and later mixed movement. | Structural comparison only. |
| Xeus | 2-9, 38-45, 70-75 | Moving taps around held lanes, hold-based relief, then an active return. | Structural comparison only. |
| Cthugha | 3-10, 37-44, 85-92, 117-139 | Sparse opening, mixed activity, lighter return, and a chord-heavy late section. | The reviewer flags simultaneous-reading difficulty; not a positive endorsement. |
| Trrricksters!! | 2-9, 38-45, 50-69, 86-95 | Bars 58-65 become mainly held material with few new attacks before the active return. | Scoring accessibility is not chart-quality praise. |
| ouroboros -twin stroke of the end- | 2-9, 36-43, 84-115 | Sparse middle contrast, dense late activity, inner-lane alternation at 107, then hold relief. | Scoring accessibility is not chart-quality praise. |

Each score route is
`https://ez2pattern.kr/djmax/chart/<URL-encoded exact title>/4B/SC`.
Unavailable scores, including Miles, HELIX MX, WhiteBlue, Hypernaid, and
Grid System, are excluded from observed-layout claims. Missing viewer data
does not prove the game has no such chart.

The favorable evaluations above come from one player's 4B report, not five
independent endorsers. The article's individual comments do not always repeat
the difficulty; the inspected images are explicitly SC:
<https://note.com/are0t0/n/n81bba949d732>.

## Musical correspondence: established context and open alignment

| Case | Separately supported musical context | What is not yet established |
| --- | --- | --- |
| ELIXIR | TAG describes starting from a mysterious piano phrase and pursuing a mysterious atmosphere with a contrasting stylistic detour. | Which printed bars carry that piano phrase; whether the sparse figure or dense return selects it. |
| Vertical Eclipse | TAG describes composing for a strong playing/performance feel. He identifies his own chart work as 5B SC, not the inspected 4B. | Which 4B placements express which sounds; authorship must not be transferred between modes. |
| Author's rejected DPC2025 submission | cyg explicitly intended strings first, then guitar and drums. Their reflection says avoiding repeated shapes displaced keysound correspondence, the first chorus reused the source too closely, and the ending was over-weighted. | This is counterevidence about a rejected 5B submission, not praise or validation of a 4B reference. |

Primary sources:

- TAG, ELIXIR:
  <https://note.com/tag_underground/n/n25e69ccecfcd>
- TAG, Vertical Eclipse:
  <https://note.com/tag_underground/n/nf8ace99118bd>
- cyg, DPC2025 reflection:
  <https://note.com/cyg5882/n/n30618058d971>

The creator reflection directly defeats the assumption that many different
shapes alone make a musically grounded chart. A proposed Chronomia passage
must name the selected audible material, its attack/rest/sustain structure,
the actual phrase transition, and why the proposed physical gesture expresses
those events. Unresolved attribution stays unresolved; it is not filled with
an instrument guessed from lane geometry.

## Contrasting musical cases, not mood-to-shape formulas

The following comparisons use the firsthand music/player account at
<https://note.com/saburou1341/n/n437e95987d39>. They are attributed observations,
not listening performed in this session. The writer explicitly disclaims formal
music expertise; exact meter claims therefore need independent verification.

| Case | Attributed musical observation | Decision it motivates | Limit or counterexample |
| --- | --- | --- | --- |
| Away | Genuine slow quarter-note feel at BPM 78, punctuated by brief fast piano figures. | Preserve the slow pulse and local ornament as different articulations; a short flourish need not destroy spaciousness. | "Ballad" does not imply uniformly sparse notes. Mode and precise bar correspondence are unspecified here. |
| Insane Drift | At 1:34, the drop strips down to kick and screech; the player singles out lane 1 in 6B. | A stable lane can make a stripped, repeated attack physically explicit instead of adding decorative travel. | This is the strongest specific sound/key correspondence in this source, but it is 6B, not verified 4B SC. |
| Rhapsody for The VEndetta | The player experiences recurring six-beat accents and a distinctive compound feel. | Phrase and gesture grouping should follow the perceived accents, not an automatic four-beat/sixteen-slot formula. | This is perceptual testimony, not an independently verified time-signature annotation. |
| SIN ~The Last Scene~ | The account distinguishes subdivided breakbeats from the sudden four-on-the-floor outro. | A change in the underlying pulse may justify a categorical change in gesture rather than merely adding notes. | The writer does not identify button mode; the inspected 4B geometry alone cannot complete the alignment. |

These cases oppose three tempting shortcuts. Slow atmosphere can coexist with
fast local ornament; high energy can be expressed by a deliberately narrow
repeated gesture; and phrase identity can depend on accents that cross a
convenient counting block. None establishes "sad means stairs" or "intense means
chords." For Chronomia, the selected sound and its articulation must be identified
first; geometry is the later physical translation.

The separate 4B evaluator above likes D2's music but does not recommend its
repeated-note/asymmetric-trill chart. That disagreement is useful: musical
enthusiasm and high difficulty do not establish enjoyable physical translation.
Conversely, favorable evaluations of ELIXIR and Tok9 Train do not establish which
individual sound their lane shapes select. Keep both gaps visible.

## Existing repository corpus

Actual `notes` arrays were parsed, grouped by time, and checked against each
chart's timing map. "Peak 2x" counts notes in a 2000 ms chart-time window. It is a
physical-load estimate, not a difficulty rating.

| Source | Notes | Attack moments | Chord share | Peak 1x / 2x |
| --- | ---: | ---: | ---: | ---: |
| Chronomia Normal | 825 | 634 | 27.9% | 12 / 23 |
| Luminaria osu base | 1133 | 837 | 32.5% | 21 / 31 |
| End Time | 1098 | 840 | 27.7% | 32 / 49 |
| Aleph-0 base | 877 | 616 | 41.2% | 17 / 30 |
| Calamity Fortune osu base | 748 | 629 | 18.0% | 14 / 23 |
| Poison AND OR Affection osu base | 665 | 550 | 20.7% | 10 / 18 |
| Breaking Dawn base | 1272 | 929 | 34.9% | 16 / 27 |
| Break Through Myself osu base | 894 | 644 | 38.7% | 15 / 25 |
| Stellaria draft | 1059 | 790 | 33.0% | 17 / 30 |

Imported difficulties and folded charts are not DJMAX calibration data.
Representative consecutive note groups were inspected as well as totals.
Chronomia's existing same-lane minimum is 132 ms, and most of its attack moments
use whole or half beats. Its 76-81 second passage provides a structural contrast
to its sparser repeated quarter-note and chord passages around 29-33 seconds.
These are observations of the existing chart, not claims about hearing audio.

## Remap rules

1. Preserve the complete source `timing`, `autoCoef`, speed-limit and delta data.
   Use `chartMs = audioMs + offsetMs`; do not estimate replacement timing.
2. Use measured audio attacks on the editor's default sixteenth-note grid.
   Do not reinterpret every off-grid peak as a triplet or a thirty-second note.
   A finer rhythm needs a repeated musical reason, not merely a closer grid.
3. Base selection on audio attack evidence and phrase-level strength. Flag
   rejected attacks rather than silently moving them or filling arbitrary ticks.
4. Choose recurring gestures only after identifying recurring musical material.
   Mirroring, anchoring, chord weight, and release are alternatives to justify,
   not a mandatory checklist. A phrase boundary needs musical evidence rather
   than an arbitrary fixed bar count.
5. Avoid uniform stairs, gratuitous chords, and unprepared fast same-lane repeats.
   Audit adjacent transitions at the game's possible 2x speed.
6. Verify exact grid membership for every note. Distinguish attack-to-grid error
   from output alignment. The editor must display the grid actually used.
7. Deliver a separate, unrated full-song draft and a reproducible review report;
   do not overwrite the original or describe a three-second preview as finished.
