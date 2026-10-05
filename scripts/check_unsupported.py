#!/usr/bin/env python3
"""Check how the bison frontend rejects the samples it does not accept.

For every sample in the list (tests/unsupported_samples.txt, see
scripts/unsupported.py), `paykan --dump-ast` must accept it with
recursive-descent (so the file is excluded for the feature alone), and
reject it with the bison frontend (exit status 1, no crash) as follows:

  generics  exactly one diagnostic, the generics one, located at a '<' of
            the source
  syntax    a syntax error first, never a crash (no internal error)

--generics <dir> adds every .pkn file below <dir> as a generics program
(tests/generics: one per generic construct).

Usage:
    check_unsupported.py --paykan <prefix>/bin/paykan --samples <dir>
        --list tests/unsupported_samples.txt [--generics tests/generics]
        [--paykan-arg=--plugin=<module> ...] [--frontend bison]
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import unsupported

GENERICS = ("generics are not supported by the bison frontend; "
            "use --frontend=recursive-descent")
ERROR_RE = re.compile(r"^.*:(\d+):(\d+): error: (.*)$", re.M)


def dump(paykan: list[str], frontend: str, path: Path):
    return subprocess.run([*paykan, f"--frontend={frontend}", "--dump-ast",
                           str(path)],
                          capture_output=True, text=True, errors="replace")


def problems(feature: str, path: Path, r) -> list[str]:
    if r.returncode != 1:
        return [f"exit status {r.returncode}, expected 1 (a rejected parse)"]
    errors = ERROR_RE.findall(r.stderr)
    if not errors:
        return ["no diagnostic"]
    if any("internal parser error" in msg for _, _, msg in errors):
        return ["internal parser error"]
    if feature == "generics":
        if len(errors) != 1 or errors[0][2] != GENERICS:
            return ["expected exactly the generics diagnostic, got: " +
                    "; ".join(msg for _, _, msg in errors)]
        line, col = int(errors[0][0]), int(errors[0][1])
        lines = path.read_text(encoding="utf-8").splitlines()
        if not (0 < line <= len(lines) and lines[line - 1][col - 1:col] == "<"):
            return [f"the generics diagnostic at {line}:{col} is not at a '<'"]
    elif not errors[0][2].startswith("syntax error"):
        return [f"expected a syntax error first, got: {errors[0][2]}"]
    return []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--paykan", required=True, help="the paykan binary")
    ap.add_argument("--paykan-arg", action="append", default=[],
                    help="an argument for every paykan run (repeatable)")
    ap.add_argument("--samples", required=True, type=Path,
                    help="the samples corpus (share/paykan/samples)")
    ap.add_argument("--list", required=True,
                    help="the list of unsupported samples")
    ap.add_argument("--generics", type=Path,
                    help="a directory of programs that use generics")
    ap.add_argument("--frontend", default="bison",
                    help="the frontend under test (default: bison)")
    args = ap.parse_args()
    paykan = [args.paykan, *args.paykan_arg]

    listed = unsupported.load(args.list)
    if not listed:
        print("error: the list is empty")
        return 1
    entries = {args.samples / rel: (rel, feature)
               for rel, feature in listed.items()}
    if args.generics:
        programs = sorted(args.generics.rglob("*.pkn"))
        if not programs:
            print(f"error: no .pkn files in {args.generics}")
            return 1
        for path in programs:
            entries[path] = (str(path.relative_to(args.generics.parent)),
                             "generics")
    failures = 0
    for path, (rel, feature) in sorted(entries.items()):
        if not path.is_file():
            found = [f"{rel} does not exist"]
        elif dump(paykan, "recursive-descent", path).returncode != 0:
            found = ["recursive-descent rejects it too: not a "
                     f"{feature}-only exclusion"]
        else:
            found = problems(feature, path, dump(paykan, args.frontend, path))
        if found:
            failures += 1
            print(f"FAIL {rel} ({feature}): " + "; ".join(found))
    counts = {f: sum(1 for _, v in entries.values() if v == f)
              for f in unsupported.FEATURES}
    print(f"{len(entries) - failures}/{len(entries)} unsupported programs "
          f"rejected as expected by {args.frontend} (" +
          ", ".join(f"{n} {f}" for f, n in counts.items()) + ")")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
