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


class WikilinkTitleTest(unittest.TestCase):
    TITLES = {"why-idempotency": "멱등성이 왜 필요한가", "ci-cd": "CI/CD 기본"}

    def _titled(self, body: str) -> str:
        return inject_dates.title_wikilinks(body, self.TITLES)

    # 별칭 구분자는 늘 "\|" 로 쓴다. Quartz 가 어디서든 받아 주고, 표 안에서도 칸을 가르지 않는다.
    def test_bare_link_gets_note_title_as_alias(self):
        self.assertEqual(self._titled("[[why-idempotency]]를 보라"), "[[why-idempotency\\|멱등성이 왜 필요한가]]를 보라")

    def test_table_row_without_leading_pipe_is_not_split(self):
        self.assertEqual(self._titled("a | [[why-idempotency]] | c"), "a | [[why-idempotency\\|멱등성이 왜 필요한가]] | c")

    def test_link_after_inner_shorter_fence_stays_in_code(self):
        body = "````\n```\n[[why-idempotency]]\n````"
        self.assertEqual(self._titled(body), body)

    def test_tilde_fence_is_not_closed_by_backticks(self):
        body = "~~~\n```\n[[why-idempotency]]\n~~~"
        self.assertEqual(self._titled(body), body)

    def test_one_line_code_span_does_not_open_fence(self):
        body = "```js x```\n[[why-idempotency]]"
        self.assertEqual(self._titled(body), "```js x```\n[[why-idempotency\\|멱등성이 왜 필요한가]]")

    def test_link_in_double_backtick_code_is_kept(self):
        self.assertEqual(self._titled("``x [[why-idempotency]] ``"), "``x [[why-idempotency]] ``")

    def test_frontmatter_is_kept(self):
        body = "---\nrelated: [[why-idempotency]]\n---\n[[why-idempotency]]"
        self.assertEqual(self._titled(body), "---\nrelated: [[why-idempotency]]\n---\n[[why-idempotency\\|멱등성이 왜 필요한가]]")

    def test_path_link_gets_title_of_its_last_segment(self):
        self.assertEqual(self._titled("[[02-x/why-idempotency]]"), "[[02-x/why-idempotency\\|멱등성이 왜 필요한가]]")

    def test_slug_alias_is_replaced_with_title(self):
        self.assertEqual(self._titled("[[02-x/why-idempotency|why-idempotency]]"), "[[02-x/why-idempotency\\|멱등성이 왜 필요한가]]")

    def test_old_slug_alias_is_replaced_with_title(self):
        self.assertEqual(self._titled("[[why-idempotency|old-name]]"), "[[why-idempotency\\|멱등성이 왜 필요한가]]")

    def test_escaped_slug_alias_in_table_is_replaced(self):
        self.assertEqual(self._titled("| [[why-idempotency\\|why-idempotency]] |"), "| [[why-idempotency\\|멱등성이 왜 필요한가]] |")

    def test_readable_alias_is_kept_even_in_english(self):
        self.assertEqual(self._titled("[[why-idempotency|Idempotency]]"), "[[why-idempotency|Idempotency]]")

    def test_link_with_alias_is_kept(self):
        self.assertEqual(self._titled("[[why-idempotency|여기]]"), "[[why-idempotency|여기]]")

    def test_unknown_link_is_kept(self):
        self.assertEqual(self._titled("[[no-such-note]]"), "[[no-such-note]]")

    def test_embed_is_kept(self):
        self.assertEqual(self._titled("![[why-idempotency]]"), "![[why-idempotency]]")

    def test_slash_in_title_becomes_middle_dot(self):
        self.assertEqual(self._titled("[[ci-cd]]"), "[[ci-cd\\|CI·CD 기본]]")

    def test_link_in_table_row_escapes_pipe(self):
        self.assertEqual(self._titled("| [[why-idempotency]] | 설명 |"), "| [[why-idempotency\\|멱등성이 왜 필요한가]] | 설명 |")

    def test_link_in_fenced_code_is_kept(self):
        body = "```\n[[why-idempotency]]\n```\n[[why-idempotency]]"
        self.assertEqual(self._titled(body), "```\n[[why-idempotency]]\n```\n[[why-idempotency\\|멱등성이 왜 필요한가]]")

    def test_link_in_inline_code_is_kept(self):
        self.assertEqual(self._titled("`[[why-idempotency]]`"), "`[[why-idempotency]]`")


class TitleIndexTest(unittest.TestCase):
    def test_reads_title_by_file_stem_and_strips_quotes(self):
        with tempfile.TemporaryDirectory() as tmp:
            note = Path(tmp) / "02-practical-backend" / "idempotency" / "why-idempotency.md"
            note.parent.mkdir(parents=True)
            note.write_text('---\ntitle: "멱등성이 왜 필요한가"\n---\n본문\n', encoding="utf-8")

            self.assertEqual(inject_dates.title_index(Path(tmp)), {"why-idempotency": "멱등성이 왜 필요한가"})

    def _index_of(self, text: str) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "note.md").write_text(text, encoding="utf-8")
            return inject_dates.title_index(Path(tmp))

    def test_title_line_in_body_is_not_the_title(self):
        self.assertEqual(self._index_of("---\ntags: [a]\n---\ntitle: 본문 줄\n"), {})

    def test_empty_title_does_not_take_next_line(self):
        self.assertEqual(self._index_of("---\ntitle:\ntags: [a]\n---\n"), {})

    def test_title_with_comment_or_inner_quote_is_left_out(self):
        self.assertEqual(self._index_of("---\ntitle: 'It''s' # c\n---\n"), {})

    def test_duplicate_stem_is_left_out(self):
        with tempfile.TemporaryDirectory() as tmp:
            for folder in ["a", "b"]:
                (Path(tmp) / folder).mkdir()
                (Path(tmp) / folder / "same.md").write_text(f"---\ntitle: {folder}\n---\n", encoding="utf-8")

            self.assertEqual(inject_dates.title_index(Path(tmp)), {})


if __name__ == "__main__":
    unittest.main()
