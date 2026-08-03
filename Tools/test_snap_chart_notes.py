import unittest

from Tools.snap_chart_notes import snap_chart, snap_time


class SnapChartNotesTests(unittest.TestCase):
    def test_snaps_to_coarse_declared_grid(self):
        data = {
            "timing": {"bpm": 250, "snapDiv": 48, "bpmChanges": []},
            "notes": [{"timeMs": 965, "lane": 0, "durationMs": 0}],
        }
        snap_chart(data, divisor=4)
        self.assertEqual(data["timing"]["snapDiv"], 4)
        self.assertEqual(data["notes"][0]["timeMs"], 960)

    def test_snaps_hold_tail(self):
        data = {
            "timing": {"bpm": 180, "snapDiv": 4, "bpmChanges": []},
            "notes": [{"timeMs": 1332, "lane": 0, "durationMs": 168}],
        }
        snap_chart(data)
        self.assertEqual(data["notes"][0]["timeMs"], 1333)
        self.assertEqual(data["notes"][0]["durationMs"], 167)

    def test_rounds_like_editor(self):
        self.assertEqual(snap_time(1333, [(0, 180)], 4), 1333)


if __name__ == "__main__":
    unittest.main()
