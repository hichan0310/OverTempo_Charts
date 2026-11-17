#!/usr/bin/env python3
"""Read-only, exploratory audio/chart alignment audit. Requires numpy and ffmpeg.

Positive residual means audio attacks occur later than chart-predicted audio times.
The corresponding offsetMs candidate is current offsetMs minus residual.
These are spectral-attack estimates, not listening-verified chart corrections.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np

SR = 22050
HOP = 110
FFT = 512
STEP_MS = HOP * 1000 / SR
BANDS = ((40, 250), (250, 2500), (2500, 10000))
SHIFTS = np.arange(-40, 41)  # Approximately +/-200 ms, in ~5 ms steps.


def features(audio):
    """Centered STFT, positive log-magnitude spectral difference by frequency band."""
    frames = np.lib.stride_tricks.sliding_window_view(np.pad(audio, FFT // 2), FFT)[::HOP]
    frequencies = np.fft.rfftfreq(FFT, 1 / SR)
    masks = [(frequencies >= low) & (frequencies < high) for low, high in BANDS]
    window = np.hanning(FFT)
    chunks = []
    previous = np.zeros(FFT // 2 + 1)
    for start in range(0, len(frames), 1024):
        spectrum = np.log1p(20 * np.abs(np.fft.rfft(frames[start:start + 1024] * window, axis=1)))
        difference = np.maximum(0, np.diff(np.vstack([previous, spectrum]), axis=0))
        chunks.append(np.stack([difference[:, mask].mean(axis=1) for mask in masks]))
        previous = spectrum[-1]
    flux = np.concatenate(chunks, axis=1)
    for band in flux:
        baseline = np.convolve(band, np.ones(201) / 201, mode='same')
        band /= baseline + max(float(np.percentile(baseline, 75)) * .15, 1e-8)
        band[:] = np.convolve(band, [.25, .5, .25], mode='same')
    return flux


def score(envelopes, times):
    positions = times[:, None] * SR / HOP + SHIFTS[None, :]
    return np.stack([np.interp(positions.ravel(), np.arange(len(band)), band)
                     .reshape(positions.shape).mean(axis=0) for band in envelopes])


def calibration():
    rng = np.random.default_rng(1207)
    times = np.arange(1, 10, .731)
    audio = np.zeros(SR * 11, dtype=np.float32)
    for time in times:
        start = round(time * SR)
        audio[start:start + 220] += rng.normal(size=220) * np.exp(-np.arange(220) / 30)
    profile = score(features(audio), times)
    bias = SHIFTS[np.argmax(profile, axis=1)] * STEP_MS
    for delay_ms in (-37, 23):
        measured = SHIFTS[np.argmax(score(features(audio), times - delay_ms / 1000), axis=1)] * STEP_MS - bias
        assert np.max(np.abs(measured - delay_ms)) <= 2 * STEP_MS, (delay_ms, measured)
    return bias


def audit(chart_path, bias):
    raw = chart_path.read_bytes()
    chart = json.loads(raw.decode('utf-8-sig'))
    audio_path = chart_path.parent / chart['meta']['audioFileName']
    result = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(audio_path), '-f', 'f32le',
                             '-ac', '1', '-ar', str(SR), 'pipe:1'], check=True, capture_output=True)
    audio = np.frombuffer(result.stdout, dtype='<f4')
    offset = float(chart['timing'].get('offsetMs', 0))
    times = np.unique([n['timeMs'] for n in chart['notes']]) / 1000 - offset / 1000
    times = times[(times > 3) & (times < len(audio) / SR - 2)]
    if len(times) < 20:
        raise ValueError('Too few distinct note heads to estimate alignment')
    envelope = features(audio)
    profiles = score(envelope, times)
    # Align the three bands to a common detector-calibrated lag axis before averaging.
    lag_ms = SHIFTS * STEP_MS
    aligned = np.stack([np.interp(lag_ms + b, lag_ms, p) for b, p in zip(bias, profiles)])
    combined = aligned.mean(axis=0)
    best = int(np.argmax(combined))
    residual = float(lag_ms[best])
    band_lags = lag_ms[np.argmax(profiles, axis=1)] - bias
    segments = []
    for start in np.arange(0, len(audio) / SR, 20):
        selected = times[(times >= start) & (times < start + 20)]
        if len(selected) < 20:
            continue
        profile = score(envelope, selected)
        normalized = np.stack([np.interp(lag_ms + b, lag_ms, p) for b, p in zip(bias, profile)]).mean(axis=0)
        segments.append({'startSeconds': float(start), 'noteHeads': len(selected),
                         'residualMs': float(lag_ms[np.argmax(normalized)])})
    segment_lags = np.array([s['residualMs'] for s in segments])
    spread = float(np.median(np.abs(segment_lags - np.median(segment_lags)))) if len(segment_lags) else None
    band_spread = float(np.ptp(band_lags))
    outside_peak = np.abs(lag_ms - residual) >= 30
    prominence = float((combined[best] - combined[outside_peak].max()) / max(combined[best], 1e-8))
    support = float(np.mean(np.abs(segment_lags - residual) <= 20)) if len(segment_lags) else 0
    confidence = 'candidate' if (abs(residual) < 180 and band_spread <= 20 and support >= .7
                                  and prominence >= .06 and len(segments) >= 3) else 'ambiguous'
    assert chart_path.read_bytes() == raw, 'Audit must never modify authored charts'
    return {'song': chart_path.parent.name, 'chart': str(chart_path), 'audio': str(audio_path),
            'chartSha256': hashlib.sha256(raw).hexdigest(), 'currentOffsetMs': offset,
            'residualMs': round(residual, 1), 'candidateOffsetMs': round(offset - residual, 1),
            'confidence': confidence, 'distinctNoteHeads': len(times),
            'bandResidualsMs': np.round(band_lags, 1).tolist(), 'bandSpreadMs': round(band_spread, 1),
            'segmentMedianAbsoluteDeviationMs': round(spread, 1) if spread is not None else None,
            'segmentSupport': round(support, 3), 'peakProminence': round(prominence, 3),
            'segments': segments, 'lagMs': lag_ms.tolist(), 'score': combined.tolist()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--songs', type=Path, default=Path('Songs'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    bias = calibration()
    print('Synthetic +/- timing checks passed; band detector biases (ms):', bias, flush=True)
    rows = []
    for path in sorted(args.songs.glob('*/*.4k-speedcoef.json')):
        row = audit(path, bias)
        rows.append(row)
        print(row['song'], row['residualMs'], row['confidence'], 'bands', row['bandResidualsMs'],
              'segment support', row['segmentSupport'], flush=True)
        (args.output / 'alignment.json').write_text(json.dumps({'detectorBiasMs': bias.tolist(), 'songs': rows}, ensure_ascii=False, indent=2) + '\n')
    fields = ['song', 'currentOffsetMs', 'residualMs', 'candidateOffsetMs', 'confidence',
              'distinctNoteHeads', 'bandSpreadMs', 'segmentMedianAbsoluteDeviationMs', 'segmentSupport', 'peakProminence']
    with (args.output / 'alignment.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    notes = ['# Audio/chart alignment audit', '',
             'Exploratory spectral-attack estimates only; no chart, client, build or release was changed.',
             'Positive residual: audio attack later than the chart-predicted audio time. Candidate offset = current offset - residual.',
             'Resolution ~5 ms. Attack timing depends on timbre; this is not perceptual or device latency calibration.',
             'candidate = agreement across frequency bands and 20-second segments; ambiguous = do not auto-apply.', '',
             '| Song | Current offset ms | Residual ms | Candidate offset ms | Status |',
             '|---|---:|---:|---:|---|']
    notes += [f"| {r['song']} | {r['currentOffsetMs']} | {r['residualMs']} | {r['candidateOffsetMs']} | {r['confidence']} |" for r in rows]
    (args.output / 'README.md').write_text('\n'.join(notes) + '\n')


if __name__ == '__main__':
    main()
