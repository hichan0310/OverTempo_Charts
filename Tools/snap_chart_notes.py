#!/usr/bin/env python3
"""Snap chart note starts and hold tails to an explicitly chosen beat grid."""

from __future__ import annotations

import argparse
import bisect
import json
import math
from pathlib import Path


def js_round(value: float) -> int:
    return math.floor(value + 0.5)


def tempo_segments(data: dict) -> list[tuple[int, float]]:
    timing = data.get("timing") or {}
    segments = [(0, float(timing["bpm"]))]
    for change in timing.get("bpmChanges", []):
        bpm = float(change.get("bpm", 0))
        if math.isfinite(bpm) and bpm > 0:
            segments.append((max(1, js_round(float(change.get("timeMs", 0)))), bpm))
    return sorted(dict(segments).items())


def snap_time(time_ms: float, segments: list[tuple[int, float]], divisor: int) -> int:
    starts = [start for start, _ in segments]
    index = max(0, bisect.bisect_right(starts, time_ms) - 1)
    start, bpm = segments[index]
    step_ms = 60000 / bpm / divisor
    tick = js_round((time_ms - start) / step_ms)
    return max(start, js_round(start + tick * step_ms))


def snap_chart(data: dict, divisor: int | None = None) -> dict:
    timing = data.get("timing") or {}
    selected_divisor = int(divisor or timing.get("snapDiv", 4))
    if selected_divisor <= 0:
        raise ValueError("snap divisor must be positive")
    timing["snapDiv"] = selected_divisor
    segments = tempo_segments(data)

    for note in data.get("notes", []):
        old_start = float(note.get("timeMs", note.get("time", 0)))
        duration = float(note.get("durationMs", note.get("duration", 0)) or 0)
        new_start = snap_time(old_start, segments, selected_divisor)
        note["timeMs"] = new_start
        if duration > 0:
            new_end = snap_time(old_start + duration, segments, selected_divisor)
            if new_end <= new_start:
                starts = [start for start, _ in segments]
                index = max(0, bisect.bisect_right(starts, new_start) - 1)
                step_ms = 60000 / segments[index][1] / selected_divisor
                new_end = js_round(new_start + step_ms)
            note["durationMs"] = new_end - new_start
        else:
            note["durationMs"] = 0

    keys = [(note["timeMs"], note["lane"]) for note in data.get("notes", [])]
    if len(keys) != len(set(keys)):
        raise ValueError("snapping creates duplicate notes in the same lane")
    return data


def iter_chart_paths(inputs: list[Path], excluded_song_dirs: set[str]):
    for item in inputs:
        paths = [item] if item.is_file() else sorted(item.rglob("*.4k-speedcoef.json"))
        for path in paths:
            if path.parent.name not in excluded_song_dirs:
                yield path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--snap-div", type=int)
    parser.add_argument("--exclude-song", action="append", default=[])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    paths = list(iter_chart_paths(args.inputs, set(args.exclude_song)))
    if args.snap_div and len(paths) != 1:
        parser.error("--snap-div requires exactly one chart file")

    changed_count = 0
    for path in paths:
        original = path.read_text(encoding="utf-8-sig")
        data = json.loads(original)
        snap_chart(data, args.snap_div)
        rendered = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        if rendered != original:
            changed_count += 1
            print(("off-grid" if args.check else "snapped") + f": {path}")
            if not args.check:
                path.write_text(rendered, encoding="utf-8")
    if args.check and changed_count:
        print(f"ERROR: {changed_count} chart(s) have notes off their declared grid")
        return 1
    print(f"checked {len(paths)} chart(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
