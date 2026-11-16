"""Validation of SA11 page records and document errors."""


def _object(value, fields, label):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ValueError(f"{label}: expected fields {', '.join(fields)}")


def _string(value, label, *, nonempty=False):
    if not isinstance(value, str) or (nonempty and not value):
        raise ValueError(f"{label}: expected {'non-empty ' if nonempty else ''}string")


def _strings(value, label):
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{label}: expected list of strings")


def validate_page(record):
    """Raise ValueError if a successful page does not follow the contract."""
    _object(
        record, ("source", "page", "method", "text", "tables", "uncertainty"), "page"
    )
    _string(record["source"], "source", nonempty=True)
    if type(record["page"]) is not int or record["page"] < 1:
        raise ValueError("page: expected positive integer")
    _string(record["method"], "method", nonempty=True)
    _string(record["text"], "text")
    _strings(record["uncertainty"], "uncertainty")
    if not isinstance(record["tables"], list):
        raise ValueError("tables: expected list")  # noqa: TRY004 - public validator contract
    for table in record["tables"]:
        _object(table, ("columns", "rows"), "table")
        _strings(table["columns"], "columns")
        if not isinstance(table["rows"], list):
            raise ValueError("rows: expected list")  # noqa: TRY004 - public validator contract
        for row in table["rows"]:
            _strings(row, "row")


def validate_batch(payload):
    """Raise ValueError if the separate pages and errors are invalid."""
    _object(payload, ("pages", "errors"), "batch")
    if not isinstance(payload["pages"], list) or not isinstance(
        payload["errors"], list
    ):
        raise ValueError("pages and errors: expected lists")  # noqa: TRY004 - public validator contract
    for page in payload["pages"]:
        validate_page(page)
    for error in payload["errors"]:
        _object(error, ("source", "error", "continued"), "error")
        _string(error["source"], "source", nonempty=True)
        _string(error["error"], "error", nonempty=True)
        if error["continued"] is not True:
            raise ValueError("continued: expected true")
