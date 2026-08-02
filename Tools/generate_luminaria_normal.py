#!/usr/bin/env python3
"""Build a four-key Luminaria draft from the imported osu!mania timing map.

The imported chart contributes musical-event times only. Its lane, chord, and hold
patterns are discarded; the four-key vocabulary and speed coefficients are tuned to
the Normal charts for End Time and Chronomia.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


BPM_CHANGES = [
    {"timeMs": 104140, "bpm": 197},
    {"timeMs": 105053, "bpm": 212},
    {"timeMs": 105902, "bpm": 227},
    {"timeMs": 107487, "bpm": 212},
    {"timeMs": 107770, "bpm": 227},
    {"timeMs": 110413, "bpm": 212},
    {"timeMs": 110696, "bpm": 227},
]

# Section start, end, selection mode.  At 227 BPM an even sixteenth mask is an
# eighth-note stream (7.57 objects/s); medium/dense add short sixteenth bursts.
SECTIONS = [
    (0, 18501, "intro"),
    (18501, 31189, "sparse"),
    (31189, 56563, "medium"),
    (56563, 66078, "sparse"),
    (66078, 91453, "dense"),
    (91453, 104140, "sparse"),
    (104140, 113867, "gimmick"),
    (113867, 120210, "sparse"),
    (120210, 140033, "medium"),
    (140033, 150000, "ending"),
]

TEMPO_ANCHORS = [
    (858, 227),
    (18501, 227),
    (31189, 227),
    (56563, 227),
    (66078, 227),
    (91453, 227),
    (104140, 197),
    (105053, 212),
    (105901, 227),
    (107487, 212),
    (107769, 227),
    (109091, 227),
    (110413, 212),
    (110694, 227),
    (113867, 227),
    (120210, 227),
    (140033, 227),
]

AUTO_SETTINGS = {
    "sigmaMs": 1600,
    "stepMs": 100,
    "minMultiplier": 0.8,
    "maxMultiplier": 1,
    "densityPower": 1.15,
    "rampGain": 0.05,
    "rampStartMultiplier": 1,
    "rampEndMultiplier": 1.05,
    "rampPower": 1.2,
    "cap": 1.1,
    "axisMax": 1.1,
    "showCurve": True,
    "anchors": "",
}

# Strong audio attacks missing from the imported timing map. Times are snapped to
# the local 1/16 grid after spectral-flux inspection of the actual MP3.
SUPPLEMENTAL_TIMES = {
    660, 726, 858,
    19757, 20549, 21342, 22135, 22928, 23721, 24250,
    60726, 61651, 62378, 62973, 63369, 64096,
    116642, 118360,
    148095,
}


def section_at(time_ms: int) -> tuple[int, int, str]:
    for section in SECTIONS:
        if section[0] <= time_ms < section[1]:
            return section
    return SECTIONS[-1]


def tempo_grid_at(time_ms: int) -> tuple[int, float, int]:
    anchor, bpm = TEMPO_ANCHORS[0]
    for candidate_anchor, candidate_bpm in TEMPO_ANCHORS:
        if candidate_anchor <= time_ms:
            anchor, bpm = candidate_anchor, candidate_bpm
        else:
            break
    step = 60000 / bpm / 4
    tick = round((time_ms - anchor) / step)
    return tick, abs((time_ms - anchor) / step - tick), round(step)


def selected_time(time_ms: int, source_notes: list[dict]) -> bool:
    start, _, mode = section_at(time_ms)
    if mode == "ending":
        return True

    tick, error, _ = tempo_grid_at(time_ms)
    phase = tick % 16
    bar = tick // 16
    even = phase % 2 == 0
    if mode == "intro":
        return True

    if mode == "sparse":
        keep = even
    elif mode == "medium":
        # One recurring three-hit flick per measure.
        burst_phase = 9 if bar % 2 == 0 else 13
        keep = even or phase == burst_phase
    elif mode == "dense":
        # Keep the recognizable short roll without exceeding an eighth-note
        # stream on average: one cluster replaces, rather than adds to, its beats.
        if bar % 4 == 0:
            keep = phase in {0, 1, 2, 3, 4, 8, 10, 12}
        elif bar % 2 == 0:
            keep = phase in {0, 1, 2, 4, 6, 8, 10, 12}
        else:
            keep = even
    else:  # The tempo-warp passage benefits from retaining its irregular attacks.
        keep = even or phase in {3, 11}

    # Do not retain isolated imported micro-offsets solely because of mask rounding.
    if error > 0.16:
        return False
    return keep and time_ms >= start


def build_notes(source: dict) -> list[dict]:
    groups: dict[int, list[dict]] = defaultdict(list)
    for note in source["notes"]:
        groups[round(note["timeMs"])].append(note)
    for time_ms in SUPPLEMENTAL_TIMES:
        groups.setdefault(time_ms, [])

    output: list[dict] = []
    lane_use: Counter = Counter()
    previous_lanes: set[int] = set()
    previous_time = -10000
    section_indices: Counter = Counter()
    chord_index = 0

    single_patterns = [
        (0, 1, 2, 3, 2, 1),
        (3, 2, 1, 0, 1, 2),
        (0, 2, 1, 3),
        (3, 1, 2, 0),
    ]
    chord_patterns = [(0, 3), (1, 2), (0, 1), (2, 3)]

    for time_ms in sorted(groups):
        source_notes = groups[time_ms]
        if time_ms not in SUPPLEMENTAL_TIMES and not selected_time(time_ms, source_notes):
            continue

        tick, _, _ = tempo_grid_at(time_ms)
        phase = tick % 16
        section_start, _, mode = section_at(time_ms)
        local_index = section_indices[section_start]
        bar = tick // 16

        chord = False
        if phase == 0:
            if mode in {"intro", "sparse"}:
                chord = True
            elif mode == "medium":
                chord = bar % 2 == 0
            elif mode == "dense":
                chord = bar % 4 == 0
            elif mode == "gimmick":
                chord = bar % 3 == 0

        if mode == "ending":
            lanes = (0, 1, 2, 3)
        elif chord:
            lanes = chord_patterns[chord_index % len(chord_patterns)]
            chord_index += 1
        else:
            pattern = single_patterns[bar % len(single_patterns)]
            lane = pattern[local_index % len(pattern)]
            if time_ms - previous_time <= 140 and lane in previous_lanes:
                available = [item for item in range(4) if item not in previous_lanes]
                lane = min(available, key=lambda item: (lane_use[item], abs(item - lane), item))
            lanes = (lane,)

        for position, lane in enumerate(lanes):
            base = 1
            if position > 0 and chord_index % 3 != 0:
                base = 0
            elif position == 0 and local_index % 4 == 3:
                base = 0
            output.append(
                {
                    "timeMs": time_ms,
                    "lane": lane,
                    "baseSpeedupCoef": base,
                    "durationMs": 0,
                }
            )
            lane_use[lane] += 1
        previous_time = time_ms
        previous_lanes = set(lanes)
        section_indices[section_start] += 1

    return sorted(output, key=lambda note: (note["timeMs"], note["lane"]))


def apply_double_staircases(notes: list[dict]) -> tuple[list[dict], list[int]]:
    """Overlay deliberate 01→12→23 / 23→12→01 motifs on playable runs."""
    groups: dict[int, list[dict]] = defaultdict(list)
    for note in notes:
        groups[note["timeMs"]].append(note)
    times = sorted(groups)

    def held_lanes_at(time_ms: int) -> set[int]:
        return {
            note["lane"]
            for note in notes
            if note["durationMs"] and note["timeMs"] < time_ms < note["timeMs"] + note["durationMs"]
        }

    ranges = [
        (24580, 31189, 4200),
        (91453, 104140, 5200),
        (118492, 140033, 6500),
    ]
    motif_starts: list[int] = []
    direction = 1
    for start, end, spacing in ranges:
        last = start - spacing
        candidates = [time_ms for time_ms in times if start <= time_ms < end]
        for index in range(len(candidates) - 2):
            triple = candidates[index:index + 3]
            if triple[0] - last < spacing:
                continue
            if not all(55 <= b - a <= 140 for a, b in zip(triple, triple[1:])):
                continue
            if any(any(note["durationMs"] for note in groups[time_ms]) for time_ms in triple):
                continue
            if any(held_lanes_at(time_ms) for time_ms in triple):
                continue

            pattern = [(0, 1), (1, 2), (2, 3)] if direction > 0 else [(2, 3), (1, 2), (0, 1)]
            for step_index, (time_ms, lanes) in enumerate(zip(triple, pattern)):
                old = groups[time_ms]
                primary_base = max(note["baseSpeedupCoef"] for note in old)
                groups[time_ms] = [
                    {
                        "timeMs": time_ms,
                        "lane": lane,
                        "baseSpeedupCoef": primary_base if lane == lanes[0] else (1 if step_index == 1 else 0),
                        "durationMs": 0,
                    }
                    for lane in lanes
                ]
            motif_starts.append(triple[0])
            direction *= -1
            last = triple[0]

    result = [note for time_ms in sorted(groups) for note in sorted(groups[time_ms], key=lambda item: item["lane"])]
    return result, motif_starts


def bridge_phrase_gaps(notes: list[dict], source: dict) -> tuple[list[dict], list[tuple[int, int]]]:
    """Carry sparse musical passages with holds instead of leaving dead air."""
    source_times = sorted({round(note["timeMs"]) for note in source["notes"]})
    groups: dict[int, list[dict]] = defaultdict(list)
    for note in notes:
        groups[note["timeMs"]].append(note)

    bridged: list[tuple[int, int]] = []
    bridge_index = 0
    for before, after in zip(source_times, source_times[1:]):
        gap = after - before
        if gap < 750 or before >= 140033:
            continue
        candidates = [time_ms for time_ms in groups if time_ms <= before and before - time_ms <= 150]
        if not candidates:
            continue
        start = max(candidates)
        group = groups[start]
        desired_end = after - min(264, max(90, gap // 8))
        duration = desired_end - start
        if duration < 400:
            continue

        note = sorted(group, key=lambda item: (item["durationMs"] > 0, abs(item["lane"] - (bridge_index % 4))))[0]
        held_lane = note["lane"]
        for time_ms in sorted(groups):
            if not start < time_ms < desired_end:
                continue
            later_group = groups[time_ms]
            for later_note in later_group:
                if later_note["lane"] != held_lane:
                    continue
                used = {item["lane"] for item in later_group}
                alternatives = [lane for lane in range(4) if lane != held_lane and lane not in used]
                if not alternatives:
                    desired_end = time_ms
                    break
                later_note["lane"] = min(alternatives, key=lambda lane: (abs(lane - held_lane), lane))
        duration = desired_end - start
        note["durationMs"] = max(note["durationMs"], duration)
        bridged.append((start, start + note["durationMs"]))
        bridge_index += 1

    result = [note for time_ms in sorted(groups) for note in sorted(groups[time_ms], key=lambda item: item["lane"])]
    return result, bridged


def shape_ending(notes: list[dict]) -> list[dict]:
    for note in notes:
        if note["timeMs"] == 140033 and note["lane"] in {0, 3}:
            note["durationMs"] = 148095 - 140033 - 264
    return notes


def interpolate(curve: list[dict], time_ms: int) -> dict:
    if time_ms <= curve[0]["timeMs"]:
        return curve[0]
    index = min(len(curve) - 1, max(1, math.ceil(time_ms / AUTO_SETTINGS["stepMs"])))
    before, after = curve[index - 1], curve[index]
    amount = (time_ms - before["timeMs"]) / max(1, after["timeMs"] - before["timeMs"])

    def lerp(field: str) -> float:
        return before[field] + (after[field] - before[field]) * amount

    return {field: lerp(field) for field in (
        "densityMultiplier", "rampMultiplier", "manualMultiplier", "finalUncapped", "multiplier"
    )}


def apply_auto_coefficients(notes: list[dict], duration_ms: int) -> tuple[list[dict], list[dict]]:
    settings = AUTO_SETTINGS
    sigma = settings["sigmaMs"]
    events = []
    for note in notes:
        duration = note["durationMs"]
        bpm = next(
            (bpm for anchor, bpm in reversed(TEMPO_ANCHORS) if anchor <= note["timeMs"]),
            TEMPO_ANCHORS[0][1],
        )
        beat_ms = 60000 / bpm
        weight = 1 + min(2, duration / beat_ms * 0.5)
        events.append((note["timeMs"] + duration * 0.5, weight))

    curve = []
    max_density = 0.0
    for time_ms in range(0, duration_ms + 1, settings["stepMs"]):
        density = sum(
            weight * math.exp(-0.5 * ((time_ms - event_time) / sigma) ** 2)
            for event_time, weight in events
            if abs(time_ms - event_time) <= sigma * 4
        )
        max_density = max(max_density, density)
        curve.append({"timeMs": time_ms, "density": density})

    for point in curve:
        density01 = point.pop("density") / max_density if max_density else 0
        difficulty01 = max(0, min(1, density01)) ** settings["densityPower"]
        density_multiplier = settings["minMultiplier"] + (
            settings["maxMultiplier"] - settings["minMultiplier"]
        ) * difficulty01
        position = max(0, min(1, point["timeMs"] / max(1, duration_ms)))
        ramp_multiplier = settings["rampStartMultiplier"] + (
            settings["rampEndMultiplier"] - settings["rampStartMultiplier"]
        ) * position ** settings["rampPower"]
        uncapped = density_multiplier * ramp_multiplier
        point.update(
            density01=density01,
            difficulty01=difficulty01,
            densityMultiplier=density_multiplier,
            rampMultiplier=ramp_multiplier,
            manualMultiplier=1.0,
            finalUncapped=uncapped,
            multiplier=max(0, min(settings["cap"], uncapped)),
        )

    final_notes = []
    for note in notes:
        base = note["baseSpeedupCoef"]
        point = interpolate(curve, note["timeMs"]) if base else None
        final_notes.append(
            {
                "timeMs": note["timeMs"],
                "lane": note["lane"],
                "baseSpeedupCoef": base,
                "densitySpeedupCoefMultiplier": round(point["densityMultiplier"], 6) if point else 0,
                "rampSpeedupCoefMultiplier": round(point["rampMultiplier"], 6) if point else 0,
                "manualSpeedupCoefMultiplier": 1 if point else 0,
                "autoSpeedupCoefMultiplier": round(point["multiplier"], 6) if point else 0,
                "speedupCoef": round(base * point["multiplier"], 6) if point else 0,
                "durationMs": note["durationMs"],
            }
        )

    clean_curve = []
    for point in curve:
        clean_curve.append(
            {
                "timeMs": point["timeMs"],
                "density01": round(point["density01"], 6),
                "difficulty01": round(point["difficulty01"], 6),
                "densityMultiplier": round(point["densityMultiplier"], 6),
                "rampMultiplier": round(point["rampMultiplier"], 6),
                "manualMultiplier": 1,
                "finalUncapped": round(point["finalUncapped"], 6),
                "multiplier": round(point["multiplier"], 6),
            }
        )
    return final_notes, clean_curve


def validate_playability(notes: list[dict]) -> int:
    groups: dict[int, list[dict]] = defaultdict(list)
    for note in notes:
        groups[note["timeMs"]].append(note)

    active: list[tuple[int, int]] = []
    max_fingers = 0
    for time_ms in sorted(groups):
        active = [(end, lane) for end, lane in active if end > time_ms]
        pressed = groups[time_ms]
        max_fingers = max(max_fingers, len(active) + len(pressed))
        if len(active) + len(pressed) > 4:
            raise ValueError(f"more than four keys required at {time_ms}ms")
        occupied = {lane for _, lane in active}
        if any(note["lane"] in occupied for note in pressed):
            raise ValueError(f"note overlaps an active hold lane at {time_ms}ms")
        for note in pressed:
            if note["durationMs"]:
                active.append((time_ms + note["durationMs"], note["lane"]))
    return max_fingers


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("Songs/Luminaria/Luminaria_osu_base.4k-speedcoef.json"))
    parser.add_argument("--output", type=Path, default=Path("Songs/Luminaria/Luminaria_Normal.4k-speedcoef.json"))
    args = parser.parse_args()

    source = json.loads(args.source.read_text(encoding="utf-8"))
    notes = build_notes(source)
    notes, double_staircases = apply_double_staircases(notes)
    notes, gap_holds = bridge_phrase_gaps(notes, source)
    notes = shape_ending(notes)
    max_fingers = validate_playability(notes)
    notes, curve = apply_auto_coefficients(notes, 149400)

    chart = {
        "version": 1,
        "meta": {
            "title": "Luminaria",
            "artist": "Lime",
            "source": "",
            "mapper": "Codex draft — End Time / Chronomia style",
            "previewStartMs": 66078,
            "previewEndMs": 81078,
            "extra": "Four-key Normal draft derived from the imported osu!mania timing reference.",
            "coverDataUrl": "",
            "audioFileName": "3-12 Luminaria.mp3",
        },
        "difficulty": {
            "name": "Normal",
            "level": 1,
            "scroll": 1,
            "baseSpeed": 1,
            "notes": "Short sixteenth-note bursts, same-side chords, and adjacent double staircases.",
            "lanes": 4,
        },
        "timing": {"bpm": 227, "offsetMs": 182, "snapDiv": 4, "bpmChanges": BPM_CHANGES},
        "editorSettings": {"encryptionEnabled": True, "encryptionArgId": "arg_luminaria"},
        "preview": {"startMs": 66078, "endMs": 81078},
        "speedLimitLines": [],
        "stageDeltaLines": [],
        "notes": notes,
        "autoCoef": {
            "schemaVersion": 1,
            "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "description": "Final speedupCoef = baseSpeedupCoef * autoSpeedupCoefMultiplier. Load restores editable coef 0/1 from baseSpeedupCoef.",
            "settings": AUTO_SETTINGS,
            "curve": curve,
        },
    }
    args.output.write_text(json.dumps(chart, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    groups = defaultdict(list)
    for note in notes:
        groups[note["timeMs"]].append(note)
    chords = Counter(len(group) for group in groups.values())
    holds = sum(note["durationMs"] > 0 for note in notes)
    positive = sum(note["baseSpeedupCoef"] > 0 for note in notes)
    print(f"wrote {args.output}")
    print(f"notes={len(notes)} objects={len(groups)} chords={dict(sorted(chords.items()))}")
    print(f"holds={holds} ({holds / len(notes):.1%}) speedup={positive} ({positive / len(notes):.1%})")
    print(f"double_staircases={len(double_staircases)} starts={double_staircases}")
    print(f"gap_holds={len(gap_holds)} spans={gap_holds}")
    print(f"maximum_simultaneous_fingers={max_fingers}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
