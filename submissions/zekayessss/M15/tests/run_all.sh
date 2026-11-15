#!/bin/sh
# Прогон всех проверок для папки сайта (по умолчанию — исправленная result/site).
# Пример «до»:    sh tests/run_all.sh ../../../materials/M15/input/site
# Пример «после»: sh tests/run_all.sh
cd "$(dirname "$0")/.." || exit 2
SITE="${1:-result/site}"
PY="${PYTHON:-python3}"
status=0
echo "== JS: калькулятор /shop (app.js) =="
node tests/test_shop.js "$SITE" || status=1
echo
echo "== Python: страницы стенда (serve.py) =="
out=$("$PY" tests/test_server.py "$SITE" 2>&1) || status=1
# Абсолютные пути в traceback заменяются относительными, чтобы вывод не зависел от машины.
printf '%s\n' "$out" | sed "s|$(pwd)/||g"
echo
echo "ОБЩИЙ КОД ВЫХОДА: $status"
exit $status
