# Проверки секретов

Gitleaks CLI 8.30.1 доступен. Перед первым коммитом `gitleaks git --staged --redact .` выполнен после git add и повторён после правки evidence/индекса: отдельный вызов exit 0, no leaks found. Собственный коммит fb345a3 проверен `gitleaks git --redact --log-opts="origin/main..HEAD" .`: отдельный вызов exit 0, 1 commit scanned, no leaks found. Проверен только собственный диапазон по заданию; чужая старая история не изменялась. Перед каждым дальнейшим коммитом и push применяются те же две обязательные проверки, код возврата проверяется напрямую, без pipe/tail и без отключения сканера.

`git diff --cached --check` после удаления trailing whitespace в evidence/pdfinfo.txt — exit 0. Все добавленные пути только submissions/Vrnur/SA06/. Утечек не найдено; это не заменяет независимую проверку кода.
