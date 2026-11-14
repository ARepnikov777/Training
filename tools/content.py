"""Учебные данные и небольшие исходные проекты без готовых решений."""

import csv
import hashlib
import json
import shutil
import zipfile


def text(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def jsn(path, value):
    text(path, json.dumps(value, ensure_ascii=False, indent=2))


def table(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def archive(path, files):
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 14, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, content.encode() if isinstance(content, str) else content)


CART = '''"""Учебный проект. Процентная скидка содержит намеренный дефект."""

def total(price, quantity, discount_percent=0):
    if price < 0 or quantity <= 0 or int(quantity) != quantity or not 0 <= discount_percent <= 100:
        raise ValueError('Недопустимый ввод')
    return round(price * quantity * (1 - discount_percent), 2)

if __name__ == '__main__':
    print(total(1000, 3, 10))
'''
CART_SPEC = """# Контракт расчёта

Сумма = цена × количество × (1 − скидка / 100), округление до двух знаков.
Цена — число ≥ 0, скидка 0–100 включительно. Для E02 количество — положительное целое.
Для M02 новая возможность: положительное дробное количество; округлять только итог.
Неверные значения должны приводить к ValueError. Функция total(price, quantity, discount_percent=0) находится в cart.py.
Старт: python -m unittest discover -v. Имеющийся тест проверяет только заказ без скидки; добавьте регрессионный тест самостоятельно.
"""
BASE_TEST = """import unittest
from cart import total

class ExistingTests(unittest.TestCase):
    def test_without_discount(self):
        self.assertEqual(total(1000, 2, 0), 2000)
"""
ARCHIVE_FILES = {
    "incoming/report.txt": "Report version A\n",
    "backup/report-copy.txt": "Report version A\n",
    "other/report.txt": "Report version B\n",
    "set-a/a.txt": "Alpha\n",
    "set-a/sub/b.md": "# Beta\n",
    "set-a-copy/a.txt": "Alpha\n",
    "set-a-copy/sub/b.md": "# Beta\n",
    "set-different/a.txt": "Alpha changed\n",
    "set-different/sub/b.md": "# Gamma\n",
    "empty.txt": "",
    "backup/empty-copy.txt": "",
    "notes/one.txt": "One\n",
    "notes/two.txt": "Two\n",
    "photos/readme.md": "No photos; training only.\n",
    "data/january.csv": "id,value\n1,100\n",
    "data/february.csv": "id,value\n2,200\n",
    "notes/Текст с пробелами.txt": "Unicode example\n",
    "notes/archive-notes.txt": "Keep me\n",
}
ARCHIVE_POLICY = """# Правила H01

В архиве 18 файлов. Работайте только с распакованной копией.
1. Дубликаты файлов: одинаковые байты независимо от имени, расширения и пути; пустые файлы тоже участвуют.
2. Дубликаты папок: одинаковые относительные пути вложенных файлов и одинаковое содержимое каждого файла, рекурсивно. Сравниваются все непустые папки, включая вложенные; даты не учитываются. Имена сравниваемых корневых папок могут различаться.
3. Сначала составьте отчёт по группам файлов, группам папок и конфликтам имён. Не меняйте ничего при предварительном просмотре.
4. План нормализации: уникальные файлы копируются/переносятся в result/files, точные повторы — в result/duplicates с сохранением исходного относительного пути. Представитель группы — лексикографически первый путь в Python sorted(). Не удаляйте данные физически.
5. Конфликт имени разных файлов: добавьте к stem двойное подчёркивание и первые 8 знаков SHA-256. При совпадении коротких суффиксов увеличивайте длину до различимости.
6. Не выполняйте отдельные перемещения дублей папок: их файлы уже учтены на шаге 4. Группы папок — самостоятельный раздел отчёта.
7. Журнал должен позволять отменить реальное перемещение: восстановить исходные пути и байты, убрать созданные пустые выходные папки. Разрешено начинать с варианта копирования, но итоговое упражнение должно показать выполнение и отмену плана переноса.
8. Сдать утилиту, report.json, plan.json, журнал, доказательства dry-run и отката. Пример формата отчёта — checks/report-schema.json; готовой утилиты в комплекте нет.
"""


def programming(root, assets):
    p = root / "E01"
    docs = {
        "readme.txt": "Read me\n",
        "notes.md": "# Notes\n",
        "record.json": '{"id": 1}\n',
    }
    for name, value in docs.items():
        text(p / "input/files" / name, value)
    shutil.copy2(assets / "text.pdf", p / "input/files/manual.pdf")
    for i in range(1, 5):
        (p / "input/files").mkdir(parents=True, exist_ok=True)
        shutil.copy2(
            assets / "images" / f"product-{i}.png",
            p / "input/files" / f"picture-{i}.png",
        )
        table(p / "input/files" / f"table-{i}.csv", ["id", "value"], [[i, i * 10]])
    expected = {
        "documents": ["manual.pdf", "notes.md", "readme.txt", "record.json"],
        "images": [f"picture-{i}.png" for i in range(1, 5)],
        "tables": [f"table-{i}.csv" for i in range(1, 5)],
    }
    jsn(p / "checks/expected.json", expected)
    text(
        p / "input/rules.md",
        "Распределите копии файлов: .txt/.md/.json/.pdf → documents; .png → images; .csv → tables. Каталоги input/files не менять. Выходная папка result создаётся отдельно. Все 12 файлов должны быть учтены.",
    )
    for code in ["E02", "M02"]:
        p = root / code
        text(p / "input/project/cart.py", CART)
        text(p / "input/project/test_existing.py", BASE_TEST)
        text(p / "input/project/SPEC.md", CART_SPEC)
        cases = [
            {"price": 1000, "quantity": 3, "discount_percent": 10, "expected": 2700},
            {"price": 100, "quantity": 2, "discount_percent": 100, "expected": 0},
            {"price": 99, "quantity": 1, "discount_percent": 0, "expected": 99},
        ]
        if code == "M02":
            cases += [
                {
                    "price": 200,
                    "quantity": 1.5,
                    "discount_percent": 10,
                    "expected": 270,
                },
                {"price": 10, "quantity": 0.25, "discount_percent": 0, "expected": 2.5},
            ]
        jsn(p / "checks/cases.json", cases)
        text(
            p / "checks/invalid.md",
            "Проверьте отрицательную цену, количество 0, отрицательное количество, скидку -1 и 101. Ожидается ValueError. В E02 дробное количество также недопустимо; в M02 положительное дробное количество допустимо.",
        )
    p = root / "M01"
    for name, value in {
        "a/report.txt": "A",
        "b/report.txt": "B",
        "c/data.csv": "id,value\n1,5",
        "c/note.md": "# Note",
    }.items():
        text(p / "input/files" / name, value)
    text(
        p / "input/starter.py",
        """from pathlib import Path
import shutil

def copy_files(source, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    for p in Path(source).iterdir():
        if p.is_file():
            shutil.copy2(p, output / p.name)
""",
    )
    text(
        p / "input/rules.md",
        "Рекурсивно обходите input/files; копируйте .txt/.md в documents, .csv в tables. Для конфликтов имён: пути сортируются; первый получает исходное имя, следующие — stem__2.ext, stem__3.ext. Dry-run ничего не меняет. Источник сохраняется. Журнал: исходный путь, целевой путь, действие, причина пропуска. Чтение ошибки файла не скрывать.",
    )
    jsn(
        p / "checks/expected.json",
        {
            "documents/report.txt": "A\n",
            "documents/report__2.txt": "B\n",
            "documents/note.md": "# Note\n",
            "tables/data.csv": "id,value\n1,5\n",
        },
    )
    p = root / "H01"
    archive(p / "input/archive.zip", ARCHIVE_FILES)
    text(p / "input/rules.md", ARCHIVE_POLICY)
    jsn(
        p / "checks/original-manifest.json",
        [
            {
                "path": k,
                "size": len(v.encode()),
                "sha256": hashlib.sha256(v.encode()).hexdigest(),
            }
            for k, v in sorted(ARCHIVE_FILES.items())
        ],
    )
    jsn(
        p / "checks/expected.json",
        {
            "file_count": 18,
            "duplicate_file_groups": [
                ["backup/report-copy.txt", "incoming/report.txt"],
                ["set-a/a.txt", "set-a-copy/a.txt"],
                ["set-a/sub/b.md", "set-a-copy/sub/b.md"],
                ["backup/empty-copy.txt", "empty.txt"],
            ],
            "duplicate_folder_groups": [
                ["set-a", "set-a-copy"],
                ["set-a/sub", "set-a-copy/sub"],
            ],
            "basename_conflicts": ["report.txt", "a.txt", "b.md"],
        },
    )
    jsn(
        p / "checks/report-schema.json",
        {
            "duplicate_files": [["relative/path", "relative/other"]],
            "duplicate_folders": [["folder", "other-folder"]],
            "name_conflicts": [
                {
                    "name": "report.txt",
                    "paths": ["incoming/report.txt", "other/report.txt"],
                }
            ],
        },
    )
    p = root / "H02"
    text(p / "input/project/discount.py", CART.replace("def total(", "def total("))
    text(
        p / "input/project/shipping.py",
        '"""Учебный дефект границы бесплатной доставки."""\ndef shipping(total):\n    return 0 if total > 5000 else 500\n',
    )
    text(
        p / "input/project/test_existing.py",
        """import unittest
from discount import total
from shipping import shipping
class Existing(unittest.TestCase):
    def test_no_discount(self): self.assertEqual(total(100, 2), 200)
    def test_paid_shipping(self): self.assertEqual(shipping(4000), 500)
""",
    )
    text(
        p / "input/project/SPEC.md",
        'Два независимых дефекта: A — процентная скидка в discount.total по формуле SPEC; B — shipping.shipping: доставка бесплатна при сумме >=5000, иначе 500. Рабочие области: агент A меняет discount.py и свой test_discount.py; агент B — shipping.py и test_shipping.py. Координатор интегрирует. Старт: git init, git add ., git commit -m "Учебный старт"; затем отдельные ветки/worktree. Общая проверка: python -m unittest discover -v. Если харнес не умеет запускать агентов, используйте два отдельных его процесса с одинаковым брифом ролей; один процесс не изображает независимое ревью.',
    )
    jsn(
        p / "checks/cases.json",
        {
            "discount": [[1000, 3, 10, 2700]],
            "shipping": [[4999, 500], [5000, 0], [5001, 0]],
        },
    )
    for code in ["E03", "M03", "H03"]:
        p = root / code
        if code == "E03":
            spec = "Создайте локальную HTML-страницу с полями price, quantity, discount и выводом total. Формула: price*quantity*(1-discount/100). Цена >=0, количество — положительное целое, скидка 0–100; пустые поля недопустимы. Округление до двух знаков; интерфейс должен объяснять ошибку."
            cases = [
                {"price": 1000, "quantity": 3, "discount": 10, "expected": 2700},
                {"price": 50, "quantity": 2, "discount": 100, "expected": 0},
                {"price": 0, "quantity": 1, "discount": 0, "expected": 0},
            ]
        else:
            spec = "Создайте локальное приложение. Поля задачи/заявки: id (уникальный), title (1–100 символов после trim), description (текст), status (новая/в работе/готово). Создание со статусом новая; редактирование названия/описания и любого из трёх статусов; фильтр по статусу. Сохраняйте данные локально между перезагрузками и запусками. Удаление не требуется."
            cases = [
                {
                    "step": "Создать «Проверить скан»",
                    "expected": "Появилась новая запись",
                },
                {
                    "step": "Переименовать в «Проверить PDF», статус готово",
                    "expected": "Сохранены новые поля",
                },
                {"step": "Перезагрузить приложение", "expected": "Данные сохранились"},
                {
                    "step": "Создать запись с пробелами вместо title",
                    "expected": "Понятная ошибка; запись не добавлена",
                },
            ]
            if code == "H03":
                spec += " Добавьте поиск по части title без учёта регистра, импорт и экспорт CSV UTF-8: id,title,description,status. Повторный импорт существующего id обновляет запись. Плохие строки не принимаются, но не мешают хорошим; ошибки содержат номер CSV-строки (заголовок = 1). Разрешены только три статуса. Автоматизация через браузер не обязательна, проверьте заданные сценарии."
                table(
                    p / "input/import-valid.csv",
                    ["id", "title", "description", "status"],
                    [
                        ["T001", "Проверить скан", "Первые три страницы", "новая"],
                        ["T002", "Обновить таблицу", "Бюджет курса", "в работе"],
                    ],
                )
                table(
                    p / "input/import-mixed.csv",
                    ["id", "title", "description", "status"],
                    [
                        ["T003", "Сверить итог", "", "готово"],
                        ["T004", "", "Нет названия", "новая"],
                        ["T005", "Неизвестный статус", "", "архив"],
                    ],
                )
                cases += [
                    {
                        "step": "Импортировать import-valid.csv дважды",
                        "expected": "Всего две импортированные записи, без дублей",
                    },
                    {
                        "step": "Импортировать import-mixed.csv",
                        "expected": "T003 принята, ошибки строк 3 и 4",
                    },
                ]
        text(p / "input/SPEC.md", spec)
        jsn(p / "checks/cases.json", cases)
