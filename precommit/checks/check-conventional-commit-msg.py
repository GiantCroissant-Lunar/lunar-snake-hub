#!/usr/bin/env python3
import re
import sys
from pathlib import Path

ALLOWED_TYPES = {
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "build",
    "ci",
    "chore",
    "revert",
}


def read_commit_message() -> str:
    # commit-msg hook normally passes the file path as argv[1].
    # However, on some Windows setups we observed that this can be missing.
    if len(sys.argv) >= 2 and sys.argv[1]:
        p = Path(sys.argv[1])
        if p.is_file():
            return p.read_text(encoding="utf-8", errors="replace")

    # Fallback to git's default commit message file.
    fallback = Path(".git") / "COMMIT_EDITMSG"
    if fallback.is_file():
        return fallback.read_text(encoding="utf-8", errors="replace")

    return ""


def main() -> int:
    msg = read_commit_message().splitlines()
    first_line = ""
    for line in msg:
        if line.strip() and not line.strip().startswith("#"):
            first_line = line.strip()
            break

    if not first_line:
        print("ERROR: Empty commit message")
        return 1

    # Conventional commit: type(scope?)!: subject
    m = re.match(r"^(?P<type>[a-z]+)(\([^)]+\))?(?P<bang>!)?:\s+.+$", first_line)
    if not m:
        print(
            "ERROR: Commit message must follow conventional format: type(scope?): subject"
        )
        print(f"  Got: {first_line}")
        return 1

    commit_type = m.group("type")
    if commit_type not in ALLOWED_TYPES:
        print("ERROR: Commit type is not allowed")
        print(f"  Got: {commit_type}")
        print(f"  Allowed: {', '.join(sorted(ALLOWED_TYPES))}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
