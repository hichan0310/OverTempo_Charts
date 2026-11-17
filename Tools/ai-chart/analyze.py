#!/usr/bin/env python3
"""Extract beat-aligned *candidates* and descriptive audio features for AI charting.

No game source, song chart, or audio file is modified. This is not a keysound
transcription model. Audio-derived source hints are proxies unless stems are given.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

ATTACK_DETECTOR = "mel-flux-512-64-local1s-v2"


def js_round(value: float) -> int:
    return math.floor(value + 0.5)


def load_chart(path: Path) -> dict:
    chart = json.loads(path.read_text(encoding="utf-8-sig"))
    timing = chart.get("timing", {})
    if not math.isfinite(float(timing.get("bpm", 0))) or float(timing.get("bpm", 0)) <= 0:
        raise ValueError("chart must provide a positive timing.bpm")
    if int(chart.get("difficulty", {}).get("lanes", 4)) != 4:
        raise ValueError("only four-key charts are supported")
    return chart


def timing_segments(timing: dict) -> list[tuple[int, float]]:
    bpm = float(timing["bpm"])
    if not math.isfinite(bpm) or bpm <= 0:
        raise ValueError("timing.bpm must be finite and positive")
    segments = [(0, max(1, bpm))]
    for change in timing.get("bpmChanges", []):
        start, bpm = js_round(float(change["timeMs"])), float(change["bpm"])
        if start <= 0 or not math.isfinite(bpm) or bpm <= 0:
            raise ValueError("invalid BPM change")
        segments.append((start, bpm))
    segments.sort()
    if len({s for s, _ in segments}) != len(segments):
        raise ValueError("duplicate BPM change time")
    return segments


def snap_grid(timing: dict, chart_ms: float, subdivision: int) -> dict:
    """Match the editor's snapTime, including JS rounding and segment boundaries."""
    if not isinstance(subdivision, int) or isinstance(subdivision, bool) or not 1 <= subdivision <= 48:
        raise ValueError("subdivision must be an integer in 1..48")
    segments = timing_segments(timing)
    t = max(0, chart_ms)
    index = max(i for i, (start, _) in enumerate(segments) if start <= t)
    start, bpm = segments[index]
    end = segments[index + 1][0] if index + 1 < len(segments) else float("inf")
    step = 60000.0 / bpm / subdivision
    best = min(end, max(start, start + js_round((t - start) / step) * step))
    for boundary in (start, end):
        if math.isfinite(boundary) and abs(boundary - t) < abs(best - t):
            best = boundary
    snapped = js_round(best)
    # A rounded tick may land on the next BPM marker.
    index = max(i for i, (start, _) in enumerate(segments) if start <= snapped)
    start, bpm = segments[index]
    tick = js_round((snapped - start) * bpm * subdivision / 60000)
    return {"chartMs": snapped, "segmentIndex": index, "bpm": bpm,
            "bar": tick // (subdivision * 4), "beatInBar": (tick // subdivision) % 4,
            "sub": tick % subdivision, "beatKey": f"{index}:{tick // subdivision}",
            "subdivisionsPerBeat": subdivision}


def beat_grid(timing: dict, start_chart_ms: float, end_chart_ms: float, subdivision: int):
    """Grid follows existing editor: each BPM segment restarts at a beat boundary."""
    if subdivision < 1 or subdivision > 48:
        raise ValueError("subdivision must be 1..48")
    segments = timing_segments(timing)
    for index, (start, bpm) in enumerate(segments):
        end = segments[index + 1][0] if index + 1 < len(segments) else float("inf")
        low, high = max(start, start_chart_ms), min(end, end_chart_ms)
        if low >= high:
            continue
        step = 60000.0 / (bpm * subdivision)
        first = max(0, math.ceil((low - start - 1e-7) / step))
        last = math.ceil((high - start - 1e-7) / step)
        for tick in range(first, last):
            t = js_round(start + tick * step)
            if t < low or t >= high:
                continue
            yield {
                "chartMs": t,
                "segmentIndex": index,
                "bpm": bpm,
                "bar": tick // (subdivision * 4),
                "beatInBar": (tick // subdivision) % 4,
                "sub": tick % subdivision,
                "beatKey": f"{index}:{tick // subdivision}",
            }


def _robust_scale(values):
    import numpy as np
    values = np.asarray(values, dtype=np.float64)
    percentile = np.percentile(values, 95) if values.size else 0.0
    return np.clip(values / max(float(percentile), 1e-9), 0, 1)


def describe_track(audio_path: Path, start_sec: float, duration_sec: float, sr=22050, hop=256) -> dict:
    """Analyze only the requested audio excerpt. Work with waveforms, not a language model."""
    import librosa
    import numpy as np
    from scipy.ndimage import maximum_filter1d

    y, sr = librosa.load(str(audio_path), sr=sr, mono=True, offset=start_sec, duration=duration_sec)
    if len(y) < 2048:
        raise ValueError(f"audio too short for requested range: {audio_path}")
    stft = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    flux = np.maximum(0, np.diff(stft, axis=1, prepend=stft[:, :1]))

    def band(a: float, b: float):
        mask = (freqs >= a) & (freqs < b)
        return _robust_scale(flux[mask, :].mean(axis=0)) if np.any(mask) else np.zeros(stft.shape[1])

    low, mid, high = band(25, 200), band(200, 2000), band(2000, 10000)
    onset = _robust_scale(0.3 * low + 0.45 * mid + 0.25 * high)
    # The raw RMS frames also summarize whether the passage is calm or dense.
    rms = librosa.feature.rms(S=stft, frame_length=2048)[0]
    rms = _robust_scale(rms)
    # Chroma indicates dominant pitch classes, NOT which instrument plays them.
    chroma = librosa.feature.chroma_stft(S=stft ** 2, sr=sr, hop_length=hop)
    # Locate attacks separately from descriptive band features. Raw linear-STFT
    # flux peaks can precede an impulse or promote a decaying tone's leakage.
    attack_hop = 64
    attack_env = librosa.onset.onset_strength(
        y=y, sr=sr, n_fft=512, hop_length=attack_hop, n_mels=64, max_size=1)
    # A distant loud accent must not suppress a quieter pitch change. Keep
    # normalization local, and retain adjacent pitch movement rather than
    # treating it as vibrato with a frequency maximum filter.
    attack_reference = maximum_filter1d(
        attack_env, size=2 * round(.5 * sr / attack_hop) + 1, mode="nearest")
    attack_env = attack_env / np.maximum(attack_reference, 1e-9)
    attack_frames = librosa.onset.onset_detect(
        onset_envelope=attack_env, sr=sr, hop_length=attack_hop, normalize=False)
    # Peak picking reports the leading edge. Measure its confidence across the
    # same half-window, without moving that timestamp to the later maximum.
    attack_lookahead = 512 // (2 * attack_hop)
    attacks = [{"audioSec": start_sec + int(frame) * attack_hop / sr,
                "strength": float(np.max(attack_env[frame:frame + attack_lookahead + 1]))}
               for frame in attack_frames]
    return {"start_sec": start_sec, "frame_sec": hop / sr,
            "attacks": attacks,
            "attack": flux.mean(axis=0),
            "onset": onset, "low": low, "mid": mid, "high": high,
            "rms": rms, "chroma": chroma, "duration_sec": len(y) / sr}


def _window(track: dict, sec: float, radius_sec: float = 0.055) -> dict:
    import numpy as np
    center = (sec - track["start_sec"]) / track["frame_sec"]
    r = max(1, math.ceil(radius_sec / track["frame_sec"]))
    a = max(0, int(center) - r)
    b = min(len(track["onset"]), int(center) + r + 1)
    if a >= b:
        return {"onset": 0., "low": 0., "mid": 0., "high": 0., "rms": 0.,
                "deviationMs": 0, "pitchClass": None, "pitchConfidence": 0.}
    peaks = track["onset"][a:b]
    best_index = a + int(np.argmax(peaks))
    chroma = np.mean(track["chroma"][:, a:b], axis=1)
    chroma_total = max(float(np.sum(chroma)), 1e-9)
    pitch = int(np.argmax(chroma))
    return {
        "onset": round(float(np.max(peaks)), 3),
        "low": round(float(np.max(track["low"][a:b])), 3),
        "mid": round(float(np.max(track["mid"][a:b])), 3),
        "high": round(float(np.max(track["high"][a:b])), 3),
        "rms": round(float(np.mean(track["rms"][a:b])), 3),
        "deviationMs": js_round((best_index - center) * track["frame_sec"] * 1000),
        "pitchClass": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"][pitch],
        "pitchConfidence": round(float(chroma[pitch] / chroma_total), 3),
    }


def analyze(chart_path: Path, audio_path: Path, start_sec: float = 0.0,
            duration_sec: float = 20.0, subdivision: int = 4,
            max_events: int = 140, threshold: float = 0.22,
            stems_dir: Path | None = None, mood_notes: str = "",
            fine_subdivisions: tuple[int, ...] = (6, 8), max_deviation_ms: float = 20) -> dict:
    if not audio_path.is_file():
        raise FileNotFoundError(audio_path)
    if start_sec < 0 or not (1 <= duration_sec <= 90):
        raise ValueError("start must be nonnegative; duration must be 1..90 seconds")
    if max_events < 1 or not 0 <= threshold <= 1:
        raise ValueError("invalid max_events or threshold")
    chart = load_chart(chart_path)
    timing = chart["timing"]
    offset_ms = float(timing.get("offsetMs", 0))
    if not math.isfinite(offset_ms) or not math.isfinite(max_deviation_ms) or max_deviation_ms <= 0:
        raise ValueError("offset must be finite and max deviation must be positive")
    divisions = [subdivision] + sorted(set(d for d in fine_subdivisions if d > subdivision))
    for division in (subdivision, *fine_subdivisions):
        snap_grid(timing, 0, division)
    audio = describe_track(audio_path, start_sec, duration_sec)
    stems = {}
    if stems_dir:
        for name in ("drums", "bass", "vocals", "other"):
            for ext in (".wav", ".flac", ".ogg", ".mp3"):
                stem_path = stems_dir / (name + ext)
                if stem_path.exists():
                    stems[name] = describe_track(stem_path, start_sec, duration_sec)
                    break
    # Detect attacks first, so off-grid music cannot silently disappear from review.
    found_by_time = {}
    review = []
    for attack in audio["attacks"]:
        strength = attack["strength"]
        if strength < threshold:
            continue
        attack_sec = attack["audioSec"]
        if attack_sec >= start_sec + duration_sec:
            continue
        attack_chart_ms = attack_sec * 1000 + offset_ms
        choices = [snap_grid(timing, attack_chart_ms, d) for d in divisions]
        accepted = [g for g in choices if attack_chart_ms >= 0 and
                    abs(g["chartMs"] - attack_chart_ms) <=
                    min(max_deviation_ms, 60000 / g["bpm"] / g["subdivisionsPerBeat"] * .2)]
        if not accepted:
            nearest = min(choices, key=lambda g: abs(g["chartMs"] - attack_chart_ms))
            review.append({"attackAudioMs": attack_sec * 1000, "attackChartMs": attack_chart_ms,
                           "nearestGridMs": nearest["chartMs"],
                           "deviationMs": attack_chart_ms - nearest["chartMs"],
                           "reviewRequired": True, "reason": "attack outside grid tolerance"})
            continue
        g = accepted[0]
        feats = _window(audio, attack_sec, audio["frame_sec"] * .49)
        extra = {name: _window(data, attack_sec)["onset"] for name, data in stems.items()}
        item = {**g, **feats, "onset": round(float(strength), 3),
                "audioMs": g["chartMs"] - offset_ms, "attackAudioMs": attack_sec * 1000,
                "deviationMs": attack_chart_ms - g["chartMs"]}
        if extra:
            item["stems"] = extra
        previous = found_by_time.get(g["chartMs"])
        if previous is None or item["onset"] > previous["onset"]:
            found_by_time[g["chartMs"]] = item
    found = sorted(found_by_time.values(), key=lambda e: e["chartMs"])
    # Restrict extremely busy songs without accidentally picking only one section.
    if len(found) > max_events:
        stride = max(1, math.ceil(len(found) / max_events))
        buckets = [found[i:i + stride] for i in range(0, len(found), stride)]
        found = [max(bucket, key=lambda e: e["onset"]) for bucket in buckets]
        if len(found) > max_events:
            found = sorted(found, key=lambda e: e["onset"], reverse=True)[:max_events]
        found.sort(key=lambda e: e["chartMs"])
    for i, item in enumerate(found, 1):
        item["id"] = f"E{i:04d}"
    # Four-bar summaries follow BPM; a segment boundary resets bar indexing.
    groups: dict[tuple[int, int], list[dict]] = {}
    for e in found:
        groups.setdefault((e["segmentIndex"], e["bar"] // 4), []).append(e)
    phrases = []
    for (seg, block), entries in sorted(groups.items()):
        phrases.append({"segment": seg, "block4Bars": block,
                        "fromChartMs": min(e["chartMs"] for e in entries),
                        "toChartMs": max(e["chartMs"] for e in entries),
                        "attackCount": len(entries),
                        "avgRms": round(sum(e["rms"] for e in entries) / len(entries), 3),
                        "avgLow": round(sum(e["low"] for e in entries) / len(entries), 3),
                        "avgHigh": round(sum(e["high"] for e in entries) / len(entries), 3)})
    hasher = hashlib.sha256()
    with audio_path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            hasher.update(block)
    digest = hasher.hexdigest()
    identity = {"audio": digest, "start": start_sec, "duration": duration_sec,
                "offset": offset_ms, "timing": timing, "subdivisions": divisions,
                "maxDeviationMs": max_deviation_ms, "attackDetector": ATTACK_DETECTOR,
                "threshold": threshold, "maxEvents": max_events}
    analysis_id = hashlib.sha256(json.dumps(identity, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:20]
    return {
        "schemaVersion": 1, "analysisId": analysis_id,
        "song": str(chart.get("meta", {}).get("title", audio_path.stem)),
        "template": str(chart_path),
        "sourceAudio": audio_path.name,
        "sourceAudioSha256": digest,
        "attackDetector": ATTACK_DETECTOR,
        "alignment": {"startAudioSec": start_sec, "durationSec": duration_sec,
                      "offsetMs": offset_ms, "subdivisionsPerBeat": subdivision,
                      "allowedSubdivisionsPerBeat": divisions, "maxDeviationMs": max_deviation_ms,
                      "bpm": float(timing["bpm"]), "bpmChanges": timing.get("bpmChanges", [])},
        "moodNotesFromHuman": mood_notes,
        "featureCaveat": "Frequency bands are spectral proxies, not isolated instruments or exact keysounds. Use stems or music review.",
        "stemNames": sorted(stems), "phrases": phrases,
        "events": found, "reviewRequired": review,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chart", type=Path, required=True, help="existing four-key chart template")
    parser.add_argument("--audio", type=Path, help="default: template meta.audioFileName")
    parser.add_argument("--start-sec", type=float, default=0.)
    parser.add_argument("--duration-sec", type=float, default=20.)
    parser.add_argument("--subdivision", type=int, default=4, help="grid slots per beat")
    parser.add_argument("--fine-subdivisions", type=int, nargs="*", default=[6, 8],
                        help="additional finer slots per beat; default: 6 8 (24th/32nd notes)")
    parser.add_argument("--max-deviation-ms", type=float, default=20,
                        help="maximum attack/grid error; larger errors require review")
    parser.add_argument("--threshold", type=float, default=0.22)
    parser.add_argument("--max-events", type=int, default=140)
    parser.add_argument("--stems-dir", type=Path, help="optional Demucs drums/bass/vocals/other stems")
    parser.add_argument("--mood-notes", default="", help="listening impression, supplied by human")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    chart = load_chart(args.chart)
    audio = args.audio or args.chart.parent / str(chart.get("meta", {}).get("audioFileName", ""))
    if args.output.exists():
        parser.error("refusing to overwrite existing analysis JSON")
    result = analyze(args.chart, audio, args.start_sec, args.duration_sec,
                     args.subdivision, args.max_events, args.threshold,
                     args.stems_dir, args.mood_notes, tuple(args.fine_subdivisions),
                     args.max_deviation_ms)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {args.output} ({len(result['events'])} candidate events)")


if __name__ == "__main__":
    main()
