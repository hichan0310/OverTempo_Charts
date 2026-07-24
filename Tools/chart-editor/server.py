#!/usr/bin/env python3
from __future__ import annotations

import base64
import binascii
import io
import json
import math
import mimetypes
import os
import re
import shutil
import tempfile
import threading
import urllib.parse
import webbrowser
from email.parser import BytesParser
from email.policy import default
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

EDITOR_DIR = Path(__file__).resolve().parent
# Expected location: OverTempo_Charts/Tools/chart-editor/server.py
REPO_ROOT = EDITOR_DIR.parents[1]
SONGS_DIR = REPO_ROOT / "Songs"

AUDIO_EXTS = {".mp3", ".ogg", ".wav", ".flac", ".m4a"}
COVER_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
CHART_SUFFIX = ".4k-speedcoef.json"
ENCRYPTED_CHART_SUFFIX = ".otchart"
ARG_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
SONG_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
MAX_AUDIO_BYTES = 2 * 1024 * 1024 * 1024
UPLOAD_CHUNK_BYTES = 1024 * 1024


def json_bytes(data: object, status: int = 200) -> tuple[int, bytes, str]:
    return status, (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"), "application/json; charset=utf-8"


def error_bytes(message: str, status: int = 400) -> tuple[int, bytes, str]:
    return json_bytes({"ok": False, "error": message}, status)


def safe_component(name: str, *, field: str = "name") -> str:
    name = (name or "").strip()
    if not name or "/" in name or "\\" in name or name in {".", ".."}:
        raise ValueError(f"invalid {field}")
    return name


def clean_filename(name: str, fallback: str = "file") -> str:
    name = Path(name or fallback).name.strip()
    name = re.sub(r'[\\/:*?"<>|]+', "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    if not name or name in {".", ".."}:
        return fallback
    return name


def chart_filename(name: str) -> str:
    name = clean_filename(name, "NewChart.4k-speedcoef.json")
    if not name.endswith(".json"):
        name += CHART_SUFFIX
    return name


def encrypted_chart_filename(name: str) -> str:
    name = clean_filename(name, "NewChart.4k-speedcoef.json")
    if name.endswith(CHART_SUFFIX):
        name = name[: -len(CHART_SUFFIX)]
    elif name.endswith(".json"):
        name = name[:-5]
    elif name.endswith(ENCRYPTED_CHART_SUFFIX):
        name = name[: -len(ENCRYPTED_CHART_SUFFIX)]
    return (name or "NewChart") + ENCRYPTED_CHART_SUFFIX


def validate_song_id(song_id: str) -> str:
    song_id = (song_id or "").strip()
    if not SONG_ID_PATTERN.fullmatch(song_id):
        raise ValueError(
            "songId must start with a lowercase ASCII letter or digit and contain only "
            "lowercase ASCII letters, digits, dots, underscores, or hyphens"
        )
    return song_id


def validate_encrypted_envelope(data: object) -> dict:
    if not isinstance(data, dict):
        raise ValueError("encrypted chart envelope must be an object")

    required = {
        "schemaVersion",
        "argId",
        "cipher",
        "kdf",
        "iterations",
        "salt",
        "iv",
        "ciphertext",
        "tag",
    }
    missing = sorted(required - data.keys())
    if missing:
        raise ValueError(f"encrypted chart envelope missing: {', '.join(missing)}")
    if data["schemaVersion"] != 1:
        raise ValueError("unsupported encrypted chart schemaVersion")
    if data["cipher"] != "AES-256-CBC+HMAC-SHA256":
        raise ValueError("unsupported encrypted chart cipher")
    if data["kdf"] != "PBKDF2-HMAC-SHA256":
        raise ValueError("unsupported encrypted chart kdf")
    if not ARG_ID_PATTERN.fullmatch(str(data["argId"])):
        raise ValueError("invalid encrypted chart argId")

    iterations = data["iterations"]
    if not isinstance(iterations, int) or isinstance(iterations, bool) or not 100000 <= iterations <= 2000000:
        raise ValueError("encrypted chart iterations must be an integer from 100000 to 2000000")

    decoded: dict[str, bytes] = {}
    for field in ("salt", "iv", "ciphertext", "tag"):
        try:
            decoded[field] = base64.b64decode(str(data[field]), validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError(f"encrypted chart {field} is not valid Base64") from exc

    if len(decoded["salt"]) != 16:
        raise ValueError("encrypted chart salt must be 16 bytes")
    if len(decoded["iv"]) != 16:
        raise ValueError("encrypted chart iv must be 16 bytes")
    if len(decoded["tag"]) != 32:
        raise ValueError("encrypted chart tag must be 32 bytes")
    if not decoded["ciphertext"] or len(decoded["ciphertext"]) % 16:
        raise ValueError("encrypted chart ciphertext must be non-empty AES blocks")
    return data


def safe_song_dir(song: str) -> Path:
    song = safe_component(song, field="song name")
    path = (SONGS_DIR / song).resolve()
    if SONGS_DIR.resolve() not in path.parents and path != SONGS_DIR.resolve():
        raise ValueError("path traversal rejected")
    if not path.is_dir():
        raise FileNotFoundError(f"song not found: {song}")
    return path


def ensure_song_dir(song: str) -> Path:
    song = safe_component(song, field="song name")
    SONGS_DIR.mkdir(parents=True, exist_ok=True)
    path = (SONGS_DIR / song).resolve()
    if SONGS_DIR.resolve() not in path.parents:
        raise ValueError("path traversal rejected")
    path.mkdir(parents=True, exist_ok=False)
    return path


def new_song_target(song: str) -> tuple[str, Path]:
    song = safe_component(song, field="song name")
    SONGS_DIR.mkdir(parents=True, exist_ok=True)
    path = (SONGS_DIR / song).resolve()
    if SONGS_DIR.resolve() not in path.parents:
        raise ValueError("path traversal rejected")
    if path.exists():
        raise FileExistsError(f"song already exists: {song}")
    return song, path


def safe_song_file(song: str, filename: str) -> Path:
    filename = safe_component(filename, field="filename")
    song_dir = safe_song_dir(song)
    path = (song_dir / filename).resolve()
    if song_dir.resolve() not in path.parents and path != song_dir.resolve():
        raise ValueError("path traversal rejected")
    if not path.is_file():
        raise FileNotFoundError(f"file not found: {filename}")
    return path


def target_song_file(song_dir: Path, filename: str) -> Path:
    filename = safe_component(filename, field="filename")
    path = (song_dir / filename).resolve()
    if song_dir.resolve() not in path.parents:
        raise ValueError("path traversal rejected")
    return path


def make_blank_chart(*, title: str, artist: str, mapper: str, audio_file: str, difficulty_name: str, difficulty_level: float, bpm: float, offset_ms: float, snap_div: int) -> dict:
    return {
        "version": 2,
        "meta": {
            "title": title,
            "artist": artist,
            "source": "",
            "mapper": mapper,
            "previewStartMs": 0,
            "previewEndMs": 15000,
            "extra": "",
            "audioFileName": audio_file,
        },
        "difficulty": {
            "name": difficulty_name,
            "level": difficulty_level,
            "scroll": 1,
            "baseSpeed": 1,
            "notes": "",
            "lanes": 4,
        },
        "timing": {
            "bpm": bpm,
            "offsetMs": offset_ms,
            "snapDiv": snap_div,
            "bpmChanges": [],
        },
        "preview": {
            "startMs": 0,
            "endMs": 15000,
        },
        "speedLimitLines": [],
        "stageDeltaLines": [],
        "notes": [],
    }


def write_chart(path: Path, data: dict, *, backup: bool = True) -> None:
    if backup and path.exists():
        path.with_suffix(path.suffix + ".bak").write_bytes(path.read_bytes())
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_encrypted_chart(path: Path, data: dict) -> None:
    body = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    with tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)
        handle.write(body)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def create_song_from_stream(
    stream,
    content_length: int,
    *,
    song_name: str,
    song_id: str,
    title: str,
    artist: str,
    audio_filename: str,
    bpm: float,
    offset_ms: float,
    difficulty_name: str,
    difficulty_level: float,
    snap_div: int = 4,
) -> dict:
    song, final_dir = new_song_target(song_name)
    song_id = validate_song_id(song_id)
    audio_name = clean_filename(audio_filename, "audio.wav")
    if Path(audio_name).suffix.lower() not in AUDIO_EXTS:
        raise ValueError(f"unsupported audio extension: {audio_name}")
    if not 0 < content_length <= MAX_AUDIO_BYTES:
        raise ValueError("audio upload size is missing or too large")
    if not math.isfinite(bpm) or bpm <= 0:
        raise ValueError("BPM must be greater than zero")
    if not math.isfinite(offset_ms):
        raise ValueError("offsetMs must be finite")
    if not math.isfinite(difficulty_level):
        raise ValueError("difficultyLevel must be finite")
    if snap_div < 1 or snap_div > 192:
        raise ValueError("snapDiv is out of range")

    temp_dir = Path(tempfile.mkdtemp(prefix=".new-song-", dir=SONGS_DIR))
    try:
        audio_path = target_song_file(temp_dir, audio_name)
        remaining = content_length
        with audio_path.open("wb") as output:
            while remaining:
                chunk = stream.read(min(UPLOAD_CHUNK_BYTES, remaining))
                if not chunk:
                    raise ConnectionError("audio upload ended before Content-Length bytes were received")
                output.write(chunk)
                remaining -= len(chunk)
            output.flush()
            os.fsync(output.fileno())

        chart = chart_filename(f"{song}_{difficulty_name}.4k-speedcoef.json")
        chart_path = target_song_file(temp_dir, chart)
        blank = make_blank_chart(
            title=title or song,
            artist=artist,
            mapper="",
            audio_file=audio_name,
            difficulty_name=difficulty_name or "Normal",
            difficulty_level=difficulty_level,
            bpm=bpm,
            offset_ms=offset_ms,
            snap_div=snap_div,
        )
        write_chart(chart_path, blank, backup=False)
        patch_path = target_song_file(temp_dir, "song.patch.json")
        write_chart(
            patch_path,
            {
                "id": song_id,
                "title": title or song,
                "artist": artist,
                "enabled": True,
            },
            backup=False,
        )
        temp_dir.rename(final_dir)
        return {
            "ok": True,
            "song": song,
            "songId": song_id,
            "chart": chart,
            "audio": audio_name,
            "songDir": str(final_dir),
        }
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def list_songs() -> dict:
    songs = []
    if not SONGS_DIR.exists():
        return {"ok": True, "repoRoot": str(REPO_ROOT), "songsDir": str(SONGS_DIR), "songs": []}

    for song_dir in sorted([p for p in SONGS_DIR.iterdir() if p.is_dir()], key=lambda p: p.name.lower()):
        json_files = sorted([p.name for p in song_dir.glob("*.json") if p.name != "song.patch.json"])
        chart_files = [name for name in json_files if name.endswith(CHART_SUFFIX)]
        if not chart_files:
            chart_files = json_files

        audio = sorted([p.name for p in song_dir.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTS])
        covers = sorted([p.name for p in song_dir.iterdir() if p.is_file() and p.suffix.lower() in COVER_EXTS])
        osu = sorted([p.name for p in song_dir.glob("*.osu")])

        songs.append({
            "name": song_dir.name,
            "charts": chart_files,
            "audio": audio,
            "covers": covers,
            "osu": osu,
        })

    return {"ok": True, "repoRoot": str(REPO_ROOT), "songsDir": str(SONGS_DIR), "songs": songs}


def parse_multipart(content_type: str, body: bytes) -> tuple[dict[str, str], dict[str, tuple[str, bytes, str]]]:
    headers = f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8")
    msg = BytesParser(policy=default).parsebytes(headers + body)
    fields: dict[str, str] = {}
    files: dict[str, tuple[str, bytes, str]] = {}

    if not msg.is_multipart():
        raise ValueError("request is not multipart")

    for part in msg.iter_parts():
        disposition = part.get("Content-Disposition", "")
        if "form-data" not in disposition:
            continue
        name = part.get_param("name", header="content-disposition")
        if not name:
            continue
        filename = part.get_filename()
        payload = part.get_payload(decode=True) or b""
        if filename:
            files[name] = (clean_filename(filename), payload, part.get_content_type())
        else:
            fields[name] = payload.decode("utf-8", errors="replace")
    return fields, files


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(EDITOR_DIR), **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        print("[chart-editor]", fmt % args)

    def send_blob(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/api/songs":
            status, body, ctype = json_bytes(list_songs())
            self.send_blob(status, body, ctype)
            return

        if parsed.path == "/api/chart":
            try:
                q = urllib.parse.parse_qs(parsed.query)
                song = q.get("song", [""])[0]
                chart = q.get("chart", [""])[0]
                path = safe_song_file(song, chart)
                if path.suffix.lower() != ".json":
                    raise ValueError("chart must be a json file")
                body = path.read_bytes()
                self.send_blob(200, body, "application/json; charset=utf-8")
            except Exception as exc:
                status, body, ctype = error_bytes(str(exc), 404)
                self.send_blob(status, body, ctype)
            return

        if parsed.path == "/api/media":
            try:
                q = urllib.parse.parse_qs(parsed.query)
                song = q.get("song", [""])[0]
                filename = q.get("file", [""])[0]
                path = safe_song_file(song, filename)
                ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
                self.send_blob(200, path.read_bytes(), ctype)
            except Exception as exc:
                status, body, ctype = error_bytes(str(exc), 404)
                self.send_blob(status, body, ctype)
            return

        return super().do_GET()

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/api/song-upload":
            try:
                q = urllib.parse.parse_qs(parsed.query)

                def value(name: str, default_value: str = "") -> str:
                    return q.get(name, [default_value])[0]

                result = create_song_from_stream(
                    self.rfile,
                    int(self.headers.get("Content-Length", "0")),
                    song_name=value("songName"),
                    song_id=value("songId"),
                    title=value("title"),
                    artist=value("artist"),
                    audio_filename=value("audioFileName", "audio.wav"),
                    bpm=float(value("bpm", "180")),
                    offset_ms=float(value("offsetMs", "0")),
                    difficulty_name=value("difficultyName", "Normal"),
                    difficulty_level=float(value("difficultyLevel", "1")),
                    snap_div=int(value("snapDiv", "4")),
                )
                status, body, ctype = json_bytes(result)
                self.send_blob(status, body, ctype)
            except Exception as exc:
                status, body, ctype = error_bytes(str(exc), 400)
                self.send_blob(status, body, ctype)
            return

        if parsed.path == "/api/chart":
            try:
                q = urllib.parse.parse_qs(parsed.query)
                song = q.get("song", [""])[0]
                chart = chart_filename(q.get("chart", [""])[0])
                song_dir = safe_song_dir(song)
                path = target_song_file(song_dir, chart)

                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length)
                data = json.loads(raw.decode("utf-8"))
                write_chart(path, data, backup=True)

                status, body, ctype = json_bytes({"ok": True, "song": song, "chart": chart, "path": str(path)})
                self.send_blob(status, body, ctype)
            except Exception as exc:
                status, body, ctype = error_bytes(str(exc), 400)
                self.send_blob(status, body, ctype)
            return

        if parsed.path == "/api/encrypted-chart":
            try:
                q = urllib.parse.parse_qs(parsed.query)
                song = q.get("song", [""])[0]
                chart = encrypted_chart_filename(q.get("chart", [""])[0])
                song_dir = safe_song_dir(song)
                path = target_song_file(song_dir, chart)

                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length)
                data = validate_encrypted_envelope(json.loads(raw.decode("utf-8")))
                write_encrypted_chart(path, data)

                status, body, ctype = json_bytes(
                    {"ok": True, "song": song, "chart": chart, "path": str(path)}
                )
                self.send_blob(status, body, ctype)
            except Exception as exc:
                status, body, ctype = error_bytes(str(exc), 400)
                self.send_blob(status, body, ctype)
            return

        if parsed.path == "/api/new-chart":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                data = json.loads(self.rfile.read(length).decode("utf-8"))
                song = safe_component(data.get("song", ""), field="song")
                song_dir = safe_song_dir(song)
                chart = chart_filename(data.get("chart", ""))
                path = target_song_file(song_dir, chart)
                if path.exists():
                    raise FileExistsError(f"chart already exists: {chart}")

                blank = make_blank_chart(
                    title=str(data.get("title") or song),
                    artist=str(data.get("artist") or ""),
                    mapper=str(data.get("mapper") or ""),
                    audio_file=str(data.get("audioFileName") or ""),
                    difficulty_name=str(data.get("difficultyName") or "Normal"),
                    difficulty_level=float(data.get("difficultyLevel") or 1),
                    bpm=float(data.get("bpm") or 180),
                    offset_ms=float(data.get("offsetMs") or 0),
                    snap_div=int(data.get("snapDiv") or 4),
                )
                write_chart(path, blank, backup=False)
                status, body, ctype = json_bytes({"ok": True, "song": song, "chart": chart, "path": str(path)})
                self.send_blob(status, body, ctype)
            except Exception as exc:
                status, body, ctype = error_bytes(str(exc), 400)
                self.send_blob(status, body, ctype)
            return

        if parsed.path == "/api/song":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length)
                fields, files = parse_multipart(self.headers.get("Content-Type", ""), raw)

                if "audioFile" not in files:
                    raise ValueError("audioFile is required")
                audio_name, audio_body, _ = files["audioFile"]
                result = create_song_from_stream(
                    io.BytesIO(audio_body),
                    len(audio_body),
                    song_name=fields.get("songName", ""),
                    song_id=fields.get("songId", ""),
                    title=fields.get("title", ""),
                    artist=fields.get("artist", ""),
                    audio_filename=audio_name,
                    bpm=float(fields.get("bpm") or 180),
                    offset_ms=float(fields.get("offsetMs") or 0),
                    difficulty_name=fields.get("difficultyName") or "Normal",
                    difficulty_level=float(fields.get("difficultyLevel") or 1),
                    snap_div=int(fields.get("snapDiv") or 4),
                )
                status, body, ctype = json_bytes(result)
                self.send_blob(status, body, ctype)
            except Exception as exc:
                status, body, ctype = error_bytes(str(exc), 400)
                self.send_blob(status, body, ctype)
            return

        status, body, ctype = error_bytes("unknown endpoint", 404)
        self.send_blob(status, body, ctype)


def main() -> None:
    host = "127.0.0.1"
    port = 5173
    url = f"http://{host}:{port}/"

    print("OverTempo Chart Editor")
    print("Repo root :", REPO_ROOT)
    print("Songs dir :", SONGS_DIR)
    print("URL       :", url)
    print()
    print("종료: Ctrl+C")

    server = ThreadingHTTPServer((host, port), Handler)
    threading.Timer(0.7, lambda: webbrowser.open(url)).start()
    server.serve_forever()


if __name__ == "__main__":
    main()
