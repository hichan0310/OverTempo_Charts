# BMS audio restoration

Restored with `Tools/chart-editor/bms_audio_renderer.py`, using 44,100 Hz stereo
PCM16 WAV, a one-second tail, and peak attenuation only when necessary.
The JSON reports record every used sample's SHA-256 and the output hashes.
Source archives and the Python virtual environment are retained locally in
the ignored `.audio-work/` directory.

## Sources and results

### Elixir — Lime / Kankitsu

- [Official BOF:ET entry](https://manbow.nothing.sh/event/event.cgi?action=More_def&event=140&num=457)
- [Author-linked BMS archive](https://drive.google.com/file/d/1T0cMTPNkjgaq2n3ifWcicB9ZH5f2SItJ/view)
- Input: `Lime_Elixir_ogg/_Elixir_hyper7.bme`.
- Output: `Songs/Elixir/Elixir_BMS.wav`, 145.000 seconds.
- 7,410 audio events, 955 unique samples, no missing keysounds.
- This is the BMS version. The original OGG keysounds remain lossy sources;
  writing WAV avoids another lossy encode but does not restore lost frequencies.
- Audio and jacket are ready. `enabled: false` until a playable chart is authored.

### End Time — Cres

- [Official BOF 2006 entry](https://manbow.nothing.sh/event/event.cgi?action=More_def&event=36&num=81)
- Original `100sec.com/bms/endtime.zip` no longer returned a usable archive.
- [GENOSIDE individual-song mirror listing](https://www.bmsworld.nz/genoside-starter-pack-bms-pack/)
- [Downloaded BMS preservation copy](https://mega.nz/#!uEITkaLI!yHpDyxX02X7UfkfqJcBt4IrOIfk0Ll5Ff7powmt5pVc)
- Input: `[Cres.]endtime/end_time_h.bms` (author's hyper chart).
- Output: `Songs/End Time/End_Time_BMS.wav`, 133.650 seconds.
- 2,134 audio events, 336 unique samples, no missing keysounds.
- Windows tar warned about a final RAR metadata record; all referenced audio
  files and the chart extracted and decoded successfully.
- Existing `audio.mp3` is retained for comparison. Its decoded peak was 1.465;
  the restored WAV's peak is 0.980. No subjective listening test was performed.
- Cross-correlation on 8-second mono windows at 30, 60, 90 and 115 seconds
  estimated the restored recording to be 430–431 ms later than the old audio.
  Correlation was only 0.20–0.32 (the recordings differ); the 5-second window
  estimated 399 ms. Therefore the 430 ms correction is an automatic estimate,
  not a claim of sample-exact equivalence.
- Updated only the chart's audio filename and offset, from 449 to 19 ms.
  The editor uses `audioMs = chartMs - offsetMs`. All existing notes and other
  chart fields, including the user's pre-existing edits, are preserved.

### Change the Game — REDALiCE & USAO

- Source: user-provided `TCDR-0261 REDALiCE & USAO - Change the Game.zip`.
- Copied `Change the Game.wav` (vocal version, 182.080 seconds) and `jacket.png`
  byte-for-byte into `Songs/Change the Game/`.
- Audio and jacket are ready. `enabled: false` until a playable chart is authored.

## Reproduce

From the repository root (install `numpy soundfile scipy` in your Python environment):

```powershell
python Tools/chart-editor/bms_audio_renderer.py `
  .audio-work/elixir/Lime_Elixir_ogg/_Elixir_hyper7.bme `
  -o Songs/Elixir/Elixir_BMS.wav --report Tools/audio-restoration/elixir.report.json

python Tools/chart-editor/bms_audio_renderer.py `
  '.audio-work/endtime/[Cres.]endtime/end_time_h.bms' `
  -o 'Songs/End Time/End_Time_BMS.wav' --report Tools/audio-restoration/end-time.report.json
```

Only BMS/audio/image data was used from downloaded packages; package text was
not treated as instructions to run commands or alter the repository.
