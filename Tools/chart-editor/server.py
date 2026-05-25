#!/usr/bin/env python3
from __future__ import annotations

import json
import mimetypes
import re
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
        },
        "preview": {
            "startMs": 0,
            "endMs": 15000,
        },
        "notes": [],
    }


def write_chart(path: Path, data: dict, *, backup: bool = True) -> None:
    if backup and path.exists():
        path.with_suffix(path.suffix + ".bak").write_bytes(path.read_bytes())
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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

                song = safe_component(fields.get("songName", ""), field="song name")
                song_dir = ensure_song_dir(song)

                if "audioFile" not in files:
                    raise ValueError("audioFile is required")
                audio_name, audio_body, _ = files["audioFile"]
                if Path(audio_name).suffix.lower() not in AUDIO_EXTS:
                    raise ValueError(f"unsupported audio extension: {audio_name}")
                audio_path = target_song_file(song_dir, audio_name)
                audio_path.write_bytes(audio_body)

                title = fields.get("title") or song
                artist = fields.get("artist") or ""
                difficulty_name = fields.get("difficultyName") or "Normal"
                difficulty_level = float(fields.get("difficultyLevel") or 1)
                bpm = float(fields.get("bpm") or 180)
                offset_ms = float(fields.get("offsetMs") or 0)
                snap_div = int(fields.get("snapDiv") or 4)

                chart = chart_filename(f"{song}_{difficulty_name}.4k-speedcoef.json")
                chart_path = target_song_file(song_dir, chart)
                blank = make_blank_chart(
                    title=title,
                    artist=artist,
                    mapper="",
                    audio_file=audio_name,
                    difficulty_name=difficulty_name,
                    difficulty_level=difficulty_level,
                    bpm=bpm,
                    offset_ms=offset_ms,
                    snap_div=snap_div,
                )
                write_chart(chart_path, blank, backup=False)

                status, body, ctype = json_bytes({
                    "ok": True,
                    "song": song,
                    "chart": chart,
                    "audio": audio_name,
                    "songDir": str(song_dir),
                })
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
