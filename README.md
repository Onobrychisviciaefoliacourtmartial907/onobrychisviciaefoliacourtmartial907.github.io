# Helena Mannochio Russo — personal website

A static website built by a small Python script (standard library only) and
published with GitHub Pages. The publications page is generated from `.ris`
citation files.

```
publications/
  papers/        ← peer-reviewed papers, one .ris file each
  preprints/     ← preprints, one .ris file each (shown with a "Preprint" tag)
  highlighted.txt← DOIs shown under "Highlighted" and on the home page
data/presentations.txt ← talks and posters (Presentations page + CV)
pages/           ← text of each page (Home, Experience, Awards, …)
templates/       ← header/footer shared by all pages; cv.html = the CV
assets/          ← CSS, JavaScript, photo, icons
site.json        ← name, menu, profile links, how your name is recognized
scripts/build.py ← builds everything into _site/
scripts/add_doi.py ← downloads the .ris for a DOI
```

## Adding a new paper

**Option A — on github.com (no software needed)**

1. Download the citation as RIS from the journal page (usually "Cite" →
   "RIS"), Zotero, or Google Scholar.
2. In the repository, open `publications/papers/` (or `publications/preprints/`)
   → **Add file → Upload files** → drop the `.ris` file → **Commit changes**.
3. The site rebuilds automatically after the commit (Actions tab shows the
   progress, ~1 minute). You can also rebuild by hand: **Actions → Build and
   deploy website → Run workflow**.

**Option B — from your computer, by DOI**

```bash
python scripts/add_doi.py 10.1038/s41592-026-03186-8
python scripts/add_doi.py --preprint 10.1101/2024.05.13.593988
git add publications && git commit -m "Add new paper" && git push
```

The file can have any name: after each commit, GitHub renames it to the standard
`year-firstauthor-title-words.ris` (e.g. `2025-mannochio-russo-microbiome-diversifies-long-short-chain.ris`)
and commits the rename. On your computer you can do the same with
`python3 scripts/rename_ris.py` (add `--dry-run` to preview). Run `git pull`
before editing locally, since GitHub may have renamed files.

A `.ris` file can contain one paper or many (e.g. a whole Zotero export);
files with several papers keep their name.
If the same DOI appears twice, only the first copy is shown.

### Optional touches inside a .ris file

Open the file in any text editor:

| What | How |
|---|---|
| Co-first author | add ` †` at the end of their `AU` line: `AU  - Mannochio-Russo, Helena †` |
| Corresponding author | add ` *`: `AU  - Dorrestein, Pieter C. *` |
| Status note (e.g. "In press", "in revision at Nature") | add a line `N1  - status: In press` before `ER  -` |
| Preprint server name | `T2  - medRxiv` (defaults to bioRxiv for bioRxiv DOIs) |
| Wrong year | change the `PY  -` line |

When a preprint gets published, delete its file from `preprints/` (or keep
both) and add the published version to `papers/`.

## CV (PDF)

Every build creates `cv.html` and `cv.pdf` (printed with headless Chrome),
linked from the menu and the home page. The CV fills in automatically:

- **Publications / Manuscripts accepted / Preprints** come from the `.ris`
  files. A paper with `N1  - status: In press` goes under "Manuscripts accepted";
  remove that line once it is published.
- **Invited talks / Oral / Poster presentations** come from
  `data/presentations.txt`.

Everything else (education, skills, projects, awards, teaching, …) is written in
`templates/cv.html`; edit the text there and commit.

A Word version is kept **in the repository only** (not on the website):
`cv/Helena_Mannochio_Russo_CV.docx`, next to a copy of the PDF. The GitHub
Action regenerates both and commits them whenever the CV content changes, so
run `git pull` before editing locally. To refresh them on your computer:
`python3 -m pip install --user python-docx` (once), then
`python3 scripts/build.py --cv-files`.

## Adding a presentation

Add a block to `data/presentations.txt` (blank line between blocks):

```
year: 2026
type: oral
title: Your talk title
event: Conference name
location: City, State, Country
```

`type` can be `oral`, `poster`, `invited`, or several (`oral, poster`); add
`mode: online` for virtual talks. Commit, and the Presentations page and the
CV both update.

## Highlighted papers

Edit `publications/highlighted.txt`: one DOI per line, in the order you want.
The first five also appear as "Selected publications" on the home page
(change `selected_on_home` in `site.json`).

## Editing the other pages

Change the HTML in `pages/*.html` (awards, presentations, etc.) and commit.
The menu, profile links and name live in `site.json`.

## Preview on your computer

```bash
python3 scripts/build.py --serve
```

then open <http://localhost:8000>.

## First-time GitHub setup

1. Create an empty repository on GitHub (e.g. `helenamrusso.github.io` to get
   the address `https://helenamrusso.github.io`, or any name to get
   `https://helenamrusso.github.io/<name>`).
2. Push this folder:
   ```bash
   git remote add origin https://github.com/helenamrusso/<repo>.git
   git push -u origin main
   ```
3. On GitHub: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
4. **Actions → Build and deploy website → Run workflow** (or push any change).
