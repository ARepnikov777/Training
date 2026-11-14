"""Локальные сайты для браузерных упражнений: без аккаунтов и внешних сервисов."""

import shutil
from pathlib import Path

from content import jsn, text


def catalog():
    records = []
    for n in range(1, 51):
        category = "laptop" if n <= 20 else ("accessory" if n <= 35 else "office")
        record = {
            "id": f"P{n:03}",
            "name": f"Orion L{n:02}" if n <= 20 else f"Учебный товар {n:02}",
            "category": category,
            "price": 200000 + n * 1000 if n <= 20 else n * 100,
            "currency": "KZT",
            "supplier": f"Поставщик {n:02}",
            "availability": "в наличии",
            "ram_GB": 16 if n <= 20 else None,
            "ssd_GB": 512 if n <= 20 else None,
            "screen_inches": 15.6 if n <= 20 else None,
        }
        if n <= 3:
            record.update(
                name="Orion L15 / 16 GB / 512 GB",
                supplier=["Учебный Альфа", "Учебный Бета", "Учебный Гамма"][n - 1],
                price=[245000, 239000, 249000][n - 1],
                availability=["в наличии", "нет в наличии", None][n - 1],
            )
        records.append(record)
    return records


SHOP_CHECKS = """# Контрольные сценарии учебного магазина

1. /shop: цена 1000, количество 3, скидка 10 → ожидается 2700.00. В исходной версии намеренно получается 3000.00: скидка игнорируется.
2. /shop: очистить количество, рассчитать → ожидается понятная ошибка и отсутствие числового итога. В исходной версии получается 0.00: пустое поле принято как ноль. Цена <0, количество 0/дробь и скидка вне 0–100 также должны отвергаться.
3. /shop: ссылка «Контакты» → ожидается /contacts и контактная страница. В исходнике ссылка ведёт на /missing и даёт 404.

Для H15: ошибки 1 и 2 — критичные (неверный расчёт и неверный заказ); ошибка 3 — некритичная. Перед исправлением сохраните фактические результаты, после — повторите сценарии. Соседние контрольные сценарии: 100×2 при скидке 0 →200.00; 100×2 при скидке 100 →0.00; /catalog и /register доступны. Исправлять следует локальную копию serve.py/app.js, не рабочие сайты.
"""
FORM_CHECKS = """# Восемь сценариев формы

Правила: имя 1–80 символов после trim (любые буквы/знаки разрешены); email — один @, непустая часть до него, точка в домене, без пробелов; consent=true. Повторная отправка тем же token не создаёт новую запись. novalidate намеренно отключает встроенную проверку браузера: проверяется логика приложения.

|№|Вход|Ожидается|
|---|---|---|
|1|Анна; anna@example.test; согласие|Успех, одна запись|
|2|Пустое имя; корректный email; согласие|Ошибка name|
|3|Анна; not-an-email; согласие|Ошибка email|
|4|Имя из 81 буквы а; корректный email; согласие|Ошибка name|
|5|Имя из 80 букв а; корректный email; согласие|Успех|
|6|Анна; a b@example.test; согласие|Ошибка email|
|7|Повторить отправку успешной формы без перезагрузки|Тот же id, без новой записи|
|8|После пустого имени ввести Анна и отправить|Успех|

В mode=form-buggy намеренно нарушены два класса требований: формат email не проверяется, верхняя граница имени ошибочно равна 120. Сценарии 3,4,6 должны выявить дефекты. Дополнительно можно проверить отсутствие согласия: ожидается consent. Список сохранённых записей: /api/registrations. Вводите только вымышленные данные.
"""


def make(root):
    tools = Path(__file__).parent
    records = catalog()
    for code in ["E13", "E14", "E15", "M13", "M14", "M15", "H13", "H14", "H15"]:
        p = root / code
        site = p / "input/site"
        site.mkdir(parents=True, exist_ok=True)
        for name in ["serve.py", "app.js", "style.css"]:
            shutil.copy2(tools / name, site / name)
        mode = (
            "form-buggy"
            if code == "M14"
            else ("shop-buggy" if code in ["E15", "M15", "H15"] else "normal")
        )
        jsn(site / "config.json", {"mode": mode, "synthetic": True})
        jsn(site / "catalog.json", records)
        text(
            p / "input/START.md",
            """# Запуск

Требуется Python 3.10+; сторонние пакеты не нужны. Из папки задания запустите:

    python input/site/serve.py --port 8765

Если команда python отсутствует, используйте python3 (Linux/macOS) или py -3 (Windows). Если порт занят, замените 8765 на 8766 и в команде, и в адресе. Откройте http://127.0.0.1:8765/ в браузере. Остановка: Ctrl+C в терминале. Все записи сохраняются только в input/site/_state.json; для чистого прогона после остановки переименуйте этот файл, если он появился. Никаких внешних API/учётных записей/SSH нет. Цены, поставщики и товары вымышлены.
""",
        )
        if code == "E13":
            text(
                p / "input/targets.md",
                "Сравните http://127.0.0.1:8765/product?id=P001 , http://127.0.0.1:8765/product?id=P002 , http://127.0.0.1:8765/product?id=P003 . Одна конфигурация Orion L15 /16 GB/512 GB. В таблице: supplier, name, ram_GB, ssd_GB, screen_inches, price, currency, availability, ссылка и ваше фактическое время проверки. null означает «не указано», а не «нет в наличии». Доставку не рассчитывать.",
            )
            jsn(p / "checks/expected.json", records[:3])
        elif code == "E14":
            jsn(
                p / "input/participant.json",
                {
                    "name": "Анна Учебная",
                    "email": "anna.student@example.test",
                    "consent": True,
                },
            )
            text(
                p / "input/scenario.md",
                "Откройте /register. Перенесите значения из participant.json. Сохраните скриншот заполненной формы до отправки. Отправьте на этом локальном стенде; сохраните подтверждение с id. Сверьте поля в /api/registrations. Не вводите реальные персональные данные.",
            )
            jsn(
                p / "checks/expected.json",
                {
                    "name": "Анна Учебная",
                    "email": "anna.student@example.test",
                    "registrations_for_same_form": 1,
                },
            )
        elif code in ["E15", "M15", "H15"]:
            text(
                p / "input/requirements.md",
                "Проверьте /shop: формула price*quantity*(1-discount/100), округление 2 знака. Цена >=0, quantity положительное целое, discount 0–100. Все поля обязательны. Ссылка «Контакты» должна открывать контактную страницу. Исходник намеренно содержит три дефекта. E15: только отчёт. M15: исправьте все три. H15: независимая приёмка, исправление критичных дефектов, решение о готовности с оставшимися ограничениями. Для baseline не меняйте config.json: ошибки устраняются в коде, а не переключением режима на normal.",
            )
            text(p / "checks/scenarios.md", SHOP_CHECKS)
        elif code == "M13":
            text(
                p / "input/selection.md",
                "Откройте /catalog?category=laptop. Соберите все 20 ноутбуков со всех страниц. Поля: id,name,category,price,currency,supplier,availability,ram_GB,ssd_GB,screen_inches,source_url. Пропущенные значения оставить пустыми/не указано. Собирать через браузер; чтение catalog.json допустимо только для проверки. Пагинация: по 10 записей.",
            )
            jsn(
                p / "checks/expected-ids.json",
                [r["id"] for r in records if r["category"] == "laptop"],
            )
        elif code == "M14":
            text(p / "input/scenarios.md", FORM_CHECKS.split("В mode=")[0])
            text(p / "checks/known-defects.md", FORM_CHECKS)
        elif code == "H13":
            text(
                p / "input/scenario.md",
                "Соберите 50 товаров с /catalog, по 10 на странице. Поля как в catalog: id,name,category,price,currency,supplier,availability,ram_GB,ssd_GB,screen_inches плюс source_url. Сохраняйте прогресс по id. Первый запуск: /catalog?fail=1 — третья страница вернёт 503. После получения первых 20 записей прервите агент/сборщик, сохранив состояние и доказательства ошибки. Продолжите без fail=1; итог — ровно 50 уникальных записей. Для управляемого прерывания можно задать сборщику остановку после двух страниц. Не объявляйте частичный набор полным. Через браузер собирать, catalog.json использовать только для проверки.",
            )
            jsn(p / "checks/expected-ids.json", [r["id"] for r in records])
        else:
            text(
                p / "input/scenario.md",
                "Откройте /tickets. Создайте заявку с уникальным title «Проверить PDF <идентификатор запуска>», description «Страницы 1–3». Сохраните id. Измените title на «Проверить PDF и таблицу <идентификатор>», description на «Страницы 1–3 и итог», status на «в работе». Найдите заявку поиском по её id, перезагрузите страницу и сверьте все поля. Повторите с новым идентификатором. Сдать автоматизацию/повторяемую инструкцию и доказательства этапов. Разрешены статусы новая/в работе/готово, title 1–100 после trim. API документирован ниже только для проверки и диагностики; основной сценарий выполнить браузером. GET /api/tickets?q=<id>, POST /api/tickets {title,description}, PUT /api/tickets/<id> {title,description,status}. Состояние хранится локально.",
            )
            jsn(
                p / "checks/expected.json",
                {
                    "initial_status": "новая",
                    "final_status": "в работе",
                    "final_description": "Страницы 1–3 и итог",
                    "per_run_new_ticket": 1,
                    "persists_after_reload": True,
                },
            )
