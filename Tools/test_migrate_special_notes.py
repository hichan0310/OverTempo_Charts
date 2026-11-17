import unittest
from migrate_special_notes import convert_chart


class SpecialMigrationTests(unittest.TestCase):
    def test_dense_delta_preserves_total_and_ordinary_notes(self):
        notes = [{'timeMs': 100, 'lane': 0, 'durationMs': 900, 'speedupCoef': .5}]
        chart = {'notes': notes, 'meta': {'title': 'example'}, 'stageDeltaLines': [
            {'timeMs': 100 + i * 50, 'stageDelta': -.2} for i in range(10)]}
        result = convert_chart(chart)
        self.assertEqual(result['notes'], notes)
        self.assertEqual(result['meta'], chart['meta'])
        self.assertEqual(result['specialNotes'], [{'timeMs': 100, 'durationMs': 450, 'effect': 'delta', 'speedDelta': -.13}])
        self.assertEqual(len(chart['stageDeltaLines']), 10)
        self.assertNotIn('stageDeltaLines', result)
        self.assertEqual(convert_chart(result), result)

    def test_sparse_limits_and_dense_ramp(self):
        limits = [{'timeMs': 0, 'maxSpeed': 2}, {'timeMs': 1000, 'maxSpeed': 1.8},
                  {'timeMs': 1050, 'maxSpeed': 1.7}, {'timeMs': 1100, 'maxSpeed': 1.6},
                  {'timeMs': 3000, 'maxSpeed': 1}]
        result = convert_chart({'speedLimitLines': limits})['specialNotes']
        self.assertEqual([n['durationMs'] for n in result], [0, 100, 0])
        self.assertNotIn('startMaxSpeed', result[1])
        self.assertEqual(result[1]['maxSpeed'], 1.6)

    def test_direction_changes_and_two_events_stay_separate(self):
        lines = [{'timeMs': 100, 'stageDelta': 1}, {'timeMs': 150, 'stageDelta': -1},
                 {'timeMs': 200, 'stageDelta': -1}]
        self.assertEqual(len(convert_chart({'stageDeltaLines': lines})['specialNotes']), 3)

    def test_existing_holds_and_labels_survive(self):
        note = {'timeMs': 10, 'durationMs': 1000, 'stageDelta': -3, 'label': 'wind'}
        result = convert_chart({'stageDeltaLines': [note]})['specialNotes'][0]
        self.assertEqual(result, {'timeMs':10,'durationMs':1000,'speedDelta':-.195,'label':'wind','effect':'delta'})


class SpeedChordCleanupTests(unittest.TestCase):
    @staticmethod
    def chord(time, coefficient=0, duration=0):
        return [dict(timeMs=time, lane=lane, speedupCoef=coefficient,
                     baseSpeedupCoef=coefficient, durationMs=duration) for lane in range(4)]

    def test_exact_and_offset_markers_become_special_only(self):
        for time in [1000, 949]:
            special = [{'timeMs': 1000, 'durationMs': 400, 'effect': 'limit', 'maxSpeed': 1}]
            source = {'notes': self.chord(time), 'specialNotes': special}
            result = convert_chart(source, remove_speed_markers=True)
            self.assertEqual(result['notes'], [])
            self.assertEqual(result['specialNotes'], special)
            self.assertEqual(len(source['notes']), 4)
            self.assertEqual(convert_chart(result, remove_speed_markers=True), result)

    def test_musical_chords_holds_and_partial_chords_are_kept(self):
        for notes in [self.chord(1000, 1), self.chord(1100), self.chord(1000, 0, 500), self.chord(1000)[:2]]:
            source = {'notes': notes, 'specialNotes': [{'timeMs': 1000, 'effect': 'delta', 'speedDelta': -.13}]}
            self.assertEqual(convert_chart(source, remove_speed_markers=True)['notes'], notes)

    def test_cleanup_is_opt_in_for_intentional_overlaps(self):
        source = {'notes': self.chord(1000), 'specialNotes': [{'timeMs': 1000, 'effect': 'delta', 'speedDelta': -.13}]}
        self.assertEqual(convert_chart(source)['notes'], source['notes'])

    def test_legacy_events_are_converted_before_marker_cleanup(self):
        source = {'notes': self.chord(1000), 'speedLimitLines': [{'timeMs': 1000, 'maxSpeed': 1.2}]}
        result = convert_chart(source, remove_speed_markers=True)
        self.assertEqual(result['notes'], [])
        self.assertEqual(result['specialNotes'][0]['maxSpeed'], 1.2)


class SpecialOverlapTests(unittest.TestCase):
    def test_every_intersecting_note_is_removed_including_tails(self):
        notes = [{'timeMs': time, 'durationMs': duration, 'lane': lane, 'speedupCoef': 1}
                 for time, duration, lane in [(500, 0, 0), (700, 0, 1), (400, 100, 2),
                                               (1000, 0, 3), (1001, 0, 0), (399, 100, 1)]]
        source = {'notes': notes, 'specialNotes': [{'timeMs': 500, 'durationMs': 500, 'effect': 'limit', 'maxSpeed': 1}]}
        result = convert_chart(source, remove_overlaps=True)
        self.assertEqual(result['notes'], notes[-2:])
        self.assertEqual(result['specialNotes'], source['specialNotes'])
        self.assertEqual(convert_chart(result, remove_overlaps=True), result)


if __name__ == '__main__':
    unittest.main()
