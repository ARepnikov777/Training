# Декомпозиция SA06

Веха: https://github.com/ARepnikov777/Training/milestone/8; родитель #57. Шесть подзадач соответствуют шести отдельным результатам: граф, данные, изображения, сборка, независимое ревью и сдача. Два исследования независимы по входам и не пишут файлы, поэтому запускаются параллельно. Общий макет требует одного worker, параллельных пишущих нет.

## [[SA06.1] Vrnur — Граф и контракт](https://github.com/ARepnikov777/Training/issues/124)

Роль: координатор; зависимости: нет. Входы: #57, #47, source/H11 и результат предыдущего этапа. Область: `workflow.md, briefs/, decomposition.md, evidence/workflow*`. DoD: Граф сохранён до предметных запусков, проверен graph_check и Mermaid, N/T/параллелизм указаны.

## [[SA06.2] Vrnur — Сверить товарные данные](https://github.com/ARepnikov777/Training/issues/125)

Роль: explorer; зависимости: Граф и контракт. Входы: #57, #47, source/H11 и результат предыдущего этапа. Область: `только чтение source/H11/input/products.csv, brief.md и README`. DoD: Отдельный отчёт пяти строк CSV с точными полями, csv_line и page 2+2+1.

## [[SA06.3] Vrnur — Проверить изображения и происхождение](https://github.com/ARepnikov777/Training/issues/126)

Роль: explorer; зависимости: Граф и контракт. Входы: #57, #47, source/H11 и результат предыдущего этапа. Область: `только чтение source/H11/input/*.png, LICENSE.md, provenance.md`. DoD: Отдельный визуальный отчёт пяти изображений, SHA256 и лицензий.

## [[SA06.4] Vrnur — Собрать каталог и проверки](https://github.com/ARepnikov777/Training/issues/127)

Роль: worker; зависимости: оба explorer-отчёта. Входы: #57, #47, source/H11 и результат предыдущего этапа. Область: `build_catalog.py, validate_catalog.py, tests/, requirements.txt, fonts/, result/, evidence/test*, evidence/negative*`. DoD: Редактируемая сборка, PDF A4 3 страницы 2+2+1, пять точных карточек, ведомость сверки, Red/Green и безопасная подмена изображения обнаружена.

## [[SA06.5] Vrnur — Независимое ревью](https://github.com/ARepnikov777/Training/issues/128)

Роль: reviewer; зависимости: сборка и приёмка координатора. Входы: #57, #47, source/H11 и результат предыдущего этапа. Область: `только чтение всей области SA06, отчёт в ответе без записи`. DoD: Все страницы просмотрены и все карточки сверены, отрицательный сценарий проверен, подтверждённые замечания исправлены или эскалированы.

## [[SA06.6] Vrnur — Локальная приёмка и один PR](https://github.com/ARepnikov777/Training/issues/129)

Роль: координатор; зависимости: положительное reviewer и отрицательный сценарий. Входы: #57, #47, source/H11 и результат предыдущего этапа. Область: `README.md, run-log.md, reviewer-report.md, evidence/, briefs/, decomposition.md`. DoD: Каждый DoD с доказательством, gitleaks staged и свои commits exit 0, один PR main, комментарий #57 со всеми ссылками; merge человеку.

Ветки: student/Vrnur/SA06 — интеграция; student/Vrnur/SA06-catalog — worker в том же явном checkout /Users/arnursain/orca/workspaces/Training/sa06. Запись последовательная: координатор передаёт право worker и до завершения worker файлов не меняет. Explorer/reviewer только читают. Публичные ветки исследований не нужны, поскольку они не пишут. Запреты: не менять входы, materials/downloads/чужие решения; субагенты без делегирования, commit/push/merge/публикации.
