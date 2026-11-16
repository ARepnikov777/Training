"""Самодостаточный локальный учебный стенд. Python 3.10+, без зависимостей."""

import argparse
import json
import re
import uuid
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse


def registration_errors(data, buggy=False):
    errors = []
    name = str(data.get("name", "")).strip()
    if not 1 <= len(name) <= (120 if buggy else 80):
        errors.append("name")
    if not buggy and not re.fullmatch(
        r"[^\s@]+@[^\s@]+\.[^\s@]+", str(data.get("email", ""))
    ):
        errors.append("email")
    if not data.get("email"):
        errors.append("email")
    if data.get("consent") is not True:
        errors.append("consent")
    return sorted(set(errors))


def page(title, body):
    return f"""<!doctype html><html lang="ru"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title><link rel="stylesheet" href="/style.css">
<body><header><b>Учебная мастерская</b><nav><a href="/">Главная</a>
<a href="/catalog">Каталог</a><a href="/register">Регистрация</a>
<a href="/shop">Заказ</a><a href="/tickets">Заявки</a></nav></header>
<main><h1>{escape(title)}</h1>{body}</main></body></html>"""


class Handler(BaseHTTPRequestHandler):
    site = Path(".")

    def send(self, status, payload, content_type="text/html; charset=utf-8"):
        body = payload if isinstance(payload, bytes) else payload.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def json(self, status, data):
        self.send(
            status,
            json.dumps(data, ensure_ascii=False),
            "application/json; charset=utf-8",
        )

    def state(self):
        path = self.site / "_state.json"
        return (
            json.loads(path.read_text())
            if path.exists()
            else {"registrations": [], "tickets": []}
        )

    def save(self, state):
        (self.site / "_state.json").write_text(
            json.dumps(state, ensure_ascii=False, indent=2)
        )

    def config(self):
        return json.loads((self.site / "config.json").read_text())

    def do_GET(self):
        parsed = urlparse(self.path)
        route = parsed.path
        query = parse_qs(parsed.query)
        if route in ["/app.js", "/style.css"]:
            types = {
                ".js": "text/javascript; charset=utf-8",
                ".css": "text/css; charset=utf-8",
            }
            p = self.site / route[1:]
            return self.send(200, p.read_bytes(), types[p.suffix])
        if route == "/api/config":
            return self.json(200, self.config())
        if route == "/api/tickets":
            records = self.state()["tickets"]
            q = query.get("q", [""])[0].lower()
            return self.json(
                200, [r for r in records if q in (r["title"] + r["id"]).lower()]
            )
        if route == "/api/registrations":
            return self.json(200, self.state()["registrations"])
        if route == "/catalog":
            try:
                num = max(1, int(query.get("page", ["1"])[0]))
            except ValueError:
                return self.send(
                    400, page("Ошибка", "Номер страницы должен быть целым.")
                )
            if num == 3 and query.get("fail") == ["1"]:
                return self.send(
                    503,
                    page("Временный сбой", "Учебная имитация. Повторите без fail=1."),
                )
            records = json.loads((self.site / "catalog.json").read_text())
            category = query.get("category", [""])[0]
            if category:
                records = [r for r in records if r["category"] == category]
            per_page = 10
            chosen = records[(num - 1) * per_page : num * per_page]
            rows = "".join(
                f"""<tr><td>{r["id"]}</td><td><a href="/product?id={r["id"]}">{r["name"]}</a></td>
<td>{r["category"]}</td><td>{r["price"]}</td><td>{r["currency"]}</td></tr>"""
                for r in chosen
            )
            links = " ".join(
                f'<a href="/catalog?{urlencode({"page": n, "category": category, "fail": query.get("fail", ["0"])[0]})}">{n}</a>'
                for n in range(1, (len(records) + 9) // 10 + 1)
            )
            return self.send(
                200,
                page(
                    "Каталог",
                    f"""<p>Все сведения синтетические, цены учебные. Всего: <b id="count">{len(records)}</b>.</p>
<p><a href="/catalog">Все товары</a> · <a href="/catalog?category=laptop">Ноутбуки</a></p>
<table><tr><th>ID</th><th>Название</th><th>Категория</th><th>Цена</th><th>Валюта</th></tr>{rows}</table><nav aria-label="Страницы">{links}</nav>""",
                ),
            )
        if route == "/product":
            records = json.loads((self.site / "catalog.json").read_text())
            record = next(
                (r for r in records if r["id"] == query.get("id", [""])[0]), None
            )
            if record is None:
                return self.send(404, page("Не найдено", "Такого товара нет."))
            body = "".join(
                f"<dt>{escape(str(k))}</dt><dd>{escape(str(v))}</dd>"
                for k, v in record.items()
            )
            return self.send(200, page(record["name"], "<dl>" + body + "</dl>"))
        if route == "/register":
            return self.send(
                200,
                page(
                    "Регистрация",
                    """<p>Только вымышленные данные. Имя: 1–80 символов; email: адрес с @ и точкой в домене; согласие обязательно.</p>
<form id="register" novalidate><label>Имя<input id="name" name="name"></label>
<label>Email<input id="email" name="email" type="text"></label>
<label><input id="consent" type="checkbox"> Согласен с учебной обработкой</label>
<button>Отправить</button></form><p id="result" role="status"></p><script src="/app.js"></script>""",
                ),
            )
        if route == "/shop":
            return self.send(
                200,
                page(
                    "Стоимость заказа",
                    """<p>Правила: цена ≥ 0; количество — положительное целое; скидка 0–100%. Пустые поля недопустимы.</p>
<form id="shop" novalidate><label>Цена<input id="price" value="1000"></label>
<label>Количество<input id="quantity" value="3"></label><label>Скидка, %<input id="discount" value="10"></label><button>Рассчитать</button></form>
<p id="total" role="status"></p><p><a href="/missing">Контакты</a></p><script src="/app.js"></script>""",
                ),
            )
        if route == "/tickets":
            return self.send(
                200,
                page(
                    "Заявки",
                    """<form id="ticket"><label>Название<input id="title" required maxlength="100"></label><label>Описание<textarea id="description"></textarea></label><button>Создать</button></form>
<label>Поиск по названию или ID<input id="search"></label><button id="find">Найти</button><div id="tickets"></div><p id="result" role="status"></p><script src="/app.js"></script>""",
                ),
            )
        if route == "/contacts":
            return self.send(
                200, page("Контакты", "Учебная мастерская: course@example.test")
            )
        if route == "/":
            return self.send(
                200,
                page(
                    "Локальный учебный стенд",
                    "<p>Выберите раздел в навигации. Данные и дефекты созданы специально для упражнений.</p>",
                ),
            )
        self.send(404, page("404", "Страница не найдена."))

    def read_json(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise TypeError("object required")
            return data
        except (ValueError, TypeError, json.JSONDecodeError):
            self.json(400, {"error": "Ожидается JSON-объект"})
            return None

    def do_POST(self):
        data = self.read_json()
        if data is None:
            return
        state = self.state()
        if self.path == "/api/register":
            errors = registration_errors(
                data, self.config().get("mode") == "form-buggy"
            )
            if errors:
                return self.json(400, {"errors": errors})
            token = str(data.get("token", ""))
            existing = next(
                (r for r in state["registrations"] if token and r["token"] == token),
                None,
            )
            if existing:
                return self.json(200, existing)
            record = {
                "id": str(uuid.uuid4()),
                "token": token,
                "name": data["name"],
                "email": data["email"],
            }
            state["registrations"].append(record)
            self.save(state)
            return self.json(201, record)
        if self.path == "/api/tickets":
            if not 1 <= len(str(data.get("title", "")).strip()) <= 100:
                return self.json(400, {"error": "Название: 1–100 символов"})
            record = {
                "id": str(uuid.uuid4()),
                "title": data["title"].strip(),
                "description": str(data.get("description", "")),
                "status": "новая",
            }
            state["tickets"].append(record)
            self.save(state)
            return self.json(201, record)
        self.json(404, {"error": "Не найдено"})

    def do_PUT(self):
        data = self.read_json()
        if data is None:
            return
        record_id = self.path.removeprefix("/api/tickets/")
        state = self.state()
        record = next((r for r in state["tickets"] if r["id"] == record_id), None)
        if record is None:
            return self.json(404, {"error": "Не найдено"})
        if "title" in data and not 1 <= len(str(data["title"]).strip()) <= 100:
            return self.json(400, {"error": "Название: 1–100 символов"})
        if "status" in data and data["status"] not in ["новая", "в работе", "готово"]:
            return self.json(400, {"error": "Недопустимый статус"})
        for key in ["title", "description", "status"]:
            if key in data:
                record[key] = str(data[key]).strip()
        self.save(state)
        self.json(200, record)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--site", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    Handler.site = args.site.resolve()
    print(
        f"Учебный стенд: http://127.0.0.1:{args.port} (Ctrl+C для остановки)",
        flush=True,
    )
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
