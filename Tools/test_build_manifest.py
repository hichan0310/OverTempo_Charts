#!/usr/bin/env python3
import json
import sys
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
