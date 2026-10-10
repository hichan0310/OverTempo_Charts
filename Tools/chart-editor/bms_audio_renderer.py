#!/usr/bin/env python3
"""Render an official BMS keysound package into one reference audio file.

The renderer schedules channel 01 BGM objects and every playable/long-note
keysound. It never downloads audio: all #WAVxx files must already exist beside
the selected BMS file.

Runtime dependencies:
    python -m pip install numpy soundfile scipy
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from bms_to_overtempo import ParsedBms, Timeline, parse_bms, read_bms_text


@dataclass(frozen=True)
class AudioEvent:
    time_ms: float
    wav_id: str
    path: Path


def is_audio_channel(channel: str) -> bool:
    if channel == "01":
        return True
    return (
        len(channel) == 2
        and channel[0] in {"1", "2", "5", "6"}
        and channel[1] in "123456789"
    )


def wav_definitions(parsed: ParsedBms) -> dict[str, str]:
    return {
        key[3:].upper(): value.strip().strip('"')
        for key, value in parsed.headers.items()
        if key.startswith("WAV") and len(key) == 5 and value.strip()
    }


def resolve_sample_path(bms_path: Path, reference: str) -> Path:
    relative = Path(reference.replace("\\", "/"))
    if relative.is_absolute() or relative.drive or ".." in relative.parts:
        raise ValueError(f"#WAV path escapes the BMS folder: {reference}")
    candidate = bms_path.parent / relative
    if candidate.is_file():
        return candidate

    # BMS packs are often authored on a case-insensitive filesystem.
    current = bms_path.parent
    for part in relative.parts:
        if part in {".", ""}:
            continue
        if part == "..":
            raise ValueError(f"#WAV path escapes the BMS folder: {reference}")
        exact = current / part
        if exact.exists():
            current = exact
            continue
        match = next(
            (
                child
                for child in current.iterdir()
                if child.name.casefold() == part.casefold()
            ),
            None,
        )
        if match is None and part == relative.parts[-1]:
            requested_stem = Path(part).stem.casefold()
            match = next(
                (
                    child
                    for child in current.iterdir()
                    if child.is_file()
                    and child.stem.casefold() == requested_stem
                    and child.suffix.casefold()
                    in {".wav", ".ogg", ".flac", ".mp3", ".m4a"}
                ),
                None,
            )
        if match is None:
            return candidate
        current = match
    return current


def collect_audio_events(
    bms_path: Path,
    parsed: ParsedBms,
    timeline: Timeline,
) -> tuple[list[AudioEvent], list[str]]:
    definitions = wav_definitions(parsed)
    warnings: list[str] = []
    events: list[AudioEvent] = []
    missing_ids: set[str] = set()
    missing_paths: set[str] = set()
    resolved_paths: dict[str, Path] = {}
    lnobj = parsed.headers.get("LNOBJ", "").upper()

    for obj in parsed.objects:
        if not is_audio_channel(obj.channel):
            continue
        if lnobj and obj.value == lnobj:
            # #LNOBJ marks a release endpoint and commonly names a deliberately
            # absent silent sample such as "Long_End".
            continue
        reference = definitions.get(obj.value)
        if reference is None:
            missing_ids.add(obj.value)
            continue
        sample_path = resolved_paths.get(obj.value)
        if sample_path is None:
            sample_path = resolve_sample_path(bms_path, reference)
            resolved_paths[obj.value] = sample_path
        if not sample_path.is_file():
            missing_paths.add(reference)
            continue
        events.append(
            AudioEvent(
                time_ms=timeline.milliseconds(obj.position),
                wav_id=obj.value,
                path=sample_path,
            )
        )

    if missing_ids:
        warnings.append(
            "undefined keysound IDs: " + ", ".join(sorted(missing_ids))
        )
    if missing_paths:
        warnings.append(
            "missing keysound files: " + ", ".join(sorted(missing_paths))
        )
    events.sort(key=lambda event: (event.time_ms, event.wav_id))
    return events, warnings


def load_audio_modules():
    try:
        import numpy as np
        import soundfile as sf
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "BMS audio rendering requires numpy and soundfile. Install them with: "
            "python -m pip install numpy soundfile"
        ) from exc
    return np, sf


def decode_sample(path: Path, output_rate: int, np, sf):
    data, sample_rate = sf.read(
        path,
        dtype="float32",
        always_2d=True,
    )
    if data.shape[1] == 1:
        data = np.repeat(data, 2, axis=1)
    elif data.shape[1] > 2:
        data = data[:, :2]

    if sample_rate != output_rate and len(data):
        from scipy.signal import resample_poly

        divisor = math.gcd(sample_rate, output_rate)
        data = resample_poly(
            data, output_rate // divisor, sample_rate // divisor, axis=0
        ).astype("float32")
    return data


def render_bms_audio(
    bms_path: Path,
    output_path: Path,
    *,
    sample_rate: int = 44100,
    tail_seconds: float = 1.0,
    report_path: Path | None = None,
) -> tuple[int, list[str]]:
    text = read_bms_text(bms_path)
    if re.search(r"^\s*#(?:RANDOM|SETRANDOM|IF|ELSEIF|ELSE|ENDIF)\b", text, re.I | re.M):
        raise ValueError(
            "conditional #RANDOM/#IF BMS is not rendered automatically; "
            "resolve one branch first"
        )

    parsed = parse_bms(text)
    timeline = Timeline(parsed)
    events, warnings = collect_audio_events(bms_path, parsed, timeline)
    if not events:
        raise ValueError("BMS contains no resolvable audio events")
    if warnings:
        raise ValueError("; ".join(warnings))

    np, sf = load_audio_modules()
    cache: dict[Path, object] = {}
    scheduled = []
    total_frames = 0
    for event in events:
        sample = cache.get(event.path)
        if sample is None:
            sample = decode_sample(event.path, sample_rate, np, sf)
            cache[event.path] = sample
        start_frame = max(0, round(event.time_ms * sample_rate / 1000))
        scheduled.append((start_frame, sample))
        total_frames = max(total_frames, start_frame + len(sample))

    total_frames += max(0, round(tail_seconds * sample_rate))
    mix = np.zeros((total_frames, 2), dtype="float32")
    for start_frame, sample in scheduled:
        mix[start_frame : start_frame + len(sample)] += sample

    peak = float(np.max(np.abs(mix))) if len(mix) else 0
    if not math.isfinite(peak):
        raise ValueError("rendered audio contains non-finite samples")
    if peak > 0.98:
        mix *= 0.98 / peak
        warnings.append(f"prevented clipping; original mixed peak was {peak:.3f}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(output_path, mix, sample_rate, subtype="PCM_16")
    if report_path is not None:
        report = {
            "sourceChart": bms_path.name,
            "sourceChartSha256": hashlib.sha256(bms_path.read_bytes()).hexdigest(),
            "output": output_path.name,
            "outputSha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
            "sampleRate": sample_rate,
            "frames": total_frames,
            "durationSeconds": total_frames / sample_rate,
            "tailSeconds": tail_seconds,
            "scheduledEvents": len(events),
            "uniqueSamples": len(cache),
            "peakBeforeGain": peak,
            "gain": min(1.0, 0.98 / peak) if peak else 1.0,
            "warnings": warnings,
            "samples": [
                {"file": path.relative_to(bms_path.parent).as_posix(),
                 "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                for path in sorted(cache)
            ],
        }
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(events), warnings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help=".bms, .bme, or .bml chart")
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--sample-rate", type=int, default=44100)
    parser.add_argument("--tail-seconds", type=float, default=1.0)
    parser.add_argument("--report", type=Path, help="write source hashes and rendering statistics as JSON")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.input.suffix.lower() not in {".bms", ".bme", ".bml"}:
        raise SystemExit("input must be a .bms, .bme, or .bml file")
    if args.sample_rate < 8000 or args.sample_rate > 192000:
        raise SystemExit("--sample-rate must be between 8000 and 192000")
    output = args.output or args.input.with_name(f"{args.input.stem}_rendered.wav")
    count, warnings = render_bms_audio(
        args.input,
        output,
        sample_rate=args.sample_rate,
        tail_seconds=max(0, args.tail_seconds),
        report_path=args.report,
    )
    print(f"wrote {output} ({count} scheduled keysounds)")
    for warning in warnings:
        print(f"warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
