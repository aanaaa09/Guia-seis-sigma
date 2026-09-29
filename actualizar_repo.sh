#!/usr/bin/env bash
# Uso: ./actualizar_repo.sh /ruta/a/tu/clon/de/seis-sigma [rama]
# Sustituye el contenido del repo por la web nueva y deja el commit hecho (sin push).
set -euo pipefail
DEST="${1:?Pasa la ruta del repo clonado (git clone https://github.com/aanaaa09/seis-sigma)}"
BRANCH="${2:-master}"
SRC="$(cd "$(dirname "$0")" && pwd)"

[ -d "$DEST/.git" ] || { echo "❌ $DEST no es un repo git"; exit 1; }
cd "$DEST"
git checkout "$BRANCH"
git pull --ff-only || true

echo "→ Borrando lo antiguo (se conserva .git)…"
find . -mindepth 1 -maxdepth 1 ! -name '.git' -exec rm -rf {} +

echo "→ Copiando la web nueva…"
cp -R "$SRC/public" "$SRC/scripts" "$SRC/vercel.json" "$SRC/requirements.txt" "$SRC/README.md" "$SRC/.gitignore" .

git add -A
git commit -m "Rehacer web: estructura limpia, responsive, imágenes recortadas y despliegue en Vercel"
echo "✅ Listo. Revisa con 'git show --stat' y sube con: git push origin $BRANCH"
echo "   (si quieres el patch: git format-patch -1)"
