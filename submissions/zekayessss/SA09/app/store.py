"""Хранилище заявок: валидация, JSON-файл, импорт и экспорт CSV (контракт SA09, разделы 1, 2, 4, 5, 8)."""

from __future__ import annotations

import csv
import io
import json
import os
import re
from pathlib import Path

STATUSES = ("новая", "в работе", "готово")
DEFAULT_STATUS = "новая"
TITLE_MAX = 100
CSV_HEADER = ["id", "title", "description", "status"]
DEFAULT_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "tasks.json"

MSG_TITLE_EMPTY = "Название не может быть пустым"
MSG_TITLE_LONG = "Название длиннее 100 символов"
MSG_ID_EMPTY = "Не указан id"
MSG_NO_FIELDS = "Нет полей для изменения"
MSG_NOT_UTF8 = "Файл не в кодировке UTF-8"
MSG_EMPTY_FILE = "Файл пуст"
MSG_BAD_HEADER = "Неверный заголовок: ожидается id,title,description,status"


class StoreError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ValidationError(StoreError):
    pass


class NotFoundError(StoreError):
    pass


class FileFormatError(StoreError):
    pass


class CorruptDataError(StoreError):
    """Файл данных существует, но не разбирается (РК-8)."""


def status_error(value: str) -> str:
    return f"Недопустимый статус «{value}»: разрешены «новая», «в работе», «готово»"


def columns_error(n: int) -> str:
    return f"Ожидается 4 поля, получено {n}"


def not_found_error(task_id: str) -> str:
    return f"Заявка с id «{task_id}» не найдена"


def type_error(field: str) -> str:
    return f"Поле {field} должно быть строкой"


def normalize_title(title) -> str:
    if title is None:
        raise ValidationError(MSG_TITLE_EMPTY)
    if not isinstance(title, str):
        raise ValidationError(type_error("title"))
    title = title.strip()
    if not title:
        raise ValidationError(MSG_TITLE_EMPTY)
    if len(title) > TITLE_MAX:
        raise ValidationError(MSG_TITLE_LONG)
    return title


def normalize_status(status) -> str:
    if not isinstance(status, str):
        raise ValidationError(type_error("status"))
    status = status.strip()
    if status not in STATUSES:
        raise ValidationError(status_error(status))
    return status


def normalize_description(description) -> str:
    if description is None:
        return ""
    if not isinstance(description, str):
        raise ValidationError(type_error("description"))
    return description


_C_ID = re.compile(r"^C(\d+)$")


class TaskStore:
    def __init__(self, path=None):
        self.path = Path(path) if path is not None else DEFAULT_DATA_PATH
        self.tasks: list[dict] = self._load()

    # ---- хранение ----
    def _load(self) -> list[dict]:
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CorruptDataError(str(exc)) from exc
        if not isinstance(raw, dict) or "tasks" not in raw:
            raise CorruptDataError("нет ключа tasks")
        tasks = raw["tasks"]
        if not isinstance(tasks, list) or not all(isinstance(t, dict) for t in tasks):
            raise CorruptDataError("tasks должен быть списком объектов")
        return [
            {
                "id": str(t.get("id", "")),
                "title": str(t.get("title", "")),
                "description": str(t.get("description", "")),
                "status": str(t.get("status", "")),
            }
            for t in tasks
        ]

    def _save(self, tasks: list[dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(self.path.name + ".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"tasks": tasks}, fh, ensure_ascii=False, indent=2)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, self.path)
        self.tasks = tasks

    def _index(self, task_id: str, tasks=None) -> int:
        for i, t in enumerate(self.tasks if tasks is None else tasks):
            if t["id"] == task_id:
                return i
        return -1

    def _next_id(self) -> str:
        nums = [int(m.group(1)) for t in self.tasks if (m := _C_ID.match(t["id"]))]
        n = max(nums, default=0) + 1
        ids = {t["id"] for t in self.tasks}
        while f"C{n:04d}" in ids:
            n += 1
        return f"C{n:04d}"

    # ---- операции ----
    def list(self, q: str = "", status: str = "") -> list[dict]:
        q = (q or "").strip().casefold()
        status = status or ""
        if status and status not in STATUSES:
            raise ValidationError(status_error(status))
        return [
            dict(t)
            for t in self.tasks
            if (not q or q in t["title"].casefold()) and (not status or t["status"] == status)
        ]

    def get(self, task_id: str) -> dict:
        i = self._index(task_id)
        if i < 0:
            raise NotFoundError(not_found_error(task_id))
        return dict(self.tasks[i])

    def create(self, title, description="") -> dict:
        task = {
            "id": self._next_id(),
            "title": normalize_title(title),
            "description": normalize_description(description),
            "status": DEFAULT_STATUS,
        }
        self._save(self.tasks + [task])
        return dict(task)

    def update(self, task_id: str, fields: dict) -> dict:
        i = self._index(task_id)
        if i < 0:
            raise NotFoundError(not_found_error(task_id))
        changes = {}
        if "title" in fields:
            changes["title"] = normalize_title(fields["title"])
        if "description" in fields:
            if not isinstance(fields["description"], str):
                raise ValidationError(type_error("description"))
            changes["description"] = fields["description"]
        if "status" in fields:
            changes["status"] = normalize_status(fields["status"])
        if not changes:
            raise ValidationError(MSG_NO_FIELDS)
        tasks = [dict(t) for t in self.tasks]
        tasks[i].update(changes)
        self._save(tasks)
        return dict(tasks[i])

    def import_csv(self, data: bytes) -> dict:
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise FileFormatError(MSG_NOT_UTF8)
        try:
            rows = list(enumerate(csv.reader(io.StringIO(text, newline="")), start=1))
        except csv.Error as exc:
            raise FileFormatError(f"Ошибка разбора CSV: {exc}")
        if not rows:
            raise FileFormatError(MSG_EMPTY_FILE)
        _, header = rows[0]
        if [h.strip() for h in header] != CSV_HEADER:
            raise FileFormatError(MSG_BAD_HEADER)

        tasks = [dict(t) for t in self.tasks]
        accepted, errors = [], []
        created = updated = 0
        for line, row in rows[1:]:
            if not row:
                continue
            row_id = row[0].strip() if row else ""
            error = self._check_row(row)
            if error:
                errors.append({"line": line, "id": row_id, "error": error})
                continue
            values = {
                "title": row[1].strip(),
                "description": row[2],
                "status": row[3].strip(),
            }
            i = self._index(row_id, tasks)
            if i >= 0:
                tasks[i].update(values)
                action = "updated"
                updated += 1
            else:
                tasks.append({"id": row_id, **values})
                action = "created"
                created += 1
            accepted.append({"line": line, "id": row_id, "action": action})
        if accepted:
            self._save(tasks)
        return {"accepted": accepted, "errors": errors, "created": created, "updated": updated}

    @staticmethod
    def _check_row(row: list) -> str | None:
        if len(row) != 4:
            return columns_error(len(row))
        row_id, title, _description, status = row
        if not row_id.strip():
            return MSG_ID_EMPTY
        title = title.strip()
        if not title:
            return MSG_TITLE_EMPTY
        if len(title) > TITLE_MAX:
            return MSG_TITLE_LONG
        if status.strip() not in STATUSES:
            return status_error(status.strip())
        return None

    def export_csv(self) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        writer.writerow(CSV_HEADER)
        for t in self.tasks:
            writer.writerow([t["id"], t["title"], t["description"], t["status"]])
        return buf.getvalue()
