"""Collect the synthetic catalog through an Orca browser tab."""
import argparse
import csv
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import uuid
from urllib.parse import parse_qs, urlencode, urlparse

ORCA = r"C:/Users/lyudm/AppData/Local/Programs/orca/resources/bin/orca.exe"
FIELDS = ["id", "name", "category", "price", "currency", "supplier", "availability", "ram_GB", "ssd_GB", "screen_inches", "source_url"]
PAGES = [1, 2, 3, 4, 5]

class CollectorError(Exception):
    pass

def atomic_text(path, text):
    temporary = path.with_name(path.name + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()

def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"

def load_checkpoint(path, base):
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(state, dict) or state.get("schema_version") != 1 or state.get("base_url") != base:
            raise ValueError("schema version or base URL mismatch")
        records, done, pending, errors = (state[k] for k in ("records", "completed_pages", "pending_pages", "errors"))
        if not isinstance(records, dict) or not isinstance(done, list) or not isinstance(pending, list) or not isinstance(errors, list):
            raise ValueError("invalid checkpoint types")
        if any(type(p) is not int for p in done + pending) or sorted(done + pending) != PAGES or len(set(done + pending)) != 5:
            raise ValueError("invalid page lists")
        if type(state.get("complete")) is not bool or state["complete"] != (not pending and len(records) == 50):
            raise ValueError("inconsistent completion")
        if len(records) > 50 or len(records) < 10 * len(done):
            raise ValueError("inconsistent record count")
        for key, record in records.items():
            if not isinstance(record, dict) or set(record) != set(FIELDS) or record["id"] != key or not isinstance(key, str) or not key or key == "None":
                raise ValueError("invalid record")
            if any(not isinstance(record[field], str) or record[field] == "None" for field in ("name", "category", "currency", "supplier", "source_url")):
                raise ValueError("invalid text field")
            if record["availability"] == "None":
                record["availability"] = None
            if record["availability"] is not None and not isinstance(record["availability"], str):
                raise ValueError("invalid availability")
            if type(record["price"]) is not int or any(record[field] is not None and type(record[field]) is not int for field in ("ram_GB", "ssd_GB")):
                raise ValueError("invalid integer field")
            screen = record["screen_inches"]
            if screen is not None:
                if type(screen) not in (int, float) or not math.isfinite(screen):
                    raise ValueError("invalid screen_inches")
                record["screen_inches"] = float(screen)
            source = urlparse(record["source_url"])
            if source.scheme not in ("http", "https") or source.netloc != urlparse(base).netloc:
                raise ValueError("invalid source URL")
        if any(not isinstance(e, dict) or not isinstance(e.get("url"), str) or type(e.get("status")) is not int or type(e.get("resolved")) is not bool for e in errors):
            raise ValueError("invalid errors")
        return state
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise CollectorError(f"Invalid checkpoint: {exc}") from exc

def export(output, state):
    records = list(state["records"].values())
    atomic_text(output / "products.json", json_text(records))
    import io
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    atomic_text(output / "products.csv", buf.getvalue())
    atomic_text(output / "errors.json", json_text(state["errors"]))

def save(output, state):
    atomic_text(output / "checkpoint.json", json_text(state))
    export(output, state)

class OrcaBrowser:
    def __init__(self, page=None):
        self.page = page

    def call(self, *args):
        try:
            result = subprocess.run([ORCA, *args, "--json"], capture_output=True, text=True, encoding="utf-8", timeout=45, check=True)
            data = json.loads(result.stdout)
            if not data.get("ok"):
                raise CollectorError(f"Orca failed: {data.get('error')}")
            return data["result"]
        except (OSError, subprocess.SubprocessError, ValueError, KeyError) as exc:
            raise CollectorError(f"Orca invocation failed: {exc}") from exc

    def navigate(self, url):
        if self.page is None:
            result = self.call("tab", "create", "--url", "about:blank")
            self.page = result.get("browserPageId")
            if not self.page:
                raise CollectorError("Orca did not return a browser page ID")
        navigation = self.call("goto", "--page", self.page, "--url", url)
        if navigation.get("effects", {}).get("loading") is True:
            self.call("wait", "--page", self.page, "--load", "load")
        expression = """(() => ({status: performance.getEntriesByType('navigation')[0]?.responseStatus, url: location.href, links: Array.from(document.querySelectorAll('table tr td a[href]'), a => a.href), fields: Object.fromEntries(Array.from(document.querySelectorAll('dl dt'), dt => [dt.textContent.trim(), dt.nextElementSibling?.textContent.trim()]))}))()"""
        result = self.call("eval", "--page", self.page, "--expression", expression)
        try:
            value = json.loads(result["result"])
            if not isinstance(value, dict) or type(value.get("status")) is not int:
                raise ValueError("missing navigation status")
            if value.get("url") != url:
                raise ValueError(f"navigation URL mismatch: expected {url}, got {value.get('url')}")
            return value
        except (KeyError, TypeError, ValueError) as exc:
            raise CollectorError(f"Invalid Orca eval response: {exc}") from exc

def normalize_record(data):
    fields = data.get("fields")
    if not isinstance(fields, dict) or set(fields) != set(FIELDS[:-1]):
        raise CollectorError("Card has unexpected fields")
    record = dict(fields)
    for key in ("availability", "ram_GB", "ssd_GB", "screen_inches"):
        if record[key] == "None":
            record[key] = None
    if any(not isinstance(record[key], str) or record[key] == "None" for key in ("id", "name", "category", "currency", "supplier")):
        raise CollectorError("Invalid required text field")
    if record["availability"] is not None and not isinstance(record["availability"], str):
        raise CollectorError("Invalid availability")
    try:
        record["price"] = int(record["price"])
        for key in ("ram_GB", "ssd_GB"):
            if record[key] is not None:
                record[key] = int(record[key])
        if record["screen_inches"] is not None:
            record["screen_inches"] = float(record["screen_inches"])
            if not math.isfinite(record["screen_inches"]):
                raise ValueError("non-finite number")
    except (TypeError, ValueError) as exc:
        raise CollectorError(f"Invalid numeric field: {exc}") from exc
    record["source_url"] = data.get("url")
    if not isinstance(record["id"], str) or not record["id"] or not isinstance(record["source_url"], str) or not urlparse(record["source_url"]).netloc:
        raise CollectorError("Card has invalid id or URL")
    return record

def collect(base_url, output, browser, fail_third=False):
    output = Path(output)
    base = base_url.rstrip("/")
    checkpoint = output / "checkpoint.json"
    try:
        parsed = urlparse(base)
        if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.path or parsed.query or parsed.fragment:
            raise CollectorError("base URL must be an HTTP(S) origin")
        resumed = checkpoint.exists()
        state = load_checkpoint(checkpoint, base) if resumed else {"schema_version": 1, "base_url": base, "records": {}, "completed_pages": [], "pending_pages": PAGES.copy(), "errors": [], "complete": False}
    except CollectorError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    output.mkdir(parents=True, exist_ok=True)
    run_id = uuid.uuid4().hex
    def event(kind, **data):
        entry = {"timestamp": datetime.now(timezone.utc).isoformat(), "pid": os.getpid(), "run_id": run_id, "event": kind, **data}
        with (output / "events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry, ensure_ascii=False) + "\n")
    try:
        if resumed:
            event("resume", count=len(state["records"]))
        if state["complete"]:
            export(output, state)
            event("exit", code=0, count=len(state["records"]))
            return 0
        save(output, state)
        for page in list(state["pending_pages"]):
            query = {"page": page}
            if fail_third and page == 3:
                query["fail"] = 1
            url = base + "/catalog?" + urlencode(query)
            result = browser.navigate(url)
            status = result.get("status")
            event("navigation", url=url, status=status, count=len(state["records"]))
            if status != 200:
                if type(status) is not int:
                    raise CollectorError("Missing HTTP status")
                state["errors"].append({"url": url, "status": status, "resolved": False})
                save(output, state)
                code = 2 if status == 503 else 1
                event("exit", code=code, count=len(state["records"]))
                return code
            links = result.get("links")
            if not isinstance(links, list) or len(links) != 10 or len(set(links)) != 10:
                raise CollectorError(f"Page {page} does not have 10 unique cards")
            page_ids = set()
            for link in links:
                if not isinstance(link, str) or urlparse(link).netloc != parsed.netloc:
                    raise CollectorError("Invalid card link")
                card = browser.navigate(link)
                event("navigation", url=link, status=card.get("status"), count=len(state["records"]))
                if card.get("status") != 200:
                    raise CollectorError(f"Card HTTP status {card.get('status')} at {link}")
                record = normalize_record(card)
                previous = state["records"].get(record["id"])
                if record["id"] in page_ids or (previous is not None and previous["source_url"] != record["source_url"]):
                    raise CollectorError(f"Duplicate product ID: {record['id']}")
                page_ids.add(record["id"])
                state["records"][record["id"]] = record
                save(output, state)
            state["completed_pages"].append(page)
            state["pending_pages"].remove(page)
            for error in state["errors"]:
                q = urlparse(error["url"])
                if q.path == "/catalog" and parse_qs(q.query).get("page") == [str(page)]:
                    error["resolved"] = True
            state["complete"] = not state["pending_pages"] and len(state["records"]) == 50
            save(output, state)
            event("page_complete", url=url, status=status, count=len(state["records"]), page=page)
        code = 0 if state["complete"] else 1
        event("exit", code=code, count=len(state["records"]))
        return code
    except (CollectorError, OSError, ValueError, TypeError) as exc:
        print(f"Collection failed: {exc}", file=sys.stderr)
        event("exit", code=1, error=str(exc), count=len(state["records"]))
        return 1

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--fail-third", action="store_true")
    parser.add_argument("--page")
    args = parser.parse_args()
    return collect(args.base_url, args.output, OrcaBrowser(args.page), args.fail_third)

if __name__ == "__main__":
    sys.exit(main())
