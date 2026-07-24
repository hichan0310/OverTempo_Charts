from __future__ import annotations

import base64
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


SERVER_PATH = Path(__file__).with_name("server.py")
SPEC = importlib.util.spec_from_file_location("overtempo_chart_editor_server", SERVER_PATH)
assert SPEC and SPEC.loader
server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(server)


def valid_envelope() -> dict:
    return {
        "schemaVersion": 1,
        "argId": "arg_test",
        "cipher": "AES-256-CBC+HMAC-SHA256",
        "kdf": "PBKDF2-HMAC-SHA256",
        "iterations": 600000,
        "salt": base64.b64encode(bytes(range(16))).decode("ascii"),
        "iv": base64.b64encode(bytes(range(16, 32))).decode("ascii"),
        "ciphertext": base64.b64encode(bytes(range(32))).decode("ascii"),
        "tag": base64.b64encode(bytes(range(32))).decode("ascii"),
    }


class EncryptedChartServerTests(unittest.TestCase):
    def test_release_filename_replaces_plain_chart_suffix(self) -> None:
        self.assertEqual(
            server.encrypted_chart_filename("Song_Hard.4k-speedcoef.json"),
            "Song_Hard.otchart",
        )

    def test_valid_envelope_is_accepted(self) -> None:
        envelope = valid_envelope()
        self.assertIs(server.validate_encrypted_envelope(envelope), envelope)

    def test_invalid_arg_id_is_rejected(self) -> None:
        envelope = valid_envelope()
        envelope["argId"] = "ARG Secret"
        with self.assertRaisesRegex(ValueError, "argId"):
            server.validate_encrypted_envelope(envelope)

    def test_invalid_binary_lengths_are_rejected(self) -> None:
        envelope = valid_envelope()
        envelope["tag"] = base64.b64encode(b"short").decode("ascii")
        with self.assertRaisesRegex(ValueError, "tag must be 32 bytes"):
            server.validate_encrypted_envelope(envelope)

    def test_encrypted_write_round_trips_without_plaintext_backup(self) -> None:
        envelope = valid_envelope()
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "chart.otchart"
            server.write_encrypted_chart(path, envelope)
            self.assertEqual(json.loads(path.read_text("utf-8")), envelope)
            self.assertEqual([item.name for item in path.parent.iterdir()], [path.name])

    def test_streaming_song_create_writes_audio_and_chart(self) -> None:
        previous_songs_dir = server.SONGS_DIR
        with tempfile.TemporaryDirectory() as temp_dir:
            server.SONGS_DIR = Path(temp_dir)
            try:
                audio = b"RIFF-test-audio"
                result = server.create_song_from_stream(
                    io.BytesIO(audio),
                    len(audio),
                    song_name="Aleph-0",
                    song_id="aleph-0",
                    title="Aleph-0",
                    artist="LeaF",
                    audio_filename="127 Aleph-0(2022).wav",
                    bpm=250,
                    offset_ms=0,
                    difficulty_name="Normal",
                    difficulty_level=1,
                )
                song_dir = Path(temp_dir) / "Aleph-0"
                self.assertEqual((song_dir / result["audio"]).read_bytes(), audio)
                chart = json.loads((song_dir / result["chart"]).read_text("utf-8"))
                self.assertEqual(chart["meta"]["artist"], "LeaF")
                self.assertEqual(chart["timing"]["bpm"], 250)
                self.assertEqual(chart["meta"]["audioFileName"], "127 Aleph-0(2022).wav")
                patch = json.loads((song_dir / "song.patch.json").read_text("utf-8"))
                self.assertEqual(
                    patch,
                    {
                        "id": "aleph-0",
                        "title": "Aleph-0",
                        "artist": "LeaF",
                        "enabled": True,
                    },
                )
            finally:
                server.SONGS_DIR = previous_songs_dir

    def test_interrupted_upload_leaves_no_partial_song(self) -> None:
        previous_songs_dir = server.SONGS_DIR
        with tempfile.TemporaryDirectory() as temp_dir:
            server.SONGS_DIR = Path(temp_dir)
            try:
                with self.assertRaisesRegex(ConnectionError, "ended before"):
                    server.create_song_from_stream(
                        io.BytesIO(b"short"),
                        100,
                        song_name="Interrupted",
                        song_id="interrupted",
                        title="Interrupted",
                        artist="",
                        audio_filename="audio.wav",
                        bpm=180,
                        offset_ms=0,
                        difficulty_name="Normal",
                        difficulty_level=1,
                    )
                self.assertEqual(list(Path(temp_dir).iterdir()), [])
            finally:
                server.SONGS_DIR = previous_songs_dir

    def test_invalid_song_id_leaves_no_partial_song(self) -> None:
        previous_songs_dir = server.SONGS_DIR
        with tempfile.TemporaryDirectory() as temp_dir:
            server.SONGS_DIR = Path(temp_dir)
            try:
                with self.assertRaisesRegex(ValueError, "songId"):
                    server.create_song_from_stream(
                        io.BytesIO(b"audio"),
                        5,
                        song_name="Bad ID",
                        song_id="Bad ID",
                        title="Bad ID",
                        artist="",
                        audio_filename="audio.wav",
                        bpm=180,
                        offset_ms=0,
                        difficulty_name="Normal",
                        difficulty_level=1,
                    )
                self.assertEqual(list(Path(temp_dir).iterdir()), [])
            finally:
                server.SONGS_DIR = previous_songs_dir


if __name__ == "__main__":
    unittest.main()
