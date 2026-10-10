#!/usr/bin/env python3
"""Build the website into _site/.

    python scripts/build.py            # build
    python scripts/build.py --serve    # build and preview at http://localhost:8000

Pages come from pages/*.html wrapped in templates/layout.html. The publications
page is generated from the .ris files in publications/papers/ and
publications/preprints/. Only the Python standard library is used.
"""
import argparse
import datetime as dt
import html
import json
import re
import shutil
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"
PUBS = ROOT / "publications"
CONFIG = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
MARKERS = "†*"
COLLAPSE_OVER = 20  # author lists longer than this get a "show all" button

# ---------------------------------------------------------------- RIS parsing


def parse_ris(text):
    """Return a list of {tag: [values]} dicts, one per record in the file."""
    records, cur, last = [], None, None
    for raw in text.lstrip("﻿").splitlines():
        m = re.match(r"^([A-Z][A-Z0-9])  -(?: (.*))?$", raw.rstrip())
        if not m:
            if cur is not None and last and raw.strip():  # wrapped continuation line
                cur[last][-1] += " " + raw.strip()
            continue
        tag, val = m.group(1), (m.group(2) or "").strip()
        if tag == "TY":
            cur, last = {"TY": [val]}, None
        elif tag == "ER":
            if cur:
                records.append(cur)
            cur, last = None, None
        elif cur is not None:
            cur.setdefault(tag, []).append(val)
            last = tag
    if cur:  # file without a final ER line
        records.append(cur)
    return records


def first(rec, *tags):
    for t in tags:
        for v in rec.get(t, []):
            if v:
                return v
    return ""


def clean_doi(doi):
    return re.sub(r"^(https?://)?(dx\.)?(www\.)?doi\.org/|^doi:\s*", "", doi.strip(), flags=re.I)


def norm(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9, ]", " ", text)).strip()


def split_author(raw):
    """'Last, First †' -> ('First Last', '†', 'last, first')."""
    raw = raw.strip()
    marks = ""
    while raw and raw[-1] in MARKERS + " ":
        if raw[-1] in MARKERS:
            marks = raw[-1] + marks
        raw = raw[:-1]
    if "," in raw:
        last, given = [p.strip() for p in raw.split(",", 1)]
        display = f"{given} {last}".strip()
    else:
        display = raw
    return display, "".join(sorted(set(marks), key=MARKERS.index)), raw


ME = [re.compile(p) for p in CONFIG["my_name_patterns"]]


def is_me(raw_name):
    n = norm(raw_name)
    return any(p.search(n) for p in ME)


def to_record(rec, kind, source):
    doi = clean_doi(first(rec, "DO"))
    title = first(rec, "TI", "T1", "CT", "BT")
    date = first(rec, "DA", "PY", "Y1", "Y2")
    year_m = re.search(r"(19|20)\d{2}", date)
    date_key = tuple(int(x) for x in re.findall(r"\d+", date)[:3]) if date else ()
    venue = first(rec, "T2", "JO", "JF", "JA", "J2")
    if not venue and kind == "preprint":
        venue = "bioRxiv" if doi.startswith(("10.1101/", "10.64898/")) else first(rec, "PB") or "Preprint"
    notes = [n.split(":", 1)[1].strip() for n in rec.get("N1", []) if n.lower().startswith("status:")]
    url = f"https://doi.org/{doi}" if doi else first(rec, "UR", "L1", "L2")
    authors = []
    for a in rec.get("AU", []) + rec.get("A1", []):
        display, marks, raw = split_author(a)
        authors.append({"name": display, "marks": marks, "me": is_me(raw)})
    return {
        "title": title, "authors": authors, "venue": venue, "year": int(year_m.group(0)) if year_m else 0,
        "date_key": date_key, "doi": doi, "url": url, "kind": kind, "status": "; ".join(notes),
        "source": source,
    }


def load_publications():
    pubs, seen = [], {}
    for kind, folder in (("paper", "papers"), ("preprint", "preprints")):
        for path in sorted((PUBS / folder).glob("*.ris")):
            for rec in parse_ris(path.read_text(encoding="utf-8", errors="replace")):
                p = to_record(rec, kind, path.relative_to(ROOT).as_posix())
                if not p["title"]:
                    print(f"  warning: skipped a record without a title in {p['source']}")
                    continue
                key = p["doi"].lower() or norm(strip_tags(p["title"]))
                if key in seen:
                    print(f"  warning: {p['source']} duplicates {seen[key]} — keeping the first")
                    continue
                seen[key] = p["source"]
                pubs.append(p)
    pubs.sort(key=lambda p: (p["year"], p["date_key"], norm(p["title"])), reverse=True)
    for i, p in enumerate(pubs):
        p["number"] = len(pubs) - i
    return pubs


def load_highlighted(pubs):
    path = PUBS / "highlighted.txt"
    if not path.exists():
        return []
    by_doi = {p["doi"].lower(): p for p in pubs if p["doi"]}
    by_title = {norm(strip_tags(p["title"])): p for p in pubs}
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = by_doi.get(clean_doi(line).lower()) or by_title.get(norm(line))
        if p:
            out.append(p)
        else:
            print(f"  warning: highlighted.txt entry not found among the .ris files: {line}")
    return out


# ---------------------------------------------------------------- HTML


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)


def safe_title(title):
    """Escape a title but keep the italic/sub/superscript markup publishers use."""
    t = html.escape(html.unescape(title), quote=False)
    t = re.sub(r"&lt;(/?)(i|em|sub|sup|b)&gt;", r"<\1\2>", t, flags=re.I)
    t = re.sub(r"&lt;/?[a-z:]+[^&]*?&gt;", "", t, flags=re.I)  # drop <scp>, <mml:...> and the like
    return t


def render_authors(authors):
    n = len(authors)
    collapse = n > COLLAPSE_OVER
    keep = set(range(10)) | set(range(n - 3, n)) if collapse else set(range(n))
    keep |= {i for i, a in enumerate(authors) if a["me"] or a["marks"]}
    parts, gap = [], False
    for i, a in enumerate(authors):
        hidden = i not in keep
        if hidden and not gap:
            parts.append('<span class="gap">…</span>')
        gap = hidden
        cls = ["au"] + (["me"] if a["me"] else []) + (["extra"] if hidden else [])
        marks = f'<sup class="mark">{html.escape(a["marks"])}</sup>' if a["marks"] else ""
        parts.append(f'<span class="{" ".join(cls)}"><span class="nm">{html.escape(a["name"])}</span>{marks}</span>')
    toggle = f'<button type="button" class="more" aria-expanded="false">Show all {n} authors</button>' if collapse else ""
    return f'<p class="authors{" collapsed" if collapse else ""}">{"".join(parts)}</p>{toggle}'


def render_pub(p, number):
    badge = '<span class="badge">Preprint</span>' if p["kind"] == "preprint" else ""
    status = f', {html.escape(p["status"])}' if p["status"] else ""
    title = safe_title(p["title"])
    title_html = f'<a href="{html.escape(p["url"])}" target="_blank" rel="noopener">{title}</a>' if p["url"] else title
    return (
        f'<li class="pub" data-kind="{p["kind"]}">'
        f'<span class="num">{number}.</span><div class="body">'
        f'<h3 class="pub-title">{title_html}</h3>'
        f'{render_authors(p["authors"])}'
        f'<p class="venue"><strong>{html.escape(p["venue"])}</strong>{status}, {p["year"] or "n.d."} {badge}</p>'
        f"</div></li>"
    )


def publications_page(pubs, highlighted):
    years = sorted({p["year"] for p in pubs}, reverse=True)
    n_pre = sum(p["kind"] == "preprint" for p in pubs)
    n_first = sum(1 for p in pubs if p["authors"] and (p["authors"][0]["me"] or any(a["me"] and "†" in a["marks"] for a in p["authors"])))
    jump = ['<a class="pill active" href="#highlighted">Highlighted</a>'] if highlighted else []
    jump += [f'<a class="pill" href="#year-{y}">{y or "n.d."}</a>' for y in years]
    sections = []
    if highlighted:
        items = "".join(render_pub(p, i + 1) for i, p in enumerate(highlighted))
        sections.append(f'<section id="highlighted" class="card pub-group"><h2>Highlighted papers</h2><ol class="pubs">{items}</ol></section>')
    sections.append('<h2 class="all-heading">All publications</h2>')
    for y in years:
        items = "".join(render_pub(p, p["number"]) for p in pubs if p["year"] == y)
        sections.append(f'<section id="year-{y}" class="card pub-group year-group"><h2>{y or "Undated"}</h2><ol class="pubs">{items}</ol></section>')
    return f"""
<section class="page-head">
  <p class="eyebrow">Research output</p>
  <h1>Publications</h1>
  <p class="lede">{len(pubs) - n_pre} peer-reviewed papers and {n_pre} preprints, {n_first} as first or co-first author.
  For citation metrics, see my <a href="https://scholar.google.com/citations?user=-HEC0H8AAAAJ&amp;hl=en" target="_blank" rel="noopener">Google Scholar profile</a>.</p>
</section>
<div class="pub-layout">
  <aside class="jump">
    <p class="eyebrow">Jump to</p>
    <nav>{"".join(jump)}</nav>
  </aside>
  <div class="pub-main">
    <div class="toolbar card">
      <input type="search" id="pub-search" placeholder="Search title, author, journal…" aria-label="Search publications">
      <div class="filters" role="group" aria-label="Filter">
        <button type="button" class="chip on" data-filter="all">All</button>
        <button type="button" class="chip" data-filter="paper">Papers</button>
        <button type="button" class="chip" data-filter="preprint">Preprints</button>
      </div>
      <p class="legend"><span><b class="mark">†</b> co-first authors</span><span><b class="mark">*</b> corresponding author</span><span><b class="me-swatch">Name</b> me</span></p>
    </div>
    <p id="no-results" class="card" hidden>No publications match your search.</p>
    {"".join(sections)}
  </div>
</div>"""


def selected_list(highlighted):
    items = "".join(render_pub(p, i + 1) for i, p in enumerate(highlighted[: CONFIG.get("selected_on_home", 5)]))
    return f'<ol class="pubs">{items}</ol>'


def profile_links():
    return "".join(
        f'<a class="profile" href="{html.escape(url)}" target="_blank" rel="noopener">'
        f'<img src="assets/img/icons/{icon}.png" alt="" width="20" height="20">{html.escape(label)}</a>'
        for label, url, icon in CONFIG["links"]
    )


def build():
    print("Building site…")
    pubs = load_publications()
    highlighted = load_highlighted(pubs)
    print(f"  {len(pubs)} publications ({sum(p['kind'] == 'preprint' for p in pubs)} preprints), {len(highlighted)} highlighted")

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "assets", OUT / "assets")
    layout = (ROOT / "templates" / "layout.html").read_text(encoding="utf-8")
    today = dt.date.today()
    values = {
        "name": html.escape(CONFIG["name"]),
        "tagline": html.escape(CONFIG["tagline"]),
        "profile_links": profile_links(),
        "selected_publications": selected_list(highlighted),
        "updated": today.strftime("%B %Y"),
        "year": str(today.year),
    }

    def fill(text):
        return re.sub(r"\{\{\s*(\w+)\s*\}\}", lambda m: values.get(m.group(1), m.group(0)), text)

    for page, title in CONFIG["pages"].items():
        body = publications_page(pubs, highlighted) if page == "publications.html" else (ROOT / "pages" / page).read_text(encoding="utf-8")
        nav = "".join(
            f'<a href="{href}"{" aria-current=page" if href == page else ""}>{label}</a>' for href, label in CONFIG["nav"]
        )
        full_title = CONFIG["name"] if page == "index.html" else f"{title} · {CONFIG['name']}"
        out = fill(layout.replace("{{content}}", fill(body)).replace("{{nav}}", nav).replace("{{title}}", html.escape(full_title)))
        (OUT / page).write_text(out, encoding="utf-8")
    (OUT / ".nojekyll").write_text("")
    print(f"  wrote {len(CONFIG['pages'])} pages to {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--serve", action="store_true", help="preview at http://localhost:8000 after building")
    args = ap.parse_args()
    build()
    if args.serve:
        import functools
        import http.server

        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
        print("Preview at http://localhost:8000  (Ctrl+C to stop)")
        http.server.ThreadingHTTPServer(("127.0.0.1", 8000), handler).serve_forever()
