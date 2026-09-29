#!/usr/bin/env python3
"""
Convierte el export eXeLearning "Guia_Calidad_Seis_Sigma" en una web estática moderna.

Uso:
    python3 scripts/build.py RUTA_AL_ZIP_O_CARPETA [--out public]

- Lee las 17 páginas HTML originales y las convierte a un contenido limpio (sin <font>, sin JS viejo).
- Recorta los bordes blancos de las capturas y las exporta a .webp + .jpg.
- Genera public/ listo para servir en Vercel (sin build step en Vercel).
"""
import argparse, glob, html, os, re, shutil, sys, tempfile, zipfile, warnings
from bs4 import BeautifulSoup, NavigableString, XMLParsedAsHTMLWarning
from PIL import Image
import numpy as np

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

SITE_TITLE = "Calidad: Seis Sigma"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------- capítulos ----------
CHAPTERS = [
    ("0_cmo_utilizar_esta_gua.html", "00-como-utilizar-esta-guia", "0", "¿Cómo utilizar esta Guía?"),
    ("1_introduccin.html", "01-introduccion", "1", "Introducción"),
    ("2_diagrama_de_procesos.html", "02-diagrama-de-procesos", "2", "Diagrama de procesos"),
    ("3_minitab.html", "03-minitab", "3", "Minitab"),
    ("4_r__r.html", "04-r-and-r", "4", "R & R"),
    ("5_probabilidad.html", "05-probabilidad", "5", "Probabilidad"),
    ("6_estadstica_bsica.html", "06-estadistica-basica", "6", "Estadística básica"),
    ("7_capacidad_de_proceso.html", "07-capacidad-de-proceso", "7", "Capacidad de proceso"),
    ("8_intervalos_de_confianza.html", "08-intervalos-de-confianza", "8", "Intervalos de confianza"),
    ("9_contraste_de_hiptesis.html", "09-contraste-de-hipotesis", "9", "Contraste de hipótesis"),
    ("10_anlisis_grfico.html", "10-analisis-grafico", "10", "Análisis gráfico"),
    ("11_regresin.html", "11-regresion", "11", "Regresión"),
    ("12_anova.html", "12-anova", "12", "ANOVA"),
    ("13_doe_1_parte.html", "13-doe-1-parte", "13", "DoE · 1ª parte"),
    ("14_doe_2_parte.html", "14-doe-2-parte", "14", "DoE · 2ª parte"),
    ("15_control.html", "15-control", "15", "Control"),
]
FILE2SLUG = {c[0]: c[1] for c in CHAPTERS}
FILE2SLUG["index.html"] = ""
FILE2SLUG["fdl.html"] = "licencia"

# ---------- iconos (trazo, 24x24) ----------
ICONS = {
    "objectives": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.2"/>',
    "preknowledge": '<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z"/>',
    "reading": '<path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5z"/><path d="M4 5.5v16"/><path d="M9 8h7"/>',
    "casestudy": '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"/><path d="M3 13h18"/>',
    "question": '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.6 2.2c-.7.4-1.1 1-1.1 1.8"/><path d="M12 17h.01"/>',
    "reflection": '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/><path d="M8.5 11h7M8.5 14h4"/>',
    "activity": '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18v3h3l6.3-6.3a4 4 0 0 0 5.4-5.4l-2.6 2.6-2.4-.6-.6-2.4z"/>',
}
def icon(name):
    return f'<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>'

DEVICE_KIND = {
    "objectivesIdevice": ("objectives", "Objetivos"),
    "preknowledgeIdevice": ("preknowledge", "Conocimientos previos"),
    "readingIdevice": ("reading", "Actividad de lectura"),
    "CasestudyIdevice": ("casestudy", "Caso de estudio"),
    "MultichoiceIdevice": ("question", "Pon a prueba lo aprendido"),
    "ReflectionIdevice": ("reflection", "Reflexión final"),
    "activityIdevice": ("activity", "Actividad"),
}

# ---------- imágenes ----------
def crop_white(im, thr=245):
    a = np.array(im.convert("RGB"))
    mask = (a < thr).any(axis=2)
    rows = np.where(mask.sum(axis=1) >= 2)[0]
    cols = np.where(mask.sum(axis=0) >= 2)[0]
    if len(rows) == 0 or len(cols) == 0:
        return im
    return im.crop((cols[0], rows[0], cols[-1] + 1, rows[-1] + 1))

IMG_INFO = {}  # nombre original (lower) -> (slug, w, h)

def process_images(src, out_img):
    os.makedirs(out_img, exist_ok=True)
    for f in sorted(glob.glob(os.path.join(src, "*"))):
        n = os.path.basename(f)
        if not n.lower().endswith((".jpg", ".jpeg")) or n.lower() == "top_nav.jpg":
            continue
        im = crop_white(Image.open(f).convert("RGB"))
        slug = os.path.splitext(n)[0].lower().replace("_", "-")
        im.save(os.path.join(out_img, slug + ".jpg"), quality=88, optimize=True, progressive=True)
        im.save(os.path.join(out_img, slug + ".webp"), quality=86, method=6)
        IMG_INFO[n.lower()] = (slug, im.width, im.height)

# ---------- limpieza HTML ----------
def clean_fragment(soup, node):
    """Limpia un nodo: quita <font>, align, style, ids viejos, etc."""
    for t in node.find_all("font"):
        t.unwrap()
    for t in node.find_all(True):
        for attr in ("align", "style", "onmousedown", "onmouseover", "onclick", "valign", "border",
                     "cellpadding", "cellspacing", "bgcolor", "width", "height", "face", "size"):
            if t.name != "img" and attr in t.attrs:
                del t.attrs[attr]
        if t.name == "div" and t.get("class") == ["block"]:
            t.attrs.pop("class", None)
        t.attrs.pop("id", None) if t.name in ("div", "p") and str(t.get("id", "")).startswith(("ta", "taf", "taans")) else None
    # imágenes
    for img in node.find_all("img"):
        src = (img.get("src") or "").strip()
        key = os.path.basename(src).lower()
        if key in IMG_INFO:
            slug, w, h = IMG_INFO[key]
            alt = img.get("alt") or ""
            pic = soup.new_tag("picture")
            s = soup.new_tag("source", srcset=f"/img/{slug}.webp", type="image/webp")
            im = soup.new_tag("img", src=f"/img/{slug}.jpg", width=str(w), height=str(h), loading="lazy", decoding="async", alt=alt)
            pic.append(s); pic.append(im)
            fig = soup.new_tag("figure", **{"class": "captura"})
            fig.append(pic)
            img.replace_with(fig)
        else:
            img.decompose()
    # figure dentro de p -> sacar
    for fig in node.find_all("figure"):
        p = fig.find_parent("p")
        if p is not None:
            p.insert_before(fig.extract())
            if not p.get_text(strip=True) and not p.find("figure"):
                p.decompose()
    # enlaces internos
    for a in node.find_all("a", href=True):
        h = a["href"]
        base = os.path.basename(h.split("#")[0])
        if base in FILE2SLUG:
            a["href"] = "/" + FILE2SLUG[base] if FILE2SLUG[base] else "/"
        elif h.startswith("http"):
            a["target"] = "_blank"; a["rel"] = "noopener"
    # limpieza de basura
    for t in node.find_all(["br"]):
        pass
    for p in node.find_all("p"):
        if not p.get_text(strip=True) and not p.find(["img", "figure", "picture"]):
            p.decompose()
    for d in node.find_all("div"):
        if not d.get_text(strip=True) and not d.find(["img", "figure", "picture", "table"]):
            d.decompose()
    return node

def inner_html(node):
    return "".join(str(c) for c in node.children).replace("\r", "").replace("\xa0", " ").strip()

def get_blocks(idev_inner):
    """Devuelve los bloques de texto (div.block) directos de un iDevice."""
    return idev_inner.find_all("div", class_="block", recursive=False)

# ---------- construcción de componentes ----------
def card(kind, title, body_html, extra_cls=""):
    return (f'<section class="card card--{kind} {extra_cls}">'
            f'<header class="card__head"><span class="card__icon">{icon(kind)}</span>'
            f'<h2 class="card__title">{html.escape(title)}</h2></header>'
            f'<div class="card__body prose">{body_html}</div></section>')

FB_OK = re.compile(r"^[¡¿\s]*(EXACTO|CORRECTO|OK\b|JUSTO)", re.I)
FB_BAD = re.compile(r"^[¡¿\s]*(NO\b|ERROR|INCORRECTO|INCOMPLETO|NUNCA|REVISE|DEFINITIVAMENTE)", re.I)

def build_multichoice(soup, inner, qcount):
    """Convierte las preguntas tipo test del iDevice en HTML accesible."""
    out = []
    children = [c for c in inner.children if getattr(c, "name", None)]
    groups, cur = [], None
    for c in children:
        cid = c.get("id", "") or ""
        if c.name == "div" and cid.startswith("taquestion"):
            cur = {"q": c, "hint": None, "table": None, "fb": []}
            groups.append(cur)
        elif cur is not None:
            if c.name == "div" and cid.startswith("hint"):
                cur["hint"] = c
            elif c.name == "table":
                cur["table"] = c
            elif c.name == "div" and re.match(r"sa\d+b", cid):
                cur["fb"].append(c)
    for g in groups:
        qcount[0] += 1
        n = qcount[0]
        q = clean_fragment(soup, g["q"])
        parts = [f'<div class="quiz" data-quiz="{n}"><div class="quiz__q prose">{inner_html(q)}</div>']
        if g["hint"] is not None:
            for x in g["hint"].find_all("div", class_="popupDivLabel"):
                x.decompose()
            for x in g["hint"].find_all("img"):
                x.decompose() if "stock-stop" in (x.get("src") or "") else None
            hint = clean_fragment(soup, g["hint"])
            parts.append(f'<details class="reveal"><summary>Ver sugerencia</summary><div class="prose">{inner_html(hint)}</div></details>')
        if g["table"] is not None:
            rows = g["table"].find_all("tr")
            parts.append('<div class="quiz__opts" role="radiogroup">')
            for i, r in enumerate(rows):
                tds = r.find_all("td")
                txt = clean_fragment(soup, tds[-1]) if tds else None
                fb = g["fb"][i] if i < len(g["fb"]) else None
                fbtxt = fb.get_text(" ", strip=True) if fb is not None else ""
                state = "ok" if FB_OK.match(fbtxt) else ("bad" if FB_BAD.match(fbtxt) else "info")
                fbh = inner_html(clean_fragment(soup, fb)) if fb is not None else ""
                parts.append(
                    f'<label class="opt"><input type="radio" name="q{n}" value="{i}" data-state="{state}">'
                    f'<span class="opt__mark"></span><span class="opt__text prose">{inner_html(txt) if txt else ""}</span></label>'
                    f'<div class="opt__fb opt__fb--{state}" hidden data-for="q{n}-{i}"><div class="prose">{fbh}</div></div>'
                )
            parts.append("</div>")
        parts.append("</div>")
        out.append("".join(parts))
    return "".join(out)

def build_reflection_like(soup, inner):
    blocks = get_blocks(inner)
    main = "".join(inner_html(clean_fragment(soup, b)) for b in blocks[:1])
    hidden = ""
    fb = inner.find("div", class_="feedback")
    if fb is not None:
        hidden = inner_html(clean_fragment(soup, fb))
    body = main
    if hidden:
        body += f'<details class="reveal"><summary>Ver respuesta</summary><div class="prose">{hidden}</div></details>'
    return body

def build_device(soup, dev, qcount):
    cls = [c for c in dev.get("class", []) if c.endswith("Idevice")]
    if not cls:
        return ""
    cls = cls[0]
    inner = dev.find("div", class_="iDevice_inner")
    if cls == "FreeTextIdevice":
        inner_div = dev.find("div", class_="iDevice") or dev
        blocks = inner_div.find_all("div", class_="block", recursive=False)
        body = "".join(inner_html(clean_fragment(soup, b)) for b in blocks)
        if not BeautifulSoup(body, "lxml").get_text(strip=True) and "<figure" not in body:
            return ""
        return f'<section class="lead prose">{body}</section>'
    kind, default_title = DEVICE_KIND.get(cls, ("activity", "Actividad"))
    title_el = dev.find("span", class_="iDeviceTitle")
    title = title_el.get_text(strip=True) if title_el else default_title
    if cls == "MultichoiceIdevice":
        body = build_multichoice(soup, inner, qcount)
        return card(kind, "Pon a prueba lo aprendido" if title.lower().startswith(("pregunta", "test")) else title, body)
    if cls in ("ReflectionIdevice", "CasestudyIdevice"):
        return card(kind, title, build_reflection_like(soup, inner))
    blocks = get_blocks(inner) if inner else []
    body = "".join(inner_html(clean_fragment(soup, b)) for b in blocks)
    return card(kind, title, body)

# ---------- plantilla ----------
def sidebar(active_slug):
    items = ['<a class="nav__home%s" href="/">Inicio</a>' % (" is-active" if active_slug == "" else "")]
    for _, slug, num, name in CHAPTERS:
        cur = ' is-active" aria-current="page' if slug == active_slug else ""
        items.append(f'<a class="nav__item{cur}" href="/{slug}"><span class="nav__num">{num}</span><span>{html.escape(name)}</span></a>')
    return "\n".join(items)

def page(title, slug, body, desc="", prev=None, nxt=None, chapter=None):
    pager = ""
    if prev or nxt:
        pager = '<nav class="pager" aria-label="Paginación de capítulos">'
        if prev:
            pager += f'<a class="pager__a pager__a--prev" href="/{prev[0]}"><small>Anterior</small><strong>{html.escape(prev[1])}</strong></a>'
        else:
            pager += "<span></span>"
        if nxt:
            pager += f'<a class="pager__a pager__a--next" href="/{nxt[0]}"><small>Siguiente</small><strong>{html.escape(nxt[1])}</strong></a>'
        pager += "</nav>"
    head_title = f"{title} · {SITE_TITLE}" if slug else f"{SITE_TITLE} · Guía de estudio"
    kicker = f'<p class="kicker">Capítulo {chapter}</p>' if chapter is not None else ""
    h1 = f'<h1 class="page-title">{html.escape(title)}</h1>' if slug else ""
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(head_title)}</title>
<meta name="description" content="{html.escape(desc or 'Guía de estudio de la metodología Seis Sigma: estadística, Minitab, capacidad de proceso, ANOVA, DoE y control.')}">
<meta name="theme-color" content="#0f172a">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700;12..96,800&family=Figtree:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/styles.css">
<script>document.documentElement.dataset.theme=localStorage.getItem('theme')||'';</script>
</head>
<body>
<a class="skip" href="#contenido">Saltar al contenido</a>
<header class="topbar">
  <button class="topbar__btn" id="menuBtn" aria-label="Abrir menú" aria-expanded="false" aria-controls="sidebar">
    <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
  </button>
  <a class="topbar__brand" href="/">Seis <b>Sigma</b></a>
  <button class="topbar__btn" id="themeBtn" aria-label="Cambiar tema">
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
  </button>
</header>
<div class="scrim" id="scrim" hidden></div>
<aside class="sidebar" id="sidebar" aria-label="Índice de la guía">
  <a class="sidebar__brand" href="/"><span class="sidebar__logo">σ</span><span>Calidad<br><b>Seis Sigma</b></span></a>
  <nav class="nav">
{sidebar(slug)}
  </nav>
</aside>
<main class="main" id="contenido">
  <div class="progress" aria-hidden="true"><span id="progressBar"></span></div>
  <article class="article">
    {kicker}
    {h1}
    {body}
    {pager}
  </article>
  <footer class="footer">
    <span>Material docente original licenciado bajo <a href="/licencia">GNU FDL 1.2</a>. Versión web modernizada.</span>
  </footer>
</main>
<script src="/js/app.js" defer></script>
</body>
</html>
"""

def build_home():
    cards = []
    for _, slug, num, name in CHAPTERS:
        cards.append(f'<a class="tile" href="/{slug}"><span class="tile__num">{num}</span><span class="tile__name">{html.escape(name)}</span>'
                     f'<svg class="tile__arrow" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a>')
    body = f"""
<section class="hero">
  <p class="hero__eyebrow">Guía de estudio</p>
  <h1 class="hero__title">Metodología <span>Seis Sigma</span></h1>
  <p class="hero__lead">Estadística aplicada a la mejora de procesos con Minitab: desde el diagrama de procesos hasta el control, pasando por capacidad, ANOVA y diseño de experimentos.</p>
  <div class="hero__cta">
    <a class="btn btn--primary" href="/00-como-utilizar-esta-guia">Empezar por el capítulo 0</a>
    <a class="btn" href="/01-introduccion">Ir a la introducción</a>
  </div>
</section>
<section aria-labelledby="idx"><h2 id="idx" class="section-title">Contenido</h2><div class="tiles">{''.join(cards)}</div></section>
"""
    return page(SITE_TITLE, "", body, nxt=None)

def build_license(src):
    raw = open(os.path.join(src, "fdl.html"), encoding="utf-8", errors="replace").read()
    s = BeautifulSoup(raw, "lxml")
    body = s.body
    for t in body.find_all(["script", "style"]):
        t.decompose()
    for t in body.find_all(True):
        for a in ("style", "class", "id", "align"):
            t.attrs.pop(a, None)
    html_body = "".join(str(c) for c in body.children)
    html_body = html_body.replace("<h2>GNU Free Documentation License</h2>", "", 1)
    return page("Licencia de documentación libre GNU (FDL 1.2)", "licencia",
                f'<div class="prose prose--license">{html_body}</div>')

def build_chapter(src, idx, out):
    fname, slug, num, name = CHAPTERS[idx]
    raw = open(os.path.join(src, fname), encoding="utf-8", errors="replace").read()
    s = BeautifulSoup(raw, "lxml")
    main = s.find("div", id="main")
    qcount = [0]
    parts = []
    for dev in main.find_all("div", recursive=False):
        cls = dev.get("class") or []
        if any(c.endswith("Idevice") for c in cls):
            parts.append(build_device(s, dev, qcount))
    body = "".join(p for p in parts if p)
    prev = (CHAPTERS[idx - 1][1], f"{CHAPTERS[idx-1][2]}. {CHAPTERS[idx-1][3]}") if idx > 0 else None
    nxt = (CHAPTERS[idx + 1][1], f"{CHAPTERS[idx+1][2]}. {CHAPTERS[idx+1][3]}") if idx < len(CHAPTERS) - 1 else None
    title = name
    with open(os.path.join(out, slug + ".html"), "w", encoding="utf-8") as f:
        f.write(page(title, slug, body, prev=prev, nxt=nxt, chapter=num))

# ---------- main ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="ZIP del export eXeLearning o carpeta ya descomprimida")
    ap.add_argument("--out", default=os.path.join(ROOT, "public"))
    args = ap.parse_args()

    src = args.source
    tmp = None
    if os.path.isfile(src) and src.lower().endswith(".zip"):
        tmp = tempfile.mkdtemp()
        with zipfile.ZipFile(src) as z:
            z.extractall(tmp)
        # por si el zip trae una carpeta raíz
        entries = os.listdir(tmp)
        if "index.html" not in entries and len(entries) == 1 and os.path.isdir(os.path.join(tmp, entries[0])):
            tmp = os.path.join(tmp, entries[0])
        src = tmp
    if not os.path.exists(os.path.join(src, "index.html")):
        sys.exit("No encuentro index.html en el origen: ¿es el export correcto?")

    out = args.out
    os.makedirs(out, exist_ok=True)
    process_images(src, os.path.join(out, "img"))
    for i in range(len(CHAPTERS)):
        build_chapter(src, i, out)
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as f:
        f.write(build_home())
    with open(os.path.join(out, "licencia.html"), "w", encoding="utf-8") as f:
        f.write(build_license(src))
    print(f"OK -> {out}  ({len(CHAPTERS)} capítulos, {len(IMG_INFO)} imágenes)")
    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    main()
