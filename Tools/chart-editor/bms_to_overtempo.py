#!/usr/bin/env python3
"""Convert a 4-key BMS chart to an OverTempo chart JSON.

Supported timing features:
  * #BPM and #BPMxx / channel 08 BPM changes
  * channel 03 hexadecimal BPM changes
  * channel 02 variable measure lengths
  * #STOPxx / channel 09 stops (baked into subsequent timestamps)

Supported note features:
  * normal playable channels (1x)
  * long-note channels (5x, LNTYPE 1 alternating endpoints)
  * #LNOBJ endpoints on normal playable channels

The converter normally requires native 4K. Pass --fold-7k to proportionally
compress a single-player 7K chart into four lanes using union semantics for
colliding taps and long notes.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Iterable

from lane_fold import fold_notes


BASE36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
HEADER_RE = re.compile(r"^#([A-Z0-9]+)(?:\s+|:)(.*)$", re.IGNORECASE)
MEASURE_RE = re.compile(r"^#(\d{3})([0-9A-Z]{2}):(.*)$", re.IGNORECASE)
P1_KEYS = ("11", "12", "13", "14", "15", "18", "19")
P2_KEYS = ("21", "22", "23", "24", "25", "28", "29")
PLAYABLE_KEYS = P1_KEYS + P2_KEYS


def base36(value: str) -> int:
    value = value.strip().upper()
    if not value or any(char not in BASE36 for char in value):
        raise ValueError(f"invalid base-36 value: {value!r}")
    result = 0
    for char in value:
        result = result * 36 + BASE36.index(char)
    return result


def read_bms_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "cp932", "utf-8"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            pass
    return raw.decode("cp932", errors="replace")


@dataclass(frozen=True, order=True)
class Position:
    measure: int
    fraction: Fraction


@dataclass(frozen=True)
class RawObject:
    position: Position
    channel: str
    value: str


@dataclass
class ParsedBms:
    headers: dict[str, str]
    measure_lengths: dict[int, Fraction]
    objects: list[RawObject]
    bpm_refs: dict[str, float]
    stop_refs: dict[str, Fraction]


def parse_bms(text: str) -> ParsedBms:
    headers: dict[str, str] = {}
    measure_lengths: dict[int, Fraction] = {}
    objects: list[RawObject] = []
    bpm_refs: dict[str, float] = {}
    stop_refs: dict[str, Fraction] = {}

    for line_number, source_line in enumerate(text.splitlines(), 1):
        line = source_line.strip()
        if not line or not line.startswith("#"):
            continue

        measure_match = MEASURE_RE.match(line)
        if measure_match:
            measure = int(measure_match.group(1))
            channel = measure_match.group(2).upper()
            data = re.sub(r"\s+", "", measure_match.group(3)).upper()
            if channel == "02":
                try:
                    measure_lengths[measure] = Fraction(data)
                except (ValueError, ZeroDivisionError) as exc:
                    raise ValueError(
                        f"line {line_number}: invalid measure length {data!r}"
                    ) from exc
                continue
            if not data:
                continue
            if len(data) % 2:
                raise ValueError(
                    f"line {line_number}: channel data must contain 2-character objects"
                )
            count = len(data) // 2
            for index in range(count):
                value = data[index * 2 : index * 2 + 2]
                if value != "00":
                    objects.append(
                        RawObject(
                            Position(measure, Fraction(index, count)),
                            channel,
                            value,
                        )
                    )
            continue

        header_match = HEADER_RE.match(line)
        if not header_match:
            continue
        key = header_match.group(1).upper()
        value = header_match.group(2).strip()
        if key.startswith("BPM") and len(key) == 5:
            try:
                bpm_refs[key[3:]] = float(value)
            except ValueError as exc:
                raise ValueError(f"line {line_number}: invalid {key} value") from exc
        elif key.startswith("STOP") and len(key) == 6:
            try:
                stop_refs[key[4:]] = Fraction(value)
            except (ValueError, ZeroDivisionError) as exc:
                raise ValueError(f"line {line_number}: invalid {key} value") from exc
        else:
            headers[key] = value

    return ParsedBms(headers, measure_lengths, objects, bpm_refs, stop_refs)


class Timeline:
    def __init__(self, parsed: ParsedBms):
        self.parsed = parsed
        self.measure_starts: dict[int, Fraction] = {0: Fraction(0)}
        max_measure = max(
            [0, *parsed.measure_lengths.keys(), *(obj.position.measure for obj in parsed.objects)]
        )
        beat = Fraction(0)
        for measure in range(max_measure + 2):
            self.measure_starts[measure] = beat
            beat += Fraction(4) * parsed.measure_lengths.get(measure, Fraction(1))

        self.initial_bpm = float(parsed.headers.get("BPM", "120"))
        if not math.isfinite(self.initial_bpm) or self.initial_bpm <= 0:
            raise ValueError("#BPM must be a positive finite number")

        timing_by_beat: dict[Fraction, list[tuple[str, float | Fraction]]] = {}
        for obj in parsed.objects:
            beat_position = self.beat_of(obj.position)
            if obj.channel == "03":
                bpm = float(int(obj.value, 16))
                if bpm > 0:
                    timing_by_beat.setdefault(beat_position, []).append(("bpm", bpm))
            elif obj.channel == "08":
                bpm = parsed.bpm_refs.get(obj.value)
                if bpm is None:
                    raise ValueError(f"undefined #BPM{obj.value}")
                if bpm <= 0 or not math.isfinite(bpm):
                    raise ValueError(f"#BPM{obj.value} must be positive and finite")
                timing_by_beat.setdefault(beat_position, []).append(("bpm", bpm))
            elif obj.channel == "09":
                stop = parsed.stop_refs.get(obj.value)
                if stop is None:
                    raise ValueError(f"undefined #STOP{obj.value}")
                timing_by_beat.setdefault(beat_position, []).append(("stop", stop))

        self._points: list[tuple[Fraction, float, float]] = []
        current_beat = Fraction(0)
        current_ms = float(parsed.headers.get("OFFSET", "0")) * 1000
        current_bpm = self.initial_bpm
        self.bpm_changes: list[dict[str, float | int]] = []
        self.stop_count = 0

        for beat_position in sorted(timing_by_beat):
            current_ms += float(beat_position - current_beat) * 60000 / current_bpm
            current_beat = beat_position
            for kind, value in timing_by_beat[beat_position]:
                if kind == "bpm":
                    current_bpm = float(value)
                    self.bpm_changes.append(
                        {"timeMs": round(current_ms), "bpm": current_bpm}
                    )
                else:
                    # BMS STOP units are 1/192 of a four-beat measure.
                    current_ms += float(value) / 192 * 4 * 60000 / current_bpm
                    self.stop_count += 1
            self._points.append((current_beat, current_ms, current_bpm))

        if self.bpm_changes and self.bpm_changes[0]["timeMs"] == round(
            float(parsed.headers.get("OFFSET", "0")) * 1000
        ):
            self.initial_bpm = float(self.bpm_changes[0]["bpm"])
            self.bpm_changes.pop(0)

    def beat_of(self, position: Position) -> Fraction:
        length = self.parsed.measure_lengths.get(position.measure, Fraction(1))
        return self.measure_starts[position.measure] + Fraction(4) * length * position.fraction

    def milliseconds(self, position: Position) -> float:
        target = self.beat_of(position)
        beat = Fraction(0)
        ms = float(self.parsed.headers.get("OFFSET", "0")) * 1000
        bpm = float(self.parsed.headers.get("BPM", "120"))
        for point_beat, point_ms, point_bpm in self._points:
            if point_beat > target:
                break
            beat, ms, bpm = point_beat, point_ms, point_bpm
        return ms + float(target - beat) * 60000 / bpm


def normal_channel(channel: str) -> str | None:
    return channel if channel in PLAYABLE_KEYS else None


def long_channel_to_normal(channel: str) -> str | None:
    if len(channel) != 2 or channel[0] not in {"5", "6"}:
        return None
    candidate = ("1" if channel[0] == "5" else "2") + channel[1]
    return candidate if candidate in PLAYABLE_KEYS else None


def active_channels(parsed: ParsedBms) -> list[str]:
    found: set[str] = set()
    for obj in parsed.objects:
        channel = normal_channel(obj.channel) or long_channel_to_normal(obj.channel)
        if channel:
            found.add(channel)
    return [channel for channel in PLAYABLE_KEYS if channel in found]


def parse_channel_selection(value: str) -> list[str]:
    channels = [part.strip().upper() for part in value.split(",") if part.strip()]
    if len(channels) != 4 or len(set(channels)) != 4:
        raise argparse.ArgumentTypeError("--channels requires four unique channels")
    invalid = [channel for channel in channels if channel not in PLAYABLE_KEYS]
    if invalid:
        raise argparse.ArgumentTypeError(
            f"unsupported playable channel(s): {', '.join(invalid)}"
        )
    return channels


def choose_channels(
    parsed: ParsedBms,
    requested: list[str] | None,
    fold_7k: bool,
) -> list[str]:
    if requested:
        if fold_7k:
            raise ValueError("--channels and --fold-7k cannot be used together")
        return requested
    detected = active_channels(parsed)
    if fold_7k:
        if detected == list(P1_KEYS) or detected == list(P2_KEYS):
            return detected
        rendered = ", ".join(detected) or "none"
        raise ValueError(
            f"7K folding requires exactly one complete 7-key side; "
            f"active key channels: {rendered}"
        )
    if len(detected) != 4:
        rendered = ", ".join(detected) or "none"
        raise ValueError(
            f"safe 4K detection failed; active key channels: {rendered}. "
            "Use --channels with exactly four channels."
        )
    return detected


def make_note(time_ms: float, lane: int, duration_ms: float = 0) -> dict:
    return {
        "timeMs": max(0, round(time_ms)),
        "lane": lane,
        "baseSpeedupCoef": 1,
        "densitySpeedupCoefMultiplier": 1,
        "rampSpeedupCoefMultiplier": 1,
        "manualSpeedupCoefMultiplier": 1,
        "autoSpeedupCoefMultiplier": 1,
        "speedupCoef": 1,
        "durationMs": max(0, round(duration_ms)),
    }


def convert_notes(
    parsed: ParsedBms, timeline: Timeline, channels: list[str]
) -> tuple[list[dict], list[str]]:
    lane_for_channel = {channel: lane for lane, channel in enumerate(channels)}
    warnings: list[str] = []
    notes: list[dict] = []

    normal_objects: list[tuple[RawObject, str]] = []
    long_objects: dict[str, list[RawObject]] = {channel: [] for channel in channels}
    for obj in parsed.objects:
        normal = normal_channel(obj.channel)
        if normal in lane_for_channel:
            normal_objects.append((obj, normal))
        long_normal = long_channel_to_normal(obj.channel)
        if long_normal in lane_for_channel:
            long_objects[long_normal].append(obj)

    lnobj = parsed.headers.get("LNOBJ", "").upper()
    pending_lnobj_start: dict[str, dict] = {}
    for obj, channel in sorted(normal_objects, key=lambda item: item[0].position):
        time_ms = timeline.milliseconds(obj.position)
        if lnobj and obj.value == lnobj:
            start = pending_lnobj_start.pop(channel, None)
            if start is None:
                warnings.append(
                    f"orphan #LNOBJ endpoint at measure {obj.position.measure:03d}"
                )
            else:
                start["durationMs"] = max(0, round(time_ms - start["timeMs"]))
            continue
        note = make_note(time_ms, lane_for_channel[channel])
        notes.append(note)
        pending_lnobj_start[channel] = note

    for channel, objects in long_objects.items():
        start_time: float | None = None
        for obj in sorted(objects, key=lambda item: item.position):
            time_ms = timeline.milliseconds(obj.position)
            if start_time is None:
                start_time = time_ms
            else:
                notes.append(
                    make_note(
                        start_time,
                        lane_for_channel[channel],
                        time_ms - start_time,
                    )
                )
                start_time = None
        if start_time is not None:
            warnings.append(f"unclosed long note on BMS channel {channel}")

    notes.sort(key=lambda note: (note["timeMs"], note["lane"], note["durationMs"]))
    deduped: list[dict] = []
    occupied: set[tuple[int, int]] = set()
    for note in notes:
        key = (note["timeMs"], note["lane"])
        if key in occupied:
            warnings.append(
                f"dropped duplicate note at {note['timeMs']}ms lane {note['lane'] + 1}"
            )
            continue
        occupied.add(key)
        deduped.append(note)
    return deduped, warnings


def infer_snap_div(parsed: ParsedBms) -> int:
    denominators = [
        obj.position.fraction.denominator
        for obj in parsed.objects
        if normal_channel(obj.channel) or long_channel_to_normal(obj.channel)
    ]
    if not denominators:
        return 4
    required = 1
    for denominator in denominators:
        required = math.lcm(required, denominator)
        if required > 48:
            return 48
    for supported in (1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48):
        if supported >= required and supported % required == 0:
            return supported
    return 48


def convert_bms(
    path: Path,
    *,
    channels: list[str] | None = None,
    fold_7k: bool = False,
    title: str | None = None,
    artist: str | None = None,
) -> tuple[dict, list[str]]:
    parsed = parse_bms(read_bms_text(path))
    selected = choose_channels(parsed, channels, fold_7k)
    timeline = Timeline(parsed)
    notes, warnings = convert_notes(parsed, timeline, selected)
    if fold_7k:
        notes, fold_stats = fold_notes(notes, 7)
        warnings.append(fold_stats.summary(7))
    if timeline.stop_count:
        warnings.append(
            f"baked {timeline.stop_count} BMS STOP event(s) into note timestamps; "
            "OverTempo has no native STOP event"
        )

    bpm_changes = []
    last: tuple[int, float] | None = None
    for change in timeline.bpm_changes:
        item = (int(change["timeMs"]), float(change["bpm"]))
        if item != last:
            bpm_changes.append({"timeMs": item[0], "bpm": item[1]})
            last = item

    chart_title = title or parsed.headers.get("TITLE", path.stem)
    chart_artist = artist or parsed.headers.get("ARTIST", "")
    level_text = parsed.headers.get("PLAYLEVEL", "1")
    try:
        level = float(level_text)
    except ValueError:
        level = 1

    extra = (
        f"Imported from BMS {path.name}; channels {','.join(selected)}"
        + (f"; {'; '.join(warnings)}" if warnings else "")
    )
    chart = {
        "version": 2,
        "meta": {
            "title": chart_title,
            "artist": chart_artist,
            "source": parsed.headers.get("SUBTITLE", ""),
            "mapper": parsed.headers.get("GENRE", "BMS import"),
            "previewStartMs": 0,
            "previewEndMs": 15000,
            "extra": extra,
            "coverDataUrl": "",
            "audioFileName": "",
        },
        "difficulty": {
            "name": parsed.headers.get("DIFFICULTY", "BMS Base"),
            "level": level,
            "scroll": 1,
            "baseSpeed": 1,
            "notes": "",
            "lanes": 4,
        },
        "timing": {
            "bpm": timeline.initial_bpm,
            "offsetMs": 0,
            "snapDiv": infer_snap_div(parsed),
            "bpmChanges": bpm_changes,
        },
        "editorSettings": {"encryptionEnabled": False, "argId": ""},
        "preview": {"startMs": 0, "endMs": 15000},
        "speedLimitLines": [],
        "stageDeltaLines": [],
        "notes": notes,
    }
    return chart, warnings


def default_output_path(input_path: Path) -> Path:
    safe_stem = re.sub(r'[\\/:*?"<>|]+', "_", input_path.stem).strip() or "BMS"
    return input_path.with_name(f"{safe_stem}_BMS.4k-speedcoef.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help=".bms, .bme, or .bml source file")
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument(
        "--channels",
        type=parse_channel_selection,
        help="four BMS key channels in output lane order, e.g. 11,12,13,14",
    )
    parser.add_argument(
        "--fold-7k",
        action="store_true",
        help="compress one complete 7K side to 4K using lane-union semantics",
    )
    parser.add_argument("--title", help="override #TITLE")
    parser.add_argument("--artist", help="override #ARTIST")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.input.suffix.lower() not in {".bms", ".bme", ".bml"}:
        raise SystemExit("input must be a .bms, .bme, or .bml file")
    chart, warnings = convert_bms(
        args.input,
        channels=args.channels,
        fold_7k=args.fold_7k,
        title=args.title,
        artist=args.artist,
    )
    output = args.output or default_output_path(args.input)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(chart, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {output} ({len(chart['notes'])} notes)")
    for warning in warnings:
        print(f"warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
