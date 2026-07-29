from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from osu_mania_to_overtempo import convert_osu


SAMPLE = """\
osu file format v14

[General]
AudioFilename: audio.ogg
PreviewTime: 1000
Mode: 3

[Editor]
BeatDivisor: 8

[Metadata]
Title:Test
Artist:Artist
Creator:Mapper
Version:[4K] Normal
BeatmapID:12
BeatmapSetID:34

[Difficulty]
CircleSize:4
OverallDifficulty:7

[TimingPoints]
500,500,4,2,0,100,1,0
2500,250,4,2,0,100,1,0

[HitObjects]
64,192,1000,1,0,0:0:0:0:
448,192,2000,128,0,3000:0:0:0:0:
"""


class OsuConverterTests(unittest.TestCase):
    def test_conversion(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "test.osu"
            source.write_text(SAMPLE, encoding="utf-8")
            chart = convert_osu(source)

        self.assertEqual(chart["timing"]["bpm"], 120)
        self.assertEqual(chart["timing"]["offsetMs"], 1500)
        self.assertEqual(chart["timing"]["bpmChanges"], [{"timeMs": 4000, "bpm": 240}])
        self.assertEqual(chart["timing"]["snapDiv"], 8)
        self.assertEqual(chart["notes"][0]["timeMs"], 2500)
        self.assertEqual(chart["notes"][0]["lane"], 0)
        self.assertEqual(chart["notes"][1]["timeMs"], 3500)
        self.assertEqual(chart["notes"][1]["lane"], 3)
        self.assertEqual(chart["notes"][1]["durationMs"], 1000)

    def test_rejects_non_4k(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "test.osu"
            source.write_text(SAMPLE.replace("CircleSize:4", "CircleSize:7"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not native 4K"):
                convert_osu(source)

    def test_opt_in_7k_fold_unions_colliding_lanes(self) -> None:
        seven = SAMPLE.replace("CircleSize:4", "CircleSize:7").replace(
            "64,192,1000,1,0,0:0:0:0:",
            "36,192,1000,1,0,0:0:0:0:\n"
            "109,192,1000,1,0,0:0:0:0:",
        )
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "seven.osu"
            source.write_text(seven, encoding="utf-8")
            chart = convert_osu(source, fold_7k=True)

        self.assertEqual(len(chart["notes"]), 2)
        self.assertEqual(chart["notes"][0]["lane"], 0)
        self.assertIn("7K->4K", chart["meta"]["extra"])

    def test_infers_finer_grid_than_saved_editor_divisor(self) -> None:
        fine_sample = SAMPLE.replace(
            "64,192,1000,1,0,0:0:0:0:",
            "64,192,1000,1,0,0:0:0:0:\n"
            "192,192,511,1,0,0:0:0:0:",
        ).replace("BeatDivisor: 8", "BeatDivisor: 4")
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "fine.osu"
            source.write_text(fine_sample, encoding="utf-8")
            chart = convert_osu(source)

        self.assertEqual(chart["timing"]["snapDiv"], 48)


if __name__ == "__main__":
    unittest.main()
