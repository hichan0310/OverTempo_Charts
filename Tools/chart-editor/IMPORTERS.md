# OverTempo chart importers

These command-line tools create editable OverTempo base charts from existing
rhythm-game chart files. They do not copy or download audio.

## osu!mania

Native 4-key mania maps are accepted directly; 7K compression is opt-in.

```powershell
python .\Tools\chart-editor\osu_mania_to_overtempo.py `
  .\source.osu `
  -o .\output.4k-speedcoef.json
```

For a 7K source, compression must be requested explicitly:

```powershell
python .\Tools\chart-editor\osu_mania_to_overtempo.py `
  .\source-7k.osu `
  --fold-7k `
  -o .\output.4k-speedcoef.json
```

The importer preserves uninherited BPM changes, tap notes, and hold-note end
times. It normalizes the first osu! red timing point onto an OverTempo bar
line, stores the matching audio offset, and selects a sufficiently fine snap
division (up to 1/48) so imported notes line up with the editor grid. It
refuses non-mania and non-4K maps instead of guessing a lane conversion.

## BMS

```powershell
python .\Tools\chart-editor\bms_to_overtempo.py `
  .\source.bms `
  -o .\output.4k-speedcoef.json
```

Supported input extensions are `.bms`, `.bme`, and `.bml`. The parser supports:

- `#BPM`, extended `#BPMxx`, channel `03`, and channel `08`
- measure-length changes on channel `02`
- `#STOPxx` and channel `09`
- ordinary playable channels
- `#LNTYPE 1` long notes and `#LNOBJ`
- UTF-8 and common Japanese BMS encodings such as CP932

A native 4K BMS is detected automatically. For an unusual 4-lane layout,
explicitly list exactly four BMS channels:

```powershell
python .\Tools\chart-editor\bms_to_overtempo.py `
  .\source.bms `
  --channels 11,12,13,14 `
  -o .\output.4k-speedcoef.json
```

For a complete single-player 7K BMS, opt into proportional compression:

```powershell
python .\Tools\chart-editor\bms_to_overtempo.py `
  .\source-7k.bms `
  --fold-7k `
  -o .\output.4k-speedcoef.json
```

The 7K lane centres map left-to-right as `1,2→1`, `3→2`, `4,5→3`,
and `6,7→4`. Simultaneous taps in a merged lane become one tap, overlapping
holds become their interval union, and taps that fall inside the resulting
hold are removed. The converter reports every collapsed category. Folding is
never implicit, and 14K is still rejected.

## Tests

```powershell
Set-Location .\Tools\chart-editor
python -m unittest test_lane_fold.py test_bms_to_overtempo.py test_osu_mania_to_overtempo.py
```

## Render official BMS keysounds to audio

Install the two decoding/mixing dependencies once:

```powershell
python -m pip install numpy soundfile
```

Then render all BGM and playable keysounds referenced by a BMS chart:

```powershell
python .\Tools\chart-editor\bms_audio_renderer.py `
  .\official-package\chart.bms `
  -o .\rendered.wav
```

The renderer only reads the local official BMS package. It schedules channel
`01`, ordinary key channels, scratch channels, and long-note channels; mixes
overlapping samples; and prevents clipping. Missing `#WAVxx` files and
conditional `#RANDOM`/`#IF` charts are rejected instead of producing silently
incomplete audio.
