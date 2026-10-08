#!/usr/bin/env python3
"""Backup behaviour of Diagram.write(): runs in throwaway directories, prints one
line per scenario, exits 1 on the first failure."""
import io
import pathlib
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
import drawio_kit as kit  # noqa: E402
from drawio_kit import Diagram, Page, Z  # noqa: E402


def write(label: str, f: pathlib.Path) -> str:
    """Diagram.write with its messages captured; returns them."""
    out = io.StringIO()
    with redirect_stdout(out):
        diagram(label).write(f)
    return out.getvalue()


def diagram(label: str) -> Diagram:
    p = Page("1. Test")
    p.title(f"Version {label}")
    p.box(100, 100, 200, 80, f"Box\n{label}", Z.APP)
    return Diagram([p])


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout


def backups(docs):
    d = docs / kit.BACKUP_DIR
    return sorted(d.glob("*.drawio")) if d.exists() else []


def check(name, cond, detail=""):
    print(f"  {'ok  ' if cond else 'FAIL'}  {name}" + (f": {detail}" if detail and not cond else ""))
    if not cond:
        sys.exit(1)


with tempfile.TemporaryDirectory() as tmp:
    repo = pathlib.Path(tmp)
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@example.invalid"); git(repo, "config", "user.name", "t")
    docs = repo / "docs"; docs.mkdir()
    f = docs / "architecture.drawio"

    write("1", f)
    gi = (repo / ".gitignore").read_text()
    check("first write: no backup, .gitignore gets both patterns",
          not backups(docs) and ".drawio-backups/" in gi and ".$*.bkp" in gi, gi)

    git(repo, "add", "-A"); git(repo, "commit", "-qm", "v1")
    write("1", f)
    check("same content again: no backup", not backups(docs))

    msg = write("2", f)
    bs = backups(docs)
    check("changed content: previous version backed up", len(bs) == 1 and "Version 1" in bs[0].read_text())
    status = git(repo, "status", "--porcelain")
    check("backup is invisible to git", ".drawio-backups" not in status and "architecture.drawio" in status, status)

    check("generator change is not reported as a hand edit", "changed after the last build" not in msg, msg)
    msg = write("2b", f)
    check("second build before commit is not a hand edit either", "changed after the last build" not in msg, msg)

    git(repo, "add", "-A"); git(repo, "commit", "-qm", "v2")
    f.write_text(f.read_text().replace("Version 2b", "Version 2b, edited by hand in draw.io"))
    msg = write("3", f)
    hand = [b for b in backups(docs) if "edited by hand" in b.read_text()]
    check("hand edit after the last build: warned and kept in a backup",
          "changed after the last build" in msg and len(hand) == 1, msg)

    for i in range(4, 4 + kit.BACKUP_KEEP + 3):
        write(str(i), f)
    check(f"rotation keeps the newest {kit.BACKUP_KEEP}", len(backups(docs)) == kit.BACKUP_KEEP, str(len(backups(docs))))

    gi_before = (repo / ".gitignore").read_text()
    write("x", f)
    check("patterns are not appended twice", (repo / ".gitignore").read_text() == gi_before)

with tempfile.TemporaryDirectory() as tmp:
    plain = pathlib.Path(tmp)
    f = plain / "architecture.drawio"
    write("1", f); write("2", f)
    check("outside git: backup made, no .gitignore created",
          len(backups(plain)) == 1 and not (plain / ".gitignore").exists())
