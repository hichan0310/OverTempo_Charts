#!/usr/bin/env python3
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_manifest


class EncryptedSongValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.arg_id = "0123456789abcdef0123456789abcdef"
        self.song = Path(self.temp.name) / self.arg_id
        self.song.mkdir()
        self.meta = {"id": self.arg_id, "enabled": True, "encrypted": True,
                     "publicTitle": "Encrypted Content", "encryptedAssets": {"End_Time_BMS.wav": "audio.wav"}}
        envelope = {
            "schemaVersion": 1,
            "argId": self.arg_id,
            "cipher": "AES-256-CBC+HMAC-SHA256",
            "kdf": "PBKDF2-HMAC-SHA256",
            "iterations": 600000,
            "salt": "AA==",
            "iv": "AA==",
            "ciphertext": "AA==",
            "tag": "AA==",
        }
        (self.song / f"{self.arg_id}.otchart").write_text(json.dumps(envelope), encoding="utf-8")
        (self.song / "End_Time_BMS.wav").write_bytes(b"audio")
        (self.song / "song.patch.json").write_text(json.dumps(self.meta), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_accepts_encrypted_only_song(self):
        build_manifest.validate_song(self.song, self.meta)

    def test_packages_only_ciphertext_and_generic_media_from_plaintext_source(self):
        (self.song / "End_Time.4k-speedcoef.json").write_text('{"meta":{"title":"End Time"}}', encoding="utf-8")
        (self.song / "End_Time.4k-speedcoef.json.bak").write_text("secret backup", encoding="utf-8")
        build_manifest.validate_song(self.song, self.meta)
        output = Path(self.temp.name) / "output"
        output.mkdir()
        archive = build_manifest.build_song_zip(Path(self.temp.name), self.song, self.arg_id,
                                                output, "release.zip", self.meta)
        with zipfile.ZipFile(archive) as package:
            self.assertEqual(sorted(package.namelist()),
                             [f"{self.arg_id}/{self.arg_id}.otchart", f"{self.arg_id}/audio.wav",
                              f"{self.arg_id}/song.patch.json"])
            self.assertNotIn(b"End Time", package.read(f"{self.arg_id}/song.patch.json"))

    def test_rejects_unmapped_media(self):
        (self.song / "endtime_cover.png").write_bytes(b"cover")
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


class CreatorReleaseTests(unittest.TestCase):
    def test_creator_release_excludes_arg_assets_and_retires_previous_copy(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            normal = root / "Songs" / "Visible"
            hidden = root / "Songs" / "Secret"
            for folder in (normal, hidden): folder.mkdir(parents=True)
            (normal / "song.patch.json").write_text(json.dumps({"id":"visible"}))
            (normal / "test.4k-speedcoef.json").write_text(json.dumps({"notes":[{"timeMs":0,"lane":0}]}))
            hidden_id = "a" * 32
            (hidden / "song.patch.json").write_text(json.dumps({"id":hidden_id,"encrypted":True,"retireSongIds":["old-hidden"]}))
            (hidden / "secret.otchart").write_text("private cipher")
            (hidden / "secret.wav").write_text("private audio")
            (hidden / "secret.png").write_text("private art")
            output = root / "output" / "songs"
            output.mkdir(parents=True)
            (output / (hidden_id + "_old.zip")).write_text("stale release")
            with patch.object(build_manifest, "git", return_value="b" * 40), patch("sys.argv", ["build_manifest.py", "--repo", str(root), "--audience", "creators"]):
                self.assertEqual(build_manifest.main(),0)
            manifest = json.loads((root / "output" / "manifest.json").read_text())
            self.assertEqual(manifest["audience"], "creators")
            self.assertEqual([song["id"] for song in manifest["songs"]],["visible"])
            self.assertEqual(set(manifest["removed"]), {hidden_id,"old-hidden"})
            self.assertEqual(len(list(output.iterdir())),1)
            self.assertTrue((hidden / "secret.otchart").exists())


if __name__ == "__main__":
    unittest.main()
