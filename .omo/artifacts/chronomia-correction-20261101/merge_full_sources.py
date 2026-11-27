"""Merge independently measured full-song candidates without moving their times."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

repo = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(repo / "Tools/ai-chart"))
from analyze import snap_grid
from build import compile_chart

root = repo / "Tools/ai-chart/output/chronomia-20261101/analysis"
output = root.parent / "fullpack"
template_path = repo / "Songs/Chronomia/Chronomia_Normal.4k-speedcoef.json"
template_bytes = template_path.read_bytes()
template = json.loads(template_bytes.decode("utf-8-sig"))
inputs = [("upper", "upper.full.analysis.json")]
inputs += [(key, f"{key}.{part}.analysis.json")
           for key in ("drums", "bass") for part in ("front", "back")]
sources = []
members = defaultdict(list)
reviews = []
counts = Counter()
for source_key, name in inputs:
    path = root / name
    raw = path.read_bytes()
    analysis = json.loads(raw)
    for field, value in (("bpm", template["timing"]["bpm"]),
                         ("offsetMs", template["timing"].get("offsetMs", 0)),
                         ("bpmChanges", template["timing"].get("bpmChanges", []))):
        assert analysis["alignment"][field] == value, (path, field)
    assert analysis["alignment"]["allowedSubdivisionsPerBeat"] == [4]
    assert analysis["alignment"]["maxDeviationMs"] == 12
    sources.append({"sourceKey": source_key, "path": str(path),
                    "fileSha256": hashlib.sha256(raw).hexdigest(),
                    "analysisId": analysis["analysisId"],
                    "sourceAudio": analysis["sourceAudio"],
                    "sourceAudioSha256": analysis["sourceAudioSha256"],
                    "attackDetector": analysis["attackDetector"]})
    for event in analysis["events"]:
        in_chunk = (source_key == "upper"
                    or (name.endswith(".front.analysis.json") and event["chartMs"] < 74000)
                    or (name.endswith(".back.analysis.json") and event["chartMs"] >= 74000))
        if not in_chunk:
            continue
        assert not event.get("reviewRequired")
        assert event["chartMs"] == snap_grid(template["timing"], event["chartMs"], 4)["chartMs"]
        assert abs(event["deviationMs"]) <= 12
        assert abs(event["chartMs"] - event["audioMs"]
                   - template["timing"].get("offsetMs", 0)) < 1e-7
        assert abs(event["attackAudioMs"] + template["timing"].get("offsetMs", 0)
                   - event["chartMs"] - event["deviationMs"]) < 1e-7
        members[event["chartMs"]].append({
            "sourceKey": source_key, "sourceAnalysisId": analysis["analysisId"],
            "sourceEventId": event["id"], "originalEvent": copy.deepcopy(event)})
        counts[source_key] += 1
    for index, event in enumerate(analysis["reviewRequired"], 1):
        in_chunk = (source_key == "upper"
                    or (name.endswith(".front.analysis.json")
                        and event["attackChartMs"] < 74000)
                    or (name.endswith(".back.analysis.json")
                        and event["attackChartMs"] >= 74000))
        if in_chunk:
            reviews.append({"id": f"FR-{source_key}-{analysis['analysisId']}-{index:05d}",
                            "sourceKey": source_key,
                            "sourceAnalysisId": analysis["analysisId"],
                            "reviewRequired": True,
                            "originalReview": copy.deepcopy(event)})

events = []
priority = {"upper": 0, "drums": 1, "bass": 2}
for index, (chart_ms, parts) in enumerate(sorted(members.items()), 1):
    assert len({p["sourceKey"] for p in parts}) == len(parts), chart_ms
    parts.sort(key=lambda p: priority[p["sourceKey"]])
    reference = parts[0]["originalEvent"]
    event = {key: copy.deepcopy(reference[key])
             for key in ("chartMs", "audioMs", "attackAudioMs", "deviationMs",
                         "segmentIndex", "bpm", "bar", "beatInBar", "sub",
                         "beatKey", "subdivisionsPerBeat")}
    event.update({"id": f"FG{index:04d}", "sourceParts": parts,
                  "timingReference": {"sourceKey": parts[0]["sourceKey"],
                                      "sourceAnalysisId": parts[0]["sourceAnalysisId"],
                                      "sourceEventId": parts[0]["sourceEventId"]}})
    upper = [p for p in parts if p["sourceKey"] == "upper"]
    if upper:
        event["upperEvidence"] = copy.deepcopy(upper[0]["originalEvent"]["upperEvidence"])
    events.append(event)

identity = {"schema": "exact-time-source-union-v1", "windowChartMs": [0, 149817],
            "sources": sources, "events": events, "reviewRequired": reviews,
            "settings": {"subdivision": 4, "maxDeviationMs": 12,
                         "chunkCutChartMs": 74000,
                         "separation": "demucs4.0.1/htdemucs/shifts0/float32"}}
analysis_id = hashlib.sha256(json.dumps(identity, sort_keys=True,
                                        ensure_ascii=False).encode()).hexdigest()[:20]
upper_analysis = json.loads((root / "upper.full.analysis.json").read_text())
combined = {"schemaVersion": 1, "analysisId": analysis_id, "song": "Chronomia",
            "template": str(template_path), "sourceAudio": "composite separated source estimates",
            "sourceAudioSha256": None, "attackDetector": "source-specific; see provenance",
            "alignment": copy.deepcopy(upper_analysis["alignment"]),
            "events": events, "reviewRequired": reviews, "phrases": [],
            "sourceProvenance": sources, "mergeSettings": identity["settings"],
            "featureCaveat": "No listening. Source-local strengths are not cross-source dominance. "
                             "CQT bins include harmonics, not certified pitches or instruments. "
                             "Bass/drum-only events are not upper melody. Reviews are unselectable."}
assert sum(len(e["sourceParts"]) for e in events) == sum(counts.values())
assert len({e["id"] for e in events}) == len(events)
smoke, smoke_report = compile_chart(
    combined, {"schemaVersion": 1, "analysisId": analysis_id,
               "notes": [{"eventId": events[0]["id"], "lanes": [0]}]}, template)
assert smoke_report["valid"], smoke_report
for field in template:
    if field not in {"version", "meta", "difficulty", "editorSettings", "notes"}:
        assert smoke[field] == template[field], field
assert template_path.read_bytes() == template_bytes

output.mkdir(parents=True, exist_ok=True)
analysis_path = output / "full.analysis.json"
tsv_path = output / "full.events.tsv"
provenance_path = output / "PROVENANCE.md"
for path in (analysis_path, tsv_path, provenance_path):
    if path.exists():
        raise FileExistsError(path)
analysis_path.write_text(json.dumps(combined, ensure_ascii=False, indent=2) + "\n")
rows = ["id\tchartMs\tbar0\tbeat0\tsub\tsources\tupperOnset\tupperChange"
        "\trisingBins\tbeforeBins\tafterBins\tpositiveChange"]
for event in events:
    upper = [p["originalEvent"] for p in event["sourceParts"] if p["sourceKey"] == "upper"]
    evidence = event.get("upperEvidence", {})
    rows.append("\t".join(str(value) for value in (
        event["id"], event["chartMs"], event["bar"], event["beatInBar"], event["sub"],
        "+".join(p["sourceKey"] for p in event["sourceParts"]),
        upper[0]["onset"] if upper else "", evidence.get("spectralChange", ""),
        json.dumps(evidence.get("risingPitchEnergyBins", []), separators=(",", ":")),
        json.dumps(evidence.get("beforePitchEnergyBins", []), separators=(",", ":")),
        json.dumps(evidence.get("afterPitchEnergyBins", []), separators=(",", ":")),
        evidence.get("positiveChangeMagnitude", ""))))
tsv_path.write_text("\n".join(rows) + "\n")
provenance_path.write_text(
    f"# Full-song evidence rebuild, 2026-11-01\n\n"
    f"analysisId: `{analysis_id}`\n\n"
    f"{len(events)} union positions; {sum(counts.values())} contributions: {dict(counts)}. "
    f"{len(reviews)} source-specific reviews remain unselectable.\n\n"
    "The reboot removed the old temporary evidence. This is a new separation/analysis run, "
    "not a claimed byte-identical recovery. Demucs 4.0.1, htdemucs, shifts=0, float32; "
    "the source MP3 was not retimed. Original timing, offset, and acceleration remain fixed.\n\n"
    "Front [0,74s), back [74s,end) are selected from overlapping detector runs starting "
    "at 0s and 73s. All measured attacks and deviations remain in originalEvent. "
    "CQT energy-delta48-107-v2 is the recovered enrichment method. No transcription "
    "model, new pitch estimate or assumed melody register was imported.\n\n"
    "Positions are merged by exact chartMs only. A genuine upper, otherwise drum, "
    "otherwise bass contributor provides root timing. That priority is not dominance. "
    "Every contributor passed the existing snap_grid and chartMs=audioMs+offsetMs "
    "checks with subdivision 4 and maxDeviationMs 12. The compiler smoke test wrote "
    "no chart and preserved every other template field; the source hash is unchanged.\n\n"
    "Identity binds full inputs, source file hashes, membership, reviews and settings. "
    "No within-stem normalized strength is compared across sources. Root events have "
    "no invented aggregate strength or pitch label. originalReview is never selectable.\n\n"
    f"Template SHA-256: `{hashlib.sha256(template_bytes).hexdigest()}`\n\n"
    f"Inputs:\n```json\n{json.dumps(sources, indent=2)}\n```\n")
print(f"Wrote {analysis_id}: {len(events)} positions, {dict(counts)}, {len(reviews)} reviews")
