#!/usr/bin/env python3
"""The nesting limit is the same with the bison frontend as with
recursive-descent.

PaykanLang's GrammarEdge.NestingLimitIsTheSameOnEveryFrontend checks this in
the parser suite, but one of its constructs is a generic type, which the bison
frontend does not accept, so that test is filtered out (tests/CMakeLists.txt).
This script checks every other construct of it, and the conversions, through
`paykan --dump-ast`: built exactly at the limit (512 levels, docs/grammar.md
section 9, counting the function body) each frontend accepts it, and one level
past it each rejects it, the bison frontend first with `nesting too deep`.
(Recursive descent reports a conversion one level too deep as a chained
comparison instead: its look-ahead for type arguments gives up at the limit.)

Usage:
    nesting_limit.py --paykan <prefix>/bin/paykan
        [--paykan-arg=--plugin=<module> ...] [--frontend bison]
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile

LIMIT = 512
NESTING = "error: nesting too deep (more than 512 levels)"


def in_main(stmts: str) -> str:
    return "fn main() -> int { " + stmts + " return 0; }\n"


# Each construct nests n levels inside the function body.
CONSTRUCTS = {
    "blocks": lambda n: in_main("{ " * n + "} " * n),
    "if statements": lambda n: in_main("if (a) { " * n + "} " * n),
    "parentheses": lambda n: in_main("x = " + "(" * n + "1" + ")" * n + ";"),
    "array literals": lambda n: in_main("x = " + "[" * n + "1" + "]" * n + ";"),
    "calls": lambda n: in_main("x = " + "f(" * n + "1" + ")" * n + ";"),
    "subscripts": lambda n: in_main("x = " + "a[" * n + "1" + "]" * n + ";"),
    "prefix operators": lambda n: in_main("x = " + "!" * n + "a;"),
    "unary minus": lambda n: in_main("x = a - " + "- " * n + "a;"),
    "conditionals": lambda n: in_main("x = " + "if a then 1 else " * n + "2;"),
    "nested then-branches": lambda n: in_main(
        "x = " + "if a then " * n + "1" + " else 2" * n + ";"),
    "tuple types": lambda n: in_main(
        "x: " + "(int, " * n + "int" + ")" * n + " = 1;"),
    "conversions": lambda n: in_main(
        "x = " + "Str<int>(" * n + "1" + ")" * n + ";"),
    "conversion source types": lambda n: in_main(
        "x = Str<" + "(int, " * (n - 1) + "int" + ")" * (n - 1) + ">(1);"),
    "mixed": lambda n: in_main(
        "x = " + "-(" * (n // 2) + ("-1" if n % 2 else "1") + ")" * (n // 2)
        + ";"),
    "empty brackets at the limit": lambda n: in_main(
        "{ " * (n - 1) + "f(); x: int[] = []; " + "} " * (n - 1)),
}


def outcome(paykan: list[str], frontend: str, path: str) -> tuple[bool, str]:
    r = subprocess.run([*paykan, f"--frontend={frontend}", "--dump-ast", path],
                       capture_output=True, text=True, errors="replace")
    if r.returncode == 0:
        return True, ""
    first = re.search(r"error: .*", r.stderr)
    return False, first.group(0) if first else f"exit {r.returncode}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--paykan", required=True, help="the paykan binary")
    ap.add_argument("--paykan-arg", action="append", default=[],
                    help="an argument for every paykan run (repeatable)")
    ap.add_argument("--frontend", default="bison",
                    help="the frontend compared with recursive-descent")
    args = ap.parse_args()
    paykan = [args.paykan, *args.paykan_arg]

    failures = 0
    with tempfile.TemporaryDirectory(prefix="paykan-nesting-") as tmp:
        path = os.path.join(tmp, "t.pkn")
        for what, make in CONSTRUCTS.items():
            # Empty brackets add no level: at the limit only.
            sizes = [LIMIT - 1] if what.startswith("empty") else [LIMIT - 1, LIMIT]
            for n in sizes:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(make(n))
                accept = n < LIMIT
                for fe in ("recursive-descent", args.frontend):
                    ok, first = outcome(paykan, fe, path)
                    if ok != accept or (not ok and fe == args.frontend
                                        and first != NESTING):
                        failures += 1
                        print(f"FAIL {what} x{n}, {fe}: " +
                              ("accepted" if ok else first))
    print(f"{len(CONSTRUCTS)} constructs: {failures} failures")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
