import unittest

from Tools.limit_chart_coef_per_measure import choose_notes


class ChooseNotesTests(unittest.TestCase):
    def test_selects_at_most_one_note_per_beat_and_four_per_measure(self):
        data = {
            "timing": {"bpm": 120, "bpmChanges": []},
            "notes": [
                {"timeMs": 0, "lane": 0, "baseSpeedupCoef": 1, "durationMs": 0},
                {"timeMs": 0, "lane": 1, "baseSpeedupCoef": 1, "durationMs": 0},
                {"timeMs": 250, "lane": 2, "baseSpeedupCoef": 1, "durationMs": 0},
                {"timeMs": 500, "lane": 1, "baseSpeedupCoef": 1, "durationMs": 0},
                {"timeMs": 1000, "lane": 2, "baseSpeedupCoef": 1, "durationMs": 0},
                {"timeMs": 1500, "lane": 3, "baseSpeedupCoef": 1, "durationMs": 0},
                {"timeMs": 1750, "lane": 0, "baseSpeedupCoef": 1, "durationMs": 0},
            ],
        }

        selected = choose_notes(data)

        self.assertEqual(4, len(selected))
        selected_times = [data["notes"][index]["timeMs"] for index in selected]
        self.assertEqual(len(selected_times), len(set(selected_times)))

    def test_never_promotes_an_existing_coef_zero_note(self):
        data = {
            "timing": {"bpm": 120, "bpmChanges": []},
            "notes": [
                {"timeMs": 0, "lane": 0, "baseSpeedupCoef": 0, "durationMs": 0},
                {"timeMs": 250, "lane": 1, "baseSpeedupCoef": 1, "durationMs": 0},
            ],
        }

        self.assertEqual({1}, choose_notes(data))


if __name__ == "__main__":
    unittest.main()
