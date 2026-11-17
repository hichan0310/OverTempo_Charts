from __future__ import annotations

import importlib.util
import copy
import json
import math
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))
from analyze import analyze, beat_grid, snap_grid
from build import compile_chart
from validate import evaluate


class AudioPipelineTests(unittest.TestCase):
    def analysis(self, events, template=None):
        timing = (template or self.template())["timing"]
        return {"schemaVersion": 1, "alignment": {
            "bpm": timing["bpm"], "offsetMs": timing.get("offsetMs", 0),
            "bpmChanges": timing.get("bpmChanges", []), "subdivisionsPerBeat": 4,
            "allowedSubdivisionsPerBeat": [4, 6, 8], "maxDeviationMs": 20},
            "events": [{**e, "audioMs": e["chartMs"] - timing.get("offsetMs", 0)} for e in events]}

    def template(self):
        return {
            "version": 2,
            "meta": {"title": "synthetic", "audioFileName": "test.wav", "mapper": "person"},
            "difficulty": {"name": "Normal", "level": 3, "lanes": 4},
            "timing": {"bpm": 120, "offsetMs": 0, "snapDiv": 4, "bpmChanges": []},
            "notes": [{"timeMs": 9000, "lane": 0, "durationMs": 0}],
            "speedLimitLines": [{"timeMs": 2500, "maxSpeed": 1.2}],
            "stageDeltaLines": [{"timeMs": 3000, "stageDelta": 1}],
        }

    def test_bpm_change_grid_restarts(self):
        timing = {"bpm": 120, "bpmChanges": [{"timeMs": 2000, "bpm": 240}]}
        entries = list(beat_grid(timing, 1850, 2300, 4))
        self.assertIn(2000, [e["chartMs"] for e in entries])
        self.assertIn(2063, [e["chartMs"] for e in entries])
        self.assertEqual(next(e for e in entries if e["chartMs"] == 2000)["beatKey"], "1:0")

    def test_grid_has_no_duplicate_on_change_boundary(self):
        timing = {"bpm": 120, "bpmChanges": [{"timeMs": 1999, "bpm": 240}]}
        entries = list(beat_grid(timing, 1900, 2200, 4))
        times = [e["chartMs"] for e in entries]
        self.assertEqual(len(times), len(set(times)))
        self.assertTrue(all(1900 <= t < 2200 for t in times))

    def test_chart_compile_and_original_immutability(self):
        template = self.template()
        analysis = {**self.analysis([
            {"id": "E0001", "chartMs": 1000, "beatKey": "0:2"},
            {"id": "E0002", "chartMs": 1125, "beatKey": "0:2"},
            {"id": "E0003", "chartMs": 1500, "beatKey": "0:3"},
        ]), "analysisId": "abc"}
        plan = {"schemaVersion": 1, "analysisId": "abc", "notes": [
            {"eventId": "E0001", "lanes": [0, 2]},
            {"eventId": "E0002", "lanes": [1]},
            {"eventId": "E0003", "lanes": [3]},
        ]}
        compiled, report = compile_chart(analysis, plan, template)
        self.assertTrue(report["valid"])
        self.assertEqual(len(compiled["notes"]), 4)
        self.assertEqual(sum(n["baseSpeedupCoef"] for n in compiled["notes"]), 2)
        self.assertEqual(template["notes"][0]["timeMs"], 9000)
        self.assertEqual(template["speedLimitLines"][0]["maxSpeed"], 1.2)
        self.assertEqual(compiled["speedLimitLines"], template["speedLimitLines"])
        self.assertEqual(compiled["stageDeltaLines"], template["stageDeltaLines"])
        self.assertEqual(compiled["timing"], template["timing"])
        self.assertEqual(report["grid"]["checkedNotes"], 4)
        self.assertTrue(all(n["durationMs"] == 0 for n in compiled["notes"]))

    def test_reject_nonexistent_event_and_second_acceleration(self):
        t = self.template()
        a = self.analysis([
            {"id": "E0001", "chartMs": 1000, "beatKey": "0:2"},
            {"id": "E0002", "chartMs": 1125, "beatKey": "0:2"},
        ])
        with self.assertRaises(ValueError):
            compile_chart(a, {"schemaVersion": 1, "notes": [{"eventId": "bad", "lanes": [0]}]}, t)
        with self.assertRaises(ValueError):
            compile_chart(a, {"schemaVersion": 1, "notes": [
                {"eventId": "E0001", "lanes": [0], "accelerate": True},
                {"eventId": "E0002", "lanes": [1], "accelerate": True},
            ]}, t)
        with self.assertRaises(ValueError):
            compile_chart(a, {"schemaVersion": 1, "notes": [
                {"eventId": "E0001", "lanes": [0, 4]},
            ]}, t)

    def test_compile_mixed_hold_and_tap_from_event_endpoints(self):
        # Given a held lane, a simultaneous tap and another lane during the hold.
        template = self.template()
        template["timing"].update(offsetMs=-42.5, bpmChanges=[{"timeMs": 1250, "bpm": 240}])
        before = copy.deepcopy(template)
        analysis = self.analysis([
            {"id": "start", "chartMs": 1000},
            {"id": "middle", "chartMs": 1250},
            {"id": "end", "chartMs": 1500},
        ], template)
        plan = {"schemaVersion": 1, "notes": [
            {"eventId": "start", "lanes": [0, 2], "holdEnds": {"0": "end"}},
            {"eventId": "middle", "lanes": [1]},
        ]}
        # When both endpoint coordinates come from validated measured events.
        chart, report = compile_chart(analysis, plan, template)
        # Then only the requested lane is held, with source settings intact.
        self.assertEqual([(n["lane"], n["durationMs"]) for n in chart["notes"]],
                         [(0, 500), (2, 0), (1, 0)])
        self.assertEqual(report["grid"]["checkedHoldEnds"], 1)
        self.assertEqual(report["stats"]["holds"], 1)
        self.assertEqual(template, before)
        for key in ("timing", "speedLimitLines", "stageDeltaLines"):
            self.assertEqual(chart[key], before[key])

    def test_compile_rejects_invalid_hold_references(self):
        # Given valid start/end candidates and malformed or unreviewed endings.
        base = self.analysis([
            {"id": "start", "chartMs": 1000},
            {"id": "end", "chartMs": 1500},
        ])
        cases = [
            ({"0": "missing"}, {}),
            ({"1": "end"}, {}),
            ({"0": "start"}, {}),
            ({"0": "end"}, {"chartMs": 875, "audioMs": 875}),
            ({"0": "end"}, {"chartMs": 1510, "audioMs": 1510}),
            ({"0": "end"}, {"reviewRequired": True}),
            ({"0": "end"}, {"deviationMs": 21}),
            ({"0": "end"}, {"audioMs": 1499}),
        ]
        for hold_ends, updates in cases:
            with self.subTest(hold_ends=hold_ends, updates=updates):
                analysis = copy.deepcopy(base)
                analysis["events"][1].update(updates)
                # When an invalid endpoint is requested.
                with self.assertRaises(ValueError):
                    compile_chart(analysis, {"schemaVersion": 1, "notes": [
                        {"eventId": "start", "lanes": [0], "holdEnds": hold_ends},
                    ]}, self.template())

    def test_validate_hold_tail_uses_grid_after_bpm_change(self):
        # Given a hold crossing a marker and a tap exactly at its release.
        chart = self.template()
        chart["timing"]["bpmChanges"] = [{"timeMs": 2000, "bpm": 240}]
        chart["notes"] = [
            {"timeMs": 1875, "lane": 0, "durationMs": 188},
            {"timeMs": 2063, "lane": 0, "durationMs": 0},
        ]
        # When validating start and release against their respective segments.
        report = evaluate(chart)
        # Then a release at the new segment's rounded tick is valid.
        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual(report["grid"]["checkedHoldEnds"], 1)

    def test_validate_rejects_invalid_hold_duration_and_tail(self):
        for duration in (-1, True, 1.5, "500", 501):
            with self.subTest(duration=duration):
                # Given a malformed duration or an off-grid release.
                chart = self.template()
                chart["notes"] = [{"timeMs": 1000, "lane": 0, "durationMs": duration}]
                # When validating, no snapping or duration repair is allowed.
                report = evaluate(chart)
                # Then the invalid hold is rejected.
                self.assertFalse(report["valid"])

    def test_validate_rejects_tap_inside_same_lane_hold(self):
        # Given a tap while the same lane is occupied by a hold.
        chart = self.template()
        chart["notes"] = [
            {"timeMs": 1000, "lane": 0, "durationMs": 500},
            {"timeMs": 1125, "lane": 0, "durationMs": 0},
        ]
        # When evaluating the combined lane occupancy.
        report = evaluate(chart)
        # Then the collision is rejected rather than hidden by valid start grids.
        self.assertFalse(report["valid"])
        self.assertTrue(any("overlap" in error for error in report["errors"]))

    def test_reject_analysis_plan_mismatch(self):
        analysis = {"schemaVersion": 1, "analysisId": "abc", "events": [
            {"id": "E0001", "chartMs": 1000, "beatKey": "0:2"}
        ]}
        with self.assertRaises(ValueError):
            compile_chart(analysis, {"schemaVersion": 1, "analysisId": "wrong", "notes": [
                {"eventId": "E0001", "lanes": [0]}
            ]}, self.template())

    @unittest.skipUnless(shutil.which("node"), "node is required for editor parity")
    def test_snap_matches_actual_editor_across_bpm_boundaries(self):
        # Given the actual editor functions, fractional markers and half ticks.
        editor = (SCRIPT_DIR.parent / "chart-editor" / "index.html").read_text()
        functions = editor.split("function normalizedBpmChanges(){", 1)[1].split(
            "function movePlayheadOnGrid(", 1)[0]
        functions = "function normalizedBpmChanges(){" + functions
        timing = {"bpm": 227, "bpmChanges": [{"timeMs": 1999.5, "bpm": 173}]}
        inputs = [0, 33.04, 125, 1990, 1999, 2000, 2001, 2070, 5000]
        for division in (4, 6, 8, 24, 32):
            state = {**timing, "snapDiv": division}
            script = ("const state=" + json.dumps(state) + ";" + functions +
                      "console.log(JSON.stringify(" + json.dumps(inputs) + ".map(t=>snapTime(t))));")
            # When snapping with the editor and with the analyzer.
            result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
            actual = [snap_grid(timing, t, division)["chartMs"] for t in inputs]
            # Then both use identical segment origins and integer rounding.
            self.assertEqual(actual, json.loads(result.stdout))

    def test_validate_checks_every_note_and_rejects_off_grid(self):
        # Given valid fine-grid ticks and a deliberately invalid final note.
        t = self.template()
        t["timing"]["bpmChanges"] = [{"timeMs": 1999, "bpm": 240}]
        t["notes"] = [{"timeMs": ms, "lane": 0, "durationMs": 0}
                      for ms in (125, 83, 63, 1999, 2062, 2070)]
        # When evaluating all notes.
        report = evaluate(t)
        # Then the last note is rejected, not rounded into place.
        self.assertFalse(report["valid"])
        self.assertEqual(report["grid"]["checkedNotes"], 6)
        self.assertEqual(report["grid"]["offGridNoteIndices"], [5])

    def test_compile_preserves_timing_acceleration_and_source(self):
        # Given non-default source timing and acceleration settings.
        t = self.template()
        t["timing"].update(offsetMs=-42.5, bpmChanges=[{"timeMs": 1999, "bpm": 240}])
        t["autoCoef"] = {"settings": {"enabled": True, "manualMultiplier": 1.7}, "curve": [
            {"timeMs": 0, "densityMultiplier": .5, "rampMultiplier": 1,
             "manualMultiplier": 1.7, "multiplier": .85},
            {"timeMs": 2000, "densityMultiplier": 1, "rampMultiplier": 1,
             "manualMultiplier": 1.7, "multiplier": 1.7}]}
        t["notes"] = [{"timeMs": 1000, "lane": 2, "baseSpeedupCoef": 0,
                      "speedupCoef": 0, "manualSpeedupCoefMultiplier": 2.3}]
        before = copy.deepcopy(t)
        a = self.analysis([{"id": "E1", "chartMs": 1000, "beatKey": "wrong"}], t)
        # When compiling a chord, including an existing coordinate.
        chart, report = compile_chart(a, {"schemaVersion": 1, "notes": [
            {"eventId": "E1", "lanes": [0, 2]}]}, t)
        # Then source settings and matching note coefficients remain intact.
        self.assertEqual(t, before)
        self.assertEqual(chart["timing"], before["timing"])
        self.assertEqual(chart["autoCoef"], before["autoCoef"])
        self.assertEqual(chart["notes"][0]["autoSpeedupCoefMultiplier"], 1.275)
        self.assertEqual(chart["notes"][1]["manualSpeedupCoefMultiplier"], 2.3)
        self.assertEqual(chart["notes"][1]["baseSpeedupCoef"], 0)
        self.assertTrue(report["valid"])

    def test_compile_rejects_timing_mismatch_and_plan_overrides(self):
        # Given an analysis from the correct template and a valid selection.
        a = self.analysis([{"id": "E1", "chartMs": 1000, "beatKey": "0:2"}])
        p = {"schemaVersion": 1, "notes": [{"eventId": "E1", "lanes": [0]}]}
        for key, value in (("bpm", 150), ("offsetMs", 30),
                           ("bpmChanges", [{"timeMs": 1000, "bpm": 140}])):
            t = self.template()
            t["timing"][key] = value
            # When the reusable compiler receives a different timing source.
            with self.assertRaisesRegex(ValueError, "timing mismatch"):
                compile_chart(a, p, t)
        for extra in ({"timing": {}}, {"autoCoef": {}}):
            with self.assertRaisesRegex(ValueError, "cannot override"):
                compile_chart(a, {**p, **extra}, self.template())
        for extra in ({"timeMs": 1001}, {"accelerate": True}):
            with self.assertRaisesRegex(ValueError, "may only select"):
                compile_chart(a, {**p, "notes": [{**p["notes"][0], **extra}]}, self.template())

    def test_compile_rejects_off_grid_and_review_events(self):
        for changes in ({"chartMs": 1010, "audioMs": 1010},
                        {"reviewRequired": True}, {"deviationMs": 21},
                        {"audioMs": 999}):
            # Given an invalid candidate that still has a real event ID.
            a = self.analysis([{"id": "E1", "chartMs": 1000, "beatKey": "0:2"}])
            a["events"][0].update(changes)
            # When selected, compilation rejects it rather than snapping it.
            with self.assertRaises(ValueError):
                compile_chart(a, {"schemaVersion": 1, "notes": [
                    {"eventId": "E1", "lanes": [0]}]}, self.template())

    def test_attack_first_matching_handles_offsets_fine_grids_and_review(self):
        import numpy as np
        # Given exact audio feature attacks, including one far from every grid.
        for offset in (-100, 100.5, .1):
            track = {"start_sec": 0, "frame_sec": .0005, "duration_sec": 2}
            peaks = np.zeros(4000)
            for chart_ms in (1000, 1083, 1187.5, 1042):
                peaks[round((chart_ms - offset) * 2)] = 1
            track.update({name: peaks for name in ("attack", "onset", "low", "mid", "high", "rms")})
            track["chroma"] = np.ones((12, len(peaks)))
            track["attacks"] = [{"audioSec": frame * track["frame_sec"], "strength": 1}
                                for frame in np.flatnonzero(peaks)]
            t = self.template()
            t["timing"]["offsetMs"] = offset
            with tempfile.TemporaryDirectory() as td:
                base = Path(td)
                audio = base / "test.wav"
                audio.write_bytes(b"feature test")
                chart_path = base / "template.json"
                chart_path.write_text(json.dumps(t))
                # Only the waveform-to-features seam is fixed; matching is real.
                with patch("analyze.describe_track", return_value=track):
                    result = analyze(chart_path, audio, duration_sec=2)
                    limited = analyze(chart_path, audio, duration_sec=2, max_events=1)
            # Then coarse, triplet and fine ticks are selected, but not the outlier.
            self.assertEqual([e["chartMs"] for e in result["events"]], [1000, 1083, 1188])
            self.assertEqual([e["subdivisionsPerBeat"] for e in result["events"]], [4, 6, 8])
            self.assertEqual(len(result["reviewRequired"]), 1)
            for e in result["events"]:
                self.assertAlmostEqual(e["chartMs"], e["audioMs"] + offset)
                self.assertAlmostEqual(e["deviationMs"], e["attackAudioMs"] + offset - e["chartMs"])
            plan = {"schemaVersion": 1, "analysisId": result["analysisId"], "notes": [
                {"eventId": e["id"], "lanes": [i % 4]} for i, e in enumerate(result["events"])]}
            self.assertNotEqual(result["analysisId"], limited["analysisId"])
            with self.assertRaisesRegex(ValueError, "plan.analysisId"):
                compile_chart(limited, plan, t)
            chart, report = compile_chart(result, plan, t)
            self.assertEqual(report["reviewRequired"], result["reviewRequired"])
            self.assertEqual(report["grid"]["checkedNotes"], len(chart["notes"]))

    @unittest.skipUnless(importlib.util.find_spec("soundfile") and importlib.util.find_spec("librosa"),
                         "optional audio dependencies missing")
    def test_legato_pitch_changes_survive_an_earlier_loud_accent(self):
        import numpy as np
        import soundfile as sf
        sr = 22050
        time = np.arange(sr * 3) / sr
        frequency = np.where(time < 1, 523.251,
                             np.where(time < 1.5, 554.365, 622.254))
        phase = np.cumsum(frequency) * 2 * np.pi / sr
        y = .2 * np.sin(phase) * np.minimum(time / .1, 1) * np.minimum((3 - time) / .1, 1)
        y[round(.5 * sr)] += .8
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            audio = base / "legato.wav"
            chart = base / "template.json"
            sf.write(audio, y, sr, subtype="FLOAT")
            chart.write_text(json.dumps(self.template()))
            data = analyze(chart, audio, duration_sec=3, threshold=.2,
                           fine_subdivisions=(), max_deviation_ms=12)
        by_time = {e["chartMs"]: e for e in data["events"]}
        for target in (1000, 1500):
            self.assertIn(target, by_time, "upper pitch change must not be hidden by an earlier accent")
            self.assertLessEqual(abs(by_time[target]["attackAudioMs"] - target), 8)

    @unittest.skipUnless(importlib.util.find_spec("soundfile") and importlib.util.find_spec("librosa"),
                         "optional audio dependencies missing")
    def test_known_attack_is_not_lost_or_replaced_by_late_decay(self):
        import numpy as np
        import soundfile as sf
        sr = 22050
        for rise_ms in (0, 1, 10, 30, 60):
            with self.subTest(rise_ms=rise_ms), tempfile.TemporaryDirectory() as td:
                base = Path(td)
                y = np.zeros(sr * 3, dtype="float32")
                if rise_ms == 0:
                    y[sr] = .8
                else:
                    time = np.arange(round(sr * .3)) / sr
                    envelope = np.minimum(time / (rise_ms / 1000), 1) * np.exp(-time * 12)
                    y[sr:sr + len(time)] = .5 * np.sin(2 * np.pi * 1200 * time) * envelope
                audio = base / "known.wav"
                chart = base / "template.json"
                sf.write(audio, y, sr, subtype="FLOAT")
                chart.write_text(json.dumps(self.template()))
                data = analyze(chart, audio, duration_sec=2.5, threshold=.2,
                               fine_subdivisions=(), max_deviation_ms=12)
                self.assertEqual([e["chartMs"] for e in data["events"]], [1000],
                                 "known attack must not vanish or become a late decay note")
                self.assertLessEqual(abs(data["events"][0]["attackAudioMs"] - 1000), 8)

    @unittest.skipUnless(importlib.util.find_spec("soundfile") and importlib.util.find_spec("librosa"),
                         "optional audio dependencies missing")
    def test_synthetic_clicks_map_to_grid(self):
        import numpy as np
        import soundfile as sf
        sr = 22050
        y = np.zeros(sr * 4, dtype="float32")
        for sec in (1.0, 1.5, 2.0, 3.0):
            idx = int(sec * sr)
            dur = int(.035 * sr)
            time = np.arange(dur, dtype="float32") / sr
            y[idx:idx + dur] += .7 * np.sin(2 * np.pi * 1100 * time) * np.exp(-time * 110)
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            audio = base / "test.wav"
            chart_path = base / "dummy.4k-speedcoef.json"
            sf.write(audio, y, sr)
            chart_path.write_text(json.dumps(self.template()))
            data = analyze(chart_path, audio, start_sec=0, duration_sec=3.5, threshold=.16, max_events=100)
            self.assertGreaterEqual(len(data["events"]), 3)
            found = [e["chartMs"] for e in data["events"]]
            for millis in (1000, 1500, 2000):
                self.assertLessEqual(min(abs(t - millis) for t in found), 125)
            self.assertTrue(all(e["chartMs"] >= 0 for e in data["events"]))
            self.assertEqual(data["alignment"]["offsetMs"], 0)
            self.assertEqual(len(data["analysisId"]), 20)
            analysis_path = base / "analysis.json"
            plan_path = base / "plan.json"
            output = base / "draft.4k-speedcoef.json"
            analysis_path.write_text(json.dumps(data))
            plan_path.write_text(json.dumps({
                "schemaVersion": 1, "analysisId": data["analysisId"],
                "notes": [{"eventId": e["id"], "lanes": [i % 4]}
                          for i, e in enumerate(data["events"])]}))
            subprocess.run([sys.executable, str(SCRIPT_DIR / "build.py"),
                            "--analysis", str(analysis_path), "--plan", str(plan_path),
                            "--template", str(chart_path), "--output", str(output)],
                           check=True, capture_output=True, text=True)
            result = subprocess.run([sys.executable, str(SCRIPT_DIR / "validate.py"), str(output)],
                                    check=True, capture_output=True, text=True)
            report = json.loads(result.stdout)
            self.assertTrue(report["valid"])
            self.assertEqual(report["grid"]["checkedNotes"], len(data["events"]))
            generated = json.loads(output.read_text())
            self.assertEqual(generated["timing"], self.template()["timing"])
            self.assertEqual(json.loads(output.with_suffix(".review.json").read_text())["reviewRequired"],
                             data["reviewRequired"])


if __name__ == "__main__":
    unittest.main()
