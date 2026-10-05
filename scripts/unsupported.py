"""The list of samples the bison frontend does not accept.

tests/unsupported_samples.txt names, one per line, a category of programs the
bison frontend leaves out (`generics`, `syntax`) and a sample path relative to
PaykanLang's samples corpus.  diff_frontends.py and samples_frontends.py skip
the listed files (--exclude); check_unsupported.py checks how the bison
frontend rejects each one.
"""
from __future__ import annotations

FEATURES = ("generics", "syntax")


def load(path: str) -> dict[str, str]:
    """The listed samples: {relative path: feature}."""
    entries: dict[str, str] = {}
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 2 or parts[0] not in FEATURES:
                raise SystemExit(f"{path}:{n}: expected '<feature> <path>' with "
                                 f"a feature of {', '.join(FEATURES)}: {line}")
            feature, rel = parts
            if rel in entries:
                raise SystemExit(f"{path}:{n}: {rel} is listed twice")
            entries[rel] = feature
    return entries
