"""Тесты хранилища и smoke-тест HTTP (контракт SA09). Запуск: python3 -m unittest discover -s tests"""

import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

SA09 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SA09 / "app"))
INPUT = SA09.parents[2] / "materials" / "H03" / "input"

from store import (  # noqa: E402
    FileFormatError,
    NotFoundError,
    TaskStore,
    ValidationError,
)
import server  # noqa: E402

VALID = (INPUT / "import-valid.csv").read_bytes()
MIXED = (INPUT / "import-mixed.csv").read_bytes()
STATUS_ARCHIVE = "Недопустимый статус «архив»: разрешены «новая», «в работе», «готово»"


class StoreTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "sub" / "tasks.json"
        self.store = TaskStore(self.path)

    def tearDown(self):
        self._tmp.cleanup()

    def reopen(self):
        return TaskStore(self.path)


class CreateTests(StoreTestCase):
    def test_create_defaults(self):
        task = self.store.create("  Проверить скан  ", "Первые три страницы")
        self.assertEqual(
            task,
            {"id": "C0001", "title": "Проверить скан", "description": "Первые три страницы", "status": "новая"},
        )
        self.assertEqual(self.store.create("Вторая")["id"], "C0002")
        self.assertEqual(self.store.create("Третья")["description"], "")

    def test_blank_title_rejected_nothing_saved(self):
        with self.assertRaises(ValidationError) as cm:
            self.store.create("   ")
        self.assertEqual(cm.exception.message, "Название не может быть пустым")
        self.assertEqual(self.store.list(), [])
        self.assertFalse(self.path.exists())

    def test_title_length(self):
        self.store.create("я" * 100)
        with self.assertRaises(ValidationError) as cm:
            self.store.create("я" * 101)
        self.assertEqual(cm.exception.message, "Название длиннее 100 символов")
        self.assertEqual(len(self.store.list()), 1)


class UpdateTests(StoreTestCase):
    def setUp(self):
        super().setUp()
        self.store.create("Проверить скан", "Первые три страницы")

    def test_update_fields(self):
        task = self.store.update("C0001", {"title": " Проверить PDF ", "status": "готово"})
        self.assertEqual(task["title"], "Проверить PDF")
        self.assertEqual(task["status"], "готово")
        task = self.store.update("C0001", {"description": "Все страницы"})
        self.assertEqual(task["description"], "Все страницы")
        self.assertEqual(self.reopen().list(), [task])

    def test_invalid_status_leaves_record(self):
        before = self.store.list()
        with self.assertRaises(ValidationError) as cm:
            self.store.update("C0001", {"title": "Новое", "status": "архив"})
        self.assertEqual(cm.exception.message, STATUS_ARCHIVE)
        self.assertEqual(self.store.list(), before)
        self.assertEqual(self.reopen().list(), before)

    def test_unknown_id(self):
        with self.assertRaises(NotFoundError) as cm:
            self.store.update("X999", {"title": "a"})
        self.assertEqual(cm.exception.message, "Заявка с id «X999» не найдена")

    def test_no_fields(self):
        with self.assertRaises(ValidationError) as cm:
            self.store.update("C0001", {"id": "Z"})
        self.assertEqual(cm.exception.message, "Нет полей для изменения")


class PersistenceTests(StoreTestCase):
    def test_new_instance_sees_data(self):
        self.store.create("Проверить скан")
        self.store.import_csv(VALID)
        self.assertEqual(self.reopen().list(), self.store.list())
        self.assertEqual([t["id"] for t in self.reopen().list()], ["C0001", "T001", "T002"])
        self.assertFalse(self.path.with_name("tasks.json.tmp").exists())
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(len(raw["tasks"]), 3)


class SearchTests(StoreTestCase):
    def setUp(self):
        super().setUp()
        self.store.import_csv(VALID)
        self.store.import_csv(MIXED)

    def test_search_case_insensitive(self):
        self.assertEqual([t["id"] for t in self.store.list(q="ПРОВЕРИТЬ")], ["T001"])
        self.assertEqual([t["id"] for t in self.store.list(q="  таблицу ")], ["T002"])

    def test_status_filter(self):
        self.assertEqual([t["id"] for t in self.store.list(status="готово")], ["T003"])
        self.assertEqual(len(self.store.list()), 3)
        self.assertEqual(self.store.list(q="проверить", status="готово"), [])
        with self.assertRaises(ValidationError):
            self.store.list(status="архив")


class ImportTests(StoreTestCase):
    def test_valid_twice(self):
        r1 = self.store.import_csv(VALID)
        self.assertEqual(
            r1,
            {
                "accepted": [
                    {"line": 2, "id": "T001", "action": "created"},
                    {"line": 3, "id": "T002", "action": "created"},
                ],
                "errors": [],
                "created": 2,
                "updated": 0,
            },
        )
        r2 = self.store.import_csv(VALID)
        self.assertEqual((r2["created"], r2["updated"], r2["errors"]), (0, 2, []))
        self.assertEqual([a["action"] for a in r2["accepted"]], ["updated", "updated"])
        self.assertEqual([t["id"] for t in self.reopen().list()], ["T001", "T002"])

    def test_mixed(self):
        r = self.store.import_csv(MIXED)
        self.assertEqual(r["accepted"], [{"line": 2, "id": "T003", "action": "created"}])
        self.assertEqual(
            r["errors"],
            [
                {"line": 3, "id": "T004", "error": "Название не может быть пустым"},
                {"line": 4, "id": "T005", "error": STATUS_ARCHIVE},
            ],
        )
        self.assertEqual((r["created"], r["updated"]), (1, 0))
        self.assertEqual([t["id"] for t in self.reopen().list()], ["T003"])

    def test_good_row_after_bad_not_lost(self):
        data = "id,title,description,status\nT010,,плохая,новая\nT011,Хорошая,,в работе\n".encode()
        r = self.store.import_csv(data)
        self.assertEqual(r["errors"], [{"line": 2, "id": "T010", "error": "Название не может быть пустым"}])
        self.assertEqual(r["accepted"], [{"line": 3, "id": "T011", "action": "created"}])
        self.assertEqual([t["id"] for t in self.reopen().list()], ["T011"])

    def test_row_checks_order(self):
        data = (
            "id,title,description,status\n"
            "T1,a,b\n"
            "  ,a,b,новая\n"
            "T2," + "x" * 101 + ",,новая\n"
            "T3,a,,\n"
            "\n"
            "T4,a,,  готово \n"
        ).encode()
        r = self.store.import_csv(data)
        self.assertEqual(
            r["errors"],
            [
                {"line": 2, "id": "T1", "error": "Ожидается 4 поля, получено 3"},
                {"line": 3, "id": "", "error": "Не указан id"},
                {"line": 4, "id": "T2", "error": "Название длиннее 100 символов"},
                {"line": 5, "id": "T3", "error": "Недопустимый статус «»: разрешены «новая», «в работе», «готово»"},
            ],
        )
        self.assertEqual(r["accepted"], [{"line": 7, "id": "T4", "action": "created"}])
        self.assertEqual(self.store.list()[0]["status"], "готово")

    def test_reimport_updates_t001(self):
        self.store.import_csv(VALID)
        data = "id,title,description,status\nT001,Проверить скан v2,Все страницы,готово\n".encode()
        r = self.store.import_csv(data)
        self.assertEqual(r["accepted"], [{"line": 2, "id": "T001", "action": "updated"}])
        tasks = self.reopen().list()
        self.assertEqual(len(tasks), 2)
        self.assertEqual(
            tasks[0], {"id": "T001", "title": "Проверить скан v2", "description": "Все страницы", "status": "готово"}
        )

    def test_bom_accepted(self):
        r = self.store.import_csv(b"\xef\xbb\xbf" + VALID)
        self.assertEqual(r["created"], 2)

    def test_file_errors(self):
        self.store.import_csv(VALID)
        before = self.path.read_bytes()
        cases = {
            "Файл не в кодировке UTF-8": "id,title,description,status\nT9,Тест,,новая\n".encode("cp1251"),
            "Файл пуст": b"",
            "Неверный заголовок: ожидается id,title,description,status": "id,name,description,status\nT9,a,,новая\n".encode(),
        }
        for message, data in cases.items():
            with self.subTest(message=message):
                with self.assertRaises(FileFormatError) as cm:
                    self.store.import_csv(data)
                self.assertEqual(cm.exception.message, message)
                self.assertEqual(self.path.read_bytes(), before)
                self.assertEqual(len(self.store.list()), 2)


class ExportTests(StoreTestCase):
    def test_roundtrip(self):
        self.store.import_csv(VALID)
        self.store.import_csv(MIXED)
        self.store.create("Проверить скан", "ручная")
        csv_text = self.store.export_csv()
        self.assertTrue(csv_text.startswith("id,title,description,status\n"))

        other = TaskStore(Path(self._tmp.name) / "b" / "tasks.json")
        r = other.import_csv(csv_text.encode("utf-8"))
        self.assertEqual(r["errors"], [])
        self.assertEqual(r["created"], 4)
        self.assertEqual(other.list(), self.store.list())

        r = self.store.import_csv(csv_text.encode("utf-8"))
        self.assertEqual((r["created"], r["updated"], r["errors"]), (0, 4, []))
        self.assertEqual(len(self.store.list()), 4)

    def test_special_characters_roundtrip(self):
        self.store.create("Запятая, и \"кавычки\"", "строка 1\nстрока 2, \"цитата\"")
        self.store.update("C0001", {"status": "в работе"})
        csv_text = self.store.export_csv()
        self.assertIn('"Запятая, и ""кавычки"""', csv_text)
        other = TaskStore(Path(self._tmp.name) / "c.json")
        r = other.import_csv(csv_text.encode("utf-8"))
        self.assertEqual(r["accepted"], [{"line": 2, "id": "C0001", "action": "created"}])
        self.assertEqual(other.list(), self.store.list())


class HttpSmokeTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        store = TaskStore(Path(self._tmp.name) / "data" / "tasks.json")
        self.httpd = server.make_server(store, 0)
        self.httpd.RequestHandlerClass.log_message = lambda *args: None
        self.base = "http://127.0.0.1:%d" % self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=5)
        self._tmp.cleanup()

    def request(self, method, path, body=None, ctype="application/json"):
        req = urllib.request.Request(self.base + path, data=body, method=method)
        if body is not None:
            req.add_header("Content-Type", ctype)
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, resp.headers, resp.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers, exc.read()

    def test_api(self):
        status, headers, body = self.request("GET", "/api/tasks")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "application/json; charset=utf-8")
        self.assertEqual(json.loads(body), {"tasks": []})

        status, _, body = self.request("POST", "/api/tasks", json.dumps({"title": "Проверить скан"}).encode())
        self.assertEqual(status, 201)
        self.assertEqual(json.loads(body)["task"]["id"], "C0001")

        status, _, body = self.request("POST", "/api/tasks", json.dumps({"title": "   "}).encode())
        self.assertEqual((status, json.loads(body)), (400, {"error": "Название не может быть пустым"}))

        status, _, body = self.request("POST", "/api/import", MIXED, "text/csv")
        self.assertEqual(status, 200)
        report = json.loads(body)
        self.assertEqual(report["created"], 1)
        self.assertEqual([e["line"] for e in report["errors"]], [3, 4])

        status, _, body = self.request("POST", "/api/import", b"", "text/csv")
        self.assertEqual((status, json.loads(body)), (400, {"error": "Файл пуст"}))

        status, _, body = self.request("PATCH", "/api/tasks/C0001", json.dumps({"status": "готово"}).encode())
        self.assertEqual((status, json.loads(body)["task"]["status"]), (200, "готово"))

        status, _, body = self.request("GET", "/api/tasks?status=%D0%B3%D0%BE%D1%82%D0%BE%D0%B2%D0%BE")
        self.assertEqual([t["id"] for t in json.loads(body)["tasks"]], ["C0001", "T003"])

        status, headers, body = self.request("GET", "/api/export")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn('filename="tasks.csv"', headers["Content-Disposition"])
        self.assertEqual(
            body.decode("utf-8"),
            "id,title,description,status\nC0001,Проверить скан,,готово\nT003,Сверить итог,,готово\n",
        )

        status, _, body = self.request("GET", "/nope")
        self.assertEqual((status, json.loads(body)), (404, {"error": "Не найдено"}))
        status, _, body = self.request("GET", "/static/../store.py")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
