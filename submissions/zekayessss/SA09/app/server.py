"""HTTP-сервер «Заявки практикума» (контракт SA09, разделы 3 и 6). Только стандартная библиотека."""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))

from store import (  # noqa: E402
    DEFAULT_DATA_PATH,
    CorruptDataError,
    FileFormatError,
    NotFoundError,
    TaskStore,
    ValidationError,
    type_error,
)

HOST = "127.0.0.1"
STATIC_DIR = Path(__file__).resolve().parent / "static"
CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
}
MSG_NOT_FOUND = "Не найдено"
MSG_METHOD = "Метод не поддерживается"
MSG_BAD_JSON = "Тело запроса должно быть JSON-объектом"


class Handler(BaseHTTPRequestHandler):
    server_version = "SA09"
    store: TaskStore  # задаётся в make_server

    # ---- вспомогательные ----
    def log_message(self, fmt, *args):  # тихий лог в stderr
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, code: int, body: bytes, content_type: str, extra=None):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, code: int, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self._send(code, body, "application/json; charset=utf-8")

    def _error(self, code: int, message: str):
        self._json(code, {"error": message})

    def _body(self) -> bytes:
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length) if length > 0 else b""

    def _json_body(self):
        try:
            obj = json.loads(self._body().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        return obj if isinstance(obj, dict) else None

    def _route(self):
        parts = urlsplit(self.path)
        return parts.path, parse_qs(parts.query, keep_blank_values=True)

    # ---- методы ----
    def do_GET(self):
        path, query = self._route()
        if path == "/":
            return self._static("index.html")
        if path.startswith("/static/"):
            return self._static(unquote(path[len("/static/"):]))
        if path == "/api/tasks":
            q = query.get("q", [""])[0]
            status = query.get("status", [""])[0]
            try:
                return self._json(200, {"tasks": self.store.list(q=q, status=status)})
            except ValidationError as exc:
                return self._error(400, exc.message)
        if path == "/api/export":
            body = self.store.export_csv().encode("utf-8")
            return self._send(
                200,
                body,
                "text/csv; charset=utf-8",
                {"Content-Disposition": 'attachment; filename="tasks.csv"'},
            )
        if path == "/api/import" or path.startswith("/api/tasks/"):
            return self._error(405, MSG_METHOD)
        return self._error(404, MSG_NOT_FOUND)

    def do_POST(self):
        path, _ = self._route()
        if path == "/api/tasks":
            body = self._json_body()
            if body is None:
                return self._error(400, MSG_BAD_JSON)
            for field in ("title", "description"):
                if field in body and not isinstance(body[field], str):
                    return self._error(400, type_error(field))
            try:
                task = self.store.create(body.get("title", ""), body.get("description", ""))
            except ValidationError as exc:
                return self._error(400, exc.message)
            return self._json(201, {"task": task})
        if path == "/api/import":
            try:
                report = self.store.import_csv(self._body())
            except FileFormatError as exc:
                return self._error(400, exc.message)
            return self._json(200, report)
        if path in ("/", "/api/export") or path.startswith("/static/") or path.startswith("/api/tasks/"):
            return self._error(405, MSG_METHOD)
        return self._error(404, MSG_NOT_FOUND)

    def do_PATCH(self):
        path, _ = self._route()
        if path.startswith("/api/tasks/") and len(path) > len("/api/tasks/"):
            task_id = unquote(path[len("/api/tasks/"):])
            body = self._json_body()
            if body is None:
                return self._error(400, MSG_BAD_JSON)
            for field in ("title", "description", "status"):
                if field in body and not isinstance(body[field], str):
                    return self._error(400, type_error(field))
            try:
                task = self.store.update(task_id, body)
            except NotFoundError as exc:
                return self._error(404, exc.message)
            except ValidationError as exc:
                return self._error(400, exc.message)
            return self._json(200, {"task": task})
        return self._unsupported(path)

    def do_PUT(self):
        self._unsupported(self._route()[0])

    def do_DELETE(self):
        self._unsupported(self._route()[0])

    def _unsupported(self, path: str):
        known = path in ("/", "/api/tasks", "/api/import", "/api/export") or path.startswith(
            ("/static/", "/api/tasks/")
        )
        self._error(405 if known else 404, MSG_METHOD if known else MSG_NOT_FOUND)

    def _static(self, name: str):
        if not name or "/" in name or "\\" in name or name.startswith(".") or ".." in name:
            return self._error(404, MSG_NOT_FOUND)
        file = STATIC_DIR / name
        if not file.is_file():
            return self._error(404, MSG_NOT_FOUND)
        ctype = CONTENT_TYPES.get(file.suffix, "application/octet-stream")
        self._send(200, file.read_bytes(), ctype)


def make_server(store: TaskStore, port: int) -> HTTPServer:
    handler = type("BoundHandler", (Handler,), {"store": store})
    return HTTPServer((HOST, port), handler)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Заявки практикума — локальный сервер")
    parser.add_argument("--port", type=int, default=8000, help="порт (по умолчанию 8000)")
    parser.add_argument("--data", default=None, help="путь к JSON-файлу данных")
    args = parser.parse_args(argv)

    data_path = Path(args.data).resolve() if args.data else DEFAULT_DATA_PATH
    try:
        store = TaskStore(data_path)
    except CorruptDataError as exc:
        print(f"Ошибка: файл данных {data_path} повреждён: {exc.message}", file=sys.stderr)
        return 1

    server = make_server(store, args.port)
    print(f"Сервер запущен: http://{HOST}:{args.port}/ (данные: {data_path})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
