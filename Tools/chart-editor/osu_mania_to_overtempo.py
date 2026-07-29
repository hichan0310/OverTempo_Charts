#!/usr/bin/env python3
"""Convert a native 4K osu!mania .osu file to OverTempo chart JSON."""

from __future__ import annotations

import argparse
import json
import math
import re
from bisect import bisect_right
from pathlib import Path

from lane_fold import fold_notes


SUPPORTED_SNAP_DIVISORS = (1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48)


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "cp932", "utf-8"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace")


def sections(text: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    current = ""
    for source_line in text.splitlines():
        line = source_line.strip()
        if not line or line.startswith("//"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            result.setdefault(current, [])
        elif current:
            result[current].append(line)
    return result


def key_values(lines: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in lines:
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
    return result


def make_note(time_ms: int, lane: int, duration_ms: int = 0) -> dict:
    return {
        "timeMs": max(0, time_ms),
        "lane": lane,
        "baseSpeedupCoef": 1,
        "densitySpeedupCoefMultiplier": 1,
        "rampSpeedupCoefMultiplier": 1,
        "manualSpeedupCoefMultiplier": 1,
        "autoSpeedupCoefMultiplier": 1,
        "speedupCoef": 1,
        "durationMs": max(0, duration_ms),
    }


def infer_snap_divisor(
    notes: list[dict],
    timing_points: list[tuple[int, float]],
    chart_shift_ms: int,
    editor_divisor: int,
) -> int:
    """Find the smallest supported grid at least as fine as osu!'s editor grid."""
    transformed = [
        (time_ms + chart_shift_ms, bpm) for time_ms, bpm in timing_points
    ]
    starts = [time_ms for time_ms, _ in transformed]
    positions = [
        position
        for note in notes
        for position in (
            [note["timeMs"]]
            if not note["durationMs"]
            else [note["timeMs"], note["timeMs"] + note["durationMs"]]
        )
    ]

    candidates = [
        divisor
        for divisor in SUPPORTED_SNAP_DIVISORS
        if divisor >= editor_divisor and divisor % editor_divisor == 0
    ]
    if not candidates:
        candidates = [editor_divisor]

    for divisor in candidates:
        fits = True
        for position in positions:
            index = max(0, bisect_right(starts, position) - 1)
            segment_start, bpm = transformed[index]
            step_ms = 60000 / bpm / divisor
            units = (position - segment_start) / step_ms
            error_ms = abs(units - round(units)) * step_ms
            if error_ms > 1.1:
                fits = False
                break
        if fits:
            return divisor
    return candidates[-1]


def chart_shift_for_first_timing(first_timing_ms: int, bpm: float) -> int:
    """Place the first osu! red line on the earliest non-negative bar line."""
    if first_timing_ms <= 0:
        return -first_timing_ms
    bar_ms = 60000 / bpm * 4
    target_bar = math.ceil(first_timing_ms / bar_ms) * bar_ms
    return round(target_bar - first_timing_ms)


def convert_osu(path: Path, *, fold_7k: bool = False) -> dict:
    parsed = sections(read_text(path))
    general = key_values(parsed.get("General", []))
    difficulty = key_values(parsed.get("Difficulty", []))
    metadata = key_values(parsed.get("Metadata", []))
    editor = key_values(parsed.get("Editor", []))

    if int(float(general.get("Mode", "-1"))) != 3:
        raise ValueError("source is not an osu!mania chart (Mode must be 3)")
    keys = int(round(float(difficulty.get("CircleSize", "0"))))
    if keys != 4 and not (fold_7k and keys == 7):
        suffix = "; pass --fold-7k for a 7K source" if keys == 7 else ""
        raise ValueError(f"source is {keys}K, not native 4K{suffix}")

    timing_points: list[tuple[int, float]] = []
    for line in parsed.get("TimingPoints", []):
        fields = line.split(",")
        if len(fields) < 2:
            continue
        time_ms = round(float(fields[0]))
        beat_length = float(fields[1])
        uninherited = len(fields) < 7 or fields[6] == "1"
        if uninherited and beat_length > 0:
            bpm = 60000 / beat_length
            if math.isfinite(bpm) and bpm > 0:
                timing_points.append((time_ms, bpm))
    timing_points.sort()
    if not timing_points:
        raise ValueError("source has no valid uninherited timing point")

    # OverTempo's grid starts at chart time 0, while osu! timing points are
    # expressed in audio time. Move the first red timing point to the earliest
    # non-negative bar line and preserve audio playback using offsetMs:
    #
    #   audioMs = chartMs - offsetMs
    #
    # Without this normalization the notes still sound at the right time, but
    # the editor grid is phase-shifted by the first osu! timing-point offset.
    # Moving to a bar rather than always moving to 0 also keeps any audio intro
    # visible on the non-negative OverTempo timeline.
    first_timing_ms = timing_points[0][0]
    base_bpm = timing_points[0][1]
    chart_shift_ms = chart_shift_for_first_timing(first_timing_ms, base_bpm)
    bpm_changes = [
        {"timeMs": time_ms + chart_shift_ms, "bpm": bpm}
        for time_ms, bpm in timing_points[1:]
        if time_ms + chart_shift_ms >= 0
    ]

    notes: list[dict] = []
    for line in parsed.get("HitObjects", []):
        fields = line.split(",")
        if len(fields) < 5:
            continue
        x = int(fields[0])
        time_ms = round(float(fields[2])) + chart_shift_ms
        object_type = int(fields[3])
        lane = max(0, min(keys - 1, x * keys // 512))
        duration = 0
        if object_type & 128:
            if len(fields) < 6:
                continue
            end_text = fields[5].split(":", 1)[0]
            duration = max(
                0,
                round(float(end_text)) + chart_shift_ms - time_ms,
            )
        notes.append(make_note(time_ms, lane, duration))

    notes.sort(key=lambda note: (note["timeMs"], note["lane"]))
    seen: set[tuple[int, int]] = set()
    deduped: list[dict] = []
    for note in notes:
        key = (note["timeMs"], note["lane"])
        if key not in seen:
            seen.add(key)
            deduped.append(note)
    fold_summary = ""
    if fold_7k:
        deduped, fold_stats = fold_notes(deduped, 7)
        fold_summary = f"; {fold_stats.summary(7)}"

    beat_divisor = int(float(editor.get("BeatDivisor", "4")))
    editor_divisor = (
        beat_divisor if beat_divisor in SUPPORTED_SNAP_DIVISORS else 4
    )
    snap_div = infer_snap_divisor(
        deduped,
        timing_points,
        chart_shift_ms,
        editor_divisor,
    )
    version = metadata.get("Version", "osu!mania Base")
    source_preview_ms = int(float(general.get("PreviewTime", "0")))
    chart_preview_ms = max(0, source_preview_ms + chart_shift_ms)
    return {
        "version": 2,
        "meta": {
            "title": metadata.get("TitleUnicode") or metadata.get("Title", path.stem),
            "artist": metadata.get("ArtistUnicode") or metadata.get("Artist", ""),
            "source": metadata.get("Source", ""),
            "mapper": metadata.get("Creator", ""),
            "previewStartMs": chart_preview_ms,
            "previewEndMs": max(
                15000, chart_preview_ms + 15000
            ),
            "extra": (
                f"Imported from osu!mania {path.name}; "
                f"difficulty {version}; BeatmapID {metadata.get('BeatmapID', '')}; "
                f"BeatmapSetID {metadata.get('BeatmapSetID', '')}; "
                f"first timing point {first_timing_ms}ms"
                f"{fold_summary}"
            ),
            "coverDataUrl": "",
            "audioFileName": general.get("AudioFilename", ""),
        },
        "difficulty": {
            "name": version,
            "level": round(float(difficulty.get("OverallDifficulty", "1")), 2),
            "scroll": 1,
            "baseSpeed": 1,
            "notes": "",
            "lanes": 4,
        },
        "timing": {
            "bpm": base_bpm,
            "offsetMs": chart_shift_ms,
            "snapDiv": snap_div,
            "bpmChanges": bpm_changes,
        },
        "editorSettings": {"encryptionEnabled": False, "argId": ""},
        "preview": {
            "startMs": chart_preview_ms,
            "endMs": max(
                15000, chart_preview_ms + 15000
            ),
        },
        "speedLimitLines": [],
        "stageDeltaLines": [],
        "notes": deduped,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument(
        "--fold-7k",
        action="store_true",
        help="compress a 7K chart to 4K using lane-union semantics",
    )
    args = parser.parse_args()
    output = args.output or args.input.with_name(
        re.sub(r'[\\/:*?"<>|]+', "_", args.input.stem)
        + "_osu.4k-speedcoef.json"
    )
    chart = convert_osu(args.input, fold_7k=args.fold_7k)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(chart, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {output} ({len(chart['notes'])} notes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
