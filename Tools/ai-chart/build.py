#!/usr/bin/env python3
"""Compile an LLM event-selection plan into an editable OverTempo 4K draft."""
from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path

from analyze import snap_grid
from validate import evaluate

SUFFIX = ".4k-speedcoef.json"


def compile_chart(analysis: dict, plan: dict, template: dict) -> tuple[dict, dict]:
    if analysis.get("schemaVersion") != 1 or plan.get("schemaVersion") != 1:
        raise ValueError("analysis and plan must have schemaVersion=1")
    if analysis.get("analysisId") and plan.get("analysisId") != analysis["analysisId"]:
        raise ValueError("plan.analysisId does not match analysis; wrong song or time range")
    if template.get("difficulty", {}).get("lanes") != 4:
        raise ValueError("4 lanes required")
    if not isinstance(plan.get("notes"), list) or not plan["notes"]:
        raise ValueError("plan.notes must be a nonempty list")
    if set(plan) - {"schemaVersion", "analysisId", "designNotes", "notes"}:
        raise ValueError("plan cannot override source timing, grid, or acceleration settings")
    alignment = analysis["alignment"]
    timing = template["timing"]
    if any(alignment[key] != timing.get(key, default) for key, default in
           (("bpm", None), ("offsetMs", 0), ("bpmChanges", []))):
        raise ValueError("analysis/template timing mismatch; run analyze again")
    subdivisions = alignment.get("allowedSubdivisionsPerBeat", [alignment["subdivisionsPerBeat"]])
    source_notes = {(n["timeMs"], n["lane"]): n for n in template.get("notes", [])}
    events = {e["id"]: e for e in analysis["events"]}
    seen_events = set()
    # max one acceleration note per beat regardless of how many selected events/chords
    acceleration_beats = set()
    compiled = []
    for i, item in enumerate(sorted(plan["notes"], key=lambda n: events.get(n.get("eventId"), {}).get("chartMs", -1) if isinstance(n, dict) else -1)):
        if not isinstance(item, dict):
            raise ValueError(f"plan.notes[{i}] must be object")
        if set(item) - {"eventId", "lanes", "holdEnds", "motif", "focus"}:
            raise ValueError("plan notes may only select eventId, lanes, holdEnds, motif, and focus")
        event_id = item.get("eventId")
        if event_id not in events or event_id in seen_events:
            raise ValueError(f"unknown or repeated eventId: {event_id}")
        seen_events.add(event_id)
        lanes = item.get("lanes")
        if not isinstance(lanes, list) or not lanes or len(set(map(str, lanes))) != len(lanes) or len(lanes) > 4:
            raise ValueError(f"invalid lanes for {event_id}")
        if any(not isinstance(l, int) or isinstance(l, bool) or l not in (0, 1, 2, 3) for l in lanes):
            raise ValueError(f"lane must be integer 0..3 for {event_id}")
        hold_ends = item.get("holdEnds", {})
        if (not isinstance(hold_ends, dict)
                or set(hold_ends) - {str(lane) for lane in lanes}
                or any(not isinstance(ref, str) for ref in hold_ends.values())):
            raise ValueError(f"invalid holdEnds for {event_id}")
        checked = {}
        for ref in [event_id, *hold_ends.values()]:
            if ref not in events:
                raise ValueError(f"unknown hold endpoint: {ref}")
            candidate = events[ref]
            if candidate.get("reviewRequired"):
                raise ValueError(f"event requires timing review: {ref}")
            if not math.isclose(candidate["chartMs"], candidate["audioMs"] + alignment["offsetMs"],
                                rel_tol=0, abs_tol=1e-7):
                raise ValueError(f"event audio/chart time mismatch: {ref}")
            position = snap_grid(timing, candidate["chartMs"],
                                 candidate.get("subdivisionsPerBeat", alignment["subdivisionsPerBeat"]))
            if position["chartMs"] != candidate["chartMs"]:
                raise ValueError(f"event is off grid: {ref}")
            if position["subdivisionsPerBeat"] not in subdivisions:
                raise ValueError(f"event uses an undeclared subdivision: {ref}")
            tolerance = min(alignment.get("maxDeviationMs", 20),
                            60000 / position["bpm"] / position["subdivisionsPerBeat"] * .2)
            if abs(candidate.get("deviationMs", 0)) > tolerance:
                raise ValueError(f"event requires timing review: {ref}")
            checked[ref] = candidate, position
        e, position = checked[event_id]
        if any(checked[ref][0]["chartMs"] <= e["chartMs"] for ref in hold_ends.values()):
            raise ValueError(f"hold endpoint must be later than start: {event_id}")
        beat_id = position["beatKey"]
        requested = beat_id not in acceleration_beats
        if requested:
            acceleration_beats.add(beat_id)
        for lane_idx, lane in enumerate(sorted(lanes)):
            coef = 1 if requested and lane_idx == 0 else 0
            note = {"timeMs": e["chartMs"], "lane": lane,
                    "baseSpeedupCoef": coef,
                    "densitySpeedupCoefMultiplier": 1,
                    "rampSpeedupCoefMultiplier": 1,
                    "manualSpeedupCoefMultiplier": 1,
                    "autoSpeedupCoefMultiplier": 1,
                    "speedupCoef": coef,
                    "durationMs": (checked[hold_ends[str(lane)]][0]["chartMs"] - e["chartMs"]
                                   if str(lane) in hold_ends else 0)}
            # Reuse the source curve, never regenerate it from the AI's density.
            curve = template.get("autoCoef", {}).get("curve", [])
            if curve:
                point = curve[0] if e["chartMs"] <= curve[0]["timeMs"] else curve[-1]
                for a, b in zip(curve, curve[1:]):
                    if a["timeMs"] < e["chartMs"] <= b["timeMs"]:
                        k = (e["chartMs"] - a["timeMs"]) / max(1, b["timeMs"] - a["timeMs"])
                        point = {field: a.get(field, 0) + (b.get(field, 0) - a.get(field, 0)) * k
                                 for field in ("densityMultiplier", "rampMultiplier", "manualMultiplier", "multiplier")}
                        break
                for field, key in (("densityMultiplier", "densitySpeedupCoefMultiplier"),
                                   ("rampMultiplier", "rampSpeedupCoefMultiplier"),
                                   ("manualMultiplier", "manualSpeedupCoefMultiplier"),
                                   ("multiplier", "autoSpeedupCoefMultiplier")):
                    note[key] = round(point.get(field, 1), 6) if coef else 0
                note["speedupCoef"] = round(coef * note["autoSpeedupCoefMultiplier"], 6)
            original = source_notes.get((e["chartMs"], lane), {})
            for key in note:
                if key not in ("timeMs", "lane", "durationMs") and key in original:
                    note[key] = copy.deepcopy(original[key])
            compiled.append(note)
    compiled.sort(key=lambda n: (n["timeMs"], n["lane"]))
    chart = copy.deepcopy(template)
    chart["version"] = max(int(template.get("version", 2)), 2)
    chart.setdefault("meta", {})["mapper"] = "AI draft - human review required"
    chart["meta"]["extra"] = "AI-assisted draft. Timing and pattern QA required; source chart notes were not copied."
    chart.setdefault("difficulty", {})["name"] = "AI Draft"
    chart["difficulty"]["level"] = 0
    chart["difficulty"]["lanes"] = 4
    chart["difficulty"]["notes"] = "AI candidate; not rated"
    chart["editorSettings"] = {"encryptionEnabled": False, "argId": ""}
    chart["aiChartGrid"] = {"subdivisionsPerBeat": subdivisions}
    chart["notes"] = compiled
    report = evaluate(chart)
    report["reviewRequired"] = copy.deepcopy(analysis.get("reviewRequired", []))
    if report["reviewRequired"]:
        report["warnings"].append(f"{len(report['reviewRequired'])} audio attacks need timing review; excluded from notes")
    if not report["valid"]:
        raise ValueError("invalid generated chart: " + "; ".join(report["errors"]))
    return chart, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.output.name.endswith(SUFFIX):
        parser.error(f"output file must end in {SUFFIX}")
    report_path = args.output.with_suffix(".review.json")
    if args.output.resolve() == args.template.resolve() or args.output.exists() or report_path.exists():
        parser.error("refusing to overwrite a template, existing file, or review report")
    patch_path = args.output.parent / "song.patch.json"
    if patch_path.is_file() and json.loads(patch_path.read_text(encoding="utf-8")).get("encrypted") is True:
        parser.error("cannot put AI drafts in an ARG/encrypted song folder")
    a = json.loads(args.analysis.read_text(encoding="utf-8"))
    p = json.loads(args.plan.read_text(encoding="utf-8"))
    t = json.loads(args.template.read_text(encoding="utf-8-sig"))
    c, report = compile_chart(a, p, t)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output} ({len(c['notes'])} notes) and {report_path}")
    if report["warnings"]:
        print("WARNINGS:\n- " + "\n- ".join(report["warnings"]))


if __name__ == "__main__":
    main()
