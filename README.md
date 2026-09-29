# Guía de Calidad: Seis Sigma

Web estática (HTML + CSS + JS, sin frameworks) generada desde el export original de eXeLearning.

## Estructura

```
public/            ← lo que se despliega (ya generado, se sube al repo)
  index.html, 00-…15-….html, licencia.html
  css/styles.css, js/app.js, img/ (webp + jpg recortadas), favicon.svg
scripts/build.py   ← regenera public/ desde el zip original
vercel.json
```

## Regenerar el contenido (solo si cambia el zip)

```bash
pip install -r requirements.txt
python3 scripts/build.py Guia_Calidad_Seis_Sigma.zip
```

## Vercel

Framework Preset: **Other** · Build Command: vacío · Output Directory: `public` (ya está en `vercel.json`).
