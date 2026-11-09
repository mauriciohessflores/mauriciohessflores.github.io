# Personal research website

Static site for Mauricio Hess-Flores, built with `python3 build.py` (stdlib only) into `docs/`, served by GitHub Pages from `docs/`.

- `src/index.html` – home page body (`{{SELECTED:<theme>}}` is filled from the publication data)
- `src/style.css`, `src/img/`, `src/papers/*.pdf`, `src/cv/` – copied as is
- `data/publications.json` – the publication list; `pdf: true` means `src/papers/<id>.pdf` exists and gets a landing page with Google Scholar tags
- `data/abstracts.json` – abstracts extracted from the PDFs
- `build.py` – settings at the top: `SITE_URL`, `CUSTOM_DOMAIN`, `GOATCOUNTER`

Preview: `python3 -m http.server -d docs 8000`.
