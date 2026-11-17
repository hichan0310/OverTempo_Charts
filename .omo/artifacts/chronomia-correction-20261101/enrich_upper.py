"""Attach measured upper-source pitch-energy changes, not certified melody labels."""
import hashlib
import json
from pathlib import Path

import librosa
import matplotlib.pyplot as plt
import numpy as np

root = Path(__file__).resolve().parents[3] / "Tools/ai-chart/output/chronomia-20261101/analysis"
front = json.loads((root / "other.front.analysis.json").read_text())
back = json.loads((root / "other.back.analysis.json").read_text())
assert front["sourceAudioSha256"] == back["sourceAudioSha256"]
assert front["attackDetector"] == back["attackDetector"]
for field in ("bpm", "offsetMs", "bpmChanges", "allowedSubdivisionsPerBeat"):
    assert front["alignment"][field] == back["alignment"][field]
source = Path("/home/hichan/Projects/OverTempo_Charts/Tools/ai-chart/output/chronomia-20261101/stems/htdemucs/4-03 Chronomia/other.wav")
y, sr = librosa.load(source, sr=22050)
hop = 128
energy = np.abs(librosa.cqt(
    y, sr=sr, hop_length=hop, fmin=librosa.note_to_hz("C3"),
    n_bins=60, bins_per_octave=12))
frame_seconds = hop / sr
events = [e for e in front["events"] if e["chartMs"] < 74000]
events += [e for e in back["events"] if e["chartMs"] >= 74000]
events.sort(key=lambda e: e["chartMs"])
assert len({e["chartMs"] for e in events}) == len(events)
for index, event in enumerate(events, 1):
    event["id"] = f"E{index:04d}"
    second = event["attackAudioMs"] / 1000
    profiles = []
    raw_profiles = []
    top_bins = []
    for low, high in ((second - .030, second - .006), (second + .006, second + .030)):
        a = max(0, round(low / frame_seconds))
        b = min(energy.shape[1], max(a + 1, round(high / frame_seconds)))
        profile = energy[:, a:b].mean(axis=1)
        raw_profiles.append(profile.copy())
        profile /= max(float(profile.sum()), 1e-12)
        profiles.append(profile)
        top_bins.append([[int(i + 48), round(float(profile[i]), 4)]
                         for i in np.argsort(profile)[-5:][::-1]])
    before, after = profiles
    cosine = float(np.dot(before, after)) / max(float(np.linalg.norm(before) * np.linalg.norm(after)), 1e-12)
    event["sourceLayer"] = "demucs-other-estimate"
    event["upperEvidence"] = {
        "spectralChange": round(max(0, 1 - cosine), 5),
        "beforePitchEnergyBins": top_bins[0],
        "afterPitchEnergyBins": top_bins[1],
        "energyCentroidMidi": round(float(np.dot(np.arange(60) + 48, after)), 3),
    }
    upper_band = after[12:49]
    upper_fraction = float(upper_band.sum())
    upper_band = upper_band / max(upper_fraction, 1e-12)
    event["upperEvidence"]["upperBandEnergyFraction"] = round(upper_fraction, 4)
    event["upperEvidence"]["upperBandPitchEnergyBins"] = [
        [int(i + 60), round(float(upper_band[i]), 4)]
        for i in np.argsort(upper_band)[-5:][::-1]
    ]
    positive_change = np.maximum(raw_profiles[1] - raw_profiles[0], 0)
    positive_total = float(positive_change.sum())
    positive_change /= max(positive_total, 1e-12)
    event["upperEvidence"]["risingPitchEnergyBins"] = [
        [int(i + 48), round(float(positive_change[i]), 4)]
        for i in np.argsort(positive_change)[-5:][::-1]
    ]
    event["upperEvidence"]["positiveChangeMagnitude"] = round(positive_total, 6)
    rms_before = y[max(0, round((second - .030) * sr)):max(1, round((second - .006) * sr))]
    rms_after = y[max(0, round((second + .006) * sr)):round((second + .030) * sr)]
    event["upperEvidence"]["rmsBeforeAbsolute"] = round(float(np.sqrt(np.mean(rms_before**2))), 7)
    event["upperEvidence"]["rmsAfterAbsolute"] = round(float(np.sqrt(np.mean(rms_after**2))), 7)
review = [e for e in front["reviewRequired"] if e["attackAudioMs"] < 74000]
review += [e for e in back["reviewRequired"] if e["attackAudioMs"] >= 74000]
result = dict(front)
provenance = {"chunkIds": [front["analysisId"], back["analysisId"]],
              "cutChartMs": 74000, "evidence": "cqt-energy-delta48-107-v2"}
result["analysisId"] = hashlib.sha256(json.dumps(provenance, sort_keys=True).encode()).hexdigest()[:20]
result["alignment"] = dict(front["alignment"], durationSec=len(y) / sr)
result["events"] = events
result["reviewRequired"] = review
result["phrases"] = []
result["mergeProvenance"] = provenance
result["musicalFocusFromUser"] = "상부 선율, 질감; previous bass/drum-led A/B/C were rejected"
result["evidenceCaveat"] = (
    "No listening. CQT bins represent measured frequency energy including harmonics, "
    "not performed notes, isolated voices, certified melody or pitch height. "
    "Centroid is not melody pitch. All selectable attacks originate from the other "
    "stem itself. The MIDI60-96 measurement band is not a guaranteed melody range. "
    "No bass/drum event is substituted for a missing upper attack."
)
(root / "upper.full.analysis.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
db = librosa.amplitude_to_db(energy, ref=np.max, top_db=60)
fig, axes = plt.subplots(4, 1, figsize=(18, 13))
for ax, (low, high) in zip(axes, ((0, 40), (40, 80), (80, 120), (120, len(y) / sr))):
    a, b = round(low / frame_seconds), round(high / frame_seconds)
    ax.imshow(db[:, a:b], origin="lower", aspect="auto", cmap="magma",
              extent=[low, high, 47.5, 107.5], vmin=-60, vmax=0)
    ax.set_yticks([48, 60, 72, 84, 96], ["C3", "C4", "C5", "C6", "C7"])
    ax.set_xlabel("Original audio seconds (offset remains 0)")
    ax.set_title("Measured other-stem frequency energy; harmonics are not separate notes")
fig.tight_layout()
fig.savefig(root / "upper_full_spectrum.png", dpi=120)
plt.close(fig)
print(f"Wrote {len(events)} upper-source events and {len(review)} review attacks")
