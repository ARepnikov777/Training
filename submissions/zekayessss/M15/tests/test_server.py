"""Регрессионный тест страниц стенда: ссылка «Контакты» и соседние страницы.

Поднимает настоящий serve.py указанной папки сайта на свободном порту.
Сайт копируется во временную папку, чтобы _state.json не попадал в решение.

Запуск: python3 tests/test_server.py <папка-сайта>   (по умолчанию result/site)
"""

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

SITE = Path(
    sys.argv.pop(1) if len(sys.argv) > 1 else Path(__file__).parent.parent / "result" / "site"
).resolve()


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class ServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        site = Path(cls.tmp) / "site"
        shutil.copytree(SITE, site)
        cls.port = free_port()
        cls.proc = subprocess.Popen(
            [sys.executable, str(site / "serve.py"), "--port", str(cls.port), "--site", str(site)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(50):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{cls.port}/", timeout=1)
                break
            except OSError:
                time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.wait(5)
        shutil.rmtree(cls.tmp)

    def get(self, path):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}", timeout=5) as r:
                return r.status, r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8")

    def test_s3_contacts_link_opens_contacts_page(self):
        """S3: ссылка «Контакты» на /shop ведёт на /contacts, страница отвечает 200."""
        status, html = self.get("/shop")
        self.assertEqual(status, 200)
        links = re.findall(r'<a href="([^"]+)">Контакты</a>', html)
        self.assertEqual(links, ["/contacts"], f"ссылка «Контакты» ведёт на {links}")
        status, html = self.get(links[0])
        self.assertEqual(status, 200, f"{links[0]} отвечает {status}")
        self.assertIn("<h1>Контакты</h1>", html)

    def test_neighbor_pages_available(self):
        """Соседние страницы стенда доступны, как и до исправления."""
        for path in ["/", "/catalog", "/register", "/tickets", "/contacts", "/shop", "/app.js", "/style.css"]:
            with self.subTest(path=path):
                self.assertEqual(self.get(path)[0], 200)

    def test_unknown_page_still_404(self):
        self.assertEqual(self.get("/missing")[0], 404)

    def test_config_mode_unchanged(self):
        """Исправление в коде, а не переключением режима: config остаётся shop-buggy."""
        status, body = self.get("/api/config")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["mode"], "shop-buggy")


if __name__ == "__main__":
    print(f"Сайт: {os.path.relpath(SITE)}", flush=True)
    unittest.main(verbosity=2)
