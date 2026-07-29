from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bms_audio_renderer import (
    collect_audio_events,
    is_audio_channel,
    resolve_sample_path,
)
from bms_to_overtempo import Timeline, parse_bms


class BmsAudioRendererTests(unittest.TestCase):
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
