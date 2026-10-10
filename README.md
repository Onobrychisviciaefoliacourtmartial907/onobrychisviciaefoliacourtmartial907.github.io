# Helena Mannochio Russo — personal website

A static website built by a small Python script (standard library only) and
published with GitHub Pages. The publications page is generated from `.ris`
citation files.

```
publications/
  papers/        ← peer-reviewed papers, one .ris file each
  preprints/     ← preprints, one .ris file each (shown with a "Preprint" tag)
  highlighted.txt← DOIs shown under "Highlighted" and on the home page
pages/           ← text of each page (Home, Experience, Awards, …)
templates/       ← header/footer shared by all pages
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

A `.ris` file can contain one paper or many (e.g. a whole Zotero export).
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
