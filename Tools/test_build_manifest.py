#!/usr/bin/env python3
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_manifest


class EncryptedSongValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.song = Path(self.temp.name) / "arg-01"
        self.song.mkdir()
        self.meta = {"id": "arg-01", "enabled": True, "encrypted": True}
        envelope = {
            "schemaVersion": 1,
            "argId": "arg_self_test",
            "cipher": "AES-256-CBC+HMAC-SHA256",
            "kdf": "PBKDF2-HMAC-SHA256",
            "iterations": 600000,
            "salt": "AA==",
            "iv": "AA==",
            "ciphertext": "AA==",
            "tag": "AA==",
        }
        (self.song / "chart.otchart").write_text(json.dumps(envelope), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_accepts_encrypted_only_song(self):
        build_manifest.validate_song(self.song, self.meta)

    def test_rejects_plaintext_leak(self):
        (self.song / "leaked.4k-speedcoef.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(SystemExit):
            build_manifest.validate_song(self.song, self.meta)

    def test_backup_files_are_never_zipped(self):
        backup = self.song / "chart.4k-speedcoef.json.bak"
        backup.write_text("secret", encoding="utf-8")
        self.assertFalse(build_manifest.should_zip(backup))


class SpeedcoefValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.song = Path(self.temp.name) / "grid-song"
        self.song.mkdir()
        self.meta = {"id": "grid-song", "enabled": True}

    def tearDown(self):
        self.temp.cleanup()

    def test_ignores_snap_grid_and_possible_snap_collisions(self):
        (self.song / "chart.4k-speedcoef.json").write_text(
            json.dumps(
                {
                    "timing": {"bpm": 227, "snapDiv": 2, "bpmChanges": []},
                    "notes": [
                        {"timeMs": 90990, "lane": 1, "durationMs": 0},
                        {"timeMs": 91122, "lane": 1, "durationMs": 0},
                    ],
                }
            ),
            encoding="utf-8",
        )
        build_manifest.validate_song(self.song, self.meta)

    def test_empty_chart_requires_explicit_opt_in(self):
        (self.song / "draft.4k-speedcoef.json").write_text(
            json.dumps({"notes": [], "meta": {"audioFileName": "song.wav"}}),
            encoding="utf-8",
        )
        (self.song / "song.wav").write_bytes(b"audio")
        with self.assertRaises(SystemExit):
            build_manifest.validate_song(self.song, self.meta)

        self.meta["allowEmptyChart"] = True
        build_manifest.validate_song(self.song, self.meta)

    def test_release_zip_preserves_images_and_omits_editor_cover_url(self):
        chart = self.song / "chart.4k-speedcoef.json"
        chart.write_text(
            json.dumps({"meta": {"title": "Example", "coverDataUrl": "data:image/png;base64,abc"}, "notes": []}),
            encoding="utf-8",
        )
        (self.song / "cover.png").write_bytes(b"image")
        (self.song / "bg.JPG").write_bytes(b"image")
        (self.song / "song.wav").write_bytes(b"audio")
        output = Path(self.temp.name) / "output"
        output.mkdir()

        archive_path = build_manifest.build_song_zip(
            Path(self.temp.name), self.song, "grid-song", output, "song.zip"
        )
        with zipfile.ZipFile(archive_path) as archive:
            self.assertEqual(
                sorted(archive.namelist()),
                ["grid-song/bg.JPG", "grid-song/chart.4k-speedcoef.json", "grid-song/cover.png", "grid-song/song.wav"],
            )
            self.assertEqual(archive.read("grid-song/cover.png"), b"image")
            packaged_chart = json.loads(archive.read("grid-song/chart.4k-speedcoef.json"))
            self.assertEqual(packaged_chart["meta"], {"title": "Example"})
        self.assertEqual(json.loads(chart.read_text())["meta"]["coverDataUrl"], "data:image/png;base64,abc")


if __name__ == "__main__":
    unittest.main()
