#!/usr/bin/env python3
"""Mix the soundtrack of a rendered ARG reveal and encode it to MP4.

Input is the folder written by Unity `ArgRevealScriptChecks.RenderEndTimeMovie`
(frame-0000.png..., audio.json). Every script sound is cut sample-accurately with
its requested fades, and the song lead-in follows SongPreviewPlayer.LeadInGain, so
the result sounds like the game.

usage: render_reveal_movie.py FRAMES_DIR OUTPUT.mp4
Needs numpy + soundfile (e.g. Tools/ai-chart/.venv) and ffmpeg.
"""
import json
import subprocess
import sys

import numpy as np
import soundfile as sf


def stereo(x):
    return x if x.ndim == 2 else np.stack([x, x], 1)


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def main(folder, output):
    cfg = json.load(open(f"{folder}/audio.json"))
    song, sr = sf.read(cfg["song"])
    song = stereo(song)
    duration = cfg["frames"] / cfg["fps"]
    mix = np.zeros((int(duration * sr) + 1, 2))

    def place(src, start, a, b, gain):
        i0, s0 = int(round(start * sr)), int(round(a * sr))
        s1 = min(len(src), int(round(b * sr)))
        n = min(s1 - s0, len(mix) - i0)
        if n > 0:
            mix[i0:i0 + n] += src[s0:s0 + n] * gain(np.arange(n) / sr)[:, None]

    for seg in cfg["segments"]:
        src = song if seg["name"] is None else stereo(sf.read(f"{cfg['assets']}/{seg['name']}")[0])
        length = (seg["to"] - seg["from"]) if seg["to"] >= 0 else len(src) / sr - seg["from"]
        if seg["stopAt"] >= 0:
            length = min(length, seg["stopAt"] - seg["start"] + seg["stopFade"])

        def gain(t, seg=seg, length=length):
            g = np.full_like(t, seg["volume"])
            if seg["fadeIn"] > 0:
                g *= np.clip(t / seg["fadeIn"], 0, 1)
            if seg["fadeOut"] > 0:
                g *= np.clip((length - t) / seg["fadeOut"], 0, 1)
            return g

        place(src, seg["start"], seg["from"], seg["from"] + length, gain)

    if "leadIn" in cfg:  # SongPreviewPlayer.LeadInGain, reaching previewMs exactly at coverAt
        cover, lead, white = cfg["leadIn"]
        begins, preview = cover - lead, cfg["previewMs"] / 1000

        def lead_gain(t):
            t = t + begins
            if white <= begins or white >= cover:
                return smooth((t - begins) / lead)
            return np.where(t <= white, 0.1 * smooth((t - begins) / (white - begins)),
                            0.1 + 0.9 * smooth((t - white) / (cover - white)))

        place(song, begins, preview - lead, preview - lead + duration - begins, lead_gain)

    knee = 0.9
    over = np.abs(mix) > knee
    mix[over] = np.sign(mix[over]) * (knee + 0.09 * np.tanh((np.abs(mix[over]) - knee) / 0.09))
    sf.write(f"{folder}/soundtrack.wav", mix, sr, subtype="PCM_16")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", str(cfg["fps"]),
                    "-i", f"{folder}/frame-%04d.png", "-i", f"{folder}/soundtrack.wav", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-shortest", output], check=True)
    print(f"{output}: {duration:.2f}s, limited {over.mean() * 100:.2f}% of samples")


if __name__ == "__main__":
    main(*sys.argv[1:3])
