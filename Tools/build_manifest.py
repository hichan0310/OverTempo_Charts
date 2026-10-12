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
OPAQUE_ID_RE = re.compile(r"^[0-9a-f]{32}$")
RELEASE_MEDIA_SUFFIXES = {".wav", ".mp3", ".ogg", ".flac", ".png", ".jpg", ".jpeg", ".webp"}

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
    if path.suffix.lower() in {".bak", ".tmp"} or path.name.endswith("~"):
        return False
    if any(part.startswith(".") for part in path.parts):
        return False
    return path.is_file()

def validate_song(song_dir: Path, meta: dict) -> None:
    charts = list(song_dir.glob("*.osu")) + list(song_dir.glob("*.4k-speedcoef.json"))
    encrypted_charts = list(song_dir.glob("*.otchart"))
    encrypted = meta.get("encrypted") is True

    if encrypted:
        if not encrypted_charts:
            die(f"encrypted song has no .otchart file: {song_dir}")

        assets = meta.get("encryptedAssets")
        if not isinstance(assets, dict) or not assets:
            die(f"encrypted song must declare its packaged media: {song_dir}")
        destinations = set()
        for source, destination in assets.items():
            if (not isinstance(source, str) or not isinstance(destination, str) or
                    Path(source).name != source or Path(destination).name != destination or
                    source.startswith(".") or destination.startswith(".") or
                    Path(source).suffix.lower() not in RELEASE_MEDIA_SUFFIXES or
                    Path(destination).suffix.lower() not in RELEASE_MEDIA_SUFFIXES or
                    destination in destinations or not (song_dir / source).is_file()):
                die(f"invalid encrypted media mapping: {song_dir}: {source!r} -> {destination!r}")
            destinations.add(destination)
        actual_media = {path.name for path in song_dir.iterdir()
                        if path.is_file() and path.suffix.lower() in RELEASE_MEDIA_SUFFIXES}
        if actual_media != set(assets):
            die(f"encrypted song media mapping is incomplete: {song_dir}")

        for encrypted_chart in encrypted_charts:
            if not OPAQUE_ID_RE.fullmatch(encrypted_chart.stem):
                die(f"encrypted chart filename must be opaque: {encrypted_chart}")
            envelope = load_json(encrypted_chart)
            required = {
                "schemaVersion", "argId", "cipher", "kdf", "iterations",
                "salt", "iv", "ciphertext", "tag"
            }
            missing = sorted(required - set(envelope))
            if missing:
                die(f"invalid encrypted chart envelope {encrypted_chart}: missing {', '.join(missing)}")
            if envelope.get("schemaVersion") != 1:
                die(f"unsupported encrypted chart schema: {encrypted_chart}")
            if envelope.get("cipher") != "AES-256-CBC+HMAC-SHA256":
                die(f"unsupported encrypted chart cipher: {encrypted_chart}")
            if envelope.get("kdf") != "PBKDF2-HMAC-SHA256":
                die(f"unsupported encrypted chart KDF: {encrypted_chart}")
            if envelope.get("argId") != encrypted_chart.stem:
                die(f"encrypted chart ARG ID does not match its filename: {encrypted_chart}")
    elif not charts:
        die(f"no chart file found in {song_dir}")

    if not encrypted and encrypted_charts:
        die(f"song has .otchart files but song.patch.json is not marked encrypted: {song_dir}")

    for osu in ([] if encrypted else song_dir.glob("*.osu")):
        audio = parse_osu_audio(osu)
        if audio and not (song_dir / audio).is_file():
            die(f"osu AudioFilename target missing: {osu} -> {audio}")

    for sc in ([] if encrypted else song_dir.glob("*.4k-speedcoef.json")):
        data = load_json(sc)
        notes = data.get("notes")
        if not isinstance(notes, list) or (not notes and meta.get("allowEmptyChart") is not True):
            die(f"speedcoef chart has no notes: {sc}")
        audio = ((data.get("meta") or {}).get("audioFileName") or "").strip()
        if audio and not (song_dir / audio).is_file():
            die(f"speedcoef audioFileName target missing: {sc} -> {audio}")

def build_song_zip(repo: Path, song_dir: Path, song_id: str, output_songs: Path, zip_name: str,
                   meta: dict | None = None) -> Path:
    zip_path = output_songs / zip_name
    if zip_path.exists():
        zip_path.unlink()

    meta_path = song_dir / "song.patch.json"
    meta = meta if meta is not None else (load_json(meta_path) if meta_path.is_file() else {})
    encrypted = meta.get("encrypted") is True
    files = sorted(p for p in song_dir.rglob("*") if should_zip(p))
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        if encrypted:
            # Keep editor plaintext and backups in the source tree, but package only
            # authenticated envelopes and explicitly named release media.
            release_meta = {"id": song_id, "enabled": True, "encrypted": True,
                            "publicTitle": str(meta.get("publicTitle", "Encrypted Content")),
                            "publicArtist": str(meta.get("publicArtist", ""))}
            zf.writestr(f"{song_id}/song.patch.json",
                        json.dumps(release_meta, ensure_ascii=False, indent=2) + "\n")
            for chart in sorted(song_dir.glob("*.otchart")):
                zf.write(chart, f"{song_id}/{chart.name}")
            for source, destination in sorted(meta["encryptedAssets"].items()):
                zf.write(song_dir / source, f"{song_id}/{destination}")
            return zip_path
        for path in files:
            rel = path.relative_to(song_dir).as_posix()
            archive_name = f"{song_id}/{rel}"
            if path.name.endswith(".4k-speedcoef.json"):
                chart = load_json(path)
                meta = chart.get("meta")
                if isinstance(meta, dict) and "coverDataUrl" in meta:
                    meta.pop("coverDataUrl")
                    zf.writestr(archive_name, json.dumps(chart, ensure_ascii=False, indent=2) + "\n")
                    continue
            zf.write(path, archive_name)
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
    removed = set()

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
        if meta.get("encrypted") is True and not OPAQUE_ID_RE.fullmatch(song_id):
            die(f"encrypted song id must be opaque: {meta_path}")
        retired = meta.get("retireSongIds", [])
        if not isinstance(retired, list) or any(not isinstance(item, str) or not SONG_ID_RE.fullmatch(item)
                                                for item in retired):
            die(f"invalid retired song IDs: {meta_path}")
        removed.update(retired)

        validate_song(song_dir, meta)

        rel_dir = song_dir.relative_to(repo).as_posix()
        content_hash = git(["rev-parse", f"HEAD:{rel_dir}"], repo)
        short_hash = content_hash[:12]
        zip_name = f"{song_id}_{short_hash}.zip"
        zip_path = build_song_zip(repo, song_dir, song_id, output_songs, zip_name, meta)

        encrypted = meta.get("encrypted") is True
        entries.append({
            "id": song_id,
            "title": str(meta.get("publicTitle", "Encrypted Content") if encrypted else meta.get("title", song_id)),
            "artist": str(meta.get("publicArtist", "") if encrypted else meta.get("artist", "")),
            "encrypted": encrypted,
            "contentHash": content_hash,
            "file": zip_name,
            "sha256": sha256_file(zip_path),
            "size": zip_path.stat().st_size
        })

    if removed.intersection(entry["id"] for entry in entries):
        die("a song cannot be both active and retired")
    manifest = {
        "schemaVersion": 1,
        "sourceCommit": source_commit,
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "baseUrl": args.base_url,
        "songs": entries,
        "removed": sorted(removed)
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
