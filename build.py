#!/usr/bin/env python3
"""Build the static site into docs/ (served by GitHub Pages). Stdlib only.

    python3 build.py            # writes docs/
    python3 -m http.server -d docs 8000
"""
import html, json, shutil
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
SRC, OUT = ROOT / "src", ROOT / "docs"

# Change SITE_URL when a custom domain is set up (and CNAME is written below).
SITE_URL = "https://mauriciohessflores.github.io"
CUSTOM_DOMAIN = ""      # e.g. "mauriciohessflores.com"
GOATCOUNTER = "mhessflores"   # dashboard: https://mhessflores.goatcounter.com
GOOGLE_VERIFY = "SFerGgqA7v_Tk9SlD5iYh78mS9imiPeHBFSEyyCAsgc"   # Search Console HTML tag; keep
NAME = "Mauricio Hess-Flores"
EMAIL = "mhessflores@spacescience.org"
PROFILES = {
    "Google Scholar": "https://scholar.google.com/citations?user=iLHqpg4AAAAJ",
    "ORCID": "https://orcid.org/0000-0003-0313-1009",
    "LinkedIn": "https://www.linkedin.com/in/mauriciohessflores/",
}
THEMES = {
    "geometry": "Multi-view geometry",
    "uncertainty": "Error and uncertainty visualization",
    "aerial": "Aerial and large-scale reconstruction",
    "earth": "Earth and planetary science",
    "early": "Image processing",
}
NAV = [("index.html", "Home"), ("publications.html", "Publications"),
       ("cv/CV_MauricioHessFlores.pdf", "CV")]

e = html.escape


def page(path, title, description, body, head_extra=""):
    depth = path.count("/")
    up = "../" * depth
    nav = "".join(
        f'<a href="{up}{href}"{" aria-current=page" if href == path else ""}>{label}</a>'
        for href, label in NAV)
    analytics = (f'<script data-goatcounter="https://{GOATCOUNTER}.goatcounter.com/count" '
                 'async src="//gc.zgo.at/count.js"></script>') if GOATCOUNTER else ""
    canonical = f"{SITE_URL}/{'' if path == 'index.html' else path}"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="google-site-verification" content="{GOOGLE_VERIFY}">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="website">
<meta property="og:image" content="{SITE_URL}/img/feature-tracks.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{up}style.css">
{head_extra}{analytics}
</head>
<body>
<header class="site"><div class="wrap">
<a class="brand" href="{up}index.html">{NAME}</a>
<nav>{nav}</nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer class="site"><div class="wrap">
<span>© {date.today().year} {NAME}</span>
<span><a href="mailto:{EMAIL}">{EMAIL}</a></span>
</div></footer>
</body>
</html>
"""


def authors_html(authors):
    return ", ".join(f"<strong>{e(a)}</strong>" if "Hess" in a else e(a) for a in authors)


def links(p, up=""):
    out = []
    if p.get("pdf"):
        out.append(f'<a href="{up}papers/{p["id"]}.pdf">PDF</a>')
    if p.get("doi"):
        out.append(f'<a href="https://doi.org/{p["doi"]}">DOI</a>')
    if p.get("url"):
        out.append(f'<a href="{p["url"]}">Open access</a>')
    if p.get("pdf") and not up:
        out.append(f'<a href="papers/{p["id"]}.html">Abstract</a>')
    return " · ".join(out)


def pub_item(p, up=""):
    award = f' <span class="award">{e(p["award"])}</span>' if p.get("award") else ""
    note = f' <span class="note">{e(p["note"])}.</span>' if p.get("note") else ""
    lk = links(p, up)
    return (f'<li data-theme="{p["theme"]}"><span class="ptitle">{e(p["title"])}</span>{award}<br>'
            f'<span class="pauth">{authors_html(p["authors"])}</span><br>'
            f'<span class="pvenue">{e(p["venue"])}, {p["year"]}.</span>{note}'
            f'{f"<br><span class=plinks>{lk}</span>" if lk else ""}</li>')


def scholar_meta(p):
    """Google Scholar inclusion tags (Highwire Press) for a paper landing page."""
    m = [("citation_title", p["title"])]
    m += [("citation_author", a) for a in p["authors"] if a != "et al."]
    m.append(("citation_publication_date", str(p["year"])))
    if p.get("journal"):
        m.append(("citation_journal_title", p["journal"]))
    elif p.get("conference"):
        m.append(("citation_conference_title", p["conference"]))
    if p.get("institution"):
        m.append(("citation_dissertation_institution", p["institution"]))
    if p.get("doi"):
        m.append(("citation_doi", p["doi"]))
    if p.get("abstract"):
        m.append(("citation_abstract", p["abstract"]))
    if p.get("pdf"):
        m.append(("citation_pdf_url", f"{SITE_URL}/papers/{p['id']}.pdf"))
    return "\n".join(f'<meta name="{k}" content="{e(v)}">' for k, v in m) + "\n"


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(SRC, OUT, ignore=shutil.ignore_patterns("*.html", "._*", ".DS_Store"))
    pubs = json.loads((ROOT / "data/publications.json").read_text())
    abstracts = json.loads((ROOT / "data/abstracts.json").read_text())
    urls = []

    # Home: src/index.html is the body; {{SELECTED}} lists papers by theme.
    body = (SRC / "index.html").read_text()
    for t in THEMES:
        sel = [p for p in pubs if p["theme"] == t and p["type"] != "abstract"][:4]
        body = body.replace(f"{{{{SELECTED:{t}}}}}",
                            "<ul class=mini>" + "".join(
                                f'<li><a href="{"papers/" + p["id"] + ".html" if p.get("pdf") else "https://doi.org/" + p["doi"] if p.get("doi") else "publications.html"}">'
                                f'{e(p["title"])}</a> <span>{e(p.get("conference") or p["venue"].split(",")[0])}</span></li>'
                                for p in sel) + "</ul>")
    sameas = json.dumps(list(PROFILES.values()))
    person = f"""<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Person","name":"{NAME}","alternateName":"Mauricio A. Hess-Flores",
"url":"{SITE_URL}/","image":"{SITE_URL}/img/feature-tracks.jpg","email":"mailto:{EMAIL}",
"jobTitle":"Computer Vision Scientist","affiliation":{{"@type":"Organization","name":"Space Science Institute"}},
"alumniOf":[{{"@type":"CollegeOrUniversity","name":"University of California, Davis"}},{{"@type":"CollegeOrUniversity","name":"Universidad de Costa Rica"}}],
"knowsAbout":["Computer vision","Space science","Planetary science","3D reconstruction","Structure from motion","Photogrammetry","Multi-view triangulation","Planetary science imaging","Geospatial data processing","Uncertainty visualization"],
"sameAs":{sameas}}}
</script>
"""
    (OUT / "index.html").write_text(page(
        "index.html", f"{NAME}, PhD | Computer Vision for Earth and Space Science",
        "Mauricio Hess-Flores is a computer vision scientist focused on Earth and space science: 3D reconstruction, "
        "structure-from-motion, photogrammetry and planetary mission imagery (Space Science Institute, NASA JPL, UC Davis, LLNL).",
        body, person))
    urls.append("")

    # Publications page
    groups = [("Journal articles", "journal"), ("Peer-reviewed conference and workshop papers", "conference"),
              ("Dissertation", "thesis"), ("Conference presentations and abstracts", "abstract")]
    filt = "".join(f'<button data-f="{k}">{v}</button>' for k, v in THEMES.items() if k != "early")
    parts = [f"""<h1>Publications</h1>
<p class="lead">Also on <a href="{PROFILES['Google Scholar']}">Google Scholar</a> and
<a href="{PROFILES['ORCID']}">ORCID</a>. PDFs are the authors' versions.</p>
<div class="filters" role="group" aria-label="Filter by topic"><button data-f="all" class="on">All</button>{filt}</div>"""]
    for label, kind in groups:
        items = [p for p in pubs if p["type"] == kind]
        parts.append(f"<h2>{label}</h2><ol class=pubs>" + "".join(pub_item(p) for p in items) + "</ol>")
    parts.append("""<h2>Data products</h2>
<p class="pauth">P. G. Brodrick, R. Pavlick, M. Bernas, J. W. Chapman, R. Eckert, M. Helmlinger, <strong>M. A. Hess-Flores</strong>, et al.
SHIFT airborne campaign datasets, ORNL DAAC:</p>
<ul class="plain">
<li>AVIRIS-NG L1B Calibrated Radiance, V2 (2025). <a href="https://doi.org/10.3334/ORNLDAAC/2432">doi:10.3334/ORNLDAAC/2432</a></li>
<li>AVIRIS-NG L2A Orthorectified Surface Reflectance, V2 (2025). <a href="https://doi.org/10.3334/ORNLDAAC/2431">doi:10.3334/ORNLDAAC/2431</a></li>
<li>AVNG L2 Weekly Georeferenced Surface Reflectance Mosaics (2025). <a href="https://doi.org/10.3334/ORNLDAAC/2289">doi:10.3334/ORNLDAAC/2289</a></li>
<li>AVIRIS-NG L2A Unrectified Surface Reflectance, V1 (2023). <a href="https://doi.org/10.3334/ORNLDAAC/2376">doi:10.3334/ORNLDAAC/2376</a></li>
<li>AVIRIS-NG L1A Unrectified Radiance (2023). <a href="https://doi.org/10.3334/ORNLDAAC/2184">doi:10.3334/ORNLDAAC/2184</a></li>
<li>AVIRIS-NG L2A Unrectified Reflectance (2023). <a href="https://doi.org/10.3334/ORNLDAAC/2183">doi:10.3334/ORNLDAAC/2183</a></li>
</ul>
<script>
document.querySelectorAll('.filters button').forEach(b => b.onclick = () => {
  document.querySelectorAll('.filters button').forEach(x => x.classList.toggle('on', x === b));
  document.querySelectorAll('ol.pubs li').forEach(li =>
    li.hidden = b.dataset.f !== 'all' && li.dataset.theme !== b.dataset.f);
});
</script>""")
    (OUT / "publications.html").write_text(page(
        "publications.html", f"Publications | {NAME}",
        "Papers by Mauricio Hess-Flores on multi-view triangulation, structure-from-motion, bundle adjustment, "
        "aerial 3D reconstruction, uncertainty visualization and atmospheric tomography, with PDFs.",
        "\n".join(parts)))
    urls.append("publications.html")

    # One landing page per paper with a PDF (what Google Scholar indexes)
    for p in pubs:
        if not p.get("pdf"):
            continue
        path = f"papers/{p['id']}.html"
        award = f'<p class="award">{e(p["award"])}</p>' if p.get("award") else ""
        body = f"""<p class="crumb"><a href="../publications.html">← Publications</a></p>
<h1 class="paper">{e(p['title'])}</h1>
<p class="pauth">{authors_html(p['authors'])}</p>
<p class="pvenue">{e(p['venue'])}, {p['year']}.</p>{award}
<p class="plinks big">{links(p, '../')}</p>
{f'<h2>Abstract</h2><p class="abstract">{e(abstracts[p["id"]])}</p>' if p["id"] in abstracts else ""}
<p class="topic">Topic: {THEMES[p['theme']]}</p>"""
        p["abstract"] = abstracts.get(p["id"], "")
        (OUT / path).write_text(page(path, f"{p['title']} ({p['year']})",
                                     f"{p['title']}. {', '.join(p['authors'])}. {p['venue']}, {p['year']}.",
                                     body, scholar_meta(p)))
        urls.append(path)

    today = date.today().isoformat()
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"<url><loc>{SITE_URL}/{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls)
        + "</urlset>\n")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    (OUT / ".nojekyll").write_text("")
    if CUSTOM_DOMAIN:
        (OUT / "CNAME").write_text(CUSTOM_DOMAIN + "\n")
    print(f"built {len(urls)} pages into {OUT}")


if __name__ == "__main__":
    build()
