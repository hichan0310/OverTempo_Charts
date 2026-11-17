# Human-corrected rhythm reference

The user completed edits to the Refined chart on November 1, 2026.
Their stated intent is a steady rhythmic flow, two-hand simultaneous hits at
important sounds, and holds where sounds extend. They did not design pitch
mapping or acceleration coefficients. Acceleration work is deferred until the
note shapes are settled.

Reference file:
`Songs/Chronomia/Chronomia_AI_Upper_Rhythm_Holds_25-45_Refined.4k-speedcoef.json`

Compare against `refined-146-before-human.json`, not the earlier 169-note draft.
Do not overwrite the human reference.

## Observed changes

- Notes: 146 to 180; distinct onset moments: 112 to 145.
- Chord moments: 32 to 34; holds: 4 to 14.
- Inter-onset gaps, measured in sixteenth-note grid ticks:
  before: 1:10, 2:68, 3:1, 4:23, 5:1, 6:5, 8:3.
  after: 1:24, 2:109, 4:10, 16:1.
- All saved starts and hold endpoints match the integer editor grid.
- The one 16-tick onset gap is 29339 to 30396 ms: a hold occupies that
  interval. It is sustained playing, not an unsupported empty gap.
- At 27225 ms, lane 0 holds to 28018 ms while other lanes continue taps.
- At 34097 and 34361 ms, paired holds alternate lane pairs [0,2] and [1,3].
- The user retained short sixteenth runs. Their concern was not a ban on
  offbeat positions, nor an instruction to fill every grid slot.

These are measured geometry and the user's musical interpretation, not an
independent listening assessment or proof of pitch identity. The recurring
two-tick pulse is a reference for continuity, not authorization to fabricate
attacks where the audio evidence has none.

## Settings

The saved timing and specialNotes equal the original source. autoCoef.settings
is unchanged, but its generatedAt and curve differ after editor saving.
Do not rewrite the user's file to repair this. A separate generated full-song
draft must preserve the original source autoCoef and special settings exactly.
Do not infer pitch order from the reference's lane choices.

## Extension requirements

Use measured selectable attacks, with original unsnapped timing and source
provenance retained. Label drum/bass support separately from estimated upper
texture. A regular pulse must not replace upper-layer correspondence.
Use important evidenced accents for two-hand chords, and supported sustained
texture for holds. Preserve intentional sustained passages instead of forcing
constant tapping. Avoid arbitrary 3-, 5-, or 6-tick gaps during continuing
phrases, but do not invent attacks to remove a gap.

Keep the human reference passage unchanged in a separate full-song draft.
Unresolved source attribution, absent selectable attacks, or uncertain hold
endpoints remain review information, not silently solved transcription.

## Editor inspection

The parent displayed and examined the real editor at 27 and 34 seconds.
The editor loaded all 180 notes and 14 holds with the original MP3 waveform.
At 34 seconds, the alternating paired holds and continuing taps were visible.
No chart was saved or modified by the inspection.

A bounded event-based replay used a native pointer click on Preview; the
captured DOM click had isTrusted=true. All 180 oscillator starts were observed,
and their scheduled chart positions matched saved onsets within
7.28e-12 ms. This checks scheduling arguments, not acoustic synchronization.
The BGM start was scheduled at context time zero while suspended; oscillator
states included suspended during startup and running later. That startup
anchor is not accepted as presentation-latency evidence. No physical listening
or new output-latency conclusion is claimed.

## Human authorship versus regenerated detector membership

Of the 145 distinct human-authored onset moments, 141 have exact chartMs
membership in regenerated v2 candidates. Four do not: 27753, 31189, 39053,
and 40242 ms. Every human hold endpoint has a selectable v2 event.
This is source membership, not a musical correctness score.

Reference onset membership counts:
bass+upper 10; bass+drums+upper 71; upper 8; bass+drums 25;
bass 15; drums 6; drums+upper 6; human-only 4.
The 46 bass/drum-only moments are not detector-confirmed upper melody.

Preserve the four human-only moments as explicit human-authored exceptions
when carrying the user's reference geometry into the full draft. Do not
fabricate measured event IDs, change detector tolerance, label these as
detector-confirmed, or silently remove them. AI-designed notes outside the
reference must still use selectable measured candidates. Upper attribution
and musical correspondence require separate evidence even at shared times.
