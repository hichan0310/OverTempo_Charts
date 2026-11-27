"""Prepare full-song original-mix evidence without choosing chart notes."""
from __future__ import annotations

import copy
import hashlib
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

root = repo / "Tools/ai-chart/output/chronomia-20261101/fullpack"
source_path = root / "full.analysis.json"
source_bytes = source_path.read_bytes()
source = json.loads(source_bytes)
mix_path = repo / "Songs/Chronomia/4-03 Chronomia.mp3"
mix_hash = hashlib.sha256(mix_path.read_bytes()).hexdigest()
y, sr = librosa.load(mix_path, sr=22050)
duration = len(y) / sr
front = describe_track(mix_path, 0, 75)
back = describe_track(mix_path, 73, duration - 73)
attacks = [a for a in front["attacks"] if a["audioSec"] < 74]
attacks += [a for a in back["attacks"] if a["audioSec"] >= 74]
hop = 128
frame_seconds = hop / sr
energy = np.abs(librosa.cqt(y, sr=sr, hop_length=hop,
                           fmin=librosa.note_to_hz("C3"), n_bins=60))
events = copy.deepcopy(source["events"])
for event in events:
    second = event["attackAudioMs"] / 1000
    profiles = []
    for low, high in ((second - .030, second - .006), (second + .006, second + .030)):
        a = min(energy.shape[1] - 1, max(0, round(low / frame_seconds)))
        b = min(energy.shape[1], max(a + 1, round(high / frame_seconds)))
        profiles.append(energy[:, a:b].mean(axis=1))
    before, after = profiles
    norm_product = float(np.linalg.norm(before) * np.linalg.norm(after))
    spectral_valid = norm_product > 0
    cosine = float(np.dot(before, after)) / norm_product if spectral_valid else None
    rising = np.maximum(after - before, 0)
    magnitude = float(rising.sum())
    rising_valid = magnitude > 0
    if rising_valid:
        rising /= magnitude
    nearest = min(attacks, key=lambda attack: abs(attack["audioSec"] - second))
    upper_bins = event.get("upperEvidence", {}).get("risingPitchEnergyBins", [])
    event["mixVerification"] = {
        "nearestUnsnappedMixAttackAudioMs": nearest["audioSec"] * 1000,
        "chartMinusNearestMixAttackMs": event["chartMs"] - nearest["audioSec"] * 1000,
        "spectralComparisonValid": spectral_valid,
        "spectralChange": max(0, 1 - cosine) if cosine is not None else None,
        "positiveChangeMagnitude": magnitude,
        "positiveChangeValid": rising_valid,
        "risingPitchEnergyBins": [[int(i + 48), float(rising[i])]
                                  for i in np.argsort(rising)[-5:][::-1]] if rising_valid else [],
        "mixPositiveFractionAtUpperTop5Bins": float(
            sum(rising[index - 48] for index, _ in upper_bins)) if rising_valid else None}

identity = {"parentAnalysisId": source["analysisId"],
            "parentFileSha256": hashlib.sha256(source_bytes).hexdigest(),
            "mixSha256": mix_hash, "windowChartMs": [0, round(duration * 1000)],
            "method": "mix-cqt-change-48-107-24ms-v2-energy-validity; detector-front0-back73-cut74",
            "events": events, "unsnappedMixAttacks": attacks,
            "reviews": source["reviewRequired"]}
analysis_id = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:20]
result = copy.deepcopy(source)
result.update({"analysisId": analysis_id, "events": events,
               "unsnappedMixAttacks": attacks,
               "mixVerificationProvenance": {
                   key: value for key, value in identity.items()
                   if key not in {"events", "reviews", "unsnappedMixAttacks"}},
               "musicalVerificationStatus": "Not listened to. Frequency support and detector "
               "agreement do not certify voices, melody or note identity."})
analysis_path = root / "full-mix-v2.analysis.json"
tsv_path = root / "full-mix-v2.compact.tsv"
image_path = root / "original-mix-spectrum-v2.png"
for path in (analysis_path, tsv_path, image_path):
    if path.exists():
        raise FileExistsError(path)
analysis_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
rows = ["id\tms\tbar0\tbeat0\tsub\tsources\tupperOnset\tupperChange"
        "\tupperRise3\tmixDeltaMs\tmixChange\tmixRise3\tmixFractionAtUpper5"]
for event in events:
    upper = [p["originalEvent"] for p in event["sourceParts"] if p["sourceKey"] == "upper"]
    ue = event.get("upperEvidence", {})
    me = event["mixVerification"]
    rows.append("\t".join(str(value) for value in (
        event["id"], event["chartMs"], event["bar"], event["beatInBar"], event["sub"],
        "+".join(p["sourceKey"] for p in event["sourceParts"]),
        upper[0]["onset"] if upper else "", ue.get("spectralChange", ""),
        ",".join(str(index) for index, _ in ue.get("risingPitchEnergyBins", [])[:3]),
        round(me["chartMinusNearestMixAttackMs"], 2),
        round(me["spectralChange"], 4) if me["spectralChange"] is not None else "",
        ",".join(str(index) for index, _ in me["risingPitchEnergyBins"][:3]),
        round(me["mixPositiveFractionAtUpperTop5Bins"], 4)
        if me["mixPositiveFractionAtUpperTop5Bins"] is not None else "")))
tsv_path.write_text("\n".join(rows) + "\n")
db = librosa.amplitude_to_db(energy, ref=np.max, top_db=60)
fig, axes = plt.subplots(4, 1, figsize=(18, 13))
for ax, (start, end) in zip(axes, ((0, 40), (40, 80), (80, 120), (120, duration)), strict=True):
    a, b = round(start / frame_seconds), round(end / frame_seconds)
    ax.imshow(db[:, a:b], origin="lower", aspect="auto", cmap="magma",
              extent=(start, end, 47.5, 107.5), vmin=-60, vmax=0)
    ax.set_yticks((48, 60, 72, 84, 96))
    ax.set_ylabel("Frequency-energy bin\nnot performed pitch")
    ax.set_xlabel("Unmodified original audio seconds, offset 0")
fig.suptitle("Original-mix measured frequency energy; harmonics are not separate notes")
fig.tight_layout()
fig.savefig(image_path, dpi=120)
plt.close(fig)
assert source_path.read_bytes() == source_bytes
assert hashlib.sha256(mix_path.read_bytes()).hexdigest() == mix_hash
print(f"Wrote full-mix evidence {analysis_id}: {len(events)} candidates, "
      f"{len(attacks)} unsnapped mix attacks; no chart or pattern generated")
