#!/usr/bin/env python3
"""
Comprueba overflow horizontal / elementos cortados en 1920, 1024, 768, 480 y 375 px.

    pip install playwright && playwright install chromium
    python3 scripts/check.py public [--shots capturas]

Sale con código 1 si alguna página tiene overflow. Muestra los elementos culpables
para poder añadir la regla concreta en responsive.css.
"""
import argparse, glob, os, sys
from playwright.sync_api import sync_playwright

WIDTHS = [1920, 1024, 768, 480, 375]

JS = """() => {
  const vw = document.documentElement.clientWidth;
  const scrollableAncestor = el => {
    for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) {
      const o = getComputedStyle(p).overflowX;
      if ((o === 'auto' || o === 'scroll') && p.scrollWidth > p.clientWidth) return true;
    }
    return false;
  };
  const off = [];
  for (const el of document.body.querySelectorAll('*')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    if (r.right > vw + 1 || r.left < -1) {
      if (scrollableAncestor(el)) continue;
      off.push(el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') +
               (el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\\s+/).join('.') : '') +
               ' [left=' + Math.round(r.left) + ', right=' + Math.round(r.right) + ']');
    }
  }
  return { vw, sw: document.documentElement.scrollWidth, off: off.slice(0, 10), total: off.length };
}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--shots", help="carpeta donde guardar capturas full-page")
    a = ap.parse_args()

    pages = sorted(glob.glob(os.path.join(a.folder, "*.html")))
    if not pages:
        sys.exit("No hay .html en la carpeta")
    if a.shots:
        os.makedirs(a.shots, exist_ok=True)

    bad = 0
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        for w in WIDTHS:
            ctx = br.new_context(viewport={"width": w, "height": 900})
            pg = ctx.new_page()
            for p in pages:
                pg.goto("file://" + os.path.abspath(p))
                pg.wait_for_load_state("load")
                r = pg.evaluate(JS)
                ok = r["sw"] <= r["vw"] and r["total"] == 0
                if not ok:
                    bad += 1
                    print(f"[FALLO {w}px] {os.path.basename(p)}  scrollWidth={r['sw']} > {r['vw']}  elementos fuera={r['total']}")
                    for o in r["off"]:
                        print("      ", o)
                if a.shots:
                    pg.screenshot(path=os.path.join(a.shots, f"{os.path.splitext(os.path.basename(p))[0]}_{w}.png"), full_page=True)
            ctx.close()
        br.close()
    if not bad:
        print("TODO OK: sin overflow en", WIDTHS)
    if bad:
        print(f"{bad} combinaciones página/ancho con problemas")
        sys.exit(1)


if __name__ == "__main__":
    main()