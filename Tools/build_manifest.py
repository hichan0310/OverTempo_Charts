#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

SONG_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")

def die(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)

def git(args, cwd: Path) -> str:
    return subprocess.check_output(["git"] + args, cwd=str(cwd), text=True).strip()

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_json(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        die(f"failed to read json: {path}: {exc}")

def parse_osu_audio(path: Path) -> str:
    in_general = False
    try:
        for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            line = raw.strip()
            if line.startswith("[") and line.endswith("]"):
                in_general = line == "[General]"
                continue
            if in_general and line.startswith("AudioFilename:"):
                return line.split(":", 1)[1].strip()
    except Exception as exc:
        die(f"failed to read osu: {path}: {exc}")
    return ""

def should_zip(path: Path) -> bool:
    if path.name in {".DS_Store", "Thumbs.db"}:
        return False
    if path.suffix.lower() == ".zip":
        return False
    if any(part.startswith(".") for part in path.parts):
        return False
    return path.is_file()

def validate_song(song_dir: Path, meta: dict) -> None:
    charts = list(song_dir.glob("*.osu")) + list(song_dir.glob("*.4k-speedcoef.json"))
    if not charts:
        die(f"no chart file found in {song_dir}")

    for osu in song_dir.glob("*.osu"):
        audio = parse_osu_audio(osu)
        if audio and not (song_dir / audio).is_file():
            die(f"osu AudioFilename target missing: {osu} -> {audio}")

    for sc in song_dir.glob("*.4k-speedcoef.json"):
        data = load_json(sc)
        notes = data.get("notes")
        if not isinstance(notes, list) or len(notes) == 0:
            die(f"speedcoef chart has no notes: {sc}")
        audio = ((data.get("meta") or {}).get("audioFileName") or "").strip()
        if audio and not (song_dir / audio).is_file():
            die(f"speedcoef audioFileName target missing: {sc} -> {audio}")

def build_song_zip(repo: Path, song_dir: Path, song_id: str, output_songs: Path, zip_name: str) -> Path:
    zip_path = output_songs / zip_name
    if zip_path.exists():
        zip_path.unlink()

    files = sorted(p for p in song_dir.rglob("*") if should_zip(p))
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in files:
            rel = path.relative_to(song_dir).as_posix()
            zf.write(path, f"{song_id}/{rel}")
    return zip_path

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".", help="charts repository root")
    parser.add_argument("--songs-dir", default="Songs", help="songs directory under repo")
    parser.add_argument("--output-dir", default="output", help="output directory under repo")
    parser.add_argument("--base-url", default="songs/", help="base URL or relative path for song zips")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    songs_root = repo / args.songs_dir
    output_root = repo / args.output_dir
    output_songs = output_root / "songs"

    if not songs_root.is_dir():
        die(f"songs directory not found: {songs_root}")

    output_songs.mkdir(parents=True, exist_ok=True)

    source_commit = git(["rev-parse", "HEAD"], repo)
    entries = []

    for song_dir in sorted(p for p in songs_root.iterdir() if p.is_dir()):
        meta_path = song_dir / "song.patch.json"
        if not meta_path.is_file():
            die(f"missing song.patch.json: {song_dir}")

        meta = load_json(meta_path)
        if meta.get("enabled") is False:
            continue

        song_id = str(meta.get("id", "")).strip()
        if not song_id:
            die(f"missing id in {meta_path}")
        if not SONG_ID_RE.match(song_id):
            die(f"invalid song id in {meta_path}: {song_id}")

        validate_song(song_dir, meta)

        rel_dir = song_dir.relative_to(repo).as_posix()
        content_hash = git(["rev-parse", f"HEAD:{rel_dir}"], repo)
        short_hash = content_hash[:12]
        zip_name = f"{song_id}_{short_hash}.zip"
        zip_path = build_song_zip(repo, song_dir, song_id, output_songs, zip_name)

        entries.append({
            "id": song_id,
            "title": str(meta.get("title", song_id)),
            "artist": str(meta.get("artist", "")),
            "contentHash": content_hash,
            "file": zip_name,
            "sha256": sha256_file(zip_path),
            "size": zip_path.stat().st_size
        })

    manifest = {
        "schemaVersion": 1,
        "sourceCommit": source_commit,
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "baseUrl": args.base_url,
        "songs": entries,
        "removed": []
    }

    manifest_path = output_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {manifest_path}")
    print(f"wrote {len(entries)} song zip(s) under {output_songs}")
    for entry in entries:
        print(f"{entry['id']} {entry['file']} {entry['size']} bytes")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
