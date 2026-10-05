#!/usr/bin/env python3
"""Run PaykanLang's samples corpus with each frontend and compare the results.

Every runnable sample (codegen/, leak-check/ and each imports/<dir>/main.pkn
not named err_*) is run with `paykan --frontend=<name> --backend=<backend>
--track-heap` for every frontend named on the command line.  The frontends
must agree on stdout, on stderr (apart from the heap statistics) and on the
exit code, and every run must end with zero live heap blocks.  A sample with
`// expect-stdout: <line>` comments must print exactly those lines.  Printed
object addresses (`Foo@0x...`) are normalised before comparing.

Every sample runs with the arguments `a b`, or with the words of its
`// args: <word>...` line, where `{tmpdir}` is a fresh, empty directory for
that run alone.

The corpus is copied to a scratch directory first: the installed one
(<paykan-prefix>/share/paykan/samples) may be read-only, and the import
samples write module caches next to themselves.

Usage:
    samples_frontends.py --paykan <prefix>/bin/paykan --samples <dir>
        [--paykan-arg=--plugin=<module> ...]
        [--backend c] --frontend recursive-descent --frontend bison
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ADDR_RE = re.compile(r"@0x[0-9a-fA-F]+")
LIVE_RE = re.compile(r"^  live blocks\s*:\s*(-?\d+)$", re.M)
STATS_RE = re.compile(r"^paykan heap stats:\n(?:  .*\n?)*", re.M)
EXPECT_RE = re.compile(r"^// expect-stdout:(?: (.*))?$", re.M)
ARGS_RE = re.compile(r"^// args:(.*)$", re.M)
DEFAULT_ARGS = ["a", "b"]
TMPDIR = "{tmpdir}"


def samples(root):
    files = sorted((root / "codegen").glob("*.pkn"))
    files += sorted((root / "leak-check").glob("*.pkn"))
    imports = root / "imports"
    if imports.is_dir():
        for d in sorted(imports.iterdir()):
            main = d / "main.pkn"
            if main.is_file() and not d.name.startswith("err_"):
                files.append(main)
    return files


def expected_stdout(sample):
    lines = EXPECT_RE.findall(sample.read_text())
    if not lines:
        return None
    return "".join(line + "\n" for line in lines)


def sample_args(sample, scratch):
    m = ARGS_RE.search(sample.read_text())
    if not m:
        return list(DEFAULT_ARGS)
    words = m.group(1).split()
    if any(TMPDIR in w for w in words):
        tmp = tempfile.mkdtemp(prefix=f"{sample.stem}-", dir=scratch)
        words = [w.replace(TMPDIR, tmp) for w in words]
    return words


def run(paykan, frontend, backend, sample, scratch, cwd):
    cmd = [*paykan, f"--frontend={frontend}", f"--backend={backend}",
           "--track-heap", str(sample), *sample_args(sample, scratch)]
    p = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True,
                       text=True, errors="replace", cwd=str(cwd))
    out = ADDR_RE.sub("@ADDR", p.stdout)
    m = LIVE_RE.search(p.stderr)
    live = int(m.group(1)) if m else None
    err = ADDR_RE.sub("@ADDR", STATS_RE.sub("", p.stderr))
    return p.returncode, out, err, live


def check(args, scratch):
    corpus = Path(scratch) / "samples"
    shutil.copytree(args.samples, corpus,
                    ignore=shutil.ignore_patterns(".paykan_cache"))
    files = samples(corpus)
    if not files:
        print(f"error: no samples under {args.samples}")
        return 1
    failures = 0
    for sample in files:
        rel = sample.relative_to(corpus)
        results = {fe: run([args.paykan, *args.paykan_arg], fe, args.backend,
                           sample, scratch, corpus)
                   for fe in args.frontend}
        problems = []
        for fe, (rc, out, err, live) in results.items():
            if live is None:
                problems.append(f"{fe}: no heap report (exit {rc})")
            elif live != 0:
                problems.append(f"{fe}: {live} live blocks")
        expected = expected_stdout(sample)
        if expected is not None:
            for fe, (_, out, _, _) in results.items():
                if out != expected:
                    problems.append(f"{fe}: stdout differs from expect-stdout")
        ref_name = args.frontend[0]
        ref = results[ref_name]
        for fe in args.frontend[1:]:
            rc, out, err, _ = results[fe]
            if rc != ref[0]:
                problems.append(f"exit code {ref_name}={ref[0]} {fe}={rc}")
            if out != ref[1]:
                problems.append(f"stdout differs between {ref_name} and {fe}")
            if err != ref[2]:
                problems.append(f"stderr differs between {ref_name} and {fe}")
        if problems:
            failures += 1
            print(f"FAIL {rel}: " + "; ".join(problems))
            if args.verbose:
                for fe, (rc, out, err, live) in results.items():
                    print(f"--- {fe} (exit {rc}, live {live})\n{out}{err}")
        elif args.verbose:
            print(f"ok   {rel}")
    print(f"{len(files) - failures}/{len(files)} samples identical on "
          f"{', '.join(args.frontend)} (backend {args.backend})")
    return 1 if failures else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--paykan", required=True, help="the paykan binary")
    ap.add_argument("--samples", required=True, type=Path,
                    help="the samples corpus (share/paykan/samples)")
    ap.add_argument("--backend", default="c", help="the backend (default: c)")
    ap.add_argument("--frontend", action="append", required=True,
                    help="a frontend to run (repeatable; the first is the "
                         "reference)")
    ap.add_argument("--paykan-arg", action="append", default=[],
                    help="an argument for every paykan run, e.g. "
                         "--paykan-arg=--plugin=<file> (repeatable)")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    args.paykan = os.path.abspath(args.paykan)
    with tempfile.TemporaryDirectory(prefix="paykan-frontends-") as scratch:
        return check(args, scratch)


if __name__ == "__main__":
    sys.exit(main())
