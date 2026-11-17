# OverTempo AI Chart Lab (30-second pilot)

AI-assisted chart-pattern prototyping for **`hichan0310/OverTempo_Charts`**, not the Unity project. It generates editable `.4k-speedcoef.json` **drafts** with taps and optional holds; `.otchart` is a separate encrypted ARG release format and is never written here.

The existing `~/.omo/omo.jsonc` remains intact. The project `.omo/omo.jsonc` defines one additional category, `chart-design` (Opus 5.5), with a strict music/chart design brief. This does not replace the user's existing artistry/deep-high/deep-low assignments. In OmO Native or OpenCode, launch from the **OverTempo_Charts repository root** so project config and `file://` prompts resolve properly. Run `omo doctor` or `bunx oh-my-openagent doctor` if the category is missing.

## 1. Install (Linux / CachyOS)

```bash
cd OverTempo_Charts
python3 -m venv Tools/ai-chart/.venv
Tools/ai-chart/.venv/bin/python -m pip install -r Tools/ai-chart/requirements.txt
```

The `.venv/` and `output/` directories inside `Tools/ai-chart/` are ignored by the included scoped `.gitignore`. Prefer `/tmp/` for private analysis and draft outputs. Audio decoding of `.mp3` may require a system FFmpeg installation, depending on your codec setup.

## 2. Make 20-second event candidates

Use an **existing chart of the target song as a timing, metadata, and acceleration template**, even if its notes are incomplete or unrelated. It is not a source of note patterns. Check timing in the editor before analysis. The pipeline must preserve source `timing.bpm`, `timing.offsetMs`, and `timing.bpmChanges` exactly. Grids restart at every BPM marker, exactly as in the editor. `chartMs = audioMs + timing.offsetMs`.

Source acceleration settings are immutable too. Preserve the original top-level `autoCoef` and all special or legacy speed-limit and stage-delta settings, including `speedLimitLines` and `stageDeltaLines`. Don't change timing or acceleration settings to make a proposed pattern fit.

```bash
Tools/ai-chart/.venv/bin/python Tools/ai-chart/analyze.py \
  --chart 'Songs/Chronomia/Chronomia_Normal.4k-speedcoef.json' \
  --start-sec 25 --duration-sec 20 --subdivision 4 \
  --fine-subdivisions 6 8 --max-deviation-ms 20 \
  --mood-notes 'Describe what you hear in this section; e.g., a light melody and heavier percussion later' \
  --output /tmp/chronomia.analysis.json

Tools/ai-chart/.venv/bin/python Tools/ai-chart/visualize.py \
  --analysis /tmp/chronomia.analysis.json --output /tmp/chronomia.analysis.png
```

The default `subdivision=4` is the editor's `subdivisionsPerBeat=4`: four slots per beat, or sixteenth notes. Additional `fine_subdivisions=(6, 8)` allow 1/24 and 1/32 notes, respectively, when the audio supports them. The CLI exposes these as `--fine-subdivisions 6 8`; finer grids aren't a reason to add notes without an attack.

Analysis is **attack-first**: detect audio attacks, then match each to the coarsest allowed grid within `min(max_deviation_ms, grid_step_ms * 0.2)`. The default `max_deviation_ms` is 20, set with `--max-deviation-ms 20`. `audioMs` is the snapped grid position in audio time, while `attackAudioMs` is the observed attack position and `deviationMs` records the snapping difference. The compiler owns the conversion to `chartMs`.

Attack timestamps use a separate, short-window log-mel onset detector (512-sample
FFT, 64-sample hop) with one-second local normalization. It retains adjacent pitch
changes rather than suppressing them with a frequency maximum filter, and does
not use maxima of the descriptive linear-STFT band features. The detector
identity and candidate filters are recorded in `analysisId`, so plans from a
different detector, threshold, or event limit cannot be reused silently.
The detector identity is also stored in the analysis output.
The known-waveform regression checks both missing attacks and false late decay
notes, plus continuous pitch changes after a loud accent; it does not certify
synchronization for arbitrary music.

For an upper-layer design, analyze the separated `other.wav` explicitly with
`--audio` rather than treating mixed-audio attacks or bass off-beats as melody.
Such an analysis identifies the separated source in `sourceAudio`/its hash; the
compiled chart still preserves the template's original music filename. Separation
and onset detection remain estimates, and pitch/foreground claims need separate
evidence. Do not call the resulting chart upper-led merely because its name says
so.

Attacks that don't match stay in `reviewRequired`, outside selectable `events`. They are propagated to the generated `.review.json` for human inspection, not converted into off-grid notes.

The script automatically reads the audio named in `meta.audioFileName` from the same song folder. To override, add `--audio path/to/song.wav`.

For better source-specific information, first separate audio with Demucs **outside this toolkit** and use:

```bash
Tools/ai-chart/.venv/bin/python Tools/ai-chart/analyze.py \
  --chart 'Songs/Chronomia/Chronomia_Normal.4k-speedcoef.json' \
  --start-sec 25 --duration-sec 20 --stems-dir /path/to/demucs/song \
  --output /tmp/chronomia.stems.analysis.json
```

Stems directory convention: `drums.wav`, `bass.wav`, `vocals.wav`, `other.wav` (also `.mp3`, `.flac`, `.ogg`). The tool deliberately **does not** download tracks, automate copyrighted chart copying, or claim to recover exact original keysounds. It stores only feature summaries and source hashes. Source stem quality and musical meaning still need review.

## 3. Delegate chart design to Opus

Open `omo` from the **OverTempo_Charts root**. Give the main agent this task (or invoke `task(category: "chart-design", ...)` manually):

> Create three distinct and musically motivated 4-key pattern plans for `/tmp/chronomia.analysis.json` in `Tools/ai-chart/OPUS_PROMPT.md` format. Use `chart-design` (Opus 5.5) for creative pattern decisions and `deep-high` only for validation concerns. Compare the analysis PNG and my mood notes. Do not write into Songs, invent timestamps, or copy other mappers' patterns. Save `/tmp/chronomia.plan-a.json`, `plan-b.json`, `plan-c.json`. Then compile, validate, visualize, and report differences. Do not claim to have heard the original audio.

**Plan file schema:**

```json
{
  "schemaVersion": 1,
  "analysisId": "COPY_FROM_ANALYSIS_JSON",
  "designNotes": "e.g. sparse melodic taps -> denser two-hand bursts at the climax",
  "notes": [
    {"eventId": "E0001", "lanes": [0, 2], "motif": "jump", "focus": "strong attack"},
    {"eventId": "E0004", "lanes": [1], "motif": "stream", "focus": "melody"}
  ]
}
```

Copy `analysisId` exactly from the actual analysis JSON (the compiler rejects mismatches). Event IDs above are **illustrative**. Use only IDs from the actual analysis file's selectable `events`. Each chosen ID identifies a snapped grid position, not an LLM-generated time. Opus chooses event IDs, lanes, phrasing, difficulty, and pattern design only. The compiler rejects plan timing, explicit timestamps, and acceleration overrides, including `accelerate`.

For a supported sustained layer, add `"holdEnds": {"0": "E0004"}` to an entry
whose selected lanes include 0. Lane 0 then holds from that entry's event to
E0004; other selected lanes remain taps. Both references must be selectable,
on-grid and timing-reviewed. The endpoint must be later, and no note may start
inside the same lane's hold. Opus never supplies `durationMs`; the compiler
derives it from the two events. A hold endpoint is a phrase/gesture choice with
source evidence, not a certified transcription of acoustic note-off.

## 4. Compile and inspect (no overwrites)

```bash
Tools/ai-chart/.venv/bin/python Tools/ai-chart/build.py \
  --analysis /tmp/chronomia.analysis.json \
  --plan /tmp/chronomia.plan-a.json \
  --template 'Songs/Chronomia/Chronomia_Normal.4k-speedcoef.json' \
  --output /tmp/Chronomia_AI_Draft.4k-speedcoef.json

Tools/ai-chart/.venv/bin/python Tools/ai-chart/validate.py /tmp/Chronomia_AI_Draft.4k-speedcoef.json

Tools/ai-chart/.venv/bin/python Tools/ai-chart/visualize.py \
  --analysis /tmp/chronomia.analysis.json \
  --chart /tmp/Chronomia_AI_Draft.4k-speedcoef.json \
  --output /tmp/chronomia.chart-preview.png
```

`build.py` rejects existing targets, refuses overwriting the template, and blocks writes into encrypted song directories. Analysis/template alignment is checked inside `compile_chart`, not just by the CLI, so direct callers must meet the same source timing contract.

The compiler preserves the template's acceleration settings described above. At matching chart-time/lane coordinates, it also preserves the original per-note coefficient fields. New coordinates receive deterministic compiler coefficients, never Opus overrides. This preserves settings without copying source notes as patterns.

The generated chart records allowed grids in `aiChartGrid.subdivisionsPerBeat`. The validator checks **every note start and hold endpoint** against these editor-equivalent grids, restarting at each BPM marker and requiring exact integer positions computed with JavaScript `Math.round` semantics. Attack-matching tolerance does not permit off-grid output notes.

The generated `.review.json` includes unmatched attacks from `reviewRequired`, warnings, and approximate 2x-speed physical demands. It is *not* a reliable playability or quality score. It will not automatically run the Unity game.

To review in the existing browser editor, **manually copy** the new draft to a *non-ARG* song folder under `Songs/`, verify `meta.audioFileName`, then run `python Tools/chart-editor/server.py` and select the draft. Never replace an existing chart. For ARG songs, use a separate private unencrypted work folder to inspect drafts, and follow the established encryption/release process only after human approval.

## Interpretation limits / quality gate

1. Onset and band features identify **candidate musical attacks**, not isolated melody or keysound identity. A pitch-class estimate is not music transcription. Music mood should come from human listening notes or a separate capable audio understanding model; Opus cannot hear the file merely because it is stored locally.
2. Compare **three genuinely different patterns** for the same 20-second excerpt and test which has a better musical relationship and 2x hand feel. If attacks don't align, stop for human audio alignment inspection. This pipeline must not change source BPM, offset, BPM markers, or acceleration settings to resolve a mismatch; a separately corrected source needs fresh analysis.
3. Existing handmade charts are formatting and game-feel references, *not a gold-standard dataset*. Do not bulk ingest uncurated osu!mania charts or copy copyrighted charts into releases.
4. The preview plots and estimated statistics do not prove chart quality. A skilled 4K player must judge the final difficulty, awkwardness, and musical expression.

## Run unit tests

```bash
Tools/ai-chart/.venv/bin/python -m unittest discover -s Tools/ai-chart/tests -v
```
