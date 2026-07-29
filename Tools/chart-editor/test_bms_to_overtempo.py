from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bms_to_overtempo import convert_bms


SAMPLE = """\
#PLAYER 1
#TITLE Parser Test
#ARTIST Test Artist
#BPM 120
#BPM01 240
#STOP01 48
#LNOBJ ZZ
#PLAYLEVEL 5
#00111:0100
#00112:010001ZZ
#00113:0100
#00114:0100
#00108:0001
#00202:0.5
#00251:0101
#00309:0100
#00411:0100
"""


class BmsConverterTests(unittest.TestCase):
    def test_notes_timing_bpm_long_notes_and_stop(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "sample.bms"
            source.write_text(SAMPLE, encoding="utf-8")
            chart, warnings = convert_bms(source)

        self.assertEqual(chart["meta"]["title"], "Parser Test")
        self.assertEqual(chart["meta"]["artist"], "Test Artist")
        self.assertEqual(chart["timing"]["bpm"], 120)
        self.assertEqual(chart["timing"]["bpmChanges"], [{"timeMs": 3000, "bpm": 240.0}])
        self.assertEqual(len(chart["notes"]), 7)

        lane_two_hold = next(
            note
            for note in chart["notes"]
            if note["lane"] == 1 and note["durationMs"] > 0
        )
        self.assertEqual(lane_two_hold["timeMs"], 3000)
        self.assertEqual(lane_two_hold["durationMs"], 250)

        channel_hold = next(
            note
            for note in chart["notes"]
            if note["lane"] == 0 and note["durationMs"] > 0
        )
        self.assertEqual(channel_hold["timeMs"], 3500)
        self.assertEqual(channel_hold["durationMs"], 250)

        # STOP01=48 at 240 BPM delays later timestamps by 250ms.
        self.assertEqual(chart["notes"][-1]["timeMs"], 5250)
        self.assertTrue(any("STOP" in warning for warning in warnings))

    def test_rejects_unsafe_7k_autodetection(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "seven.bms"
            source.write_text(
                "#BPM 120\n"
                + "\n".join(f"#001{channel}:01" for channel in ("11", "12", "13", "14", "15")),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "safe 4K detection failed"):
                convert_bms(source)

    def test_opt_in_7k_fold_unions_colliding_lanes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "seven.bms"
            source.write_text(
                "#BPM 120\n"
                + "\n".join(
                    f"#001{channel}:01"
                    for channel in ("11", "12", "13", "14", "15", "18", "19")
                ),
                encoding="utf-8",
            )
            chart, warnings = convert_bms(source, fold_7k=True)

        self.assertEqual(len(chart["notes"]), 4)
        self.assertEqual(
            [note["lane"] for note in chart["notes"]],
            [0, 1, 2, 3],
        )
        self.assertTrue(any("7K->4K" in warning for warning in warnings))


if __name__ == "__main__":
    unittest.main()
