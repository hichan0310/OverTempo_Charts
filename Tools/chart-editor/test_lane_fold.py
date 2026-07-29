from __future__ import annotations

import unittest

from lane_fold import fold_notes, target_lane


def note(time_ms: int, lane: int, duration_ms: int = 0) -> dict:
    return {"timeMs": time_ms, "lane": lane, "durationMs": duration_ms}


class LaneFoldTests(unittest.TestCase):
    def test_balanced_7k_mapping_preserves_geometry(self) -> None:
        self.assertEqual(
            [target_lane(lane, 7) for lane in range(7)],
            [0, 0, 1, 2, 2, 3, 3],
        )

    def test_colliding_taps_become_one_tap(self) -> None:
        folded, stats = fold_notes([note(100, 0), note(100, 1)], 7)
        self.assertEqual(folded, [note(100, 0)])
        self.assertEqual(stats.duplicate_taps, 1)

    def test_overlapping_holds_union_and_cover_taps(self) -> None:
        folded, stats = fold_notes(
            [
                note(100, 0, 200),
                note(200, 1, 300),
                note(250, 0),
                note(600, 1),
            ],
            7,
        )
        self.assertEqual(folded, [note(100, 0, 400), note(600, 0)])
        self.assertEqual(stats.merged_holds, 1)
        self.assertEqual(stats.taps_inside_holds, 1)


if __name__ == "__main__":
    unittest.main()
