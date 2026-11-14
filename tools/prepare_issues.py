"""Подготовить тексты issues со ссылками на опубликованный commit, без отправки."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def prepare(revision):
    catalog = json.loads((ROOT / "catalog.json").read_text())
    source = {
        x["code"]: x for x in json.loads((ROOT / "tools/issue-source.json").read_text())
    }
    updates = []
    for item in catalog:
        code = item["code"]
        p = ROOT / "materials" / code
        manifest = json.loads((p / "manifest.json").read_text())
        spec = source[code]
        prefix = (
            f"https://github.com/ARepnikov777/Training/blob/{revision}/materials/{code}"
        )
        raw = f"https://raw.githubusercontent.com/ARepnikov777/Training/{revision}/downloads/{code}.zip"
        readme = (p / "README.md").read_text()
        start = (
            readme.split("## Как начать\n\n", 1)[1]
            .split("\n## Входные файлы", 1)[0]
            .strip()
        )
        inputs = "\n".join(
            f"- [{name}]({prefix}/{name})" for name in manifest["inputs"]
        )
        checks = "\n".join(
            f"- [{name}]({prefix}/{name})" for name in manifest["checks"]
        )
        dod = "\n".join("- [ ] " + line for line in spec["dod"])
        level = {"E": "easy", "M": "medium", "H": "hard"}[code[0]]
        times = {"E": "15–25", "M": "30–50", "H": "60–90"}[code[0]]
        body = f"""## Что сделать

{item["goal"]}

**Уровень:** {level}. **Код:** {code}. Ориентир времени: {times} минут, предварительная оценка.

## Готовые материалы

**[Скачать полный комплект {code}.zip]({raw})** · [Открыть инструкцию]({prefix}/README.md)

ZIP содержит все входные данные, точные правила и контрольные примеры. Искать дополнительные исходники у преподавателя не нужно. Распакуйте ZIP: просмотр файлов в GitHub не заменяет скачивание для запуска стенда.

SHA-256 ZIP: `{item["sha256"]}`. Ссылка привязана к проверенной редакции материалов.

## Как начать

{start}

## Входные файлы и правила

{inputs}

## Контрольные примеры

{checks}

Контрольные файлы — данные для самопроверки, не готовая программа решения. Сначала выполните задание по input, затем сверяйте результат с checks.

## Definition of Done (DoD)

{dod}

## Что сдать

Готовый результат, редактируемые исходники/промпты при наличии, инструкцию открытия или запуска и доказательства выполненных проверок. Конкретные форматы, поля, правила и сценарии заданы в README и input-файлах комплекта.

## Как сдать

Подготовь решение в `submissions/<твой-GitHub-логин>/{code}/`, создай ветку `student/<твой-GitHub-логин>/{code}` в этом же репозитории и открой один PR в `main`. Fork не требуется. В README решения приведи результаты и доказательства по каждому пункту DoD; исходные материалы не меняй. В описании PR укажи `Задание: #{item["issue"]}` без `Closes`. Замечания преподавателя исправляй в том же PR.

Полные правила подготовки и сдачи: [README репозитория](https://github.com/ARepnikov777/Training#подготовка-и-сдача-задания).

## Условия

Все документы, персонажи, товары и числа в комплекте вымышлены и подготовлены специально для обучения. Работа выполняется на своём компьютере, без SSH, удалённого сервера и облачного развёртывания. Исходные файлы сохраняйте без перезаписи; работу выполняйте на копии. Локальный браузерный стенд использует Python 3.10+ без сторонних пакетов. Для графики есть вариант без платного AI-генератора.

<!-- course-practice:{code} -->
"""
        updates.append(
            {
                "number": item["issue"],
                "code": code,
                "title": spec["title"],
                "body": body,
                "level": level,
            }
        )
    return updates


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("revision", help="Опубликованный SHA коммита")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.write_text(
        json.dumps(prepare(args.revision), ensure_ascii=False, indent=2) + "\n"
    )
    print("Подготовлено 45 текстов issues; внешние записи не выполнялись.")
