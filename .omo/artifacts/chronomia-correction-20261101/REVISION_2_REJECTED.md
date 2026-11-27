# Revision 2 review status: previous rejection attribution withdrawn

On 2026-11-01 the parent initially attributed the user's negative feedback to
the 169-note, six-hold excerpt. The user subsequently clarified:
"아 잠깐만 너가 채보를 여러 개 만들고 있구나. 내가 이전 것만 계속 봤다. 어떤 걸 봐야 해?"
The parent supplied the exact latest-draft URL. That feedback cannot be treated
as a confirmed review or rejection of revision 2. It is not approval either.
The file's historical name is retained for existing audit references.

The user has now reviewed the correctly identified revision 2: it is substantially
improved, but unnecessary within-beat 1/4 and 3/4 articulations often obscure the
groove. Some are necessary and must remain. This supersedes the earlier pending
status; it is a targeted refinement request, not rejection or final approval.
The measurements below remain evidence and caveats, not user quality judgments.

## New measured evidence

`timing-source-measurements.json` and four `timing-source-window-*.png` panels
  compare unmodified mix/other audio with the revision-2 notes. All four panels
were displayed and visually examined. No audio was listened to.

- Across 135 attack moments, chart-minus-nearest-unsnapped-detector-attack
  has median -2.361 ms in the mix and -2.703 ms in other. This is not a musical
  correspondence test and does not establish perceptual alignment.
- Mix deltas range from -69.467 to +131.773 ms; other deltas from -69.490 to
  +60.161 ms. This does not support one constant correction for every note.
- CE0092 at 34031 ms is 63.063 ms after the nearest mix detector attack and
  60.161 ms after the nearest other detector attack in the rebuilt source.
  The rebuilt full-source analysis also has events at 33965 and 34097, but
  none at 34031. The apparent one-sixteenth-late correspondence needs review.
- CE0049 at 30132 ms is 131.773 ms after the nearest mix detector attack, but
  10.449 ms before the nearest other detector attack. This is an example where
  source-local event timing does not establish which audible gesture is charted.
- Of 117 old upper-supported moments, 13 are not reproduced within 12 ms of a
  nearby unsnapped other detector attack in the rebuilt separation:
  CE0005, CE0070, CE0072, CE0079, CE0092, CE0118, CE0119, CE0128, CE0132,
  CE0155, CE0161, CE0173, CE0178.

The new separation uses shifts=0 and float32, unlike the lost earlier stem run.
These discrepancies demonstrate support instability across separation settings,
not proof that all 13 moments are false. Detector attacks themselves are estimates.
No nearest attack is automatically substituted or moved onto a selected note.

## Design evidence gaps

The rationale itself calls H1 and H5 gesture releases before the sustained band
ends; H2/H5/H6 may represent low-band leakage or harmonics. Those are not verified
performed hold releases or upper voices. Recurring rising-bin families do not
establish a melody's notes, phrase or foreground role. Adding chord/hold geometry
did not repair those missing musical correspondences.

## Next discriminating check

The independent paired run is now saved in `visual-clock-qa.json`. DOM minus
context medians were -3.33 ms at 1x and -17.33 ms at 2x. DOM minus extrapolated
browser output timestamp medians were +24.84 ms and +39.52 ms, respectively.
No accumulating drift or source resync occurred. Positive values mean visuals
ahead of browser-reported output, not late. Physical output and the user's
device were not measured, so this is not a perceptual-latency conclusion.

The user clarified that music and note hit sounds did not match, then explained
they had repeatedly viewed older drafts. A fresh musical review of the exact
latest draft is needed before attributing that symptom to revision 2. Do not
shift BPM, offset, the source audio or every note based on these comparisons.
Do not treat the existing grid/scheduling checks as musical approval.
