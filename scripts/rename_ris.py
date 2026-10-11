#!/usr/bin/env python3
"""Give every .ris file in publications/ the standard name:

    <year>-<first-author-surname>-<first-title-words>.ris
    e.g. 2025-mannochio-russo-microbiome-diversifies-long-short-chain.ris

Usage:
    python scripts/rename_ris.py            # rename
    python scripts/rename_ris.py --dry-run  # only show what would change

Runs automatically in the GitHub Action before the site is built, so files
uploaded with any name (e.g. "citation (3).ris") are tidied up.
Files holding several records (e.g. a whole Zotero export) are left as they are.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from add_doi import slugify  # noqa: E402
from build import first, parse_ris  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FOLDERS = [ROOT / "publications" / "papers", ROOT / "publications" / "preprints"]


def standard_name(rec):
    date = first(rec, "PY", "DA", "Y1", "Y2")
    year = re.search(r"(19|20)\d{2}", date)
    author = re.sub(r"\s*[†*]+\s*$", "", first(rec, "AU", "A1"))
    surname = author.split(",")[0] if "," in author else (author.split() or ["anon"])[-1]
    title = first(rec, "TI", "T1", "CT")
    return f"{year.group(0) if year else 'nd'}-{slugify(surname, 3)}-{slugify(title)}.ris"


def plan():
    """Return [(old_path, new_path)] for files whose name is not the standard one."""
    moves = []
    for folder in FOLDERS:
        taken = {p.name for p in folder.glob("*.ris")}
        for path in sorted(folder.glob("*.ris")):
            records = parse_ris(path.read_text(encoding="utf-8", errors="replace"))
            if len(records) != 1:
                continue
            want = standard_name(records[0])
            stem = want[:-4]
            # already standard, including a "-2", "-3"... suffix used to avoid clashes
            if path.name == want or re.fullmatch(re.escape(stem) + r"-\d+\.ris", path.name):
                continue
            target, n = want, 2
            while target in taken:
                target = f"{stem}-{n}.ris"
                n += 1
            taken.discard(path.name)
            taken.add(target)
            moves.append((path, folder / target))
    return moves


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="show the changes without renaming")
    args = ap.parse_args()
    moves = plan()
    for old, new in moves:
        print(f"{'would rename' if args.dry_run else 'renamed'}: {old.relative_to(ROOT)} -> {new.name}")
        if not args.dry_run:
            old.rename(new)
    if not moves:
        print("All .ris file names are already standard.")


if __name__ == "__main__":
    main()
