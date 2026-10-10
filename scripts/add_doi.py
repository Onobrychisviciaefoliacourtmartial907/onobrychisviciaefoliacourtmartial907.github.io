#!/usr/bin/env python3
"""Download the RIS citation for one or more DOIs into the publications folders.

Usage:
    python scripts/add_doi.py 10.1016/j.cell.2024.02.019
    python scripts/add_doi.py --preprint 10.1101/2024.05.13.593988
    python scripts/add_doi.py 10.1038/a 10.1038/b          # several at once

The file is saved as publications/papers/<year>-<first-author>-<title-words>.ris
(or publications/preprints/... with --preprint). Open it afterwards if you want
to mark co-first (†) or corresponding (*) authors or add a status note.
"""
import argparse
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STOPWORDS = {"a", "an", "the", "of", "and", "in", "on", "for", "to", "with", "by", "from", "via", "as", "at"}


def clean_doi(doi):
    doi = doi.strip()
    return re.sub(r"^(https?://)?(dx\.)?(www\.)?doi\.org/", "", doi, flags=re.I)


def fetch_ris(doi):
    req = urllib.request.Request(
        "https://doi.org/" + clean_doi(doi),
        headers={"Accept": "application/x-research-info-systems", "User-Agent": "personal-website-builder"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    if "TY  -" not in text:
        raise ValueError(f"doi.org did not return RIS for {doi}")
    return text.replace("\r\n", "\n").strip() + "\n"


def slugify(text, max_words=5):
    text = re.sub(r"<[^>]+>", " ", text)  # titles may carry <i>, <sub>... markup
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    words = [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS]
    return "-".join(words[:max_words]) or "untitled"


def filename_for(ris):
    def first(tag):
        m = re.search(rf"^{tag}  - (.+)$", ris, flags=re.M)
        return m.group(1).strip() if m else ""

    year = re.search(r"\d{4}", first("PY") or first("DA") or first("Y1") or "")
    surname = (first("AU") or first("A1") or "anon").split(",")[0]
    return f"{year.group(0) if year else 'nd'}-{slugify(surname, 2)}-{slugify(first('TI') or first('T1'))}.ris"


def add(doi, preprint=False, venue=None):
    ris = fetch_ris(doi)
    if preprint and not re.search(r"^(T2|JO|JF)  - ", ris, flags=re.M):
        # Crossref leaves the server name out of preprint records
        name = venue or ("bioRxiv" if clean_doi(doi).startswith(("10.1101/", "10.64898/")) else "Preprint")
        ris = ris.replace("\nAU  - ", f"\nT2  - {name}\nAU  - ", 1)
    folder = ROOT / "publications" / ("preprints" if preprint else "papers")
    path = folder / filename_for(ris)
    n = 2
    while path.exists() and clean_doi(doi).lower() not in path.read_text(encoding="utf-8").lower():
        path = folder / filename_for(ris).replace(".ris", f"-{n}.ris")
        n += 1
    path.write_text(ris, encoding="utf-8")
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dois", nargs="+")
    ap.add_argument("--preprint", action="store_true", help="save into publications/preprints/")
    ap.add_argument("--venue", help="preprint server name, e.g. medRxiv (default: bioRxiv for 10.1101 DOIs)")
    args = ap.parse_args()
    failed = False
    for doi in args.dois:
        try:
            print("saved", add(doi, args.preprint, args.venue).relative_to(ROOT))
        except Exception as e:  # keep going for the remaining DOIs
            failed = True
            print(f"FAILED {doi}: {e}", file=sys.stderr)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
