"""Attach unmodified mix evidence to candidates, without selecting notes or lanes."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import librosa
import numpy as np

repo = Path(__file__).resolve().parents[3]
root = Path(__file__).parent
full_path = repo / "Tools/ai-chart/output/chronomia-20261101/fullpack/full.analysis.json"
full_bytes = full_path.read_bytes()
full = json.loads(full_bytes)
probe = json.loads((root / "timing-source-measurements.json").read_text())
mix_path = repo / "Songs/Chronomia/4-03 Chronomia.mp3"
mix_hash = hashlib.sha256(mix_path.read_bytes()).hexdigest()
y, sr = librosa.load(mix_path, sr=22050, offset=24.5, duration=21.0)
hop = 128
energy = np.abs(librosa.cqt(y, sr=sr, hop_length=hop,
                           fmin=librosa.note_to_hz("C3"), n_bins=60))
frame_seconds = hop / sr
events = copy.deepcopy([e for e in full["events"] if 25000 <= e["chartMs"] < 45000])
for event in events:
    second = event["attackAudioMs"] / 1000
    profiles = []
    for low, high in ((second - .030, second - .006), (second + .006, second + .030)):
        a = max(0, round((low - 24.5) / frame_seconds))
        b = min(energy.shape[1], max(a + 1, round((high - 24.5) / frame_seconds)))
        profiles.append(energy[:, a:b].mean(axis=1))
    before, after = profiles
    cosine = float(np.dot(before, after)) / max(
        float(np.linalg.norm(before) * np.linalg.norm(after)), 1e-12)
    rising = np.maximum(after - before, 0)
    rising_total = float(rising.sum())
    rising /= max(rising_total, 1e-12)
    nearest = min(probe["rawSourceAttacks"]["mix"],
                  key=lambda attack: abs(attack["audioSec"] - second))
    evidence = {
        "nearestUnsnappedMixAttackAudioMs": nearest["audioSec"] * 1000,
        "chartMinusNearestMixAttackMs": event["chartMs"] - nearest["audioSec"] * 1000,
        "spectralChange": max(0, 1 - cosine),
        "positiveChangeMagnitude": rising_total,
        "risingPitchEnergyBins": [[int(i + 48), float(rising[i])]
                                  for i in np.argsort(rising)[-5:][::-1]],
    }
    upper_bins = event.get("upperEvidence", {}).get("risingPitchEnergyBins", [])
    evidence["mixPositiveFractionAtUpperTop5Bins"] = float(
        sum(rising[index - 48] for index, _ in upper_bins))
    event["mixVerification"] = evidence

reviews = [review for review in full["reviewRequired"]
           if 25000 <= review["originalReview"]["attackChartMs"] < 45000]
identity = {"parentAnalysisId": full["analysisId"],
            "parentFileSha256": hashlib.sha256(full_bytes).hexdigest(),
            "windowChartMs": [25000, 45000], "mixSha256": mix_hash,
            "measurement": "mix-cqt-change-48-107-24ms-windows-v1",
            "unsnappedMixAttacks": probe["rawSourceAttacks"]["mix"],
            "events": events, "reviews": reviews}
analysis_id = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:20]
result = copy.deepcopy(full)
result.update({"analysisId": analysis_id, "events": events, "reviewRequired": reviews,
               "mixVerificationProvenance": {
                   key: value for key, value in identity.items()
                   if key not in {"events", "reviews", "unsnappedMixAttacks"}},
               "unsnappedMixAttacks": probe["rawSourceAttacks"]["mix"],
               "musicalVerificationStatus": "Unverified; no listening performed. "
               "Mix/source spectral agreement is not proof of a performed note or foreground voice."})
result["alignment"].update({"startAudioSec": 25.0, "durationSec": 20.0})
analysis_path = root / "rhythm.analysis.json"
tsv_path = root / "rhythm.events.tsv"
for path in (analysis_path, tsv_path):
    if path.exists():
        raise FileExistsError(path)
analysis_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
rows = ["id\tchartMs\tbar0\tbeat0\tsub\tsources\tupperOnset\tupperChange"
        "\tupperRisingBins\tmixAttackDeltaMs\tmixChange\tmixRisingBins\tmixFractionAtUpperTop5"]
for event in events:
    upper = [p["originalEvent"] for p in event["sourceParts"] if p["sourceKey"] == "upper"]
    ue = event.get("upperEvidence", {})
    me = event["mixVerification"]
    rows.append("\t".join(str(value) for value in (
        event["id"], event["chartMs"], event["bar"], event["beatInBar"], event["sub"],
        "+".join(p["sourceKey"] for p in event["sourceParts"]),
        upper[0]["onset"] if upper else "", ue.get("spectralChange", ""),
        json.dumps(ue.get("risingPitchEnergyBins", []), separators=(",", ":")),
        round(me["chartMinusNearestMixAttackMs"], 3),
        round(me["spectralChange"], 5),
        json.dumps(me["risingPitchEnergyBins"], separators=(",", ":")),
        round(me["mixPositiveFractionAtUpperTop5Bins"], 5))))
tsv_path.write_text("\n".join(rows) + "\n")
assert full_path.read_bytes() == full_bytes
assert hashlib.sha256(mix_path.read_bytes()).hexdigest() == mix_hash
print(f"Wrote rhythm evidence {analysis_id}: {len(events)} candidate positions, "
      f"{len(reviews)} unselectable reviews; no plan or chart generated")
