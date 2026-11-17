"""git_deploy: commit/push only the chosen files; deploy charts to a launcher's internal branch.
Uses throwaway local repos for every remote — nothing is pushed anywhere real."""
import json, subprocess, tempfile, unittest
from pathlib import Path
import git_deploy

CHARTS = Path(__file__).resolve().parents[2]


def sh(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, text=True, capture_output=True).stdout.strip()


def make_clone(root: Path, name: str) -> tuple[Path, Path]:
    origin, work = root / f"{name}.git", root / name
    sh(root, "init", "-q", "--bare", "-b", "main", str(origin))
    sh(root, "clone", "-q", str(origin), str(work))
    for k, v in (("user.name", "t"), ("user.email", "t@t")):
        sh(work, "config", k, v)
    return origin, work


class CommitPush(unittest.TestCase):
    def test_commits_only_selected_files_and_pushes(self):
        with tempfile.TemporaryDirectory() as t:
            origin, work = make_clone(Path(t), "charts")
            (work / "Songs" / "A").mkdir(parents=True); (work / "Songs" / "B").mkdir(parents=True)
            (work / "Songs/A/a.json").write_text("1"); (work / "Songs/B/b.json").write_text("1")
            sh(work, "add", "."); sh(work, "commit", "-qm", "init"); sh(work, "push", "-q", "origin", "main")
            (work / "Songs/A/a.json").write_text("2"); (work / "Songs/B/b.json").write_text("2")
            status = git_deploy.repo_status(work)
            self.assertEqual({f["path"] for f in status["files"]}, {"Songs/A/a.json", "Songs/B/b.json"})
            with self.assertRaises(ValueError):
                git_deploy.commit_and_push(work, ["../outside.json"], "x")
            with self.assertRaises(ValueError):
                git_deploy.commit_and_push(work, ["Songs/A/unchanged.json"], "x")
            result = git_deploy.commit_and_push(work, ["Songs/A/a.json"], "A: update")
            self.assertEqual(sh(origin, "rev-parse", "main"), result["commit"])
            self.assertEqual(sh(origin, "show", "main:Songs/A/a.json"), "2")
            self.assertEqual(sh(origin, "show", "main:Songs/B/b.json"), "1")  # not selected -> not committed
            self.assertEqual([f["path"] for f in git_deploy.repo_status(work)["files"]], ["Songs/B/b.json"])


class DeployDevCharts(unittest.TestCase):
    def test_builds_from_a_clean_commit_and_pushes_dev_folder(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            origin, launcher = make_clone(root, "launcher")
            (launcher / "dev").mkdir(); (launcher / "dev/manifest.json").write_text('{"sourceCommit":"old"}')
            (launcher / "index.html").write_text("public")
            sh(launcher, "add", "."); sh(launcher, "commit", "-qm", "init"); sh(launcher, "push", "-q", "origin", "main:internal")
            logs = []
            result = git_deploy.deploy_dev_charts(CHARTS, logs.append, ref="HEAD", wait_seconds=0, launcher=launcher)
            head = sh(CHARTS, "rev-parse", "HEAD")
            self.assertEqual(result["sourceCommit"], head)
            manifest = json.loads(sh(origin, "show", "internal:dev/manifest.json"))
            self.assertEqual(manifest["sourceCommit"], head)
            songs = sh(origin, "ls-tree", "-r", "-l", "internal", "dev/songs").splitlines()
            self.assertTrue(songs)
            sizes = {line.split("\t")[1].rsplit("/", 1)[-1]: int(line.split()[3]) for line in songs}
            for song in manifest["songs"]:
                self.assertEqual(sizes[song["file"]], song["size"])
                if not song.get("encrypted"):
                    self.assertGreater(song["size"], 22, song["id"])
            self.assertEqual(sh(origin, "show", "internal:index.html"), "public")  # outside dev/ untouched
            self.assertNotIn("overtempo-chart-deploy", sh(CHARTS, "worktree", "list"))  # temp worktrees removed
            # a second deploy of the same commit changes nothing and pushes nothing
            before = sh(origin, "rev-parse", "internal")
            again = git_deploy.deploy_dev_charts(CHARTS, logs.append, ref="HEAD", wait_seconds=0, launcher=launcher)
            self.assertIsNone(again["deployCommit"]); self.assertEqual(sh(origin, "rev-parse", "internal"), before)


if __name__ == "__main__":
    unittest.main()
