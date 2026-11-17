# Completion audit: separate full-song review draft

## Scope

Deliver a corrected approach, a validated 25-45 second reference, and a
separate full-song draft, with original settings preserved and unresolved
musical attribution explicit. This is not approval of a final playable chart.
The user asked to proceed on best judgment after a question timed out.
No timeout is treated as endorsement.

The extra full-song user-approval task was added by the assistant, not required
as a delivery gate by the user. It is dropped rather than marked approved.
The user's actual 25-45 second edit remains the reference used before extension.

## Requirement-to-evidence map

| Requirement | Current evidence |
|---|---|
| Diagnose attack selection rather than assume grid validity means sync | `../timing-source-measurements.json`, `../diagnose_excerpt_timing.py`, `../HUMAN_REFERENCE.md`, and phrase-specific `RATIONALE.md` distinguish source membership, spectral changes, scheduling and musical interpretation. The earlier sparse deletion approach is not the full-song design. |
| Correct audio/chart conversion without retiming the source | Compiler checks every selected attack and hold endpoint using chartMs = audioMs + offsetMs. All 761 distinct selected start/end references passed this check. Original BPM 227, offset 0 and BPM markers are unchanged. |
| Upper-layer attacks and texture evidence instead of bass/drum-only melody claims | 594 of 758 AI onset moments contain the separated other-stem source and its texture evidence; 164 rhythm-section-only moments are explicitly labelled support. `RATIONALE.md` separates measurements, provisional phrase readings and geometry. This supports an estimated upper-texture approach, not certified melody or pitch transcription. |
| Validate 25-45 seconds before extending | The user corrected the 180-note, 14-hold Refined passage and explained its rhythm, chord and sustain intent. Exact-grid, overlap and real-editor checks are recorded in `../HUMAN_REFERENCE.md`. The extension was designed afterward. |
| Separate whole-song draft, not only an excerpt | `Songs/Chronomia/Chronomia_AI_Full_HumanRhythm_Draft.4k-speedcoef.json` contains 1,118 notes, 903 onset moments and 29 holds, with 20 AI phrases outside the human window. First and last charted sounds are 3,172 and 142,731 ms; the intro and decay rests are explained in `RATIONALE.md`. |
| Preserve originals and source settings | Original source SHA256 is c323becd97f68d97b529633248e31e587be3ff7e2a7308e6730bccc0e051514f. Human reference SHA256 is d34250696c6b6db1307768bfcc11547c375924c00c025283dedee5aebfb57cdc. Neither was overwritten. Full-draft timing, autoCoef and specialNotes equal the original. |
| Preserve human geometry; defer acceleration work | All 180 human notes, including their saved per-note fields, are copied exactly. Original top-level autoCoef remains unchanged. No acceleration optimization or pitch-order claim was added. |
| Every start and hold end on the editor grid | Actual `validate.py` CLI exited 0: 1,118 starts and 29 hold ends checked, no errors or off-grid indices. Allowed subdivision is 4. |
| Measured-event provenance and unresolved reviews retained | `full.plan.json` selects only v2 event IDs; all contributor deviations are within 12 ms. The review companion retains all 2,463 unselectable source-review attacks, source/plan hashes and selected IDs. Four human-only onset moments are explicitly attributed to the user, not fabricated detector events. |
| Actual Opus for creative design, no silent fallback | Accepted task st_01a19669 used claude-opus-5-5 throughout its reported 46 assistant turns. Plan SHA256 is 80336c140b2fd4010179fa12db89fce2bd8a23a22ac4edb70376e1ac8a8833c2. The earlier fallback task was cancelled and no output from it was used. |
| Appropriate checks and actual editor use | Compiler and structural checks passed. Real scores at 3, 45, 65, 98, 115 and 142 seconds were displayed and examined. `EDITOR_QA.json` records a trusted-click, single continuous 2x run with 1,118 of 1,118 oscillator starts, no missing or duplicate onset counts, one running BGM anchor and minimum scheduling lead 78.67 ms. This is scheduling evidence, not hardware latency or listening. |
| No false listening claim | No listening or skilled-player test occurred. Separation and spectral-bin attribution remain estimates in the draft metadata, rationale and review companion. |
| Direct URL and running editor, no release | The direct full-draft URL was delivered. The local editor remains the review surface at port 5173. No client build, release, deploy or repository commit was requested or performed for this draft. |

## Explicit remaining review data

- Dotted waits in bars 60, 61, 107 and 123; dotted chain in bar 56.
- Three weak holds at 64,890, 96,211 and 98,326 ms.
- The final tap at 142,731 ms.
- Constant 2x density advisory: estimated peak 28 NPS, including the human
  reference's own peak. Playability is not certified.
- Starting playback exactly on the 60,000 ms note produced about 21.33 chart-ms
  of first-hit startup delay. It did not occur in the decisive continuous run.
  No speculative editor or source-timing fix was made for this startup boundary.
- Biome LSP is unavailable. JSON parsing, the actual structural validator and
  real editor checks were used; no package was installed.

These are retained limitations of a review draft, not facts silently resolved
by a timeout. The requested full-song draft and technical evidence exist.
No claim is made that the complete song has received musical approval.
