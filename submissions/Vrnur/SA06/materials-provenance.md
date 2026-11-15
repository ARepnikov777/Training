# Материалы

Данные и изображения: `source/H11/input/`; происхождение и условия: `provenance.md` и `LICENSE.md` в этом каталоге (синтетические изображения, CC0 1.0).

Шрифты DejaVu Sans и DejaVu Sans Bold взяты из LibreOffice, поставляемого с локальным Codex runtime. Условия и уведомления Bitstream/DejaVu и Arev сохранены в `fonts/LICENSE-DejaVu.html` как раздел Deja Vu из `Resources/LICENSE.html`.

Сборка: `python3 build_catalog.py`. Проверка: `python3 validate_catalog.py`. Негативный сценарий с отдельной копией входа, подменой и восстановлением: `python3 -m unittest discover -s tests -v` из каталога SA06. Проверяющий вход в `--input` должен оставаться доверенным и неизменным.
