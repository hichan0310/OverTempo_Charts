from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bms_audio_renderer import (
    collect_audio_events,
    is_audio_channel,
    resolve_sample_path,
    decode_sample,
    render_bms_audio,
)
from bms_to_overtempo import Timeline, parse_bms


class BmsAudioRendererTests(unittest.TestCase):
    def test_rejects_existing_sample_outside_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "outside.wav").write_bytes(b"x")
            folder = root / "package"
            folder.mkdir()
            with self.assertRaises(ValueError):
                resolve_sample_path(folder / "chart.bms", "../outside.wav")

    def test_resampling_preserves_duration_and_removes_aliasing(self) -> None:
        import numpy as np
        import soundfile as sf

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "tone.wav"
            t = np.arange(48000) / 48000
            sf.write(path, 0.5 * np.sin(2 * np.pi * 18000 * t), 48000)
            result = decode_sample(path, 24000, np, sf)
            self.assertEqual(result.shape, (24000, 2))
            self.assertLess(float(np.sqrt(np.mean(result[100:-100] ** 2))), 0.002)

    def test_renders_overlapping_keys_with_exact_timing(self) -> None:
        import numpy as np
        import soundfile as sf

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sf.write(root / "key.wav", np.full(800, 0.75), 8000, subtype="FLOAT")
            source = root / "chart.bms"
            source.write_text("#BPM 120\n#WAV01 key.wav\n#00101:01\n#00111:01\n")
            output = root / "mix.wav"
            count, warnings = render_bms_audio(source, output, sample_rate=8000, tail_seconds=0)
            data, rate = sf.read(output)
            self.assertEqual(count, 2)
            self.assertEqual(rate, 8000)
            self.assertEqual(data.shape, (16800, 2))
            self.assertTrue(np.all(data[:16000] == 0))
            self.assertAlmostEqual(float(data[16000, 0]), 0.98, places=4)
            self.assertEqual(len(warnings), 1)

    def test_audio_channel_detection(self) -> None:
        self.assertTrue(is_audio_channel("01"))
        self.assertTrue(is_audio_channel("11"))
        self.assertTrue(is_audio_channel("16"))
        self.assertTrue(is_audio_channel("51"))
        self.assertFalse(is_audio_channel("03"))
        self.assertFalse(is_audio_channel("08"))

    def test_collects_bgm_keys_and_long_note_samples(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("bgm.ogg", "key.wav", "long.ogg"):
                (root / name).write_bytes(b"placeholder")
            source = root / "chart.bms"
            text = (
                "#BPM 120\n"
                "#LNOBJ ZZ\n"
                "#WAV01 bgm.ogg\n"
                "#WAV02 key.wav\n"
                "#WAV03 long.ogg\n"
                "#WAVZZ Long_End\n"
                "#00101:01\n"
                "#00111:02\n"
                "#00151:03\n"
                "#00211:ZZ\n"
            )
            parsed = parse_bms(text)
            events, warnings = collect_audio_events(
                source,
                parsed,
                Timeline(parsed),
            )

        self.assertEqual(warnings, [])
        self.assertEqual([event.wav_id for event in events], ["01", "02", "03"])
        self.assertTrue(all(event.time_ms == 2000 for event in events))

    def test_resolves_case_insensitive_sample_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            actual = root / "Kick.OGG"
            actual.write_bytes(b"x")
            resolved = resolve_sample_path(root / "chart.bms", "kick.ogg")
            self.assertEqual(resolved, actual)

    def test_resolves_ogg_conversion_of_wav_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            actual = root / "Bgm_01.ogg"
            actual.write_bytes(b"x")
            resolved = resolve_sample_path(root / "chart.bms", "BGM_01.wav")
            self.assertEqual(resolved, actual)


if __name__ == "__main__":
    unittest.main()
