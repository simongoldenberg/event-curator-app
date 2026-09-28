"""Prüft Git-Index und Historie vor einem Upload. Kein Ersatz für eine Diff-Prüfung."""
from pathlib import PurePosixPath
import re
import subprocess
import sys

ROOT_FILES = {".gitignore", ".env.example", "AGENTS.md", "README.md", "CHANGELOG.md", "LICENSE", "requirements.txt", "config.py", "main.py"}
SOURCE_DIRS = {"event_curator", "scripts", "tests"}
SECRET = re.compile(rb"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|(?im:^BANDSINTOWN_APP_ID[ \t]*=[ \t]*[^\s#]+))")


def public_path(path):
    p = PurePosixPath(path)
    if path in ROOT_FILES or path in {"data/sample_artists.csv", "event_curator/ui/europe_map.svg", "event_curator/ui/dashboard.css", "event_curator/ui/dashboard.js"}:
        return True
    return len(p.parts) > 1 and p.parts[0] in SOURCE_DIRS and p.suffix in {".py", ".ps1", ".sh", ".md"} and not any(part.startswith("user_") for part in p.parts)


def git(*args):
    return subprocess.check_output(["git", *args], stderr=subprocess.DEVNULL)


def inspect_tree(records, issues):
    for record in records.split(b"\0"):
        if not record:
            continue
        meta, raw_path = record.split(b"\t", 1)
        path = raw_path.decode("utf-8")
        fields = meta.decode().split()
        mode, object_id = fields[0], fields[-1]
        if not public_path(path):
            issues.add(f"Nicht freigegebener Git-Pfad: {path}")
        if mode in ("120000", "160000"):
            issues.add(f"Symlink/Submodul nicht für Upload freigegeben: {path}")
            continue
        content = git("cat-file", "blob", object_id)
        if SECRET.search(content):
            issues.add(f"Möglicher Zugangsschlüssel in: {path} (Wert wird nicht ausgegeben)")


def check():
    issues = set()
    staged = git("ls-files", "--stage", "-z")
    tree = []
    for record in staged.split(b"\0"):
        if record:
            meta, path = record.split(b"\t", 1)
            mode, oid, stage = meta.split()
            if stage != b"0":
                issues.add("Ungelöste Merge-Konflikte im Index.")
            tree.append(mode + b" blob " + oid + b"\t" + path)
    inspect_tree(b"\0".join(tree), issues)
    for commit in git("rev-list", "--all").decode().splitlines():
        inspect_tree(git("ls-tree", "-r", "-z", commit), issues)
    probes = ["data/artists.csv", "data/user_party_profile.json", "data/user_upload.csv", "data/arbitrary.txt", ".env", "exports/digest.html", "local.db", "preferences.json"]
    for path in probes:
        result = subprocess.run(["git", "check-ignore", "--no-index", "-q", path], capture_output=True)
        if result.returncode != 0:
            issues.add(f"Gitignore-Schutz fehlt: {path}")
    if issues:
        print("Upload blockiert:", file=sys.stderr)
        for issue in sorted(issues):
            print("- " + issue, file=sys.stderr)
        return 1
    print("Datenschutzprüfung: Index und erreichbare Historie enthalten nur freigegebene Dateipfade; keine erkannten Zugangsschlüssel.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(check())
    except (subprocess.CalledProcessError, ValueError, OSError):
        print("Datenschutzprüfung fehlgeschlagen; kein Upload freigegeben.", file=sys.stderr)
        raise SystemExit(1)
