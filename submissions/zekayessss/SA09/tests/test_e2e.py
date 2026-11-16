"""Сквозные сценарии SA09 (контракт, раздел 7): настоящий процесс сервера + HTTP.

Только стандартная библиотека. Запуск из submissions/zekayessss/SA09/:
    python3.12 -m unittest tests.test_e2e -v
Каталог приложения: переменная окружения SA09_APP_DIR (по умолчанию app/ рядом с tests/).
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
APP_DIR = Path(os.environ.get("SA09_APP_DIR") or (HERE.parent / "app")).resolve()
REPO_ROOT = HERE.parents[3]
INPUT_DIR = REPO_ROOT / "materials" / "H03" / "input"
VALID_CSV = INPUT_DIR / "import-valid.csv"
MIXED_CSV = INPUT_DIR / "import-mixed.csv"

STATUS_ARCHIVE_ERR = "Недопустимый статус «архив»: разрешены «новая», «в работе», «готово»"
TITLE_EMPTY_ERR = "Название не может быть пустым"


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Server:
    """Настоящий процесс app/server.py на свободном порту."""

    def __init__(self, data_path: Path, port: int | None = None):
        self.data_path = data_path
        self.port = port or free_port()
        self.base = f"http://127.0.0.1:{self.port}"
        self.proc: subprocess.Popen | None = None

    def start(self):
        self.proc = subprocess.Popen(
            [sys.executable, str(APP_DIR / "server.py"), "--port", str(self.port), "--data", str(self.data_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError(f"сервер завершился с кодом {self.proc.returncode}")
            try:
                with urllib.request.urlopen(self.base + "/api/tasks", timeout=1) as r:
                    if r.status == 200:
                        return self
            except (urllib.error.URLError, ConnectionError, OSError):
                time.sleep(0.05)
        self.stop()
        raise RuntimeError("сервер не ответил за 10 с")

    def stop(self):
        if self.proc is not None and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=5)
        self.proc = None

    # ---- HTTP ----
    def request(self, method: str, path: str, body: bytes | None = None, ctype: str | None = None):
        req = urllib.request.Request(self.base + path, data=body, method=method)
        if ctype:
            req.add_header("Content-Type", ctype)
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, dict(r.headers), r.read()
        except urllib.error.HTTPError as exc:
            return exc.code, dict(exc.headers), exc.read()

    def json(self, method: str, path: str, obj=None):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8") if obj is not None else None
        status, _headers, raw = self.request(method, path, body, "application/json" if body else None)
        return status, json.loads(raw.decode("utf-8"))

    def tasks(self, **params):
        query = ("?" + urllib.parse.urlencode(params)) if params else ""
        status, data = self.json("GET", "/api/tasks" + query)
        assert status == 200, (status, data)
        return data["tasks"]

    def import_bytes(self, data: bytes):
        status, _h, raw = self.request("POST", "/api/import", data, "text/csv")
        return status, json.loads(raw.decode("utf-8"))

    def import_file(self, path: Path):
        return self.import_bytes(path.read_bytes())


class E2EBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="sa09-e2e-")
        self.tmp = Path(self._tmp.name)
        self.servers: list[Server] = []

    def tearDown(self):
        for s in self.servers:
            s.stop()
        self._tmp.cleanup()

    def start_server(self, name: str = "a", data_path: Path | None = None, port: int | None = None) -> Server:
        data_path = data_path or (self.tmp / name / "tasks.json")
        if data_path not in [s.data_path for s in self.servers]:
            self.assertFalse(data_path.exists(), "хранилище должно быть новым несуществующим путём")
        srv = Server(data_path, port)
        self.servers.append(srv)
        return srv.start()

    def import_ok(self, srv: Server, path: Path):
        status, rep = srv.import_file(path)
        self.assertEqual(status, 200, rep)
        return rep


class TestScenarios(E2EBase):
    # ---- статика ----
    def test_static_index_and_js(self):
        srv = self.start_server()
        status, headers, body = srv.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertTrue(headers["Content-Type"].startswith("text/html"), headers["Content-Type"])
        self.assertIn(b"<html", body.lower())
        status, headers, body = srv.request("GET", "/static/app.js")
        self.assertEqual(status, 200)
        self.assertIn("javascript", headers["Content-Type"])
        self.assertTrue(body.strip())

    # ---- C1–C6 ----
    def test_C1_create(self):
        srv = self.start_server()
        status, data = srv.json("POST", "/api/tasks", {"title": "Проверить скан"})
        self.assertEqual(status, 201, data)
        self.assertEqual(data["task"]["id"], "C0001")
        self.assertEqual(data["task"]["title"], "Проверить скан")
        self.assertEqual(data["task"]["status"], "новая")
        self.assertEqual(srv.tasks(), [data["task"]])

    def _create_and_patch(self, srv: Server):
        status, data = srv.json("POST", "/api/tasks", {"title": "Проверить скан"})
        self.assertEqual(status, 201, data)
        status, data = srv.json(
            "PATCH", "/api/tasks/" + urllib.parse.quote("C0001"), {"title": "Проверить PDF", "status": "готово"}
        )
        self.assertEqual(status, 200, data)
        return data["task"]

    def test_C2_rename_and_status(self):
        srv = self.start_server()
        task = self._create_and_patch(srv)
        self.assertEqual(task["id"], "C0001")
        self.assertEqual(task["title"], "Проверить PDF")
        self.assertEqual(task["status"], "готово")
        listed = srv.tasks()
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["title"], "Проверить PDF")
        self.assertEqual(listed[0]["status"], "готово")

    def test_C3_restart_persists(self):
        srv = self.start_server()
        self._create_and_patch(srv)
        pid1 = srv.proc.pid
        srv.stop()
        self.assertTrue(srv.data_path.exists())
        stored = json.loads(srv.data_path.read_text(encoding="utf-8"))
        self.assertIn(
            {"id": "C0001", "title": "Проверить PDF", "description": "", "status": "готово"}, stored["tasks"]
        )
        srv.start()  # тот же --data, новый процесс
        self.assertNotEqual(srv.proc.pid, pid1)
        listed = srv.tasks()
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["id"], "C0001")
        self.assertEqual(listed[0]["title"], "Проверить PDF")
        self.assertEqual(listed[0]["status"], "готово")

    def test_C4_blank_title_rejected(self):
        srv = self.start_server()
        srv.json("POST", "/api/tasks", {"title": "Проверить скан"})
        before = len(srv.tasks())
        status, data = srv.json("POST", "/api/tasks", {"title": "   "})
        self.assertEqual(status, 400)
        self.assertEqual(data, {"error": TITLE_EMPTY_ERR})
        self.assertEqual(len(srv.tasks()), before)

    def test_C5_import_valid_twice(self):
        srv = self.start_server()
        rep1 = self.import_ok(srv, VALID_CSV)
        self.assertEqual(rep1["created"], 2)
        self.assertEqual(rep1["updated"], 0)
        self.assertEqual(rep1["errors"], [])
        self.assertEqual(
            rep1["accepted"],
            [{"line": 2, "id": "T001", "action": "created"}, {"line": 3, "id": "T002", "action": "created"}],
        )
        rep2 = self.import_ok(srv, VALID_CSV)
        self.assertEqual(rep2["created"], 0)
        self.assertEqual(rep2["updated"], 2)
        self.assertEqual(rep2["errors"], [])
        self.assertEqual([t["id"] for t in srv.tasks()], ["T001", "T002"])

    def _check_mixed(self, srv: Server):
        rep = self.import_ok(srv, MIXED_CSV)
        self.assertEqual(rep["accepted"], [{"line": 2, "id": "T003", "action": "created"}])
        self.assertEqual(
            rep["errors"],
            [
                {"line": 3, "id": "T004", "error": TITLE_EMPTY_ERR},
                {"line": 4, "id": "T005", "error": STATUS_ARCHIVE_ERR},
            ],
        )
        ids = [t["id"] for t in srv.tasks()]
        self.assertIn("T003", ids)
        self.assertNotIn("T004", ids)
        self.assertNotIn("T005", ids)
        return rep

    def test_C6_import_mixed(self):
        srv = self.start_server()
        self._check_mixed(srv)

    # ---- I1–I5 ----
    def test_I1_search_case_insensitive(self):
        srv = self.start_server()
        self.import_ok(srv, VALID_CSV)
        found = srv.tasks(q="ПРОВЕРИТЬ")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["id"], "T001")
        self.assertEqual(found[0]["title"], "Проверить скан")

    def test_I2_status_filter_and_reset(self):
        srv = self.start_server()
        self.import_ok(srv, VALID_CSV)
        self.import_ok(srv, MIXED_CSV)
        self.assertEqual(
            {t["id"]: t["status"] for t in srv.tasks()},
            {"T001": "новая", "T002": "в работе", "T003": "готово"},
        )
        self.assertEqual([t["id"] for t in srv.tasks(status="готово")], ["T003"])
        self.assertEqual([t["id"] for t in srv.tasks()], ["T001", "T002", "T003"])

    def test_I3_reimport_updates_T001(self):
        srv = self.start_server()
        self.import_ok(srv, VALID_CSV)
        before = len(srv.tasks())
        changed = self.tmp / "import-T001-v2.csv"
        changed.write_text("id,title,description,status\nT001,Проверить скан v2,Все страницы,готово\n", encoding="utf-8")
        rep = self.import_ok(srv, changed)
        self.assertEqual(rep["accepted"], [{"line": 2, "id": "T001", "action": "updated"}])
        self.assertEqual(rep["errors"], [])
        listed = srv.tasks()
        self.assertEqual(len(listed), before)
        t001 = next(t for t in listed if t["id"] == "T001")
        self.assertEqual(
            t001, {"id": "T001", "title": "Проверить скан v2", "description": "Все страницы", "status": "готово"}
        )

    def test_I4_export_import_roundtrip(self):
        a = self.start_server("a")
        self.import_ok(a, VALID_CSV)
        self.import_ok(a, MIXED_CSV)
        a.json("POST", "/api/tasks", {"title": "Проверить, \"кавычки\"", "description": "строка1\nстрока2"})
        list_a = a.tasks()
        status, headers, exported = a.request("GET", "/api/export")
        self.assertEqual(status, 200)
        self.assertTrue(headers["Content-Type"].startswith("text/csv"))
        self.assertIn("attachment", headers.get("Content-Disposition", ""))
        export_file = self.tmp / "tasks.csv"
        export_file.write_bytes(exported)

        b = self.start_server("b")
        self.assertNotEqual(a.port, b.port)
        self.assertNotEqual(a.data_path, b.data_path)
        rep_b = self.import_ok(b, export_file)
        self.assertEqual(rep_b["errors"], [])
        self.assertEqual(rep_b["updated"], 0)
        self.assertEqual(rep_b["created"], len(list_a))
        self.assertTrue(all(x["action"] == "created" for x in rep_b["accepted"]))
        self.assertEqual(b.tasks(), list_a)

        rep_a = self.import_ok(a, export_file)
        self.assertEqual(rep_a["errors"], [])
        self.assertEqual(rep_a["created"], 0)
        self.assertEqual(rep_a["updated"], len(list_a))
        self.assertEqual(a.tasks(), list_a)

    def test_I5_mixed_line_numbers(self):
        srv = self.start_server()
        rep = self._check_mixed(srv)
        # заголовок = строка 1, значит первая запись данных = строка 2
        self.assertEqual([e["line"] for e in rep["errors"]], [3, 4])
        self.assertEqual(rep["created"], 1)
        self.assertEqual(rep["updated"], 0)

    # ---- отрицательная проверка: корректная строка не теряется ----
    def test_NEG_good_row_kept(self):
        srv = self.start_server()
        csv_file = self.tmp / "bad-then-good.csv"
        csv_file.write_text(
            "id,title,description,status\nB1,,пусто,новая\nG1,Хорошая строка,после плохой,новая\n", encoding="utf-8"
        )
        rep = self.import_ok(srv, csv_file)
        self.assertEqual(rep["errors"], [{"line": 2, "id": "B1", "error": TITLE_EMPTY_ERR}])
        self.assertEqual(rep["accepted"], [{"line": 3, "id": "G1", "action": "created"}])
        ids = [t["id"] for t in srv.tasks()]
        self.assertIn("G1", ids)
        self.assertNotIn("B1", ids)


if __name__ == "__main__":
    unittest.main()
