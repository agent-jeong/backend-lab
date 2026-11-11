"""Run: python3 -m unittest discover -s site/scripts -p 'test_*.py'"""
import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

_spec = importlib.util.spec_from_file_location("inject_dates", Path(__file__).with_name("inject-dates.py"))
inject_dates = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(inject_dates)


def _commit(root: Path, rel: str, text: str, date: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    env = {**os.environ, "GIT_AUTHOR_DATE": f"{date}T12:00:00", "GIT_COMMITTER_DATE": f"{date}T12:00:00"}
    subprocess.run(["git", "-C", str(root), "add", rel], check=True, env=env)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", rel], check=True, env=env)


class FolderIndexDatesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.root, self.content = base / "repo", base / "content"
        self.root.mkdir()
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.email", "t@example.com"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.name", "t"], check=True)
        _commit(self.root, "02-practical-backend/transaction/transaction.md", "---\ntitle: 트랜잭션\n---\n", "2026-01-05")
        _commit(self.root, "02-practical-backend/transaction/why.md", "---\ntitle: 왜\n---\n", "2026-03-10")
        for rel in ["02-practical-backend/transaction/transaction.md", "02-practical-backend/transaction/why.md"]:
            (self.content / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.content / rel).write_text((self.root / rel).read_text(encoding="utf-8"), encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def _index(self, rel: str) -> str:
        return (self.content / rel / "index.md").read_text(encoding="utf-8")

    def test_topic_folder_index_takes_latest_change_in_folder_as_modified(self):
        inject_dates.write_folder_indexes(self.content, self.root)

        self.assertIn("modified: 2026-03-10\n", self._index("02-practical-backend/transaction"))

    def test_topic_folder_index_takes_first_commit_in_folder_as_created(self):
        inject_dates.write_folder_indexes(self.content, self.root)

        self.assertIn("created: 2026-01-05\n", self._index("02-practical-backend/transaction"))

    def test_top_folder_index_gets_dates_too(self):
        inject_dates.write_folder_indexes(self.content, self.root)

        self.assertIn("modified: 2026-03-10\n", self._index("02-practical-backend"))

    def test_folder_without_git_history_gets_no_date_line(self):
        (self.content / "05-ai-workflows").mkdir()
        (self.content / "05-ai-workflows" / "new.md").write_text("---\ntitle: 새 글\n---\n", encoding="utf-8")

        inject_dates.write_folder_indexes(self.content, self.root)

        self.assertNotIn("modified:", self._index("05-ai-workflows"))


if __name__ == "__main__":
    unittest.main()
