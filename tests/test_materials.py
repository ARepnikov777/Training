"""Проверки целостности учебных исходников, а не решений заданий."""

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))


def test_local_server_contract():
    spec = importlib.util.spec_from_file_location(
        "course_server", ROOT / "tools" / "serve.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert (
        module.registration_errors(
            {"name": "Анна", "email": "anna@example.test", "consent": True}
        )
        == []
    )
    assert "email" in module.registration_errors(
        {"name": "Анна", "email": "bad", "consent": True}
    )
    assert "name" in module.registration_errors(
        {"name": "x" * 81, "email": "a@example.test", "consent": True}
    )
    assert (
        module.registration_errors(
            {"name": "x" * 80, "email": "a@example.test", "consent": True}
        )
        == []
    )
    assert "consent" in module.registration_errors(
        {"name": "Анна", "email": "a@example.test", "consent": False}
    )


def test_all_45_packs_are_self_contained():
    import zipfile

    packs = ROOT / "materials"
    expected = {f"{prefix}{n:02}" for prefix in "EMH" for n in range(1, 16)}
    assert packs.exists(), "Материалы ещё не созданы"
    assert {p.name for p in packs.iterdir() if p.is_dir()} == expected
    for code in sorted(expected):
        p = packs / code
        manifest = json.loads((p / "manifest.json").read_text())
        assert manifest["code"] == code
        assert manifest["inputs"] and manifest["checks"]
        for relative in manifest["inputs"] + manifest["checks"]:
            assert (p / relative).is_file(), (code, relative)
        readme = (p / "README.md").read_text()
        assert "преподаватель выдаст" not in readme.lower()
        with zipfile.ZipFile(ROOT / "downloads" / f"{code}.zip") as z:
            assert z.testzip() is None
            assert f"{code}/README.md" in z.namelist()
            assert all(
                not name.startswith("/") and ".." not in Path(name).parts
                for name in z.namelist()
            )


def test_archive_has_real_duplicates_and_name_conflicts():
    import zipfile

    with zipfile.ZipFile(ROOT / "materials" / "H01" / "input" / "archive.zip") as z:
        assert z.read("incoming/report.txt") == z.read("backup/report-copy.txt")
        assert z.read("incoming/report.txt") != z.read("other/report.txt")
        assert len(z.namelist()) == 18


def test_scans_have_no_embedded_text():
    from pypdf import PdfReader

    for code in ["E04", "M04"]:
        reader = PdfReader(ROOT / "materials" / code / "input" / "scan.pdf")
        assert len(reader.pages) == 3
        assert all(not p.extract_text().strip() for p in reader.pages)
        assert all(len(p.images) > 0 for p in reader.pages)


def test_browser_catalog_counts():
    catalog = json.loads(
        (ROOT / "materials" / "H13" / "input" / "site" / "catalog.json").read_text()
    )
    assert len(catalog) == 50
    assert len({r["id"] for r in catalog}) == 50
    assert len([r for r in catalog if r["category"] == "laptop"]) == 20


def test_checksums_match_every_file_after_rebuild():
    import hashlib

    for pack in (ROOT / "materials").iterdir():
        manifest = json.loads((pack / "checksums.json").read_text())
        assert "checksums.json" not in manifest
        for name, expected in manifest.items():
            assert hashlib.sha256((pack / name).read_bytes()).hexdigest() == expected, (
                pack.name,
                name,
            )


def test_fixed_totals_match_input_values():
    import csv

    expense_file = ROOT / "materials/E08/input/expenses.csv"
    with expense_file.open() as f:
        rows = list(csv.DictReader(f))
    assert sum(int(r["amount_KZT"]) for r in rows) == 235000
    for code in ["M06", "H06"]:
        info = json.loads(
            (ROOT / "materials" / code / "input/audio-info.json").read_text()
        )
        assert 600 <= info["duration_seconds"] <= 900
        assert (ROOT / "materials" / code / "input/meeting.mp3").stat().st_size > 100000


def test_http_form_and_ticket_lifecycle(tmp_path):
    import threading
    from http.server import ThreadingHTTPServer
    from urllib.error import HTTPError
    from urllib.request import Request, urlopen

    spec = importlib.util.spec_from_file_location(
        "course_server_http", ROOT / "tools/serve.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.Handler.site = tmp_path
    (tmp_path / "config.json").write_text('{"mode":"normal"}')
    server = ThreadingHTTPServer(("127.0.0.1", 0), module.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"

    def call(path, method="GET", data=None):
        request = Request(
            base + path,
            data=None if data is None else json.dumps(data).encode(),
            method=method,
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=5) as response:
            return response.status, json.load(response)

    try:
        participant = {
            "name": "Анна",
            "email": "a@example.test",
            "consent": True,
            "token": "test-token",
        }
        status, registered = call("/api/register", "POST", participant)
        assert status == 201
        status, repeated = call("/api/register", "POST", participant)
        assert status == 200 and repeated["id"] == registered["id"]
        assert len(call("/api/registrations")[1]) == 1
        try:
            call("/api/register", "POST", {**participant, "email": "invalid"})
        except HTTPError as error:
            assert error.code == 400
        else:
            raise AssertionError("Неверный email принят в исправной форме")
        _, ticket = call(
            "/api/tickets", "POST", {"title": "PDF", "description": "Страницы"}
        )
        assert ticket["status"] == "новая"
        _, updated = call(
            "/api/tickets/" + ticket["id"],
            "PUT",
            {"title": "PDF и таблица", "status": "в работе"},
        )
        assert updated["status"] == "в работе"
        assert call("/api/tickets?q=" + ticket["id"])[1][0]["title"] == "PDF и таблица"
        state = json.loads((tmp_path / "_state.json").read_text())
        assert state["tickets"][0]["status"] == "в работе"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_pack_does_not_require_runtime_state():
    import zipfile

    for pack in (ROOT / "materials").iterdir():
        manifest = json.loads((pack / "manifest.json").read_text())
        assert all(
            "_state.json" not in name and "__pycache__" not in name
            for name in manifest["inputs"]
        )
        with zipfile.ZipFile(ROOT / "downloads" / (pack.name + ".zip")) as z:
            names = set(z.namelist())
            assert all(
                pack.name + "/" + name in names
                for name in manifest["inputs"] + manifest["checks"]
            )
