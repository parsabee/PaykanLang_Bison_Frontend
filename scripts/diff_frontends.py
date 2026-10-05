#!/usr/bin/env python3
"""Differential check of the Paykan frontends.

Runs `paykan --frontend=<name> --dump-ast` with two frontends over every
`.pkn` file below the given directories and reports any file for which the
two differ in exit status or in the printed AST.  Both frontends must accept
the same inputs, reject the same inputs and build the same AST (PaykanLang's
docs/grammar.md); this script is the CI gate for that rule.  Diagnostics are
not compared: their wording, and the errors after the first (each frontend
recovers in its own way), may differ between frontends (docs/grammar.md
section 9).

Usage:
    scripts/diff_frontends.py --paykan <prefix>/bin/paykan <dir> [dir ...]
        [--paykan-arg=--plugin=<module> ...] [--frontends recursive-descent,bison]
        [--exclude tests/unsupported_samples.txt]

--paykan-arg passes an argument to every paykan run (repeatable): the
plugin to load (`--paykan-arg=--no-plugins --paykan-arg=--plugin=<file>`).

--exclude skips the files a list names (scripts/unsupported.py), by their
path relative to the directory they are found in: the programs that use a
feature the bison frontend leaves out.  A listed file that none of the
directories has is an error, so the list cannot go stale unnoticed.

The installed samples corpus is <paykan-prefix>/share/paykan/samples
(PAYKAN_SAMPLES_DIR in CMake).

Exits non-zero when any file differs or a frontend is unavailable.
"""
from __future__ import annotations

import argparse
import difflib
import os
import subprocess
import sys

import unsupported


def dump(paykan: list[str], frontend: str, path: str) -> tuple[int, str, str]:
    r = subprocess.run(
        [*paykan, f"--frontend={frontend}", "--dump-ast", path],
        capture_output=True,
        text=True,
        errors="replace",
    )
    return r.returncode, r.stdout, r.stderr


def collect(dirs: list[str], excluded: set[str]) -> tuple[list[str], set[str]]:
    """The .pkn files below dirs but the excluded ones, and the excluded
    paths that were found."""
    files: list[str] = []
    found: set[str] = set()
    for d in dirs:
        for root, _, names in os.walk(d):
            for n in names:
                if not n.endswith(".pkn"):
                    continue
                path = os.path.join(root, n)
                rel = os.path.relpath(path, d).replace(os.sep, "/")
                if rel in excluded:
                    found.add(rel)
                else:
                    files.append(path)
    return sorted(files), found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--paykan", required=True, help="path to the paykan binary")
    ap.add_argument(
        "--frontends",
        default="recursive-descent,bison",
        help="comma-separated pair of frontend names (default: recursive-descent,bison)",
    )
    ap.add_argument(
        "--paykan-arg",
        action="append",
        default=[],
        help="an argument for every paykan run, e.g. --paykan-arg=--plugin=<file>",
    )
    ap.add_argument(
        "--exclude",
        help="a list of files to skip (tests/unsupported_samples.txt)",
    )
    ap.add_argument("dirs", nargs="+", help="directories to scan for .pkn files")
    args = ap.parse_args()
    paykan = [args.paykan, *args.paykan_arg]

    names = [n.strip() for n in args.frontends.split(",") if n.strip()]
    if len(names) != 2:
        sys.exit("error: --frontends needs exactly two names")
    dirs = args.dirs

    listed = subprocess.run(
        [*paykan, "--list-frontends"], capture_output=True, text=True
    ).stdout
    # "<name>[ (default)][: <description>][ [<file>]]" per frontend.
    available = [line.split()[0].rstrip(":") for line in listed.splitlines()
                 if line.strip() and not line.startswith("rejected plugin")]
    for n in names:
        if n not in available:
            sys.exit(f"error: frontend '{n}' is not available in "
                     f"{' '.join(paykan)} (available: {available})\n{listed}")

    excluded = set(unsupported.load(args.exclude)) if args.exclude else set()
    files, found = collect(dirs, excluded)
    if not files:
        sys.exit("error: no .pkn files found")
    if excluded - found:
        sys.exit("error: excluded files not found: " +
                 ", ".join(sorted(excluded - found)))

    failures = 0
    accepted = rejected = 0
    for path in files:
        a = dump(paykan, names[0], path)
        b = dump(paykan, names[1], path)
        if a[0] != b[0] or a[1] != b[1]:
            failures += 1
            rel = os.path.relpath(path, os.path.commonpath(dirs))
            print(f"DIFF {rel}: {names[0]} exit={a[0]}, {names[1]} exit={b[0]}")
            if a[0] == 0 and b[0] == 0:
                for line in list(difflib.unified_diff(
                        a[1].splitlines(), b[1].splitlines(),
                        fromfile=names[0], tofile=names[1], lineterm=""))[:20]:
                    print("   ", line)
            else:
                for n, r in ((names[0], a), (names[1], b)):
                    first = r[2].strip().splitlines()[:1]
                    print(f"    {n}: {first[0] if first else '(no diagnostic)'}")
            continue
        if a[0] == 0:
            accepted += 1
        else:
            rejected += 1

    print(f"{len(files)} files: {accepted} accepted and {rejected} rejected "
          f"identically by {names[0]} and {names[1]}; {failures} differ; "
          f"{len(found)} excluded")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
