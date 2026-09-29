#!/usr/bin/env python3
"""
Convierte el export eXeLearning "Guia_Calidad_Seis_Sigma" en una web responsive.
Mantiene el HTML y diseño original, arreglando la superposición de cajas y agregando
un menú colapsable (acordeón/dropdown) en móvil para evitar que ocupe demasiado espacio.

Uso:
    python3 scripts/build.py RUTA_AL_ZIP_O_CARPETA [--out public]
"""

import argparse
import glob
import os
import shutil
import sys
import tempfile
import warnings
import zipfile
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from PIL import Image
import numpy as np

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# CSS Responsive con forzado estricto de colapso en menú móvil
RESPONSIVE_CSS = """
/* ANULACIÓN FORZOSA DE POSICIONAMIENTOS ABSOLUTOS Y SOLAPAMIENTOS DE EXELEARNING */
html, body, #nodeDecoration, #header, #emptyHeader, #siteFooter, #footer,
#siteNav, #main, #content, #wrapper, #outer, .iDevice, #nav, #navcontainer,
div[id*="nav"], div[id*="site"], div[id*="main"], div[id*="content"] {
    position: relative !important;
    float: none !important;
    clear: both !important;
    top: auto !important;
    bottom: auto !important;
    left: auto !important;
    right: auto !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
    padding-left: 0 !important;
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
}

html, body {
    margin: 0 !important;
    padding: 0 !important;
    overflow-x: hidden !important;
    background-color: #f5f7f9 !important;
    font-family: system-ui, -apple-system, sans-serif !important;
}

/* CONTENEDOR PRINCIPAL FLEXIBLE */
#content, #wrapper, #container {
    display: flex !important;
    flex-direction: column !important;
    max-width: 1200px !important;
    margin: 0 auto !important;
    padding: 15px !important;
    gap: 20px !important;
}

/* LIMPIEZA Y ESTILIZADO DE LAS CAJAS DE CONTENIDO (IDEVICES) */
.iDevice, div[class*="iDevice"], .iDevice_wrapper, article.iDevice {
    margin-top: 20px !important;
    margin-bottom: 20px !important;
    padding: 20px !important;
    background-color: #ffffff !important;
    background-image: none !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04) !important;
    clear: both !important;
    display: block !important;
}

/* REMOVER BARRAS GRISES Y DECORACIONES DE CABECERA */
.iDevice_header, header.iDevice_header, .iDeviceTitle, div[class*="header"] {
    background: transparent !important;
    background-image: none !important;
    border: none !important;
    padding: 0 0 10px 0 !important;
    margin: 0 0 15px 0 !important;
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    border-bottom: 2px solid #84a929 !important;
}

/* CONTENIDO INTERNO DE LAS CAJAS */
.iDevice_inner, .iDevice_content, .iDevice_wrapper .block, div[class*="content"] {
    background: #ffffff !important;
    background-color: #ffffff !important;
    border: none !important;
    padding: 0 !important;
    margin: 0 !important;
}

/* --- ESTILOS DE NAVEGACIÓN (MENÚ) --- */
#siteNav, #nav, #navcontainer {
    display: block !important;
    width: 100% !important;
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    padding: 10px !important;
    margin-bottom: 15px !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04) !important;
}

/* Botón desplegable */
.mobile-menu-toggle {
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    width: 100% !important;
    background: #84a929 !important;
    color: #ffffff !important;
    border: none !important;
    padding: 12px 15px !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
    cursor: pointer !important;
    text-align: left !important;
    box-sizing: border-box !important;
}

.mobile-menu-toggle::after {
    content: "▼" !important;
    font-size: 0.8rem !important;
    transition: transform 0.2s ease !important;
}

.mobile-menu-toggle.active::after {
    transform: rotate(180deg) !important;
}

/* Ocultamiento estricto en móvil (< 850px) */
@media (max-width: 849px) {
    /* Ocultar cualquier ul, ol o nav interno en móvil por defecto */
    #siteNav ul, #siteNav ol, #nav ul, #nav ol, #navcontainer ul {
        display: none !important;
        list-style: none !important;
        padding: 10px 0 0 0 !important;
        margin: 0 !important;
    }

    /* Mostrar solo cuando tenga la clase .menu-expanded */
    #siteNav ul.menu-expanded, #siteNav ol.menu-expanded,
    #nav ul.menu-expanded, #nav ol.menu-expanded,
    #navcontainer ul.menu-expanded {
        display: block !important;
    }
}

#siteNav li, #nav li {
    margin-bottom: 4px !important;
}

#siteNav a, #nav a {
    display: block !important;
    padding: 8px 12px !important;
    text-decoration: none !important;
    color: #333333 !important;
    border-radius: 4px !important;
    word-break: break-word !important;
    font-size: 0.95rem !important;
}

#siteNav a:hover, #nav a:hover {
    background-color: #f1f5f9 !important;
    color: #84a929 !important;
}

/* ÁREA DE CONTENIDO PRINCIPAL */
#main {
    flex: 1 !important;
    min-width: 0 !important;
    background: transparent !important;
    padding: 0 !important;
}

/* ESCRITORIO (850px o más) */
@media (min-width: 850px) {
    #content, #wrapper, #container {
        flex-direction: row !important;
        align-items: flex-start !important;
    }

    .mobile-menu-toggle {
        display: none !important;
    }

    #siteNav, #nav, #navcontainer {
        width: 280px !important;
        flex-shrink: 0 !important;
        position: sticky !important;
        top: 20px !important;
        max-height: calc(100vh - 40px) !important;
        overflow-y: auto !important;
        margin-bottom: 0 !important;
    }

    #siteNav ul, #siteNav ol, #nav ul, #nav ol, #navcontainer ul {
        display: block !important;
        list-style: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
}

img, picture, svg, video, iframe {
    max-width: 100% !important;
    height: auto !important;
}

table {
    display: block !important;
    overflow-x: auto !important;
    max-width: 100% !important;
}
"""

# JS robusto para alternar el menú desplegable en móvil
TOGGLE_JS = """
document.addEventListener("DOMContentLoaded", function() {
    var nav = document.querySelector("#siteNav, #nav, #navcontainer");
    if (!nav) return;

    // Buscar lista dentro del menú
    var list = nav.querySelector("ul, ol");
    if (!list) return;

    // Crear botón si no existe
    if (!nav.querySelector(".mobile-menu-toggle")) {
        var btn = document.createElement("button");
        btn.className = "mobile-menu-toggle";
        btn.type = "button";
        btn.innerHTML = "<span>☰ Índice del Módulo</span>";

        btn.addEventListener("click", function(e) {
            e.preventDefault();
            btn.classList.toggle("active");
            list.classList.toggle("menu-expanded");
        });

        nav.insertBefore(btn, nav.firstChild);
    }
});
"""

IMG_INFO = {}


def crop_white(im, thr=245):
    a = np.array(im.convert("RGB"))
    mask = (a < thr).any(axis=2)
    rows = np.where(mask.sum(axis=1) >= 2)[0]
    cols = np.where(mask.sum(axis=0) >= 2)[0]
    if len(rows) == 0 or len(cols) == 0:
        return im
    return im.crop((cols[0], rows[0], cols[-1] + 1, rows[-1] + 1))


def process_images(src, out_img):
    os.makedirs(out_img, exist_ok=True)
    for f in sorted(glob.glob(os.path.join(src, "*"))):
        n = os.path.basename(f)
        if not n.lower().endswith((".jpg", ".jpeg", ".png")) or n.lower() == "top_nav.jpg":
            continue
        try:
            im = crop_white(Image.open(f).convert("RGB"))
            slug = os.path.splitext(n)[0].lower().replace("_", "-")
            im.save(os.path.join(out_img, slug + ".jpg"), quality=88, optimize=True, progressive=True)
            im.save(os.path.join(out_img, slug + ".webp"), quality=86, method=6)
            IMG_INFO[n.lower()] = (slug, im.width, im.height)
        except Exception as e:
            print(f"Error procesando imagen {n}: {e}")


def process_html_file(file_path, out_dir):
    filename = os.path.basename(file_path)
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        soup = BeautifulSoup(f.read(), "lxml")

    head = soup.find("head")
    if not head:
        head = soup.new_tag("head")
        if soup.html:
            soup.html.insert(0, head)

    # 1. Ajustar Viewport
    viewport = head.find("meta", attrs={"name": "viewport"})
    if viewport:
        viewport["content"] = "width=device-width, initial-scale=1.0"
    else:
        viewport = soup.new_tag("meta", attrs={"name": "viewport", "content": "width=device-width, initial-scale=1.0"})
        head.append(viewport)

    # 2. Insertar estilos CSS
    style_tag = soup.new_tag("style", type="text/css")
    style_tag.string = RESPONSIVE_CSS
    head.append(style_tag)

    # 3. Insertar script JS
    script_tag = soup.new_tag("script", type="text/javascript")
    script_tag.string = TOGGLE_JS
    if soup.body:
        soup.body.append(script_tag)
    else:
        head.append(script_tag)

    # 4. Sustituir imágenes por responsive (<picture>)
    for img in soup.find_all("img"):
        src = (img.get("src") or "").strip()
        key = os.path.basename(src).lower()
        if key in IMG_INFO:
            slug, w, h = IMG_INFO[key]
            alt = img.get("alt") or ""

            pic = soup.new_tag("picture")
            s = soup.new_tag("source", srcset=f"img/{slug}.webp", type="image/webp")
            im = soup.new_tag("img", src=f"img/{slug}.jpg", width=str(w), height=str(h), loading="lazy",
                              decoding="async", alt=alt)

            pic.append(s)
            pic.append(im)
            img.replace_with(pic)

    out_path = os.path.join(out_dir, filename)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(str(soup))


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
        entries = os.listdir(tmp)
        if "index.html" not in entries and len(entries) == 1 and os.path.isdir(os.path.join(tmp, entries[0])):
            tmp = os.path.join(tmp, entries[0])
        src = tmp

    if not os.path.exists(os.path.join(src, "index.html")):
        sys.exit("No encuentro index.html en el origen.")

    out = args.out
    os.makedirs(out, exist_ok=True)

    # Copiar recursos
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(out, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        elif not item.lower().endswith((".html", ".htm")):
            shutil.copy2(s, d)

    process_images(src, os.path.join(out, "img"))

    html_files = glob.glob(os.path.join(src, "*.html")) + glob.glob(os.path.join(src, "*.htm"))
    for html_file in html_files:
        process_html_file(html_file, out)

    print(f"OK -> {out} ({len(html_files)} páginas procesadas, {len(IMG_INFO)} imágenes convertidas)")

    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()