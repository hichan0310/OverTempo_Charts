"""Git commit/push for the charts repository and developer-channel deployment of charts.

Folder layout (the current one):
    <projects>/OverTempo_Charts            charts repository (this editor lives in Tools/chart-editor)
    <projects>/OverTempo_Launcher          launcher repository; its `internal` branch is what Netlify serves
Deploying copies `Tools/build_manifest.py` output for one charts commit into `dev/songs` and
`dev/manifest.json` on `internal` (same layout as OverTempo_Launcher/deploy charts-dev), pushes it,
then waits for Netlify to serve the new manifest.

Deploying publishes what the editor has saved: chart changes under Songs/ that are not committed yet
are committed (and pushed) first, then that commit is built. Earlier the button built only the last
commit, so saved-but-uncommitted charts silently never reached the dev channel.
The build itself runs from a clean temporary worktree of that commit; files outside Songs/ (tools,
editor state) are never committed or deployed by this button.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

DEPLOY_BRANCH = "internal"
DEV_ROOT = "dev"
DEFAULT_SITE = "https://overtempolauncher.netlify.app/"
DEPLOY_IDENTITY = ("-c", "user.name=OverTempo chart editor deploy",
                   "-c", "user.email=local-deploy@users.noreply.github.com")


class GitError(RuntimeError):
    pass


def git(cwd: Path, *args: str, check: bool = True, timeout: float = 600, strip: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, timeout=timeout,
                            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    if check and result.returncode != 0:
        raise GitError(f"git {' '.join(args)} 실패:\n{(result.stderr or result.stdout).strip()}")
    return result.stdout.strip() if strip else result.stdout


def launcher_path(charts: Path) -> Path:
    return Path(os.environ.get("OT_LAUNCHER_DIR") or charts.parent / "OverTempo_Launcher")


def site_url() -> str:
    url = os.environ.get("OT_LAUNCHER_SITE", DEFAULT_SITE)
    return url if url.endswith("/") else url + "/"


# ----------------------------------------------------------------------------- status / commit

def parse_porcelain(text: str) -> list[dict]:
    files = []
    entries = text.split("\0")
    i = 0
    while i < len(entries):
        entry = entries[i]
        i += 1
        if len(entry) < 4:
            continue
        code, path = entry[:2], entry[3:]
        if code[0] in "RC":  # rename/copy: the next entry is the original path
            i += 1
        files.append({"path": path, "code": code.strip() or code, "staged": code[0] not in " ?",
                      "untracked": code == "??"})
    return files


def repo_status(charts: Path) -> dict:
    branch = git(charts, "rev-parse", "--abbrev-ref", "HEAD")
    head = git(charts, "rev-parse", "HEAD")
    upstream = git(charts, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}", check=False)
    ahead = behind = None
    if upstream:
        counts = git(charts, "rev-list", "--left-right", "--count", f"{upstream}...HEAD", check=False).split()
        if len(counts) == 2:
            behind, ahead = int(counts[0]), int(counts[1])
    files = parse_porcelain(git(charts, "status", "--porcelain=v1", "-z", "--untracked-files=all", strip=False))
    launcher = launcher_path(charts)
    dev = None
    try:
        dev = fetch_json(site_url() + f"{DEV_ROOT}/manifest.json", timeout=6).get("sourceCommit")
    except Exception:
        pass
    return {"branch": branch, "head": head, "upstream": upstream or None, "ahead": ahead, "behind": behind, "devSourceCommit": dev,
            "files": files, "launcher": str(launcher), "launcherFound": (launcher / ".git").exists(),
            "site": site_url()}


def commit_and_push(charts: Path, paths: list[str], message: str, push: bool = True) -> dict:
    message = (message or "").strip()
    if not message:
        raise ValueError("커밋 메시지를 입력하세요.")
    if not paths:
        raise ValueError("커밋할 파일을 선택하세요.")
    changed = {f["path"] for f in repo_status(charts)["files"]}
    root = charts.resolve()
    for path in paths:
        resolved = (root / path).resolve()
        if root not in resolved.parents and resolved != root:
            raise ValueError(f"저장소 밖의 경로입니다: {path}")
        if path not in changed:
            raise ValueError(f"변경되지 않은 파일입니다: {path}")
    git(charts, "add", "-A", "--", *paths)
    # Commit exactly the selected paths, even if other files were staged before.
    git(charts, "commit", "-m", message, "--", *paths)
    sha = git(charts, "rev-parse", "HEAD")
    pushed = ""
    if push:
        branch = git(charts, "rev-parse", "--abbrev-ref", "HEAD")
        if branch == "HEAD":
            raise GitError("브랜치에 있지 않습니다(detached HEAD). 커밋은 됐지만 푸시하지 않았습니다.")
        pushed = git(charts, "push", "origin", f"HEAD:refs/heads/{branch}", timeout=900) or f"origin/{branch}"
    return {"ok": True, "commit": sha, "pushed": bool(push), "pushOutput": pushed}


# ----------------------------------------------------------------------------- deploy

def sign_manifests(launcher: Path, root: Path) -> list[str]:
    """Sign update manifests with the local release key (launcher repo ci/sign_manifests.py).

    The launcher refuses manifests without a valid signature, so a deployment must never skip this."""
    script = launcher / "ci" / "sign_manifests.py"
    if not script.is_file():
        raise GitError(f"매니페스트 서명 도구가 없습니다: {script}")
    spec = importlib.util.spec_from_file_location("overtempo_sign_manifests", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        return [path.relative_to(root).as_posix() for path in module.sign_tree(root)]
    except RuntimeError as error:
        raise GitError(f"매니페스트 서명 실패: {error}") from error


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def healthy_deployment(dev: Path, sha: str) -> bool:
    """True when dev/ already serves `sha` and every listed song file is present, the right size and not empty."""
    manifest = read_json(dev / "manifest.json")
    if manifest.get("sourceCommit") != sha or manifest.get("audience") != "full" or not manifest.get("songs"):
        return False
    for song in manifest["songs"]:
        path = dev / "songs" / str(song.get("file", ""))
        size = int(song.get("size", -1))
        if not path.is_file() or path.stat().st_size != size or (not song.get("encrypted") and size <= 22):
            return False
    return True


def fetch_json(url: str, timeout: float = 15) -> dict:
    request = urllib.request.Request(url + ("&" if "?" in url else "?") + f"t={time.time():.0f}",
                                     headers={"Cache-Control": "no-cache", "User-Agent": "OverTempo-chart-editor"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


SONGS_DIR = "Songs/"


def commit_saved_charts(charts: Path, log, push: bool = True) -> str | None:
    """Commits every saved change under Songs/ so the deploy contains exactly what the editor shows."""
    pending = [f["path"] for f in repo_status(charts)["files"] if f["path"].startswith(SONGS_DIR)]
    if not pending:
        return None
    songs = sorted({path[len(SONGS_DIR):].split("/", 1)[0] for path in pending})
    message = "Chart editor: " + ", ".join(songs[:6]) + (f" and {len(songs) - 6} more" if len(songs) > 6 else "")
    log(f"저장된 채보 변경 {len(pending)}개 파일 커밋 중 ({', '.join(songs)})")
    try:
        result = commit_and_push(charts, pending, message, push=push)
    except GitError as error:
        # The commit exists even when the push failed; the deploy can still use it.
        if "푸시" not in str(error) and "push" not in str(error):
            raise
        log(f"푸시 실패, 커밋은 로컬에 남았습니다: {error}")
        return git(charts, "rev-parse", "HEAD")
    log(f"커밋 {result['commit'][:12]}" + (" · 원격 저장소 푸시 완료" if result["pushed"] else ""))
    return result["commit"]


def deploy_dev_charts(charts: Path, log, ref: str = "HEAD", wait_seconds: float = 300,
                      launcher: Path | None = None, commit_saved: bool = True) -> dict:
    """Commit saved chart changes, then build the manifest for `ref` and push it to dev/ on the launcher's internal branch."""
    launcher = launcher or launcher_path(charts)
    if not (launcher / ".git").exists():
        raise GitError(f"런처 저장소를 찾을 수 없습니다: {launcher}")
    if commit_saved and ref == "HEAD":
        commit_saved_charts(charts, log)
    sha = git(charts, "rev-parse", f"{ref}^{{commit}}")
    log(f"채보 커밋 {sha[:12]} 배포 준비")
    with tempfile.TemporaryDirectory(prefix="overtempo-chart-deploy-") as temp:
        temp_path = Path(temp)
        source, internal, built = temp_path / "charts", temp_path / "internal", temp_path / "built"
        git(charts, "worktree", "add", "--detach", str(source), sha)
        try:
            log("깨끗한 작업 폴더에서 매니페스트·곡 압축 빌드 중 (커밋 안 된 변경은 포함되지 않음)")
            result = subprocess.run(["python3", str(source / "Tools" / "build_manifest.py"), "--repo", str(source),
                                     "--output-dir", str(built), "--base-url", "songs/", "--audience", "full"],
                                    text=True, capture_output=True, timeout=1800)
            if result.returncode != 0:
                raise GitError("매니페스트 빌드 실패:\n" + (result.stderr or result.stdout).strip()[-3000:])
            manifest = read_json(built / "manifest.json")
            songs = manifest.get("songs", [])
            # build_manifest skips files under dot-folders; an empty zip (22 bytes) means nothing was packed.
            empty = [song["id"] for song in songs if not song.get("encrypted") and int(song.get("size", 0)) <= 22]
            if empty:
                raise GitError("빈 곡 압축 파일이 만들어져 배포를 중단합니다: " + ", ".join(empty))
            log(f"빌드 완료: 곡 {len(songs)}개")
        finally:
            git(charts, "worktree", "remove", "--force", str(source), check=False)

        log(f"런처 {DEPLOY_BRANCH} 브랜치 가져오는 중")
        git(launcher, "fetch", "origin", f"refs/heads/{DEPLOY_BRANCH}", timeout=900)
        snapshot = git(launcher, "rev-parse", "FETCH_HEAD")
        git(launcher, "worktree", "add", "--detach", str(internal), snapshot)
        try:
            dev = internal / DEV_ROOT
            if healthy_deployment(dev, sha):
                log("같은 채보 커밋이 이미 정상적으로 배포되어 있습니다.")
            else:
                shutil.rmtree(dev / "songs", ignore_errors=True)
                dev.mkdir(parents=True, exist_ok=True)
                shutil.copytree(built / "songs", dev / "songs")
                shutil.copy2(built / "manifest.json", dev / "manifest.json")
            paths = [f"{DEV_ROOT}/manifest.json", f"{DEV_ROOT}/songs"]
            paths += sign_manifests(launcher, internal)
            git(internal, "add", "-A", "-f", "--", *paths)
            if not git(internal, "diff", "--cached", "--name-only"):
                log("배포할 변경이 없어 push를 건너뜁니다.")
                deployed = None
            else:
                git(internal, *DEPLOY_IDENTITY, "commit", "-m", f"Deploy developer charts {sha[:12]}")
                log("internal 브랜치에 push 중")
                git(internal, "push", "origin", f"HEAD:refs/heads/{DEPLOY_BRANCH}", timeout=1800)
                deployed = git(internal, "rev-parse", "HEAD")
                log(f"push 완료: {deployed[:12]}")
        finally:
            git(launcher, "worktree", "remove", "--force", str(internal), check=False)

    url = site_url() + f"{DEV_ROOT}/manifest.json"
    live = None
    if wait_seconds > 0:
        log(f"Netlify 반영 확인 중: {url}")
        deadline = time.time() + wait_seconds
        while time.time() < deadline:
            try:
                live = fetch_json(url).get("sourceCommit")
            except Exception as exc:  # network hiccups are retried until the deadline
                live = f"error: {exc}"
            if live == sha:
                log("Netlify에 새 채보가 반영됐습니다.")
                break
            time.sleep(10)
        else:
            log(f"제한 시간 안에 반영을 확인하지 못했습니다. 현재 Netlify: {live}")
    return {"ok": True, "sourceCommit": sha, "deployCommit": deployed, "netlifySourceCommit": live,
            "netlifyUpdated": live == sha}


class DeployJob:
    """One deployment at a time, run in the background; the editor polls `snapshot()`."""

    _lock = threading.Lock()
    current: "DeployJob | None" = None

    def __init__(self, charts: Path, ref: str):
        self.charts, self.ref = charts, ref
        self.log_lines: list[str] = []
        self.state, self.result, self.error = "running", None, None
        self.started = time.time()

    def log(self, line: str) -> None:
        self.log_lines.append(f"[{time.strftime('%H:%M:%S')}] {line}")

    def run(self) -> None:
        try:
            self.result = deploy_dev_charts(self.charts, self.log, self.ref)
            self.state = "done"
        except Exception as exc:
            self.error, self.state = str(exc), "failed"
            self.log(f"실패: {exc}")

    def snapshot(self) -> dict:
        return {"state": self.state, "log": self.log_lines, "result": self.result, "error": self.error,
                "elapsed": round(time.time() - self.started)}

    @classmethod
    def start(cls, charts: Path, ref: str = "HEAD") -> "DeployJob":
        with cls._lock:
            if cls.current and cls.current.state == "running":
                raise GitError("이미 배포가 진행 중입니다.")
            job = cls(charts, ref)
            cls.current = job
        threading.Thread(target=job.run, daemon=True).start()
        return job
