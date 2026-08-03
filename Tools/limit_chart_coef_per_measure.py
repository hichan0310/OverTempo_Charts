#!/usr/bin/env python3
"""Reduce coef-1 notes to one representative per beat and four per measure."""

from __future__ import annotations

import argparse
import bisect
import json
import math
from pathlib import Path


COEF_FIELDS = (
    "baseSpeedupCoef",
    "densitySpeedupCoefMultiplier",
    "rampSpeedupCoefMultiplier",
    "manualSpeedupCoefMultiplier",
    "autoSpeedupCoefMultiplier",
    "speedupCoef",
)


def choose_notes(data: dict) -> set[int]:
    timing = data["timing"]
    changes = sorted(timing.get("bpmChanges", []), key=lambda item: item["timeMs"])
    segment_starts = [0, *(int(item["timeMs"]) for item in changes)]
    segment_bpms = [float(timing["bpm"]), *(float(item["bpm"]) for item in changes)]

    # Match the editor grid: every BPM segment starts a fresh four-beat measure.
    measures: dict[tuple[int, int], dict[int, dict[int, list[int]]]] = {}
    for index, note in enumerate(data["notes"]):
        base_coef = note.get("baseSpeedupCoef", note.get("speedupCoef", 1))
        if float(base_coef) <= 0:
            continue
        time_ms = int(note["timeMs"])
        segment = bisect.bisect_right(segment_starts, time_ms) - 1
        beat_ms = 60_000 / segment_bpms[segment]
        relative_ms = max(0.0, time_ms - segment_starts[segment])
        measure = math.floor((relative_ms + 1e-7) / (beat_ms * 4))
        measure_start = segment_starts[segment] + measure * beat_ms * 4
        beat = max(0, min(3, math.floor((time_ms - measure_start) / beat_ms + 1e-7)))
        measures.setdefault((segment, measure), {}).setdefault(beat, {}).setdefault(
            time_ms, []
        ).append(index)

    selected: set[int] = set()
    for (segment, measure), beats in measures.items():
        beat_ms = 60_000 / segment_bpms[segment]
        measure_start = segment_starts[segment] + measure * beat_ms * 4
        for beat, events in beats.items():
            beat_start = measure_start + beat * beat_ms
            event_time = min(events, key=lambda time: (abs(time - beat_start), time))
            chord = events[event_time]
            target_lane = (segment + measure + beat) % 4
            representative = min(
                chord,
                key=lambda note_index: (
                    0 if data["notes"][note_index].get("durationMs", 0) > 0 else 1,
                    abs(data["notes"][note_index]["lane"] - target_lane),
                    data["notes"][note_index]["lane"],
                ),
            )
            selected.add(representative)
    return selected


def limit_chart(path: Path) -> tuple[int, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    selected = choose_notes(data)

    for index, note in enumerate(data["notes"]):
        if index in selected:
            continue
        for field in COEF_FIELDS:
            note[field] = 0

    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return len(selected), len(data["notes"]) - len(selected)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("chart", type=Path)
    args = parser.parse_args()
    coef_one, coef_zero = limit_chart(args.chart)
    print(f"updated {args.chart}: coef1={coef_one}, coef0={coef_zero}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
