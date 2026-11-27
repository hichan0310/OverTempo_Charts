"""Plot unsnapped source attacks against the rejected chart; do not retime notes."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import librosa
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

repo = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(repo / "Tools/ai-chart"))
from analyze import describe_track

root = Path(__file__).parent
stem_root = repo / "Tools/ai-chart/output/chronomia-20261101/stems/htdemucs/4-03 Chronomia"
chart_path = repo / "Songs/Chronomia/Chronomia_AI_Upper_Rhythm_Holds_25-45.4k-speedcoef.json"
chart_bytes = chart_path.read_bytes()
chart = json.loads(chart_bytes)
plan = json.loads((root / "excerpt.plan.json").read_text())
original_path = repo / "Songs/Chronomia/Chronomia_Normal.4k-speedcoef.json"
original_bytes = original_path.read_bytes()
original = json.loads(original_bytes)
sources = {"mix": repo / "Songs/Chronomia/4-03 Chronomia.mp3",
           **{name: stem_root / f"{name}.wav" for name in ("other", "drums", "bass")}}
tracks = {}
samples = {}
for name, path in sources.items():
    tracks[name] = describe_track(path, 24.5, 21.0)
    samples[name], sr = librosa.load(path, sr=22050, offset=24.5, duration=21.0)

groups = {}
for note in chart["notes"]:
    groups.setdefault(note["timeMs"], []).append(note)
times = sorted(groups)
assert len(times) == len(plan["notes"])
rows = []
for time_ms, selection in zip(times, plan["notes"], strict=True):
    nearby = {}
    for name, track in tracks.items():
        attacks = track["attacks"]
        nearest = min(attacks, key=lambda event: abs(event["audioSec"] * 1000 - time_ms))
        nearby[name] = {"attackAudioMs": nearest["audioSec"] * 1000,
                        "chartMinusAttackMs": time_ms - nearest["audioSec"] * 1000,
                        "sourceLocalDetectorStrength": nearest["strength"]}
    rows.append({"chartMs": time_ms, "eventId": selection["eventId"],
                 "lanes": selection["lanes"], "focus": selection["focus"],
                 "durationsMs": [n["durationMs"] for n in groups[time_ms]],
                 "nearestUnsnappedDetectorAttacks": nearby})

windows = ((25.0, 28.8), (29.1, 31.9), (33.8, 37.1), (38.8, 42.3))
for number, (start, end) in enumerate(windows, 1):
    fig, axes = plt.subplots(4, 1, figsize=(19, 11), sharex=True)
    for ax, name in zip(axes[:2], ("mix", "other"), strict=True):
        y = samples[name]
        a, b = round((start - 24.5) * sr), round((end - 24.5) * sr)
        spectrum = np.abs(librosa.stft(y[a:b], n_fft=1024, hop_length=64))
        db = librosa.amplitude_to_db(spectrum, ref=np.max, top_db=65)
        ax.imshow(db, origin="lower", aspect="auto", cmap="magma",
                  extent=(start, end, 0, sr / 2), vmin=-65, vmax=0)
        ax.set_ylim(150, 7000)
        ax.set_ylabel(f"{name} Hz\nown dB scale")
    for name, color in (("mix", "black"), ("other", "tab:blue")):
        y = samples[name]
        frame = 44
        usable = len(y) // frame * frame
        envelope = np.sqrt(np.mean(y[:usable].reshape(-1, frame) ** 2, axis=1))
        seconds = 24.5 + (np.arange(len(envelope)) + .5) * frame / sr
        axes[2].plot(seconds, envelope, label=name, color=color, linewidth=.8)
        for attack in tracks[name]["attacks"]:
            if start <= attack["audioSec"] <= end:
                axes[3].vlines(attack["audioSec"], 0 if name == "mix" else 1,
                               .8 if name == "mix" else 1.8, color=color, linewidth=.8)
    axes[2].set_ylabel("absolute RMS")
    axes[2].legend(loc="upper right")
    axes[3].set_yticks((.4, 1.4), ("mix detector", "other detector"))
    axes[3].set_ylim(-.1, 2.0)
    for ax in axes:
        for time_ms in times:
            if start <= time_ms / 1000 <= end:
                ax.axvline(time_ms / 1000, color="red", alpha=.6, linewidth=.75)
        for time_ms in sorted({n["timeMs"] for n in original["notes"]}):
            if start <= time_ms / 1000 <= end:
                ax.axvline(time_ms / 1000, color="gray", alpha=.3, linewidth=.65,
                           linestyle=":")
        ax.set_xlim(start, end)
        ax.grid(axis="x", alpha=.2)
    axes[-1].set_xlabel("Unmodified original audio seconds, offset 0")
    fig.suptitle("Red: rejected revision starts; gray dotted: original chart reference, not truth\n"
                 "Detector lines are estimates, not certified musical onsets; no listening performed")
    fig.tight_layout()
    fig.savefig(root / f"timing-source-window-{number}.png", dpi=130)
    plt.close(fig)

result = {"scopeChartMs": [25000, 45000], "notes": rows,
          "rawSourceAttacks": {name: track["attacks"] for name, track in tracks.items()},
          "caveats": ["No listening performed.",
                      "Nearest detector attack is not proof of a corresponding musical voice.",
                      "No timestamp, source audio, chart or grid was changed.",
                      "Absolute RMS does not separate instruments.",
                      "Each spectrum uses its own dB reference; no cross-source dominance claim."]}
(root / "timing-source-measurements.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + "\n")
assert chart_path.read_bytes() == chart_bytes
assert original_path.read_bytes() == original_bytes
for source in ("mix", "other"):
    deltas = np.array([row["nearestUnsnappedDetectorAttacks"][source]["chartMinusAttackMs"]
                       for row in rows])
    print(source, {"min": float(deltas.min()), "median": float(np.median(deltas)),
                   "max": float(deltas.max()), "lateOver30ms": int((deltas > 30).sum())})
