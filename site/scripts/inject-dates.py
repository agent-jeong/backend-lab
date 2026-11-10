#!/usr/bin/env python3
"""Prepare copied notes for the blog build.

The site is built from a copy of the notes, so the build cannot read git
history itself. This script, run on the copy only:

- fills `created` and `modified` from the source repo's git history,
  leaving any value an author already wrote untouched;
- drops the body's first `# 제목` when it repeats the frontmatter title,
  because the page template already prints the title;
- writes an `index.md` for each folder so breadcrumbs and folder pages
  show a readable name instead of the folder slug.
"""
import re
import subprocess
import sys
from pathlib import Path


def git_date(root: Path, rel: str, first: bool) -> str:
    args = ["git", "-C", str(root), "log", "--format=%cs"]
    if first:
        args += ["--follow", "--diff-filter=A"]
    else:
        args += ["-1"]
    out = subprocess.run(args + ["--", rel], capture_output=True, text=True, check=True).stdout.split()
    if not out:
        return ""
    return out[-1] if first else out[0]


def inject(path: Path, created: str, modified: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return False
    end = text.find("\n---\n", 4)
    if end == -1:
        return False
    head, body = text[4:end], text[end:]
    keys = {line.split(":", 1)[0].strip() for line in head.splitlines() if ":" in line}
    extra = []
    if created and "created" not in keys:
        extra.append(f"created: {created}")
    if modified and "modified" not in keys:
        extra.append(f"modified: {modified}")
    if not extra:
        return False
    path.write_text("---\n" + head + "\n" + "\n".join(extra) + body, encoding="utf-8")
    return True


def drop_duplicate_h1(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return False
    title = re.search(r"^title:\s*(.+)$", m.group(1), re.M)
    if not title:
        return False
    body = text[m.end():]
    h1 = re.match(r"\s*# (.+)\n", body)
    if not h1 or h1.group(1).strip() != title.group(1).strip().strip('"'):
        return False
    path.write_text(text[: m.end()] + body[h1.end():], encoding="utf-8")
    return True


HUB_NOTES = {"batch": "batch-processing.md"}

TOP_FOLDERS = {
    "00-home": ("소개", "이 블로그와 용어집"),
    "01-core": ("기본기", "Java, Spring, JPA, DB, Redis, 네트워크, OS"),
    "02-practical-backend": ("실무 백엔드", "트랜잭션, 동시성, 멱등성, 성능, 운영"),
    "03-work-cases": ("내 실무 사례", "직접 겪은 문제를 일반화한 사례"),
    "04-interview-cases": ("면접 준비", "기술 질문과 면접 설계 문제"),
    "05-ai-workflows": ("AI 활용", "AI를 개발에 쓰는 방법과 사례"),
}


def write_folder_indexes(content: Path) -> int:
    count = 0
    for folder in sorted(p for p in content.rglob("*") if p.is_dir()):
        index = folder / "index.md"
        if index.exists() or folder == content:
            continue
        rel = folder.relative_to(content).as_posix()
        if rel in TOP_FOLDERS:
            title, desc = TOP_FOLDERS[rel]
            body = desc
        else:
            hub = folder / HUB_NOTES.get(folder.name, f"{folder.name}.md")
            if not hub.exists():
                hub = next(iter(sorted(folder.glob("*.md"))), None)
            if hub is None:
                continue
            found = re.search(r"^title:\s*(.+)$", hub.read_text(encoding="utf-8"), re.M)
            title = found.group(1).strip() if found else folder.name
            desc = f"{title} 주제의 글 목록"
            body = f"먼저 [[{hub.stem}|{title} 안내 글]]을 보면 읽는 순서와 핵심 질문이 있다."
        index.write_text(
            f"---\ntitle: {title}\ndescription: {desc}\ncomments: false\n---\n\n{body}\n",
            encoding="utf-8",
        )
        count += 1
    return count


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: inject-dates.py <repo-root> <content-dir>", file=sys.stderr)
        return 2
    root, content = Path(sys.argv[1]), Path(sys.argv[2])
    changed = 0
    for md in sorted(content.rglob("*.md")):
        rel = md.relative_to(content).as_posix()
        source = "00-home/index.md" if rel == "index.md" else rel
        if not (root / source).exists():
            continue
        created = git_date(root, source, first=True)
        modified = git_date(root, source, first=False)
        changed += inject(md, created, modified)
    dropped = sum(drop_duplicate_h1(md) for md in content.rglob("*.md"))
    folders = write_folder_indexes(content)
    print(f"prepare-notes: dates {changed}, duplicate titles {dropped}, folder indexes {folders}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
