#!/usr/bin/env python3
"""Structural chart checks and conservative 2x-speed playability heuristics."""
from __future__ import annotations

import argparse
import json
from bisect import bisect_right
from collections import Counter, defaultdict
from pathlib import Path

from analyze import snap_grid, timing_segments


def evaluate(chart: dict) -> dict:
    notes = chart.get("notes", [])
    errors: list[str] = []
    warnings: list[str] = []
    if chart.get("difficulty", {}).get("lanes") != 4:
        errors.append("difficulty.lanes must be 4")
    divisions = chart.get("aiChartGrid", {}).get("subdivisionsPerBeat", [4, 6, 8])
    timing = chart.get("timing", {})
    try:
        timing_segments(timing)
        if not divisions:
            raise ValueError("empty allowed subdivisions")
        for division in divisions:
            snap_grid(timing, 0, division)
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        errors.append(f"invalid timing/grid: {exc}")
    grid_ready = not errors
    off_grid = []
    off_grid_ends = []
    hold_count = 0
    seen = set()
    groups = defaultdict(list)
    lane_intervals = defaultdict(list)
    for i, n in enumerate(notes):
        t, lane, dur = n.get("timeMs"), n.get("lane"), n.get("durationMs", 0)
        if not isinstance(t, int) or isinstance(t, bool) or t < 0:
            errors.append(f"note {i}: invalid integer timeMs")
            continue
        if grid_ready and not any(snap_grid(timing, t, d)["chartMs"] == t for d in divisions):
            errors.append(f"note {i}: timeMs {t} is off grid")
            off_grid.append(i)
        if not isinstance(dur, int) or isinstance(dur, bool) or dur < 0:
            errors.append(f"note {i}: invalid integer durationMs")
            continue
        if dur > 0:
            hold_count += 1
            if grid_ready and not any(snap_grid(timing, t + dur, d)["chartMs"] == t + dur for d in divisions):
                errors.append(f"note {i}: hold endpoint {t + dur} is off grid")
                off_grid_ends.append(i)
        if not isinstance(lane, int) or isinstance(lane, bool) or lane not in range(4):
            errors.append(f"note {i}: invalid lane")
            continue
        if (t, lane) in seen:
            errors.append(f"note {i}: duplicate time/lane")
        seen.add((t, lane))
        groups[t].append(lane)
        lane_intervals[lane].append((t, t + dur))
    for lane, intervals in lane_intervals.items():
        occupied_until = -1
        for start, end in sorted(intervals):
            if start < occupied_until:
                errors.append(f"lane {lane}: note at {start}ms overlaps an existing hold")
            occupied_until = max(occupied_until, end)
    for t, lanes in groups.items():
        if len(lanes) > 4:
            errors.append(f"time {t}: over 4 notes")
    times = sorted(groups)
    lane_times = defaultdict(list)
    for t, lane in seen:
        lane_times[lane].append(t)
    for lane, lt in lane_times.items():
        st = sorted(lt)
        for a, b in zip(st, st[1:]):
            if (b - a) / 2 < 65:
                warnings.append(f"lane {lane}: {(b - a) / 2:.0f}ms same-lane gap at 2x around {a}ms")
    # Sliding 1s window on original timeline; at 2x the same notes arrive twice as fast.
    ordered = sorted(n["timeMs"] for n in notes if isinstance(n.get("timeMs"), int))
    peak_1x = 0
    peak_2x = 0
    for i, t in enumerate(ordered):
        peak_1x = max(peak_1x, bisect_right(ordered, t + 999) - i)
        # In real-time playback at 2x, 2000 ms of chart time passes in 1 s.
        peak_2x = max(peak_2x, bisect_right(ordered, t + 1999) - i)
    if peak_2x > 22:
        warnings.append(f"peak estimated {peak_2x} NPS at constant 2x (1x={peak_1x}); request skilled-player review")
    if len(times) >= 3:
        rapid = sum(b - a < 100 for a, b in zip(times, times[1:]))
        if rapid > len(times) * 0.25:
            warnings.append("high frequency of adjacent onsets under 100ms at chart speed")
    use = Counter(n["lane"] for n in notes if n.get("lane") in range(4))
    total = sum(use.values())
    if total and max(use.values(), default=0) / total > .42:
        warnings.append("one lane receives >42% of notes; check hand balance")
    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings[:30],
        "grid": {"checkedNotes": len(notes) if grid_ready else 0,
                 "offGridNoteIndices": off_grid, "subdivisionsPerBeat": divisions,
                 "checkedHoldEnds": hold_count if grid_ready else 0,
                 "offGridHoldEndIndices": off_grid_ends},
        "stats": {"notes": len(notes), "holds": hold_count, "attackMoments": len(times),
                  "chordRate": round(sum(len(v) > 1 for v in groups.values()) / max(1, len(times)), 3),
                  "laneDistribution": {str(lane): use[lane] for lane in range(4)},
                  "peakNps1x": peak_1x, "peakNps2xEstimated": peak_2x},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("chart", type=Path)
    args = parser.parse_args()
    data = json.loads(args.chart.read_text(encoding="utf-8"))
    result = evaluate(data)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
