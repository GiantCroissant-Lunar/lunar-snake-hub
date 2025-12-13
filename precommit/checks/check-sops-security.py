#!/usr/bin/env python3
"""Cross-platform SOPS security pre-commit hook.

Port of check-sops-security.sh to Python so it works on Windows and Unix.

Checks:
- .sops/age.key is never added/modified (only deletions allowed)
- Added lines containing AGE-SECRET-KEY in staged diffs
- age.key-like filenames being added/modified (warning)
- *.enc.json / *.enc.yaml contain SOPS metadata
- Warn if .sops/age.key is not ignored in .gitignore
- On POSIX, warn if .sops/age.key permissions are not 600
"""

from __future__ import annotations

import os
import re
import stat
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

RED = ""
YELLOW = ""
GREEN = ""
NC = ""


def git(args: List[str]) -> Tuple[int, str]:
    """Run git command and return (exit_code, stdout).

    Uses UTF-8 with replacement to avoid decode errors on Windows consoles.
    """
    proc = subprocess.run(
        ["git", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout or ""


def get_staged_files(diff_filter: str | None = None) -> List[str]:
    args = ["diff", "--cached", "--name-only"]
    if diff_filter:
        args.insert(2, f"--diff-filter={diff_filter}")
    code, out = git(args)
    if code not in (0, 1):
        # 1 can occur when there are no differences for that filter
        print(f"Error: git {' '.join(args)} failed with code {code}")
        sys.exit(1)
    return [line.strip() for line in out.splitlines() if line.strip()]


def check_age_key_staged() -> bool:
    """Check if .sops/age.key is staged for add/modify (disallowed)."""
    issues = False
    staged = set(get_staged_files())
    if ".sops/age.key" in staged:
        deleted = ".sops/age.key" in set(get_staged_files("D"))
        if deleted:
            print("OK: .sops/age.key is being removed from git (good!)")
        else:
            print("ERROR: SOPS private key (.sops/age.key) is staged!")
            print()
            print("  This key must NEVER be committed to git.")
            print("  It would compromise ALL encrypted secrets.")
            print()
            print("  To fix:")
            print("    git restore --staged .sops/age.key")
            print()
            issues = True
    return issues


def check_age_secret_key_in_diff() -> bool:
    """Scan staged diff for AGE-SECRET-KEY additions outside security docs."""
    issues = False
    code, diff = git(["diff", "--cached"])
    if code not in (0, 1):
        print(f"Error: git diff --cached failed with code {code}")
        sys.exit(1)
    if not diff:
        return False
    current_file: str | None = None
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:].strip()
            continue
        if not line.startswith("+") or line.startswith("+++"):
            continue
        if "AGE-SECRET-KEY" not in line:
            continue
        # Skip this script and docs/security/* as in the original shell script
        if current_file and (
            current_file.startswith("docs/security/")
            or current_file.startswith("precommit/checks/check-sops-security.")
        ):
            continue
        print("ERROR: Found AGE-SECRET-KEY being added in staged changes!")
        print()
        print("  This appears to be a private age encryption key.")
        print("  Private keys must never be committed.")
        print()
        print("  To fix:")
        print("    1. Review: git diff --cached")
        print("    2. Unstage the file containing the key")
        print("    3. Remove the private key from the file")
        print()
        issues = True
        break
    return issues


def check_age_key_filenames() -> bool:
    """Warn if age.key-like files are being added/modified."""
    issues = False
    staged_am = get_staged_files("AM")
    age_like = [f for f in staged_am if re.search(r"age\.key(\.backup)?$", f)]
    if age_like:
        print("WARNING: Found age key file pattern being added/modified")
        print()
        print("  Files matching 'age.key' pattern:")
        for f in age_like:
            print(f"    {f}")
        print()
        print("  Verify these are not private keys!")
        print()
        # This was a warning in the shell script, but we mark an issue to be safe
        issues = True
    return issues


def check_encrypted_files() -> bool:
    """Verify *.enc.json / *.enc.yaml contain SOPS metadata."""
    issues = False
    staged = get_staged_files()
    encrypted = [f for f in staged if re.search(r"\.(enc\.json|enc\.yaml)$", f)]
    if not encrypted:
        return issues

    for path_str in encrypted:
        path = Path(path_str)
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError as e:
            print(f"ERROR: Unable to read {path}: {e}")
            issues = True
            continue

        has_json_sops = bool(re.search(r'"sops"\s*:\s*{', text))
        has_yaml_sops = bool(re.search(r"^sops:\s*$", text, flags=re.MULTILINE))
        has_enc = "ENC[" in text

        if not (has_json_sops or has_yaml_sops or has_enc):
            print(f"ERROR: {path} appears to be unencrypted!")
            print()
            print(
                '  Encrypted files must contain SOPS metadata ("sops": or sops: or ENC[).'
            )
            print("  This file may have been decrypted and not re-encrypted.")
            print()
            print("  To fix:")
            print(f"    sops --encrypt {path} > {path}.tmp && mv {path}.tmp {path}")
            print()
            issues = True
        else:
            print(f"OK: {path} appears to be properly encrypted")
    return issues


def check_gitignore() -> None:
    gitignore = Path(".gitignore")
    if not gitignore.is_file():
        return
    try:
        content = gitignore.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return
    if ".sops/age.key" not in content:
        print("WARNING: .gitignore doesn't exclude .sops/age.key")
        print()
        print("  Add to .gitignore:")
        print("    .sops/age.key")
        print("    .sops/*.backup.*")
        print()


def check_age_key_permissions() -> None:
    path = Path(".sops/age.key")
    if not path.is_file():
        return
    # On POSIX, ensure 600; on Windows, just skip this check
    if os.name != "posix":
        return
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
    except OSError:
        return
    if mode != 0o600:
        print(
            f"WARNING: .sops/age.key has permissions {oct(mode)} (should be 0o600)",
        )
        print()
        print("  To fix:")
        print("    chmod 600 .sops/age.key")
        print()


def main() -> int:
    print("Checking SOPS security...")

    issues_found = False

    print("  Checking for private key in staged files...")
    if check_age_key_staged():
        issues_found = True

    print("  Checking for private key content in staged changes...")
    if check_age_secret_key_in_diff():
        issues_found = True

    print("  Checking for age key file patterns...")
    if check_age_key_filenames():
        issues_found = True

    print("  Verifying encrypted files contain SOPS metadata...")
    if check_encrypted_files():
        issues_found = True

    print("  Checking .gitignore for SOPS patterns...")
    check_gitignore()

    print("  Checking .sops/age.key permissions (if present)...")
    check_age_key_permissions()

    print()
    if not issues_found:
        print("SOPS security checks passed.")
        return 0

    print("SOPS security issues found.")
    print()
    print("Review the errors above and fix them before committing.")
    print()
    print("For more information, see:")
    print("  docs/security/README.md")
    print()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
