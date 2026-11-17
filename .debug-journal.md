# Debug Journal - Chronomia missing upper layer and late-feeling notes

Started: 2026-10-31
Goal: replace rejected bass/drum-led drafts with supported upper-melody/texture
selection and diagnose timing without changing source BPM or offset.

## Environment

- Analysis: `Tools/ai-chart/.venv/bin/python`, librosa 0.11.0.
- Separation: `/tmp/chronomia-stems-env/bin/python`, Demucs 4.0.1,
  torch/torchaudio 2.5.1, CUDA RTX 4060 Ti 8 GB.
- Editor: existing Python server at `http://127.0.0.1:5173`, session `bash_10`.
- Original Chronomia SHA-256:
  `c323becd97f68d97b529633248e31e587be3ff7e2a7308e6730bccc0e051514f`.
- No source or audio timing edits authorized; no build/release/commit requested.
- References read: debugging Python/Node runtimes, setup, investigation;
  librosa STFT/onset framing documentation through Context7.

## Hypotheses and discriminating evidence

1. H1: mixture-only candidate detection plus bass-cell reuse excludes the upper
   musical material. Compare selected event provenance/focus against independent
   upper-stem spectral changes. Fix if confirmed: source-specific candidates.
2. H2: raw spectral-flux maxima are not stable note attack timestamps across
   envelopes; grid snapping can select the next subdivision for a soft attack.
   Measure known synthetic attacks with different rise times and actual source
   waveform changes. Fix if confirmed: calibrated attack definition, not offset.
3. H3: editor chart/performance clock differs from audio context/output timing.
   Independent owned-browser track measures native source starts and clocks at
   1x/2x. Fix only if runtime measurements confirm a discrepancy.
4. H4: MP3 decoding/priming differs between analysis and browser decode. Compare
   decoded energy envelopes before attributing a global delay to the chart.

## Confirmed constraints and existing evidence

- User rejected all A/B/C excerpts as missing upper melody/texture and late-feeling.
- No listening was performed by either model.
- Grid correctness, native playback progress, and source immutability do not
  certify musical synchronization.
- The old synthetic audio test allows 125 ms error; it is not evidence of tight
  attack alignment. Preserve it and add a meaningful failing regression if needed.
- Original plans and generated A/B/C remain rejected comparison artifacts, not a
  baseline to extend.

## Artifacts registered before creation

- This journal: remove with apply_patch at cleanup after findings are promoted.
- `/tmp/chronomia-correction-20261031/`: synthetic timing probes and derived
  measurements; remove temporary probe scripts/data at cleanup.
- `/tmp/chronomia-playback-diagnosis/`: independent browser evidence; no repo edits.
- Independent child `st_01a190fe`: read-only playback diagnosis, owned browser only;
  close browser/profile on completion.
- Any new production edit or test will be registered here before modification.
- `/tmp/chronomia-upper-transcription/`: isolated Python 3.10 Basic Pitch
  experiment, synthetic calibration, upper-stem note/frame outputs; no lanes.
- `/tmp/chronomia-correction-20261031/decode_envelope.py` and generated JSON:
  compare source decoding energy with browser OfflineAudioContext at native rate.
- One isolated owned browser for decode comparison; close/remove profile in the
  same eval lifecycle. Never load or save an original chart.
- Production fix scope: `Tools/ai-chart/analyze.py` attack timestamp detection
  and detector identity; `Tools/ai-chart/tests/test_pipeline.py` failing known-
  waveform regression and feature seam update. No source JSON timing changes.
- Corrected-pattern QA: parent-owned `/tmp/chronomia-upper-qa-*` browser profile
  and screenshots. Close its browser and remove its profile at handoff; leave
  editor server `bash_10` running. Only new, separately named draft charts may be
  compiled into `Songs/Chronomia/`; original charts remain read-only.
- After rejection of the 69-single-note plan: independently analyze drums/bass
  into `/tmp/chronomia-correction-20261031/{drums,bass}.independent.analysis.json`.
  These are support-layer measurements, never replacement melody labels.
  Keep source timing and the subdivision-4/12ms gate unchanged.
- User selected holds with taps allowed where hold handling is uncertain.
  Register minimal optional `holdEnds` lane-to-event references in build.py,
  end-grid and same-lane occupancy validation in validate.py, hold rendering in
  visualize.py, regression tests in tests/test_pipeline.py and updated docs.
  Source settings remain immutable; no model-written duration or timestamps.
- Preview timing follow-up: native oscillator starts for all 69 notes were
  recorded at 1x and 2x. Relative to BGM context mapping, 1x trigger error was
  -7.667..17.333 chart ms (mean3.633), 2x -9..38 chart ms (mean15.536).
  `auditionCrossedNotes` currently waits for a render frame and calls playHit
  immediately. Register a deterministic audio-clock regression in
  Tools/chart-editor/test_editor_core.mjs and minimal look-ahead/cancellation
  changes in index.html. Do not change source audio, timing or note coordinates.

## Preview audio-clock correction

- Red: `node Tools/chart-editor/test_editor_core.mjs` failed with
  `future hits must be scheduled before their render frame`, actual0/expected1.
- Fix: schedule100ms ahead in AudioContext time using the BGM chart/context
  anchor and playback rate. Cancel future oscillators and clear their consumed
  marks when stopping/resynchronizing; cap look-ahead at a valid loop boundary.
- All five editor JS suites pass, including new deterministic 1x/2x, cancellation,
  duplicate scheduling, loop and muted-channel cases.
- Real owned Chromium: all69 hits scheduled ahead at1x and2x. Maximum native
  start-argument error relative to the BGM mapping was0 at1x and7.28e-12 chart ms
  at2x (floating-point noise), versus the pre-fix38ms maximum.
- Real pause cancelled a future hit at context138.624 before its scheduled
  time138.66833333333335; Play button returned to Play.
- These are scheduling measurements, not human listening or hardware latency.
  They do not approve the rejected69-note musical design.

## Failed rounds

- The 69-single-note upper-only draft was rejected.
- On 2026-11-01 the parent initially attributed this feedback to the
  169-note/6-hold revision:
  "여전히 거지같고 게임에 쓸 수도 없을 정도로 굉장히 아주 아주 저열한 퀄리티야. 박자도 밀려있어 씨발새끼야."
- CORRECTION: the user later said they had repeatedly viewed older charts and
  asked which file to inspect. The exact latest Upper_Rhythm_Holds URL was
  provided. Revision 2 is neither confirmed rejected nor approved. The parent
  corrected the live Opus audit and memory attribution. Await its clearly
  identified musical review; do not redesign on the false premise of rejection.
- Native scheduling equality is not proof of correspondence between performed
  musical attacks and selected notes.

## Restart and renewed timing investigation, 2026-11-01

- Reboot removed the old /tmp evidence and browser measurements. Opus result
  was recovered from its durable completion record; canonical plan hash matches
  ca3d3c5eebfbb3bd293d6b27c2bfbac82acb5f4122685819f540615c6b60a8dc.
- Restored editor server is bash_2. Source JSON hash remains c323becd...514f.
- New trusted-click Chromium runs scheduled all169 note starts ahead at1x/2x
  against one BGM source anchor each. Maximum argument error is7.28e-12 chart ms.
  A programmatic-click run left AudioContext suspended and is explicitly invalid.
- Evidence and restored scripts: .omo/artifacts/chronomia-correction-20261101/.
  Rebuilt stems and analyses: Tools/ai-chart/output/chronomia-20261101/.
  Rebuild is a new run (Demucs4.0.1, htdemucs, shifts0, float32), not a byte-identical
  recovery. Do not reuse old analysis IDs for the rebuilt candidates.
- Pending probe artifact: diagnose_excerpt_timing.py plus note-locked waveform,
  spectral panels and measured timing JSON in those folders. It may measure
  unsnapped audio only; it must not alter source timing, note times or plan lanes.
- Hypothesis A: source selection locks onto later partial/texture changes rather
  than the intended musical onset. Distinguish by raw mix/other waveform and
  spectral edges around selected starts, retaining earlier review-only attacks.
  If confirmed: replace wrong events.
- Hypothesis B: audio context and visual performance clocks diverge in the real
  editor, despite correct native hit scheduling. Distinguish by simultaneous
  DOM playhead/context/output timestamp measurements, not oscillator arguments.
  If confirmed: correct presentation clock.
- Hypothesis C: the authorial design assigns chords/holds to unsupported roles
  or releases. Distinguish sustained source energy and phrase changes from the
  rationale's gesture endpoints; no source-bin recurrence proves a voice.
  If confirmed: redesign from supported roles.
- Paired presentation-clock probe completed: 361 DOM updates per rate, one BGM
  each, trusted clicks. DOM-minus-context medians -3.33ms (1x), -17.33ms (2x);
  DOM-minus-browser-output-timestamp medians +24.84ms (1x), +39.52ms (2x).
  No accumulating drift or BGM resync. Headless output backend unidentified.
  This does not demonstrate the reported late presentation; do not implement
  a presentation clock change as a guessed explanation.
- Raw-source probe completed and all four plots displayed. CE0092 at34031ms
  lies60.161ms after the nearest rebuilt other attack and63.063ms after the
  nearest mix attack. Thirteen old upper-supported moments fail to reproduce
  within12ms in the rebuilt other source. Source settings differ, so this is
  support instability, not proof of thirteen incorrect notes. Median nearest
  attack differences are negative; no single global retiming is justified.
- Asked which surface is late: editor hit sound, editor visual notes, or actual
  game playback/judgment. This observation is not recoverable from the isolated
  browser probe and changes the component to investigate next. Pending answer.
- The user clarified: "아니 씨발아 음악 나오는거랑 노트 타격음이랑 하나도 안맞잖아".
  The active failure is music-to-hit-sound correspondence. Presentation-clock
  work is closed as a non-explanation; no presentation fix is authorized by
  this evidence. New work must validate selected attack rhythms before lanes.
- Register prepare_rhythm_evidence.py and its excerpt analysis/TSV outputs:
  add original-mix, unquantized attack and spectral-change evidence beside
  each source-specific candidate. No chart, source time or grid changes.
  Shared frequency-bin support is evidence, never voice/foreground proof.
- Correctly identified revision-2 review arrived: "오케이 검토 완료. 전체적으로 많이 좋아지긴 했지만 지금 불필요하게 1/4, 3/4 박자일 때 나오는게 많아. 물론 있어야 하는 것들도 있지만 리듬감을 느끼기 어려운 곳에 이것들이 배치되어 있어서 애매해."
  Preserve this substantially improved baseline. Refine sub1/sub3 (29 of135
  attack moments), preserving needed fills, phrase links and clear articulations.
  Do not replace it with the earlier audit's coarse80-event selection.
- Register a separate pruned plan, a separately named refined25-45 chart and
  review report, and refinement evidence under the durable artifact folder.
  Preserve all surviving notes byte-for-field: no retiming, added attacks,
  shifted hold releases, source timing/acceleration edits or reference copying.
  Validate grid/hold occupancy, exact-subset provenance, and actual editor
  rendering/playback after the selective-pruning decisions land.
- Refinement completed:146 notes,112 moments,4 holds; sub1/sub3 starts29->6.
  All146 surviving note records are exact baseline copies. Source and169-note
  baseline hashes unchanged. Validator has no errors/warnings; all146 starts
  and4 tails on grid. Original213 source reviews retained as unselectable.
- Actual refined editor views at34.0/37.5s inspected; trusted-click1x/2x each
  scheduled all146 starts ahead against one BGM anchor. Owned browser closed
  and profile removed; server bash_2 remains running. No listening claim.
- Register prepare_full_mix.py, full-mix analysis/compact TSV and full-original-
  mix spectrum under durable output: data preparation only while the user's
  refined-excerpt feedback is pending. No whole-song creative plan starts before
  the corrected passage gate is satisfied, and no baseline/source is overwritten.
- User rejected the gap behaviour of the146-note refinement:3/4,5/4 and6/4
  waits are ambiguous while melody continues, and offered a corrected example.
  Scope is inter-onset rhythm, not merely removing sub1/sub3 grid positions.
  Deletion changed6-tick gaps from1 to5 and introduced three8-tick gaps.
  Preserve refined-146-before-human.json outside Songs; native modify monitor
  watches only the user's _Refined file. Asked for a short25-31s example.
  No assistant edits to that file while the user is working.
- Full-mix prep exposed a numerical measurement bug outside the excerpt:
  zero-energy profiles produce spectralChange1 and arbitrary top bins despite
  positiveChangeMagnitude0. Register a versioned full-mix-v2 output correcting
  undefined comparisons to null and empty rising-bin lists. Preserve all v1
  data and source-event times/IDs; this is not an explanation for the user's
  excerpt feedback or a new note-selection rule.

## Observations

- B plan, 25-29.6 s: 14 selected events, all 14 bass-labelled, zero other-labelled.
- B plan, 29.6-38.1 s: 36 events, 28 bass-labelled, only 5 other-labelled.
  H1 is confirmed for the rejected upper-led claim.
- Known impulse at 1000 ms: raw spectral-flux peak 986.848 ms; no selectable event.
- Known sharp-decay tone at 1000 ms: correct attack excluded, a spurious event at
  grid 1125 ms selected from an observed 1126.168 ms peak. This is a failing
  timing/false-positive control, not evidence of Chronomia's true note times.
- Known 10/30/60 ms rise tones produce different raw peak offsets. A fixed global
  BPM/offset correction is not justified.
- Independent browser clock report: fresh 1x/2x use native start(0,25); chart
  versus render clock error <25 ms; measured output lag 26-53 real ms, up to
  roughly 105 chart ms at 2x. No explicit BGM preroll was observed.
- Source MP3 decoding comparison: both browser OfflineAudioContext and native
  libsndfile return 6,606,916 samples at 44,100 Hz, duration149.81668934240363s.
  Correlation of 1 ms energy bins over24-46s is0.9999644218668002 at0ms lag;
  the next best lag (-1ms) is0.4158667339052612. H4 is refuted for this window.
- Documented onset method comparison: mel flux with512-sample FFT,64-sample hop,
  max-filter3, no backtracking finds impulse/sharp tone at1001.361ms and the
  10/30/60ms rising tones at1004.263ms; no1125ms detection in the checked window.
  The prior raw-flux method fails the same controls. Backtracking repeats the
  old local minimum, so it is not selected.
- Red regression: `test_known_attack_is_not_lost_or_replaced_by_late_decay`
  fails all5 controls on the old code; missing impulse, substituted1125ms note,
  extra1125ms decay notes, and10.068ms onset error.
- First replacement missed the existing1500ms click because the leading-edge
  normalized strength was0.141787 (<0.16) even though a genuine peak followed.
  Measuring confidence over the same half-window restores it without changing
  the attack timestamp.
- Green: `python -m unittest discover -s Tools/ai-chart/tests -v` passes13 tests
  after that correction (1.054s); the original synthetic-click test is unchanged.
- Basic Pitch0.4.0 calibration failed its predeclared exact-pitch precision gate:
 28/28 fundamentals recovered,22 extra predictions (19 octave duplicates).
 No Chronomia transcription was run or treated as pitch truth.
- The rejected pitch model's default minimum note length is127.70ms, longer
  than Chronomia's66.08ms sixteenths. It is not an adequate fast-note calibration.
- Registered new measurement contract before running it:
  `/tmp/chronomia-correction-20261031/measure_pitch_classes.py` will test onset+
  chromatic-class groups (not absolute pitch or number of performed voices) with
  minimum_note_length40ms, required by the source sixteenth duration. A fresh
  holdout includes66ms notes and a masked upper line. Gate: precision/recall>=.85,
  onset error<=30ms, masked-upper recall>=.75. Octave-coincident predictions are
  retained as ambiguity within one class group, never separate notes. The old
  exact-pitch gate remains FAIL. No Chronomia inference unless this distinct
  contract passes. No threshold tuning after the holdout.
