#!/usr/bin/env bash
set -euo pipefail

cd "$HOME/project/blog"
export DJANGO_SETTINGS_MODULE=mysite.settings.production
PREV=$(git rev-parse HEAD)
VENV_SWAPPED=0
BACKUP="$HOME/backups/pre-deploy-$(date +%Y%m%d%H%M%S).sqlite3"

rollback() {
    trap - ERR
    # Attempt every recovery step even if another recovery step fails.
    set +e
    echo "Deployment failed; restoring $PREV and $BACKUP" >&2
    sudo systemctl stop blog blog-worker
    git reset --hard "$PREV"
    if [ "$VENV_SWAPPED" = 1 ]; then
        rm -rf venv
        mv venv.prev venv
    else
        "$HOME/.local/bin/uv" pip install -q -r requirements.txt --python venv/bin/python
    fi
    sqlite3 db.sqlite3 ".restore '$BACKUP'"
    venv/bin/python manage.py collectstatic --noinput
    sudo systemctl restart blog blog-worker
    exit 1
}

git fetch origin main
mkdir -p "$HOME/backups"
# sqlite's online backup is consistent while the site keeps serving.
sqlite3 db.sqlite3 ".backup '$BACKUP'"
trap rollback ERR
# Keep the ten newest snapshots, including this one.
find "$HOME/backups" -maxdepth 1 -type f -name 'pre-deploy-*.sqlite3' |
    sort -r | tail -n +11 | while IFS= read -r old; do rm "$old"; done

git reset --hard origin/main
TARGET_PYTHON=$(cat .python-version)
CURRENT_PYTHON=$(venv/bin/python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [ "$CURRENT_PYTHON" != "$TARGET_PYTHON" ]; then
    rm -rf venv.new
    UV_VENV_RELOCATABLE=1 "$HOME/.local/bin/uv" venv --python "$TARGET_PYTHON" venv.new
    "$HOME/.local/bin/uv" pip install -q -r requirements.txt --python venv.new/bin/python
    rm -rf venv.prev
    mv venv venv.prev
    VENV_SWAPPED=1
    mv venv.new venv
else
    "$HOME/.local/bin/uv" pip install -q -r requirements.txt --python venv/bin/python
fi
sudo systemctl stop blog blog-worker
venv/bin/python manage.py migrate --noinput
venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart blog blog-worker
sleep 5
systemctl is-active --quiet blog
systemctl is-active --quiet blog-worker
curl --fail --silent --show-error --retry 3 --retry-connrefused --max-time 15 \
    -H 'Host: aaron404.com' -H 'X-Forwarded-Proto: https' http://127.0.0.1:8000/healthz | grep -qx ok
# Resolve an existing default-locale article, not a hard-coded slug that can move.
ARTICLE=$(venv/bin/python manage.py shell -c \
    'from seo.views import posts; from urllib.parse import urlsplit; print(urlsplit(posts()[0].full_url).path)' | tail -n 1)
curl --fail --silent --show-error --max-time 30 -o /dev/null \
    -H 'Host: aaron404.com' -H 'X-Forwarded-Proto: https' "http://127.0.0.1:8000$ARTICLE"
trap - ERR
echo "deployed $(git log -1 --format='%h %s')"
